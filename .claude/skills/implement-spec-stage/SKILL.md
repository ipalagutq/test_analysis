---
name: implement-spec-stage
description: >
  Шаг ② workflow: реализация текущего этапа ТЗ.
  Triggers: "реализуй ТЗ", "implement spec", "продолжи работу",
  "spec-implementer", "implement spec stage", "реализуй этап".
  Загружает spec, собирает информацию через субагентов-трассировщиков,
  реализует текущий этап, запускает тесты, коммит.
type: workflow
step: 2
---

# Implement Spec Stage Skill

**Шаг ② workflow** — реализация текущего этапа ТЗ с учётом архитектуры проекта.

## Workflow Contract

```yaml
entry:
  branch: NOT main | master
  artifacts:
    - .ai/specs/{branch-name}.md
  condition: есть этапы со статусом ⬜ или 🔄

exit:
  condition: все этапы ✅ или текущий этап ✅ и следующий этап оставлен для новой сессии
  tests: uv run pytest passed

run_scope:
  default: один текущий этап за сессию
  all_stages: только если пользователь явно попросил выполнить все этапы сразу

next_skill: write-tests

uses:
  - commit-helper
```

## Repo-root Scripts

| Скрипт | Когда запускать | Назначение |
|---|---|---|
| `scripts/validate_workflow_state.py` | В ENTRY-проверке | Общий workflow state gate (`--step implement-spec-stage`). Путь **от корня репозитория**, не от директории навыка. |

## Skill-local Supporting Files

| Файл | Когда читать | Назначение |
|---|---|---|
| `LEARNINGS.md` | В начале запуска | Только релевантные уроки прошлых реализаций |
| `references/stage-selection.md` | Перед выбором работы | Найти текущий этап и понять, когда STOP |
| `references/context-gathering.md` | Перед чтением кода | Какой проектный контекст собрать до реализации |
| `references/agent-orchestration.md` | Перед запуском агентов | Как вызвать существующих `code-mapper` и `data-flow-tracer` без дублирования их prompt-ов |
| `references/sufficiency-gate.md` | Перед правкой файлов | Gate достаточности контекста и условия STOP |
| `references/stage-implementation.md` | Во время реализации | Границы одного этапа, работа с existing patterns, rollback мышление |
| `references/spec-status-update.md` | После тестов | Как обновить статус этапа в spec |
| `EVALS.md` | Перед изменением поведения навыка | Regression cases для eval gate |

## Алгоритм

1. **Прочитать релевантный опыт** — открыть `LEARNINGS.md` и применить только уроки, относящиеся к текущему этапу.
2. **Проверить ENTRY** — запустить `python {repo_root}/scripts/validate_workflow_state.py --step implement-spec-stage` (путь от корня репозитория, не от директории навыка); если exit code ≠ 0 — вывести issues/warnings и STOP. Затем проверить spec существует в `.ai/specs/{branch-name}.md`.
3. **Выбрать этап** — по `references/stage-selection.md`; default: только первый `⬜` или `🔄` этап.
4. **Собрать контекст** — по `references/context-gathering.md`: spec, `.ai/ARCHITECTURE.md`, целевые файлы, похожие паттерны, релевантные правила.
5. **Запустить агентов** — по `references/agent-orchestration.md`; использовать существующие `.claude/agents/code-mapper.md` и `.claude/agents/data-flow-tracer.md`.
6. **Валидировать agent output** — по `references/agent-orchestration.md` (Agent Output Validation); при `FAIL` остановиться до исправления agent output; при `WARN` дочитать 1-2 gaps и повторить sufficiency gate. Пропустить только если агенты не вызывались (docs-only, single file) — с документированием причины.
7. **Применить sufficiency gate** — по `references/sufficiency-gate.md`; при 1-2 пробелах дочитать файлы самому, при 3+ пробелах или недоопределённом spec остановиться и сообщить пользователю.
8. **Реализовать текущий этап** — по `references/stage-implementation.md`; не переходить к следующему этапу без явного запроса пользователя.
9. **Запустить проверки** — выполнить `uv run pytest` и дополнительные релевантные проверки, если их требует spec.
10. **Обновить spec** — по `references/spec-status-update.md`: обновить заголовок этапа и строку навыка `implement-spec-stage` в таблице `## Workflow выполнения` (`⬜` → `✅`). Ставить `✅` только после проходящих проверок.
11. **Сделать commit** — вызвать `commit-helper`; затем вывести путь к spec, статус этапов и следующий шаг.

## Validation Checklist

- [ ] ENTRY: текущая ветка не `main/master`.
- [ ] Найден ровно один текущий этап или пользователь явно попросил выполнить все этапы.
- [ ] Контекст собран из spec, архитектуры, целевых файлов и похожих паттернов.
- [ ] `code-mapper` и `data-flow-tracer` получили полный input, требуемый их agent-файлами.
- [ ] Agent output validation пройден (OK/WARN) или агенты пропущены с документированной причиной; FAIL не обнаружен.
- [ ] Sufficiency gate пройден или остановка явно объяснена пользователю.
- [ ] Изменения ограничены текущим этапом.
- [ ] `uv run pytest` прошёл.
- [ ] Spec обновлён после проверок, не раньше.

## Continuous Improvement

По завершении каждого запуска выполни Improvement Triage:

1. Задача решена без неоднозначностей → вывести `no_change`.
2. Обнаружен повторно применимый урок → добавить краткую запись в `LEARNINGS.md`.
3. Инструкции навыка привели к ошибке → сначала создать eval-кейс в `EVALS.md`.
4. Предлагать patch `SKILL.md` только если та же проблема может повториться.
5. Предпочитать замену, удаление или вынос в supporting file простому добавлению правил.
6. Не обновлять `SKILL.md` до прохождения соответствующего eval.

## Rules

1. Один запуск реализует один текущий этап, если пользователь явно не попросил все этапы.
2. Агентные роли не дублируются в skill: source of truth — `templates/agents/*.md`, установленная копия — `.claude/agents/*.md`.
3. Не начинать реализацию, пока sufficiency gate не пройден или не зафиксирована осознанная остановка.
4. Не ставить `✅` в spec до проходящих проверок.
5. Не расширять scope этапа ради соседних улучшений.
6. Поведенческая правка навыка требует eval-case или явного ручного обоснования.
7. Source of truth для навыка — `skills/implement-spec-stage`; установка в проекты идёт через `.claude/skills/`.
