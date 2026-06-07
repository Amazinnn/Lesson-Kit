# Gate: Section Order

The source section order controls the final Stage 1 `速览`.

| Failure | Return to | Forbidden repair |
|---|---|---|
| Source sections are missing or unordered | `intermediate/first_pass/01_inputs/source-scope.md` | Sorting final headings manually |
| Final `###` source-section headings do not match the accepted source-section order | `intermediate/first_pass/03_plans/first-pass-structure-plan.md` | Renaming headings after generation |
| Sections are reordered for conceptual convenience without allowed local dependency adjustment or implementation-chain rationale | `intermediate/first_pass/01_inputs/source-scope.md` and `03_plans/first-pass-structure-plan.md` | Adding a note that the order was “optimized” |
| Within-section knowledge-point order has no source-order, prerequisite, process, or implementation-chain rationale | `intermediate/first_pass/03_plans/first-pass-structure-plan.md` | Claiming local reordering is obvious |

Section order is fixed for ordinary chapters. Within-section order may be adjusted only when `source-scope.md` or `first-pass-structure-plan.md` records a clear rationale.

This gate must not require old first-pass pack sections, learning-item cards, time boxes, progress records, or stage-interface sections in the final student-facing artifact.
