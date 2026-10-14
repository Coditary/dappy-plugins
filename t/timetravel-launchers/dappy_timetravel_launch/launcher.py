"""Launchers for time-travel and record/replay debuggers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-timetravel-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_undo_live_recorder() -> int:
    undo = os.environ.get("UNDO_RECORD") or shutil.which("undodb-record") or shutil.which("live-record")
    program = _program()
    if undo and program:
        return _run([undo, program])
    return _info(
        "Undo LiveRecorder",
        [
            "Commercial time-travel debugger for Linux C/C++/Go/Java.",
            "Records production crashes for rewind/replay debugging.",
            "https://undo.io/ — set UNDO_RECORD to recorder binary.",
        ],
    )


def launch_pernosco() -> int:
    rr = shutil.which("rr")
    program = _program()
    if rr and program:
        return _info(
            "Pernosco",
            [
                f"rr available — record locally: rr record {program}",
                "Upload trace to Pernosco for collaborative web UI.",
                "https://pernos.co/ — builds on rr time-travel.",
                "For local DAP use rr-replay plugin.",
            ],
        )
    return _info(
        "Pernosco",
        [
            "Web-based collaborative rr trace analysis.",
            "Install rr, record crash, upload to Pernosco.",
            "Local alternative: dap-cli debug repl --adapter rr-replay",
        ],
    )


_HANDLERS = {
    "undo-live-recorder": launch_undo_live_recorder,
    "pernosco": launch_pernosco,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-timetravel-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
