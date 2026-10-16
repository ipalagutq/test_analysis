# Evals — plan-release

Regression cases. Используются как gate перед патчами `SKILL.md`.

## SC-EVAL-001 — Hidden Scope Requires Questions

**Given:** User asks for a new feature with unclear behavior, API contract, edge case handling, or Definition of Done.

**Expected:**
- The skill reads `references/scope-discovery.md`.
- The skill asks exactly one question in the ASQ round.
- The question is the highest-impact unresolved decision whose answer changes the spec.
- The spec records answered decisions in `Архитектурные решения`.

**Failure mode:** The skill silently invents non-obvious scope decisions or asks multiple questions in one ASQ round.

## SC-EVAL-001B — ASQ Never Batches Questions

**Given:** User asks for a feature with three unresolved scope decisions.

**Expected:**
- The skill asks one question only.
- After the user answers, the skill may ask the next single question in a separate round.
- The skill does not use a numbered multi-question list.

**Failure mode:** The skill groups several questions into one message.

## SC-EVAL-002 — Code Task Uses IEEE Standard

**Given:** User asks for a code feature, bugfix, API change, config change, or workflow behavior change.

**Expected:**
- The skill selects `validate-requirements-ieee29148`.
- The spec metadata records the standard and score.
- The spec passes only with score ≥85.

**Failure mode:** The skill uses a document-only standard for executable behavior.

## SC-EVAL-003 — Document Task Does Not Pretend To Be Code

**Given:** User asks for a literature review, guide, report, or other docs-only artifact.

**Expected:**
- The skill reads `references/standard-selection.md`.
- The skill asks which document standard to use when none is specified.
- The spec does not default to IEEE code validation without confirmation.

## SC-EVAL-004 — Spec Structure Is Deterministically Checked

**Given:** A spec file has been written.

**Expected:**
- The skill runs `scripts/validate_spec_structure.py {path-to-spec}`.
- Missing required sections, workflow rows, stage markers, metadata, or score metadata are reported.
- The skill fixes structural failures before branch/commit completion.

## SC-EVAL-005 — Supporting Files Stay One-Level Deep

**Given:** `plan-release` needs additional detailed guidance.

**Expected:**
- `SKILL.md` links directly to the supporting file.
- The new file has a focused purpose-based name.
- The change does not introduce chains like `SKILL.md -> reference-a.md -> reference-b.md`.

## SC-EVAL-006 — Spec Names Carry Future Release Version

**Given:** User asks for a new feature or bugfix spec.

**Expected:**
- The skill selects a future SemVer release version from `.ai/CHANGELOG.md`.
- The spec title, spec filename, branch name, and workflow metadata all contain the same `MAJOR.MINOR.PATCH` value.
- Feature artifacts use `feature-v{version}-{slug}.md` and `feature/v{version}-{slug}`.
- Bugfix artifacts use `bugfix-v{version}-{slug}.md` and `bugfix/v{version}-{slug}`.

**Failure mode:** The skill creates a spec or branch without version, with mismatched versions, or with the old `bugfix/{version}-{slug}` convention.
