"""Launchers for mobile and HTTP debugging tools."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def launch_android_studio() -> int:
    studio = os.environ.get("ANDROID_STUDIO") or shutil.which("studio")
    if not studio:
        sys.stderr.write(
            "android-studio: open Android Studio Profiler manually, or set ANDROID_STUDIO\n"
            "  adb shell am profile start <pkg>\n"
        )
        raise SystemExit(1)
    return subprocess.call([studio])


def launch_xcode_instruments() -> int:
    if sys.platform != "darwin":
        sys.stderr.write("xcode-instruments: requires macOS + Xcode\n")
        raise SystemExit(1)
    instruments = shutil.which("instruments") or shutil.which("xcrun")
    if instruments and instruments.endswith("xcrun"):
        return subprocess.call(["xcrun", "instruments", "-h"])
    if instruments:
        return subprocess.call([instruments, "-h"])
    sys.stderr.write("Install Xcode command-line tools\n")
    raise SystemExit(1)


def launch_charles_fiddler() -> int:
    for var, name in (("CHARLES", "Charles"), ("FIDDLER", "Fiddler")):
        path = os.environ.get(var) or shutil.which(f"{name}.exe") or shutil.which(name.lower())
        if path:
            return subprocess.call([path])
    sys.stderr.write("Set CHARLES or FIDDLER to proxy executable\n")
    raise SystemExit(1)


def launch_proxyman() -> int:
    proxyman = os.environ.get("PROXYMAN") or shutil.which("Proxyman")
    proxyman = proxyman or ("/Applications/Proxyman.app/Contents/MacOS/Proxyman" if sys.platform == "darwin" else None)
    if not proxyman or not os.path.exists(proxyman):
        sys.stderr.write("Install Proxyman, set PROXYMAN path\n")
        raise SystemExit(1)
    return subprocess.call([proxyman])


def launch_instruments_profiler() -> int:
    if sys.platform != "darwin":
        sys.stderr.write("instruments-profiler: requires macOS + Xcode\n")
        raise SystemExit(1)
    template = os.environ.get("INSTRUMENTS_TEMPLATE", "Time Profiler")
    instruments = shutil.which("instruments")
    program = _program()
    if instruments and program:
        return subprocess.call(
            [instruments, "-t", template, "-D", program, "-l", os.environ.get("INSTRUMENTS_DURATION", "30000")]
        )
    if shutil.which("xcrun"):
        return subprocess.call(["xcrun", "xctrace", "list", "templates"])
    sys.stderr.write(
        "instruments-profiler: install Xcode; templates: Time Profiler, Leaks, Core Animation\n"
        "  instruments -t 'Time Profiler' -D MyApp.app\n"
    )
    raise SystemExit(1)


def launch_flipper() -> int:
    flipper = shutil.which("flipper-server") or shutil.which("flipper")
    if not flipper:
        sys.stderr.write(
            "flipper: install Flipper desktop (https://fbflipper.com)\n"
            "  flipper-server or flipper CLI on PATH\n"
        )
        raise SystemExit(1)
    return subprocess.call([flipper])


_HANDLERS = {
    "android-studio": launch_android_studio,
    "xcode-instruments": launch_xcode_instruments,
    "instruments-profiler": launch_instruments_profiler,
    "charles-fiddler": launch_charles_fiddler,
    "proxyman": launch_proxyman,
    "flipper": launch_flipper,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-mobile-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
