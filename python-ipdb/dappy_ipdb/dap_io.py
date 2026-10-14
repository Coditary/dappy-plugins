"""Minimal Debug Adapter Protocol framing over a byte stream."""

from __future__ import annotations

import json
import sys
from typing import BinaryIO, Iterator


def read_message(stream: BinaryIO) -> dict | None:
    """Read one DAP message. Returns None on EOF before a complete header."""
    header = b""
    while not header.endswith(b"\r\n\r\n"):
        chunk = stream.read(1)
        if not chunk:
            return None
        header += chunk

    content_length = 0
    for line in header.decode("ascii", errors="replace").strip().split("\r\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())

    if content_length <= 0:
        return None

    body = stream.read(content_length)
    if len(body) != content_length:
        return None
    return json.loads(body.decode("utf-8"))


def write_message(stream: BinaryIO, payload: dict) -> None:
    body = json.dumps(payload, separators=(",", ":"))
    encoded = body.encode("utf-8")
    header = f"Content-Length: {len(encoded)}\r\n\r\n".encode("ascii")
    stream.write(header)
    stream.write(encoded)
    stream.flush()


def iter_messages(stream: BinaryIO) -> Iterator[dict]:
    while True:
        message = read_message(stream)
        if message is None:
            break
        yield message


def relay(src: BinaryIO, dst: BinaryIO) -> None:
    for message in iter_messages(src):
        write_message(dst, message)
