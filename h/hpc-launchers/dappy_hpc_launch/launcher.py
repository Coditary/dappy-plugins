"""Launchers for HPC parallel debuggers (MPI/OpenMP)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-hpc-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_arm_ddt() -> int:
    ddt = os.environ.get("ARM_DDT") or os.environ.get("ALLINEA_DDT") or shutil.which("ddt")
    program = _program()
    if ddt:
        args = [ddt]
        if program:
            args.append(program)
        return _run(args)
    return _info(
        "ARM DDT (Allinea)",
        [
            "Industry standard MPI/OpenMP debugger for supercomputers.",
            "Module load ddt on HPC cluster; ddt ./mpi_app",
            "Set ARM_DDT to ddt binary path.",
            "Docs: https://developer.arm.com/documentation/101469",
        ],
    )


def launch_totalview() -> int:
    tv = os.environ.get("TOTALVIEW") or shutil.which("totalview") or shutil.which("tv")
    program = _program()
    if tv:
        args = [tv]
        if program:
            args.append(program)
        return _run(args)
    return _info(
        "TotalView",
        [
            "Commercial massively parallel multi-process debugger.",
            "mpirun -np 64 totalview ./simulation",
            "Set TOTALVIEW path; Perforce TotalView license required.",
        ],
    )


def launch_stat_mpi() -> int:
    stat = shutil.which("stat-cl") or shutil.which("STAT") or os.environ.get("STAT")
    program = _program()
    if stat:
        args = [stat]
        if program:
            args.append(program)
        return _run(args)
    return _info(
        "STAT (Stack Trace Analysis Tool)",
        [
            "Collect stack traces from thousands of MPI ranks at once.",
            "Used when jobs hang — reveals cluster-wide patterns.",
            "Install LLNL STAT on HPC system; stat-cl <jobid>",
        ],
    )


_HANDLERS = {
    "arm-ddt": launch_arm_ddt,
    "totalview": launch_totalview,
    "stat-mpi": launch_stat_mpi,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-hpc-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
