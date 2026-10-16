# Learnings — write-tests

История наблюдений и уроков. Обновляется автоматически по результатам запусков.

| Дата | Контекст | Урок |
|------|----------|------|
| 2026-10-16 | v0.2.0, первый набор тестов | `scripts/validate_test_completion.py` смотрит закоммиченный diff против `--base`: до коммита даёт FAIL «no tests changed». Запускать после коммита (или игнорировать pre-commit FAIL). |
| 2026-10-16 | v0.2.0, conftest | `get_settings`/`get_engine`/`get_session_factory` — `lru_cache`: autouse-фикстура должна менять env и делать `cache_clear()` до и после теста; `dispose()` движка в teardown — только если он в кэше, иначе невалидный env теста ломает teardown. |

## Retrieval Rules

- Read at the start of each `write-tests` run.
- Use only lessons relevant to the current test writing.
- Replace obsolete lessons instead of appending contradictions.
- If a lesson exposes a failure mode, add or update `EVALS.md` before changing `SKILL.md`.
