"""Launchers for historic and OS-specific debuggers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _stub(name: str, message: str) -> int:
    sys.stderr.write(f"dappy-historic-launch [{name}]: {message}\n")
    return 1


def launch_macsbug() -> int:
    return _stub(
        "MacsBug",
        "Classic Mac OS only (pre-OS X). Use native-lldb or ghidra for modern macOS binaries.",
    )


def launch_softice() -> int:
    if sys.platform != "win32":
        return _stub("SoftICE", "Windows NT/9x kernel debugger — discontinued. Use windbg-cdb.")
    return _stub(
        "SoftICE",
        "Discontinued. Use x64dbg or windbg-cdb for modern Windows kernel debugging.",
    )


def launch_codeview() -> int:
    cv = os.environ.get("CODEVIEW") or shutil.which("cv.exe")
    if cv and sys.platform == "win32":
        args = [cv]
        program = _program()
        if program:
            args.append(program)
        return subprocess.call(args)
    return _stub("CodeView", "MS-DOS CodeView — run in DOSBox or set CODEVIEW path on Windows.")


def launch_dos_debug() -> int:
    debug = os.environ.get("DOS_DEBUG") or shutil.which("debug.exe")
    if debug and sys.platform == "win32":
        return subprocess.call([debug, _program()] if _program() else [debug])
    return _stub(
        "DEBUG.COM",
        "MS-DOS DEBUG — use DOSBox: `debug program.com` or `td` (Turbo Debugger).",
    )


def launch_turbo_debugger() -> int:
    td = os.environ.get("TURBO_DEBUGGER") or shutil.which("td.exe") or shutil.which("td")
    if td:
        args = [td]
        program = _program()
        if program:
            args.append(program)
        return subprocess.call(args)
    return _stub(
        "Turbo Debugger",
        "Install Borland Turbo Debugger (td/td32) or set TURBO_DEBUGGER.",
    )


def launch_mdb() -> int:
    mdb = shutil.which("mdb") or shutil.which("kmdb")
    if not mdb:
        return _stub("MDB", "Solaris/illumos Modular Debugger — install on illumos/Solaris.")
    program = _program()
    args = [mdb]
    if program:
        args.extend(["-k"] if program.endswith(".dump") else [program])
    return subprocess.call(args)


def launch_kadb_ddb() -> int:
    for cmd in ("ddb", "kadb", "kgdb"):
        path = shutil.which(cmd)
        if path:
            return subprocess.call([path])
    return _stub(
        "KADB/DDB",
        "BSD in-kernel debugger — boot with -d or enter from panic on FreeBSD/NetBSD.",
    )


def launch_affinic() -> int:
    affinic = os.environ.get("AFFINIC") or shutil.which("affinic")
    gdb = shutil.which("gdb")
    if affinic:
        args = [affinic]
        program = _program()
        if program:
            args.append(program)
        return subprocess.call(args)
    if gdb and sys.platform == "linux":
        return _stub(
            "Affinic",
            "Affinic not found — fallback: use native-gdb or ddd with GDB.",
        )
    return _stub("Affinic", "Linux graphical GDB UI — set AFFINIC or use ddd plugin.")


def launch_ddd() -> int:
    ddd = shutil.which("ddd")
    if not ddd:
        return _stub("DDD", "Install ddd package (Data Display Debugger).")
    program = _program()
    gdb = shutil.which("gdb") or "gdb"
    args = [ddd, "--gdb", gdb]
    if program:
        args.append(program)
    return subprocess.call(args)


def launch_ups() -> int:
    ups = shutil.which("ups") or shutil.which("xups")
    if not ups:
        return _stub("Ups", "Install ups (X11 source-level C/Fortran debugger).")
    args = [ups]
    program = _program()
    if program:
        args.append(program)
    return subprocess.call(args)


def launch_xminidump() -> int:
    if sys.platform != "win32":
        return _stub("Xminidump", "Windows minidump analysis — use windbg-cdb on Windows.")
    dump = _program() or os.environ.get("WINDBG_DUMP", "")
    cdb = shutil.which("cdb.exe") or shutil.which("windbg.exe")
    if cdb and dump:
        return subprocess.call([cdb, "-z", dump])
    return _stub(
        "Xminidump/Dumpert",
        "Set program to .dmp file or WINDBG_DUMP; install Debugging Tools (cdb).",
    )


_HANDLERS = {
    "macsbug": launch_macsbug,
    "softice": launch_softice,
    "codeview": launch_codeview,
    "dos-debug": launch_dos_debug,
    "turbo-debugger": launch_turbo_debugger,
    "mdb": launch_mdb,
    "kadb-ddb": launch_kadb_ddb,
    "affinic": launch_affinic,
    "ddd": launch_ddd,
    "ups": launch_ups,
    "xminidump": launch_xminidump,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-historic-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
