# python-ipdb (Dappy plugin)

Debug Python with [ipdb](https://github.com/gotcha/ipdb) through [ipdab](https://github.com/mvds314/ipdab), a TCP-based DAP server that mirrors the terminal debugger.

This plugin is **independent** from the built-in `python` (debugpy) adapter.

## How it works

| Layer | Role |
|-------|------|
| **Dappy** | stdio DAP client (`dap-cli`, editor proxy, MCP) |
| **`dappy-ipdb-bridge`** | stdio ↔ TCP relay + program launcher |
| **ipdab** | DAP server on `127.0.0.1:9000` (default) |
| **ipdb** | Interactive terminal debugger |

ipdab does **not** speak stdio DAP. When `ipdab.set_trace()` runs (or the bundled launcher stops at the first line of your script), ipdab starts a TCP DAP server. The bridge connects Dappy to that server.

### Observation-only control

ipdab can report stack frames, locals, globals, and evaluate expressions over DAP. It **cannot** execute continue/step/next from the IDE — ipdb owns the terminal prompt. Use the ipdb REPL (`c`, `n`, `s`, `q`, …) for control; use Dappy for inspection.

## Install

### 1. Python dependencies

```bash
pip install ipdb ipdab
```

ipdab currently requires `ipython<9.1` (see [ipdab on PyPI](https://pypi.org/project/ipdab/)). Use **Python 3.9–3.12**; Python 3.13+ may hit ipdab/IPython metaclass errors until upstream fixes land.

Optional — install the bridge entry point globally:

```bash
pip install -e /path/to/dappy-plugins/python-ipdb
```

### 2. Dappy plugin

**Development (this repo):**

```bash
export DAP_PLUGINS_DIR=/path/to/dappy-plugins
export PATH="/path/to/dappy-plugins/python-ipdb/bin:$PATH"
```

**ReqPack registry:**

```bash
rqp install dappy python-ipdb
export PATH="$HOME/.config/dap/plugins/python-ipdb/bin:$PATH"
```

## Usage

```bash
dap-cli plugin show python-ipdb
dap-cli debug repl --adapter python-ipdb script.py
```

The launcher stops at the **first executable line** of `script.py`. You can also call `ipdab.set_trace()` anywhere in code:

```python
import ipdab

ipdab.set_trace(on_continue="keep_running")
```

Or use the standard breakpoint hook:

```bash
PYTHONBREAKPOINT=ipdab.set_trace python3 script.py
```

(without Dappy — for attach-only workflows, connect an editor to `localhost:9000`).

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `PYTHON` | `python3` | Interpreter for launcher + bridge |
| `IPDAB_HOST` | `127.0.0.1` | ipdab listen address |
| `IPDAB_PORT` | `9000` | ipdab listen port |
| `DAP_PLUGINS_DIR` | — | Plugin discovery root |

## Limitations

- **No IDE-driven execution control** — continue/step/pause DAP requests are rejected by ipdab.
- **TCP, not stdio** — bridged by `dappy-ipdb-bridge`; port 9000 must be free (or override `port` in launch args).
- **Reconnection** — after continue with no remaining breakpoints, ipdab may shut down its server; clients may need to reconnect on the next `set_trace()`.
- **ipython version** — ipdab targets IPython `<9.1`; newer IPython may break terminal debugging.

## Files

| File | Purpose |
|------|---------|
| `plugin.yaml` | Dappy manifest (`launchTypes: python-ipdb`, `fileExtensions: py`) |
| `attachment.yaml` | REPL hints (throw sites, `ipdab.set_trace` patterns) |
| `dappy_ipdb/bridge.py` | stdio DAP ↔ ipdab TCP relay |
| `dappy_ipdb/launcher.py` | Start ipdab server + run script under ipdb |
| `bin/dappy-ipdb-bridge` | Shell wrapper (sets `PYTHONPATH`, invokes bridge) |
