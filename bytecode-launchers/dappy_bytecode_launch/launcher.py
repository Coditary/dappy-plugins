"""Launchers for VM, bytecode, and interpreter debugging tools."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-bytecode-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_jvmti_debugger() -> int:
    jdb = shutil.which("jdb") or shutil.which("jsdb")
    program = _program()
    if jdb and program:
        return _run([jdb, program])
    return _info(
        "JVMTI Debugger",
        [
            "Native JVM debug interface under IntelliJ/Eclipse debuggers.",
            "CLI: jdb -attach <port> or java -agentlib:jdwp=…",
            "For DAP use java-jdb plugin.",
            "JVMTI agents: -agentpath:myagent.so",
        ],
    )


def launch_v8_cdp() -> int:
    node = os.environ.get("NODE") or shutil.which("node")
    program = _program()
    port = os.environ.get("V8_CDP_PORT", "9229")
    if node and program:
        return _run([node, f"--inspect={port}", program])
    return _info(
        "V8 CDP / Node inspect",
        [
            f"Chrome DevTools Protocol on port {port}.",
            "chrome://inspect or chrome-devtools plugin.",
            "For full DAP: nodejs-inspector plugin.",
            "node --inspect-brk app.js",
        ],
    )


def launch_hhvm_hphpd() -> int:
    hphpd = shutil.which("hphpd")
    program = _program()
    if hphpd:
        args = [hphpd]
        if program:
            args.append(program)
        return _run(args)
    hhvm = shutil.which("hhvm")
    if hhvm and program:
        return _run([hhvm, program])
    return _info(
        "HHVM hphpd",
        [
            "HipHop VM command-line debugger for PHP/Hack.",
            "Install HHVM; hphpd script.php",
            "Hack: hhvm --hphp -m debugger",
        ],
    )


def launch_python_dis() -> int:
    python = os.environ.get("PYTHON") or shutil.which("python3") or shutil.which("python")
    program = _program()
    if not python:
        return _info("CPython dis", ["Install Python 3."], code=1)
    if program and os.path.isfile(program):
        return _run([python, "-m", "dis", program])
    return _info(
        "CPython dis",
        [
            "Bytecode disassembler — pass .py file as program.",
            "python -m dis script.py",
            "For interactive debugging use python / python-pdbpp plugins.",
        ],
    )


_HANDLERS = {
    "jvmti-debugger": launch_jvmti_debugger,
    "v8-cdp": launch_v8_cdp,
    "hhvm-hphpd": launch_hhvm_hphpd,
    "python-dis": launch_python_dis,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-bytecode-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
