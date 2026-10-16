# Requirements Quality

Use this reference before final validation. It turns user intent into implementable requirements.

## Requirement Checklist

Each requirement or implementation stage should be:

- **Necessary** — tied to a user/project need.
- **Unambiguous** — only one reasonable interpretation.
- **Complete** — includes inputs, outputs, edge cases, and constraints.
- **Consistent** — does not contradict architecture, workflow, or other requirements.
- **Singular** — one responsibility per requirement or stage.
- **Feasible** — realistic in the current stack and repo shape.
- **Traceable** — linked to goal, decision, or user answer.
- **Verifiable** — has an objective check, test, or inspection criterion.

## Strong Formulations

Prefer:

- "The system must create `.ai/specs/feature-v{version}-{slug}.md` before branch creation."
- "A code spec passes only when IEEE score is at least 85/100."
- "The validator must fail if `Этапы реализации` is absent."

Avoid:

- "Improve quality."
- "Handle edge cases."
- "Make it more convenient."
- "Add support for docs etc."

## Acceptance Criteria

Every stage should contain:

- files or modules expected to change
- behavior to implement
- objective Definition of Done
- tests, scripts, or manual verification
- dependencies on earlier stages

## Common Failure Modes

| Failure | Repair |
|---|---|
| Hidden decision | Move it to `Архитектурные решения` or ask the user |
| Broad stage | Split by dependency or observable behavior |
| Vague DoD | Replace with testable condition |
| Missing edge case | Add explicit acceptance criterion |
| Duplicate requirement | Keep one source and reference it |
| Architecture mismatch | Re-read `.ai/ARCHITECTURE.md` and revise |

## Final Pass

Before validation, answer:

1. Could `implement-spec-stage` implement this without asking new scope questions?
2. Could `write-tests` derive tests from the acceptance criteria?
3. Could `integrate-release` decide whether the work is complete?

If any answer is no, the spec is not ready.
