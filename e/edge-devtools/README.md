# edge-devtools

Microsoft Edge DevTools (Chromium CDP, same protocol as Chrome).

```bash
dap-cli debug repl --target edge-devtools -- index.html
export CHROME_DEBUG_PORT=9224
dap-cli debug repl --adapter edge-devtools index.html
```

Reuses `dappy-chrome-cdp` launcher (CDP-compatible). Override binary: `EDGE=microsoft-edge-stable`.
