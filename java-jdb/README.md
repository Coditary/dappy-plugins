# java-jdb

JDK **JDB** (Java Debugger) via JDWP.

```bash
dap-cli debug repl --adapter java-jdb MyApp.jar
export JDWP_PORT=5005
```

Spawns JVM with `-agentlib:jdwp` and attaches interactive `jdb`.

For IDE-grade DAP use Eclipse JDT / Red Hat `java-debug` adapter (future plugin).
