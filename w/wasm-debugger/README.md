# wasm-debugger

**WebAssembly** step debugging via Wasmtime CLI or Chrome DevTools.

```bash
cargo install wasmtime-cli   # or dnf install wasmtime
dap-cli debug repl --adapter wasm-debugger module.wasm
# wasmtime run -d module.wasm
```

Browser Wasm: **`chrome-devtools`** plugin.
