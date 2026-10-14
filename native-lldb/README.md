# native-lldb

Dappy plugin for [LLVM lldb-dap](https://lldb.llvm.org/use/lldbdap.html) — the standard DAP adapter for LLDB.

Supports C, C++, Rust, and Zig binaries with DWARF debug info.

## Install

```bash
# Fedora/LLVM
sudo dnf install lldb lldb-dap

rqp install dappy native-lldb
```

## Usage

```bash
dap-cli debug repl --adapter native-lldb ./myapp
dap-cli debug repl --adapter native-lldb ./target/debug/myapp   # Rust
```

## Environment

| Variable | Effect |
|----------|--------|
| `LLDB_DAP` | Override lldb-dap binary path (also patched by dappy-core for `rust` plugin) |

## Notes

- Distinct from the `rust` plugin (same backend, broader file routing).
- On macOS lldb-dap is the default LLDB DAP entry point.
