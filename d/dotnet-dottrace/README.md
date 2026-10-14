# dotnet-dottrace

[JetBrains dotTrace](https://www.jetbrains.com/profiler/dottrace/) — .NET profiler.

Analysis target (like `perf-record`), not a line debugger. Requires dotTrace CLI on PATH.

```bash
dottrace snapshot --save-to=app.dtps -- MyApp.exe
```

Use **dotnet-coreclr** for breakpoint debugging.
