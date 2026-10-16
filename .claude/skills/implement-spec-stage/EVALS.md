# Evals — implement-spec-stage

Regression cases. Используются как gate перед патчами `SKILL.md`.

## SI-EVAL-001 — One Stage Per Session

**Given:** Spec contains multiple unchecked stages and user says "реализуй ТЗ".

**Expected:**
- The skill selects only the first `🔄` or `⬜` stage.
- The skill does not implement later stages.
- The skill stops after completing the selected stage unless the user explicitly asked for all stages.

**Failure mode:** The skill opportunistically implements adjacent stages.

## SI-EVAL-002 — Agent Definitions Are Not Duplicated

**Given:** `templates/agents/code-mapper.md` and `templates/agents/data-flow-tracer.md` exist.

**Expected:**
- `implement-spec-stage` references existing agent files.
- Supporting files describe orchestration and required input only.
- Agent role prompts and output formats are not copied into `implement-spec-stage` references.

**Failure mode:** The same agent prompt is duplicated in both `templates/agents/` and `skills/implement-spec-stage/references/`.

## SI-EVAL-003 — Sufficiency Gate Before Edits

**Given:** Agent outputs contain `NOT_FOUND`, `INSUFFICIENT_CONTEXT`, or `CHAIN_BREAK`.

**Expected:**
- The skill evaluates gaps through `references/sufficiency-gate.md`.
- With 1-2 non-blocking gaps, the skill reads missing files directly and re-checks.
- With 3+ gaps or a blocking gap, the skill stops and explains the blocker.

**Failure mode:** The skill edits implementation files with unresolved blocking context gaps.

## SI-EVAL-004 — Spec Status Updates After Checks

**Given:** Implementation edits are complete but tests have not passed.

**Expected:**
- The selected stage is not marked `✅`.
- The skill runs required checks before status completion.

**Failure mode:** The skill marks a stage complete before validation.

## SI-EVAL-005 — Non-Main Entry Guard

**Given:** Current branch is `main` or `master`.

**Expected:**
- The skill stops before implementation.
- The skill tells the user that `implement-spec-stage` requires a feature/bugfix branch with a matching spec.

**Failure mode:** The skill starts implementation on `main` or `master`.
