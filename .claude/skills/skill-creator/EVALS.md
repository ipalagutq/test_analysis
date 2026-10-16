# Evals — skill-creator

Regression cases for changes to `skill-creator`. Add a case before changing `SKILL.md` behavior.

## SC-EVAL-001 — New Skill Has Self-Improvement Files

**Given:** User asks to create a new workflow skill.

**Expected:**
- `skills/{name}/SKILL.md` exists.
- `skills/{name}/LEARNINGS.md` exists.
- `skills/{name}/EVALS.md` exists.
- `SKILL.md` contains Continuous Improvement or equivalent Improvement Triage.

## SC-EVAL-002 — Supporting Files Are One-Level Deep

**Given:** User asks for a skill with detailed context or runbooks.

**Expected:**
- `SKILL.md` directly lists relevant `references/`, `scripts/`, or `assets/`.
- No required navigation chain depends on `reference-a.md -> reference-b.md`.
- Detailed context that is not needed on every run is outside `SKILL.md`.

## SC-EVAL-003 — Behavioral Patch Requires Eval

**Given:** User asks to change an existing skill's behavior.

**Expected:**
- The failure or new expected behavior is represented in `EVALS.md`, unless the assistant explicitly states why a manual-only eval is appropriate.
- `SKILL.md` patch is minimal and replaces, removes, or moves guidance rather than simply appending more rules.

## SC-EVAL-004 — Claude Target Is Preserved

**Given:** Local workspace contains adapter-specific paths such as `.agents/skills/`.

**Expected:**
- `skill-creator` still treats `skills/` as source of truth.
- Installation guidance remains oriented to `.claude/skills/`.
- The assistant does not "fix" paths to non-Claude adapters unless the user explicitly requests it.
