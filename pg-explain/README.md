# pg-explain

PostgreSQL **query debugger** — `EXPLAIN ANALYZE` and `pg_stat_statements`.

```sql
CREATE EXTENSION pg_stat_statements;
EXPLAIN (ANALYZE, BUFFERS) SELECT …;
```

```bash
pip install -e dappy-plugins/data-protocol-launchers
dap-cli debug repl --adapter pg-explain slow_query.sql
```
