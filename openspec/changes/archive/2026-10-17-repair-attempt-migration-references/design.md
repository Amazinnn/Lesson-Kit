## Context

SQLite updates referencing foreign-key declarations when a parent table is renamed. The existing answered-status migration renames `problem_attempts`, copies to a new table and drops the temporary parent. A child can continue referencing the dropped temporary name even though all parent rows were copied. Live CO additionally has missing attempts, which is a separate data-integrity problem.

## Decisions

- Keep repair in the existing incremental schema migration authority. Enumerate actual inbound foreign keys and preserve each referencing table's rows, columns, constraints, indexes and triggers; handle SQLite rename/FK settings deliberately with transaction boundaries understood rather than toggling foreign_keys inside an ineffective transaction.
- For healthy old schemas, preserve IDs and all pre/post row values except the intended status-check extension; external references must target `problem_attempts`, never a temporary name. Re-running migration is a no-op.
- Detect already-misbound referencing tables even when the parent status CHECK is already widened. Repair declarations without discarding child data. Do not limit inspection to a single hard-coded child if the actual schema has additional inbound references.
- A healthy isolated fixture must pass `PRAGMA foreign_key_check`. A damaged fixture whose parent rows are missing must retain all surviving data and report those unresolved rows explicitly; repairing the table name does not authorize fabricating attempts, deleting child markers or declaring integrity restored.
- Test both foreign_keys enabled/disabled entry states, relevant legacy column shapes, nonempty child tables and reruns. Restore caller settings as documented; do not commit unrelated caller transactions or silently clear data.

## Real-data boundary

Before any operator executes real-pool repair: obtain explicit authorization, verify a recoverable backup, run on an isolated copy, compare every affected row and nontarget schema object, and report remaining violations. Existing CO checkpoints reference nonexistent question/attempt rows; this change alone cannot make their historical data reappear.

## Handoff

Implement with focused meaningful regression tests, then independent full-suite/isolated acceptance. Reconcile the schema duty in DATA_MODEL/Architecture, affected manual commands and owning live OpenSpec in the same PR. The planning pass's in-memory reproduction is defect evidence, not product-fix acceptance.
