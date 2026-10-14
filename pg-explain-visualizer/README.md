# pg-explain-visualizer

Visual PostgreSQL **query plan** trees (joins, indexes, bottlenecks).

```bash
pip install -e dappy-plugins/domain-launchers
dap-cli debug repl --adapter pg-explain-visualizer slow.sql
# Outputs EXPLAIN (FORMAT JSON) — paste into explain.dalibo.com
```

CLI plans: **`pg-explain`** plugin. Function debug: **`pgadmin-pldbg`**.
