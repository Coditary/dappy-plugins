"""Minimal DAP adapter: run the real external debugger/tool, then report session state."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass
from typing import Any, BinaryIO, TextIO

# Launchers that usually open a GUI — spawn detached so the session can complete.
_DETACH_LAUNCHERS = frozenset(
    {
        "dappy-re-launch",
        "dappy-graphics-launch",
        "dappy-mobile-launch",
        "dappy-embedded-launch",
        "dappy-hardware-launch",
        "dappy-remedybg-launch",
        "dappy-dnspy-launch",
        "dappy-ilspy-launch",
        "dappy-domain-launch",
        "dappy-math-launch",
        "dappy-hpc-launch",
        "dappy-timetravel-launch",
    }
)

_out_seq = 0
_out_lock = threading.Lock()
_process: subprocess.Popen[str] | None = None
_process_lock = threading.Lock()
_session: dict[str, Any] = {}
_wrapped_cmd: list[str] = []


@dataclass
class DapMessage:
    seq: int | None = None
    type: str = ""
    command: str | None = None
    event: str | None = None
    request_seq: int | None = None
    success: bool | None = None
    body: dict[str, Any] | None = None
    message: str | None = None
    arguments: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DapMessage:
        return cls(
            seq=data.get("seq"),
            type=data.get("type", ""),
            command=data.get("command"),
            event=data.get("event"),
            request_seq=data.get("request_seq"),
            success=data.get("success"),
            body=data.get("body"),
            message=data.get("message"),
            arguments=data.get("arguments"),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"type": self.type}
        for key in (
            "seq",
            "command",
            "event",
            "request_seq",
            "success",
            "body",
            "message",
            "arguments",
        ):
            value = getattr(self, key)
            if value is not None:
                payload[key] = value
        return payload


def _read_message(stream: BinaryIO) -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        decoded = line.decode("ascii", errors="replace").strip()
        if not decoded:
            break
        key, value = decoded.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    body = stream.read(length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def _write_message(stream: TextIO, payload: dict[str, Any]) -> None:
    global _out_seq
    with _out_lock:
        _out_seq += 1
        payload = dict(payload)
        payload["seq"] = _out_seq
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    stream.buffer.write(f"Content-Length: {len(data)}\r\n\r\n".encode("ascii"))
    stream.buffer.write(data)
    stream.buffer.flush()


def _respond(
    stream: TextIO,
    request: DapMessage,
    *,
    body: dict[str, Any] | None = None,
    success: bool = True,
    message: str | None = None,
) -> None:
    _write_message(
        stream,
        {
            "type": "response",
            "request_seq": request.seq,
            "command": request.command,
            "success": success,
            "message": message or "",
            "body": body or {},
        },
    )


def _emit_event(stream: TextIO, event: str, body: dict[str, Any]) -> None:
    _write_message(stream, {"type": "event", "event": event, "body": body})


def _output(stream: TextIO, text: str, category: str = "console") -> None:
    _emit_event(stream, "output", {"category": category, "output": text})


def _program_from_args(args: dict[str, Any]) -> str:
    for key in ("program", "file", "script"):
        value = args.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _should_detach(args: dict[str, Any]) -> bool:
    if args.get("detach") is True:
        return True
    if args.get("detach") is False:
        return False
    if not _wrapped_cmd:
        return False
    return _wrapped_cmd[0] in _DETACH_LAUNCHERS


def _spawn_tool(stream: TextIO, args: dict[str, Any]) -> subprocess.Popen[str] | None:
    if not _wrapped_cmd:
        raise RuntimeError("no wrapped launcher command configured")

    program = _program_from_args(args)
    cwd = args.get("cwd") or (os.path.dirname(program) if program else None)
    env = os.environ.copy()
    if program:
        env["DAPPY_PROGRAM"] = program
    for key, value in args.items():
        if isinstance(value, str) and key.isupper():
            env[key] = value

    command = list(_wrapped_cmd)
    for candidate in (shutil.which(command[0]), command[0]):
        if candidate and (os.path.isfile(candidate) or shutil.which(candidate)):
            command[0] = candidate
            break

    if _should_detach(args):
        proc = subprocess.Popen(
            command,
            env=env,
            cwd=cwd or None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        _output(
            stream,
            f"Started {' '.join(command)} (pid {proc.pid}). "
            "Use the native debugger UI/terminal for stepping and inspection.\n",
        )
        return proc

    proc = subprocess.Popen(
        command,
        env=env,
        cwd=cwd or None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        _output(stream, line)
    proc.wait()
    if proc.returncode not in (0, None):
        _output(stream, f"Launcher exited with code {proc.returncode}\n", category="stderr")
    return proc


def _handle_initialize(stream: TextIO, request: DapMessage) -> None:
    body = {
        "supportsConfigurationDoneRequest": True,
        "supportsTerminateRequest": True,
        "supportTerminateDebuggee": True,
        "supportsRunInTerminalRequest": True,
        "supportsEvaluateForHovers": False,
        "supportsStepBack": False,
        "supportsRestartRequest": False,
    }
    _respond(stream, request, body=body)


def _handle_launch(stream: TextIO, request: DapMessage) -> None:
    global _process, _session
    args = request.arguments or {}
    _session = dict(args)
    try:
        with _process_lock:
            _process = _spawn_tool(stream, args)
        body: dict[str, Any] = {}
        if _process is not None:
            body["processId"] = _process.pid
        _respond(stream, request, body=body)
        _emit_event(stream, "initialized", {})
    except Exception as exc:  # noqa: BLE001
        _respond(stream, request, success=False, message=str(exc))


def _handle_attach(stream: TextIO, request: DapMessage) -> None:
    _handle_launch(stream, request)


def _handle_configuration_done(stream: TextIO, request: DapMessage) -> None:
    _respond(stream, request, body={})
    program = _program_from_args(_session)
    _emit_event(
        stream,
        "stopped",
        {
            "reason": "entry",
            "threadId": 1,
            "description": "External debugger session active",
            "allThreadsStopped": True,
            "text": os.path.basename(program) if program else "program",
        },
    )


def _handle_disconnect(stream: TextIO, request: DapMessage) -> None:
    with _process_lock:
        if _process is not None and _process.poll() is None:
            _process.terminate()
    _respond(stream, request, body={})


def _handle_terminate(stream: TextIO, request: DapMessage) -> None:
    _handle_disconnect(stream, request)


def _handle_threads(stream: TextIO, request: DapMessage) -> None:
    _respond(stream, request, body={"threads": [{"id": 1, "name": "MainThread"}]})


def _handle_stack_trace(stream: TextIO, request: DapMessage) -> None:
    program = _program_from_args(_session) or "<unknown>"
    _respond(
        stream,
        request,
        body={
            "stackFrames": [
                {
                    "id": 1,
                    "name": "external",
                    "source": {"path": program, "name": os.path.basename(program)},
                    "line": 1,
                    "column": 1,
                }
            ],
            "totalFrames": 1,
        },
    )


def _noop(stream: TextIO, request: DapMessage) -> None:
    _respond(stream, request, body={})


_HANDLERS = {
    "initialize": _handle_initialize,
    "launch": _handle_launch,
    "attach": _handle_attach,
    "configurationDone": _handle_configuration_done,
    "disconnect": _handle_disconnect,
    "terminate": _handle_terminate,
    "threads": _handle_threads,
    "stackTrace": _handle_stack_trace,
    "setBreakpoints": _noop,
    "setExceptionBreakpoints": _noop,
    "continue": _noop,
    "next": _noop,
    "stepIn": _noop,
    "stepOut": _noop,
    "pause": _noop,
    "scopes": _noop,
    "variables": _noop,
    "evaluate": _noop,
}


def _parse_wrapped_command(argv: list[str]) -> list[str]:
    if "--" in argv:
        idx = argv.index("--")
        return argv[idx + 1 :]
    return argv


def main() -> None:
    global _wrapped_cmd
    _wrapped_cmd = _parse_wrapped_command(sys.argv[1:])
    if not _wrapped_cmd:
        sys.stderr.write(
            "dappy-launcher-dap: usage: dappy-launcher-dap <launcher> [args...]\n"
        )
        raise SystemExit(2)

    stream = sys.stdin
    while True:
        raw = _read_message(stream.buffer)
        if raw is None:
            break
        message = DapMessage.from_dict(raw)
        if message.type != "request" or not message.command:
            continue
        handler = _HANDLERS.get(message.command, _noop)
        handler(sys.stdout, message)


if __name__ == "__main__":
    main()
