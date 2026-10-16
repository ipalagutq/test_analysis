---
name: server-check
description: >
  Подключение к VPS серверу и диагностика. Единая точка входа для любых SSH-операций.
  Triggers: "проверь сервер", "server check", "check server", "статус сервера",
  "server status", "зайди на сервер", "подключись к серверу", "ssh", "на сервере".
type: internal
---

# Server Check

Единая точка входа для работы с VPS. При любом упоминании сервера — использовать этот навык.

## Подключение

Конфигурация берётся из `deploy/deploy.env`. Если файл отсутствует — STOP.

```bash
SSH="ssh -i deploy/vps.key -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 {VPS_USER}@{VPS_HOST}"
APP_DIR={VPS_APP_DIR}/{PROJECT_NAME}
```

## Диагностика (по умолчанию)

Если задача не уточнена — запустить полную проверку:

```bash
$SSH bash -s <<'REMOTE'
echo "=== DOCKER ==="
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
echo "=== DISK ==="
df -h / | tail -1
echo "=== MEMORY ==="
free -h | grep Mem
echo "=== UPTIME ==="
uptime
echo "=== LOGS ==="
docker compose -f {APP_DIR}/repo/docker-compose.yml logs --tail 30 2>&1
REMOTE
```

Анализ:
- **Docker**: все контейнеры `Up`, нет `Restarting`
- **Disk**: `< 90%`
- **Memory**: available > 100M
- **Logs**: нет повторяющихся `ERROR`/`CRITICAL`/`Traceback`

Отчёт:

```
Сервер {VPS_HOST}: ✅ OK / ⚠️ проблемы

Контейнеры:  {статус}
Диск:        {X}% used
Память:      {X}G available
Логи:        чисто / ⚠️ {N} ошибок
```
