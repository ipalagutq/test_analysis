# Stage Implementation

Use this reference while editing files for the selected stage.

## Boundaries

Implement only the selected stage.

Allowed:

- files listed in the stage
- tests or fixtures directly needed for the stage
- small supporting edits required by the architecture

Not allowed without explicit user request:

- implementing later stages
- broad refactors
- unrelated cleanup
- changing workflow rules to make implementation easier
- editing generated or installed copies instead of source-of-truth files

## Implementation Order

1. Modify the narrowest required files first.
2. Follow existing local patterns and helper APIs.
3. Keep public contracts stable unless the spec explicitly changes them.
4. Add or update focused tests when the stage introduces behavior.
5. Run the checks identified during context gathering.
6. Update spec status only after checks pass.

## Working With Dirty Trees

If the worktree has unrelated changes:

- do not revert them
- avoid touching unrelated files
- if a needed file already has user changes, read carefully and work with them
- mention residual risk if verification is limited by unrelated dirty state

## Scope Drift Check

Before finalizing, ask:

1. Did every edit map to the selected stage?
2. Did any edit implement a later stage?
3. Did any edit change a public contract not mentioned by the spec?
4. Can `write-tests` understand what remains?

If any answer is unsafe, stop and explain before committing.
