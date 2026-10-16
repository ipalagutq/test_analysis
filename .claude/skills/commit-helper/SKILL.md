---
name: commit-helper
description: >
  INTERNAL: Управление коммитами с Conventional Commits.
  Вызывается из: implement-spec-stage, integrate-release.
  НЕ вызывается пользователем напрямую.
type: internal
called_by:
  - implement-spec-stage
  - integrate-release
---

# Commit Helper Skill

**Служебный навык** — управление коммитами с соблюдением качества.

## Usage Context

```yaml
type: internal  # НЕ вызывается пользователем напрямую

called_by:
  - implement-spec-stage  # коммит после каждого этапа
  - integrate-release      # merge commit

responsibility:
  - Conventional Commits format
  - Проверка тестов перед коммитом
```

**IMPORTANT:** CHANGELOG.md обновляется ТОЛЬКО при merge в main через `integrate-release`, не при обычных коммитах.

## Pre-Commit Checklist

### Шаг 1: Запустить тесты

```bash
uv run pytest
```

### Шаг 2: Коммит

Conventional Commits формат:

```
feat(scope): add feature description
fix(scope): handle error case
docs(arch): update ARCHITECTURE.md with new module
test(scope): add tests for new functionality
refactor(shared): extract helper function
```

Типы:
- `feat` — новый функционал
- `fix` — исправление бага
- `docs` — документация
- `test` — тесты
- `refactor` — рефакторинг без изменения поведения
- `chore` — maintenance, зависимости

Scope — название модуля или слоя.

## Формат команды

```bash
git add {files}
git commit -m "{type}({scope}): {description}"
```
