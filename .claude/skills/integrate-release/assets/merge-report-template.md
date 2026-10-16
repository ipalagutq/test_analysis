# Merge Report Template

## Spec Route

```markdown
✅ Merge завершён

Ветка:    {branch} → main
Версия:   {version}
CHANGELOG: .ai/CHANGELOG.md обновлён
Version artifacts: {updated files | none found}
Spec:      .ai/specs/archive/{branch-slug}.md
Tests:     {X} passed
Next:      deploy-release
```

## Small-Fix Route

```markdown
✅ Merge завершён

Ветка:    {branch} → main
Версия:   {version}
CHANGELOG: .ai/CHANGELOG.md обновлён
Version artifacts: {updated files | none found}
Spec:      не требуется (apply-small-fix)
Tests:     {X} passed
Next:      deploy-release
```
