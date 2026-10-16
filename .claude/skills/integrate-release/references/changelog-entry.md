# Changelog Entry

CHANGELOG — обязательный release artifact integrate-release.

## Version

Определять следующую версию по последней записи в `.ai/CHANGELOG.md`:

| Route | Bump |
|---|---|
| `spec` feature | minor |
| `spec` bugfix | patch |
| `small_fix` | patch |

Если spec уже содержит версию, использовать её, если она не конфликтует с CHANGELOG. Для spec route версия из ветки, заголовка spec и CHANGELOG должна совпадать: одно ТЗ = один релиз.

## Type

| Изменение | Heading |
|---|---|
| новая функциональность | `Added` |
| исправление дефекта | `Fixed` |
| изменение поведения/документации | `Changed` |

Для `small_fix` по умолчанию использовать `Fixed`.

## Required Fields

Каждая запись должна содержать:

- `## [{version}] — {date}`;
- `### {Added|Fixed|Changed} — {summary}`;
- краткое описание;
- `**Компоненты:**` для spec route, если изменялись конкретные модули;
- `**Tests:** {summary}`.

После подготовки записи выполнить version sync: эта же версия должна быть записана во все project version artifacts, которые обнаружены в репозитории.

## Style

- Писать с точки зрения результата для проекта.
- Не перечислять каждый commit.
- Не включать внутренние рассуждения или временные файлы.
- Для apply-small-fix явно не ссылаться на отсутствующий spec.
