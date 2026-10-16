# Learnings — implement-spec-stage

История наблюдений и уроков. Обновляется автоматически по результатам запусков.

| Дата | Контекст | Урок |
|------|----------|------|
| 2026-05-13 | Supporting files research applied to `implement-spec-stage` | `SKILL.md` should route to stage selection, context gathering, sufficiency gate, implementation, and status-update references instead of embedding all details inline. |
| 2026-05-13 | Existing agent definitions found | Do not duplicate `code-mapper` and `data-flow-tracer` prompts inside `implement-spec-stage`; source of truth is `templates/agents/*.md`, installed to `.claude/agents/*.md`. |
| 2026-05-13 | Stage execution safety | Implementation should not begin until the sufficiency gate passes or the user receives a clear stop message. |
| 2026-10-16 | v0.2.0 Этап 1, greenfield | `ruff format .` в корне переформатирует установленные workflow-скрипты (`.claude/`, `scripts/validate_*.py`) — исключать их через `extend-exclude` в `pyproject.toml` до первого запуска. Строку `implement-spec-stage` в `## Workflow выполнения` ставить ✅ только после последнего этапа. |

## Retrieval Rules

- Read at the start of each `implement-spec-stage` run.
- Use only lessons relevant to the selected stage.
- Replace obsolete lessons instead of accumulating contradictions.
- If a lesson exposes a failure mode, add or update `EVALS.md` before changing `SKILL.md`.
