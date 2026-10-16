# Decisions Check

Use this reference during step 5 of the plan-release algorithm ("Изучить контекст проекта") to verify draft requirements against formalized product boundaries.

## Format of `.ai/DECISIONS.md`

```markdown
# Project Decisions — {Project Name}

Product boundaries: чем проект является, а чем нет.

## IS (проект является)

- {утверждение о том, что проект делает/включает}

## IS NOT (проект не является)

- {утверждение о том, что проект не делает/исключено}
```

Each entry is a single statement about a product boundary. Technical decisions live in ADR (`docs/decisions/`) or inside specs, not here.

## Check Algorithm

Run this algorithm after gathering draft requirements and before writing the spec.

### Step 1: Read decisions

If `.ai/DECISIONS.md` exists, read all IS and IS NOT entries. If it does not exist, skip the check and add a note to the spec: «Product boundaries не формализованы» in `Архитектурные решения`.

### Step 2: Check each draft requirement against IS NOT

For each draft requirement in the spec:

1. Compare the requirement's implied scope against every IS NOT entry.
2. If the requirement directly contradicts an IS NOT boundary → this is a **conflict**.
3. If the requirement is adjacent but not clearly contradicting → this is an **ambiguity**.

### Step 3: Check each draft requirement against IS

For each draft requirement:

1. Compare the requirement's implied scope against every IS entry.
2. If the requirement introduces a new scope area not covered by any IS entry → this is an **expansion**.
3. If the requirement clearly falls within an existing IS entry → no action needed.

### Step 4: Handle conflicts

For each conflict found in Step 2:

1. Stop and raise an AUQ question asking the user whether the IS NOT boundary should be expanded.
2. Do not proceed with writing the spec until the user resolves the conflict.
3. If the user confirms expansion → mark for "Расширение решений проекта" section.

### Step 5: Handle expansions

For each expansion found in Step 3:

1. Record the new boundary in the spec's "Расширение решений проекта" table.
2. Raise an AUQ question to confirm the expansion is intentional.
3. If the user confirms → include in the spec; if not → remove the expanding requirement.

## AUQ Question Templates

### Conflict with IS NOT

```markdown
Нужно уточнить scope перед ТЗ:

Требование «{requirement}» конфликтует с границей продукта: «{IS NOT entry}».

Расширить границу продукта для этого ТЗ?

Почему это важно: расширение IS NOT границы меняет product scope и повлияет на будущие ТЗ.
```

### New scope not covered by IS

```markdown
Нужно уточнить scope перед ТЗ:

Требование «{requirement}» вводит новую область, не описанную в product boundaries: «{new area}».

Добавить как новую IS границу?

Почему это важно: фиксация расширения делает его явным и видимым для будущих ТЗ.
Рекомендуемый default: добавить в секцию «Расширение решений проекта» с пометкой IS
```

## Output

After running the algorithm, the spec should contain:

- Conflicts resolved through AUQ (recorded in `Архитектурные решения`).
- Expansions documented in «Расширение решений проекта» table (if any).
- A note about missing DECISIONS.md (if it does not exist).
