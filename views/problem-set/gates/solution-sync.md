# Gate: Solution Sync

Pass only if the solution file mirrors the problem-set numbering exactly.

Fail when:

| Failure | Return to | Forbidden Repair |
|---|---|---|
| A selected problem has no matching solution entry | solution render step | Dropping the problem silently |
| The solution file contains an extra unselected entry | solution render step | Leaving orphan answers for convenience |
| Missing solution is not marked `待补` | solution render step | Leaving the entry blank |
| Solution text appears in the problem-set file | problem-set render step | Hiding it with formatting |

Missing `solution` values are warnings, not blockers, when they are explicitly
marked pending.
