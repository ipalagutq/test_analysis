# Context Gathering

Use this reference before touching implementation files.

## Required Context

Read:

- current spec
- `.ai/ARCHITECTURE.md`
- selected stage section
- target files listed in the selected stage
- nearby tests or existing tests for touched modules
- project rules relevant to touched paths

Read additional `.ai/` docs only when the spec or architecture points to them.

## Target File Handling

For each file listed in the selected stage:

- If it exists, read it before editing.
- If it does not exist, identify the closest existing pattern in the same layer.
- If the path is ambiguous, stop and ask the user or revise the stage only if the spec clearly supports it.

## Reference Pattern Search

Find at least one analogous implementation when possible:

- same architectural layer
- same IO shape
- same framework or helper API
- same test style

If no pattern exists, record that explicitly before implementation.

## Context Summary

Before implementation, maintain a short summary:

```text
stage_goal: {one sentence}
target_files: {paths}
existing_patterns: {paths or NOT FOUND}
contracts: {DTO/API/CLI/file formats}
tests_to_run: {commands}
open_gaps: {none/list}
```
