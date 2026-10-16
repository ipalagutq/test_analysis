# Sufficiency Gate — apply-small-fix

Финальная проверка перед commit и передачей в `integrate-release`.

## PASS Criteria

| # | Критерий | Проверка |
|---|---|---|
| 1 | Branch | `fix/{slug}` |
| 2 | No spec | `.ai/specs/*` не создан для фикса |
| 3 | Scope | 1-3 файла или явно механическое исключение |
| 4 | Patch | изменены только scoped files |
| 5 | Verification | targeted/full check прошёл или объяснён `not applicable` |
| 6 | Commit | `fix: {summary}` через `commit-helper` |
| 7 | Next | указан `next_skill: integrate-release` |

## FAIL Signals

- diff содержит migration/schema/API change;
- появились новые workflow/spec artifacts;
- есть unrelated changes в staged files;
- тесты упали;
- fix требует ещё один этап работы.

## Output

```markdown
Small-fix gate: PASS
Branch: `fix/{slug}`
Files: {N}
Verification: `{command/result}`
Next: `integrate-release`
```
