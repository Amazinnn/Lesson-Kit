# C03 — independent read-only review, normalized checkpoint + isolated file publication

LIGHT bounded review. No source/test/doc edits, no commits, no full suite, no pool/workspace writes.
One isolated probe was executed (pure helpers + in-memory SQLite only).
Files inspected: `workbench/data/course_sync.py` (1372 lines), `workbench/data/pool.py`
(`ensure_course_sync_schema` L449-454), `pool/scripts/pool_schema.py` (L63-68, L611-624),
`workbench/domain/course_sync.py` (planner/`_valid`), `tests/workbench/test_course_sync_receive.py`
(read L440-612 in full; test names read for the rest of the file). Parent/sibling edits may have
landed while I read; line numbers are from the state I inspected.

Verdict: the three claimed corrections are real. Normalization, pending resumption and compaction
are structurally sound, and I found **three new defects** plus **two residuals** in D1/D4. Nothing
here is data-destroying-by-construction except N2/N4 (execution rebuild from a stale inspection).

## Dispositions of C02 D1-D5

| id | disposition | evidence |
|---|---|---|
| D1 lineage | **fixed** (+1 residual) | `apply_exchange` L815 now `unassigned = (not state_path.exists() and not _table_exists(pool.connect(), "course_sync_checkpoint"))`; origin then comes from `_state` (checkpoint preferred, L149-153) via `_adopt_course_origin` L655-667, and `inspect_exchange` L610 uses the same checkpoint-derived origin. C02's counterexample (checkpoint present, sidecar deleted, foreign package) now raises `different course lineage`. Test `test_missing_sidecar_does_not_reset_a_committed_course_lineage` L577-587 covers it. |
| D2 file isolation | **fixed** | `_complete_pending_files` L204-224 never raises; failures are returned, retained in `state["pending_files"]` and in `course_sync_units.pending_json`. `apply_exchange` L819-831 folds the pre-pass into `failed`; per-unit publication L889-895 reports `publication_pending`, marks the identity failed and continues. `export_course` L481/L523 turns the same failures into `cleanup_errors`/`partial`. `_state` L159-167 no longer re-raises on a committed intent, so a dead target no longer bricks the course. Tests L513-555, L590-612. |
| D3 pre-commit file write | **fixed** | `_write_unit` L1125-1128 raises `unsupported asset kind` for non-row kinds; the only publication paths are `_file_payload` L1253 (validation, no write) and `_write_file`, called from `_write_readable_files` and `_complete_pending_files` outside any SQLite transaction. |
| D4 grouped execution acks | **partly fixed** | Blocked-item contradiction is gone: `invalid_headers` L825-827 blocks the header itself, so nothing is written and the failure is reported once. But the ack set is still built from `ordered` (L873-877), not from `executions[identity]` — see residual D4a. |
| D5 pool schema ownership | **fixed** | `pool/scripts/pool_schema.py` L63-68 owns standalone `ensure_course_sync_schema` (only `re`/`sqlite3`/`warnings`/`typing` imports) and `ensure_workbench_schema` L624 delegates to it; no `workbench` import. `workbench/data/pool.py` L449-454 keeps a second copy — see residual D5a. |

## New defects

### N1 (medium, silent abort of the whole inspection) — unvalidated `execution_item.content["position"]` escapes the per-unit try
`_execution_units` L916-937 runs at L824, **outside** the per-unit `try` at L861, and indexes
`asset["content"]["position"]` (L927). `read_exchange` L1316-1333 validates row and file payloads but
only requires `execution`/`execution_item` content to be a dict, so an envelope
`{"kind":"execution_item","content":{"paper_id":"p1"},"depends_on":["execution/e1"]}` reaches
`_execution_units` and raises `KeyError: 'position'`.
Probe (executed): `_execution_units([header, that_change], {})` → `KeyError 'position'`.
Effect: the exception leaves `apply_exchange` after `_save_state` (L818) has already persisted
origin/adoption and after the pending-file pre-pass has published files, with no `applied`/`failed`
report at all — the exact "one unit blocks independent ones" invariant restored by D2, broken from a
different angle. Any local content change committed in the same call is kept, but the caller sees a
traceback and the plan is unrecoverable without hand-editing the package.
Fix (smallest): move `_execution_units` inside a try that converts the failure into
`failed=[{"code":"invalid_asset"}]` for the offending identities, or validate `position` (int, and
`content` or `deleted` consistency) in `read_exchange` L1316-1333.

