# pgadmin-pldbg

PostgreSQL function/trigger debugging via **pldbgapi** + pgAdmin.

```sql
CREATE EXTENSION pldbgapi;
```

```bash
pip install -e dappy-plugins/database-launchers
dap-cli debug repl --adapter pgadmin-pldbg
```

Debug stored procedures from pgAdmin → Tools → Server → Debug.
