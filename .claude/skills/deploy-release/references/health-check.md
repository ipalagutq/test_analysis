# Health Check

Health check подтверждает, что контейнер поднялся и не падает сразу после deploy.

## Required Checks

| Source | PASS |
|---|---|
| `docker compose ps` | сервисы в статусе `Up` или `running` |
| `docker compose logs --tail=30` | нет fatal error patterns |
| health endpoint, если документирован | HTTP 2xx/3xx или ожидаемый healthy response |

## Error Patterns

Считать подозрительными:

- `ERROR`
- `Traceback`
- `CRITICAL`
- `Exception`
- `panic`
- `fatal`
- `exited`
- `unhealthy`

Учитывать контекст: если лог явно содержит строку вроде `0 errors`, не делать вывод только по одному слову.

## Output

```markdown
Health: PASS | FAIL
Containers: {summary}
Logs: clean | suspicious
Suspicious patterns: {list|none}
```
