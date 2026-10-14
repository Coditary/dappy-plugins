# python-pdbpp — Dappy plugin for pdb++

[pdb++](https://github.com/pdbpp/pdbpp) (PyPI package `pdbpp`) is a drop-in replacement for CPython's `pdb`. This plugin lets you start a debug session with:

```bash
dap-cli debug repl --adapter python-pdbpp script.py
```

## How pdb++ replaces pdb

After `pip install pdbpp`, the package installs a **`pdb.py` module into site-packages** that shadows the stdlib `pdb` on import. Any code that does `import pdb`, `breakpoint()` (via `PYTHONBREAKPOINT=pdb.set_trace`), or `python -m pdb` automatically gets the enhanced **(Pdb++)** prompt — unless you explicitly import the stdlib copy via `pdb.pdb`.

| Mechanism | Effect with pdbpp installed |
|-----------|----------------------------|
| `import pdb; pdb.set_trace()` | pdb++ prompt |
| `breakpoint()` (Python 3.7+) | pdb++ when `PYTHONBREAKPOINT` unset (defaults to `pdb.set_trace`) |
| `python -m pdb script.py` | pdb++ CLI |
| `pytest --pdb` | pdb++ on failures |

This plugin's DAP bridge imports pdbpp first so the hijacked module is used for programmatic debugging.

## Architecture

There is **no official DAP adapter for pdb++**. This plugin ships a minimal bridge (`dappy_pdbpp_dap`) inspired by observation-only adapters like [ipdab](https://github.com/mvds314/ipdab):

```
dap-cli ──DAP──► dappy_pdbpp_dap ──bdb/pdb++──► your script.py
                      │
                      └── optional runInTerminal ──► (Pdb++) TTY
```

### Modes

| `console` launch arg | Behavior |
|---------------------|----------|
| `internalConsole` (default) | DAP-controlled: REPL drives continue/step/stack/variables |
| `integratedTerminal` | Spawns `python -m pdb <program>` in a terminal via DAP `runInTerminal` — full pdb++ UX (sticky, highlighting, completion) |

### pdb++ features

| Feature | DAP mode | Terminal mode |
|---------|----------|---------------|
| Syntax highlighting | via pdb++ when `interactive: true` + TTY | yes |
| TAB completion | via pdb++ when `interactive: true` + TTY | yes |
| Sticky mode (`sticky: true`) | enabled on stop (best in terminal) | configure via `~/.pdbrc.py` |
| Post-mortem (`postMortem: true`) | stops on uncaught exceptions | yes |
| `pdb.xpm()` / `pm` | use in source; attachment patterns help REPL | yes |

## Install

### ReqPack (end users)

```bash
pip install pdbpp dappy-pdbpp-dap
rqp install dappy python-pdbpp
dap-cli debug repl --adapter python-pdbpp script.py
```

### Local development

```bash
cd dappy-plugins/python-pdbpp
pip install -e .

export DAP_PLUGINS_DIR=/path/to/dappy-plugins
dap-cli plugin show python-pdbpp
dap-cli debug repl --adapter python-pdbpp /path/to/script.py
```

## Launch options

| Field | Default | Description |
|-------|---------|-------------|
| `stopOnEntry` | `true` | Break before first line of the target script |
| `postMortem` | `true` | Break on uncaught exceptions |
| `sticky` | `false` | Enable pdb++ sticky mode on each stop |
| `interactive` | `false` | Drop into pdb++ prompt on stop (requires TTY) |
| `console` | `internalConsole` | Set to `integratedTerminal` for terminal launch |

## Limitations

- **No IDE-style control during terminal mode** — pdb/ipdb-style debuggers own the TTY at the prompt; DAP can only observe or launch, not inject commands mid-prompt.
- **Not a debugpy replacement** — no multi-threaded debugging, no remote attach, no variable mutation.
- **Requires pdbpp** — install separately (`pip install pdbpp`); the adapter exits with a clear error if missing.
- **Single-threaded** — only the main thread is reported to DAP.

## Files

| File | Role |
|------|------|
| `plugin.yaml` | Dappy manifest |
| `attachment.yaml` | REPL hints for `breakpoint()`, `set_trace`, post-mortem |
| `dappy_pdbpp_dap/` | Minimal DAP ↔ pdb++ bridge |
| `requirements.txt` | Runtime deps |
