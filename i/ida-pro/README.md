# ida-pro

[IDA Pro](https://hex-rays.com/ida-pro/) — industry-standard interactive disassembler.

```bash
pip install -e dappy-plugins/re-launchers
export IDA=/opt/ida/ida64
dap-cli debug repl --adapter ida-pro malware.exe
```

Opens IDA GUI — no native DAP. Pair with `native-gdb` for scripted debugging.
