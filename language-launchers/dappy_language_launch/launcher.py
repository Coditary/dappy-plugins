"""Launchers for specialized language and interpreter debuggers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-language-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_perl_debugger() -> int:
    perl = os.environ.get("PERL") or shutil.which("perl")
    program = _program()
    if not perl:
        return _info("Perl debugger", ["Install perl."], code=1)
    if not program:
        return _info("Perl debugger", ["Pass a .pl file as program."], code=1)
    return _run([perl, "-d", program])


def launch_ruby_debug() -> int:
    ruby = os.environ.get("RUBY") or shutil.which("ruby")
    program = _program()
    if not ruby:
        return _info("Ruby debug", ["Install ruby."], code=1)
    if not program:
        return _info("Ruby debug", ["Pass a .rb file as program."], code=1)
    return _run([ruby, "-r", "debug/debug", program])


def launch_ruby_pry() -> int:
    pry = shutil.which("pry") or shutil.which("bundle")
    program = _program()
    if not pry:
        return _info(
            "Pry",
            ["gem install pry", "Then: pry -r ./script.rb"],
            code=1,
        )
    if pry.endswith("bundle"):
        args = [pry, "exec", "pry"]
    else:
        args = [pry]
    if program:
        args.extend(["-r", program])
    return _run(args)


def launch_ruby_rdbg() -> int:
    rdbg = shutil.which("rdbg") or shutil.which("bundle")
    program = _program()
    if rdbg and rdbg.endswith("bundle"):
        if not program:
            return _info("rdbg", ["Pass a .rb file."], code=1)
        return _run([rdbg, "exec", "rdbg", "-n", "--open", program])
    if rdbg:
        args = [rdbg, "-n", "--open"]
        if program:
            args.append(program)
        else:
            return _info("rdbg", ["Install debug gem: gem install debug", "Pass a .rb file."], code=1)
        return _run(args)
    return _info(
        "rdbg",
        [
            "Ruby 3.1+ debug gem (DAP-capable).",
            "gem install debug",
            "rdbg -n --open script.rb",
        ],
        code=1,
    )


def launch_v8_inspector() -> int:
    node = os.environ.get("NODE") or shutil.which("node")
    program = _program()
    if not node:
        return _info("V8 Inspector", ["Install Node.js."], code=1)
    port = os.environ.get("V8_INSPECT_PORT", "9229")
    if program:
        return _run([node, f"--inspect-brk={port}", program])
    return _info(
        "V8 Inspector",
        [
            f"Node started with --inspect-brk on port {port}.",
            "Attach via chrome://inspect or nodejs-inspector DAP plugin.",
            "For full DAP use: dap-cli debug repl --adapter nodejs-inspector app.js",
        ],
    )


def launch_lua_mobdebug() -> int:
    lua = os.environ.get("LUA") or shutil.which("lua") or shutil.which("luajit")
    program = _program()
    mob_host = os.environ.get("MOBDEBUG_HOST", "127.0.0.1")
    mob_port = os.environ.get("MOBDEBUG_PORT", "8172")
    if lua and program:
        script = (
            f"require('mobdebug').start('{mob_host}:{mob_port}');"
            f"dofile('{program.replace(chr(39), chr(92)+chr(39))}')"
        )
        return _run([lua, "-e", script])
    return _info(
        "LuaDB / MobDebug",
        [
            "MobDebug remote debugger (ZeroBrane Studio, VS Code extensions).",
            "Install mobdebug.lua in LUA_PATH; start IDE listener on 8172.",
            f"Env: MOBDEBUG_HOST={mob_host}, MOBDEBUG_PORT={mob_port}",
            "LuaDB: standalone Lua debugger — set LUA to interpreter.",
        ],
    )


def launch_rstudio_debugger() -> int:
    rstudio = os.environ.get("RSTUDIO") or shutil.which("rstudio")
    if rstudio:
        args = [rstudio]
        program = _program()
        if program:
            args.append(program)
        return _run(args)
    rscript = shutil.which("Rscript")
    program = _program()
    if rscript and program:
        return _run([rscript, "-e", f"debug(source('{program}'))"])
    return _info(
        "RStudio Debugger",
        [
            "Open .R file in RStudio and set breakpoints (browser()).",
            "Or: R -e \"debug(source('script.R'))\"",
            "Set RSTUDIO to desktop binary path.",
        ],
    )


def launch_gdb_mi() -> int:
    try:
        import dappy_gdb_dap  # noqa: F401
    except ImportError:
        return _info(
            "GDB/MI",
            [
                "GDB Machine Interface — use native-gdb plugin.",
                "pip install -e dappy-plugins/native-gdb",
                "dap-cli debug repl --adapter native-gdb ./a.out",
            ],
            code=1,
        )
    return _run([sys.executable, "-m", "dappy_gdb_dap"])


_HANDLERS = {
    "perl-debugger": launch_perl_debugger,
    "ruby-debug": launch_ruby_debug,
    "ruby-pry": launch_ruby_pry,
    "ruby-rdbg": launch_ruby_rdbg,
    "v8-inspector": launch_v8_inspector,
    "lua-mobdebug": launch_lua_mobdebug,
    "rstudio-debugger": launch_rstudio_debugger,
    "gdb-mi": launch_gdb_mi,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-language-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
