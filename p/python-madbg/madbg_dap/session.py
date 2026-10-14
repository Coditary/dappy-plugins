"""Manage madbg TCP sessions (launch, attach, connect)."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from madbg.communication import send_message

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 0xDB9  # 3513
CONNECT_TIMEOUT = 30.0

# IPython / pdb prompt heuristics
_PROMPT_MARKERS = (
    b"(Pdb)",
    b"ipdb>",
    b"-->",
    b"... ",
)


@dataclass
class MadbgSession:
    """One madbg debug session bridged to DAP."""

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    program: str = ""
    python: str = field(default_factory=lambda: sys.executable)
    process: Optional[subprocess.Popen] = None
    socket: Optional[socket.socket] = None
    relay_thread: Optional[threading.Thread] = None
    running: bool = False
    stopped: bool = False
    output_buffer: str = ""
    on_output: Optional[Callable[[str, str], None]] = None
    on_stopped: Optional[Callable[[str], None]] = None
    on_terminated: Optional[Callable[[], None]] = None
    _write_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _stop_relay: threading.Event = field(default_factory=threading.Event, repr=False)

    def launch(
        self,
        program: str,
        *,
        cwd: Optional[str] = None,
        use_set_trace: bool = True,
        run_as_module: bool = False,
        script_args: Optional[list[str]] = None,
        no_post_mortem: bool = False,
    ) -> None:
        self.program = program
        cmd = [
            self.python,
            "-m",
            "madbg",
            "run",
            "-i",
            self.host,
            "-p",
            str(self.port),
        ]
        if use_set_trace:
            cmd.append("-s")
        if no_post_mortem:
            cmd.append("-n")
        if run_as_module:
            cmd.append("-m")
        cmd.append(program)
        if script_args:
            cmd.extend(script_args)

        self.process = subprocess.Popen(
            cmd,
            cwd=cwd or None,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._start_stderr_reader()
        self._wait_for_server()
        self._connect()

    def attach(self, pid: int) -> None:
        """Inject madbg into a running process, then connect."""
        from madbg.api import _inject_set_trace

        _inject_set_trace(int(pid), self.host, self.port)
        self._wait_for_server()
        self._connect()

    def connect_only(self) -> None:
        """Connect to an already listening madbg server (set_trace / madbg connect)."""
        self._connect()

    def send_command(self, command: str) -> None:
        """Send a debugger command line to madbg."""
        if not self.socket:
            raise RuntimeError("not connected to madbg")
        payload = command if command.endswith("\n") else f"{command}\n"
        data = payload.encode("utf-8", errors="replace")
        with self._write_lock:
            self.socket.sendall(data)

    def continue_execution(self) -> None:
        self.stopped = False
        self.send_command("c")

    def step_over(self) -> None:
        self.stopped = False
        self.send_command("n")

    def step_in(self) -> None:
        self.stopped = False
        self.send_command("s")

    def step_out(self) -> None:
        self.stopped = False
        self.send_command("r")

    def evaluate(self, expression: str) -> str:
        marker = f"__madbg_eval_{time.time_ns()}"
        self.output_buffer = ""
        self.send_command(f"{expression}")
        deadline = time.time() + 5.0
        while time.time() < deadline:
            if self.stopped or self._looks_like_prompt(self.output_buffer):
                break
            time.sleep(0.05)
        return self.output_buffer.strip()

    def disconnect(self, terminate: bool = False) -> None:
        self._stop_relay.set()
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self.socket.close()
            except OSError:
                pass
            self.socket = None
        if terminate and self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.running = False

    def _start_stderr_reader(self) -> None:
        if not self.process or not self.process.stderr:
            return

        def reader() -> None:
            assert self.process and self.process.stderr
            for line in iter(self.process.stderr.readline, b""):
                text = line.decode("utf-8", errors="replace")
                if self.on_output:
                    self.on_output(text, "stderr")
            if self.process and self.process.poll() is not None and self.on_terminated:
                self.on_terminated()

        threading.Thread(target=reader, name="madbg-stderr", daemon=True).start()

    def _wait_for_server(self, timeout: float = CONNECT_TIMEOUT) -> None:
        deadline = time.time() + timeout
        last_error: Optional[Exception] = None
        while time.time() < deadline:
            if self.process and self.process.poll() is not None:
                raise RuntimeError(
                    f"madbg run exited early with code {self.process.returncode}"
                )
            try:
                probe = socket.create_connection((self.host, self.port), timeout=0.5)
                probe.close()
                return
            except OSError as exc:
                last_error = exc
                time.sleep(0.1)
        raise TimeoutError(
            f"madbg server not reachable at {self.host}:{self.port} ({last_error})"
        )

    def _connect(self) -> None:
        sock = socket.create_connection((self.host, self.port), timeout=CONNECT_TIMEOUT)
        term_data = {
            "term_attrs": self._default_term_attrs(),
            "term_type": os.environ.get("TERM", "dumb"),
            "term_size": (24, 80),
        }
        send_message(sock, term_data)
        self.socket = sock
        self.running = True
        self._stop_relay.clear()
        self.relay_thread = threading.Thread(
            target=self._relay_loop, name="madbg-relay", daemon=True
        )
        self.relay_thread.start()

    def _relay_loop(self) -> None:
        assert self.socket
        sock = self.socket
        sock.settimeout(0.2)
        pending = b""
        while not self._stop_relay.is_set():
            try:
                chunk = sock.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            if not chunk:
                break
            pending += chunk
            text = pending.decode("utf-8", errors="replace")
            self.output_buffer += text
            if self.on_output:
                self.on_output(text, "stdout")
            if not self.stopped and self._looks_like_prompt(pending):
                self.stopped = True
                if self.on_stopped:
                    self.on_stopped("breakpoint")
            pending = b""

        self.running = False
        if self.on_terminated:
            self.on_terminated()

    @staticmethod
    def _looks_like_prompt(data: bytes | str) -> bool:
        blob = data if isinstance(data, bytes) else data.encode("utf-8", errors="replace")
        trimmed = blob.rstrip()
        return any(trimmed.endswith(marker) for marker in _PROMPT_MARKERS)

    @staticmethod
    def _default_term_attrs() -> list:
        """Minimal termios-like attrs for headless clients."""
        # [iflag, oflag, cflag, lflag, ispeed, ospeed, cc...]
        cc = [0] * 32
        cc[6] = 3  # VEOF
        cc[7] = 8  # VEOL
        return [0, 0, 0, 0, 0, 0, *cc]
