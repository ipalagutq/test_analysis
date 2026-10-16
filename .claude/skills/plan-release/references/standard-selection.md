# Standard Selection

Use this reference when choosing how to validate a spec.

## Decision Table

| Task type | Signals | Standard |
|---|---|---|
| Code feature | Source code, API, CLI, config, tests, runtime behavior | `validate-requirements-ieee29148` |
| Bugfix | Broken behavior, failing test, regression, compatibility issue | `validate-requirements-ieee29148` |
| Workflow skill/rule change | `skills/`, `rules/`, `templates/`, `init/` changes that alter behavior | `validate-requirements-ieee29148` unless user asks for docs-only |
| Documentation or research | Markdown review, literature review, guide, report | Ask user which document standard to use |
| Mixed code + docs | Code behavior plus docs | `validate-requirements-ieee29148` for implementation requirements; include docs acceptance criteria |
| Unclear | Ambiguous impact | Ask user before writing spec |

## Rules

1. If implementation touches executable behavior, choose `validate-requirements-ieee29148`.
2. If the task is only a document artifact, do not pretend it is a software requirements spec; ask for the document quality standard.
3. If user asks for a small local edit without a spec, stop: `plan-release` is not the small-fix route.
4. If a task changes workflow governance, include traceability and install/update implications in the spec.

## Metadata

Record the selected standard in the spec header:

```markdown
> **Standard:** validate-requirements-ieee29148 | Score: {score}/100
```

For document standards:

```markdown
> **Standard:** {document-standard-name} | Score: {score-or-manual-pass}
```
