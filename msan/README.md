# msan

**MemorySanitizer** — detects reads of uninitialized memory.

```bash
clang -fsanitize=memory -g -O1 -o app app.c
pip install -e dappy-plugins/sanitizer-launchers
dap-cli debug repl --target msan -- ./app
```

Requires Clang MSan instrumented build (no mixed uninstrumented libs).
