"""Minimal Debug Adapter Protocol (DAP) stdio framing."""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Optional


MAX_BODY = 16 * 1024 * 1024


def read_message(stream) -> Optional[Dict[str, Any]]:
    content_length: Optional[int] = None
    while True:
        line = stream.readline()
        if not line:
            return None
        trimmed = line.decode("utf-8", errors="replace").strip("\r\n")
        if not trimmed:
            break
        lower = trimmed.lower()
        if lower.startswith("content-length:"):
            content_length = int(trimmed.split(":", 1)[1].strip())
    if content_length is None:
        raise ValueError("missing Content-Length header")
    if content_length > MAX_BODY:
        raise ValueError("Content-Length too large")
    body = stream.read(content_length)
    if len(body) != content_length:
        return None
    return json.loads(body.decode("utf-8"))


def write_message(stream, value: Dict[str, Any]) -> None:
    body = json.dumps(value, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    stream.write(header)
    stream.write(body)
    stream.flush()


class DapWriter:
    def __init__(self, stream, seq_start: int = 1) -> None:
        self._stream = stream
        self._seq = seq_start

    def next_seq(self) -> int:
        value = self._seq
        self._seq += 1
        return value

    def send(self, value: Dict[str, Any]) -> None:
        write_message(self._stream, value)

    def response(
        self,
        request_seq: int,
        command: str,
        body: Optional[Dict[str, Any]] = None,
        success: bool = True,
        message: Optional[str] = None,
    ) -> None:
        payload: Dict[str, Any] = {
            "type": "response",
            "seq": self.next_seq(),
            "requestSeq": request_seq,
            "success": success,
            "command": command,
        }
        if body is not None:
            payload["body"] = body
        if message is not None:
            payload["message"] = message
        self.send(payload)

    def event(self, event: str, body: Optional[Dict[str, Any]] = None) -> None:
        payload: Dict[str, Any] = {
            "type": "event",
            "seq": self.next_seq(),
            "event": event,
        }
        if body is not None:
            payload["body"] = body
        self.send(payload)


def log_stderr(message: str) -> None:
    print(message, file=sys.stderr, flush=True)
