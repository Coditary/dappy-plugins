"""Trepan remote TCP client (comcodes + length-prefixed messages)."""

from __future__ import annotations

import re
import socket
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

TCP_MAX_PACKET = 8192
LOG_MAX_MSG = 4

PRINT = "."
COMMAND = "C"
CONFIRM_TRUE = "Y"
CONFIRM_FALSE = "N"
CONFIRM_REPLY = "?"
QUIT = "q"
PROMPT = "p"
SYNC = "s"
RESTART = "r"

PROMPT_RE = re.compile(
    r"^\((?P<path>[^:)]+):(?P<line>\d+)\s*@\d+\):\s*(?P<name>.*)$"
)
FRAME_RE = re.compile(
    r"^\s*(?P<index>\d+)\s+(?P<name>\S+)?\s*file\s+'(?P<path>[^']+)'\s+at\s+line\s+(?P<line>\d+)"
)


def pack_msg(msg: str) -> bytes:
    byte_msg = msg.encode("utf-8")
    header = f"{len(byte_msg):0{LOG_MAX_MSG}d}".encode("ascii")
    return header + byte_msg


def unpack_msg(buf: bytes) -> Tuple[bytes, bytes]:
    if not buf:
        return b"", b"q"
    length = int(buf[:LOG_MAX_MSG].decode("ascii"))
    data = buf[LOG_MAX_MSG : LOG_MAX_MSG + length]
    rest = buf[LOG_MAX_MSG + length :]
    return rest, data


@dataclass
class StopLocation:
    path: str
    line: int
    name: str = "<module>"


@dataclass
class StackFrame:
    id: int
    name: str
    path: str
    line: int


@dataclass
class TrepanClient:
    host: str = "127.0.0.1"
    port: int = 1955
    _sock: Optional[socket.socket] = field(default=None, init=False, repr=False)
    _buf: bytes = field(default=b"", init=False, repr=False)
    _output: List[str] = field(default_factory=list, init=False, repr=False)
    stop_location: Optional[StopLocation] = field(default=None, init=False, repr=False)

    def connect(self, timeout: float = 30.0) -> None:
        deadline = time.time() + timeout
        last_error: Optional[OSError] = None
        while time.time() < deadline:
            try:
                sock = socket.create_connection((self.host, self.port), timeout=1.0)
                sock.settimeout(2.0)
                self._sock = sock
                return
            except OSError as exc:
                last_error = exc
                time.sleep(0.1)
        raise ConnectionError(
            f"could not connect to trepan server at {self.host}:{self.port}: {last_error}"
        )

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None

    def _read_msg(self) -> str:
        assert self._sock is not None
        while True:
            if len(self._buf) >= LOG_MAX_MSG:
                self._buf, data = unpack_msg(self._buf)
                if data:
                    return data.decode("utf-8", errors="replace")
            chunk = self._sock.recv(TCP_MAX_PACKET)
            if not chunk:
                raise EOFError("trepan server closed connection")
            self._buf += chunk

    def _write_line(self, code: str, msg: str = "") -> None:
        assert self._sock is not None
        payload = pack_msg(code + msg)
        view = memoryview(payload)
        while view:
            sent = self._sock.send(view)
            view = view[sent:]

    def _drain_until_prompt(self, command: str, timeout: float = 30.0) -> List[str]:
        deadline = time.time() + timeout
        lines: List[str] = []
        while time.time() < deadline:
            control, remote = self._read_remote()
            if control == PRINT:
                if remote:
                    lines.append(remote.rstrip("\n"))
            elif control in (CONFIRM_TRUE, CONFIRM_FALSE):
                default = control == CONFIRM_TRUE
                answer = "Y" if default else "N"
                self._write_line(CONFIRM_REPLY, answer)
            elif control == PROMPT:
                prompt_text = remote.rstrip("\n")
                match = PROMPT_RE.match(prompt_text)
                if match:
                    self.stop_location = StopLocation(
                        path=match.group("path"),
                        line=int(match.group("line")),
                        name=match.group("name").strip() or "<module>",
                    )
                self._write_line(CONFIRM_REPLY, command)
                return lines
            elif control == QUIT:
                raise EOFError("trepan session ended")
            elif control == RESTART:
                raise RuntimeError("trepan requested restart; not supported by DAP bridge")
            else:
                if remote:
                    lines.append(remote.rstrip("\n"))
        raise TimeoutError(f"trepan did not respond to command: {command}")

    def _read_remote(self) -> Tuple[str, str]:
        coded = self._read_msg()
        if not coded:
            raise EOFError("empty trepan message")
        return coded[0], coded[1:]

    def wait_for_initial_prompt(self, timeout: float = 60.0) -> StopLocation:
        deadline = time.time() + timeout
        while time.time() < deadline:
            control, remote = self._read_remote()
            if control == PRINT:
                continue
            if control == PROMPT:
                match = PROMPT_RE.match(remote.rstrip("\n"))
                if match:
                    self.stop_location = StopLocation(
                        path=match.group("path"),
                        line=int(match.group("line")),
                        name=match.group("name").strip() or "<module>",
                    )
                return self.stop_location or StopLocation("<unknown>", 1)
            if control == QUIT:
                raise EOFError("trepan exited before initial stop")
        raise TimeoutError("timed out waiting for trepan initial prompt")

    def command(self, text: str, timeout: float = 30.0) -> str:
        output = self._drain_until_prompt(text.strip(), timeout=timeout)
        return "\n".join(output).strip()

    def set_breakpoint(self, path: str, line: int) -> None:
        self.command(f"break {path}:{line}")

    def clear_breakpoints(self) -> None:
        self.command("delete -y")

    def continue_execution(self) -> None:
        self._drain_until_prompt("continue")

    def step_over(self) -> None:
        self._drain_until_prompt("next")

    def step_in(self) -> None:
        self._drain_until_prompt("step")

    def step_out(self) -> None:
        self._drain_until_prompt("finish")

    def parse_backtrace(self, text: str) -> List[StackFrame]:
        frames: List[StackFrame] = []
        for line in text.splitlines():
            match = FRAME_RE.search(line)
            if not match:
                continue
            frames.append(
                StackFrame(
                    id=int(match.group("index")) + 1,
                    name=match.group("name") or "<module>",
                    path=match.group("path"),
                    line=int(match.group("line")),
                )
            )
        if not frames and self.stop_location:
            frames.append(
                StackFrame(
                    id=1,
                    name=self.stop_location.name,
                    path=self.stop_location.path,
                    line=self.stop_location.line,
                )
            )
        return frames

    def backtrace(self) -> List[StackFrame]:
        text = self.command("backtrace")
        return self.parse_backtrace(text)
