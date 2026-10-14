# tsan

ThreadSanitizer — Data-race detection (TSan)

```bash
pip install -e dappy-plugins/sanitizer-launchers
# Binary must be built with sanitizer flags where applicable
dap-cli debug repl --target tsan -- ./myapp
```
