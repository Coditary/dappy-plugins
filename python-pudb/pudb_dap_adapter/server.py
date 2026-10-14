#!/usr/bin/env python3
"""Minimal DAP adapter that launches PuDB in a terminal.

PuDB is a full-screen TUI debugger with no native DAP support. This bridge:

* Spawns ``python -m pudb <program>`` (or remote/breakpoint modes) via
  ``runInTerminal`` when the client supports it, otherwise inherits the
  current terminal when one is available.
* Completes the standard DAP init handshake so Dappy can route sessions.
* Does **not** proxy stepping, stack traces, or variables — control stays
  in the PuDB terminal (same limitation as ipdab for pdb/ipdb).
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import threading
from dataclasses import dataclass
from typing import Any, BinaryIO, TextIO

# DAP sequence counter (events/responses share the outbound stream).
_out_seq = 0
_out_lock = threading.Lock()

# Background process started for the debug session.
_process: subprocess.Popen[str] | None = None
_process_lock = threading.Lock()

# Parsed launch configuration for the active session.
_session: dict[str, Any] = {}

# Whether the DAP client declared runInTerminal support in initialize.
_supports_run_in_terminal = False

# Remote-mode telnet port detected from child stdout (if any).
_remote_port: int | None = None

_TELNET_HINT = re.compile(
    r"telnet\s+(?P<host>[\d.]+)\s+(?P<port>\d+)", re.IGNORECASE
)
_PUDUB_PORT = re.compile(r"pudb:(?P<port>\d+)", re.IGNORECASE)


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


def _next_seq() -> int:
    global _out_seq
    with _out_lock:
        _out_seq += 1
        return _out_seq


def _write_message(stream: TextIO, message: DapMessage) -> None:
    message.seq = _next_seq()
    body = json.dumps(message.to_dict(), separators=(",", ":"))
    encoded = body.encode("utf-8")
    header = f"Content-Length: {len(encoded)}\r\n\r\n"
    with _out_lock:
        stream.write(header)
        stream.write(body)
        stream.flush()


def _read_message(stream: BinaryIO) -> dict[str, Any] | None:
    header = b""
    while b"\r\n\r\n" not in header:
        chunk = stream.read(1)
        if not chunk:
            return None
        header += chunk
        if len(header) > 8192:
            raise ValueError("DAP header too large")

    content_length = 0
    for line in header.decode("ascii", errors="replace").split("\r\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
    if content_length <= 0:
        raise ValueError("missing Content-Length in DAP header")

    body = stream.read(content_length)
    if len(body) != content_length:
        return None
    return json.loads(body.decode("utf-8"))


def _emit_event(stream: TextIO, event: str, body: dict[str, Any] | None = None) -> None:
    _write_message(
        stream,
        DapMessage(type="event", event=event, body=body or {}),
    )


def _respond(
    stream: TextIO,
    request: DapMessage,
    *,
    success: bool = True,
    body: dict[str, Any] | None = None,
    message: str | None = None,
) -> None:
    _write_message(
        stream,
        DapMessage(
            type="response",
            request_seq=request.seq,
            command=request.command,
            success=success,
            body=body,
            message=message,
        ),
    )


def _output(stream: TextIO, text: str, category: str = "console") -> None:
    _emit_event(
        stream,
        "output",
        {"category": category, "output": text},
    )


def _kill_process() -> None:
    global _process
    with _process_lock:
        proc = _process
        _process = None
    if proc is None:
        return
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def _monitor_process(stream: TextIO, proc: subprocess.Popen[str]) -> None:
    """Watch the debuggee and emit terminated when it exits."""
    global _process
    exit_code = proc.wait()
    with _process_lock:
        if _process is proc:
            _process = None
    _emit_event(
        stream,
        "terminated",
        {
            "restart": False,
            "exitCode": exit_code,
        },
    )


def _watch_stdout_for_remote(stream: TextIO, proc: subprocess.Popen[str]) -> None:
    """Parse child stdout for pudb remote telnet hints."""
    global _remote_port
    if proc.stdout is None:
        return
    for line in proc.stdout:
        text = line.rstrip("\n")
        if text:
            _output(stream, text + "\n")
        match = _TELNET_HINT.search(text) or _PUDUB_PORT.search(text)
        if match and "port" in match.groupdict():
            port = int(match.group("port"))
            _remote_port = port
            host = match.groupdict().get("host") or "127.0.0.1"
            _output(
                stream,
                f"\nConnect PuDB with: telnet {host} {port}\n"
                "(or use your terminal multiplexer — PuDB is waiting for a client.)\n",
            )


def _build_command(args: dict[str, Any]) -> tuple[list[str], dict[str, str], str]:
    """Return argv, extra env, and a human-readable mode label."""
    python = args.get("python") or os.environ.get("PYTHON") or sys.executable
    program = args["program"]
    mode = (args.get("mode") or "launch").lower()
    pudb_module = args.get("pudbModule") or "pudb"
    cwd = args.get("cwd") or os.path.dirname(program) or os.getcwd()

    env = os.environ.copy()
    label = mode

    if mode == "launch":
        argv = [python, "-m", pudb_module, program]
    elif mode == "remote":
        env["PYTHONBREAKPOINT"] = "pudb.remote.set_trace"
        host = args.get("remoteHost") or "127.0.0.1"
        port = str(args.get("remotePort") or 6899)
        env["PUDB_RDB_HOST"] = host
        env["PUDB_RDB_PORT"] = port
        term_size = args.get("termSize")
        if term_size:
            env["PUDB_TERM_SIZE"] = term_size
        argv = [python, program]
        label = f"remote ({host}:{port})"
    elif mode == "breakpoint":
        env["PYTHONBREAKPOINT"] = "pudb.set_trace"
        argv = [python, program]
    else:
        raise ValueError(f"unknown pudb launch mode: {mode}")

    # Preserve cwd via env hint for runInTerminal consumers; spawn uses cwd directly.
    _session["cwd"] = cwd
    return argv, env, label


def _spawn_direct(
    stream: TextIO,
    argv: list[str],
    env: dict[str, str],
    cwd: str,
    *,
    capture_output: bool,
) -> subprocess.Popen[str]:
    stdout = subprocess.PIPE if capture_output else None
    stderr = subprocess.STDOUT if capture_output else None
    proc = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        stdout=stdout,
        stderr=stderr,
        text=True,
    )
    with _process_lock:
        global _process
        _process = proc
    threading.Thread(
        target=_monitor_process, args=(stream, proc), daemon=True
    ).start()
    if capture_output:
        threading.Thread(
            target=_watch_stdout_for_remote, args=(stream, proc), daemon=True
        ).start()
    return proc


def _request_run_in_terminal(
    stream: TextIO,
    request: DapMessage,
    argv: list[str],
    env: dict[str, str],
    cwd: str,
    title: str,
) -> dict[str, Any]:
    """Send a runInTerminal reverse request and block for the response."""
    term_request = DapMessage(
        type="request",
        command="runInTerminal",
        arguments={
            "kind": "integrated",
            "title": title,
            "cwd": cwd,
            "args": argv,
            "env": env,
        },
    )
    term_request.seq = _next_seq()
    body = json.dumps(term_request.to_dict(), separators=(",", ":"))
    encoded = body.encode("utf-8")
    header = f"Content-Length: {len(encoded)}\r\n\r\n"
    with _out_lock:
        stream.write(header)
        stream.write(body)
        stream.flush()

    while True:
        raw = _read_message(sys.stdin.buffer)
        if raw is None:
            raise RuntimeError("client closed before runInTerminal response")
        message = DapMessage.from_dict(raw)
        if message.type == "response" and message.request_seq == term_request.seq:
            if not message.success:
                raise RuntimeError(message.message or "runInTerminal failed")
            return message.body or {}
        # Forward unrelated traffic (shouldn't happen during sync wait).
        if message.type == "event":
            _write_message(stream, message)


def _launch_pudb(stream: TextIO, request: DapMessage) -> None:
    global _session, _remote_port
    _remote_port = None
    args = request.arguments or {}
    _session = dict(args)

    argv, env, mode_label = _build_command(args)
    cwd = _session.get("cwd") or os.getcwd()
    console = (args.get("console") or "externalTerminal").lower()
    title = args.get("terminalTitle") or f"PuDB ({mode_label})"

    use_run_in_terminal = console in {
        "externalterminal",
        "integratedterminal",
        "external",
        "integrated",
    }
    capture_output = (args.get("mode") or "launch").lower() in {"remote", "breakpoint"}

    proc: subprocess.Popen[str] | None = None
    terminal_body: dict[str, Any] | None = None

    if use_run_in_terminal and _supports_run_in_terminal:
        terminal_body = _request_run_in_terminal(stream, request, argv, env, cwd, title)
        pid = terminal_body.get("processId")
        if pid:
            _output(stream, f"PuDB spawned in terminal (pid {pid}).\n")
        log_path = terminal_body.get("logPath")
        if log_path:
            _output(stream, f"Terminal output log: {log_path}\n")
    elif sys.stdin.isatty() and sys.stdout.isatty():
        _output(
            stream,
            "Starting PuDB in the current terminal (no runInTerminal support detected).\n",
        )
        proc = _spawn_direct(stream, argv, env, cwd, capture_output=capture_output)
    elif _supports_run_in_terminal:
        terminal_body = _request_run_in_terminal(stream, request, argv, env, cwd, title)
    else:
        _output(
            stream,
            "Warning: no TTY and client lacks runInTerminal — attempting detached spawn.\n"
            "Install PuDB in a real terminal for the full-screen UI.\n",
        )
        proc = _spawn_direct(stream, argv, env, cwd, capture_output=capture_output)

    _emit_event(stream, "initialized", {})

    body: dict[str, Any] = {}
    if proc is not None:
        body["processId"] = proc.pid
    if terminal_body:
        body.update(
            {k: v for k, v in terminal_body.items() if k in {"processId", "logPath"}}
        )
    _respond(stream, request, body=body)

    if console not in {"internalconsole"}:
        _output(
            stream,
            "\nPuDB is a terminal UI debugger — use the PuDB window for "
            "stepping, breakpoints, and inspection.\n"
            "DAP continue/step/stackTrace requests are acknowledged but do "
            "not control PuDB.\n",
        )


def _handle_initialize(stream: TextIO, request: DapMessage) -> None:
    global _supports_run_in_terminal
    args = request.arguments or {}
    _supports_run_in_terminal = bool(args.get("supportsRunInTerminalRequest"))

    body = {
        "supportsConfigurationDoneRequest": True,
        "supportsRunInTerminalRequest": True,
        "supportsTerminateRequest": True,
        "supportTerminateDebuggee": True,
        "supportsCancelRequest": False,
        "supportsEvaluateForHovers": False,
        "supportsStepBack": False,
        "supportsRestartRequest": False,
        "supportsExceptionOptions": False,
    }
    _respond(stream, request, body=body)


def _handle_launch(stream: TextIO, request: DapMessage) -> None:
    try:
        _launch_pudb(stream, request)
    except Exception as exc:  # noqa: BLE001 — surface spawn failures to the client
        _respond(stream, request, success=False, message=str(exc))


def _handle_configuration_done(stream: TextIO, request: DapMessage) -> None:
    _respond(stream, request, body={})
    program = _session.get("program") or ""
    _emit_event(
        stream,
        "stopped",
        {
            "reason": "entry",
            "threadId": 1,
            "description": "PuDB session active — control debugging in the terminal",
            "allThreadsStopped": True,
            "text": os.path.basename(program) if program else "python",
        },
    )


def _handle_threads(stream: TextIO, request: DapMessage) -> None:
    _respond(stream, request, body={"threads": [{"id": 1, "name": "MainThread"}]})


def _handle_stack_trace(stream: TextIO, request: DapMessage) -> None:
    program = _session.get("program") or "<unknown>"
    _respond(
        stream,
        request,
        body={
            "stackFrames": [
                {
                    "id": 1,
                    "name": "PuDB",
                    "source": {"path": program, "name": os.path.basename(program)},
                    "line": 1,
                    "column": 1,
                }
            ],
            "totalFrames": 1,
        },
    )


def _handle_scopes(stream: TextIO, request: DapMessage) -> None:
    _respond(
        stream,
        request,
        body={
            "scopes": [
                {
                    "name": "PuDB",
                    "variablesReference": 0,
                    "expensive": False,
                    "presentationHint": "locals",
                }
            ]
        },
    )


def _handle_variables(stream: TextIO, request: DapMessage) -> None:
    _respond(stream, request, body={"variables": []})


def _handle_continue(stream: TextIO, request: DapMessage) -> None:
    _output(
        stream,
        "continue: PuDB runs in its own terminal — use PuDB keys (n/s/c/q) there.\n",
    )
    _respond(stream, request, body={"allThreadsContinued": True})
    _emit_event(
        stream,
        "continued",
        {"threadId": 1, "allThreadsContinued": True},
    )


def _handle_pause(stream: TextIO, request: DapMessage) -> None:
    _output(stream, "pause: not supported — PuDB is controlled from its terminal.\n")
    _respond(stream, request, body={})


def _handle_next_step(stream: TextIO, request: DapMessage, label: str) -> None:
    _output(
        stream,
        f"{label}: not supported via DAP — use PuDB keybindings in the terminal.\n",
    )
    _respond(stream, request, body={})


def _handle_set_breakpoints(stream: TextIO, request: DapMessage) -> None:
    _respond(
        stream,
        request,
        body={"breakpoints": (request.arguments or {}).get("breakpoints", [])},
    )


def _handle_disconnect(stream: TextIO, request: DapMessage) -> None:
    terminate = (request.arguments or {}).get("terminateDebuggee", True)
    if terminate:
        _kill_process()
    _respond(stream, request, body={})


def _handle_terminate(stream: TextIO, request: DapMessage) -> None:
    _kill_process()
    _respond(stream, request, body={})


def _dispatch(stream: TextIO, request: DapMessage) -> None:
    command = request.command or ""
    handlers = {
        "initialize": _handle_initialize,
        "launch": _handle_launch,
        "attach": _handle_launch,
        "configurationDone": _handle_configuration_done,
        "threads": _handle_threads,
        "stackTrace": _handle_stack_trace,
        "scopes": _handle_scopes,
        "variables": _handle_variables,
        "continue": _handle_continue,
        "pause": _handle_pause,
        "next": lambda s, r: _handle_next_step(s, r, "next"),
        "stepIn": lambda s, r: _handle_next_step(s, r, "stepIn"),
        "stepOut": lambda s, r: _handle_next_step(s, r, "stepOut"),
        "setBreakpoints": _handle_set_breakpoints,
        "setExceptionBreakpoints": lambda s, r: _respond(s, r, body={}),
        "disconnect": _handle_disconnect,
        "terminate": _handle_terminate,
    }
    handler = handlers.get(command)
    if handler:
        handler(stream, request)
    else:
        _respond(stream, request, body={})


def main() -> int:
    stream = sys.stdout
    try:
        while True:
            raw = _read_message(sys.stdin.buffer)
            if raw is None:
                break
            message = DapMessage.from_dict(raw)
            if message.type == "request":
                _dispatch(stream, message)
    finally:
        _kill_process()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