### N2 (medium, local data loss) — an execution is rebuilt from `inspect_exchange`'s stale `local`, wiping items created between inspect and apply
`_execution_units` L928-936 merges the *inspection-time* `local_assets` (= `inspection["local"]`,
L822) for every `execution_item`; `_write_execution` L949-950 rebuilds the record from that merged
set, and `_write_active` L1065 does `DELETE FROM active_practice_items` before re-inserting, while
`_write_checkpoint` L1107 replaces `paper_state.checkpoint_json` wholesale.
Counterexample: `inspect_exchange` → user answers questions / a draft autosaves into
`active_practice_items` (or a new parked `paper_state.checkpoint_json` item is created) → `apply_exchange`
of the inspected plan whose peer changed only the header (e.g. `cursor`/`progress`) or one item →
items written after the inspection are deleted, and the header commit acks it as received.
The apply path never re-reads `active_practice_items`/`paper_state.checkpoint_json`; it trusts the
inspection snapshot. Test `test_an_active_execution_is_rebuilt_with_its_drafts` L258+ cannot catch
this because it never mutates between inspect and apply.
Fix: re-read the item set at apply time (inside the unit transaction) for the header being rebuilt,
and merge inspection items only for positions absent locally.

### N3 (low-medium, intent loss) — `pending_json` is one slot per identity while `pending_files` is a list per change
`_unit_checkpoint` L185-195 stores exactly one intent per identity (and L187 selects it by
`pending["identity"] == identity`); `state["pending_files"]` may hold several entries for one
identity. Reachable path: identity X already has an unpublished intent from an earlier receive
(L819 attempts it, fails, keeps it in `state["pending_files"]`), the peer then edits the *same* file
and the new change for X is applied in the same call (L889-891 appends a second entry, no
deduplication).
`_complete_pending_files` L218-219 clears `course_sync_units.pending_json` after **each** successful
write for that identity, so old-writes-ok + new-writes-fail clears the durable slot while leaving
only the in-memory/sidecar entry. The next `_state` sees no pending in the units table, and
`_checkpoint` L177 never stores `pending_files`, so the newer intent disappears: disk holds the old
bytes, `state["base"]` acks the new content (L888 commits the ack before publication). The next
inspection then reports `baseline_mismatch` (L637) or replans a phantom local edit, and the peer's
content is never applied — silently, since nothing reports a dropped intent.
Fix: refuse a second intent for an identity that already has one, or key the intent by
`(identity, hash(content))`, or compare `state["pending_files"]` against the units table after
publication and fail loudly on divergence.

## Residuals in the "fixed" items

### D4a (low, ack without write) — items excluded from grouping are still acknowledged
`_execution_units` L925 skips `execution_item` changes whose `content` is falsy; the ack loop L873-877
adds **every** ordered item of the applied header, without the same condition.
Probe (executed): header + `{"kind":"execution_item","deleted":true}` (no `content`) →
`grouped positions {'execution/e1': [0]}` while the tombstone is in `ordered`.
So the tombstone is (a) never written, silently skipped by L841-849, (b) acknowledged into
`state["base"]`/`course_sync_units`, (c) absent from both `applied` and `failed`. A retry plans
nothing (local overlay/base now agree), so the sender's item deletion is lost and reported as success.
`read_exchange` L1316-1319 admits content-less deleted assets, and `domain/course_sync.py` `_valid`
L28 admits them too, so a hand-edited or third-party package reaches it. Export never produces this
shape (`_execution_projection` L467-473 keeps `content` in tombstones), which is why no test catches it.
Fix: filter the ack loop with the same predicate as L925, and report the skipped identity in `failed`.

### D1a (low, false lineage rejection) — table presence is used as a proxy for a recorded lineage
`unassigned` L815 tests `_table_exists(...)`, not "a checkpoint row exists". Since D5's fix,
`create-tables.py`/`ensure_workbench_schema` creates an **empty** `course_sync_checkpoint` for every
new pool. Probe (executed): after `ensure_course_sync_schema`, `_table_exists == True` and
`row_present == 0`.
Counterexample: a course DB created/migrated by `create-tables.py`, seeded with rows, never received
anything, sidecar absent (fresh clone, `state.json` not tracked) → `unassigned=False` → a package from
a peer installation raises `the package belongs to a different course lineage; explicit association
input is required` even though this installation never recorded a lineage, and the first receive is
the one case where adoption should be automatic. Safe (refuses rather than corrupts), but a
user-visible false rejection of the unassigned path.
Fix: `SELECT 1 FROM course_sync_checkpoint WHERE singleton=1` instead of `_table_exists`, and make
`_state` able to distinguish "no checkpoint row and no sidecar" (L170) from "state recorded".

