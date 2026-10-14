"""Launchers for domain-specific visual debuggers (LabVIEW, SQL visualizers)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-domain-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_labview_highlight() -> int:
    labview = os.environ.get("LABVIEW") or shutil.which("labview") or shutil.which("LabVIEW")
    program = _program()
    if labview:
        args = [labview]
        if program and program.endswith(".vi"):
            args.append(program)
        return _run(args)
    return _info(
        "LabVIEW Highlight Execution",
        [
            "Visual dataflow debugger — enable light-bulb (Highlight Execution).",
            "Right-click VI → Highlight Execution — watch values on wires.",
            "Set LABVIEW to LabVIEW executable path.",
            "Simulink: use Simulink Debugger / step simulation similarly.",
        ],
    )


def launch_pg_explain_visualizer() -> int:
    psql = shutil.which("psql")
    program = _program()
    pgadmin = os.environ.get("PGADMIN") or shutil.which("pgadmin4")
    if psql and program and os.path.isfile(program):
        query = open(program, encoding="utf-8", errors="replace").read()
        db = os.environ.get("PGDATABASE", "postgres")
        result = subprocess.run(
            [psql, "-d", db, "-t", "-A", "-c", f"EXPLAIN (FORMAT JSON) {query}"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            sys.stderr.write("EXPLAIN JSON plan (paste into visualizer):\n")
            sys.stderr.write(result.stdout[:4000] + "\n")
            sys.stderr.write("Visualizers: https://explain.dalibo.com/ or pgAdmin Query Tool\n")
            return 0
    if pgadmin:
        return _run([pgadmin])
    return _info(
        "pgAdmin EXPLAIN Visualizer",
        [
            "Visual query plan trees for PostgreSQL bottlenecks.",
            "pgAdmin: Query Tool → Explain → Graphical / JSON tab.",
            "Online: https://explain.dalibo.com/",
            "Pass .sql file for EXPLAIN (FORMAT JSON) output.",
            "See also pg-explain plugin for EXPLAIN ANALYZE.",
        ],
    )


_HANDLERS = {
    "labview-highlight": launch_labview_highlight,
    "pg-explain-visualizer": launch_pg_explain_visualizer,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-domain-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
