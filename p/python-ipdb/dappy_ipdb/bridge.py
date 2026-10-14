"""Stdio DAP bridge: Dappy ↔ ipdab TCP server (127.0.0.1:9000)."""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import BinaryIO

from .dap_io import iter_messages, read_message, relay, write_message


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9000


def plugin_root() -> Path:
    return Path(__file__).resolve().parent.parent


def wait_for_port(host: str, port: int, timeout: float = 120.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            try:
                sock.connect((host, port))
                return
            except OSError:
                time.sleep(0.05)
    raise TimeoutError(f"timed out waiting for ipdab at {host}:{port}")


def launch_program(
    *,
    python: str,
    program: str,
    cwd: str | None,
    host: str,
    port: int,
    script_args: list[str],
) -> subprocess.Popen[bytes]:
    env = os.environ.copy()
    env["IPDAB_HOST"] = host
    env["IPDAB_PORT"] = str(port)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(plugin_root()), env.get("PYTHONPATH", "")]
    ).strip(os.pathsep)

    cmd = [
        python,
        "-m",
        "dappy_ipdb.launcher",
        "--program",
        program,
        "--host",
        host,
        "--port",
        str(port),
        "--",
        *script_args,
    ]
    return subprocess.Popen(
        cmd,
        cwd=cwd or None,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=sys.stderr,
        stderr=sys.stderr,
    )


def connect_tcp(host: str, port: int) -> tuple[socket.socket, BinaryIO, BinaryIO]:
    sock = socket.create_connection((host, port), timeout=5)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    reader = sock.makefile("rb", buffering=0)
    writer = sock.makefile("wb", buffering=0)
    return sock, reader, writer


def extract_launch_args(
    message: dict,
) -> tuple[str, str | None, str, int, str, list[str]]:
    arguments = message.get("arguments") or {}
    program = arguments.get("program")
    if not program:
        raise ValueError("launch request missing program")

    cwd = arguments.get("cwd")
    host = str(arguments.get("host") or DEFAULT_HOST)
    port = int(arguments.get("port") or DEFAULT_PORT)
    python = str(arguments.get("python") or os.environ.get("PYTHON", "python3"))

    script_args = arguments.get("args") or []
    if not isinstance(script_args, list):
        script_args = []

    return str(program), cwd, host, port, python, [str(arg) for arg in script_args]


def forward_message(reader: BinaryIO, writer: BinaryIO, message: dict) -> dict:
    write_message(writer, message)
    while True:
        reply = read_message(reader)
        if reply is None:
            raise EOFError("ipdab closed connection during handshake")
        write_message(sys.stdout.buffer, reply)
        if reply.get("type") == "response" and reply.get("request_seq") == message.get("seq"):
            return reply


def run_bridge() -> int:
    buffered: list[dict] = []
    launch_message: dict | None = None

    for message in iter_messages(sys.stdin.buffer):
        if message.get("command") == "launch":
            launch_message = message
            break
        buffered.append(message)

    if launch_message is None:
        print("dappy_ipdb bridge: expected launch request", file=sys.stderr)
        return 2

    program, cwd, host, port, python, script_args = extract_launch_args(launch_message)
    child = launch_program(
        python=python,
        program=program,
        cwd=cwd,
        host=host,
        port=port,
        script_args=script_args,
    )

    try:
        wait_for_port(host, port)
        sock, reader, writer = connect_tcp(host, port)
    except Exception as exc:
        print(f"dappy_ipdb bridge: {exc}", file=sys.stderr)
        if child.poll() is None:
            child.terminate()
        return 1

    try:
        for message in buffered:
            forward_message(reader, writer, message)
        forward_message(reader, writer, launch_message)

        def stdin_to_tcp() -> None:
            try:
                relay(sys.stdin.buffer, writer)
            finally:
                try:
                    writer.close()
                except OSError:
                    pass

        def tcp_to_stdout() -> None:
            try:
                relay(reader, sys.stdout.buffer)
            finally:
                try:
                    reader.close()
                except OSError:
                    pass

        ingress = threading.Thread(target=stdin_to_tcp, daemon=True)
        egress = threading.Thread(target=tcp_to_stdout, daemon=True)
        ingress.start()
        egress.start()

        while ingress.is_alive() or egress.is_alive():
            if child.poll() is not None and not egress.is_alive():
                break
            time.sleep(0.05)
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
        try:
            sock.close()
        except OSError:
            pass

    return child.returncode or 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dappy stdio bridge for ipdab")
    parser.parse_args(argv)
    try:
        return run_bridge()
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