### D5a (low, drift risk) — the same DDL now exists twice with no test tying them together
`pool/scripts/pool_schema.py` L63-68 and `workbench/data/pool.py` L449-454 declare
`course_sync_checkpoint`/`course_sync_units` independently. A migration added to one side (e.g. an
index or a NOT NULL) will not reach the other; nothing in the suite compares them. Cheap guard: assert
both `sqlite_master` shapes match in one test, or have the wheel import the pool-side helper under a
guarded `try` (which is what D5 was meant to avoid — so the test is the better fix).

## Confirmed-correct areas (no action)

1. **Commit/ack ordering** — every unit's rows, `row_identities` delta, `base` ack and file intent land
   in one `pool.transaction(immediate=True)` via `_unit_checkpoint` (L185-195, L862-880). `index`
   rollback L883 restores identity lookups.
2. **Compaction is safe by ordering** — `_checkpoint` L175-182 writes the merged snapshot and prunes
   `pending_json IS NULL` rows in the same transaction; `_save_state` at the start of
   `apply_exchange` (L818) always runs *before* new unit rows are written, and each `_state`
   (L159-167) reconstructs base/mappings from surviving unit rows first, so the prune never deletes
   the only copy of an acknowledgement. Unit rows always win over the checkpoint, and I could not
   construct a case where the checkpoint holds a *newer* value than a surviving unit row.
3. **Pending overlay and resumption** — `_projection` L391-401 overlays committed intents over disk
   bytes (so inspection/export agree without writing), and `_managed_files` L336-388 suppresses the
   missing-file errors for exactly the same key form (`path` relative posix) for goals, figures
   (`.lessonkit/figures/<logical>`) and `managed_paths`, so a pending create/delete neither raises nor
   re-plans. C02's open figure-key question: the key forms match; I found no mismatch.
4. **Identity mapping** — `_portable_integer_references` L307-333 registers
   `table/[local key] -> portable identity` and rewrites PK-bearing references; `_identity_index`
   L722-735 reads them back; `_write_unit` L1164-1172 registers the new local id after insert. A
   row's portable identity is generated once (L263-264) and reused across receives.
5. **Read-only inspection** — `inspect_exchange` L586-591 uses `read_only=True` (no `_installation_origin`
   write, no publication) and reports `publication_pending` for committed intents.

## Reporting/limitation notes (not defects, worth knowing)

- `applied` and `failed` mix units of the current inspection with long-lived intents: a permanently
  unwritable file makes **every** later receive `status="partial"` with a `publication_pending` entry
  for an identity the current package never mentioned (asserted by test L590-612). There is no
  abandon/resolve path, so the UI can never reach `success` for that course; the entry is honest but
  not attributable to the current exchange.
- `applied` lists only header identities; execution items written with their header are acked but never
  appear in `applied`, so `local.applied` undercounts for practice runs.
- A single `execution_item` whose dependency is missing from the package rejects the whole run
  (`invalid_headers` L825-827): a parked/active execution can never be received partially, and every
  retry reports the same `invalid_dependency` for the header and its items.
- `apply_exchange` never re-validates `inspection`'s `plan`/`local` against the DB at apply time (same
  root cause as N2); `_side_choices`/`_dependency_order` operate on the snapshot.
- `_atomic_json(state_path, state)` L900 is outside any transaction and outside try: an `OSError`
  there aborts the call after all units committed and after `paper_progress.flush_files` (L899), so the
  caller sees an exception for an applied receive (`test_committed_history_survives_sidecar_failure…`
  L499 encodes this as expected). Sidecar content is then only as fresh as the last successful write,
  though the checkpoint/units remain authoritative.

## Verification limitations

- No pytest runs (brief: LIGHT, no full suite). Evidence is source reading plus three executed probes:
  `_execution_units` grouping of a content-less item, `KeyError` on missing `position`,
  `_table_exists`/row count for an empty checkpoint table, plus `_dependency_order` and
  `_identity_key` sanity output. N2 and N3 are argued from code paths, not reproduced; both have cheap
  fixtures (`pair`, `publish`, `receive`, `monkeypatch` in `tests/workbench/test_course_sync_receive.py`).
- Not reviewed: scheduling/CLI wiring, `_write_readable_files` conflict semantics, `paper_progress`
  flush ordering beyond the call site, per-unit `deepcopy(state)`/full-snapshot cost (out of scope).
- This is not package acceptance: the crash matrix for N1-N3 and the D4a ack filter is untested.
