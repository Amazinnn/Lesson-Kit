# C02 — independent read-only review, receive checkpoint correction (WP01)

Scope: LIGHT bounded review of uncommitted worktree diff, not a WP01 acceptance.
Source state reviewed (no edits made by me):

- HEAD `c4995aba`; working tree dirty, nothing staged:
  `workbench/data/course_sync.py` (+85/−19), `workbench/data/pool.py` (+11),
  `pool/scripts/pool_schema.py` (+7), `FILE_CONTRACT.md` (+6), `docs/DATA_MODEL.md` (+6),
  `openspec/changes/expand-file-mediated-course-sync/design.md` (+6),
  `tests/workbench/test_course_sync_receive.py` (+128),
  `tests/workbench/test_course_sync_data.py` (+8/−3). Untracked: `docs/design/.../debug.log`.
- Parent may have edited while I read; line numbers below are from the state I inspected.

## Verified as correct in source (no action)

1. Row unit commit/ack ordering — `apply_exchange` L815-834: rows, `state["row_identities"]`,
   `state["base"][identity]` and `pending_files` all land in one `pool.transaction(immediate=True)`
   via `_checkpoint(connection, state)`. Acknowledgement can no longer be published without the rows.
2. Unit isolation — L815/835-840: `before_state = deepcopy(state)`, `before_index = dict(index)` are
   restored on failure and the identity is added to `failed_identities`, so dependents fail through the
   L808-814 path while independent units still run. (Shallow `dict(index)` is safe: `_identity_index`
   values are `(table, id)` tuples replaced, not mutated.)
3. Read-only overlay — `_state(..., read_only=True)` skips `_complete_pending_files` (L161-162) and
   `_projection` L369-370 overrides the on-disk bytes with the committed pending asset/tombstone after
   `_managed_files`, so `inspect_exchange` (L554) never writes files and never re-plans a committed file.
4. Projection exclusion — `_database_projection` L206 discards `course_sync_checkpoint` before the
   unknown-table check and before table iteration, so it cannot enter assets, inventory or manifests.
5. Sidecar-after-commit failure (L843) leaves the committed checkpoint authoritative; retry dedupes.
6. `_state(pool=None)` default is not a hazard in practice: all production call sites pass `pool`
   (L449, L554, L781) and the new tests pass it too.

## Issues, newest-evidence first

### D1 (high, lineage/identity corruption) — `unassigned` still trusts the sidecar, not the checkpoint
`apply_exchange` L780: `unassigned = not state_path.exists()`, while `_state` L147-163 now returns the
SQLite checkpoint when present and only falls back to `state.json`.

Reproducible scenario:
1. Checkpoint holds `course.origin = "course-A"` but `.lessonkit/course-sync/state.json` is absent —
   reachable when `_save_state` commits `_checkpoint` (L178-179) and the following `_atomic_json`
   (L180) fails on the first export, or when the sidecar is deleted/restored without it.
2. `apply_exchange` a package from a *different* lineage (`origin = "course-B"`).
3. `_state` returns course-A with a non-empty `local` projection, so `_adopt_course_origin`
   L626-629 takes the `unassigned=True` branch and overwrites the local origin with `course-B`
   *without* the "explicit association input is required" error (L630-632).
4. L783 immediately persists the foreign lineage into the recreated sidecar.

Result: two installations claim one course lineage with divergent local rows; the next exchange merges
or duplicates history — the exact failure the checkpoint is supposed to prevent.
Fix: derive `unassigned` from state, e.g. `state["course"].get("origin") is None or not state.get("initialized")`.

### D2 (medium-high, one bad file blocks independent units and is un-recoverable) — file intent commit
`apply_exchange` L823-825 + L841-843, `_complete_pending_files` L183-193.

- `pending_files` and `base[identity]` commit together (L828/L834), so between commit and publication
  the checkpoint both acknowledges and intends. Correct so far, but:
