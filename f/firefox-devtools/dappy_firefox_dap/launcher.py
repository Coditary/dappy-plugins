"""Firefox remote debugging attach helper."""

from __future__ import annotations

import os
import sys


def main() -> None:
    port = os.environ.get("FIREFOX_DEBUG_PORT", "9223")
    sys.stderr.write(
        "dappy-firefox-dap: start Firefox with remote debugging:\n"
        f"  firefox --remote-debugging-port={port} index.html\n"
        "Full DAP attach via js-debug Firefox profile (set JS_DEBUG_ADAPTER).\n"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
