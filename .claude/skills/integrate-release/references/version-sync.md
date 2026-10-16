# Version Sync

Use this reference after the CHANGELOG entry is ready and before archiving/merge.

## Release Version

The release version is authoritative from the spec route:

1. Parse `vMAJOR.MINOR.PATCH` from the current branch name (`feature/v{version}-{slug}` or `bugfix/v{version}-{slug}`).
2. Confirm the same version appears in the spec title and spec metadata.
3. Confirm the CHANGELOG entry uses the same version.

For `small_fix`, use the patch version selected for the CHANGELOG and include it in the merge message.

If branch, spec, and CHANGELOG disagree, stop before merge and fix the mismatch.

## Version Artifacts To Check

Search tracked project files for explicit project version storage. Minimum check:

- `pyproject.toml`: `project.version` or `tool.poetry.version`
- `package.json`: top-level `version`
- `Cargo.toml`: package `version`
- `VERSION` or `version.txt`
- source files with `__version__ = "..."`

Also update project-specific analogs discovered in the repository, including lockfiles or generated metadata when they are the project's accepted source of version truth.

## Update Rules

- Set every discovered version artifact to the release version without the `v` prefix.
- Keep branch/spec/CHANGELOG display as `v{version}` only where the local convention already includes `v`; manifest files usually store `{version}`.
- Use structured tooling when available (`tomllib`/TOML writer, package manager command, project script). If no writer is available, edit only the exact version field.
- Do not finish merge with CHANGELOG updated but another discovered version artifact still pointing to the previous release.

## Report

Record in the merge report:

```markdown
Version: {version}
Version artifacts: {updated files | none found}
```
