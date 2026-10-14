# lightrun

[Lightrun](https://lightrun.com/) — non-breaking live debugging for microservices and Kubernetes (snapshots, logs, metrics without redeploy).

```bash
pip install -e dappy-plugins/observability-launchers
export LIGHTRUN_SERVER=https://api.lightrun.com
export LIGHTRUN_API_KEY=...
dap-cli debug repl --adapter lightrun ./service.jar
```

Attach the Lightrun agent to your JVM/Node/Python process, then use the IDE plugin or Lightrun UI — no breakpoints that halt production traffic.
