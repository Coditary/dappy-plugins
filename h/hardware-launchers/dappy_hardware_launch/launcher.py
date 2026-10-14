"""Launchers for firmware, FPGA, and emulator debugging tools."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-hardware-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_saleae_logic() -> int:
    for var in ("LOGIC2", "SALEAE_LOGIC"):
        path = os.environ.get(var)
        if path:
            return _run([path])
    for name in ("Logic", "logic2"):
        path = shutil.which(name)
        if path:
            return _run([path])
    return _info(
        "Saleae Logic",
        [
            "Digital logic analyzer — SPI, I2C, UART protocol decode.",
            "Install Logic 2 from saleae.com; set LOGIC2 path.",
        ],
    )


def launch_sigrok_pulseview() -> int:
    pv = shutil.which("pulseview") or shutil.which("sigrok-cli")
    if pv:
        args = [pv]
        program = _program()
        if program and "sigrok" in pv:
            args.extend(["-i", program])
        elif program:
            args.append(program)
        return _run(args)
    return _info(
        "Sigrok / PulseView",
        [
            "Open-source logic analyzer software.",
            "dnf install pulseview sigrok-cli",
            "pulseview — capture and decode protocols.",
        ],
    )


def launch_vivado_modelsim() -> int:
    for var, names in (
        ("VIVADO", ("vivado",)),
        ("MODELSIM", ("vsim", "modelsim")),
    ):
        custom = os.environ.get(var)
        if custom:
            return _run([custom])
        for name in names:
            path = shutil.which(name)
            if path:
                program = _program()
                args = [path]
                if program and name == "vsim":
                    args.extend(["-do", f"vsim {program}"])
                return _run(args)
    return _info(
        "Vivado / ModelSim",
        [
            "VHDL/Verilog simulation and waveform debug.",
            "Xilinx Vivado Simulator or Siemens ModelSim.",
            "Set VIVADO or MODELSIM; use gtkwave for VCD dumps.",
        ],
    )


def launch_openvera_uvm() -> int:
    return _info(
        "OpenVera / UVM",
        [
            "Microchip/verification debug — UVM testbench simulation.",
            "Use ModelSim/Questa with UVM libraries.",
            "Env: UVM_HOME, QUESTA — commercial EDA toolchain.",
        ],
    )


def launch_qemu_gdb_stub() -> int:
    qemu = shutil.which("qemu-system-x86_64") or shutil.which("qemu-system-aarch64")
    program = _program()
    if qemu and program:
        port = os.environ.get("QEMU_GDB_PORT", "1234")
        return _run([qemu, "-s", "-S", "-kernel", program, "-nographic"])
    gdb = shutil.which("gdb")
    if gdb:
        port = os.environ.get("QEMU_GDB_PORT", "1234")
        return _info(
            "QEMU GDB stub",
            [
                f"QEMU with -s -S exposes gdb-remote on :{port}",
                f"Attach: gdb -ex 'target remote :{port}'",
                "Or use Dappy target: qemu-x86-kernel",
            ],
        )
    return _info(
        "QEMU GDB stub",
        [
            "qemu-system-x86_64 -s -S -kernel vmlinuz",
            "See also dappy target qemu-x86-kernel.",
        ],
    )


def launch_bochs_debugger() -> int:
    bochs = shutil.which("bochs")
    program = _program()
    if bochs:
        args = [bochs]
        if program and program.endswith(".bxrc"):
            args.extend(["-f", program])
        return _run(args)
    return _info(
        "Bochs debugger",
        [
            "x86 emulator with built-in CPU debugger.",
            "bochs -q -f bochsrc.txt — Ctrl-C in console for debug prompt.",
            "Powerful for bootloader/kernel development.",
        ],
    )


def launch_mame_debugger() -> int:
    mame = shutil.which("mame") or shutil.which("mame64")
    program = _program()
    if mame:
        args = [mame, "-debug"]
        if program:
            args.append(program)
        return _run(args)
    return _info(
        "MAME debugger",
        [
            "Arcade emulator with CPU/memory debugger for RE.",
            "mame -debug pacman — F12 debugger overlay.",
            "Docs: https://docs.mamedev.org/debugging/",
        ],
    )


def launch_higan_bsnes() -> int:
    for name in ("bsnes", "higan", "ares"):
        path = shutil.which(name)
        if path:
            args = [path]
            program = _program()
            if program:
                args.append(program)
            return _run(args)
    return _info(
        "higan / bsnes",
        [
            "Cycle-accurate SNES emulators with debugger.",
            "Tools → Debugger in bsnes-qt.",
            "Install bsnes or higan from distro/packages.",
        ],
    )


_HANDLERS = {
    "saleae-logic": launch_saleae_logic,
    "sigrok-pulseview": launch_sigrok_pulseview,
    "vivado-modelsim": launch_vivado_modelsim,
    "openvera-uvm": launch_openvera_uvm,
    "qemu-gdb-stub": launch_qemu_gdb_stub,
    "bochs-debugger": launch_bochs_debugger,
    "mame-debugger": launch_mame_debugger,
    "higan-bsnes": launch_higan_bsnes,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-hardware-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
