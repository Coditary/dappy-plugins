# nodejs-inspector

Node.js debugging via the V8 inspector and Microsoft's [js-debug](https://github.com/microsoft/vscode-js-debug) DAP adapter.

## Install

```bash
npm install -g @vscode/js-debug
pip install -e dappy-plugins/nodejs-inspector
rqp install dappy nodejs-inspector
```

## Usage

```bash
dap-cli debug repl --adapter nodejs-inspector app.js
dap-cli debug repl --adapter nodejs-inspector src/index.ts
```

## Environment

| Variable | Purpose |
|----------|---------|
| `JS_DEBUG_ADAPTER` | Path to js-debug `cli.js` |
| `NODE` | Node binary (default: `node` on PATH) |

## Fallback

Without js-debug, launches `node --inspect-brk` for Chrome DevTools attach on port 9229.
