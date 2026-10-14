"""Minimal stdio DAP adapter backed by Python's bdb/pdb debugger."""

from __future__ import annotations

import bdb
import json
import os
import queue
import sys
import threading
import traceback
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


MAX_BODY = 16 * 1024 * 1024


@dataclass
class BreakpointSpec:
    path: str
    line: int


@dataclass
class DebugCommand:
    name: str
    thread_id: int = 1


class DapPdb(bdb.Bdb):
    """Non-interactive bdb driver controlled by DAP requests."""

    def __init__(self, bridge: "PdbDapAdapter") -> None:
        super().__init__()
        self.bridge = bridge
        self._active_frame: Optional[Any] = None

    def user_line(self, frame: Any) -> None:
        if not self.bridge.ready_to_run:
            return
        if self.bridge.pending_entry and self.bridge.stop_on_entry:
            self.bridge.pending_entry = False
            self._stop(frame, "entry")
            return
        if self.break_here(frame):
            self._stop(frame, "breakpoint")

    def user_breakpoint(self, frame: Any, tb: Any) -> None:
        if not self.bridge.ready_to_run:
            return
        if self.break_here(frame):
            self._stop(frame, "breakpoint")

    def user_return(self, frame: Any, return_value: Any) -> None:
        if not self.bridge.ready_to_run:
            return
        if self.bridge.step_out_pending:
            self._stop(frame, "step")

    def user_exception(self, frame: Any, exc_info: Tuple[Any, Any, Any]) -> None:
        if not self.bridge.ready_to_run:
            return
        self._stop(frame, "exception")

    def _stop(self, frame: Any, reason: str) -> None:
        self._active_frame = frame
        self.bridge.on_stopped(frame, reason)
        self._wait_for_command(frame)

    def _wait_for_command(self, frame: Any) -> None:
        while True:
            cmd = self.bridge.wait_command()
            if cmd.name == "continue":
                self.set_continue()
                self.bridge.step_out_pending = False
                return
            if cmd.name == "next":
                self.set_next(frame)
                self.bridge.step_out_pending = False
                return
            if cmd.name == "stepIn":
                self.set_step()
                self.bridge.step_out_pending = False
                return
            if cmd.name == "stepOut":
                self.set_return(frame)
                self.bridge.step_out_pending = True
                return
            if cmd.name == "pause":
                continue


