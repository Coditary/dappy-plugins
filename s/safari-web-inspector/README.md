# safari-web-inspector

Apple [Safari Web Inspector](https://webkit.org/web-inspector/) — macOS and iOS WebKit debugging.

**macOS only.** Enable Safari → Settings → Advanced → *Show features for web developers*.

```bash
dap-cli debug repl --adapter safari-web-inspector index.html
```

For headless DAP on macOS, use `@vscode/js-debug` with `type: safari`.
