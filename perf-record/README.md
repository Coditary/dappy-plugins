# perf-record

Linux `perf` profiling target for Dappy — hardware-level performance analysis, not classic breakpoint debugging.

## Usage

```bash
dap-cli target show perf-record
perf report -i perf.data    # after run
```

## What it measures

- CPU hotspots
- Cache misses
- Function call graphs (`-g`)

## Supported languages

C, C++, Rust, Go, Zig — anything with symbols in the binary.

## Notes

- This target **records** a profile; use `perf report`, `perf annotate`, or `hotspot` to analyze.
- Not a substitute for gdb/lldb when you need breakpoints.
