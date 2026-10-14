# jlink-gdbserver

SEGGER [J-Link GDB Server](https://www.segger.com/products/debug-probes/j-link/tools/j-link-gdb-server/) — probe bridge to GDB.

```bash
export JLINK_DEVICE=STM32F407VG
export JLINK_INTERFACE=SWD
export JLINK_PORT=2331
dap-cli debug repl --target jlink-gdbserver -- firmware.elf
```
