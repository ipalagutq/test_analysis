# Generated Skill Structure

Use this reference when creating a new skill or doing a large restructuring.

## Directory Layout

```text
skills/{skill-name}/
├── SKILL.md
├── references/
│   └── {focused-topic}.md
├── scripts/
│   └── {validator-or-helper}
├── assets/
│   └── {template-or-static-resource}
├── LEARNINGS.md
└── EVALS.md
```

Create only the supporting directories that are useful for the skill. `LEARNINGS.md` and `EVALS.md` are always required.

## SKILL.md Contents

`SKILL.md` should contain:

1. Frontmatter: `name`, `description`, `type`, and `step` for workflow skills.
2. One-paragraph purpose.
3. Workflow Contract for workflow/internal skills.
4. Supporting Files table with direct links to useful files.
5. Short algorithm for the normal path.
6. Validation checklist.
7. Continuous Improvement block.
8. No more than 7 behavioral rules.

## Supporting File Rules

- `references/`: detailed checklists, rubrics, runbooks, edge cases, examples that are not needed on every run.
- `scripts/`: deterministic validators, generators, converters, or repeated checks.
- `assets/`: templates, static examples, images, or data.
- Keep references one-level deep from `SKILL.md`.
- Give files purpose-based names: `requirements-quality.md`, `merge-safety.md`, `deploy-rollback.md`.

## LEARNINGS.md Template

```markdown
# Learnings — {skill-name}

| Date | Lesson | Trigger |
|---|---|---|

## Retrieval Rules

- Read at the start of each run.
- Use only lessons relevant to the current task.
- Replace obsolete lessons instead of accumulating contradictions.
```

## EVALS.md Template

```markdown
# Evals — {skill-name}

Regression cases for behavior changes.

## {SKILL}-EVAL-001 — {Case Name}

**Given:** {starting condition}

**Expected:**
- {observable result}
- {observable result}
```
