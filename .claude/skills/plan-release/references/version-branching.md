# Version And Branching

Use this reference before creating the spec file, branch, or commit.

## Version Source

Read `.ai/CHANGELOG.md` and find the latest released or in-progress version entry.

Each spec is a release plan. The selected version is the future project version after the whole workflow finishes, not merely an internal planning number.

Default bump:

- Feature or workflow capability: minor bump.
- Bugfix or correction: patch bump.
- Breaking workflow change: major bump.
- Documentation-only spec: ask if it belongs to the current version or a docs-specific version.

## Names

Use lowercase kebab-case slugs.

| Artifact | Feature | Bugfix |
|---|---|---|
| Spec title | `# {Feature Name} — Specification (v{version})` | `# {Bug Name} — Bugfix Specification (v{version})` |
| Spec file | `.ai/specs/feature-v{version}-{slug}.md` | `.ai/specs/bugfix-v{version}-{slug}.md` |
| Branch | `feature/v{version}-{slug}` | `bugfix/v{version}-{slug}` |
| Commit | `docs: add spec for {feature-name}` | `docs: add bugfix spec for {bug-name}` |

The same `MAJOR.MINOR.PATCH` value must appear in the title, spec file, branch, and Workflow metadata. If any of them disagree, stop and fix the names before committing.

## Slug Rules

- Use 2-6 words.
- Remove filler words.
- Prefer domain nouns: `skill-supporting-files`, `spec-validator`, `deploy-rollback`.
- Keep version out of the slug; version is already in the prefix.

## Safety Checks

Before branch creation:

- current branch is `main` or `master`
- no active spec already covers the same change
- proposed file path does not exist
- branch name does not exist locally
- chosen version is greater than the latest tracked project version
- branch and spec file both include `v{version}` exactly once

Before commit:

- only the new spec should be staged unless the user explicitly requested more
- validation score is recorded
- next skill is clear: `implement-spec-stage`
