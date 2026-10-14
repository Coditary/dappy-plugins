"""Run binaries under sanitizers and memory analysis tools."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    p = os.environ.get("DAPPY_PROGRAM", "")
    if not p:
        sys.stderr.write("dappy-sanitizer-run: DAPPY_PROGRAM required\n")
        raise SystemExit(1)
    return p


def run_asan() -> int:
    env = os.environ.copy()
    env.setdefault("ASAN_OPTIONS", "halt_on_error=1:abort_on_error=1:print_stacktrace=1")
    return subprocess.call([_program()], env=env)


def run_tsan() -> int:
    env = os.environ.copy()
    env.setdefault("TSAN_OPTIONS", "halt_on_error=1")
    return subprocess.call([_program()], env=env)


def run_ubsan() -> int:
    env = os.environ.copy()
    env.setdefault("UBSAN_OPTIONS", "halt_on_error=1:print_stacktrace=1")
    return subprocess.call([_program()], env=env)


def run_msan() -> int:
    env = os.environ.copy()
    env.setdefault("MSAN_OPTIONS", "halt_on_error=1:abort_on_error=1:print_stacktrace=1")
    return subprocess.call([_program()], env=env)


def run_dfsan() -> int:
    env = os.environ.copy()
    env.setdefault("DFSAN_OPTIONS", "halt_on_error=1")
    return subprocess.call([_program()], env=env)


def run_lsan() -> int:
    env = os.environ.copy()
    env.setdefault("LSAN_OPTIONS", "exitcode=1:print_suppressions=0")
    asan_opts = env.get("ASAN_OPTIONS", "")
    if "detect_leaks" not in asan_opts:
        env["ASAN_OPTIONS"] = (asan_opts + ":detect_leaks=1").lstrip(":")
    return subprocess.call([_program()], env=env)


def run_efence() -> int:
    lib = os.environ.get("EFENCE_LIB", "libefence.so.0")
    env = os.environ.copy()
    env["LD_PRELOAD"] = lib + (":" + env["LD_PRELOAD"] if env.get("LD_PRELOAD") else "")
    return subprocess.call([_program()], env=env)


def run_duma() -> int:
    lib = os.environ.get("DUMA_LIB", "libduma.so")
    env = os.environ.copy()
    env["LD_PRELOAD"] = lib + (":" + env["LD_PRELOAD"] if env.get("LD_PRELOAD") else "")
    return subprocess.call([_program()], env=env)


def run_dr_memory() -> int:
    drm = shutil.which("drmemory") or shutil.which("drmemory.exe")
    if not drm:
        sys.stderr.write("dappy-sanitizer-run: install Dr. Memory (drmemory)\n")
        raise SystemExit(1)
    return subprocess.call([drm, "-t", "--", _program()])


def run_purify() -> int:
    sys.stderr.write("purify: commercial IBM Rational Purify — use native Purify GUI.\n")
    raise SystemExit(1)


def run_aqtime() -> int:
    sys.stderr.write("aqtime-pro: commercial AQTime — use Embarcadero AQTime GUI.\n")
    raise SystemExit(1)


_HANDLERS = {
    "asan": run_asan,
    "tsan": run_tsan,
    "ubsan": run_ubsan,
    "msan": run_msan,
    "dfsan": run_dfsan,
    "lsan": run_lsan,
    "efence": run_efence,
    "duma": run_duma,
    "dr-memory": run_dr_memory,
    "purify": run_purify,
    "aqtime-pro": run_aqtime,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    if len(sys.argv) > 2:
        os.environ["DAPPY_PROGRAM"] = sys.argv[2]
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-sanitizer-run: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
