"""Minimal DAP (Debug Adapter Protocol) framing over stdio."""

from __future__ import annotations

import json
import sys
from typing import Any, Callable, Optional


def read_message(readline: Callable[[], bytes]) -> Optional[dict[str, Any]]:
    """Read one DAP message using Content-Length framing."""
    header = b""
    while True:
        chunk = readline()
        if not chunk:
            return None
        header += chunk
        if header.endswith(b"\r\n\r\n"):
            break
        if len(header) > 65536:
            raise ValueError("DAP header too large")

    content_length = None
    for line in header.decode("utf-8", errors="replace").split("\r\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break
    if content_length is None:
        raise ValueError(f"missing Content-Length in DAP header: {header!r}")

    body = b""
    while len(body) < content_length:
        chunk = sys.stdin.buffer.read(content_length - len(body))
        if not chunk:
            raise EOFError("unexpected EOF while reading DAP body")
        body += chunk

    return json.loads(body.decode("utf-8"))


def write_message(obj: dict[str, Any]) -> None:
    """Write one DAP message to stdout."""
    payload = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


def response(request_seq: int, command: str, body: Optional[dict[str, Any]] = None, success: bool = True) -> dict[str, Any]:
    msg: dict[str, Any] = {
        "type": "response",
        "request_seq": request_seq,
        "success": success,
        "command": command,
        "seq": 0,
    }
    if body is not None:
        msg["body"] = body
    return msg


def event(event_name: str, body: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    msg: dict[str, Any] = {"type": "event", "event": event_name, "seq": 0}
    if body is not None:
        msg["body"] = body
    return msg
