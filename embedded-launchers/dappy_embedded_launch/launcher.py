"""Launchers for embedded / JTAG / MCU debug tools."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _require(cmd: str | None, hint: str) -> str:
    if not cmd:
        sys.stderr.write(hint + "\n")
        raise SystemExit(1)
    return cmd


def launch_openocd() -> int:
    openocd = shutil.which("openocd")
    openocd = _require(openocd, "Install OpenOCD")
    cfg = os.environ.get("OPENOCD_CONFIG", "interface/cmsis-dap.cfg")
    target = os.environ.get("OPENOCD_TARGET", "target/stm32f4x.cfg")
    return subprocess.call([openocd, "-f", cfg, "-f", target])


def launch_jlink_gdbserver() -> int:
    jlink = os.environ.get("JLINK_GDBSERVER") or shutil.which("JLinkGDBServerCL")
    jlink = _require(jlink, "Install SEGGER J-Link software (JLinkGDBServerCL)")
    device = os.environ.get("JLINK_DEVICE", "Cortex-M4")
    port = os.environ.get("JLINK_PORT", "2331")
    iface = os.environ.get("JLINK_INTERFACE", "SWD")
    return subprocess.call(
        [jlink, "-if", iface, "-device", device, "-port", port, "-nogui", "1"]
    )


def launch_avr_gdb() -> int:
    gdb = os.environ.get("AVR_GDB") or shutil.which("avr-gdb") or shutil.which("gdb")
    gdb = _require(gdb, "Install avr-gdb (avr-gdb package)")
    program = _program()
    if not program:
        sys.stderr.write("dappy-embedded-launch: program (.elf) required for avr-gdb\n")
        raise SystemExit(1)
    return subprocess.call([gdb, program])


def launch_stm32cube_gdb() -> int:
    gdb = (
        os.environ.get("ARM_GDB")
        or shutil.which("arm-none-eabi-gdb")
        or shutil.which("gdb")
    )
    gdb = _require(gdb, "Install arm-none-eabi-gdb (GNU MCU / STM32Cube)")
    program = _program()
    if not program:
        sys.stderr.write("dappy-embedded-launch: firmware .elf required\n")
        raise SystemExit(1)
    return subprocess.call([gdb, program])


def launch_ozone() -> int:
    if sys.platform == "win32":
        ozone = os.environ.get("OZONE") or shutil.which("Ozone.exe")
    else:
        ozone = os.environ.get("OZONE") or shutil.which("Ozone")
    ozone = _require(ozone, "Install SEGGER Ozone, set OZONE path")
    args = [ozone]
    program = _program()
    if program:
        args.append(program)
    return subprocess.call(args)


def launch_trace32() -> int:
    t32 = os.environ.get("TRACE32") or shutil.which("t32marm") or shutil.which("trace32")
    t32 = _require(t32, "Install Lauterbach TRACE32, set TRACE32")
    return subprocess.call([t32])


def launch_pls_ude() -> int:
    ude = os.environ.get("PLS_UDE") or shutil.which("ude")
    ude = _require(ude, "Install PLS UDE, set PLS_UDE")
    args = [ude]
    program = _program()
    if program:
        args.append(program)
    return subprocess.call(args)


_HANDLERS = {
    "openocd": launch_openocd,
    "jlink-gdbserver": launch_jlink_gdbserver,
    "avr-gdb": launch_avr_gdb,
    "stm32cube-gdb": launch_stm32cube_gdb,
    "segger-ozone": launch_ozone,
    "trace32-lauterbach": launch_trace32,
    "pls-ude": launch_pls_ude,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-embedded-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
