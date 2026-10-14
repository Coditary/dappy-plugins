# chrome-devtools

[Chrome DevTools](https://developer.chrome.com/docs/devtools) via Chrome DevTools Protocol (CDP).

## Modes

| Mode | Command |
|------|---------|
| Launch browser | `dap-cli debug repl --target chrome-devtools -- index.html` |
| Attach (DAP) | `dap-cli debug repl --adapter chrome-devtools index.html` |

## Setup

```bash
pip install -e dappy-plugins/chrome-devtools
npm install -g @vscode/js-debug   # full DAP attach
export JS_DEBUG_ADAPTER=/path/to/js-debug/out/src/cli.js
```

## Notes

- CDP is not native DAP; js-debug bridges CDP ↔ DAP for VS Code compatibility.
- Set `CHROME_DEBUG_PORT` (default 9222).
- Override browser binary via `CHROME=chromium` in spawn env.
