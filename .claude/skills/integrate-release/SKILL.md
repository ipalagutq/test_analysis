---
name: integrate-release
description: >
  Шаг ④ workflow: интеграция релиза — merge в main с обновлением CHANGELOG.
  Triggers: "merge в main", "мерж", "готово к релизу", "merge-helper",
  "integrate release", "интегрируй релиз".
  Проверяет качество, обновляет CHANGELOG, архивирует spec для spec-маршрута
  или пропускает архивирование для apply-small-fix, выполняет merge.
type: workflow
step: 4
---

# Integrate Release Skill

**Шаг ④ workflow** — интеграция релиза: финальный merge в main с обновлением документации.

## Workflow Contract

```yaml
entry:
  branch: NOT main | master
  routes:
    spec:
      artifacts:
        - .ai/specs/{branch-name}.md
      condition:
        - все этапы ✅
    small_fix:
      branch_pattern: fix/*
      artifacts: []
      condition:
        - ветка создана навыком apply-small-fix
        - .ai/specs/{branch-name}.md отсутствует и не требуется
        - фикс закоммичен
  condition:
    - нет uncommitted changes

exit:
  branch: main
  artifacts:
    - .ai/CHANGELOG.md
    - version artifacts updated to release version
    - .ai/specs/archive/{branch-name}.md  # только spec-маршрут

next_skill: deploy-release

uses:
  - commit-helper
```

## Repo-root Scripts

| Скрипт | Когда запускать | Назначение |
|---|---|---|
| `scripts/validate_workflow_state.py` | В Шаге 0 (workflow state gate) | Общий workflow state gate (`--step integrate-release`). Путь **от корня репозитория**, не от директории навыка. |

## Skill-local Supporting Files

| Файл | Когда читать |
|---|---|
| `references/route-detection.md` | При выборе маршрута `spec` или `small_fix` |
| `references/pre-merge-checks.md` | Перед запуском финальных проверок |
| `references/module-size-review.md` | При проверке лимита 500 строк |
| `references/changelog-entry.md` | Перед обновлением `.ai/CHANGELOG.md` |
| `references/version-sync.md` | Перед архивированием и merge |
| `references/spec-archiving.md` | Перед переносом spec в `archive/` |
| `references/merge-execution.md` | Перед git-операциями merge |
| `references/sufficiency-gate.md` | Перед финальным commit/merge |
| `assets/changelog-entry-template.md` | Как шаблон записи CHANGELOG |
| `assets/merge-report-template.md` | Как шаблон финального отчёта |
| `scripts/detect_merge_route.py` | Опционально: определить маршрут и spec path |
| `scripts/validate_pre_merge.py` | Опционально: проверить entry conditions |
| `scripts/find_large_modules.py` | Опционально: найти модули >500 строк |
| `scripts/validate_changelog_entry.py` | Опционально: проверить новую запись CHANGELOG |
| `scripts/validate_merge_completion.py` | Опционально: проверить post-merge состояние |

## Алгоритм

### Шаг 0: Workflow state gate

Запустить `python {repo_root}/scripts/validate_workflow_state.py --step integrate-release` (путь от корня репозитория, не от директории навыка); если exit code ≠ 0 — вывести issues/warnings и STOP.

### Шаг 1: Определить маршрут

Использовать `references/route-detection.md`. Если маршрут неочевиден, запустить `scripts/detect_merge_route.py`.

```bash
branch=$(git branch --show-current)
spec_slug=$(echo "$branch" | tr '/' '-')
spec_file=".ai/specs/${spec_slug}.md"
```

Если `spec_file` существует → маршрут `spec`: проверить, что все этапы ✅.

Если `spec_file` отсутствует и ветка соответствует `fix/*` → маршрут `small_fix`: убедиться, что фикс уже закоммичен, а uncommitted changes отсутствуют.

Иначе STOP: для обычной фичи/багфикса нужен spec, а no-spec merge разрешён только после `apply-small-fix`.

### Шаг 2: Pre-commit checks

Использовать `references/pre-merge-checks.md`. Если нужно, запустить `scripts/validate_pre_merge.py`.

```bash
uv run pytest
```

### Шаг 3: Проверка лимита размера модулей (500 строк)

Использовать `references/module-size-review.md`. Если нужно, запустить `scripts/find_large_modules.py`.

Найти все `.py` файлы, превышающие 500 строк:

```bash
find src/test_analysis/ -name "*.py" -exec awk 'END { if (NR > 500) print FILENAME ": " NR " lines" }' {} \;
```

Для каждого найденного файла:

1. **Проверить наличие пометки** `MODULE_SIZE_REVIEWED` в начале файла
2. **Предложить пользователю решение:**
   - **Вариант A: Рефакторинг** — разбить модуль
   - **Вариант B: Оставить** — если рефакторинг нецелесообразен
