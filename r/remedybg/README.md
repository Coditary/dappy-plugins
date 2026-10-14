# remedybg

Dappy launcher for [RemedyBG](https://remedybg.com) — fast standalone Windows C/C++ debugger.

## Install

```powershell
pip install -e dappy-plugins/remedybg
set REMEDYBG=C:\Program Files\RemedyBG\RemedyBG.exe
rqp install dappy remedybg
```

## Usage

```powershell
dap-cli debug repl --adapter remedybg .\game.exe
```

## Limitations

- **Windows only**, commercial tool (separate license).
- No public DAP API — launcher opens RemedyBG GUI; not headless REPL-driven.
- Symbol loading speed is RemedyBG's strength; orchestration is via Dappy manifest + env.
