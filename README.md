# dappy-plugins

Optional adapter and RSP target manifests for [Dappy](https://github.com/Coditary/Dappy).

Plugin packages live under a letter directory (first character of the plugin id), e.g.
`p/python-pudb`, `r/rust`, `g/gdbserver`. Each package is installable via
[rqp-plugin-dappy](https://github.com/Coditary/rqp-plugin-dappy):

```bash
rqp install dappy python
rqp install dappy gdbserver
```

Catalog plugins that launch external debuggers (IDA, ocamldebug, JDB, …) require the
shared bridge and the matching launcher package:

```bash
rqp install dappy dappy-launcher-dap
rqp install dappy language-platform-launchers   # language catalog plugins
rqp install dappy re-launchers                  # IDA, Ghidra, x64dbg, …
```

Catalog metadata lives in [dappy-registry](https://github.com/Coditary/dappy-registry).

## Tool dependencies (ReqPack / `sys:`)

Many plugin directories include a `reqpack.lua` that declares the underlying debugger
or tool via [ReqPack](https://github.com/Coditary/ReqPack/wiki). Dependencies use the
built-in **`sys:`** bridge (distro-agnostic — ReqPack picks apt/dnf/pacman/homebrew on
the host) or language managers (`uv:`, `npm:`, …), not a specific Linux distro PM:

```bash
cd dappy-plugins/r/rust
rqp install .
# ensures sys:lldb-dap via the host package manager bridge
```

After `rqp install dappy <id>`, the same manifest is installed under
`$XDG_CONFIG_HOME/dap/plugins/<id>/reqpack.lua`.

## Packages

| Id | Kind | Description |
|----|------|-------------|
| `python` | DAP adapter | debugpy |
| `python-madbg` | DAP adapter | madbg remote/preemptive Python debugger |
| `python-madbg-attach` | DAP adapter | madbg attach-by-PID companion |
| `madbg-connect` | DAP adapter | madbg TCP connect-only companion |
| `rust` | DAP adapter | lldb-dap |
| `fake` | DAP adapter | Test adapter |
| `gdb-remote` | DAP adapter | Builtin gdb-remote bridge |
| `gdbserver` | RSP target | Local gdbserver |
| `qemu-x86-kernel` | RSP target | QEMU x86_64 kernel stub |
| `rsp-attach` | RSP target | Attach to running RSP endpoint |
| `native-lldb` | DAP adapter | LLVM lldb-dap (C/C++/Rust/Zig) |
| `native-gdb` | DAP adapter | GNU GDB MI3 bridge |
| `go-delve` | DAP adapter | Go Delve (`dlv dap`) |
| `rr-replay` | DAP adapter | Mozilla rr time-travel + lldb-dap |
| `rr-record` | RSP target | rr record trace |
| `valgrind-memcheck` | RSP target | Valgrind memcheck + vgdb |
| `perf-record` | RSP target | Linux perf profiling |
| `windbg-cdb` | DAP adapter | WinDbg/CDB (Windows) |
| `remedybg` | DAP adapter | RemedyBG launcher (Windows) |
| `nodejs-inspector` | DAP adapter | Node.js V8 / js-debug |
| `chrome-devtools` | DAP + target | Chrome CDP DevTools |
| `firefox-devtools` | DAP + target | Firefox remote debugging |
| `edge-devtools` | DAP + target | Edge Chromium CDP |
| `safari-web-inspector` | DAP adapter | Safari WebKit (macOS) |
| `firebug` | DAP adapter | Firebug legacy (redirect) |
| `opera-dragonfly` | DAP adapter | Opera Dragonfly legacy |
| `java-jdb` | DAP adapter | JDK JDB / JDWP |
| `dotnet-coreclr` | DAP adapter | .NET netcoredbg |
| `dnspy` | DAP adapter | dnSpyEx (Windows) |
| `ilspy` | DAP adapter | ILSpy decompiler |
| `php-xdebug` | DAP adapter | PHP Xdebug |
| `java-tod` | DAP adapter | Omniscient Debugger (TOD) |
| `fusionreactor` | RSP target | FusionReactor attach |
| `dotnet-dottrace` | RSP target | JetBrains dotTrace profiler |
| `dotnet-dotmemory` | RSP target | JetBrains dotMemory profiler |

| `ida-pro` | DAP adapter | IDA Pro disassembler |
| `ghidra` | DAP adapter | Ghidra SRE |
| `x64dbg` | DAP adapter | x64dbg/x32dbg (Windows) |
| `ollydbg` | DAP adapter | OllyDbg legacy (Windows) |
| `radare2` | DAP adapter | Radare2 CLI |
| `cutter` | DAP adapter | Cutter GUI (r2) |
| `binary-ninja` | DAP adapter | Binary Ninja |
| `immunity-debugger` | DAP adapter | Immunity Debugger |
| `capstone-disasm` | DAP adapter | Capstone/XED disasm helper |
| `asan` | RSP target | AddressSanitizer |
| `tsan` | RSP target | ThreadSanitizer |
| `ubsan` | RSP target | UBSan |
| `efence` | RSP target | Electric Fence |
| `duma` | RSP target | Duma heap guard |
| `dr-memory` | RSP target | Dr. Memory |
| `purify` | RSP target | IBM Purify (commercial) |
| `aqtime-pro` | RSP target | AQTime Pro (commercial) |

| `openocd` | RSP target | OpenOCD JTAG/SWD → gdb-remote |
| `jlink-gdbserver` | RSP target | SEGGER J-Link GDB server |
| `segger-ozone` | DAP adapter | SEGGER Ozone GUI |
| `trace32-lauterbach` | DAP adapter | Lauterbach TRACE32 |
| `pls-ude` | DAP adapter | PLS UDE automotive |
| `stm32cube-gdb` | DAP adapter | STM32 arm-none-eabi-gdb |
| `avr-gdb` | DAP adapter | AVR-GDB / Arduino |
| `android-studio` | DAP adapter | Android Studio Profiler |
| `xcode-instruments` | DAP adapter | Xcode Instruments (macOS) |
| `charles-fiddler` | DAP adapter | Charles / Fiddler HTTP proxy |
| `proxyman` | DAP adapter | Proxyman HTTP proxy |
| `flipper` | DAP adapter | Meta Flipper mobile debug |
| `macsbug` | DAP adapter | MacsBug |
| `softice` | DAP adapter | SoftICE |
| `codeview` | DAP adapter | CodeView |
| `dos-debug` | DAP adapter | DEBUG.COM |
| `turbo-debugger` | DAP adapter | Turbo Debugger |
| `mdb` | DAP adapter | MDB |
| `kadb-ddb` | DAP adapter | KADB / DDB |
| `affinic` | DAP adapter | Affinic Debugger |
| `ddd` | DAP adapter | DDD |
| `ups` | DAP adapter | Ups |
| `xminidump` | DAP adapter | Xminidump / Dumpert |
| `lightrun` | DAP adapter | Lightrun |
| `sentry` | DAP adapter | Sentry |
| `datadog-apm` | DAP adapter | Datadog APM / Live Debugger |
| `rollbar` | DAP adapter | Rollbar |
| `bugsnag` | DAP adapter | Bugsnag |
| `airbrake` | DAP adapter | Airbrake |
| `raygun` | DAP adapter | Raygun |
| `new-relic-apm` | DAP adapter | New Relic APM |
| `dynatrace` | DAP adapter | Dynatrace |
| `instana` | DAP adapter | Instana |
| `elastic-apm` | DAP adapter | Elastic APM |
| `renderdoc` | DAP adapter | RenderDoc |
| `pix` | DAP adapter | PIX |
| `nvidia-nsight` | DAP adapter | NVIDIA Nsight |
| `amd-rgp` | DAP adapter | AMD RGP |
| `intel-gpa` | DAP adapter | Intel GPA |
| `xcode-gpu-capture` | DAP adapter | Xcode GPU Frame Capture |
| `unity-profiler` | DAP adapter | Unity Profiler |
| `unreal-insight` | DAP adapter | Unreal Insight |
| `perl-debugger` | DAP adapter | Perl Debugger |
| `ruby-debug` | DAP adapter | Ruby debug |
| `ruby-pry` | DAP adapter | Pry |
| `ruby-rdbg` | DAP adapter | rdbg |
| `v8-inspector` | DAP adapter | V8 Inspector |
| `lua-mobdebug` | DAP adapter | LuaDB / MobDebug |
| `rstudio-debugger` | DAP adapter | RStudio Debugger |
| `gdb-mi` | DAP adapter | GDB/MI |
| `plsql-developer` | DAP adapter | PL/SQL Developer |
| `pgadmin-pldbg` | DAP adapter | pgAdmin / pldbgapi |
| `ssms-tsql` | DAP adapter | SSMS T-SQL Debugger |
| `toad-debugger` | DAP adapter | TOAD Debugger |
| `ibm-zos-debugger` | DAP adapter | IBM z/OS Debugger |
| `xpediter-bmc` | DAP adapter | Xpediter (BMC) |
| `wireshark` | DAP adapter | Wireshark |
| `tcpdump` | DAP adapter | tcpdump |
| `wireshark-stream` | DAP adapter | Wireshark Follow Stream |
| `postman-bruno` | DAP adapter | Postman / Bruno |
| `mitmproxy` | DAP adapter | mitmproxy |
| `wireshark-lua` | DAP adapter | Wireshark Lua Dissector |
| `typescript-tsc` | DAP adapter | TypeScript Compiler |
| `bash-trace` | DAP adapter | bash trace |
| `shdb` | DAP adapter | shdb |
| `emacs-edebug` | DAP adapter | Emacs Edebug |
| `clojure-debugger` | DAP adapter | Clojure debugger |
| `swi-prolog-tracer` | DAP adapter | SWI-Prolog Tracer |
| `ghci-debugger` | DAP adapter | GHCi Debugger |
| `elixir-erlang-debugger` | DAP adapter | Elixir/Erlang debugger |
| `saleae-logic` | DAP adapter | Saleae Logic |
| `sigrok-pulseview` | DAP adapter | Sigrok / PulseView |
| `vivado-modelsim` | DAP adapter | Vivado / ModelSim |
| `openvera-uvm` | DAP adapter | OpenVera / UVM |
| `qemu-gdb-stub` | DAP adapter | QEMU GDB stub |
| `bochs-debugger` | DAP adapter | Bochs debugger |
| `mame-debugger` | DAP adapter | MAME debugger |
| `higan-bsnes` | DAP adapter | higan / bsnes |
| `cuckoo-sandbox` | DAP adapter | Cuckoo Sandbox |
| `any-run` | DAP adapter | Any.Run |
| `api-monitor` | DAP adapter | API Monitor |
| `frida` | DAP adapter | Frida |
| `intel-pin` | DAP adapter | Intel PIN |
| `kd-kdbg` | DAP adapter | KD / KDBG |
| `kdb-linux` | DAP adapter | Linux KDB |
| `kgdb` | DAP adapter | KGDB |
| `libvmi` | DAP adapter | LibVMI |
| `hyperdbg` | DAP adapter | HyperDbg |
| `jvmti-debugger` | DAP adapter | JVMTI Debugger |
| `v8-cdp` | DAP adapter | V8 CDP / Node inspect |
| `hhvm-hphpd` | DAP adapter | HHVM hphpd |
| `python-dis` | DAP adapter | CPython dis |
| `pg-explain` | DAP adapter | pg_stat_statements / EXPLAIN |
| `grpcurl-bloomrpc` | DAP adapter | grpcurl / BloomRPC |
| `kafka-console` | DAP adapter | Kafka Console |
| `redis-cli-debug` | DAP adapter | Redis CLI debug |
| `racket-debugger` | DAP adapter | Racket Debugger |
| `agda-coq-prover` | DAP adapter | Agda / Coq |
| `idris-debugger` | DAP adapter | Idris debugger |
| `jupyter-debugger` | DAP adapter | Jupyter debugger |
| `juce-plugin-host` | DAP adapter | JUCE Plugin Host |
| `puredata-maxmsp` | DAP adapter | Pure Data / Max/MSP |
| `remix-debugger` | DAP adapter | Remix Debugger |
| `forge-debugger` | DAP adapter | Forge Debugger |
| `beam-observer` | DAP adapter | BEAM observer / dbg |
| `erratum-debugger` | DAP adapter | Erratum / Scheme debugger |
| `instruments-profiler` | DAP adapter | Instruments Profiler |
| `labview-highlight` | DAP adapter | LabVIEW Highlight Execution |
| `pg-explain-visualizer` | DAP adapter | pgAdmin EXPLAIN Visualizer |
| `arm-ddt` | DAP adapter | ARM DDT |
| `totalview` | DAP adapter | TotalView |
| `stat-mpi` | DAP adapter | STAT |
| `undo-live-recorder` | DAP adapter | Undo LiveRecorder |
| `pernosco` | DAP adapter | Pernosco |
| `matlab-debugger` | DAP adapter | MATLAB Debugger |
| `octave-debugger` | DAP adapter | GNU Octave Debugger |
| `mathematica-debugger` | DAP adapter | Mathematica Debugger |
| `freertos-zephyr-gdb` | DAP adapter | FreeRTOS / Zephyr GDB |
| `l4re-genode-debugger` | DAP adapter | L4Re / Genode Debugger |
| `msan` | RSP target | MemorySanitizer |
| `dfsan` | RSP target | DataFlowSanitizer |
| `lsan` | RSP target | LeakSanitizer |
| `ada-gnatdbg` | DAP adapter | Ada gnatdbg |
| `fortran-gdb` | DAP adapter | Fortran GDB |
| `delphi-debugger` | DAP adapter | Delphi Debugger |
| `nim-gdb` | DAP adapter | nim-gdb |
| `powershell-debugger` | DAP adapter | PowerShell Debugger |
| `autohotkey-debugger` | DAP adapter | AutoHotkey Debugger |
| `gawk-debugger` | DAP adapter | gawk debugger |
| `tcl-debugger` | DAP adapter | Tcl debugger |
| `ocamldebug` | DAP adapter | ocamldebug |
| `dart-devtools` | DAP adapter | Dart DevTools |
| `julia-debugger` | DAP adapter | Julia Debugger |
| `groovy-debugger` | DAP adapter | Groovy Debugger |
| `abap-debugger` | DAP adapter | ABAP Debugger |
| `vba-vb6-debugger` | DAP adapter | VBA / VB6 Debugger |
| `fpdebug` | DAP adapter | fpdebug |
| `vala-gdb` | DAP adapter | Vala GDB |
| `actionscript-fdb` | DAP adapter | Adobe fdb |
| `common-lisp-slime` | DAP adapter | SLIME / Swank |
| `guile-debugger` | DAP adapter | Guile Debugger |
| `pharo-debugger` | DAP adapter | Pharo Debugger |
| `wasm-debugger` | DAP adapter | Wasm Debugger |
| `qsharp-debugger` | DAP adapter | Q# Debugger |
| `processing-debugger` | DAP adapter | Processing Debugger |
| `dax-studio` | DAP adapter | DAX Studio |
| `godot-gdscript` | DAP adapter | Godot GDScript Debugger |
| `haxe-debugger` | DAP adapter | Haxe Debugger |
| `eiffelstudio-debugger` | DAP adapter | EiffelStudio Debugger |
| `factor-debugger` | DAP adapter | Factor Debugger |
| `crystal-debugger` | DAP adapter | Crystal Debugger |
| `ghostscript-debugger` | DAP adapter | Ghostscript Debugger |
