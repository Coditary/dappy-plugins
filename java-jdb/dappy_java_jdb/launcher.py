"""Launch JVM with JDWP and attach JDB (terminal) or java debug adapter."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    java = os.environ.get("JAVA", shutil.which("java"))
    jdb = shutil.which("jdb")
    if not java or not jdb:
        sys.stderr.write("dappy-java-jdb: requires `java` and `jdb` (JDK)\n")
        raise SystemExit(1)

    program = os.environ.get("DAPPY_PROGRAM", "")
    port = os.environ.get("JDWP_PORT", "5005")
    if not program:
        sys.stderr.write("dappy-java-jdb: program (class/jar) required\n")
        raise SystemExit(1)

    # Spawn JVM suspended on JDWP, then interactive jdb.
    jdwp = f"transport=dt_socket,server=y,suspend=y,address=*:{port}"
    if program.endswith(".jar"):
        jvm = [java, f"-agentlib:jdwp={jdwp}", "-jar", program]
    else:
        jvm = [java, f"-agentlib:jdwp={jdwp}", "-cp", str(Path(program).parent), Path(program).stem]

    proc = subprocess.Popen(jvm)
    try:
        raise SystemExit(subprocess.call([jdb, "-attach", f"localhost:{port}"]))
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
