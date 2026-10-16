# Git Update

Remote repo обновляется только после readiness check и env sync.

## Before Pull

Через SSH в `{APP_DIR}/repo`:

1. Получить текущий commit: `git rev-parse --short HEAD`.
2. Проверить рабочее дерево: `git status --porcelain`.
3. Убедиться, что нет локальных изменений.

Если remote worktree dirty — STOP. Не выполнять reset без явного решения пользователя.

## Pull

```bash
git pull origin main
```

После pull получить:

- новый commit hash;
- commit subject;
- текущую branch.

## Failure Handling

Если pull не удался:

- не запускать docker build/up;
- зафиксировать старый commit;
- показать stderr кратко;
- предложить ручную диагностику server-check.
