# elastic-apm

[Elastic APM](https://www.elastic.co/observability/application-performance-monitoring) — traces, logs, and errors in the ELK stack.

```bash
export ELASTIC_APM_SERVER_URL=http://localhost:8200
export ELASTIC_APM_SECRET_TOKEN=...
export ELASTIC_APM_SERVICE_NAME=my-app
export KIBANA_URL=http://localhost:5601

dap-cli debug repl --adapter elastic-apm stacktrace.json
```

View stack traces under Kibana → Observability → APM → Errors.
