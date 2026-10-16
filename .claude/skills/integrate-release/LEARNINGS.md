# Learnings — integrate-release

История наблюдений и уроков. Обновляется автоматически по результатам запусков.

| Дата | Контекст | Урок |
|------|----------|------|
| 2026-10-16 | v0.2.0: `pytest` упал только из-за ключа в локальном `.env` | Перед STOP по красным тестам прогнать их в чистом `git worktree` без `.env`; если зелёные — это дефект изоляции теста, чинить с согласия пользователя отдельным `test(...)`-коммитом до CHANGELOG. |
| 2026-10-16 | v0.2.0: `scripts/validate_source_sync.py` отсутствует в проекте-потребителе workflow | Отсутствие скрипта = WARN (нет product source layer), не FAIL; отметить в отчёте. |
| 2026-10-16 | v0.2.0: `validate_merge_completion.py` требует аргументы | Запуск: `validate_merge_completion.py --route {spec\|small_fix} {source_branch}`. |
| 2026-10-16 | v0.2.0: после merge `validate_workflow_state.py --step deploy-release` на `main` печатает `allowed=NO` при exit 0 | Ориентироваться на exit code; вывод — дефект валидатора (step-проверки выполняются только при наличии spec). |

## Retrieval Rules

- Read at the start of each `integrate-release` run.
- Use only lessons relevant to the current merge.
- Replace obsolete lessons instead of appending contradictions.
- If a lesson exposes a failure mode, add or update `EVALS.md` before changing `SKILL.md`.
