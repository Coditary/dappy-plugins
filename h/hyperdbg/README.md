# hyperdbg

[HyperDbg](https://hyperdbg.org/) — open-source hypervisor debugger (VT-x/AMD-V) for stealth Windows debugging.

```bash
# Windows host with HyperDbg installed
set HYPERDBG=C:\HyperDbg\hyperdbg-cli.exe
dap-cli debug repl --adapter hyperdbg target.exe
```

Ring -1 debugging — guest OS cannot detect the debugger.
