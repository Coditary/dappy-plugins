# dotnet-coreclr

Native **.NET / CoreCLR** debugging via [netcoredbg](https://github.com/Samsung/netcoredbg).

```bash
# Install netcoredbg (package manager or build from source)
dap-cli debug repl --adapter dotnet-coreclr ./MyApp.dll
```

Alternative: Microsoft `vsdbg` — set `NETCOREDBG=vsdbg` if using VS debugger binary.

Supports C#, F#, VB.NET with portable PDB symbols.
