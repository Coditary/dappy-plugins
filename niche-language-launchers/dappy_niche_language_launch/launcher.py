"""Launchers for exotic and functional language debuggers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-niche-language-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_racket_debugger() -> int:
    racket = shutil.which("racket") or shutil.which("drracket")
    program = _program()
    if racket and program:
        return _run([racket, "-l", "errortrace", "-t", program])
    if shutil.which("drracket"):
        return _run([shutil.which("drracket") or "drracket"])
    return _info(
        "Racket debugger",
        [
            "Visual stepper in DrRacket (Debug button).",
            "CLI: racket -l errortrace -t script.rkt",
            "Install racket package.",
        ],
    )


def launch_agda_coq_prover() -> int:
    for cmd, args in (
        ("agda", ["--interactive"]),
        ("coqc", []),
        ("coqtop", []),
    ):
        path = shutil.which(cmd)
        program = _program()
        if path and program and cmd == "agda":
            return _run([path, program])
        if path and cmd == "coqtop":
            return _run([path])
    return _info(
        "Agda / Coq",
        [
            "Interactive proof assistants — proof stepper as debugger.",
            "Agda: agda --interactive file.agda",
            "Coq: coqtop, Proof General, or CoqIDE.",
        ],
    )


def launch_idris_debugger() -> int:
    idris = shutil.which("idris2") or shutil.which("idris")
    program = _program()
    if idris and program:
        return _run([idris, program])
    if idris:
        return _run([idris])
    return _info(
        "Idris debugger",
        [
            "Dependently typed functional language REPL debugger.",
            "idris2 file.idr — :t, :reload, case split debugging.",
            "Install idris2 compiler.",
        ],
    )


def launch_beam_observer() -> int:
    erl = shutil.which("erl")
    if erl:
        return _run([erl, "-eval", "observer:start(), init:stop()."])
    elixir = shutil.which("iex")
    if elixir:
        return _run([elixir, "-S", "mix", "run", "-e", "Node.connect(:observer)"])
    return _info(
        "BEAM observer / dbg",
        [
            "Erlang/Elixir process and message-queue visual debugger.",
            "erl -eval 'observer:start()'",
            "Elixir: :observer.start() in IEx; dbg for interpreted modules.",
            "See also elixir-erlang-debugger plugin.",
        ],
    )


def launch_erratum_debugger() -> int:
    scheme = shutil.which("scheme") or shutil.which("mit-scheme") or shutil.which("racket")
    program = _program()
    if scheme and program:
        return _run([scheme, program])
    return _info(
        "Erratum / Scheme macro debugger",
        [
            "Trace macro expansions at runtime in Lisp/Scheme derivatives.",
            "Racket: macro-debugger stepper (DrRacket).",
            "MIT/GNU Scheme: trace and single-step in REPL.",
            "See also racket-debugger plugin.",
        ],
    )


def launch_jupyter_debugger() -> int:
    jupyter = shutil.which("jupyter") or shutil.which("jupyter-lab")
    program = _program()
    if jupyter:
        args = [jupyter, "lab" if "lab" in jupyter else "notebook", "--no-browser"]
        if program and os.path.isdir(program):
            args.extend(["--notebook-dir", program])
        return _run(args)
    return _info(
        "Jupyter debugger",
        [
            "IPython kernel debugger in JupyterLab (Python 3.8+).",
            "pip install ipykernel jupyterlab",
            "Use %debug magic or debugger toolbar in notebook cells.",
            "For DAP use python plugin with debugpy.",
        ],
    )


_HANDLERS = {
    "racket-debugger": launch_racket_debugger,
    "agda-coq-prover": launch_agda_coq_prover,
    "idris-debugger": launch_idris_debugger,
    "jupyter-debugger": launch_jupyter_debugger,
    "beam-observer": launch_beam_observer,
    "erratum-debugger": launch_erratum_debugger,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-niche-language-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
