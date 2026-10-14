# native-gdb

Dappy plugin for **GNU GDB** — the classic Linux debugger for C, C++, Rust, and Zig.

GDB has no official stdio DAP server; this plugin ships `dappy-gdb-dap`, a minimal MI3 bridge.

## Install

```bash
sudo dnf install gdb   # or apt install gdb

cd dappy-plugins/native-gdb && pip install -e .
rqp install dappy native-gdb
```

## Usage

```bash
dap-cli debug repl --adapter native-gdb ./myapp
export GDB=/path/to/cross-gdb   # optional cross-debugger
```

## vs native-lldb

| | GDB | LLDB |
|---|-----|------|
| Rust traits / modern C++ | older GDB can struggle | usually cleaner |
| Linux default | classic | growing (lldb-dap) |
| Time-travel | use `rr` plugin | rr + lldb |

## Limitations

- MI bridge covers launch, breakpoints, continue/step, basic stack — not full GDB feature parity.
- For gdb-remote / embedded targets use `gdbserver` + `gdb-remote` plugins instead.
