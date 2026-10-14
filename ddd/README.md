# ddd

[DDD](https://www.gnu.org/software/ddd/) — Data Display Debugger, graphical front-end for GDB/DBX on UNIX.

```bash
sudo dnf install ddd gdb
dap-cli debug repl --adapter ddd ./myapp
# Runs: ddd --gdb gdb ./myapp
```

Pair with **native-gdb** for headless DAP; DDD is the interactive GUI.
