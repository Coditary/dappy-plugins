"""Launch RemedyBG on Windows (no public DAP API)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def main() -> None:
    if sys.platform != "win32":
        sys.stderr.write(
            "dappy-remedybg: RemedyBG is Windows-only. Use native-lldb on macOS/Linux.\n"
        )
        raise SystemExit(1)

    remedy = os.environ.get("REMEDYBG") or shutil.which("RemedyBG.exe")
    if not remedy or not os.path.isfile(remedy):
        sys.stderr.write(
            "dappy-remedybg: set REMEDYBG to RemedyBG.exe path "
            "(https://remedybg.com)\n"
        )
        raise SystemExit(1)

    program = os.environ.get("DAPPY_PROGRAM", "")
    if not program:
        sys.stderr.write("dappy-remedybg: program path required\n")
        raise SystemExit(1)

    # RemedyBG CLI: open binary in standalone debugger window.
    raise SystemExit(subprocess.call([remedy, program]))


if __name__ == "__main__":
    main()
