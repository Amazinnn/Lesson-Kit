<!-- Intermediate path convention: intermediate/{course}-{ch}/{view}/{layer}/ -->

# Gate: No Summary Substitution

Use this gate before exporting any source-guided first-pass lesson.

| Failure | Return to | Forbidden repair |
|---|---|---|
| Final artifact can be read without returning to source material | `03_plans/structure-plan.md` | Removing a few details while preserving self-contained summary structure |
| Knowledge point cards explain source content as a substitute for reading | SQLite pool (knowledge_points table) and final artifact | Renaming explanations as reading guides |
| Short explanations omit source locator or reading task | SQLite pool (knowledge_points table) | Adding source locator only at section level |
| Checkpoint questions ask for memorized final prose instead of source-grounded understanding | SQLite pool (knowledge_points table) and `04_checks/coverage-check.md` | Adding generic "why" questions |

Pass only when the final artifact pushes the student back to source material for full understanding.
