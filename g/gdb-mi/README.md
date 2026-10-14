# gdb-mi

**GDB Machine Interface** — IDE bridge to GNU GDB (alias of `native-gdb` MI3 DAP).

```bash
pip install -e dappy-plugins/native-gdb
dap-cli debug repl --adapter gdb-mi ./a.out
```

Same bridge as `native-gdb`; this ID matches IDE `cppdbg` / `gdb-mi` conventions.
