---
name: apply-small-fix
description: >
  Параллельная ветка workflow: небольшой фикс без ТЗ.
  Triggers: "небольшой фикс", "small fix", "quick fix", "мелкий фикс", "исправь быстро",
  "small-fix", "apply small fix", "примени фикс".
  Работает только если задача поставлена в Plan mode; создаёт fix/* ветку,
  вносит ограниченный patch, запускает проверку и коммитит.
type: workflow
step: F1
---

# Apply Small Fix Skill

**Параллельная ветка workflow** — небольшой фикс без создания ТЗ.

## Workflow Contract

```yaml
entry:
  collaboration_mode: Plan mode required
  branch: main | master
  condition:
    - задача сформулирована в Plan mode как короткий проверяемый фикс
    - scope ограничен 1-3 файлами
    - нет миграций, новых фич, архитектурных перестроек или новых публичных контрактов
    - .ai/specs/* не создаётся и не требуется

exit:
  branch: fix/{slug}
  condition:
    - фикс реализован
    - uv run pytest passed или явно объяснено, почему тесты не применимы
    - unrelated changes не затронуты
  artifacts:
    - изменённые файлы фикса
  commit: "fix: {summary}"

next_skill: integrate-release

uses:
  - commit-helper
```

## Supporting Files

| Файл | Когда читать |
|---|---|
| `references/plan-mode-gate.md` | Перед принятием задачи в `apply-small-fix` |
| `references/scope-classification.md` | При решении `apply-small-fix` или `plan-release` |
| `references/branching.md` | Перед созданием `fix/{slug}` |
| `references/minimal-patch.md` | Перед правкой файлов |
| `references/verification.md` | Перед выбором проверки |
| `references/escalation-to-spec.md` | Если scope начинает расти |
| `references/sufficiency-gate.md` | Перед commit и финальным отчётом |
| `assets/small-fix-plan-template.md` | Как шаблон постановки в Plan mode |
| `assets/small-fix-report-template.md` | Как шаблон финального отчёта |
| `scripts/classify_small_fix.py` | Опционально: классифицировать описание/файлы |
| `scripts/validate_small_fix_entry.py` | Опционально: проверить входные условия |
| `scripts/validate_small_fix_scope.py` | Опционально: проверить patch scope |
| `scripts/validate_small_fix_completion.py` | Опционально: проверить итог перед `integrate-release` |

## Plan Mode Gate

Использовать `references/plan-mode-gate.md`.

Если текущая задача не была поставлена в **Plan mode**, STOP: попросить пользователя переключиться в Plan mode и сформулировать небольшой фикс там. Не принимать постановку для `apply-small-fix` из обычного chat/default режима.

Plan mode постановка должна содержать:
- симптом или дефект
- ожидаемое поведение
- границы изменения
- проверку готовности

## Границы небольшого фикса

Использовать `references/scope-classification.md`. Если задача сомнительная, проверить её через `scripts/classify_small_fix.py`.

`apply-small-fix` подходит, если изменение локальное, обратимо и проверяемое за одну сессию.

Если появляется хотя бы один признак ниже — STOP и направить в `plan-release`:
- требуется проектирование или выбор архитектуры
- нужно менять публичный API, схему данных, миграции или протоколы интеграций
- затрагивается больше 3 файлов без очевидной механической причины
- нужно несколько этапов реализации
- есть продуктовая неоднозначность, которую нельзя закрыть Plan mode постановкой

## Алгоритм

1. **Проверить Plan mode gate** — без Plan mode не начинать работу.
2. **Подтвердить scope** — убедиться, что задача проходит границы небольшого фикса; при росте scope использовать `references/escalation-to-spec.md`.
3. **Создать ветку** — `fix/{slug}` от `main` или `master`; использовать `references/branching.md` и при необходимости `scripts/validate_small_fix_entry.py`.
4. **Внести patch** — менять только файлы, нужные для фикса; не создавать `.ai/specs/*`; использовать `references/minimal-patch.md`.
5. **Проверить** — запустить `uv run pytest` или минимальную релевантную проверку; использовать `references/verification.md`.
6. **Коммит** — вызвать `commit-helper` с сообщением `fix: {summary}`.
7. **Вывести** — пройти `references/sufficiency-gate.md`, при необходимости `scripts/validate_small_fix_scope.py` / `scripts/validate_small_fix_completion.py`, кратко описать изменение, проверку и указать `next_skill: integrate-release`.

## Continuous Improvement

По завершении каждого запуска выполни Improvement Triage:

1. Задача решена без неоднозначностей → вывести `no_change`.
2. Обнаружен повторно применимый урок → добавить краткую запись в `LEARNINGS.md`.
3. Инструкции навыка привели к ошибке → сначала создать eval-кейс в `EVALS.md`.
4. Предлагать патч `SKILL.md` только если та же проблема может повториться.
5. Предпочитать замену или удаление устаревшего guidance добавлению новых правил.
6. Не обновлять `SKILL.md` до прохождения соответствующего eval.
