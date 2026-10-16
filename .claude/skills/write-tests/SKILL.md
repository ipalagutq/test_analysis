---
name: write-tests
description: >
  Шаг ③ workflow: написание тестов для реализованного кода.
  Triggers: "напиши тесты", "write tests", "создай тесты", "покрой тестами",
  "test-writer", "напиши проверку".
  Трассирует изменённые модули, пишет unit/api/integration/architecture tests.
type: workflow
step: 3
---

# Write Tests

**Шаг ③ workflow** — написать тесты для реализованного кода.

## Workflow Contract

```yaml
entry:
  branch: NOT main | master
  artifacts:
    - .ai/specs/{branch-name}.md
  condition: все этапы в spec имеют статус ✅

exit:
  condition: новые тесты написаны и uv run pytest GREEN
  artifacts:
    - tests/**/*.py

next_skill: integrate-release

uses:
  - commit-helper
```

## Repo-root Scripts

| Скрипт | Когда запускать | Назначение |
|---|---|---|
| `scripts/validate_workflow_state.py` | В ENTRY-проверке (Фаза 1) | Общий workflow state gate (`--step write-tests`). Путь **от корня репозитория**, не от директории навыка. |

## Skill-local Supporting Files

| Файл | Когда читать |
|---|---|
| `references/context-gathering.md` | Перед трассировкой изменённых модулей |
| `references/test-layer-selection.md` | При выборе `unit` / `api` / `integration` / `architecture` |
| `references/coverage-matrix.md` | Перед написанием тестов и при проверке полноты |
| `references/test-patterns.md` | Перед созданием новых test-файлов или фикстур |
| `references/sufficiency-gate.md` | Перед запуском финальной проверки и коммитом |
| `scripts/collect_test_targets.py` | Опционально: собрать таблицу test targets из spec + diff |
| `scripts/validate_test_completion.py` | Опционально: проверить, что новые тесты закрывают изменения |

## Выбор слоя тестов

| Если меняется | Писать |
|---|---|
| Pure/domain logic, validators, value objects | `tests/unit/` |
| HTTP clients с mocked responses | `tests/api/` |
| Pipeline flow, end-to-end через агентов | `tests/integration/` |
| Запрещённые импорты между модулями | `tests/architecture/` |

## Правила

- Не делать live API-вызовов в unit-тестах — использовать mock/stub
- Не хардкодить модели — конфиг через `Settings`
- Не придумывать новые паттерны, если уже есть референс в `tests/`

## Алгоритм

### Фаза 1: ENTRY-проверка

1. Запустить `python {repo_root}/scripts/validate_workflow_state.py --step write-tests` (путь от корня репозитория, не от директории навыка); если exit code ≠ 0 — вывести issues/warnings и STOP.
2. Проверить ветку: `git branch --show-current`
3. Найти spec: `.ai/specs/{branch-name}.md`
4. Убедиться, что все этапы `✅`

### Фаза 2: Трассировка

Использовать `references/context-gathering.md`.

Прочитать изменённые файлы (из spec или `git diff --name-only`):
- публичный контракт: input/output types
- потоки данных
- файловые артефакты
- конфиг/feature flags

Если список файлов размытый, запустить `scripts/collect_test_targets.py`.

### Фаза 3: Минимальный правильный набор тестов

Использовать `references/test-layer-selection.md`, `references/test-patterns.md` и `references/coverage-matrix.md`.

1. Новые публичные контракты
2. Граничные случаи (пустой ввод, конфликт, ошибки)
3. Регрессии статусов и артефактов
4. Runtime invariants

### Фаза 4: Запуск и коммит

Проверить полноту по `references/sufficiency-gate.md`. Если нужно, запустить `scripts/validate_test_completion.py`.

```bash
uv run pytest -v
```

Все тесты GREEN → обновить строку навыка `write-tests` в таблице `## Workflow выполнения` spec-файла (`⬜` → `✅`); вызвать `commit-helper`.

## Continuous Improvement

По завершении каждого запуска выполни Improvement Triage:

1. Задача решена без неоднозначностей → вывести `no_change`.
2. Обнаружен повторно применимый урок → добавить краткую запись в `LEARNINGS.md`.
3. Инструкции навыка привели к ошибке → сначала создать eval-кейс в `EVALS.md`.
4. Предлагать патч `SKILL.md` только если та же проблема может повториться.
5. Предпочитать замену или удаление устаревшего guidance добавлению новых правил.
6. Не обновлять `SKILL.md` до прохождения соответствующего eval.
