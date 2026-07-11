# Command: Extract Problems

## One-Line Purpose

Extract durable problems from source material, map each problem to existing
knowledge points, and insert them into the unified SQLite `problems` table.

## Entry Conditions

Use this command when:

- A course/chapter KP pool already exists in `pool/{course}.db`.
- The user wants textbook, quiz, midterm, final, makeup, or other problems
  available for views.
- The task is problem ingestion, not rendering a practice set.

Do not use this command when:

- The chapter has not been extracted into KPs yet.
- The user wants a student-facing problem set. Use `views/problem-set/command.md`.
- The user wants generated supplemental practice. Use
  `pipeline/commands/generate-problem-candidates.md`; problem extraction stores
  sourced problems only.

## Required Load List

Read before execution:

```text
RED_LINES.md
STYLE.md
docs/design/kp-pool-modular-views.md
pipeline/templates/problem-insert-manifest.md
views/common/skills/pool-query.md
```

## Workflow

1. Create the workspace:

```text
intermediate/{course}/problem_extraction/{chapter}/
├── 01_inputs/
├── 02_analysis/
├── 03_plans/
└── 04_checks/
```

2. Query the existing KP pool:

```bash
python pool/scripts/query-pool.py --db pool/{course}.db --chapter {course}-{chapter} --view knowledge-guide
```

Save the JSON as:

```text
intermediate/{course}/problem_extraction/{chapter}/01_inputs/kp-query-result.json
```

3. Build the complete source problem bank before manifest creation:

```text
intermediate/{course}/problem_extraction/{chapter}/01_inputs/full-problem-bank.md
```

This file lists every extracted problem in source order. It is an audit file,
not the final database manifest.

During this step, normalize text block formatting. The extracted problem bank
must already show clear Markdown blocks:

- stem, subparts, displayed formulas, and source preambles are separated by
  blank lines;
- subparts such as `a)`, `b)`, `c)` start their own paragraphs;
- no problem is stored as `... a) ... b) ...` collapsed onto one line.

4. Map each problem to one or more existing `kp_id` values.

Do not create new KPs in this command. If a problem cannot be mapped to any
existing KP, stop and report the gap.

5. Write:

```text
intermediate/{course}/problem_extraction/{chapter}/02_analysis/problem-insert-manifest.json
```

Follow `pipeline/templates/problem-insert-manifest.md`.

`problem_text` and non-null `solution` must preserve the same block formatting
as JSON strings using `\n\n` between logical blocks. Do not flatten the audit
file into one-line strings.

6. Insert:

```bash
python pipeline/scripts/insert-problems.py --db pool/{course}.db --manifest intermediate/{course}/problem_extraction/{chapter}/02_analysis/problem-insert-manifest.json --strict
```

Use `--upsert` only when intentionally replacing existing problem rows.

7. Validate:

```bash
python pipeline/scripts/validate-pool.py --db pool/{course}.db --course {course} --chapter {chapter}
```

Save the report as:

```text
intermediate/{course}/problem_extraction/{chapter}/04_checks/problem-pool-validation-report.md
```

## Blockers

- No existing KP rows for the chapter.
- Any problem lacks `kp_ids`.
- Any problem has invalid `problem_type` or `source_kind`.
- Any `problem_text` or non-null `solution` collapses multiple subparts or
  solution steps into one line.
- `insert-problems.py --strict` reports validation errors.

## Output Checklist

```text
intermediate/{course}/problem_extraction/{chapter}/01_inputs/kp-query-result.json
intermediate/{course}/problem_extraction/{chapter}/01_inputs/full-problem-bank.md
intermediate/{course}/problem_extraction/{chapter}/02_analysis/problem-insert-manifest.json
intermediate/{course}/problem_extraction/{chapter}/04_checks/problem-pool-validation-report.md
```
