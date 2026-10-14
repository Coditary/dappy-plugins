"""Launchers for audio and DSP debugging tools."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-audio-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_juce_plugin_host() -> int:
    host = os.environ.get("JUCE_PLUGIN_HOST") or os.environ.get("PLUGIN_HOST")
    plugin = _program()
    for name in ("AudioPluginHost", "pluginhost", "carla"):
        path = host if host else shutil.which(name)
        if path:
            args = [path]
            if plugin and plugin.endswith((".vst3", ".so", ".dll", ".component")):
                args.append(plugin)
            return _run(args)
    return _info(
        "JUCE Audio Plugin Host",
        [
            "Test VST/AU/LV2 plugins and debug DSP in real time.",
            "Build JUCE AudioPluginHost from juce.com/examples.",
            "Alt: Carla, REAPER, or Bitwig for plugin hosting.",
            "Set JUCE_PLUGIN_HOST path.",
        ],
    )


def launch_puredata_maxmsp() -> int:
    for var, names in (
        ("PUREDATA", ("pd", "puredata")),
        ("MAX_MSP", ("max",)),
    ):
        custom = os.environ.get(var)
        if custom:
            return _run([custom])
        for name in names:
            path = shutil.which(name)
            if path:
                args = [path]
                program = _program()
                if program and program.endswith(".pd"):
                    args.append(program)
                return _run(args)
    return _info(
        "Pure Data / Max/MSP",
        [
            "Visual audio/video programming — errors on patch cords.",
            "Pure Data: pd -lib script.pd — watch Pd console.",
            "Max/MSP: Max window → Max Console for errors.",
            "Set PUREDATA or MAX_MSP path.",
        ],
    )


_HANDLERS = {
    "juce-plugin-host": launch_juce_plugin_host,
    "puredata-maxmsp": launch_puredata_maxmsp,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-audio-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
