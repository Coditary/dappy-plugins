# firefox-devtools

Mozilla [Firefox Developer Tools](https://firefox-source-docs.mozilla.org/devtools-user/) / Debugger.

```bash
dap-cli debug repl --target firefox-devtools -- index.html
firefox --remote-debugging-port=9223 ./app.html
```

Uses Firefox remote debugging protocol (port 9223). Pair with `@vscode/js-debug` for DAP attach.
