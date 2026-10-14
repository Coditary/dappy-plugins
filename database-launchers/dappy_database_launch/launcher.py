"""Launchers for database and SQL debuggers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-database-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_plsql_developer() -> int:
    plsql = os.environ.get("PLSQL_DEVELOPER") or shutil.which("plsqldev.exe")
    if plsql and sys.platform == "win32":
        args = [plsql]
        program = _program()
        if program:
            args.append(program)
        return _run(args)
    return _info(
        "PL/SQL Developer",
        [
            "Oracle PL/SQL stored procedure debugger (Allround Automations).",
            "Windows GUI — set PLSQL_DEVELOPER to plsqldev.exe.",
            "Use Test Manager → Debug for procedures/packages.",
        ],
    )


def launch_pgadmin_pldbg() -> int:
    pgadmin = os.environ.get("PGADMIN") or shutil.which("pgadmin4") or shutil.which("pgAdmin4")
    if pgadmin:
        return _run([pgadmin])
    psql = shutil.which("psql")
    if psql:
        return _info(
            "pgAdmin / pldbgapi",
            [
                "Install pldbgapi extension in PostgreSQL for function/trigger debugging.",
                "CREATE EXTENSION pldbgapi; — debug via pgAdmin or EDB tools.",
                f"psql available at {psql}",
            ],
        )
    return _info(
        "pgAdmin / pldbgapi",
        [
            "PostgreSQL function debugger via pldbgapi extension.",
            "Install pgAdmin 4 + enable pldbgapi on your database.",
            "Docs: https://www.postgresql.org/docs/current/pldebugger.html",
        ],
    )


def launch_ssms_tsql() -> int:
    if sys.platform != "win32":
        return _info("SSMS T-SQL Debugger", ["Windows + SQL Server Management Studio required."], code=1)
    ssms = os.environ.get("SSMS") or shutil.which("Ssms.exe")
    if ssms:
        args = [ssms]
        program = _program()
        if program:
            args.append(program)
        return _run(args)
    return _info(
        "SSMS T-SQL Debugger",
        [
            "Visual T-SQL debugger in SQL Server Management Studio.",
            "Set SSMS to Ssms.exe; open .sql and use Debug → Start.",
            "Note: legacy feature — limited on Azure SQL.",
        ],
    )


def launch_toad_debugger() -> int:
    toad = os.environ.get("TOAD") or shutil.which("Toad.exe")
    if toad:
        args = [toad]
        program = _program()
        if program:
            args.append(program)
        return _run(args)
    return _info(
        "TOAD Debugger",
        [
            "Quest TOAD commercial database IDE with PL/SQL debugging.",
            "Set TOAD to Toad.exe (Windows).",
            "Supports Oracle, SQL Server, PostgreSQL, DB2.",
        ],
    )


_HANDLERS = {
    "plsql-developer": launch_plsql_developer,
    "pgadmin-pldbg": launch_pgadmin_pldbg,
    "ssms-tsql": launch_ssms_tsql,
    "toad-debugger": launch_toad_debugger,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-database-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
