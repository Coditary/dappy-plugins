"""DAP bridge: stdio DAP on the Dappy side, trepan TCP on the debugger side."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from typing import Any, Dict, List, Optional

from dappy_trepan2.dap_protocol import DapWriter, log_stderr, read_message
from dappy_trepan2.trepan_io import StackFrame, StopLocation, TrepanClient


class TrepanDapBridge:
    def __init__(self) -> None:
        self._writer = DapWriter(sys.stdout.buffer)
        self._client: Optional[TrepanClient] = None
        self._server_proc: Optional[subprocess.Popen] = None
        self._program: str = ""
        self._thread_id = 1
        self._breakpoints: Dict[str, List[int]] = {}
        self._initialized = False
        self._running = False
        self._stop_lock = threading.Lock()

    def run(self) -> None:
        while True:
            message = read_message(sys.stdin.buffer)
            if message is None:
                break
            self._handle(message)

    def _handle(self, message: Dict[str, Any]) -> None:
        msg_type = message.get("type")
        if msg_type == "request":
            self._handle_request(message)
        elif msg_type == "response":
            pass
        elif msg_type == "event":
            pass

    def _handle_request(self, request: Dict[str, Any]) -> None:
        command = request.get("command", "")
        seq = int(request.get("seq", 0))
        args = request.get("arguments") or {}

        handlers = {
            "initialize": self._on_initialize,
            "launch": self._on_launch,
            "attach": self._on_attach,
            "setBreakpoints": self._on_set_breakpoints,
            "configurationDone": self._on_configuration_done,
            "continue": self._on_continue,
            "next": self._on_next,
            "stepIn": self._on_step_in,
            "stepOut": self._on_step_out,
            "threads": self._on_threads,
            "stackTrace": self._on_stack_trace,
            "scopes": self._on_scopes,
            "variables": self._on_variables,
            "evaluate": self._on_evaluate,
            "disconnect": self._on_disconnect,
            "terminate": self._on_terminate,
        }
        handler = handlers.get(command)
        if handler is None:
            self._writer.response(seq, command, success=False, message=f"unsupported: {command}")
            return
        try:
            handler(seq, args)
        except Exception as exc:  # noqa: BLE001 - DAP boundary
            log_stderr(f"error handling {command}: {exc}")
            self._writer.response(seq, command, success=False, message=str(exc))

    def _on_initialize(self, seq: int, args: Dict[str, Any]) -> None:
        del args
        self._writer.response(
            seq,
            "initialize",
            body={
                "supportsConfigurationDoneRequest": True,
                "supportsEvaluateForHovers": True,
                "supportsStepBack": False,
                "supportsSetVariable": False,
                "supportsConditionalBreakpoints": False,
                "supportsFunctionBreakpoints": False,
            },
        )
        self._writer.event("initialized", {})
        self._initialized = True

    def _on_launch(self, seq: int, args: Dict[str, Any]) -> None:
        program = args.get("program") or args.get("programPath")
        if not program:
            raise ValueError("launch requires program")
        self._program = os.path.abspath(program)
        host = args.get("host", "127.0.0.1")
        port = int(args.get("port", 0) or 0)
        cwd = args.get("cwd") or os.path.dirname(self._program) or os.getcwd()
        script_args = args.get("args") or []

        if port <= 0:
            port = self._pick_port()

        actual_port = self._start_server(port, self._program, script_args, cwd)
        self._client = TrepanClient(host=host, port=actual_port)
        self._client.connect()
        self._client.wait_for_initial_prompt()
        self._apply_pending_breakpoints()
        self._emit_stopped("launch")
        self._writer.response(seq, "launch")

    def _on_attach(self, seq: int, args: Dict[str, Any]) -> None:
        host = args.get("host", "127.0.0.1")
        port = int(args.get("port", 1955))
        self._program = os.path.abspath(args.get("program") or args.get("programPath") or "")
        self._client = TrepanClient(host=host, port=port)
        self._client.connect()
        self._client.wait_for_initial_prompt()
        self._apply_pending_breakpoints()
        self._emit_stopped("attach")
        self._writer.response(seq, "attach")

    def _on_set_breakpoints(self, seq: int, args: Dict[str, Any]) -> None:
        source = args.get("source") or {}
        path = source.get("path") or self._program
        if not path:
            raise ValueError("setBreakpoints requires source.path")
        requested = args.get("breakpoints") or []
        lines = [int(item["line"]) for item in requested if "line" in item]
        self._breakpoints[path] = lines
        if self._client is not None:
            self._apply_breakpoints_for_path(path, lines)
        verified = [{"id": idx + 1, "verified": True, "line": line} for idx, line in enumerate(lines)]
        self._writer.response(seq, "setBreakpoints", body={"breakpoints": verified})

    def _on_configuration_done(self, seq: int, _args: Dict[str, Any]) -> None:
        self._writer.response(seq, "configurationDone")

    def _on_continue(self, seq: int, args: Dict[str, Any]) -> None:
        del args
        client = self._require_client()
        self._running = True
        self._writer.response(seq, "continue", body={"allThreadsContinued": True})
        threading.Thread(target=self._continue_worker, args=(client,), daemon=True).start()

    def _continue_worker(self, client: TrepanClient) -> None:
        try:
            client.continue_execution()
            self._running = False
            self._emit_stopped("breakpoint")
        except Exception as exc:  # noqa: BLE001
            log_stderr(f"continue failed: {exc}")
            self._running = False
            self._writer.event("terminated", {})

    def _on_next(self, seq: int, _args: Dict[str, Any]) -> None:
        client = self._require_client()
        client.step_over()
        self._emit_stopped("step")
        self._writer.response(seq, "next")

    def _on_step_in(self, seq: int, _args: Dict[str, Any]) -> None:
        client = self._require_client()
        client.step_in()
        self._emit_stopped("step")
        self._writer.response(seq, "stepIn")

    def _on_step_out(self, seq: int, _args: Dict[str, Any]) -> None:
        client = self._require_client()
        client.step_out()
        self._emit_stopped("step")
        self._writer.response(seq, "stepOut")

    def _on_threads(self, seq: int, _args: Dict[str, Any]) -> None:
        self._writer.response(
            seq,
            "threads",
            body={"threads": [{"id": self._thread_id, "name": "MainThread"}]},
        )

    def _on_stack_trace(self, seq: int, _args: Dict[str, Any]) -> None:
        client = self._require_client()
        frames = client.backtrace()
        self._writer.response(
            seq,
            "stackTrace",
            body={
                "stackFrames": [self._frame_to_dap(frame) for frame in frames],
                "totalFrames": len(frames),
            },
        )

    def _on_scopes(self, seq: int, args: Dict[str, Any]) -> None:
        del args
        self._writer.response(
            seq,
            "scopes",
            body={
                "scopes": [
                    {
                        "name": "Locals",
                        "variablesReference": 1,
                        "expensive": False,
                    },
                    {
                        "name": "Globals",
                        "variablesReference": 2,
                        "expensive": True,
                    },
                ]
            },
        )

    def _on_variables(self, seq: int, args: Dict[str, Any]) -> None:
        client = self._require_client()
        ref = int(args.get("variablesReference", 0))
        if ref == 1:
            text = client.command("info locals")
            variables = self._parse_info_locals(text)
        elif ref == 2:
            text = client.command("info globals")
            variables = self._parse_info_locals(text)
        else:
            variables = []
        self._writer.response(seq, "variables", body={"variables": variables})

    def _on_evaluate(self, seq: int, args: Dict[str, Any]) -> None:
        client = self._require_client()
        expression = args.get("expression", "")
        text = client.command(f"eval {expression}")
        self._writer.response(
            seq,
            "evaluate",
            body={"result": text or "", "variablesReference": 0},
        )

    def _on_disconnect(self, seq: int, _args: Dict[str, Any]) -> None:
        self._shutdown()
        self._writer.response(seq, "disconnect")

    def _on_terminate(self, seq: int, _args: Dict[str, Any]) -> None:
        self._shutdown()
        self._writer.response(seq, "terminate")
        self._writer.event("terminated", {})

    def _require_client(self) -> TrepanClient:
        if self._client is None:
            raise RuntimeError("no active trepan session")
        return self._client

    def _pick_port(self) -> int:
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def _start_server(
        self,
        port: int,
        program: str,
        script_args: List[Any],
        cwd: str,
    ) -> int:
        python2 = os.environ.get("PYTHON2", "python2")
        cmd = [
            python2,
            "-m",
            "dappy_trepan2.server_launcher",
            str(port),
            program,
            *[str(arg) for arg in script_args],
        ]
        log_stderr(f"spawning trepan2 server: {' '.join(cmd)}")
        env = os.environ.copy()
        plugin_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        env["PYTHONPATH"] = plugin_root + os.pathsep + env.get("PYTHONPATH", "")
        self._server_proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
        )
        assert self._server_proc.stdout is not None
        actual_port = port
        deadline = time.time() + 60.0
        while time.time() < deadline:
            line = self._server_proc.stdout.readline()
            if not line:
                if self._server_proc.poll() is not None:
                    err = (self._server_proc.stderr.read() if self._server_proc.stderr else "") or ""
                    raise RuntimeError(f"trepan server exited early: {err.strip()}")
                time.sleep(0.05)
                continue
            line = line.strip()
            if line.startswith("TREPAN_SERVER_PORT="):
                actual_port = int(line.split("=", 1)[1])
                log_stderr(f"trepan listening on port {actual_port}")
                return actual_port
        raise TimeoutError("timed out waiting for trepan server port")

    def _apply_pending_breakpoints(self) -> None:
        client = self._require_client()
        try:
            client.clear_breakpoints()
        except Exception:  # noqa: BLE001
            pass
        for path, lines in self._breakpoints.items():
            self._apply_breakpoints_for_path(path, lines)

    def _apply_breakpoints_for_path(self, path: str, lines: List[int]) -> None:
        client = self._require_client()
        for line in lines:
            client.set_breakpoint(path, line)

    def _emit_stopped(self, reason: str) -> None:
        with self._stop_lock:
            client = self._client
            location = client.stop_location if client else None
            body: Dict[str, Any] = {
                "reason": reason,
                "threadId": self._thread_id,
                "allThreadsStopped": True,
            }
            if location:
                body["description"] = f"{location.name} at {location.path}:{location.line}"
            self._writer.event("stopped", body)

    def _frame_to_dap(self, frame: StackFrame) -> Dict[str, Any]:
        return {
            "id": frame.id,
            "name": frame.name,
            "line": frame.line,
            "column": 1,
            "source": {"path": frame.path},
        }

    @staticmethod
    def _parse_info_locals(text: str) -> List[Dict[str, Any]]:
        variables: List[Dict[str, Any]] = []
        ref = 100
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                name, value = stripped.split("=", 1)
                variables.append(
                    {
                        "name": name.strip(),
                        "value": value.strip(),
                        "variablesReference": 0,
                    }
                )
            else:
                variables.append(
                    {
                        "name": f"item_{ref}",
                        "value": stripped,
                        "variablesReference": 0,
                    }
                )
                ref += 1
        return variables

    def _shutdown(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception:  # noqa: BLE001
                pass
            self._client = None
        if self._server_proc is not None:
            self._server_proc.terminate()
            try:
                self._server_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._server_proc.kill()
            self._server_proc = None


def main() -> None:
    TrepanDapBridge().run()


if __name__ == "__main__":
    main()
