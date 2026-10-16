# Self-Improvement Gate

Use this reference before changing any existing skill, including `skill-creator` itself.

## Decision Flow

1. **Observation:** What happened? Is it a reusable lesson, a failure, or a requested behavior change?
2. **Target:** Which file should change?
   - `LEARNINGS.md` for reusable lessons.
   - `EVALS.md` for failures and regression expectations.
   - `references/` for detailed guidance.
   - `SKILL.md` only for contract, routing, algorithm, or critical behavior changes.
3. **Eval:** If `SKILL.md` behavior changes, add or update an eval-case first.
4. **Patch:** Replace, remove, or move guidance before appending new rules.
5. **Validate:** Check the quality gate and relevant eval expectations.

## Patch Criteria

Patch `SKILL.md` only when at least one is true:

- The existing algorithm causes repeated failure.
- The trigger or entry/exit contract is wrong.
- The skill cannot find required supporting context.
- A rule is ambiguous and the ambiguity affects output.
- A supporting file exists but is not discoverable from `SKILL.md`.

Do not patch `SKILL.md` when the change is only a one-time lesson, a project-specific exception, or detailed background better stored in `references/`.

## Eval Case Requirements

An eval-case should include:

- `Given`: starting condition or user request.
- `Expected`: observable behavior.
- Optional `Failure mode`: what must not happen.
- Optional `Files touched`: expected files or directories.

Keep evals small. They should protect behavior, not become a second specification.

## Learning Memory Size and Distillation

Each `LEARNINGS.md` has a `max_chars` budget (default 4000). See `rules/skills.md` for full policy.

### Before Adding a Lesson

1. Check current file size against `max_chars`.
2. If within budget, add the lesson normally.
3. If over budget, do **not** add. Run distillation first.

### Distillation Steps

1. Remove obsolete or superseded lessons.
2. Merge duplicate or overlapping lessons into one.
3. Shorten verbose descriptions while preserving the actionable insight.
4. Re-check size. Only add the new lesson when under budget.

### Validation

Run `python scripts/validate_skill_memory.py` to check all `skills/*/LEARNINGS.md`. Oversized files return `FAIL`. Malformed entries return `WARN`.
