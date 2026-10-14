# ilspy

[ILSpy](https://github.com/icsharpcode/ILSpy) — .NET decompiler with debugging helpers.

Primarily a decompiler; use **dnspy** or **dotnet-coreclr** for full debugging.

```powershell
set ILSPY=C:\Tools\ILSpy\ILSpy.exe
dap-cli debug repl --adapter ilspy MyLib.dll
```
