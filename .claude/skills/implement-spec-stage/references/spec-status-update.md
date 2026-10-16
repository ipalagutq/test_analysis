# Spec Status Update

Use this reference after implementation and checks.

## Status Rules

| Status | Meaning | When to use |
|---|---|---|
| `⬜` | Not started | No verified work completed |
| `🔄` | In progress | Partial implementation exists but checks are not complete |
| `✅` | Complete | Implementation and required checks passed |

Do not mark a stage `✅` before tests/checks pass.

## Update Steps

1. Re-open the spec after edits.
2. Find the selected stage heading.
3. Update only that stage status unless user explicitly asked for all stages.
4. Add a short completion note only if the existing spec format has such notes.
5. Preserve unrelated spec text.

## Multi-Stage Runs

When user explicitly asked for all stages:

- update each stage immediately after its checks pass
- run sufficiency gate separately for the next stage
- stop if a later stage is under-specified

## Workflow Table Update

After updating the stage heading, update the workflow table in the spec:

1. Find the `## Workflow выполнения` section in the spec.
2. Locate the row where the `Навык` column matches the current skill name (e.g. `implement-spec-stage` or `write-tests`).
3. Replace the status cell: `⬜` → `✅`.

Each skill updates only its own row. Do not modify rows belonging to other skills.

## Completion Output

After updating the spec, report:

```text
spec: {path}
completed_stage: {stage}
remaining_stages: {count}
next_skill: write-tests | implement-spec-stage
```
