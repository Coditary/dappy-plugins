"""Minimal DAP adapter for pdb++ (pdbpp).

pdb++ is a terminal-first debugger; this bridge exposes bdb/pdb state over DAP so
Dappy (dap-cli REPL, dap-proxy, MCP) can drive continue/step/stack/variables.
Optional ``console: integratedTerminal`` uses ``runInTerminal`` for a full
(Pdb++) prompt with sticky mode, syntax highlighting, and completion.
"""

from __future__ import annotations

import json
import os
import runpy
import sys
import threading
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# ---------------------------------------------------------------------------
# pdb++ bootstrap — must run before ``import pdb`` semantics matter.
# ---------------------------------------------------------------------------


def _ensure_pdbpp() -> Any:
    """Return the hijacked ``pdb`` module provided by pdbpp."""
    try:
        import pdbpp  # noqa: F401 — ensures site-packages shadow is present
    except ImportError as exc:
        sys.stderr.write(
            "dappy-pdbpp-dap: pdbpp is not installed (pip install pdbpp)\n"
        )
        raise SystemExit(1) from exc

    import pdb

    mod_file = getattr(pdb, "__file__", "") or ""
    if "pdbpp" not in mod_file and "site-packages" not in mod_file:
        sys.stderr.write(
            "dappy-pdbpp-dap: stdlib pdb is active; install pdbpp to enable pdb++\n"
        )
    return pdb


pdb = _ensure_pdbpp()


# ---------------------------------------------------------------------------
# DAP wire protocol (Content-Length framing)
# ---------------------------------------------------------------------------


def _read_message() -> dict[str, Any] | None:
    """Read one DAP message from stdin (binary Content-Length framing)."""
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
    header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
    stdout = sys.stdout.buffer
    stdout.write(header)
    stdout.write(data)
    stdout.flush()


# ---------------------------------------------------------------------------
# Debugger session
# ---------------------------------------------------------------------------


@dataclass
class Breakpoint:
    source: str
    line: int
    verified: bool = True


@dataclass
class SessionState:
    seq: int = 1
    thread_id: int = 1
    breakpoints: dict[str, list[Breakpoint]] = field(default_factory=dict)
    stop_on_entry: bool = True
    post_mortem: bool = True
    sticky: bool = False
    interactive: bool = False
    terminal: bool = False
    program: str = ""
    cwd: str = ""
    python: str = sys.executable
    initialized: bool = False
    configuration_done: bool = False
    running: bool = False
    terminated: bool = False
    frame: Any = None
    stop_reason: str = "entry"
    stop_description: str = ""
    resume_event: threading.Event = field(default_factory=threading.Event)
    next_command: str = "continue"
    lock: threading.Lock = field(default_factory=threading.Lock)
    send_event: Callable[[str, dict[str, Any]], None] | None = None
    send_request: Callable[[str, dict[str, Any]], Any] | None = None

    def next_seq(self) -> int:
        self.seq += 1
        return self.seq


