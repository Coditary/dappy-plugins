"""Minimal DAP adapter for GNU GDB via MI3 interpreter."""

from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

_TOKEN_RE = re.compile(r"^(\d+)")


def _read_message() -> dict[str, Any] | None:
    stdin = sys.stdin.buffer
    headers: dict[str, str] = {}
    while True:
        line = stdin.readline()
        if not line:
            return None
        if line.strip() == b"":
            break
        key, _, value = line.decode("ascii", errors="replace").partition(":")
        headers[key.strip().lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length == 0:
        return None
    body = stdin.read(length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def _write_message(payload: dict[str, Any]) -> None:
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(data)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


@dataclass
class MiResult:
    token: int
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)
    records: list[dict[str, Any]] = field(default_factory=list)


class GdbMi:
    def __init__(self, gdb_command: str = "gdb") -> None:
        if not shutil.which(gdb_command):
            sys.stderr.write(f"dappy-gdb-dap: `{gdb_command}` not found on PATH\n")
            raise SystemExit(1)
        self._proc = subprocess.Popen(
            [gdb_command, "--interpreter=mi3", "-nx"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
            text=True,
        )
        self._token = 0
        self._pending: dict[int, queue.Queue[MiResult]] = {}
        self._async: queue.Queue[MiResult] = queue.Queue()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _read_loop(self) -> None:
        assert self._proc.stdout is not None
        for line in self._proc.stdout:
            line = line.rstrip("\r\n")
            if not line:
                continue
            result = self._parse_line(line)
            if result is None:
                continue
            if result.token and result.token in self._pending:
                self._pending[result.token].put(result)
            else:
                self._async.put(result)

    def _parse_line(self, line: str) -> MiResult | None:
        token = 0
        m = _TOKEN_RE.match(line)
        if m:
            token = int(m.group(1))
            line = line[m.end() :]
        if line.startswith("^"):
            kind, rest = line[1:].split(",", 1) if "," in line[1:] else (line[1:], "")
            return MiResult(token=token, kind=kind, payload=self._parse_csv(rest))
        if line.startswith("*"):
            kind, rest = line[1:].split(",", 1) if "," in line[1:] else (line[1:], "")
            return MiResult(token=token, kind=kind, payload=self._parse_csv(rest), records=[])
        if line.startswith("="):
            kind, rest = line[1:].split(",", 1) if "," in line[1:] else (line[1:], "")
            return MiResult(token=token, kind=kind, payload=self._parse_csv(rest))
        return None

    @staticmethod
    def _parse_csv(rest: str) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for part in re.findall(r'(\w+)=(?:"((?:\\.|[^"\\])*)"|([^,]*))', rest):
            key, quoted, bare = part
            out[key] = quoted if quoted else bare
        return out

    def command(self, cmd: str, timeout: float = 30.0) -> MiResult:
        self._token += 1
        token = self._token
        q: queue.Queue[MiResult] = queue.Queue()
        self._pending[token] = q
        assert self._proc.stdin is not None
        self._proc.stdin.write(f"{token}-{cmd}\n")
        self._proc.stdin.flush()
        try:
            return q.get(timeout=timeout)
        finally:
            self._pending.pop(token, None)

    def wait_stopped(self, timeout: float = 60.0) -> MiResult:
        return self._async.get(timeout=timeout)


@dataclass
class Session:
    seq: int = 1
    gdb: GdbMi | None = None
    program: str = ""
    cwd: str = ""
    gdb_command: str = "gdb"
    stop_on_entry: bool = True
    thread_id: int = 1
    frame_id: int = 1
    breakpoints: dict[str, list[int]] = field(default_factory=dict)
    configuration_done: bool = False
    running: bool = False
    resume_event: threading.Event = field(default_factory=threading.Event)
    send_event: Callable[[str, dict[str, Any]], None] | None = None

    def next_seq(self) -> int:
        self.seq += 1
        return self.seq


class GdbAdapter:
    def __init__(self) -> None:
        self.state = Session()
        self.state.send_event = self._send_event

    def run(self) -> None:
        while True:
            msg = _read_message()
            if msg is None:
                break
            if msg.get("type") == "request":
                self._handle_request(msg)

    def _send_event(self, event: str, body: dict[str, Any]) -> None:
        _write_message(
            {"type": "event", "seq": self.state.next_seq(), "event": event, "body": body}
        )

    def _send_response(
        self, request: dict[str, Any], body: dict[str, Any] | None = None, **kwargs: Any
    ) -> None:
        resp: dict[str, Any] = {
            "type": "response",
            "seq": self.state.next_seq(),
            "request_seq": request["seq"],
            "command": request["command"],
            "success": kwargs.get("success", True),
        }
        if body is not None:
            resp["body"] = body
        if "message" in kwargs:
            resp["message"] = kwargs["message"]
            resp["success"] = False
        _write_message(resp)

    def _handle_request(self, request: dict[str, Any]) -> None:
        cmd = request.get("command", "")
        args = request.get("arguments") or {}
        handlers = {
            "initialize": self._cmd_initialize,
            "launch": self._cmd_launch,
            "attach": self._cmd_attach,
            "setBreakpoints": self._cmd_set_breakpoints,
            "configurationDone": self._cmd_configuration_done,
            "threads": self._cmd_threads,
            "stackTrace": self._cmd_stack_trace,
            "scopes": self._cmd_scopes,
            "variables": self._cmd_variables,
            "continue": self._cmd_continue,
            "next": self._cmd_next,
            "stepIn": self._cmd_step_in,
            "stepOut": self._cmd_step_out,
            "disconnect": self._cmd_disconnect,
            "terminate": self._cmd_terminate,
        }
        handler = handlers.get(cmd)
        if handler:
            handler(request, args)
        else:
            self._send_response(request, body={})

    def _cmd_initialize(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self._send_response(
            request,
            body={
                "supportsConfigurationDoneRequest": True,
                "supportsStepBack": False,
            },
        )
        self._send_event("initialized", {})

    def _cmd_launch(self, request: dict[str, Any], args: dict[str, Any]) -> None:
        self.state.program = args.get("program", "")
        self.state.cwd = args.get("cwd") or os.path.dirname(self.state.program)
        self.state.gdb_command = args.get("gdb") or os.environ.get("GDB", "gdb")
        self.state.stop_on_entry = bool(args.get("stopOnEntry", True))
        self._send_response(request, body={})
        if self.state.configuration_done:
            self._start_session()

    def _cmd_attach(self, request: dict[str, Any], args: dict[str, Any]) -> None:
        self._cmd_launch(request, args)

    def _cmd_set_breakpoints(self, request: dict[str, Any], args: dict[str, Any]) -> None:
        source = args.get("source") or {}
        path = os.path.abspath(source.get("path", ""))
        lines = [int(item["line"]) for item in args.get("breakpoints") or [] if "line" in item]
        self.state.breakpoints[path] = lines
        body = {
            "breakpoints": [
                {"id": idx + 1, "verified": True, "line": line}
                for idx, line in enumerate(lines)
            ]
        }
        self._send_response(request, body=body)
        if self.state.gdb and path:
            for line in lines:
                self.state.gdb.command(f'break-insert -f "{path}:{line}"')

    def _cmd_configuration_done(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self.state.configuration_done = True
        self._send_response(request, body={})
        if self.state.program and not self.state.running:
            self._start_session()

    def _start_session(self) -> None:
        if self.state.running:
            return
        self.state.running = True
        threading.Thread(target=self._run_debuggee, daemon=True).start()

    def _run_debuggee(self) -> None:
        try:
            os.chdir(self.state.cwd or ".")
            self.state.gdb = GdbMi(self.state.gdb_command)
            gdb = self.state.gdb
            gdb.command(f'file "{self.state.program}"')
            for path, lines in self.state.breakpoints.items():
                for line in lines:
                    gdb.command(f'break-insert -f "{path}:{line}"')
            if self.state.stop_on_entry:
                gdb.command("exec-run --start")
            else:
                gdb.command("exec-run")
            while self.state.running:
                stopped = gdb.wait_stopped()
                reason = stopped.payload.get("reason", "entry")
                self._emit_stopped(reason)
                self.state.resume_event.clear()
                self.state.resume_event.wait()
        except Exception as exc:
            self._send_event(
                "output",
                {"category": "stderr", "output": f"{exc}\n"},
            )
        finally:
            self.state.running = False
            self._send_event("terminated", {})

    def _emit_stopped(self, reason: str) -> None:
        self._send_event(
            "stopped",
            {
                "reason": reason,
                "threadId": self.state.thread_id,
                "allThreadsStopped": True,
            },
        )

    def _cmd_threads(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self._send_response(
            request,
            body={"threads": [{"id": self.state.thread_id, "name": "1"}]},
        )

    def _cmd_stack_trace(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        frames = []
        if self.state.gdb:
            result = self.state.gdb.command("stack-list-frames")
            # MI returns frame data in async records; simplified single frame fallback
            frames.append(
                {
                    "id": 1,
                    "name": "frame",
                    "line": 1,
                    "column": 0,
                    "source": {"path": self.state.program},
                }
            )
        self._send_response(request, body={"stackFrames": frames, "totalFrames": len(frames)})

    def _cmd_scopes(self, request: dict[str, Any], args: dict[str, Any]) -> None:
        frame_id = int(args.get("frameId", 1))
        self._send_response(
            request,
            body={
                "scopes": [
                    {
                        "name": "Locals",
                        "variablesReference": frame_id * 100 + 1,
                        "expensive": False,
                    }
                ]
            },
        )

    def _cmd_variables(self, request: dict[str, Any], args: dict[str, Any]) -> None:
        variables = []
        if self.state.gdb:
            frame = int(args.get("variablesReference", 1)) // 100 or 1
            result = self.state.gdb.command(f"stack-list-variables --frame {frame} --all-values")
            del result
        self._send_response(request, body={"variables": variables})

    def _exec_and_wait(self, request: dict[str, Any], mi_cmd: str) -> None:
        if self.state.gdb:
            self.state.gdb.command(mi_cmd)
        self.state.resume_event.set()
        self._send_response(request, body={})

    def _cmd_continue(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self._exec_and_wait(request, "exec-continue")

    def _cmd_next(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self._exec_and_wait(request, "exec-next")

    def _cmd_step_in(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self._exec_and_wait(request, "exec-step")

    def _cmd_step_out(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self._exec_and_wait(request, "exec-finish")

    def _cmd_disconnect(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self.state.running = False
        self.state.resume_event.set()
        self._send_response(request, body={})

    def _cmd_terminate(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self.state.running = False
        self.state.resume_event.set()
        if self.state.gdb:
            self.state.gdb.command("exec-interrupt")
        self._send_response(request, body={})


def main() -> None:
    GdbAdapter().run()


if __name__ == "__main__":
    main()
