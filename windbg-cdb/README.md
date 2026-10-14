# windbg-cdb

Dappy plugin for **Microsoft WinDbg** and **CDB** on Windows.

## Use cases

- Crash dump analysis (`.dmp`, minidumps)
- User-mode C/C++ debugging without an IDE
- Kernel debugging workflows (manual setup)

## Install (Windows)

```powershell
# Windows SDK → Debugging Tools for Windows
pip install -e dappy-plugins/windbg-cdb
rqp install dappy windbg-cdb
```

## Usage

```powershell
dap-cli debug repl --adapter windbg-cdb .\app.exe
set WINDBG_DUMP=C:\dumps\crash.dmp
dap-cli debug repl --adapter windbg-cdb .\app.exe
```

## Limitations

- **Windows only** — exits with a clear message on Linux/macOS.
- CDB has no stdio DAP; current launcher spawns interactive CDB. Full DAP bridge (cppvsdbg) planned.
- For cross-platform C/C++ on Linux use `native-gdb` or `native-lldb`.
