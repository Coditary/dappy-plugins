# crystal-debugger

[Crystal](https://crystal-lang.org/) — LLVM-native debugging.

```bash
crystal run --debug app.cr
# Or: crystal build -g app.cr && lldb ./app
dap-cli debug repl --adapter crystal-debugger app.cr
```

Full DAP via **`native-lldb`** on compiled binary.
