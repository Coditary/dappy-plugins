"""Stdio DAP bridge for Python's stdlib pdb/bdb debugger."""

__version__ = "0.1.0"


def main() -> None:
    from dappy_pdb_bridge.adapter import run_adapter

    run_adapter()
