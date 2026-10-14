# python-pdb — Dappy plugin for stdlib pdb

Dappy manifest and stdio DAP bridge for Python's built-in [`pdb`](https://docs.python.org/3/library/pdb.html) / [`bdb`](https://docs.python.org/3/library/bdb.html) debugger.

Unlike the bundled `python` (debugpy) plugin, this adapter uses only the Python standard library and does not require `debugpy`.

## DAP approach

There is no official stdio DAP server for pdb. Projects like [ipdab](https://github.com/mvds314/ipdab) expose pdb over TCP when you call `set_trace()` in code (attach-only, read-mostly). For headless Dappy launch (`dap-cli debug repl --adapter python-pdb script.py`), this plugin ships a minimal **custom stdio DAP bridge** (`dappy_pdb_bridge`) that drives `bdb.Bdb` programmatically.

## Install

```bash
cd dappy-plugins/python-pdb
pip install -e .
```

The bridge has **no third-party runtime dependencies** (stdlib only). The editable install registers `python3 -m dappy_pdb_bridge` and the `dappy-pdb-adapter` console script.

### Dappy manifest discovery

Point Dappy at this plugin directory (or install via ReqPack):

```bash
export DAP_PLUGINS_DIR=/path/to/dappy-plugins
# or per-plugin override:
mkdir -p ~/.config/dap/plugins/python-pdb
cp plugin.yaml attachment.yaml ~/.config/dap/plugins/python-pdb/
pip install -e ~/.config/dap/plugins/python-pdb   # if copied without bridge sources, clone full dir
```

ReqPack:

```bash
rqp install dappy python-pdb
pip install -e ~/.config/dap/plugins/python-pdb
```

## Usage

```bash
dap-cli plugin show python-pdb
dap-cli debug repl --adapter python-pdb ./script.py
```

Optional: set `PYTHON` to choose the interpreter used for the debuggee (same as the debugpy plugin):

```bash
export PYTHON=python3.12
dap-cli debug repl --adapter python-pdb ./script.py
```

### Equivalent pdb CLI

The bridge launches the program under `bdb` with DAP control. Rough CLI equivalent:

```bash
python3 -m pdb script.py
```

For in-code breaks, stdlib `breakpoint()` / `pdb.set_trace()` still work when the program is run under this adapter.

## Limitations

- **Not debugpy** — no subprocess attach, no `justMyCode`, no hot reload, no run-in-terminal integration beyond Dappy defaults.
- **Single thread** — reports one synthetic `MainThread`; no multi-threaded debugging.
- **No conditional or function breakpoints** — line breakpoints only.
- **No setVariable** — inspect-only locals/globals via DAP.
- **Entry stop** — Dappy init sets a breakpoint at line 1; empty/comment-only first lines may stop on the first executable line instead.
- **ipdab-style attach** — not supported; use the `python` (debugpy) plugin for full IDE-style Python debugging.

## Files

| File | Purpose |
|------|---------|
| `plugin.yaml` | Dappy adapter manifest |
| `attachment.yaml` | Client hints (`breakpoint()`, `raise`, …) |
| `dappy_pdb_bridge/` | Stdio DAP ↔ bdb bridge (Python package) |
| `pyproject.toml` | Editable install / console script |

## Test locally

```bash
pip install -e dappy-plugins/python-pdb
export DAP_PLUGINS_DIR=/path/to/dappy-plugins
cd ~/Dev/Coditary/apps/dappy/dap-cli && cargo build
./target/debug/dap-cli plugin show python-pdb
./target/debug/dap-cli debug repl --adapter python-pdb /tmp/sample.py
```

Sample `/tmp/sample.py`:

```python
def greet(name):
    message = f"Hello, {name}!"
    return message

if __name__ == "__main__":
    print(greet("pdb"))
```
