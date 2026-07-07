# Command: Create Problem Set View

## One-Line Purpose

Render a practice set and matching solution file from the durable `problems`
pool.

## Entry Conditions

Use this command when:

- `pool/{course}.db` exists.
- `knowledge_points` contains rows for `{course}-{chapter}`.
- `problems` contains rows for `{course}-{chapter}`.

Do not use this command to ingest problems. Use
`pipeline/commands/extract-problems.md` first.

## Required Load List

```text
RED_LINES.md
STYLE.md
views/common/skills/pool-query.md
views/common/gates/format-rendering.md
views/common/gates/red-lines.md
views/problem-set/skills/coverage-first-selection.md
views/problem-set/skills/problem-set-rendering.md
views/problem-set/gates/coverage.md
views/problem-set/gates/solution-sync.md
views/problem-set/templates/view-scope-template.md
views/problem-set/templates/selection-plan-template.md
views/problem-set/templates/problem-set-template.md
views/problem-set/templates/solution-template.md
```

## Workflow

1. Create the workspace:

```text
intermediate/{course}-{chapter}/problem-set/
├── 01_inputs/
├── 02_analysis/
├── 03_plans/
└── 04_checks/
```

2. Capture scope in:

```text
01_inputs/view-scope.md
```

Minimum config:

- course
- chapter
- requested count or all
- source_kind, default `textbook`

3. Query the pool:

```bash
python pool/scripts/query-pool.py --db pool/{course}.db --chapter {course}-{chapter} --view problem-set --source-kind {source_kind}
```

Save as:

```text
02_analysis/problem-query-result.json
```

Stop if `problems[]` is empty.

4. Build the selection plan:

```text
03_plans/selection-plan.md
```

Default policy:

- Cover core KPs first.
- Keep source order unless the user asks for another order.
- Do not generate new problems.
- Record KP coverage gaps instead of inventing problems.

5. Render two files:

```text
output/{course}/{chapter}/{chapter}-problem-set.md
output/{course}/{chapter}/{chapter}-solutions.md
```

The problem set contains no answer/solution text. The solution file mirrors the
selected problem numbering; missing `solution` values render as `待补`.

6. Run gates and save:

```text
04_checks/problem-set-check.md
04_checks/solution-sync-check.md
```

## Blockers

- No queried problems for the requested `source_kind`.
- Selection plan has no selected problems.
- Student-facing problem set exposes `kp_id`, internal field names, or solution text.
- Solution file numbering does not match the problem set.

## Output Checklist

```text
intermediate/{course}-{chapter}/problem-set/01_inputs/view-scope.md
intermediate/{course}-{chapter}/problem-set/02_analysis/problem-query-result.json
intermediate/{course}-{chapter}/problem-set/03_plans/selection-plan.md
intermediate/{course}-{chapter}/problem-set/04_checks/problem-set-check.md
intermediate/{course}-{chapter}/problem-set/04_checks/solution-sync-check.md
output/{course}/{chapter}/{chapter}-problem-set.md
output/{course}/{chapter}/{chapter}-solutions.md
```
