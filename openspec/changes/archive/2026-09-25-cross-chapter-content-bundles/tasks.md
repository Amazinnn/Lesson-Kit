# Tasks

## 1. Confirm contracts

- [x] 1.1 Read this proposal, design, and both spec deltas; inspect the current worktree and preserve other Agents' changes.
- [x] 1.2 Keep the change additive: a bundle-level `chapter`, a single-batch result, and every stored row keep working unchanged.

## 2. Item chapters in the bundle gate

- [x] 2.1 Failing tests: an item's own chapter wins, the bundle chapter is the default, a chapterless item is refused with its label, and a bad chapter value is refused.
- [x] 2.2 Resolve a chapter per item and derive ids, figure logical paths, and the duplicate check from it.
- [x] 2.3 Report the chapters in the gate result so the apply step can group by them.

## 3. One batch per chapter

- [x] 3.1 Failing tests: a two-chapter bundle records two batches with their own counts and snapshots, keeps one backup, and stays all-or-nothing.
- [x] 3.2 Group the plans by chapter, allocate one batch id per group in chapter order, write each group's snapshot and figures root, and stamp each row with its own batch id.
- [x] 3.3 Keep the legacy single-batch fields in the result when only one chapter is present, and add `batches` for every case.
- [x] 3.4 Roll one chapter back while its sibling stays, on the existing rollback entry points.

## 4. Every content block of a reply

- [x] 4.1 Failing tests: two content blocks both land, an intent-gated block keeps its single-match rule, and a failing block leaves the other applied.
- [x] 4.2 Return the recognised content actions as a list, apply each in order, and record `actions` in the turn and the mirror while `action` stays the single element.
- [x] 4.3 Carry every batch into the next turn's provider context and the disclosure path.

## 5. Result cards

- [x] 5.1 Failing UI test: a card with two batches renders one row per batch, each with its own rollback, and reopen marks only the rolled-back row.
- [x] 5.2 Render the batch rows from `result.batches`, falling back to the legacy single-batch card, and keep the rollback call per batch id.

## 6. Teacher contract

- [x] 6.1 State that one manifest may span chapters, that each item declares its chapter, that ids and figures follow the item's chapter, and that one batch is recorded per chapter.
- [x] 6.2 State that every content block in one reply is applied, so the agent should keep going through all requested chapters in one answer.

## 7. Documents

- [x] 7.1 GLOSSARY (batch per chapter, item chapter), PRODUCT-MANUAL (one turn imports several chapters; rollback per chapter).
- [x] 7.2 ARCHITECTURE, ACTION-GRAPH (entry + L0–L4), REQUIREMENTS, L0/L1 registrations.

## 8. Verification and handoff

- [x] 8.1 Isolated end-to-end on a pool copy: a two-chapter bundle through the bridge path, figures in their own chapter directories, rollback of one chapter leaving the other, and a legacy single-chapter manifest still producing one batch.
- [x] 8.2 Full Python and Node checks, `compileall`, OpenSpec strict plus this change, `doctor`, and the workspace guards.
- [x] 8.3 Read-only check that the real learning pool is untouched; record outcomes and remaining limits.

## What changed

- `workbench/ingest/__init__.py`:
  - `_item_chapter` resolves an item's chapter (item → bundle → workspace lens) and
    refuses an item that cannot name one, naming its label; the bundle-level chapter
    is now a default instead of a requirement.
  - Every derived value follows the item chapter: the allocated id prefix, the
    figure's logical path and destination directory, the micro-quiz id, and the
    duplicate check. An explicitly named id must now carry the same chapter, so a
    chapter-14 id can no longer sit in a chapter-12 bundle and drop its figures in
    the wrong directory.
  - `_apply_content_bundle` groups the plans by chapter, allocates one batch id per
    chapter in chapter order, writes one manifest snapshot per batch with that
    chapter's `_applied` bookkeeping, stamps each row with its own batch id, creates
    only the figure directories a chapter actually needs, and reports
    `batches: [{batch_id, chapter, counts, origins}]`. A single-chapter bundle keeps
    the legacy `batch_id`/`counts`/`origins` fields as well.
  - `_has_column` extracted from `_has_exam_year`; rollback only rewrites
    `related_kp_ids` when the pool has that column, so a pool predating it no longer
    crashes the undo.
