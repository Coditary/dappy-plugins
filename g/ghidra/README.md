# ghidra

[Ghidra](https://ghidra-sre.org/) — NSA open-source SRE framework with integrated debugger.

```bash
export GHIDRA_INSTALL_DIR=/opt/ghidra
dap-cli debug repl --adapter ghidra firmware.bin
```

Headless import via `analyzeHeadless` when `GHIDRA_PROJECT` is set.
