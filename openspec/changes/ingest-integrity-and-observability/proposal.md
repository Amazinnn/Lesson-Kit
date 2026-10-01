## Why

Two course-ingest jobs ran to completion in the last four days — `ncmc`
(全国大学生数学竞赛, 17 papers 2009–2025 plus a textbook, 8 chapters) and `c04`
(宏观经济学（甲）, 8 textbook chapters plus 16 past-paper batches). Both
finished. Neither could report whether it had lost anything, and in `c04`'s case
it had.

**A problem id now denotes a different question.** `c04` lost 37 problems to a
concurrent dedup and rebuilt its manifests from the surviving shard specs.
Problem ids are minted by a positional counter, so a rebuild re-mints them from
position rather than from identity. A 974-row pre-deletion snapshot of the pool
exists in `pool/backups/`; diffing it against the live pool on `problem_id` and
comparing question text gives 37 deleted, 0 added, and **425 of the 937 surviving
ids now holding a different question** — 512 unchanged. For example
`c04-ch01-prob-204` was 「新古典增长模型中储蓄率变化的影响。」 and is now
「用数理方法和几何方法推导BP曲线…」. `problem_attempts`, `problem_progress` and
`review_schedule` all key on the same strings. `c04` has no learning records
yet; the same sequence on a course that has been practised attaches history to
the wrong questions.

**The ledger that should have caught it was a constant.** All eight per-batch
ingest logs in `c04` report byte-identical accounting (kp 324 / problems 937 /
relations 0) — including a problems count of 937 recorded while the pool held
974 rows at apply time. Every batch wrote its backup to the same file, so the
sixteen snapshots collapsed into one, and that file is gone. `ingest_batch_id`
is NULL on 937/937 problems and 324/324 knowledge points across 16 ledger
batches.

Two of these are already **violations of requirements this repository
carries**: `workbench-content-governance` requires that "every inserted row
carries the batch id" (`openspec/specs/workbench-content-governance/spec.md:163`,
scenario at `:167-168`), which 100% NULL `ingest_batch_id` violates. `workbench-ui`
already requires that every surface rendering a problem field as rich text
"SHALL run the same math pipeline over it" and be "escaped-then-rendered, never
injected raw" (`openspec/specs/workbench-ui/spec.md:1077-1083,1090-1093`) — which
the server renderer violates today by escaping the math expression twice
(`workbench/server/pages.py:796` then `:816-820`) while the client renderer
escapes once and renders correctly (`workbench/server/static/workbench.js:311,340-345`).
The promise exists; the implementation does not keep it.

The cost is not only the bugs. `ncmc` wrote 796 Python files under its `_work/kb`
tree and `c04` wrote 22 repair scripts (~92 KB) to work around missing capabilities:
no stable ids, no
manifest builder, no read-only problem query, no formula validator, no
cross-reference gate, no dry run, no per-batch backup, no graph verification
against the database, no documented manifest schema. `FILE_CONTRACT.md` does not
mention `source_location`, `related_kp_ids`, `fragile` or `graph_label` at all,
so those contracts are only recoverable by reading insert-script line numbers.

The full ledger, with a `file:line` or a reproducible query behind every row,
is in `design.md`. This change records it so the fixes can be scheduled
deliberately instead of rediscovered per course.

## What Changes

- **Record, do not fix.** This change adds no code and changes no behaviour. It
  is a defect register with each item labelled by the route its fix must take:
  - `CONFORMANCE` — a requirement already exists and the implementation
    violates it. Cheapest to fix and highest priority: the contract is not in
    question.
  - `NEW-GAP` — no requirement exists; a follow-up change must author one.
  - `DOCTRINE` — cannot be fixed without a decision this repository has
    deliberately deferred. All four sit in `pipeline/`, whose behaviour contract
    `AGENTS.md:38-39` forbids modifying, and which
    `openspec/changes/archive/2026-09-20-optional-problem-difficulty-gate/specs/workbench-content-governance/spec.md:13-14`
    already carves out of scope.
  - `NOT-A-DEFECT` — behaviour that looks wrong but is what the spec requires.
    Recorded so a later reader does not "fix" it.
- **Record one behaviour that must not be changed.** The empty
  `knowledge_relations` table and the discarded edge direction are mandated by
  `openspec/specs/review-workbench/spec.md:347-348,355-358`. The first sweep
  reported them as defects; they are not, and an earlier draft of this change
  would have proposed breaking a live requirement.
- **Record one refuted hypothesis.** The `c04` sweep was asked to confirm that
  ch05–ch08 knowledge points were tagged after problem extraction, leaving them
  referenced by zero problems. The pool shows all eight chapters non-zero, zero
  dangling references, and the vocabulary frozen before the problems landed. The
  incident did not happen; the absence of a gate that would have caught it
  either way did. `design.md` keeps the refutation so the next sweep does not
  re-open it.
- **`tasks.md` is the queue.** Each task names its route and the capability that
  owns it, so the register converts into scheduled work without re-deriving
  ownership.
- **No schema change, no migration, no data write.** Nothing in either pool is
  modified by this change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None, and `skip_specs: true` is declared in `.openspec.yaml`. A register of
defects changes no requirement. The `CONFORMANCE` items need no new requirement
— one already exists and is being violated. The `NEW-GAP` items would each need
a requirement, but writing those requirements is scope this change deliberately
does not take on: `content-dedup-and-audit` is already scope-locked to content
identity dedup, the read-only content audit, patch parity and stem-bound
removal, and appending defects across six capabilities would make its spec
deltas incoherent and collide with its own "length is not an answering-form
property" doctrine (`openspec/changes/content-dedup-and-audit/design.md:126-138`,
D9). The `DOCTRINE` items cannot get a
requirement before the layering decision is made.

Ownership, for whoever picks the work up:

| route | items | owning capability |
|---|---|---|
| `CONFORMANCE` | `ingest_batch_id` NULL, double escape | `workbench-content-governance`, `workbench-ui` |
| `NEW-GAP` | stable ids, KP cross-reference gate, apply-time accounting cross-check, difficulty coverage, manifest schema, backup per batch, per-batch provenance for KP ingest, graph label/search/filter semantics, `source_location` schema, no read-only problem query, no dry run | `workbench-content-governance`, `problem-difficulty`, `knowledge-figures` |
| `DOCTRINE` | `--upsert` column reset (both paths), non-strict exit code, collapsed-subpart false positive | none — `pipeline/` is frozen |
| `NOT-A-DEFECT` | empty `knowledge_relations`, direction discarded | `review-workbench` (already correct) |

## Impact

- **Code**: none. This change adds five files under
  `openspec/changes/ingest-integrity-and-observability/`.
- **Data**: none. No pool is read at apply time; the queries in `design.md` are
  read-only and were run in `mode=ro` against the two *course* pools — the `ncmc`
  and `c04` workspaces each carry their own `pool/<course>.db`. The repository's
  own `pool/` directory is a different set of files and is not what the
  reproduction block refers to.
- **Docs**: none. No requirement, no `PRODUCT-MANUAL.md` chapter and no
  `ACTION-GRAPH.md` entry is touched, because no behaviour changes.
- **Tests**: none.
- **Compatibility**: none.
- **Follow-ups**: four `NEW-GAP` groups will each want a change of their own once
  the `DOCTRINE` decision on `pipeline/` is made. The `CONFORMANCE` items can be
  fixed first and independently — they are bugs against requirements the
  repository already carries.