- `workbench/bridge/conversations.py`:
  - `_extract_action` returns `(answer, content actions, notice)` — every content
    block, in order, plus at most one intent-gated action or contract error.
  - `_store_answer` applies each content action through `_apply_content_action`
    (id `check-ingest`, `check-ingest-2`, …), which gives every action its own
    recovery copy — the ingest layer refuses to clobber an existing backup, so a
    shared name made the second action of a turn fail with
    `recoverable copy already exists` (caught by the isolated acceptance).
  - The turn and the mirror carry `actions`; `action` stays the single element when
    exactly one was applied, and the next-turn context summarises every batch or
    every rejection.
- `workbench/server/static/workbench.js` + `workbench.css`: a bundle that spans
  chapters renders one card with a row per batch (batch id, chapter, counts) and its
  own rollback button; reopening marks only the rolled-back row. A single batch keeps
  the existing card, and the restore path renders `message.actions`.
- Prompt: one manifest may span chapters, each item declares its chapter, ids and
  figures follow it, one batch is recorded per chapter, and every block of a reply is
  applied — so the agent finishes all requested chapters in one answer.
- Docs: GLOSSARY (content-bundle action and batch id), PRODUCT-MANUAL (one turn,
  several chapters; rollback per chapter), ARCHITECTURE, ACTION-GRAPH (entry + L0–L3),
  REQUIREMENTS.

## Evidence (2026-09-25)

Repository checks on the working tree: pytest **630** (621 before this change; +9 new
tests), Node **116** (+1), `compileall` exit 0, `openspec validate --specs --strict`
**11 passed**, `openspec validate cross-chapter-content-bundles --strict` valid,
`doctor` all checks passed, `guard extract-problems` PASS, `guard problem-set` PASS.

New coverage: `test_content_bundle.py` (+6) — a two-chapter bundle allocates
chapter-scoped ids for both chapters, records two batches, lands each chapter's
figures in its own directory, drops an item that cannot name a chapter, rejects a bad
chapter value, rejects an explicitly named id from another chapter with both chapters
named, and rolls one batch back while its sibling survives; a single-chapter bundle
keeps the legacy result. `test_conversations.py` (+3) — two content blocks in one
reply are both applied and recorded as `actions`, one failing block leaves the other
applied, and two *real* actions in one turn keep their own recovery copies (the
regression test for the shared-backup bug). `workbench_ui_interactions.test.js` (+1)
— a two-batch card renders one row per batch, marks only the rolled-back row, and
rolls back the batch the row belongs to.

Isolated acceptance (`%TEMP%/lk-bundle`, a **copy** of the real `c01.db`, stubbed
provider command so the whole `_store_answer` path runs with `ingest.apply_batch`
unmocked):

- One reply carrying two content blocks (ch12 and ch13) → **both applied** in order:
  `c01-ch12-prob-026` stamped `batch-011`, `c01-ch13-prob-025` stamped `batch-012`,
  each batch registered with its own counts, `exam_year` recorded, and each chapter's
  figure copied into `figures/c01/<chapter>/`. Two recovery copies exist, one per
  action.
- Rolling back `batch-012` removed exactly the chapter-13 row and its figure; the
  chapter-12 row, its figure, and `batch-011` were untouched, and the registry showed
  one batch rolled back and one still applied.
- A legacy single-chapter manifest still returns `batch_id`, `counts`, and `origins`
  (plus `batches`), i.e. existing consumers keep working.
- The real pool was read-only throughout: 111 problems across ch12–ch16, 0 attempts,
  0 feedback events, 10 batches (its own imports from today), no acceptance marker in
  it, mtime unchanged by this work.

## Remaining limits

- A bundle still commits as **one transaction behind one backup**: per-chapter
  granularity applies to batches and rollback, not to the commit. Rolling back one
  chapter keeps the import's other batches and their rows; the pool-level backup
  remains the whole-import recovery point.
- The legacy patch channels (`micro-quiz-patch`, `flash-card-patch`) still record a
  single batch per apply. Their ids are explicit, so they already accept several
  chapters; they are documented as the compatibility path.
- A chapter's ids are not reserved after a rollback: re-importing that chapter
  continues from the pool's current maximum, so the same content can get a different
  number than the rolled-back batch used.
- Only the first intent-gated block per reply is honoured (practice selection, goal
  form); content blocks have no such limit.
