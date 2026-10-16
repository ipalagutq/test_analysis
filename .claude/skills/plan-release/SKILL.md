---
name: plan-release
description: >
  Шаг ① workflow: планирование релиза — создание ТЗ + ветка + коммит.
  Triggers: "создай ТЗ", "new feature", "новая фича", "bugfix", "исправь баг",
  "spec-creation", "plan release", "запланируй релиз".
  Автоматически выбирает стандарт валидации по типу задачи
  (IEEE 29148:2018 для кода, другой — для документов).
  После валидации создаёт ветку feature/* или bugfix/* и коммитит spec.
type: workflow
step: 1
---

# Plan Release Skill

**Шаг ① workflow** — планирование релиза: создание ТЗ, валидация по выбранному стандарту, ветка и коммит.

## Workflow Contract

```yaml
entry:
  branch: main | master
  trigger:
    - "создай ТЗ"
    - "new feature"
    - "новая фича"
    - "bugfix"
    - "исправь баг"

exit:
  artifacts:
    - .ai/specs/{branch-type}-v{version}-{slug}.md
  branch: feature/v{version}-{slug} | bugfix/v{version}-{slug}
  commit: "docs: add spec for {feature-name}"

next_skill: implement-spec-stage

uses:
  - validate-requirements-ieee29148
```

## Supporting Files

| Файл | Когда читать или запускать | Назначение |
|---|---|---|
| `LEARNINGS.md` | В начале запуска | Только релевантные уроки прошлых запусков |
| `references/scope-discovery.md` | Перед написанием ТЗ | ASQ-вопросы, scope, edge cases, критерии готовности |
| `references/standard-selection.md` | Когда тип задачи не очевиден | Выбор стандарта для кода, документов и смешанных задач |
| `references/requirements-quality.md` | Перед валидацией и при слабых требованиях | Критерии хороших требований и anti-patterns |
| `references/version-branching.md` | Перед созданием файла, ветки и коммита | Версия, slug, имя spec-файла, branch, commit message |
| `references/decisions-check.md` | При изучении контекста проекта | Проверка draft-требований против `.ai/DECISIONS.md` |
| `assets/spec-template.md` | При создании нового spec | Канонический шаблон ТЗ |
| `references/examples.md` | Когда нужен пример формы или спорный подтип задачи | Канонические примеры feature, bugfix и document/research spec |
| `scripts/validate_spec_structure.py` | После записи spec | Детерминированная проверка структуры spec |
| `EVALS.md` | Перед изменением поведения навыка | Regression cases для eval gate |

## Алгоритм

1. **Прочитать релевантный опыт** — открыть `LEARNINGS.md` и применить только уроки, относящиеся к текущей задаче.
2. **Понять задачу** — выделить цель, ожидаемый результат, известные ограничения и тип: feature, bugfix, документ или смешанная задача.
3. **Уточнить scope** — по `references/scope-discovery.md` выявить неявные решения; если есть вопрос, который меняет scope, архитектуру, UX/API или критерии готовности, остановиться и спросить пользователя. ASQ задаёт ровно один вопрос за раунд.
4. **Выбрать стандарт** — по `references/standard-selection.md`; для кодовых задач использовать `validate-requirements-ieee29148`, для документных задач спросить стандарт.
5. **Изучить контекст проекта** — прочитать `.ai/ARCHITECTURE.md`, `.ai/CHANGELOG.md` и релевантные правила workflow. Прочитать `.ai/DECISIONS.md` (если существует) и применить `references/decisions-check.md` для проверки draft-требований против product boundaries.
6. **Определить версию и имена** — по `references/version-branching.md`; каждое ТЗ = один будущий релиз, поэтому версия `MAJOR.MINOR.PATCH` обязательна в заголовке ТЗ, имени spec-файла и ветке.
7. **Написать spec** — использовать `assets/spec-template.md`; включить принятые решения, этапы реализации, acceptance criteria и явные ограничения.
8. **Проверить качество требований** — применить `references/requirements-quality.md`, затем выбранный стандарт; проходной score для code-spec: ≥85.
9. **Проверить структуру** — запустить `scripts/validate_spec_structure.py {path-to-spec}` и исправить найденные ошибки.
10. **Создать ветку, сохранить spec и сделать commit** — только после проходящей валидации.
11. **Вывести результат** — путь до spec, ветку, commit и следующий шаг: `implement-spec-stage`.

## Validation Checklist

- [ ] ENTRY: текущая ветка `main` или `master`.
- [ ] Все scope-вопросы, влияющие на ТЗ, заданы до записи spec, по одному вопросу за ASQ-раунд.
- [ ] Стандарт выбран явно и записан в metadata spec.
- [ ] Spec содержит `Workflow выполнения`, `Видение`, `Архитектурные решения`, `Этапы реализации`.
- [ ] Каждый этап имеет файлы, действия и проверяемое определение готовности.
- [ ] Code-spec прошёл `validate-requirements-ieee29148` с score ≥85.
- [ ] Spec проверен против `.ai/DECISIONS.md`; конфликты разрешены через AUQ, расширения зафиксированы в секции «Расширение решений проекта».
- [ ] `scripts/validate_spec_structure.py` не сообщает ошибок.
- [ ] Ветка, заголовок ТЗ, файл и commit message соответствуют `references/version-branching.md`; версия везде одна и та же.

## Continuous Improvement

По завершении каждого запуска выполни Improvement Triage:

1. Задача решена без неоднозначностей → вывести `no_change`.
2. Обнаружен повторно применимый урок → добавить краткую запись в `LEARNINGS.md`.
3. Инструкции навыка привели к ошибке → сначала создать eval-кейс в `EVALS.md`.
4. Предлагать patch `SKILL.md` только если та же проблема может повториться.
5. Предпочитать замену, удаление или вынос в supporting file простому добавлению правил.
6. Не обновлять `SKILL.md` до прохождения соответствующего eval.

## Rules

1. Не писать ТЗ по неявным решениям: использовать исчерпывающий ASQ для устранения всех неоднозначностей, включая те где есть safe default; проверять ТЗ против `.ai/DECISIONS.md` через `references/decisions-check.md`.
2. `SKILL.md` остаётся контрактом и маршрутизатором; подробный контекст держать в directly linked supporting files.
3. Не дублировать стандарт IEEE 29148 здесь: для code-spec использовать `validate-requirements-ieee29148`.
4. Документные и исследовательские задачи не валидировать как code-spec без подтверждения пользователя.
5. Любая поведенческая правка навыка требует eval-case или явного ручного обоснования.
6. ТЗ без будущей SemVer-версии в заголовке, имени файла и ветке не создавать.
7. Source of truth для навыка — `skills/plan-release`; установка в проекты идёт через `.claude/skills/`.