- `_complete_pending_files` is called *outside* the per-unit `try` (L842). A publication failure
  propagates out of `apply_exchange`, so every remaining unit of that inspection is dropped
  (contradicts "one unit never blocks independent ones") and no `applied`/`failed` report is returned.
- On the next operation `_state` L162 re-raises from the same intent, so `inspect`/`export`/`receive`
  for the whole course fail until that single file is writable. A failed *delete* whose parent
  directory is read-only (or where the target became a directory / publishing is permanently denied)
  therefore bricks the course with no abandon path; `inspect_exchange` meanwhile reports the file as
  already applied (overlay, D-verified point 3), so the UI shows it synced.
  Fix (smallest): document/implement an explicit way to abandon a committed intent, and catch the
  publication error per unit so later independent units still apply.

### D3 (medium, dead pre-commit publication path) — `_write_unit` still writes files
`_write_unit` L1074-1076 calls `_write_file` directly for `kind == "file"` inside the caller's SQLite
transaction. Unreachable from `apply_exchange` today only because L823 intercepts file changes; any
future call site (or a file asset reached through another branch) publishes bytes before the checkpoint
commits, reintroducing the defect this correction removes. Delete the branch (raise instead) or route it
through the pending intent.

### D4 (medium, acknowledgement without write / contradictory report) — grouped execution items
L829-833 acks `state["base"]` for **every** `supported` `execution_item` of an applied header, while
`_execution_units` L872 only includes items whose `asset["content"]` is truthy.
- An item without `content` is acknowledged and never written → permanently skipped, never retried.
  Conditional on `read_exchange` not requiring content for `execution_item` (I could not verify within
  the tool budget).
- An item that `_dependency_order` blocked is written as part of the header record but is also reported
  in `failed` as `invalid_dependency` while base marks it acknowledged; a retry then plans nothing, so the
  reported failure never resolves.
Fix: ack only `executions[identity]` (the assets actually passed to `_write_execution`), and drop blocked
items from that grouping or keep them out of `failed`.

### D5 (low-medium, schema ownership / packaging) — pool schema now depends on the wheel
`pool/scripts/pool_schema.py` L63-66 imports `workbench.data.pool.ensure_course_sync_schema` at call
time and `ensure_workbench_schema` L617 runs it. `pipeline/scripts/create-tables.py` L31/L247 calls
`ensure_workbench_schema`, so *pool creation* now hard-depends on an importable `workbench` (fails
with ImportError if the app is not installed, e.g. a bare pool/pipeline checkout), and the DDL is owned
by the wheel while pool delegates — the inverse of the rule that pool-side schema lives in
`pool_schema.ensure_*`. Also every newly created or migrated pool DB carries a *device-local* transport
table, so a pool copied by hand carries another installation's checkpoint, which `_state` now prefers
over the sidecar. Either keep the DDL in pool_schema and have the wheel not need it, or document that
pool creation requires workbench (and that hand-copied pools carry a checkpoint).

## Verification limitations

- No test suites and no fixture probes were run (brief: LIGHT, ≤20 calls); D1-D5 are source-reading
  findings, not executed reproductions. D1 and D2 have cheap fixtures available in
  `tests/workbench/test_course_sync_receive.py` (`pair`, `publish`, `receive`) if the parent wants
  confirmation before editing.
- Did not verify `read_exchange` validation of `execution_item.content` (D4 reachability) or
  `figure_mirror._workspace_source` key form for pending figure deletes
  (`_managed_files` L331 / L344 compare pending keys against `".lessonkit/figures/" + logical` and the
  config `managed_paths` string; a key-form mismatch would raise `missing referenced figure` /
  `missing managed course path` for an already-published delete — worth one cheap probe).
- Not reviewed: `_execution_projection`/`_retire_execution` semantics, journal/`paper_progress.flush_files`
  ordering, performance of per-unit `deepcopy(state)` (scales with base size; out of scope per brief).
- I do not claim WP01 acceptance: the crash matrix for file publication, grouped execution acks, and
  lineage adoption is not covered by the new tests, and D1/D2 are exactly the untested fault windows.
