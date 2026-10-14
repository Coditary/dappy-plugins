"""Launchers for RTOS and microkernel debugging tools."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-microkernel-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_freertos_zephyr_gdb() -> int:
    openocd = shutil.which("openocd")
    gdb = shutil.which("arm-none-eabi-gdb") or shutil.which("gdb")
    program = _program()
    if openocd:
        cfg = os.environ.get("OPENOCD_CONFIG", "interface/cmsis-dap.cfg")
        target = os.environ.get("OPENOCD_TARGET", "target/stm32f4x.cfg")
        return _info(
            "FreeRTOS / Zephyr GDB",
            [
                "OpenOCD + GDB with RTOS thread awareness.",
                "FreeRTOS: enable configUSE_TRACE_FACILITY; (gdb) info threads",
                "Zephyr: west debug; thread apply all bt",
                f"openocd -f {cfg} -f {target} — then attach gdb",
                "See also openocd plugin.",
            ],
        )
    if gdb and program:
        return _run([gdb, "-ex", "set print thread-events on", program])
    return _info(
        "FreeRTOS / Zephyr GDB",
        [
            "JTAG/OpenOCD + GDB macros for RTOS task debugging.",
            "Install OpenOCD, arm-none-eabi-gdb, FreeRTOS/Zephyr GDB scripts.",
        ],
    )


def launch_l4re_genode_debugger() -> int:
    return _info(
        "L4Re / Genode Debugger",
        [
            "Microkernel diagnostics for security-critical systems.",
            "Genode: core log, nitpicker, gdb monitor on core services.",
            "L4Re: jdb kernel debugger on Fiasco.OC.",
            "Highly platform-specific — consult Genode/L4Re docs.",
        ],
    )


_HANDLERS = {
    "freertos-zephyr-gdb": launch_freertos_zephyr_gdb,
    "l4re-genode-debugger": launch_l4re_genode_debugger,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-microkernel-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
