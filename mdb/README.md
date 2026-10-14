# mdb

**MDB** — Modular Debugger for Solaris and illumos (kernel, crash dumps, live processes).

```bash
# On illumos/Solaris
mdb -k          # kernel
mdb core.12345  # crash dump
dap-cli debug repl --adapter mdb crash.dump
```

Not available on Linux — use **native-gdb** or **kadb-ddb** on BSD.
