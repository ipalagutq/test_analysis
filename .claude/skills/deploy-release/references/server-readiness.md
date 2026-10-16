# Server Readiness

Готовность сервера проверяется до копирования `.env`, pull и docker операций.

## Remote Checks

Выполнить через SSH:

| Проверка | PASS |
|---|---|
| SSH доступ | команда возвращает exit code 0 |
| Docker | `docker --version` успешен |
| Docker Compose | `docker compose version` успешен |
| Repo | `{APP_DIR}/repo/.git` существует |
| Branch | repo может checkout/pull `main` |
| Permissions | пользователь может писать в `{APP_DIR}/repo` |

## Not Ready

Если любая обязательная проверка не проходит:

1. Остановиться.
2. Не копировать `.env`.
3. Не запускать build/up.
4. Предложить `vps-setup`.

## Output

```markdown
Server readiness: PASS | FAIL
SSH: ok | fail
Docker: ok | fail
Repo: ok | fail
Action: continue | run vps-setup
```
