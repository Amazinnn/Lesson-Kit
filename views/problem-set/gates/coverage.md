# Gate: Problem-Set Coverage

Pass only if the selection plan explains what was selected and what coverage
gaps remain.

Fail when:

| Failure | Return to | Forbidden Repair |
|---|---|---|
| Selected problems do not cover any requested/core KP | `03_plans/selection-plan.md` | Adding invisible KP labels to the final problem set |
| A core KP has available problems but none were selected | `03_plans/selection-plan.md` | Inventing a new problem in v1 |
| Coverage gaps are hidden | `03_plans/selection-plan.md` | Claiming full coverage without selected problems |

Coverage details stay in the plan/check files, not in the student-facing
problem set.
