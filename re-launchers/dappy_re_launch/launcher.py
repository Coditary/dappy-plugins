"""Route to per-tool launcher by argv[1] tool id."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _win_only(name: str) -> None:
    if sys.platform != "win32":
        sys.stderr.write(f"dappy-re-launch: {name} requires Windows.\n")
        raise SystemExit(1)


def _require(path: str | None, hint: str) -> str:
    if not path:
        sys.stderr.write(hint + "\n")
        raise SystemExit(1)
    return path


def launch_ida(program: str) -> int:
    ida = os.environ.get("IDA") or shutil.which("ida64") or shutil.which("ida")
    ida = _require(ida, "Set IDA to ida64/ida executable")
    args = [ida]
    if program:
        args.append(program)
    return subprocess.call(args)


def launch_ghidra(program: str) -> int:
    ghidra = os.environ.get("GHIDRA_INSTALL_DIR")
    analyze = None
    if ghidra:
        for name in ("analyzeHeadless", "ghidraRun"):
            candidate = os.path.join(ghidra, name)
            if os.path.isfile(candidate):
                analyze = candidate
                break
    analyze = analyze or shutil.which("analyzeHeadless") or shutil.which("ghidraRun")
    analyze = _require(analyze, "Set GHIDRA_INSTALL_DIR or install Ghidra")
    if program and analyze.endswith("analyzeHeadless"):
        proj = os.environ.get("GHIDRA_PROJECT", "/tmp/ghidra-dappy")
        return subprocess.call(
            [analyze, proj, "Dappy", "-import", program, "-deleteProject"]
        )
    args = [analyze]
    if program:
        args.append(program)
    return subprocess.call(args)


def launch_x64dbg(program: str) -> int:
    _win_only("x64dbg")
    exe = os.environ.get("X64DBG") or shutil.which("x64dbg.exe") or shutil.which("x32dbg.exe")
    exe = _require(exe, "Set X64DBG to x64dbg.exe or x32dbg.exe")
    args = [exe]
    if program:
        args.extend(["-f", program])
    return subprocess.call(args)


def launch_ollydbg(program: str) -> int:
    _win_only("OllyDbg")
    exe = os.environ.get("OLLYDBG") or shutil.which("ollydbg.exe")
    exe = _require(exe, "OllyDbg is legacy 32-bit — set OLLYDBG path")
    args = [exe]
    if program:
        args.append(program)
    return subprocess.call(args)


def launch_radare2(program: str) -> int:
    r2 = shutil.which("r2") or shutil.which("radare2")
    r2 = _require(r2, "Install radare2 (r2)")
    args = [r2, "-d", program] if program else [r2]
    return subprocess.call(args)


def launch_cutter(program: str) -> int:
    cutter = os.environ.get("CUTTER") or shutil.which("cutter") or shutil.which("Cutter")
    cutter = _require(cutter, "Install Cutter GUI or set CUTTER path")
    args = [cutter]
    if program:
        args.append(program)
    return subprocess.call(args)


def launch_binary_ninja(program: str) -> int:
    bn = os.environ.get("BINARY_NINJA") or shutil.which("binaryninja")
    bn = _require(bn, "Set BINARY_NINJA to Binary Ninja executable")
    args = [bn]
    if program:
        args.append(program)
    return subprocess.call(args)


def launch_immunity(program: str) -> int:
    _win_only("Immunity Debugger")
    exe = os.environ.get("IMMUNITY") or shutil.which("immunitydebugger.exe")
    exe = _require(exe, "Set IMMUNITY to Immunity Debugger.exe")
    args = [exe]
    if program:
        args.append(program)
    return subprocess.call(args)


def launch_capstone(program: str) -> int:
    objdump = shutil.which("objdump")
    if not program or not objdump:
        sys.stderr.write(
            "capstone-disasm: disassemble with objdump -d (install capstone tools separately)\n"
        )
        raise SystemExit(1)
    return subprocess.call([objdump, "-d", program])


_HANDLERS = {
    "ida-pro": launch_ida,
    "ghidra": launch_ghidra,
    "x64dbg": launch_x64dbg,
    "ollydbg": launch_ollydbg,
    "radare2": launch_radare2,
    "cutter": launch_cutter,
    "binary-ninja": launch_binary_ninja,
    "immunity-debugger": launch_immunity,
    "capstone-disasm": launch_capstone,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-re-launch: unknown tool `{tool}`\n")
        raise SystemExit(1)
    program = os.environ.get("DAPPY_PROGRAM", "")
    raise SystemExit(handler(program))


if __name__ == "__main__":
    main()