3. **Если принято решение оставить** — добавить:
   ```python
   # MODULE_SIZE_REVIEWED: {date}. Решение: оставить. Причина: {одна строка}
   ```

### Шаг 4: Обновление CHANGELOG

Использовать `references/changelog-entry.md` и `assets/changelog-entry-template.md`. После правки можно запустить `scripts/validate_changelog_entry.py`.

Добавить запись в `.ai/CHANGELOG.md`.

Для `spec` использовать тип `Added / Fixed / Changed` по содержанию spec:

```markdown
## [{version}] — {date}

### Added / Fixed / Changed — {Feature Name}

Краткое описание изменений.

**Компоненты:**
- [module/](path/): описание

**Tests:** {X} passed
```

Для `small_fix` использовать patch bump и тип `Fixed`:

```markdown
## [{version}] — {date}

### Fixed — {Small Fix Summary}

Краткое описание исправления без ссылки на spec.

**Tests:** {X} passed
```

### Шаг 5: Синхронизация версии

Использовать `references/version-sync.md`.

Проверить, что версия релиза из ветки/spec совпадает с записью CHANGELOG. Обновить все файлы, где проект явно трекает актуальную версию: `pyproject.toml`, `package.json`, `Cargo.toml`, `VERSION`, `version.txt`, исходники с `__version__` и проектные аналоги.

Если найден version artifact, который не обновлён до версии релиза, STOP до исправления.

### Шаг 6: Обновление DECISIONS.md

Только для маршрута `spec`:

Если spec содержит секцию «Расширение решений проекта» с новыми IS/IS NOT записями — извлечь их и добавить в `.ai/DECISIONS.md`:

1. Прочитать spec и найти секцию «Расширение решений проекта».
2. Для каждой записи с типом `IS` — добавить строку в секцию `## IS` файла `.ai/DECISIONS.md`.
3. Для каждой записи с типом `IS NOT` — добавить строку в секцию `## IS NOT` файла `.ai/DECISIONS.md`.
4. Если `.ai/DECISIONS.md` не существует — создать по шаблону `templates/DECISIONS.md.tpl`.

Если секция «Расширение решений проекта» отсутствует — пропустить этот шаг.

### Шаг 7: Архивирование spec

Использовать `references/spec-archiving.md`.

Только для маршрута `spec`:

```bash
mkdir -p .ai/specs/archive/
git mv ".ai/specs/${spec_slug}.md" ".ai/specs/archive/${spec_slug}.md"
```

Для маршрута `small_fix` пропустить этот шаг.

### Шаг 8: Source-of-truth sync validation

Запустить валидатор синхронизации перед merge:

```bash
python scripts/validate_source_sync.py
```

- **FAIL (exit 1)** — drift между product source layer и local runtime layer. STOP: синхронизировать runtime-копии вручную по подсказкам валидатора, затем повторить.
- **WARN (exit 0)** — phantom-файлы или optional-расхождения. Продолжить с предупреждением, сообщить пользователю.
- **OK** — всё синхронизировано.

### Шаг 9: Merge

Перед выполнением использовать `references/sufficiency-gate.md` и `references/merge-execution.md`.

```bash
git add .ai/CHANGELOG.md {version-artifacts} ".ai/specs/archive/${spec_slug}.md"
git commit -m "docs: update CHANGELOG for {feature-name}"
git checkout main
git merge --no-ff {branch} -m "feat: {feature-name} ({version})"
git branch -d {branch}
```

Для маршрута `small_fix` не добавлять путь архива spec и использовать merge message `fix: {summary} ({version})`.

### Шаг 10: Отчёт

Использовать `assets/merge-report-template.md`. После merge можно запустить `scripts/validate_merge_completion.py`.

```
✅ Merge завершён

Ветка:    {branch} → main
CHANGELOG: .ai/CHANGELOG.md обновлён
Version:   {version} синхронизирована
Spec:      .ai/specs/archive/{branch}.md
Tests:     {X} passed
```

Для маршрута `small_fix` вывести `Spec: не требуется (apply-small-fix)`.

## Continuous Improvement

По завершении каждого запуска выполни Improvement Triage:

1. Задача решена без неоднозначностей → вывести `no_change`.
2. Обнаружен повторно применимый урок → добавить краткую запись в `LEARNINGS.md`.
3. Инструкции навыка привели к ошибке → сначала создать eval-кейс в `EVALS.md`.
4. Предлагать патч `SKILL.md` только если та же проблема может повториться.
5. Предпочитать замену или удаление устаревшего guidance добавлению новых правил.
6. Не обновлять `SKILL.md` до прохождения соответствующего eval.
