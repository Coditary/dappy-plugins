# qemu-gdb-stub

QEMU built-in **gdb-remote stub** (`-s -S`) for kernel/VM debugging.

```bash
pip install -e dappy-plugins/hardware-launchers
dap-cli debug repl --adapter qemu-gdb-stub vmlinuz
# qemu -s -S -kernel vmlinuz — attach gdb on :1234
```

For full RSP workflow use Dappy target **`qemu-x86-kernel`** + `native-gdb`.
