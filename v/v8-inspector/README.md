# v8-inspector

Raw **V8/Node inspect protocol** (`node --inspect-brk`).

```bash
dap-cli debug repl --adapter v8-inspector app.js
# Starts Node on port 9229 — attach via chrome://inspect
```

For full headless DAP (continue/step/stack), use **`nodejs-inspector`** instead.