class DappyPdb(pdb.Pdb):
    """pdb++ ``Pdb`` subclass synchronized with DAP continue/step commands."""

    def __init__(self, state: SessionState) -> None:
        super().__init__()
        self.state = state
        self._entry_seen = False
        self._skip_stop = False
        # Prevent pdb++ from blocking on stdin unless explicitly requested.
        self.prompt = "(Pdb++) "

    def user_call(self, frame: Any, argument_list: Any) -> None:
        return

    def user_return(self, frame: Any, return_value: Any) -> None:
        return

    def user_exception(self, frame: Any, exc_info: tuple) -> None:
        if not self.state.post_mortem:
            return
        if not self._is_user_frame(frame):
            return
        exc_type, exc_val, _ = exc_info
        if exc_type in (StopIteration, SystemExit, KeyboardInterrupt):
            return
        self.state.stop_reason = "exception"
        self.state.stop_description = f"{exc_type.__name__}: {exc_val}"
        self._dap_stop(frame)

    def _is_user_frame(self, frame: Any) -> bool:
        if self.state.program:
            return os.path.abspath(frame.f_code.co_filename) == os.path.abspath(
                self.state.program
            )
        return True

    def _should_stop(self, frame: Any, *, exception: bool = False) -> bool:
        if self._skip_stop:
            return False
        filename = os.path.abspath(frame.f_code.co_filename)
        line = frame.f_lineno

        if self.state.stop_on_entry and not self._entry_seen:
            prog = os.path.abspath(self.state.program)
            if filename == prog:
                self._entry_seen = True
                self.state.stop_reason = "entry"
                self.state.stop_description = "stop on entry"
                return True

        for bp in self.state.breakpoints.get(filename, []):
            if bp.line == line:
                self.state.stop_reason = "breakpoint"
                self.state.stop_description = f"breakpoint at line {line}"
                return True
        return False

    def user_line(self, frame: Any) -> None:
        if self._should_stop(frame):
            self._dap_stop(frame)

    def _dap_stop(self, frame: Any) -> None:
        self.state.frame = frame
        if self.state.sticky:
            try:
                self.do_sticky("")
            except Exception:
                pass
        if self.state.interactive and sys.stdin.isatty():
            self.interaction(frame, None)
            return
        if self.state.send_event:
            self.state.send_event(
                "stopped",
                {
                    "reason": self.state.stop_reason,
                    "threadId": self.state.thread_id,
                    "description": self.state.stop_description,
                    "allThreadsStopped": True,
                },
            )
        self.state.resume_event.clear()
        self.state.resume_event.wait()
        cmd = self.state.next_command
        self.state.next_command = "continue"
        if cmd == "continue":
            self.set_continue()
        elif cmd == "next":
            self.set_next(frame)
        elif cmd == "step":
            self.set_step()
        elif cmd == "return":
            self.set_return(frame)
        else:
            self.set_continue()

    def interaction(self, frame: Any, traceback: Any) -> None:
        """Route pdb++ interaction — terminal UI only when ``interactive`` is set."""
        if self.state.interactive:
            if self.state.sticky:
                try:
                    self.do_sticky("")
                except Exception:
                    pass
            super().interaction(frame, traceback)
            return
        self._dap_stop(frame)


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class PdbppAdapter:
    def __init__(self) -> None:
        self.state = SessionState()
        self.state.send_event = self._send_event
        self.state.send_request = self._send_request
        self._pending_requests: dict[int, threading.Event] = {}
        self._pending_responses: dict[int, dict[str, Any]] = {}
        self._debug_thread: threading.Thread | None = None

    def run(self) -> None:
        while True:
            msg = _read_message()
            if msg is None:
                break
            if "type" not in msg:
                continue
            if msg["type"] == "request":
                self._handle_request(msg)
            elif msg["type"] == "response":
                self._handle_response(msg)
            elif msg["type"] == "event":
                pass

    def _handle_response(self, msg: dict[str, Any]) -> None:
        req_seq = msg.get("request_seq")
        if req_seq is not None:
            self._pending_responses[req_seq] = msg
            event = self._pending_requests.pop(req_seq, None)
            if event:
                event.set()

    def _send_event(self, event: str, body: dict[str, Any]) -> None:
        _write_message(
            {
                "type": "event",
                "seq": self.state.next_seq(),
                "event": event,
                "body": body,
            }
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

    def _send_request(self, command: str, arguments: dict[str, Any]) -> dict[str, Any]:
        seq = self.state.next_seq()
        event = threading.Event()
        self._pending_requests[seq] = event
        _write_message(
            {
                "type": "request",
                "seq": seq,
                "command": command,
                "arguments": arguments,
            }
        )
        if not event.wait(timeout=30):
            return {"success": False, "message": "timeout waiting for client response"}
        return self._pending_responses.pop(seq, {})

    def _handle_request(self, request: dict[str, Any]) -> None:
        cmd = request.get("command", "")
        args = request.get("arguments") or {}
        handlers: dict[str, Callable[[dict[str, Any], dict[str, Any]], None]] = {
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
            "pause": self._cmd_pause,
            "disconnect": self._cmd_disconnect,
            "terminate": self._cmd_terminate,
        }
        handler = handlers.get(cmd)
        if handler:
            handler(request, args)
        else:
            self._send_response(request, body={})

    def _capabilities(self) -> dict[str, Any]:
        return {
            "supportsConfigurationDoneRequest": True,
            "supportsEvaluateForHovers": True,
            "supportsExceptionInfoRequest": True,
            "supportTerminateDebuggee": True,
            "supportTerminateRequest": True,
        }

    def _cmd_initialize(self, request: dict[str, Any], args: dict[str, Any]) -> None:
        self._send_response(request, body=self._capabilities())
        self._send_event("initialized", {})
        self.state.initialized = True

    def _cmd_launch(self, request: dict[str, Any], args: dict[str, Any]) -> None:
        self.state.program = args.get("program", "")
        self.state.cwd = args.get("cwd") or str(Path(self.state.program).parent)
        self.state.python = args.get("python") or sys.executable
        self.state.stop_on_entry = bool(args.get("stopOnEntry", True))
        self.state.post_mortem = bool(args.get("postMortem", True))
        self.state.sticky = bool(args.get("sticky", False))
        self.state.interactive = bool(args.get("interactive", False))
        console = args.get("console", "internalConsole")
        self.state.terminal = console == "integratedTerminal"

        if self.state.terminal:
            self._launch_terminal(request, args)
            return

        self._send_response(request, body={})
        if self.state.configuration_done:
            self._start_debuggee()

    def _cmd_attach(self, request: dict[str, Any], args: dict[str, Any]) -> None:
        self._cmd_launch(request, args)

    def _launch_terminal(self, request: dict[str, Any], args: dict[str, Any]) -> None:
        """Spawn pdb++ in a real terminal via DAP ``runInTerminal``."""
        program = self.state.program
        cwd = self.state.cwd
        python = self.state.python
        # ``python -m pdb`` is hijacked by pdbpp when installed (see README).
        cmd = [python, "-m", "pdb", program]

        resp = self._send_request(
            "runInTerminal",
            {
                "kind": "integrated",
                "title": f"pdb++ {Path(program).name}",
                "cwd": cwd,
                "args": cmd,
            },
        )
        if resp.get("success") is False:
            self._send_response(
                request, message=resp.get("message", "runInTerminal failed")
            )
            return
        self._send_response(request, body={})
        self._send_event("terminated", {})
        self.state.terminated = True

    def _cmd_set_breakpoints(self, request: dict[str, Any], args: dict[str, Any]) -> None:
        source = args.get("source") or {}
        path = os.path.abspath(source.get("path", ""))
        lines = args.get("breakpoints") or []
        bps = [
            Breakpoint(source=path, line=int(item.get("line", 1)))
            for item in lines
            if "line" in item
        ]
        self.state.breakpoints[path] = bps
        body = {
            "breakpoints": [
                {"id": idx + 1, "verified": True, "line": bp.line}
                for idx, bp in enumerate(bps)
            ]
        }
        self._send_response(request, body=body)

    def _cmd_configuration_done(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self.state.configuration_done = True
        self._send_response(request, body={})
        if self.state.program and not self.state.terminal and not self.state.running:
            self._start_debuggee()

    def _start_debuggee(self) -> None:
        if self.state.running or self.state.terminated:
            return
        self.state.running = True
        self._debug_thread = threading.Thread(target=self._run_debuggee, daemon=True)
        self._debug_thread.start()

    def _run_debuggee(self) -> None:
        prog = self.state.program
        cwd = self.state.cwd
        try:
            os.chdir(cwd)
            debugger = DappyPdb(self.state)
            for path, bps in self.state.breakpoints.items():
                for bp in bps:
                    debugger.set_break(bp.source, bp.line)
            debugger.runcall(self._exec_program, prog)
        except SystemExit:
            pass
        except Exception:
            if self.state.post_mortem:
                self._send_event(
                    "stopped",
                    {
                        "reason": "exception",
                        "threadId": self.state.thread_id,
                        "description": traceback.format_exc(limit=1).strip(),
                        "allThreadsStopped": True,
                    },
                )
                try:
                    pdb.post_mortem(sys.exc_info()[2])
                except Exception:
                    pass
            else:
                self._send_event(
                    "output",
                    {
                        "category": "stderr",
                        "output": traceback.format_exc(),
                    },
                )
        finally:
            self.state.terminated = True
            self.state.running = False
            if self.state.send_event:
                self._send_event("terminated", {})

    @staticmethod
    def _exec_program(program: str) -> None:
        path = Path(program)
        runpy.run_path(str(path), run_name="__main__")

    def _cmd_threads(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self._send_response(
            request,
            body={"threads": [{"id": self.state.thread_id, "name": "MainThread"}]},
        )

    def _cmd_stack_trace(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        frames = []
        frame = self.state.frame
        idx = 0
        while frame is not None:
            frames.append(
                {
                    "id": idx + 1,
                    "name": frame.f_code.co_name or "<module>",
                    "source": {
                        "path": frame.f_code.co_filename,
                    },
                    "line": frame.f_lineno,
                    "column": 0,
                }
            )
            frame = frame.f_back
            idx += 1
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
                    },
                    {
                        "name": "Globals",
                        "variablesReference": frame_id * 100 + 2,
                        "expensive": True,
                    },
                ]
            },
        )

    def _cmd_variables(self, request: dict[str, Any], args: dict[str, Any]) -> None:
        ref = int(args.get("variablesReference", 0))
        frame = self.state.frame
        if frame is None:
            self._send_response(request, body={"variables": []})
            return
        kind = ref % 100
        mapping = frame.f_locals if kind == 1 else frame.f_globals
        variables = []
        for name, value in sorted(mapping.items(), key=lambda item: item[0]):
            if name.startswith("__") and name.endswith("__"):
                continue
            variables.append(
                {
                    "name": name,
                    "value": repr(value),
                    "type": type(value).__name__,
                    "variablesReference": 0,
                }
            )
        self._send_response(request, body={"variables": variables})

    def _resume(self, request: dict[str, Any], command: str) -> None:
        self.state.next_command = command
        self.state.resume_event.set()
        self._send_response(request, body={})

    def _cmd_continue(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self._resume(request, "continue")

    def _cmd_next(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self._resume(request, "next")

    def _cmd_step_in(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self._resume(request, "step")

    def _cmd_step_out(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self._resume(request, "return")

    def _cmd_pause(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self._send_response(request, body={})

    def _cmd_disconnect(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self.state.terminated = True
        self.state.resume_event.set()
        self._send_response(request, body={})

    def _cmd_terminate(self, request: dict[str, Any], _: dict[str, Any]) -> None:
        self.state.terminated = True
        self.state.resume_event.set()
        self._send_response(request, body={})


def main() -> None:
    PdbppAdapter().run()


if __name__ == "__main__":
    main()
