"""Omniscient Debugger (TOD) launcher for Java time-travel debugging."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    tod_home = os.environ.get("TOD_HOME", "")
    tod_bin = None
    if tod_home:
        candidate = Path(tod_home) / "bin" / "tod"
        if candidate.is_file():
            tod_bin = str(candidate)
    tod_bin = tod_bin or shutil.which("tod")
    if not tod_bin:
        sys.stderr.write(
            "dappy-java-tod: install Omniscient Debugger and set TOD_HOME\n"
            "  https://github.com/OmniscientDebugger/OmniscientDebugger\n"
        )
        raise SystemExit(1)
    program = os.environ.get("DAPPY_PROGRAM", "")
    args = [tod_bin]
    if program:
        args.append(program)
    raise SystemExit(subprocess.call(args))


if __name__ == "__main__":
    main()
