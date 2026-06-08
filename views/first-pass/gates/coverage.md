# Gate: Coverage — KP Completeness and Source Traceability

<!-- Intermediate path convention: intermediate/{course}-{ch}/{view}/{layer}/ -->

Validates that every KP in the SQLite pool is accounted for in the structure plan,
and that core quality attributes (source_location, ordering) are preserved.

## Pre-Check

Run this validation SQL against the pool:
```sql
SELECT COUNT(*) FROM knowledge_points WHERE kp_id LIKE '{chapter}-%';
```
Compare with number of KPs rendered in `03_plans/structure-plan.md`.

## Checks

| # | Failure | Return To | Forbidden Repair |
|---|---------|-----------|-----------------|
| 1 | KP count in `03_plans/structure-plan.md` does not match pool query count | 02_analysis (re-query pool) | Adjust count in plan without re-querying |
| 2 | KP in plan has `source_location` NULL or empty in pool data | Pipeline (fix pool data) | Invent a source_location value |
| 3 | KP with `importance = 'core'` is deferred or omitted without documented justification in `01_inputs/view-scope.md` | 01_inputs (add justification) or 03_plans (add KP) | Change importance to 'supplementary' to skip it |
| 4 | `related_kp_ids` links to a KP not in this chapter's scope (broken relationship) | Pipeline (fix relationship data in pool) | Delete the relationship |
| 5 | Section ordering deviates from source order without documented justification in `01_inputs/view-scope.md` | 01_inputs | Fix output order to match plan |
| 6 | Student-requested priority KP (from `01_inputs/view-scope.md` configuration) is not rendered | 03_plans | Add a footnote instead of full rendering |
| 7 | KP has `kp_id` in plan but no `student_visible_title` or no `quick_absorption` | 03_plans | Add placeholder text |

## Pass Condition

Every KP from the pool appears in the structure plan with valid `student_visible_title`, `quick_absorption`, and source traceability. Core KPs are never silently omitted. Ordering changes are justified.

## Related

- `pool-query.md` — how to query the pool
- `structure-plan-template.md` — what a complete plan looks like
