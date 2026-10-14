# instruments-profiler

Apple **Instruments** — Time Profiler, Leaks, Core Animation (Swift/Obj-C runtime analysis).

```bash
# macOS + Xcode only
export INSTRUMENTS_TEMPLATE="Time Profiler"  # or Leaks, Core Animation
dap-cli debug repl --adapter instruments-profiler MyApp.app
```

General Xcode attach: **`xcode-instruments`** plugin. This plugin targets profiling templates specifically.
