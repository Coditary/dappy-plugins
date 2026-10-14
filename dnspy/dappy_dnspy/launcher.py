"""Launch dnSpyEx on Windows."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def main() -> None:
    if sys.platform != "win32":
        sys.stderr.write("dappy-dnspy: dnSpy is Windows-only. Use dotnet-coreclr on Linux.\n")
        raise SystemExit(1)
    dnspy = os.environ.get("DNSPY") or shutil.which("dnSpy.exe")
    if not dnspy:
        sys.stderr.write("dappy-dnspy: set DNSPY to dnSpy.exe (https://github.com/dnSpyEx/dnSpy)\n")
        raise SystemExit(1)
    program = os.environ.get("DAPPY_PROGRAM", "")
    args = [dnspy]
    if program:
        args.append(program)
    raise SystemExit(subprocess.call(args))


if __name__ == "__main__":
    main()
