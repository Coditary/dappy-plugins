# rr-replay

Time-travel debugging with [Mozilla rr](https://rr-project.org) for C, C++, Rust, and Zig.

## Workflow

```bash
# 1. Record
rr record ./myapp
# or: dap-cli debug repl --target rr-record -- ./myapp

# 2. Replay-debug
export RR_TRACE_DIR=./myapp-0   # rr output directory
export DAPPY_RR_TRACE_DIR=$RR_TRACE_DIR
dap-cli debug repl --adapter rr-replay ./myapp
```

## Requirements

- `rr` (Linux, x86_64/aarch64)
- `lldb-dap` (LLVM)

## Features

- Deterministic replay — reproduce Heisenbugs
- Reverse continue / reverse step (via lldb under rr)
- Works with DWARF binaries from C/C++/Rust/Zig

## Limitations

- Recording is Linux-only; replay plugin proxies to `rr replay -- lldb-dap`.
- Set `DAPPY_RR_TRACE_DIR` to the trace directory before launching.
