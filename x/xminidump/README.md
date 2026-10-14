# xminidump

Windows minidump analysis (Xminidump, Dumpert-style workflows).

```powershell
dap-cli debug repl --adapter xminidump crash.dmp
# Uses cdb -z crash.dmp when Debugging Tools installed
```

See also **windbg-cdb** plugin. Set `WINDBG_DUMP` for dump path.
