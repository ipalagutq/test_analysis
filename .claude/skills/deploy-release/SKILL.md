---
name: deploy-release
description: >
  Шаг ⑤ workflow: деплой релиза на VPS после merge в main.
  Triggers: "деплой", "deploy", "разверни", "обнови сервер", "перезапусти бота",
  "deploy-release", "задеплой релиз".
  Git pull, docker compose build/up, scp .env, проверка здоровья.
  Если сервер не настроен — вызывает vps-setup.
type: workflow
step: 5
---

# Deploy Release Skill

**Шаг ⑤ workflow** — деплой релиза на VPS после merge в main.

## Workflow Contract

```yaml
entry:
  branch: main
  condition:
    - merge завершён
    - deploy/deploy.env существует

exit:
  condition: контейнер запущен, логи без ошибок
  artifacts:
    - Отчёт о деплое в stdout

next_skill: null  # КОНЕЦ WORKFLOW

uses:
  - vps-setup  # если сервер не настроен
```

## Repo-root Scripts

| Скрипт | Когда запускать | Назначение |
|---|---|---|
| `scripts/validate_workflow_state.py` | В Шаге 0 (workflow state gate) | Общий workflow state gate (`--step deploy-release`). Путь **от корня репозитория**, не от директории навыка. |

## Skill-local Supporting Files

| Файл | Когда читать |
|---|---|
| `references/config-loading.md` | При чтении и проверке `deploy/deploy.env` |
| `references/server-readiness.md` | Перед любыми изменениями на VPS |
| `references/env-sync.md` | Перед копированием `.env` |
| `references/git-update.md` | Перед `git pull origin main` на сервере |
| `references/docker-compose-deploy.md` | Перед build/up/stop операциями |
| `references/health-check.md` | При проверке `docker compose ps` и логов |
| `references/rollback.md` | Если deploy не завершился успешно |
| `references/sufficiency-gate.md` | Перед финальным отчётом |
| `assets/deploy-report-template.md` | Как шаблон успешного отчёта |
| `assets/rollback-plan-template.md` | Как шаблон отчёта при сбое |
| `scripts/validate_deploy_config.py` | Опционально: проверить `deploy/deploy.env` |
| `scripts/check_deploy_readiness.py` | Опционально: проверить локальные условия deploy |
| `scripts/render_remote_commands.py` | Опционально: вывести SSH/SCP план без выполнения |
| `scripts/parse_compose_status.py` | Опционально: проверить вывод compose/logs |
| `scripts/validate_deploy_report.py` | Опционально: проверить полноту финального отчёта |

## Алгоритм

### Шаг 0: Workflow state gate

Запустить `python {repo_root}/scripts/validate_workflow_state.py --step deploy-release` (путь от корня репозитория, не от директории навыка); если exit code ≠ 0 — вывести issues/warnings и STOP.

### Шаг 1: Загрузка конфигурации

Использовать `references/config-loading.md`. Если нужно, запустить `scripts/validate_deploy_config.py`.

Прочитать `deploy/deploy.env` — получить `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, `VPS_APP_DIR`, `PROJECT_NAME`, `REPO_URL`.

Если файл не существует — STOP, попросить создать из `deploy/deploy.env.example`.

```bash
SSH_CMD="ssh -i {VPS_SSH_KEY} -o StrictHostKeyChecking=accept-new {VPS_USER}@{VPS_HOST}"
APP_DIR="{VPS_APP_DIR}/{PROJECT_NAME}"
```

### Шаг 2: Проверка готовности сервера

Использовать `references/server-readiness.md`. Если нужно, запустить `scripts/check_deploy_readiness.py` до SSH и `scripts/render_remote_commands.py` для плана команд.

```bash
$SSH_CMD "docker --version && test -d {APP_DIR}/repo/.git && echo 'READY'"
```

Если не `READY` — предложить запустить `vps-setup`. STOP.

### Шаг 3: Копирование .env на сервер

Использовать `references/env-sync.md`.

```bash
scp -i {VPS_SSH_KEY} .env {VPS_USER}@{VPS_HOST}:{APP_DIR}/repo/.env
```

### Шаг 4: Git pull

Использовать `references/git-update.md`.

```bash
$SSH_CMD "cd {APP_DIR}/repo && git pull origin main"
```

### Шаг 5: Build и перезапуск

Использовать `references/docker-compose-deploy.md`.

```bash
$SSH_CMD "cd {APP_DIR}/repo && docker compose build && docker compose up -d"
```

Использовать `docker compose stop` вместо `docker compose down` для остановки (без удаления контейнера).

### Шаг 6: Проверка здоровья

Использовать `references/health-check.md`. Если есть сохранённый вывод `ps` и логов, можно проверить его через `scripts/parse_compose_status.py`.

```bash
$SSH_CMD "cd {APP_DIR}/repo && docker compose ps && docker compose logs --tail=30"
```

Проверить:
- Контейнер в статусе `Up`
- Логи не содержат `ERROR`, `Traceback`, `CRITICAL`

### Шаг 7: Отчёт

Перед отчётом пройти `references/sufficiency-gate.md`. Для успеха использовать `assets/deploy-report-template.md`, для сбоя — `references/rollback.md` и `assets/rollback-plan-template.md`.

```
✅ Deploy завершён

Сервер:     {VPS_USER}@{VPS_HOST}
Проект:     {APP_DIR}
Контейнер:  {container_status}
Git:        {commit_hash} ({commit_message})
Версия:     {version из CHANGELOG}
```
## Continuous Improvement

По завершении каждого запуска выполни Improvement Triage:

1. Задача решена без неоднозначностей → вывести `no_change`.
2. Обнаружен повторно применимый урок → добавить краткую запись в `LEARNINGS.md`.
3. Инструкции навыка привели к ошибке → сначала создать eval-кейс в `EVALS.md`.
4. Предлагать патч `SKILL.md` только если та же проблема может повториться.
5. Предпочитать замену или удаление устаревшего guidance добавлению новых правил.
6. Не обновлять `SKILL.md` до прохождения соответствующего eval.
