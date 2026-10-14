# python-pudb — PuDB TUI debugger for Dappy

[PuDB](https://github.com/inducer/pudb) is a full-screen, keyboard-driven Python debugger for the terminal. Unlike debugpy, PuDB has **no native DAP implementation**. This plugin ships a small **DAP stdio bridge** (`pudb_dap_adapter`) that lets Dappy route sessions the same way as other adapters:

```bash
dap-cli debug repl --adapter python-pudb script.py
```

## Architecture

```
dap-cli / dap-proxy          pudb_dap_adapter (DAP)          PuDB TUI
      │    DAP stdio    │         runInTerminal / spawn          │
      └─────────────────┴──────────────────────────────────────────┘
```

1. Dappy sends `initialize` → `launch` → `configurationDone` over stdio.
2. The bridge spawns PuDB (`python -m pudb <program>`) via **`runInTerminal`** when the client supports it (Dappy proxy handles this headlessly).
3. You control debugging in the **PuDB terminal** — stepping, breakpoints, variables, stack.
4. DAP `continue` / `next` / `stackTrace` are acknowledged but **do not drive PuDB** (same class of limitation as [ipdab](https://github.com/mvds314/ipdab) for pdb/ipdb).

## Prerequisites

```bash
pip install -r requirements.txt
# or install the bridge package (recommended):
pip install -e .
```

Requires **Python 3.9+** and a real terminal for the PuDB UI.

## Launch modes

Set `mode` in launch arguments (defaults to `launch`):

| Mode | Behavior |
|------|----------|
| `launch` | `python -m pudb <program>` — start script under PuDB immediately |
| `remote` | `PYTHONBREAKPOINT=pudb.remote.set_trace` — script waits; connect with `telnet 127.0.0.1 6899` |
| `breakpoint` | `PYTHONBREAKPOINT=pudb.set_trace` — break at `sys.breakpointhook` sites / `breakpoint()` |

Remote mode env vars (also configurable in launch args):

- `remoteHost` → `PUDB_RDB_HOST` (default `127.0.0.1`)
- `remotePort` → `PUDB_RDB_PORT` (default `6899`)
- `termSize` → `PUDB_TERM_SIZE` (default `120x40`)

## Console / terminal handling

PuDB is a **TUI** and cannot run in `internalConsole`. The manifest sets:

```yaml
console: externalTerminal
```

| `console` value | Bridge behavior |
|-----------------|-----------------|
| `externalTerminal` / `integratedTerminal` | Sends DAP `runInTerminal` reverse request (Dappy spawns the process; output logged under `$TMPDIR/dap-run-in-terminal/`) |
| Current process has a TTY | Spawns PuDB attached to the adapter's terminal |
| No TTY, no `runInTerminal` | Detached spawn with a warning — PuDB UI may be unusable |

**Recommendation:** Use `dap-cli debug repl` or `dap-proxy` (both declare `supportsRunInTerminalRequest: true`) rather than piping stdio from a non-terminal client.

## Local development

```bash
export DAP_PLUGINS_DIR=/path/to/dappy-plugins
export PYTHONPATH=/path/to/dappy-plugins/python-pudb${PYTHONPATH:+:$PYTHONPATH}

# Validate manifest
dap-cli plugin show python-pudb

# Debug a script (needs a terminal for PuDB)
dap-cli debug repl --adapter python-pudb ./examples/hello.py
```

Alternative wrapper (no PYTHONPATH):

```bash
/path/to/dappy-plugins/python-pudb/adapter/pudb-dap-adapter
```

Use `dap-cli debug repl --adapter-cmd /path/to/pudb-dap-adapter ...` if the `-m pudb_dap_adapter` module is not installed.

## Registry install

```bash
rqp install dappy python-pudb
pip install -e ~/.config/dap/plugins/python-pudb
```

## Limitations

- **No DAP control path** — PuDB owns the terminal; the bridge only launches and monitors the process.
- **No source-level DAP breakpoints** — set breakpoints inside PuDB (`b` key) or use `mode: remote` / `mode: breakpoint`.
- **No variable/stack sync** — DAP `stackTrace` / `variables` return placeholders so REPL init succeeds; real data is in PuDB.
- **`internalConsole` unsupported** — will not render the TUI.
- **Windows** — PuDB targets Unix terminals; use WSL or remote mode with telnet.
- **Forked processes** — use `pudb.forked.set_trace` manually in child code (not automated by this plugin).

## Files

| File | Purpose |
|------|---------|
| `plugin.yaml` | Dappy manifest (`launchTypes: [python-pudb]`, `fileExtensions: [py]`) |
| `pudb_dap_adapter/` | DAP stdio bridge (Python, stdlib-only) |
| `attachment.yaml` | REPL hints for `raise`, `pudb.set_trace`, remote breakpoints |
| `requirements.txt` | Runtime deps (`pudb`) |
| `pyproject.toml` | Installable package + `pudb-dap-adapter` console script |
