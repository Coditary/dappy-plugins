"""Launchers for dynamic instrumentation and malware analysis tools."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-instrumentation-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_cuckoo_sandbox() -> int:
    cuckoo = shutil.which("cuckoo") or shutil.which("cuckoo.py")
    program = _program()
    if cuckoo and program:
        return _run([cuckoo, "submit", program])
    return _info(
        "Cuckoo Sandbox",
        [
            "Automated malware analysis sandbox.",
            "pip install cuckoo — submit sample for behavioral report.",
            "Modern fork: Cuckoo Sandbox 2 / CAPE.",
        ],
    )


def launch_any_run() -> int:
    return _info(
        "Any.Run",
        [
            "Interactive online malware analyzer (browser).",
            "https://app.any.run/ — upload sample for live debug.",
            "No local binary; use for cloud interactive analysis.",
        ],
    )


def launch_api_monitor() -> int:
    if sys.platform != "win32":
        return _info("API Monitor", ["Windows only — rohitab API Monitor."], code=1)
    apim = os.environ.get("API_MONITOR") or shutil.which("apimonitor-x64.exe")
    program = _program()
    if apim:
        args = [apim]
        if program:
            args.append(program)
        return _run(args)
    return _info(
        "API Monitor",
        [
            "Intercept Windows API calls in real time.",
            "Download from rohitab.com; set API_MONITOR path.",
        ],
    )


def launch_frida() -> int:
    frida = shutil.which("frida") or shutil.which("frida-trace")
    program = _program()
    target = os.environ.get("FRIDA_TARGET", program)
    if frida and target:
        if "trace" in frida:
            return _run([frida, "-i", "open", target])
        return _run([frida, target])
    if frida:
        return _run([frida, "--version"])
    return _info(
        "Frida",
        [
            "Dynamic instrumentation — hook native/mobile apps at runtime.",
            "pip install frida-tools",
            "frida -l script.js com.example.app",
            "frida-trace -i open* target_process",
        ],
    )


def launch_intel_pin() -> int:
    pin = os.environ.get("PIN_ROOT")
    pintool = _program()
    if pin and pintool and os.path.isfile(pintool):
        pin_bin = os.path.join(pin, "pin")
        if os.path.isfile(pin_bin):
            target = os.environ.get("PIN_TARGET", "./a.out")
            return _run([pin_bin, "-t", pintool, "--", target])
    return _info(
        "Intel PIN",
        [
            "Dynamic binary instrumentation framework.",
            "Download PIN kit; set PIN_ROOT.",
            "pin -t mytool.so -- ./program",
            "Docs: https://www.intel.com/content/www/us/en/developer/articles/tool/pin-a-dynamic-binary-instrumentation-tool.html",
        ],
    )


_HANDLERS = {
    "cuckoo-sandbox": launch_cuckoo_sandbox,
    "any-run": launch_any_run,
    "api-monitor": launch_api_monitor,
    "frida": launch_frida,
    "intel-pin": launch_intel_pin,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-instrumentation-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
