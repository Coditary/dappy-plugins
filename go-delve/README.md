# go-delve

Dappy plugin for [Delve](https://github.com/go-delve/delve) — the dedicated Go debugger.

Delve ships a native DAP server: `dlv dap` (stdio).

## Install

```bash
go install github.com/go-delve/delve/cmd/dlv@latest

rqp install dappy go-delve
```

## Usage

```bash
dap-cli debug repl --adapter go-delve ./cmd/myapp
dap-cli debug repl --adapter go-delve .   # package directory
```

## Launch options

| Field | Description |
|-------|-------------|
| `program` | Go package path or binary |
| `mode` | `exec`, `debug`, `test`, `replay` (Delve modes) |
| `args` | Program arguments |

## Notes

- Classic C debuggers (gdb/lldb) poorly understand goroutines; use Delve for Go.
- Requires `dlv` on `PATH`.
