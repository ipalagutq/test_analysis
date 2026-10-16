# Sufficiency Gate — deploy-release

Финальная проверка перед сообщением, что deploy завершён.

## PASS Criteria

| # | Критерий | Проверка |
|---|---|---|
| 1 | Branch | локально `main` |
| 2 | Config | `deploy/deploy.env` валиден |
| 3 | Server | SSH, Docker, Compose и repo готовы |
| 4 | Env | `.env` скопирован или явно не требуется |
| 5 | Git | remote repo обновлён до `origin/main` |
| 6 | Compose | build и `up -d` успешны |
| 7 | Health | контейнеры running/up, логи без критичных ошибок |
| 8 | Report | указан сервер, проект, commit, версия, статус контейнера |

## FAIL Signals

- readiness check пропущен;
- `.env` отсутствует, но build/up всё равно запущен;
- remote repo dirty перед pull;
- контейнер exited/unhealthy;
- logs содержат traceback/critical без объяснения;
- финальный отчёт не содержит commit/version.

## Output Before Final

```markdown
Deploy gate: PASS
Server: `{VPS_USER}@{VPS_HOST}`
Project: `{APP_DIR}`
Commit: `{hash}`
Version: `{version}`
Health: `{summary}`
```
