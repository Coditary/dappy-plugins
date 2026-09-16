# dappy-plugins

Optional adapter and RSP target manifests for [Dappy](https://github.com/Coditary/Dappy).

Each top-level directory is a standalone plugin package installable via [rqp-plugin-dappy](https://github.com/Coditary/rqp-plugin-dappy):

```bash
rqp install dappy python
rqp install dappy gdbserver
```

Catalog metadata lives in [dappy-registry](https://github.com/Coditary/dappy-registry).

## Packages

| Id | Kind | Description |
|----|------|-------------|
| `python` | DAP adapter | debugpy |
| `rust` | DAP adapter | lldb-dap |
| `fake` | DAP adapter | Test adapter |
| `gdb-remote` | DAP adapter | Builtin gdb-remote bridge |
| `gdbserver` | RSP target | Local gdbserver |
| `qemu-x86-kernel` | RSP target | QEMU x86_64 kernel stub |
| `rsp-attach` | RSP target | Attach to running RSP endpoint |
