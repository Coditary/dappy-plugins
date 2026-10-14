"""Launchers for Solidity/EVM smart contract debuggers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-blockchain-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_remix_debugger() -> int:
    remixd = shutil.which("remixd") or shutil.which("npx")
    project = _program() or os.getcwd()
    if remixd and remixd.endswith("npx"):
        return _run(
            [
                remixd,
                "@remix-project/remixd",
                "-s",
                project,
                "--remix-ide",
                os.environ.get("REMIX_IDE", "https://remix.ethereum.org"),
            ]
        )
    if remixd:
        return _run(
            [
                remixd,
                "-s",
                project,
                "--remix-ide",
                os.environ.get("REMIX_IDE", "https://remix.ethereum.org"),
            ]
        )
    return _info(
        "Remix Debugger",
        [
            "Ethereum/Solidity transaction debugger in Remix IDE.",
            "Open https://remix.ethereum.org → Debugger panel.",
            "Local bridge: npm install -g @remix-project/remixd",
            "remixd -s ./contracts --remix-ide https://remix.ethereum.org",
        ],
    )


def launch_forge_debugger() -> int:
    forge = shutil.which("forge")
    program = _program()
    if not forge:
        return _info(
            "Forge Debugger",
            [
                "Foundry line-based Solidity debugger.",
                "curl -L https://foundry.paradigm.xyz | bash && foundryup",
                "forge test --debug -vvv",
                "forge script Script.s.sol --debug",
            ],
            code=1,
        )
    if program and program.endswith(".sol"):
        if os.path.isfile(program):
            return _run([forge, "test", "--debug", "-vvv", "--match-path", program])
        return _run([forge, "script", program, "--debug", "-vvv"])
    return _run([forge, "test", "--debug", "-vvv"])


_HANDLERS = {
    "remix-debugger": launch_remix_debugger,
    "forge-debugger": launch_forge_debugger,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-blockchain-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
