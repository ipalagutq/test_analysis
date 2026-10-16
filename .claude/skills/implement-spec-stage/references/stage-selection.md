# Stage Selection

Use this reference before implementation. The goal is to choose exactly what this run is allowed to do.

## Inputs

- Current git branch.
- `.ai/specs/{branch-name}.md`.
- User request for this run.

## Selection Rules

1. Stop if current branch is `main` or `master`.
2. Open the spec matching the current branch.
3. Find implementation stages under `## Этапы реализации`.
4. Select the first stage marked `🔄` if one exists.
5. Otherwise select the first stage marked `⬜`.
6. If all stages are `✅`, stop and tell the user to proceed to `write-tests`.
7. If multiple stages are `🔄`, stop and ask the user which one is active.

## Run Scope

Default scope is one selected stage per session.

Continue to another stage only when the user explicitly asked to implement all stages in this run. Even then, repeat context gathering and sufficiency gate for every stage.

## Stop Conditions

Stop before edits when:

- no matching spec exists
- spec has no unchecked stages
- selected stage has no files or implementation details
- selected stage depends on an earlier incomplete stage
- user asks to skip a required workflow step

## Output Shape

Before editing, hold this internal state:

```text
spec_path: .ai/specs/{branch-name}.md
selected_stage: {stage title}
stage_status: ⬜ | 🔄
target_files: {files listed in stage}
scope: one_stage | all_stages_requested
```
