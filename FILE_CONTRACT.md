# File Contract

Intermediate files are explicit agent-facing artifacts. Do not replace them
with private reasoning, final prose, or a claim that a step was considered.

## KP Extraction

Path:

```text
intermediate/{course}/extraction/{chapter}/
```

Required files:

```text
01_inputs/source-scope.md
02_analysis/knowledge-points.md
02_analysis/knowledge-relationship-analysis.md
02_analysis/kp-consolidation-analysis.md
02_analysis/coverage-check.md
02_analysis/pool-insert-manifest.json
04_checks/pool-validation-report.md
```

## Problem Extraction

Path:

```text
intermediate/{course}/problem_extraction/{chapter}/
```

Required files:

```text
01_inputs/kp-query-result.json
01_inputs/full-problem-bank.md
02_analysis/problem-insert-manifest.json
04_checks/problem-pool-validation-report.md
```

## Problem Candidate Generation

Path:

```text
intermediate/{course}/problem_generation/{chapter}/
```

Required agent-to-script artifacts for a generation run:

```text
02_analysis/candidate-insert-manifest.json
04_checks/candidate-audit-report.json
```

The candidate manifest contains source-grounded candidate bodies and evidence.
The audit report supplies the semantic PASS/FAIL decision. Scripts independently
run structural checks. A candidate becomes `gate_passed` only when both checks
pass; only `gate_passed` candidates may be practiced or imported.

Candidate rows, attempts, and current learner signals live in the course pool.
They remain separate from durable `problems` until explicit import. Import
renders structured options into `problem_text` and answer explanations into
`solution`; it does not add candidate-only fields to the durable table.

## Course Learning Network

Low-level audited relations may be added after KP extraction.

Optional relation manifest:

```text
intermediate/{course}/extraction/{chapter}/02_analysis/relation-insert-manifest.json
```

Legacy optional learner signal map:

```text
intermediate/{course}/signals/{chapter}/signal-map.json
```

These files do not replace the required KP extraction files. Relation manifests
store durable point-to-point graph facts. New learner signals are stored in the
course SQLite pool. Signal-map JSON stays available only as a compatibility or
handoff input for Focus Map queries.

## Problem-Set View

Path:

```text
intermediate/{course}-{chapter}/problem-set/
```

Required files:

```text
01_inputs/view-scope.md
02_analysis/problem-query-result.json
03_plans/selection-plan.md
04_checks/problem-set-check.md
04_checks/solution-sync-check.md
```

Outputs:

```text
output/{course}/{chapter}/{chapter}-problem-set.md
output/{course}/{chapter}/{chapter}-solutions.md
```

## Rules

- Inputs preserve source facts and user intent.
- Analysis files preserve extracted data and mappings.
- Plans decide selection, ordering, and rendering.
- Checks state pass/fail, broken rule, return layer, and repair action.
- Student-facing problem sets must not show internal IDs, KP mappings, or
  solution text.

## Runtime Guard

`lessonkit.py guard` is the v1 phase guard for this contract. It checks that
the required files for a command exist and that check files do not contain
blocking markers such as `Result: FAIL`, `Status: FAIL`, table-cell `FAIL`, or
non-zero `ERROR` counts.

By default, guard only depends on tracked intermediate artifacts and rendered
outputs. For `extract-chapter` and `extract-problems`, passing
`--db pool/<course>.db` also runs `pipeline/scripts/validate-pool.py` and
blocks on its non-zero exit codes. This keeps source-only review lightweight
while allowing stronger local validation when the ignored SQLite pool exists.

Guard coverage:

```text
extract-chapter   -> KP Extraction
extract-problems  -> Problem Extraction
problem-set       -> Problem-Set View plus rendered outputs
```

With `--apply`, the guard writes `.lessonkit/state.yaml`:

- PASS sets `phase: complete`, clears `blocked_reason`, and records
  `next_action`.
- FAIL sets `phase: blocked`, records the first missing artifact or blocking
  marker, failed pool validation, or missing DB, and exits with code 2.

Runtime state is a recovery checkpoint for agents. It is not a substitute for
the intermediate files or for the SQLite pool.
