"""Run a Python program under ipdb with an eager ipdab DAP server."""

from __future__ import annotations

import argparse
import os
import runpy
import socket
import sys
import time


def wait_for_port(host: str, port: int, timeout: float = 60.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            try:
                sock.connect((host, port))
                return
            except OSError:
                time.sleep(0.05)
    raise TimeoutError(f"ipdab DAP server did not listen on {host}:{port} within {timeout}s")


def run_program(program: str, argv: list[str]) -> int:
    import ipdab

    target = os.path.abspath(program)
    if not os.path.isfile(target):
        print(f"dappy_ipdb: program not found: {target}", file=sys.stderr)
        return 2

    script_dir = os.path.dirname(target) or os.getcwd()
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    sys.argv = [target, *argv]

    def trace_first_line(frame, event, _arg):
        if event != "line":
            return trace_first_line
        if os.path.abspath(frame.f_code.co_filename) != target:
            return trace_first_line
        sys.settrace(None)
        ipdab.set_trace(on_continue="keep_running")
        return None

    sys.settrace(trace_first_line)
    try:
        runpy.run_path(target, run_name="__main__")
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    finally:
        sys.settrace(None)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Launch a script under ipdb/ipdab")
    parser.add_argument("--program", required=True, help="Python script to debug")
    parser.add_argument("--host", default=os.environ.get("IPDAB_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("IPDAB_PORT", "9000")),
    )
    parser.add_argument(
        "script_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the script",
    )
    args = parser.parse_args(argv)

    try:
        import ipdab
    except ImportError:
        print(
            "dappy_ipdb: missing dependency 'ipdab'. Install with: pip install ipdab ipdb",
            file=sys.stderr,
        )
        return 2

    ipdab.ipdab.host = args.host
    ipdab.ipdab.port = args.port
    ipdab.ipdab.start_in_thread()
    wait_for_port(args.host, args.port)

    forwarded = args.script_args
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]

    return run_program(args.program, forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
