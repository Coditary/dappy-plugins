# kgdb

**KGDB** — debug the Linux kernel from a second machine via GDB.

```bash
# Guest kernel: CONFIG_KGDB, kgdboc=ttyS0,115200
# Or QEMU: qemu-system-x86_64 -s -S -kernel vmlinuz

pip install -e dappy-plugins/kernel-launchers
export VMLINUX=/path/to/vmlinux
dap-cli debug repl --adapter kgdb
# gdb vmlinux -ex 'target remote :1234'
```

Pairs with **`qemu-gdb-stub`** and **`native-gdb`**.
