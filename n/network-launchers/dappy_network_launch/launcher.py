"""Launchers for protocol, network, and API debugging tools."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-network-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_wireshark() -> int:
    for name in ("wireshark", "wireshark-qt"):
        path = shutil.which(name)
        if path:
            args = [path]
            program = _program()
            if program and program.endswith((".pcap", ".pcapng", ".cap")):
                args.append(program)
            return _run(args)
    return _info(
        "Wireshark",
        [
            "Packet analyzer — install wireshark package.",
            "Capture: wireshark or tshark -i eth0",
            "Open capture file: wireshark capture.pcapng",
        ],
    )


def launch_tcpdump() -> int:
    tcpdump = shutil.which("tcpdump")
    if not tcpdump:
        return _info("tcpdump", ["Install tcpdump (libpcap)."], code=1)
    iface = os.environ.get("TCPDUMP_IFACE", "any")
    outfile = _program() or os.environ.get("TCPDUMP_OUT", "capture.pcap")
    return _run([tcpdump, "-i", iface, "-w", outfile, "-c", os.environ.get("TCPDUMP_COUNT", "100")])


def launch_wireshark_stream() -> int:
    tshark = shutil.which("tshark")
    program = _program()
    if tshark and program and program.endswith((".pcap", ".pcapng")):
        follow = os.environ.get("WIRESHARK_FOLLOW", "tcp")
        return _run([tshark, "-r", program, "-q", "-z", f"follow,{follow},ascii,0"])
    return _info(
        "Wireshark Follow Stream",
        [
            "High-level protocol stream view (Follow TCP/UDP Stream).",
            "Wireshark UI: right-click packet → Follow → TCP Stream.",
            "CLI: tshark -r cap.pcap -q -z follow,tcp,ascii,0",
            "Env: WIRESHARK_FOLLOW=tcp|udp",
        ],
    )


def launch_postman_bruno() -> int:
    for var, names in (
        ("POSTMAN", ("postman",)),
        ("BRUNO", ("bruno",)),
    ):
        custom = os.environ.get(var)
        if custom:
            return _run([custom])
        for name in names:
            path = shutil.which(name)
            if path:
                return _run([path])
    return _info(
        "Postman / Bruno",
        [
            "HTTP/REST API mock and debug clients.",
            "Install Postman or Bruno (open-source).",
            "Import OpenAPI collection; use Mock servers for webhooks.",
        ],
    )


def launch_mitmproxy() -> int:
    mitm = shutil.which("mitmproxy") or shutil.which("mitmdump") or shutil.which("mitmweb")
    if mitm:
        port = os.environ.get("MITM_PORT", "8080")
        if "mitmweb" in mitm:
            return _run([mitm, "--listen-port", port])
        return _run([mitm, "-p", port])
    return _info(
        "mitmproxy",
        [
            "Interactive SSL-capable MITM proxy for HTTP/HTTPS.",
            "pip install mitmproxy",
            "mitmproxy -p 8080 — set HTTP_PROXY for your app.",
        ],
    )


def launch_wireshark_lua() -> int:
    lua_script = _program() or os.environ.get("WIRESHARK_LUA_DISSECTOR")
    if lua_script and os.path.isfile(lua_script):
        plugins = os.environ.get("WIRESHARK_USER_PLUGINS", os.path.expanduser("~/.local/lib/wireshark/plugins"))
        return _info(
            "Wireshark Lua Dissector",
            [
                f"Copy {lua_script} to {plugins}/",
                "Restart Wireshark; dissector loads automatically.",
                "Docs: https://www.wireshark.org/docs/wsdg_html_chunked/wslua.html",
            ],
        )
    return _info(
        "Wireshark Lua Dissector",
        [
            "Custom protocol dissectors in Lua.",
            "Place .lua in ~/.local/lib/wireshark/plugins/",
            "Pass .lua file as program for install path hint.",
        ],
    )


_HANDLERS = {
    "wireshark": launch_wireshark,
    "tcpdump": launch_tcpdump,
    "wireshark-stream": launch_wireshark_stream,
    "postman-bruno": launch_postman_bruno,
    "mitmproxy": launch_mitmproxy,
    "wireshark-lua": launch_wireshark_lua,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-network-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
