"""Launch Microsoft js-debug DAP adapter for Node.js when available."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _find_js_debug() -> list[str] | None:
    env = os.environ.get("JS_DEBUG_ADAPTER")
    if env and Path(env).is_file():
        return [shutil.which("node") or "node", env]

    for base in [
        Path(os.environ.get("NODE_PATH", "")),
        Path.home() / ".npm-global/lib/node_modules/@vscode/js-debug",
        Path("/usr/lib/node_modules/@vscode/js-debug"),
    ]:
        if not base:
            continue
        for candidate in [
            base / "out/src/cli.js",
            base / "dist/src/cli.js",
            base / "src/dapDebugServer.js",
        ]:
            if candidate.is_file():
                return [shutil.which("node") or "node", str(candidate)]
    return None


def main() -> None:
    node = shutil.which("node")
    if not node:
        sys.stderr.write("dappy-node-dap: `node` not found\n")
        raise SystemExit(1)

    cmd = _find_js_debug()
    if cmd:
        raise SystemExit(subprocess.call(cmd))

    # Fallback: built-in inspector (no full DAP — user attaches DevTools).
    program = os.environ.get("DAPPY_PROGRAM", "")
    if not program:
        sys.stderr.write(
            "dappy-node-dap: install @vscode/js-debug or set JS_DEBUG_ADAPTER\n"
            "  npm i -g @vscode/js-debug\n"
        )
        raise SystemExit(1)
    port = os.environ.get("NODE_INSPECT_PORT", "9229")
    raise SystemExit(
        subprocess.call([node, f"--inspect-brk={port}", program])
    )


if __name__ == "__main__":
    main()
