## Why

PR #106 retired problem topic grouping and new `topic_label` inputs, but its
ordinary schema ensure also drops the column. Read-only inspection on
2026-10-09 found populated historical values in four registered course pools.
The user explicitly requires care with existing course data. Logical retirement
must not silently erase that data during ordinary use.

## What Changes

- Preserve an existing problem `topic_label` column and its values during normal
  schema ensures, including compatible table rebuilds.
- Keep the retired field out of new problem inputs, search and UI; flash-card
  labels retain their existing contract.
- Defer destructive removal to a separately specified explicit migration.
- Validate on temporary databases and real-pool copies only; do not migrate or
  write any actual course pool in this delivery.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-content-governance`: historical retired problem-label retention.

## Impact

The narrow existing `pool_schema.ensure_workbench_schema` step stops dropping
data; no new schema, command, user operation or dependency. This preserves
stored user data while keeping the approved feature retirement. Future removal
and broader schema doctrine remain deferred. Default pending a different user
choice is retention; no destructive authorization is inferred.
