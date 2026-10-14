"""WinDbg/CDB DAP launcher (Windows)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _find_cdb() -> str | None:
    for name in ("cdb", "cdb.exe", "windbg", "windbg.exe"):
        path = shutil.which(name)
        if path:
            return path
    kits = os.environ.get("WindowsSdkDir", "")
    if kits:
        candidate = os.path.join(kits, "Debuggers", "x64", "cdb.exe")
        if os.path.isfile(candidate):
            return candidate
    return None


def main() -> None:
    if sys.platform != "win32":
        sys.stderr.write(
            "dappy-windbg-dap: WinDbg/CDB plugin requires Windows. "
            "On Linux use native-gdb or native-lldb.\n"
        )
        raise SystemExit(1)

    cdb = _find_cdb()
    if not cdb:
        sys.stderr.write(
            "dappy-windbg-dap: install Windows SDK Debugging Tools (cdb.exe)\n"
        )
        raise SystemExit(1)

    # CDB has no native DAP — launch interactive session; future: cppvsdbg bridge.
    program = os.environ.get("DAPPY_PROGRAM", "")
    dump = os.environ.get("WINDBG_DUMP", "")
    if dump:
        cmd = [cdb, "-z", dump]
    elif program:
        cmd = [cdb, "-g", "-G", program]
    else:
        sys.stderr.write("dappy-windbg-dap: set program or WINDBG_DUMP\n")
        raise SystemExit(1)

    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
