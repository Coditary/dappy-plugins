# datadog-apm

[Datadog APM](https://www.datadoghq.com/product/apm/) and Live Debugger — enterprise tracing and live code snapshots.

```bash
export DD_API_KEY=...
export DD_SERVICE=my-service DD_ENV=dev DD_VERSION=1.0.0
export DD_TRACE_DEBUG=1
dap-cli debug repl --adapter datadog-apm
```

Enable **Live Debugger** in Datadog Security settings. Traces flow to the agent on `DD_AGENT_HOST:8126` (default).
