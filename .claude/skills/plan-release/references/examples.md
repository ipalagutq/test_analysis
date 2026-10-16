# Spec Examples

Use examples when the correct shape is unclear. Do not copy content blindly; copy structure and specificity.

## Feature Example

```markdown
# Skill Supporting Files — Specification (v0.4.0)

> **Дата создания:** 2026-05-13
> **Ветка:** `feature/v0.4.0-skill-supporting-files`
> **Статус:** В работе
> **Standard:** validate-requirements-ieee29148 | Score: 88/100

## Видение

Workflow skills should keep `SKILL.md` short and route detailed context to directly linked supporting files.

## Архитектурные решения

| # | Вопрос | Решение |
|---|---|---|
| Q1 | Где хранить подробные чеклисты? | В `references/`, one-level deep from `SKILL.md`. |

## Этапы реализации

### Этап 1: Restructure skill context

**Файлы:**
- `skills/plan-release/SKILL.md`
- `skills/plan-release/references/scope-discovery.md`

**Что делаем:**
Move detailed ASQ guidance from `SKILL.md` to a focused reference file.

**Определение готовности:** `SKILL.md` lists the reference directly and no longer embeds the full ASQ question bank.
```

## Bugfix Example

```markdown
# Bugfix Spec Validation — Specification (v0.4.1)

> **Дата создания:** 2026-05-13
> **Ветка:** `bugfix/0.4.1-spec-validation`
> **Статус:** В работе
> **Standard:** validate-requirements-ieee29148 | Score: 90/100

## Видение

Specs with missing workflow tables should fail before branch creation.

## Архитектурные решения

| # | Вопрос | Решение |
|---|---|---|
| Q1 | Проверять вручную или скриптом? | Скриптом, чтобы исключить случайные пропуски. |

## Этапы реализации

### Этап 1: Add structural validator

**Файлы:**
- `skills/plan-release/scripts/validate_spec_structure.py`

**Что делаем:**
Validate required sections and workflow rows.

**Определение готовности:** Validator exits with non-zero status when required sections are missing.
```

## Document/Research Example

```markdown
# Literature Review Update — Specification (v0.4.0)

> **Дата создания:** 2026-05-13
> **Ветка:** `feature/v0.4.0-literature-review-update`
> **Статус:** В работе
> **Standard:** {confirmed-document-standard} | Score: manual-pass

## Видение

The literature review should reflect current supporting-file best practices and distinguish hard findings from heuristics.

## Архитектурные решения

| # | Вопрос | Решение |
|---|---|---|
| Q1 | Использовать IEEE? | Нет, это документная задача; стандарт подтверждается пользователем. |
```
