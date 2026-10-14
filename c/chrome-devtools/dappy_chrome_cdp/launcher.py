"""CDP attach launcher — prefers js-debug chrome attach when available."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def main() -> None:
    js_debug = os.environ.get("JS_DEBUG_ADAPTER")
    node = shutil.which("node")
    if js_debug and node:
        raise SystemExit(subprocess.call([node, js_debug]))

    port = os.environ.get("CHROME_DEBUG_PORT", "9222")
    sys.stderr.write(
        f"dappy-chrome-cdp: start Chrome with --remote-debugging-port={port}\n"
        "  google-chrome --remote-debugging-port=9222 index.html\n"
        "Install @vscode/js-debug for full DAP attach (JS_DEBUG_ADAPTER).\n"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
