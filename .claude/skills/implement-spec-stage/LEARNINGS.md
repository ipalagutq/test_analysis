# Learnings — implement-spec-stage

История наблюдений и уроков. Обновляется автоматически по результатам запусков.

| Дата | Контекст | Урок |
|------|----------|------|
| 2026-05-13 | Supporting files research applied to `implement-spec-stage` | `SKILL.md` should route to stage selection, context gathering, sufficiency gate, implementation, and status-update references instead of embedding all details inline. |
| 2026-05-13 | Existing agent definitions found | Do not duplicate `code-mapper` and `data-flow-tracer` prompts inside `implement-spec-stage`; source of truth is `templates/agents/*.md`, installed to `.claude/agents/*.md`. |
| 2026-05-13 | Stage execution safety | Implementation should not begin until the sufficiency gate passes or the user receives a clear stop message. |
| 2026-10-16 | v0.2.0 Этап 1, greenfield | `ruff format .` в корне переформатирует установленные workflow-скрипты (`.claude/`, `scripts/validate_*.py`) — исключать их через `extend-exclude` в `pyproject.toml` до первого запуска. Строку `implement-spec-stage` в `## Workflow выполнения` ставить ✅ только после последнего этапа. |
| 2026-10-16 | v0.2.0 Этап 2, до шага ③ тестов нет | `uv run pytest` до `write-tests` даёт exit 5 (no tests collected) — это не провал; проверкой этапа служат ручной прогон из «Определения готовности» + `ruff check`/`ruff format --check`, и это явно сообщается пользователю. |
| 2026-10-16 | v0.2.0 Этап 3, имена исключений | Спец задаёт исключения без суффикса `Error` (`UnsupportedMediaType`, `ExtractionFailed`…), а python-style правило 13 требует `Error`. Приоритет — имена из spec (это контракт для маппинга в API), отклонение пометить комментарием; ruff N818 не включён, `noqa` не нужен. Битые файлы с валидной сигнатурой маппить в `UnsupportedMediaType`, иначе этап API получит 500. |

## Retrieval Rules

- Read at the start of each `implement-spec-stage` run.
- Use only lessons relevant to the selected stage.
- Replace obsolete lessons instead of accumulating contradictions.
- If a lesson exposes a failure mode, add or update `EVALS.md` before changing `SKILL.md`.
