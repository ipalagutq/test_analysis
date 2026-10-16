# Rollback

Rollback guidance используется, если deploy не прошёл build/up/health.

## Principles

1. Не импровизировать destructive команды.
2. Сохранить old commit и new commit.
3. Не скрывать частично успешное состояние.
4. Если причина не ясна — остановиться и предложить `server-check`.

## Minimal Rollback Plan

Если известен предыдущий commit и remote worktree clean:

```bash
cd {APP_DIR}/repo
git checkout {previous_commit}
docker compose build
docker compose up -d
```

Перед выполнением rollback получить явное согласие пользователя.

## Report On Failure

Зафиксировать:

- на каком шаге упало;
- старый commit;
- новый commit;
- container status;
- последние подозрительные строки логов;
- рекомендованное следующее действие.