class PdbDapAdapter:
    def __init__(self) -> None:
        self.seq = 1
        self.breakpoints: Dict[str, Set[int]] = {}
        self.program: Optional[str] = None
        self.cwd: Optional[str] = None
        self.python: str = sys.executable
        self.stop_on_entry = True
        self.pending_entry = True
        self.stop_reason: Optional[str] = None
        self.ready_to_run = False
        self.step_out_pending = False
        self.launch_request_seq: Optional[int] = None
        self.config_done = False
        self.debugger = DapPdb(self)
        self.current_frame: Optional[Any] = None
        self.thread_id = 1
        self._cmd_queue: queue.Queue[DebugCommand] = queue.Queue()
        self._debug_thread: Optional[threading.Thread] = None
        self._running = False
        self._terminated = False
        self._var_refs: Dict[int, Tuple[str, Any]] = {}
        self._next_var_ref = 1000

    def wait_command(self) -> DebugCommand:
        return self._cmd_queue.get()

    def on_stopped(self, frame: Any, reason: str) -> None:
        self.current_frame = frame
        self.stop_reason = reason
        self._write_event(
            "stopped",
            {
                "reason": reason,
                "threadId": self.thread_id,
                "allThreadsStopped": True,
            },
        )
        if self.launch_request_seq is not None:
            self._write_response(self.launch_request_seq, "launch", None)
            self.launch_request_seq = None

    def run_adapter(self) -> None:
        reader = sys.stdin.buffer
        while True:
            message = _read_message(reader)
            if message is None:
                break
            if message.get("type") == "response":
                continue
            if message.get("type") != "request":
                continue
            self._handle_request(message)

    def _handle_request(self, message: Dict[str, Any]) -> None:
        request_seq = int(message["seq"])
        command = message["command"]
        arguments = message.get("arguments") or {}

        if command == "initialize":
            self._write_response(
                request_seq,
                "initialize",
                {
                    "supportsConfigurationDoneRequest": True,
                    "supportsEvaluateForHovers": True,
                    "supportsSetVariable": False,
                    "supportsConditionalBreakpoints": False,
                    "supportsFunctionBreakpoints": False,
                    "supportsExceptionFilterOptions": False,
                },
            )
            return

        if command == "launch":
            self.program = arguments.get("program")
            self.cwd = arguments.get("cwd") or (
                os.path.dirname(self.program) if self.program else None
            )
            if arguments.get("python"):
                self.python = arguments["python"]
            self.stop_on_entry = bool(arguments.get("stopOnEntry", True))
            self.launch_request_seq = request_seq
            self._write_event("initialized", None)
            return

        if command == "attach":
            self.launch_request_seq = request_seq
            self._write_event("initialized", None)
            return

        if command == "setBreakpoints":
            self._apply_breakpoints(arguments)
            verified = []
            source = arguments.get("source") or {}
            path = source.get("path")
            for bp in arguments.get("breakpoints") or []:
                line = int(bp.get("line", 0))
                verified.append({"verified": bool(path and line), "line": line})
            self._write_response(
                request_seq, "setBreakpoints", {"breakpoints": verified}
            )
            return

        if command == "setExceptionBreakpoints":
            self._write_response(
                request_seq,
                "setExceptionBreakpoints",
                {"breakpoints": []},
            )
            return

        if command == "configurationDone":
            self.config_done = True
            self.ready_to_run = True
            self._write_response(request_seq, "configurationDone", None)
            self._start_debug_thread()
            return

        if command == "threads":
            self._write_response(
                request_seq,
                "threads",
                {"threads": [{"id": self.thread_id, "name": "MainThread"}]},
            )
            return

        if command in {"continue", "next", "stepIn", "stepOut", "pause"}:
            self._cmd_queue.put(DebugCommand(name=command))
            body: Dict[str, Any] = {}
            if command == "continue":
                body["allThreadsContinued"] = True
            self._write_response(request_seq, command, body or None)
            return

        if command == "stackTrace":
            frames = self._stack_frames()
            self._write_response(
                request_seq,
                "stackTrace",
                {"stackFrames": frames, "totalFrames": len(frames)},
            )
            return

        if command == "scopes":
            self._write_response(
                request_seq,
                "scopes",
                {
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
            return

        if command == "variables":
            variables = self._variables(int(arguments.get("variablesReference", 0)))
            self._write_response(request_seq, "variables", {"variables": variables})
            return

        if command == "evaluate":
            result = self._evaluate(str(arguments.get("expression", "")))
            self._write_response(
                request_seq,
                "evaluate",
                {"result": result, "variablesReference": 0},
            )
            return

        if command == "disconnect":
            self._terminate_debuggee()
            self._write_response(request_seq, "disconnect", None)
            return

        if command == "terminate":
            self._terminate_debuggee()
            self._write_response(request_seq, "terminate", None)
            return

        self._write_response(request_seq, command, None)

    def _apply_breakpoints(self, arguments: Dict[str, Any]) -> None:
        source = arguments.get("source") or {}
        path = source.get("path")
        if not path:
            return
        abs_path = os.path.abspath(path)
        lines: Set[int] = set()
        for bp in arguments.get("breakpoints") or []:
            line = int(bp.get("line", 0))
            if line > 0:
                lines.add(line)
                self.debugger.set_break(abs_path, line)
        self.breakpoints[abs_path] = lines

    def _start_debug_thread(self) -> None:
        if self._running or not self.program:
            return
        self._running = True

        def target() -> None:
            try:
                self._run_program()
            except bdb.BdbQuit:
                pass
            except Exception:
                traceback.print_exc(file=sys.stderr)
            finally:
                self._terminated = True
                if self.launch_request_seq is not None:
                    self._write_response(self.launch_request_seq, "launch", None)
                    self.launch_request_seq = None
                self._write_event("terminated", {})

        self._debug_thread = threading.Thread(target=target, name="pdb-debuggee", daemon=True)
        self._debug_thread.start()

    def _run_program(self) -> None:
        program = os.path.abspath(self.program or "")
        cwd = self.cwd or os.path.dirname(program) or os.getcwd()
        os.chdir(cwd)
        if cwd not in sys.path:
            sys.path.insert(0, cwd)

        with open(program, encoding="utf-8") as handle:
            source = handle.read()
        code = compile(source, program, "exec")
        globals_dict: Dict[str, Any] = {
            "__name__": "__main__",
            "__file__": program,
            "__package__": None,
            "__builtins__": __builtins__,
        }
        self.debugger.run(code, globals_dict, globals_dict)

    def _terminate_debuggee(self) -> None:
        self.ready_to_run = False
        try:
            self.debugger.set_quit()
        except Exception:
            pass

    def _stack_frames(self) -> List[Dict[str, Any]]:
        frame = self.current_frame
        if frame is None:
            return []
        frames: List[Dict[str, Any]] = []
        index = 0
        while frame is not None:
            index += 1
            frames.append(
                {
                    "id": index,
                    "name": frame.f_code.co_name or "<module>",
                    "line": frame.f_lineno,
                    "column": 1,
                    "source": {"path": os.path.abspath(frame.f_code.co_filename)},
                }
            )
            frame = frame.f_back
        return frames

    def _variables(self, ref: int) -> List[Dict[str, Any]]:
        frame = self.current_frame
        if frame is None:
            return []
        mapping = frame.f_locals if ref == 1 else frame.f_globals if ref == 2 else None
        if mapping is None:
            stored = self._var_refs.get(ref)
            if stored is None:
                return []
            _, value = stored
            return self._expand_value(value)
        return self._expand_mapping(mapping)

    def _expand_mapping(self, mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
        variables: List[Dict[str, Any]] = []
        for name in sorted(mapping):
            if name.startswith("__") and name.endswith("__"):
                continue
            variables.append(self._format_variable(name, mapping[name]))
        return variables

    def _expand_value(self, value: Any) -> List[Dict[str, Any]]:
        if isinstance(value, dict):
            return [
                self._format_variable(str(key), val) for key, val in sorted(value.items())
            ]
        if isinstance(value, (list, tuple, set)):
            return [
                self._format_variable(str(index), item)
                for index, item in enumerate(list(value)[:200])
            ]
        return []

    def _format_variable(self, name: str, value: Any) -> Dict[str, Any]:
        var_type = type(value).__name__
        if isinstance(value, (dict, list, tuple, set)) and len(value) > 0:
            ref = self._next_var_ref
            self._next_var_ref += 1
            self._var_refs[ref] = (name, value)
            return {
                "name": name,
                "value": _safe_repr(value),
                "type": var_type,
                "variablesReference": ref,
            }
        return {
            "name": name,
            "value": _safe_repr(value),
            "type": var_type,
            "variablesReference": 0,
        }

    def _evaluate(self, expression: str) -> str:
        frame = self.current_frame
        if frame is None:
            return ""
        try:
            value = eval(expression, frame.f_globals, frame.f_locals)
        except Exception as exc:
            return f"<{exc.__class__.__name__}: {exc}>"
        return _safe_repr(value)

    def _write_response(
        self, request_seq: int, command: str, body: Optional[Dict[str, Any]]
    ) -> None:
        payload: Dict[str, Any] = {
            "type": "response",
            "seq": self._next_seq(),
            "requestSeq": request_seq,
            "success": True,
            "command": command,
        }
        if body is not None:
            payload["body"] = body
        _write_message(payload)

    def _write_event(self, event: str, body: Optional[Dict[str, Any]]) -> None:
        payload: Dict[str, Any] = {
            "type": "event",
            "seq": self._next_seq(),
            "event": event,
        }
        if body is not None:
            payload["body"] = body
        _write_message(payload)

    def _next_seq(self) -> int:
        value = self.seq
        self.seq += 1
        return value


def _safe_repr(value: Any, limit: int = 512) -> str:
    try:
        text = repr(value)
    except Exception:
        text = f"<{type(value).__name__}>"
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def _read_message(reader: Any) -> Optional[Dict[str, Any]]:
    content_length: Optional[int] = None
    while True:
        line = reader.readline()
        if not line:
            return None
        stripped = line.decode("ascii", errors="replace").strip()
        if not stripped:
            break
        lower = stripped.lower()
        if lower.startswith("content-length:"):
            content_length = int(stripped.split(":", 1)[1].strip())
    if content_length is None:
        raise RuntimeError("missing Content-Length header")
    if content_length > MAX_BODY:
        raise RuntimeError("Content-Length too large")
    body = reader.read(content_length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def _write_message(payload: Dict[str, Any]) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def run_adapter() -> None:
    PdbDapAdapter().run_adapter()
