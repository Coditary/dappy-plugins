# valgrind-memcheck

Low-level memory analysis with [Valgrind](https://valgrind.org) Memcheck — not a line debugger, but essential for C/C++.

## Usage

```bash
dap-cli debug repl --target valgrind-memcheck -- ./myapp
# Uses builtin gdb-remote adapter to attach to vgdb
```

## What it finds

- Buffer overflows
- Use-after-free
- Memory leaks
- Invalid reads/writes

## Requirements

- `valgrind` on PATH
- `gdb-remote` adapter (builtin in Dappy)

## Notes

- Program runs ~10–50× slower under Valgrind.
- For breakpoints in your code, combine with `native-gdb` after vgdb attach.
