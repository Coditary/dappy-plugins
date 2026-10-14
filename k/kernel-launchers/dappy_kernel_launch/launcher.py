"""Launchers for kernel, low-level, and hypervisor debuggers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-kernel-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_kd_kdbg() -> int:
    if sys.platform != "win32":
        return _info(
            "KD/KDBG",
            [
                "Windows NT / ReactOS kernel debugger (kd.exe, KDBG).",
                "WinDbg kernel debugging: windbg-cdb plugin.",
                "ReactOS: KDBG in debug builds.",
            ],
        )
    kd = os.environ.get("KD") or shutil.which("kd.exe") or shutil.which("windbg.exe")
    if kd:
        args = [kd]
        dump = _program() or os.environ.get("KERNEL_DUMP", "")
        if dump:
            args.extend(["-z", dump])
        return _run(args)
    return _info(
        "KD/KDBG",
        [
            "Install Windows Debugging Tools (kd.exe / WinDbg).",
            "Local kernel: bcdedit /debug on",
            "Set KD path or use windbg-cdb plugin.",
        ],
    )


def launch_kdb_linux() -> int:
    return _info(
        "Linux KDB",
        [
            "In-kernel text debugger — active on panic or via serial.",
            "Boot: kgdboc=… or echo g > /proc/sysrq-trigger (if enabled).",
            "Config: CONFIG_KDB — mostly superseded by KGDB.",
            "Docs: Documentation/dev-tools/kgdb.rst in kernel tree.",
        ],
    )


def launch_kgdb() -> int:
    gdb = shutil.which("gdb")
    port = os.environ.get("KGDB_PORT", os.environ.get("QEMU_GDB_PORT", "1234"))
    if gdb:
        vmlinux = _program() or os.environ.get("VMLINUX", "vmlinux")
        if os.path.isfile(vmlinux):
            return _run([gdb, vmlinux, "-ex", f"target remote :{port}"])
        return _run([gdb, "-ex", f"target remote :{port}"])
    return _info(
        "KGDB",
        [
            "Debug Linux kernel over serial/gdb-remote from second machine.",
            "Kernel: CONFIG_KGDB, kgdboc=ttyS0,115200",
            f"Host: gdb vmlinux -ex 'target remote :{port}'",
            "Pair with qemu-gdb-stub or hardware serial.",
        ],
    )


def launch_libvmi() -> int:
    vmi = shutil.which("vmi-process") or shutil.which("vmifs")
    if vmi:
        return _run([vmi])
    return _info(
        "LibVMI",
        [
            "Virtual Machine Introspection — observe guest without in-guest agents.",
            "Install libvmi — Xen/KVM memory introspection.",
            "Tools: vmi-process, rekall, volatility3 with VMI plugins.",
            "Docs: https://libvmi.com/",
        ],
    )


def launch_hyperdbg() -> int:
    hyperdbg = os.environ.get("HYPERDBG") or shutil.which("hyperdbg-cli.exe") or shutil.which("hyperdbg")
    if hyperdbg:
        args = [hyperdbg]
        program = _program()
        if program:
            args.append(program)
        return _run(args)
    return _info(
        "HyperDbg",
        [
            "Hypervisor-based stealth debugger (VT-x/AMD-V) for Windows.",
            "https://hyperdbg.org/ — open-source, ring -1 debugging.",
            "Set HYPERDBG to hyperdbg-cli path.",
        ],
    )


_HANDLERS = {
    "kd-kdbg": launch_kd_kdbg,
    "kdb-linux": launch_kdb_linux,
    "kgdb": launch_kgdb,
    "libvmi": launch_libvmi,
    "hyperdbg": launch_hyperdbg,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-kernel-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
