# python-madbg — Dappy plugin for [madbg](https://github.com/kmaork/madbg)

Remote/preemptive Python debugger integration for [Dappy](https://github.com/Coditary/Dappy).

madbg does **not** speak DAP natively. This package ships a stdio **DAP bridge** (`madbg_dap`) that:

1. **Launch** — spawns `madbg run` and connects over TCP (default `127.0.0.1:3513`)
2. **Attach** — injects into a running PID via `madbg.attach_to_process` semantics
3. **Connect** — joins an already listening madbg server (`set_trace`, `madbg connect`)

## Requirements

- Linux
- Python ≥ 3.8
- `madbg` installed in **both** the adapter environment and the target process interpreter (attach)

```bash
pip install -r requirements.txt
# or: pip install madbg && pip install -e .
```

## Install manifest

```bash
rqp install dappy python-madbg
# optional attach/connect companions:
rqp install dappy python-madbg-attach
rqp install dappy madbg-connect
```

Dev override:

```bash
export DAP_PLUGINS_DIR=/path/to/dappy-plugins
pip install -e /path/to/dappy-plugins/python-madbg
```

## Manifests

| File | Plugin id | Mode |
|------|-----------|------|
| `plugin.yaml` | `python-madbg` | Launch (`madbg run`) |
| `attach-plugin.yaml` | `python-madbg-attach` | Attach by PID |
| `madbg-connect.yaml` | `madbg-connect` | TCP connect-only |

There is no `target.yaml`: madbg is not gdb-remote/RSP. Attach/connect use DAP `attach` via companion manifests (similar role to `rsp-attach`, but DAP-native).

## Test commands

```bash
# List / inspect
export DAP_PLUGINS_DIR=/path/to/dappy-plugins
dap-cli plugin list
dap-cli plugin show python-madbg

# Launch (stop at first line with --use-set-trace default)
dap-cli debug repl --adapter python-madbg ./script.py

# Attach to PID 12345
export MADBG_PID=12345
dap-cli debug repl --adapter python-madbg-attach -- /proc/12345/exe

# Connect to existing madbg server on default port
dap-cli debug repl --adapter madbg-connect -- ./script.py

# Headless proxy (editor integration)
dap-proxy --stdio --adapter python-madbg --program ./script.py

# Attach headless
dap-proxy --headless --adapter python-madbg-attach \
  --debug-request attach --debug-args '{"pid":12345,"program":"/path/to/script.py"}'
```

## Launch vs attach design

```
┌─────────────┐   DAP/stdio    ┌──────────────┐   TCP:3513   ┌─────────────┐
│ Dappy/Editor│◄──────────────►│ madbg_dap    │◄────────────►│ madbg server│
│ dap-cli     │                │ (bridge)     │  pickle+TTY  │ IPython pdb │
└─────────────┘                └──────┬───────┘              └──────▲──────┘
                                      │ spawn                        │
                               madbg run script.py              target process
                               madbg attach PID (inject)
```

- **Launch**: bridge spawns `python -m madbg run -i HOST -p PORT [-s] script.py`, waits for the TCP port, sends terminal metadata, relays I/O as DAP `output` events, emits `stopped` when a pdb prompt appears.
- **Attach (PID)**: bridge calls madbg inject (`_inject_set_trace`), then connects like `madbg connect`.
- **Connect**: bridge only connects to `host:port` (no spawn/inject).

The main `plugin.yaml` uses DAP `launch`. The bridge also accepts DAP `attach` when clients send it directly. Headless attach uses `python-madbg-attach` (`launch.request: attach`).

## Limitations

- **TTY bridge, not a full debugger mapping**: stack frames, scopes, and variables are minimal. Stepping sends pdb commands (`n`, `s`, `c`); evaluate relays expressions to the remote IPython debugger.
- **Linux only** (madbg platform support).
- **Attach risks**: madbg docs warn of possible deadlocks when attaching preemptively; not recommended for production.
- **Target must have madbg installed** for PID attach.
- **No native breakpoints via DAP**: use pdb `break` commands through evaluate/output, or IPython `%debug` workflows.
- **Single thread** reported to DAP (`threadId: 1`).
- Requires `pip install -e .` (or `madbg-dap-adapter` on `PATH`) so `python3 -m madbg_dap` resolves.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `PYTHON` | Python executable for adapter + madbg spawn (Dappy patches like debugpy) |
| `MADBG_PID` | Default PID for `python-madbg-attach` manifest |
| `DAP_PLUGINS_DIR` | Plugin discovery root |

## References

- [madbg README](https://github.com/kmaork/madbg)
- [Dappy AGENTS.md](../../AGENTS.md)
