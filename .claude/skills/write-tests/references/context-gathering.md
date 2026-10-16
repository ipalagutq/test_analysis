# Context Gathering — write-tests

Цель фазы — превратить завершённую реализацию в короткую карту того, что должно быть доказано тестами.

## Источники

Читать в таком порядке:

1. `.ai/specs/{branch-name}.md` — видение, архитектурные решения, все завершённые этапы.
2. `git diff --name-only main...HEAD` или ближайший доступный base — фактически изменённые файлы.
3. Сами изменённые файлы — публичные функции, классы, CLI/API entrypoints, конфиг и артефакты.
4. Существующие тесты рядом по смыслу — стиль, фикстуры, helper APIs.
5. `.ai/ARCHITECTURE.md` — границы слоёв и допустимые зависимости.

## Что извлечь

| Поле | Вопрос |
|---|---|
| Contract | Что теперь принимает и возвращает публичная поверхность? |
| Behavior | Какое новое или изменённое поведение видит пользователь/вызывающий код? |
| Failure modes | Какие ошибки, пустые входы, конфликты и degraded paths поддержаны? |
| State/artifacts | Какие файлы, статусы, БД-записи, сообщения или side effects меняются? |
| Configuration | Какие settings, env vars, feature flags или defaults влияют на поведение? |
| Boundaries | Где нужны mock/stub вместо live I/O? |

## Выход фазы

Сформировать рабочую таблицу:

| Changed file | Public surface | Risk | Existing test pattern | Proposed test layer |
|---|---|---|---|---|
| `{path}` | `{function/class/command}` | `{low/medium/high}` | `{test path or NOT_FOUND}` | `{unit/api/integration/architecture}` |

## Stop Conditions

Остановиться и уточнить у пользователя, если:

- spec не найден или не все этапы отмечены `✅`;
- diff содержит изменения, которых нет в spec и они меняют scope;
- невозможно определить expected behavior без продуктового решения;
- проверка требует live API/production credential, а mock boundary неочевидна.
