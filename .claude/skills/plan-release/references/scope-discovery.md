# Scope Discovery

Use this reference before writing a spec. The goal is to expose decisions that would otherwise be guessed.

## When To Ask

Ask the user when the answer changes:

- scope boundaries
- architecture or data flow
- user-visible behavior
- API, CLI, or file format contracts
- migration, compatibility, or rollout
- acceptance criteria or Definition of Done
- risk posture: security, performance, reliability, privacy
- answer contradicts or expands product boundaries in `.ai/DECISIONS.md`

Do not ask questions whose answer only changes wording.

**Exhaustive ASQ policy:** ask about all ambiguities, including those with a safe default, if the decision affects scope. Do not silently accept a safe default when the choice influences what the spec covers.

## Question Bank

### Outcome

- What exact user or project outcome should exist after this spec is implemented?
- What current pain or failure does this change remove?
- How will we know the change is successful?

### Scope Boundaries

- What is explicitly in scope?
- What is explicitly out of scope for this iteration?
- Are there related workflows that must stay unchanged?
- Is this a one-off change or a reusable capability?

### Product Behavior

- What should happen by default?
- What should happen for empty, missing, invalid, or conflicting input?
- Who is the user or actor for the behavior?
- Does the change need a new command, file, API endpoint, UI control, or workflow step?

### Technical Boundaries

- Which modules, skills, rules, templates, or docs are expected to change?
- Is backward compatibility required?
- Are migrations, config changes, or install changes needed?
- Are there external services, credentials, or environment assumptions?

### Quality And Tests

- What acceptance criteria are objective enough to test?
- Which tests or checks should prove the behavior?
- Is a manual verification step acceptable?
- What failure mode must not regress?

### Rollout And Risk

- Can the change be delivered in one stage?
- Does it need feature flags, fallback, rollback, or staged rollout?
- What is the highest-risk assumption?
- What would make this spec too broad?

### Decisions Alignment

- Does this requirement conflict with any IS NOT boundary in `.ai/DECISIONS.md`?
- Does this requirement introduce scope not covered by any IS boundary?
- Is the expansion of product boundaries intentional or accidental?
- Should a new IS/IS NOT entry be added to DECISIONS.md?

## ASQ Output Shape

ASQ always asks exactly one question per round. Do not group multiple questions in one request, even when several open decisions exist.

Pick the highest-impact unresolved decision first:

1. Blocks writing a correct spec.
2. Changes scope, architecture, UX/API, or Definition of Done.
3. Has no safe default.
4. Would cause the largest rework if guessed incorrectly.

```markdown
Нужно уточнить scope перед ТЗ:

{One question}

Почему это важно: {impact}
Рекомендуемый default: {default, if safe}
```

After the user answers:

1. Record the decision in working notes for the spec.
2. Re-evaluate whether another ambiguity remains — including non-blocking ones where a safe default exists but the choice affects scope.
3. If yes, ask the next single question in a new ASQ round.
4. If no ambiguity remains, write the spec and record decisions in `Архитектурные решения` and consequences in `Этапы реализации`.
