"""Launchers for mainframe and enterprise debuggers."""

from __future__ import annotations

import os
import sys


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-mainframe-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def launch_ibm_zos_debugger() -> int:
    return _info(
        "IBM z/OS Debugger",
        [
            "Standard debugger for COBOL, PL/I, Assembler, C on IBM z/OS.",
            "Runs on z/OS — connect via IBM Debug Tool / IDz / Zowe.",
            "Env: ZOWE_PROFILE, IBM_DEBUG_PORT for remote attach.",
            "Docs: https://www.ibm.com/docs/en/debug-tool",
        ],
    )


def launch_xpediter_bmc() -> int:
    host = os.environ.get("XPEDITER_HOST", "mainframe.example.com")
    return _info(
        "Xpediter (BMC)",
        [
            "Interactive mainframe debugger for CICS, DB2, batch.",
            f"Connect BMC Xpediter client to {host}.",
            "Env: XPEDITER_HOST, XPEDITER_USER",
            "Commercial — requires BMC license.",
        ],
    )


_HANDLERS = {
    "ibm-zos-debugger": launch_ibm_zos_debugger,
    "xpediter-bmc": launch_xpediter_bmc,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-mainframe-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
