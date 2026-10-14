"""Launch PHP with Xdebug 3 and proxy to DBGp/DAP adapter when available."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def main() -> None:
    php = os.environ.get("PHP", shutil.which("php"))
    if not php:
        sys.stderr.write("dappy-xdebug-dap: `php` not found\n")
        raise SystemExit(1)

    adapter = os.environ.get("PHP_DEBUG_ADAPTER")
    if adapter and shutil.which("node"):
        raise SystemExit(subprocess.call(["node", adapter]))

    program = os.environ.get("DAPPY_PROGRAM", "")
    port = os.environ.get("XDEBUG_PORT", "9003")
    if not program:
        sys.stderr.write(
            "dappy-xdebug-dap: install php-debug adapter or set PHP_DEBUG_ADAPTER\n"
            "  pecl install xdebug && enable in php.ini\n"
        )
        raise SystemExit(1)

    env = os.environ.copy()
    env["XDEBUG_MODE"] = "debug,develop"
    env["XDEBUG_CONFIG"] = f"client_port={port} client_host=127.0.0.1"
    raise SystemExit(subprocess.call([php, program], env=env, cwd=os.path.dirname(program) or "."))


if __name__ == "__main__":
    main()
