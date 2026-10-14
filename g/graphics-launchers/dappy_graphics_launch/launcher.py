"""Launchers for GPU, shader, and game-engine debugging tools."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-graphics-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_renderdoc() -> int:
    for cmd in ("renderdoccmd", "qrenderdoc"):
        path = shutil.which(cmd)
        if path:
            program = _program()
            args = [path]
            if program and cmd == "renderdoccmd":
                args.extend(["capture", program])
            elif program:
                args.append(program)
            return _run(args)
    return _info(
        "RenderDoc",
        [
            "Open-source GPU debugger (Vulkan, OpenGL, D3D11/12).",
            "Install RenderDoc, then: renderdoccmd capture ./game",
            "Env: RENDERDOC_CMD, QRENDERDOC",
            "Docs: https://renderdoc.org/docs/",
        ],
    )


def launch_pix() -> int:
    if sys.platform != "win32":
        return _info("PIX", ["Windows/Xbox only — DirectX 12 GPU debugger."], code=1)
    pix = os.environ.get("PIX") or shutil.which("PIX.exe") or shutil.which("WinPixGpuCapturer.exe")
    if pix:
        args = [pix]
        program = _program()
        if program:
            args.append(program)
        return _run(args)
    return _info(
        "PIX",
        [
            "Microsoft DirectX 12 / Xbox graphics debugger.",
            "Install PIX from Microsoft Store or Windows SDK.",
            "Set PIX to pix.exe path.",
        ],
    )


def launch_nvidia_nsight() -> int:
    for var, names in (
        ("NSIGHT_GFX", ("nsight-gfx", "nsight-gfx-ui")),
        ("NSYS", ("nsys",)),
        ("NSIGHT_SYSTEMS", ("nsys-ui",)),
    ):
        custom = os.environ.get(var)
        if custom:
            return _run([custom, _program()] if _program() else [custom])
        for name in names:
            path = shutil.which(name)
            if path:
                args = [path]
                program = _program()
                if program:
                    args.append(program)
                return _run(args)
    return _info(
        "NVIDIA Nsight",
        [
            "Nsight Graphics (frame debugging) + Nsight Systems (profiling).",
            "Install NVIDIA Nsight suite; set NSIGHT_GFX or NSYS.",
            "Docs: https://developer.nvidia.com/nsight-graphics",
        ],
    )


def launch_amd_rgp() -> int:
    rgp = os.environ.get("AMD_RGP") or shutil.which("RadeonGPUProfiler") or shutil.which("rgp")
    if rgp:
        args = [rgp]
        program = _program()
        if program:
            args.append(program)
        return _run(args)
    return _info(
        "AMD RGP",
        [
            "Radeon GPU Profiler and AMD Developer Tool Suite.",
            "Capture with RGP, analyze in Radeon GPU Profiler UI.",
            "Env: AMD_RGP — Docs: https://gpuopen.com/rgp/",
        ],
    )


def launch_intel_gpa() -> int:
    for name in ("gpa-gui", "gpa-system", "intel_gpa"):
        path = os.environ.get("INTEL_GPA") if name == "gpa-gui" else None
        path = path or shutil.which(name)
        if path:
            args = [path]
            program = _program()
            if program and name == "gpa-system":
                args.extend(["analyze", program])
            elif program:
                args.append(program)
            return _run(args)
    return _info(
        "Intel GPA",
        [
            "Intel Graphics Performance Analyzers.",
            "Install Intel GPA; set INTEL_GPA or use gpa-gui.",
            "Docs: https://www.intel.com/content/www/us/en/developer/tools/graphics-performance-analyzers/",
        ],
    )


def launch_xcode_gpu_capture() -> int:
    if sys.platform != "darwin":
        return _info("Xcode GPU Frame Capture", ["macOS + Xcode required (Metal)."], code=1)
    xcrun = shutil.which("xcrun")
    if xcrun:
        return _info(
            "Xcode GPU Frame Capture",
            [
                "Use Xcode → Debug → Capture GPU Frame (Metal apps).",
                "Or: xcrun metal-capture in Xcode 15+ workflow.",
                "Program path passed for reference: " + (_program() or "(none)"),
            ],
        )
    return _info("Xcode GPU Frame Capture", ["Install Xcode command-line tools."], code=1)


def launch_unity_profiler() -> int:
    unity = os.environ.get("UNITY_EDITOR") or shutil.which("Unity")
    if unity:
        args = [unity]
        project = _program()
        if project:
            args.extend(["-projectPath", project])
        return _run(args)
    return _info(
        "Unity Profiler",
        [
            "Unity Editor profiler and debugger.",
            "Set UNITY_EDITOR to Unity binary or open project in Unity Hub.",
            "Window → Analysis → Profiler; attach to player build.",
            "Docs: https://docs.unity3d.com/Manual/Profiler.html",
        ],
    )


def launch_unreal_insight() -> int:
    for var, names in (
        ("UNREAL_INSIGHTS", ("UnrealInsights",)),
        ("UNREAL_EDITOR", ("UnrealEditor", "UnrealEditor-Cmd")),
    ):
        custom = os.environ.get(var)
        if custom:
            return _run([custom])
        for name in names:
            path = shutil.which(name)
            if path:
                return _run([path, "-trace=cpu,gpu,frame,log"])
    return _info(
        "Unreal Insight",
        [
            "Unreal Engine Insights + Visual Logger.",
            "Launch UnrealInsights.exe or editor with -trace=…",
            "Env: UNREAL_INSIGHTS, UNREAL_EDITOR",
            "Docs: https://docs.unrealengine.com/en-US/unreal-insights/",
        ],
    )


_HANDLERS = {
    "renderdoc": launch_renderdoc,
    "pix": launch_pix,
    "nvidia-nsight": launch_nvidia_nsight,
    "amd-rgp": launch_amd_rgp,
    "intel-gpa": launch_intel_gpa,
    "xcode-gpu-capture": launch_xcode_gpu_capture,
    "unity-profiler": launch_unity_profiler,
    "unreal-insight": launch_unreal_insight,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-graphics-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
