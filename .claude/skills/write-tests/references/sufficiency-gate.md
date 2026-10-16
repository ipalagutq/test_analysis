# Sufficiency Gate — write-tests

Использовать перед финальным запуском тестов и коммитом.

## PASS Criteria

| # | Критерий | Как проверить |
|---|---|---|
| 1 | Spec завершён | Все этапы реализации в spec имеют `✅` |
| 2 | Изменённые contracts имеют тесты | Coverage matrix содержит каждый новый/изменённый публичный contract |
| 3 | Выбран правильный слой | Для каждого теста понятно, почему это `unit/api/integration/architecture` |
| 4 | Есть negative/boundary coverage для рисков | Medium/high risk не закрыт только happy path |
| 5 | Нет live I/O в unit/api | Mock/stub boundary описан и виден в тесте |
| 6 | Использован локальный стиль тестов | Найден reference pattern или явно указано `NOT_FOUND` |
| 7 | Команда тестов GREEN | `uv run pytest` прошла успешно |

## FAIL Signals

- Новый тест проверяет private implementation detail без публичного эффекта.
- Тест проходит только из-за порядка запуска или локального состояния машины.
- Изменённый файл не имеет ни прямого, ни обоснованного косвенного теста.
- Integration-тест проверяет слишком много unrelated behavior.
- Assertion допускает любой результат ради прохождения.

## Output Before Commit

Перед вызовом `commit-helper` кратко зафиксировать:

```markdown
### Test Coverage Summary
| Changed area | Tests added/updated | Risk covered |
|---|---|---|
| `{area}` | `{test path}` | `{contract/error/invariant}` |

Sufficiency gate: PASS
Test command: `uv run pytest`
```
