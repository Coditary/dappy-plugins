"""Launch ILSpy on Windows."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def main() -> None:
    if sys.platform != "win32":
        sys.stderr.write("dappy-ilspy: ILSpy is primarily Windows/.NET. Use dnspy or dotnet-coreclr.\n")
        raise SystemExit(1)
    ilspy = os.environ.get("ILSPY") or shutil.which("ILSpy.exe")
    if not ilspy:
        sys.stderr.write("dappy-ilspy: set ILSPY to ILSpy.exe\n")
        raise SystemExit(1)
    program = os.environ.get("DAPPY_PROGRAM", "")
    args = [ilspy]
    if program:
        args.extend(["/navigateTo", program])
    raise SystemExit(subprocess.call(args))


if __name__ == "__main__":
    main()
