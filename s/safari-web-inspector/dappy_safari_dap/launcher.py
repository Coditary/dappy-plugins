"""Safari Web Inspector — macOS only."""

from __future__ import annotations

import sys


def main() -> None:
    if sys.platform != "darwin":
        sys.stderr.write(
            "dappy-safari-dap: Safari Web Inspector requires macOS.\n"
            "Enable Develop menu → Connect Web Inspector.\n"
        )
        raise SystemExit(1)
    sys.stderr.write(
        "dappy-safari-dap: use Safari Develop → Connect Web Inspector.\n"
        "For automated DAP use js-debug Safari support on macOS.\n"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
