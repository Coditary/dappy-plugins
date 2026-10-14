# dnspy

[dnSpyEx](https://github.com/dnSpyEx/dnSpy) — .NET debugger, decompiler, and assembly editor.

**Windows only.**

```powershell
set DNSPY=C:\Tools\dnSpy\dnSpy.exe
dap-cli debug repl --adapter dnspy MyApp.exe
```

No public DAP API — opens dnSpy GUI. Use `dotnet-coreclr` for headless DAP on Linux/macOS.
