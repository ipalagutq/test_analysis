# Spec Archiving

Архивирование выполняется только для `spec` route.

## Source And Target

| Поле | Значение |
|---|---|
| Source | `.ai/specs/{branch-slug}.md` |
| Target dir | `.ai/specs/archive/` |
| Target | `.ai/specs/archive/{branch-slug}.md` |

`branch-slug` получается заменой `/` на `-`.

## Rules

1. Не архивировать spec до успешных pre-merge checks и обновления CHANGELOG.
2. Использовать `git mv`, чтобы история файла сохранилась.
3. Если target уже существует, остановиться и разобраться вручную.
4. Для `small_fix` вывести `Spec: не требуется (apply-small-fix)` и не создавать пустой spec.
5. После архивации source path должен отсутствовать, target path должен существовать.

## Failure Handling

Если архивация не удалась:

- не продолжать merge;
- оставить branch как есть;
- сообщить source/target и причину;
- не удалять spec вручную.
