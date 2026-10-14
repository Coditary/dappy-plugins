"""Launchers for MATLAB, Octave, and Mathematica debuggers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-math-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_matlab_debugger() -> int:
    matlab = os.environ.get("MATLAB") or shutil.which("matlab")
    program = _program()
    if matlab:
        args = [matlab, "-nodesktop", "-nosplash"]
        if program:
            args.extend(["-r", f"dbstop if error; run('{program}');"])
        return _run(args)
    return _info(
        "MATLAB Debugger",
        [
            "Visual m-code debugger — breakpoints, workspace inspection.",
            "dbstop in file.m at 10; dbstep; dbcont",
            "Set MATLAB to matlab binary path.",
        ],
    )


def launch_octave_debugger() -> int:
    octave = os.environ.get("OCTAVE") or shutil.which("octave")
    program = _program()
    if octave and program:
        return _run([octave, "--eval", f"dbstop if error; run('{program}');"])
    if octave:
        return _run([octave])
    return _info(
        "GNU Octave Debugger",
        [
            "Open-source MATLAB-like debugger: dbstop, dbstep, dbcont.",
            "octave script.m — dbstop in script at 5",
            "Install octave package.",
        ],
    )


def launch_mathematica_debugger() -> int:
    for cmd in ("wolfram", "math", "WolframKernel"):
        path = os.environ.get("WOLFRAM") or shutil.which(cmd)
        if path:
            program = _program()
            expr = "Trace[expr]" if not program else f"Get[\"{program}\"]"
            return _run([path, "-noprompt", "-run", expr])
    return _info(
        "Mathematica / Wolfram Debugger",
        [
            "Trace, Check, Sow/Reap for symbolic step debugging.",
            "wolfram -run 'Trace[Integrate[x^2, x]]'",
            "Set WOLFRAM to Wolfram Engine binary.",
        ],
    )


_HANDLERS = {
    "matlab-debugger": launch_matlab_debugger,
    "octave-debugger": launch_octave_debugger,
    "mathematica-debugger": launch_mathematica_debugger,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-math-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
