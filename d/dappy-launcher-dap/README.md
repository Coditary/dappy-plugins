# dappy-launcher-dap

Minimal DAP adapter that spawns the **real** debugger or tool named in each plugin manifest.

Many Dappy plugins wrap external programs (IDA, ocamldebug, JDB, …) that do not speak DAP
over stdio. This bridge completes the DAP handshake so `dap-cli debug repl` and headless init
succeed, then runs the configured launcher with `DAPPY_PROGRAM` set from the launch request.

Install:

```bash
rqp install dappy dappy-launcher-dap
# or: pip install -e dappy-launcher-dap/
```

Typical manifest wiring:

```yaml
adapter:
  transport: stdio
  command: python3
  args:
    - -m
    - dappy_launcher_dap
    - dappy-re-launch
    - ida-pro
```
