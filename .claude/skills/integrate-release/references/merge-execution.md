# Merge Execution

Git-операции выполняются только после sufficiency gate.

## Order

Для `spec` route:

1. Stage `.ai/CHANGELOG.md`, updated version artifacts и archived spec.
2. Commit: `docs: update CHANGELOG for {feature-name}`.
3. Checkout `main`.
4. Merge: `git merge --no-ff {branch} -m "feat: {feature-name} ({version})"` или `fix:` для bugfix.
5. Удалить merged branch только после успешного merge.

Для `small_fix` route:

1. Stage `.ai/CHANGELOG.md` и updated version artifacts, если они есть.
2. Commit: `docs: update CHANGELOG for {summary}`.
3. Checkout `main`.
4. Merge: `git merge --no-ff {branch} -m "fix: {summary} ({version})"`.
5. Удалить merged branch только после успешного merge.

## Conflict Handling

Если возникает conflict:

- остановиться;
- не выполнять автоматический rollback;
- показать конфликтующие файлы;
- предложить пользователю отдельную сессию на resolution.

## Safety Notes

- Не использовать `git reset --hard`.
- Не удалять ветку до успешного merge.
- Не делать squash merge: workflow сохраняет merge commit.
- Не менять unrelated files ради чистоты истории.
