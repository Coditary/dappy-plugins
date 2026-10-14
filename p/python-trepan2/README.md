# python-trepan2 (Dappy plugin)

Dappy manifest and DAP bridge for [trepan2](https://github.com/Trepan-Debuggers/python2-trepan), a gdb-like debugger for **Python 2**.

## Feasibility note

Python 2 is end-of-life. This plugin remains useful for legacy codebases that still run under Python 2.7 with `trepan2` installed. You need a working `python2` / `python2.7` interpreter and the `trepan2` package.

## Architecture choice

Same **hybrid remote TCP bridge** as `python-trepan3k`:

- Dappy ↔ `dappy-trepan2-dap` (DAP stdio)
- bridge ↔ trepan2 (TCP comcodes protocol)
- trepan2 ↔ Python 2 debuggee

Not an RSP/`target.yaml` setup — trepan is not gdb-remote compatible.

## Install

```bash
# trepan2 debuggee (Python 2)
python2 -m pip install trepan2

# DAP bridge (Python 3)
cd dappy-plugins/python-trepan2
pip install -e .
```

Set the Python 2 interpreter for launch spawning:

```bash
export PYTHON2=python2.7
```

## Dappy usage

```bash
export DAP_PLUGINS_DIR=/path/to/dappy-plugins

dap-cli plugin show python-trepan2
dap-cli debug repl --adapter python-trepan2 ./legacy_script.py
```

## Limitations

- **Python 2 only** for the debuggee and trepan2 server process.
- Same DAP coverage gaps as the trepan3k plugin (see that README).
- Many modern systems no longer ship Python 2; treat this plugin as legacy/optional.
- Install `dappy-trepan2-dap` into an environment on `PATH` (typically via `python2 -m pip install -e .`).

## Files

Same layout as `python-trepan3k`, with `dappy_trepan2` package and `launchTypes: python-trepan2`.
