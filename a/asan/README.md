# asan

AddressSanitizer — Compiler ASan memory error detection

```bash
pip install -e dappy-plugins/sanitizer-launchers
# Binary must be built with sanitizer flags where applicable
dap-cli debug repl --target asan -- ./myapp
```
