# Learnings — plan-release

История наблюдений и уроков. Обновляется автоматически по результатам запусков.

| Дата | Контекст | Урок |
|------|----------|------|
| 2026-05-13 | Supporting files research applied to `plan-release` | `SKILL.md` should route to focused `references/`, `assets/`, and `scripts/` instead of embedding long question banks and templates. |
| 2026-05-13 | Document/research tasks in the spec workflow | Do not validate docs-only tasks as IEEE software requirements without user confirmation; ask for the document standard first. |
| 2026-05-13 | ASQ clarification style | ASQ must ask exactly one question per round; never batch multiple questions in a single user request. |
| 2026-10-16 | ASQ round skipped by a mid-turn user message (lab-scan-mvp) | Do not re-ask a skipped ASQ question; adopt the recommended default, mark it explicitly in `Архитектурные решения` and `Validation → Open questions`, and mention it in the final output. |

## Retrieval Rules

- Read at the start of each `plan-release` run.
- Use only lessons relevant to the current request.
- Replace obsolete lessons instead of accumulating contradictions.
- If a lesson exposes a failure mode, add or update `EVALS.md` before changing `SKILL.md`.
