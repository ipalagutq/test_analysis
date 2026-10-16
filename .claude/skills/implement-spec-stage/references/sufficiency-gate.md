# Sufficiency Gate

Use this gate before implementation. It decides whether the context is strong enough to edit safely.

## Criteria

| # | Criterion | Evidence |
|---|---|---|
| 1 | Target files are known | Spec stage lists files or direct code search identifies them |
| 2 | Existing code is understood | `code-mapper` has no unresolved `NOT_FOUND` for required existing files |
| 3 | Contracts are known | DTO/API/CLI/file formats are listed or intentionally absent |
| 4 | Reference pattern is known | `code-mapper` finds a pattern or the run records `NOT FOUND` with reason |
| 5 | Data flow is understood | `data-flow-tracer` reports no blocking `CHAIN_BREAK` |
| 6 | Agent output validated | Agent output passed `validate_agent_output.py` or was manually checked against schema; agents skipped with documented reason |
| 7 | Tests/checks are known | Test command or manual verification is identified |
| 8 | Stage boundaries are clear | No dependency on an incomplete earlier stage |

## Decision

- **0 gaps:** implement.
- **1-2 gaps:** read missing files directly or inspect nearby patterns, then re-check the gate.
- **3+ gaps:** stop; report that the stage is under-specified or context is insufficient.
- **Blocking gap:** stop even if it is the only gap.

## Blocking Gaps

- target files cannot be identified
- stage goal conflicts with architecture
- required contract is missing
- data flow has a `CHAIN_BREAK` at the entry or persistence/API boundary
- agent output validation returned `FAIL` (see `references/agent-orchestration.md`)
- tests cannot be identified and no manual verification is acceptable

## Stop Message Shape

```markdown
Не начинаю реализацию: недостаточно контекста для этапа `{stage}`.

Блокер: {blocking gap}
Что нужно уточнить: {single question or concrete missing artifact}
```

### Agent Validation FAIL

```markdown
Остановка: agent output validation FAIL для этапа `{stage}`.

Агент: {agent_name}
Код: {finding_code}
Сообщение: {finding_message}
Действие: исправить agent output и перезапустить или пропустить агент с обоснованием
```
