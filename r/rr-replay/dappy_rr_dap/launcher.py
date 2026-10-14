"""Proxy stdio DAP to `rr replay <trace> -- lldb-dap`."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def main() -> None:
    if not shutil.which("rr"):
        sys.stderr.write("dappy-rr-dap: `rr` not found (https://rr-project.org)\n")
        raise SystemExit(1)
    if not shutil.which("lldb-dap"):
        sys.stderr.write("dappy-rr-dap: `lldb-dap` not found\n")
        raise SystemExit(1)

    trace_dir = os.environ.get("DAPPY_RR_TRACE_DIR", "")
    if not trace_dir:
        sys.stderr.write(
            "dappy-rr-dap: set DAPPY_RR_TRACE_DIR or use --target rr-record first\n"
        )
        raise SystemExit(1)

    cmd = ["rr", "replay", trace_dir, "--", "lldb-dap"]
    proc = subprocess.Popen(cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
    raise SystemExit(proc.wait())


if __name__ == "__main__":
    main()
