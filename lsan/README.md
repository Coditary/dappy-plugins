# lsan

LeakSanitizer — Fast standalone memory leak detector

```bash
# Build with -fsanitize=lsan
pip install -e dappy-plugins/sanitizer-launchers
dap-cli debug repl --target lsan -- ./myapp
```
