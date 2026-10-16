# Sufficiency Gate — integrate-release

Финальный gate перед commit CHANGELOG/archive и merge.

## PASS Criteria

| # | Критерий | Проверка |
|---|---|---|
| 1 | Route определён | `spec` или `small_fix`, причина записана |
| 2 | Entry conditions выполнены | branch не main/master, worktree был clean до действий integrate-release |
| 3 | Tests GREEN | `uv run pytest` прошла |
| 4 | Large modules reviewed | нет unreviewed `.py` файлов >500 строк |
| 5 | CHANGELOG готов | новая запись содержит версию, тип, summary, tests |
| 6 | Version artifacts синхронизированы | все найденные файлы версии обновлены до release version или явно `none found` |
| 7 | Spec archive корректен | для `spec`: source готов к `git mv`, target свободен |
| 8 | Merge message выбран | `feat:` / `fix:` соответствует route и типу изменения |
| 9 | Source-of-truth sync OK | `python scripts/validate_source_sync.py` — OK или WARN (не FAIL) |

## FAIL Signals

- CHANGELOG обновлён, но tests не запускались.
- Small-fix route пытается архивировать отсутствующий spec.
- Spec route пропускает archive.
- Branch удаляется до merge.
- Есть unrelated uncommitted changes.
- Найден `pyproject.toml`, `package.json`, `VERSION`, `__version__` или аналог, но версия в нём не обновлена.

## Output Before Merge

```markdown
### Merge Sufficiency
Route: `{spec|small_fix}`
Branch: `{branch}`
Version: `{version}`
Tests: `{command/result}`
Large modules: `{none|reviewed}`
CHANGELOG: ready
Version artifacts: `{updated files|none found}`
Spec archive: `{target|not required}`
Sync validation: `{OK|WARN|FAIL}`
Gate: PASS
```
