# openocd

[OpenOCD](https://openocd.org/) — JTAG/SWD debugger for ARM, MIPS, RISC-V MCUs.

```bash
pip install -e dappy-plugins/embedded-launchers
export OPENOCD_CONFIG=interface/cmsis-dap.cfg
export OPENOCD_TARGET=target/stm32f4x.cfg
dap-cli debug repl --target openocd -- firmware.elf
# Uses builtin gdb-remote on port 3333
```
