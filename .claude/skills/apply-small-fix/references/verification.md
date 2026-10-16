# Verification — apply-small-fix

Проверка должна быть минимальной, но убедительной.

## Выбор проверки

| Изменение | Проверка |
|---|---|
| Pure logic | targeted unit test |
| CLI/output bug | targeted command или соответствующий unit test |
| Config/template typo | render/parse check или lint |
| Docs/rules typo | markdown/readability check |
| Existing regression | тест, воспроизводящий symptom |

## Full Test Command

Запускать `uv run pytest`, если:

- fix затрагивает shared helper;
- невозможно выбрать один targeted test;
- изменение влияет на workflow behavior.

## Если тесты не применимы

Допустимо объяснить, почему:

```markdown
Tests: not applicable
Reason: {например, исправлена только документационная формулировка}
Manual check: {что проверено}
```

Не использовать это для кода, который можно проверить существующим тестом.
