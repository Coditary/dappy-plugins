# sentry

[Sentry](https://sentry.io/) — error tracking, crash reporting, and stack-trace analysis.

```bash
export SENTRY_DSN=https://...@sentry.io/...
export SENTRY_ORG=my-org SENTRY_PROJECT=my-app SENTRY_AUTH_TOKEN=...
pip install sentry-cli  # or npm i -g @sentry/cli

dap-cli debug repl --adapter sentry
# Lists issues when sentry-cli + org/project are configured
```

For local breakpoint debugging use language-specific DAP adapters (`python`, `native-gdb`, `nodejs-inspector`).
