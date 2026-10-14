#!/usr/bin/env python3
"""DAP stdio bridge for madbg (launch, attach, connect)."""

from __future__ import annotations

import sys
import threading
import time
from typing import Any, Optional

from madbg_dap.protocol import event, read_message, response, write_message
from madbg_dap.session import DEFAULT_HOST, DEFAULT_PORT, MadbgSession


class MadbgDapBridge:
    def __init__(self) -> None:
        self.seq = 1
        self.session: Optional[MadbgSession] = None
        self.initialized = False
        self.start_request: Optional[str] = None
        self._lock = threading.Lock()

    def next_seq(self) -> int:
        with self._lock:
            value = self.seq
            self.seq += 1
            return value

    def send(self, msg: dict[str, Any]) -> None:
        if msg.get("seq") == 0:
            msg = {**msg, "seq": self.next_seq()}
        write_message(msg)

    def emit_output(self, text: str, category: str = "stdout") -> None:
        self.send(
            event(
                "output",
                {
                    "category": category,
                    "output": text,
                },
            )
        )

    def emit_stopped(self, reason: str = "breakpoint") -> None:
        self.send(
            event(
                "stopped",
                {
                    "reason": reason,
                    "threadId": 1,
                    "allThreadsStopped": True,
                },
            )
        )

    def emit_terminated(self) -> None:
        self.send(event("terminated", {}))

    def handle(self, message: dict[str, Any]) -> None:
        if message.get("type") != "request":
            return
        request_seq = int(message["seq"])
        command = str(message["command"])
        arguments = message.get("arguments") or {}

        if command == "initialize":
            self.send(
                response(
                    request_seq,
                    "initialize",
                    {
                        "supportsConfigurationDoneRequest": True,
                        "supportsEvaluateForHovers": True,
                        "supportsSingleThreadExecutionRequests": True,
                        "supportsTerminateDebuggee": True,
                        "supportsAttachForConnect": True,
                    },
                )
            )
            self.initialized = True
            return

        if command in ("launch", "attach"):
            self.start_request = command
            self._start_session(command, arguments)
            self.send(response(request_seq, command, {}))
            self.send(event("initialized", {}))
            return

        if command == "configurationDone":
            self.send(response(request_seq, "configurationDone", {}))
            # Allow the relay thread to observe the initial pdb prompt.
            deadline = time.time() + 2.0
            while time.time() < deadline and self.session and not self.session.stopped:
                time.sleep(0.05)
            if self.session:
                self.session.stopped = True
            self.emit_stopped("entry")
            return

        if command == "disconnect":
            terminate = bool(arguments.get("terminateDebuggee"))
            if self.session:
                self.session.disconnect(terminate=terminate)
                self.session = None
            self.send(response(request_seq, "disconnect", {}))
            return

        if command == "terminate":
            if self.session:
                self.session.disconnect(terminate=True)
                self.session = None
            self.send(response(request_seq, "terminate", {}))
            self.emit_terminated()
            return

        if command == "threads":
            self.send(
                response(
                    request_seq,
                    "threads",
                    {"threads": [{"id": 1, "name": "main"}]},
                )
            )
            return

        if command == "continue":
            if self.session:
                self.session.continue_execution()
            self.send(
                response(
                    request_seq,
                    "continue",
                    {"allThreadsContinued": True},
                )
            )
            return

        if command == "next":
            if self.session:
                self.session.step_over()
            self.send(response(request_seq, "next", {}))
            return

        if command == "stepIn":
            if self.session:
                self.session.step_in()
            self.send(response(request_seq, "stepIn", {}))
            return

        if command == "stepOut":
            if self.session:
                self.session.step_out()
            self.send(response(request_seq, "stepOut", {}))
            return

        if command == "pause":
            if self.session:
                self.session.send_command("")
            self.send(response(request_seq, "pause", {}))
            self.emit_stopped("pause")
            return

        if command == "stackTrace":
            source = self.session.program if self.session else ""
            self.send(
                response(
                    request_seq,
                    "stackTrace",
                    {
                        "stackFrames": [
                            {
                                "id": 1,
                                "name": "<madbg>",
                                "line": 1,
                                "column": 1,
                                "source": {"path": source or "<unknown>"},
                            }
                        ],
                        "totalFrames": 1,
                    },
                )
            )
            return

        if command == "scopes":
            self.send(
                response(
                    request_seq,
                    "scopes",
                    {
                        "scopes": [
                            {
                                "name": "Locals",
                                "variablesReference": 0,
                                "expensive": False,
                            }
                        ]
                    },
                )
            )
            return

        if command == "variables":
            self.send(
                response(
                    request_seq,
                    "variables",
                    {"variables": []},
                )
            )
            return

        if command == "evaluate":
            expression = str(arguments.get("expression", ""))
            result = ""
            if self.session:
                result = self.session.evaluate(expression)
            self.send(
                response(
                    request_seq,
                    "evaluate",
                    {
                        "result": result or "(no output)",
                        "variablesReference": 0,
                    },
                )
            )
            return

        if command in ("setBreakpoints", "setFunctionBreakpoints", "setExceptionBreakpoints"):
            self.send(response(request_seq, command, {"breakpoints": []}))
            return

        # Acknowledge unknown requests so Dappy init does not hang.
        self.send(response(request_seq, command, {}))

    def _start_session(self, request: str, arguments: dict[str, Any]) -> None:
        host = str(arguments.get("host", DEFAULT_HOST))
        port = int(arguments.get("port", DEFAULT_PORT))
        python = str(arguments.get("python") or sys.executable)
        program = str(arguments.get("program", ""))
        connect_only = bool(arguments.get("connectOnly"))

        self.session = MadbgSession(
            host=host,
            port=port,
            program=program,
            python=python,
        )
        self.session.on_output = self.emit_output
        self.session.on_stopped = self.emit_stopped
        self.session.on_terminated = self.emit_terminated

        pid = arguments.get("processId", arguments.get("pid"))
        use_set_trace = bool(arguments.get("useSetTrace", True))
        run_as_module = bool(arguments.get("runAsModule", False))
        no_post_mortem = bool(arguments.get("noPostMortem", False))
        cwd = arguments.get("cwd") or arguments.get("program.parent")
        script_args = arguments.get("args") or []

        if request == "attach":
            if connect_only or (pid is None and program == ""):
                self.session.connect_only()
            elif pid is not None:
                self.session.attach(int(pid))
            else:
                raise RuntimeError("attach requires pid/processId or connectOnly=true")
            return

        if not program:
            raise RuntimeError("launch requires program")

        self.session.launch(
            program,
            cwd=cwd,
            use_set_trace=use_set_trace,
            run_as_module=run_as_module,
            script_args=script_args,
            no_post_mortem=no_post_mortem,
        )


def main() -> None:
    bridge = MadbgDapBridge()

    def readline() -> bytes:
        return sys.stdin.buffer.readline()

    while True:
        try:
            message = read_message(readline)
        except EOFError:
            break
        if message is None:
            break
        try:
            bridge.handle(message)
        except Exception as exc:  # noqa: BLE001 — DAP bridge must stay alive
            sys.stderr.write(f"madbg-dap error: {exc}\n")
            if message.get("type") == "request":
                bridge.send(
                    response(
                        int(message["seq"]),
                        str(message.get("command", "")),
                        success=False,
                    )
                )
            bridge.emit_output(f"madbg-dap error: {exc}\n", "stderr")


if __name__ == "__main__":
    main()
