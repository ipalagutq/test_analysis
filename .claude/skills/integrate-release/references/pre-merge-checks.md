# Pre-Merge Checks

Цель — убедиться, что merge не маскирует незавершённую работу и не переносит нестабильное состояние в `main`.

## Required Checks

| # | Проверка | PASS |
|---|---|---|
| 1 | Current branch | не `main` и не `master` |
| 2 | Route | определён как `spec` или `small_fix` |
| 3 | Worktree | `git status --porcelain` пустой до правки CHANGELOG/archive |
| 4 | Spec route | spec существует и все этапы реализации `✅` |
| 5 | Small-fix route | branch `fix/*`, spec отсутствует, изменения уже закоммичены |
| 6 | Tests | `uv run pytest` прошла успешно |
| 7 | Base branch | локальный `main` доступен для checkout/merge |

## Stop Cases

Остановиться, если:

- есть uncommitted changes до начала integrate-release;
- route не определяется однозначно;
- тесты не прошли;
- spec-route имеет незавершённый этап;
- apply-small-fix содержит spec или не выглядит как ветка `fix/*`;
- merge потребует конфликтов, которые нельзя безопасно решить локально.

## After Checks

После PASS можно менять только:

- `.ai/CHANGELOG.md`;
- `.ai/specs/archive/{branch}.md` для `spec` route;
- `MODULE_SIZE_REVIEWED` комментарии, если пользователь явно выбрал оставить крупный модуль.
