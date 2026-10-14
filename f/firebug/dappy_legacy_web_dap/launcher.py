"""Legacy browser debugger stubs (Firebug, Opera Dragonfly)."""

from __future__ import annotations

import sys

_MESSAGES = {
    "firebug": (
        "Firebug was discontinued in 2017. Use `firefox-devtools` or `chrome-devtools`.\n"
        "https://getfirebug.com/\n"
    ),
    "dragonfly": (
        "Opera Dragonfly was discontinued. Use `chrome-devtools` or `edge-devtools`.\n"
    ),
}


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "legacy"
    sys.stderr.write(_MESSAGES.get(name, "Legacy debugger — use modern browser DevTools.\n"))
    raise SystemExit(1)


if __name__ == "__main__":
    main()
