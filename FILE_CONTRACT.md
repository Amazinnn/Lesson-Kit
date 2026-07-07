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
