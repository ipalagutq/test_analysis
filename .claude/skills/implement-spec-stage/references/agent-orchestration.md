# Agent Orchestration

Use this reference when gathering stage context with existing agents.

Do not copy agent prompts into `implement-spec-stage`. The source of truth is:

- `templates/agents/code-mapper.md`
- `templates/agents/data-flow-tracer.md`

Installed target projects receive them as:

- `.claude/agents/code-mapper.md`
- `.claude/agents/data-flow-tracer.md`

## When To Invoke

Invoke both agents in parallel when the selected stage touches source code, data contracts, APIs, workflow behavior, or more than one file.

For docs-only edits or a single obvious file with no dependencies, direct reading can be enough; record why agents were skipped.

## code-mapper Input

Pass exactly:

- `stage_name`
- `target_files`
- `architecture_layer`
- `spec_summary`

If `architecture_layer` is unclear, infer it from `.ai/ARCHITECTURE.md`; if inference is unsafe, say so and use `unknown`.

## data-flow-tracer Input

Pass exactly:

- `stage_name`
- `target_files`
- `entry_point`
- `spec_summary`

If `entry_point` is unclear, choose the most likely function/class from the selected stage and mark it as inferred. If no reasonable entry point exists, ask the user or skip this agent with a reason.

## Fan-In

After both agents return:

- Compare target file lists with spec.
- Check for `NOT_FOUND`, `INSUFFICIENT_CONTEXT`, and `CHAIN_BREAK`.
- Extract DTOs/contracts, dependencies, analogous patterns, and gaps.
- Feed the results into `references/sufficiency-gate.md`.

Do not treat agent output as authoritative when it conflicts with files you read directly.

## Agent Output Validation

After Fan-In, validate agent output against machine-readable contracts before proceeding to sufficiency gate.

Schemas live in `schemas/agent-output/{agent}.json`. Validator: `scripts/validate_agent_output.py`.

### When Agent Output Is Saved to File

Run: `python scripts/validate_agent_output.py --agent {agent} --input {output_file} [--target-file PATH]...`

### When Agent Output Is Inline

Apply the same contract rules manually: check required sections, size budget, target file mentions, forbidden phrases, unknown markers, trailing text.

### Reaction to Findings

| Finding | Action |
|---|---|
| `FAIL` | Stop implementation immediately. Report: agent name, finding code (`MISSING_SECTION`, `OVER_BUDGET`, etc.), specific message. Do not proceed to sufficiency gate until the agent output is corrected or the run is retried. |
| `WARN` | Allow local gap-filling: read 1-2 additional files to compensate, then re-run sufficiency gate. Do not proceed if gaps remain. |
| `OK` | Proceed to sufficiency gate normally. |

### Skip Conditions

Skip validation only when agents were skipped (docs-only edit, single obvious file). Document the reason explicitly.
