# Branching — apply-small-fix

`apply-small-fix` всегда создаёт отдельную ветку `fix/{slug}` от `main` или `master`.

## Entry Checks

Перед созданием ветки:

- текущая ветка `main` или `master`;
- worktree clean;
- нет активного `.ai/specs/{future-branch}.md`;
- задача прошла Plan Mode Gate и Scope Classification.

## Slug

Правила:

- kebab-case;
- 3-6 слов максимум;
- без версии;
- описывает симптом или исправление.

Примеры:

- `fix/telegram-html-escaping`
- `fix/bootstrap-output-encoding`
- `fix/missing-agent-config`

## STOP

Если пользователь уже на feature/bugfix ветке, не продолжать apply-small-fix поверх неё. Спросить, нужно ли завершить текущий маршрут или начать заново от `main`.
