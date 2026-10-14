"""Launchers for additional language and script debuggers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-language-extra-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_typescript_tsc() -> int:
    tsc = shutil.which("tsc") or shutil.which("npx")
    program = _program()
    if not program:
        return _info("TypeScript tsc", ["Pass tsconfig.json or .ts file as program."], code=1)
    if tsc and tsc.endswith("npx"):
        return _run([tsc, "tsc", "--noEmit", program])
    if tsc:
        return _run([tsc, "--noEmit", program])
    return _info("TypeScript tsc", ["npm install -g typescript"], code=1)


def launch_bash_trace() -> int:
    bash = shutil.which("bash") or "/bin/bash"
    program = _program()
    if not program:
        return _info("bash trace", ["Pass .sh script as program."], code=1)
    return _run([bash, "-xv", program])


def launch_shdb() -> int:
    shdb = shutil.which("shdb")
    program = _program()
    if shdb and program:
        return _run([shdb, program])
    return _info(
        "shdb",
        [
            "Bash source debugger with breakpoints.",
            "Install: https://github.com/bashdb/bashdb",
            "Or use bash-trace plugin (bash -xv).",
        ],
        code=1 if not shdb else 0,
    )


def launch_emacs_edebug() -> int:
    emacs = shutil.which("emacs")
    program = _program()
    if emacs and program:
        return _run([emacs, "-batch", "-l", program, "-f", "edebug-all-defs"])
    return _info(
        "Emacs Edebug",
        [
            "Symbolic Elisp debugger — (edebug-defun) in Emacs.",
            "emacs -Q -l script.el — instrument with Edebug.",
        ],
    )


def launch_clojure_debugger() -> int:
    clj = shutil.which("clj") or shutil.which("clojure")
    program = _program()
    if clj and program:
        return _run([clj, "-M", "-m", "nrepl.cmdline", "--interactive"])
    return _info(
        "Clojure debugger",
        [
            "Use clojure.tools.namespace + cider-nrepl or reveal.",
            "lein repl / clj -M:dev — (require '[clojure.tools.trace])",
            "Env: CLOJURE_DEBUG=1",
        ],
    )


def launch_swi_prolog_tracer() -> int:
    swipl = shutil.which("swipl")
    program = _program()
    if swipl and program:
        return _run([swipl, "-l", program, "-g", "trace, halt"])
    if swipl:
        return _run([swipl])
    return _info("SWI-Prolog tracer", ["Install swi-prolog; use trace/0 and gtrace/0."], code=1)


def launch_ghci_debugger() -> int:
    ghci = shutil.which("ghci") or shutil.which("ghc")
    program = _program()
    if ghci and program:
        return _run([ghci, program])
    if ghci:
        return _run([ghci])
    return _info("GHCi debugger", ["Install GHC; :break, :step, :trace in GHCi."], code=1)


def launch_elixir_erlang_debugger() -> int:
    for cmd, args in (
        ("iex", ["-S", "mix"]),
        ("erl", ["-eval", "debugger:start(), halt()."]),
    ):
        path = shutil.which(cmd)
        if path:
            return _run([path] + args)
    return _info(
        "Elixir/Erlang debugger",
        [
            "Erlang: debugger:start() in erl shell.",
            "Elixir: IEx.break!/2, :int.start() for interpreted modules.",
            "Observer: recon / recon_trace for production.",
        ],
    )


_HANDLERS = {
    "typescript-tsc": launch_typescript_tsc,
    "bash-trace": launch_bash_trace,
    "shdb": launch_shdb,
    "emacs-edebug": launch_emacs_edebug,
    "clojure-debugger": launch_clojure_debugger,
    "swi-prolog-tracer": launch_swi_prolog_tracer,
    "ghci-debugger": launch_ghci_debugger,
    "elixir-erlang-debugger": launch_elixir_erlang_debugger,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-language-extra-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
