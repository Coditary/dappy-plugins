# observability-launchers

Shared launcher for cloud APM, error-tracking, and non-breaking live-debug plugins.

```bash
pip install -e dappy-plugins/observability-launchers
dappy-observability-launch sentry
```

Plugins set `DAPPY_PROGRAM` and service-specific env vars (see each plugin README).
