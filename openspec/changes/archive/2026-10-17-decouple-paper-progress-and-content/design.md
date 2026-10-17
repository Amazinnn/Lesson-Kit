## Context

Current Papers are JSON records keyed by `ps-NNN`; unfinished progress is a single SQLite workspace record with a copied ordered item list. Learning evidence is separate. This design retains those responsibilities and adds per-Paper resumability rather than storing attempts inside Paper JSON. See the dated investigation for the current 70/22-item mismatch and missing attempt evidence.

## Goals / Non-Goals

**Goals:** independent Paper/question identity; independently resumable Papers; precise invalidation; preservation of genuine learning evidence; correct mixed-item controls.

**Non-Goals:** a new ingestion system, fuzzy deduplication, a full Paper editor redesign, automatic repair of the existing CO data, or recreating missing attempts from completion markers.

## Decisions

1. **Persist progress per Paper, select one separately.** Extend the existing Data execution model with a stable per-workspace Paper association. At most one unfinished execution per Paper; any number of Papers may remain unfinished. The active singleton becomes the selected execution boundary, not the sole place where resumable progress lives. Switching persists cursor, states and unsubmitted answer/choice drafts, then selects the target without abandoning the source. Completion creates one immutable history record; an explicit new attempt starts a fresh execution. A resumed attempt keeps its original rating preference; current settings apply to new attempts.
2. **Keep learning evidence independent.** Checkpoint `attempt_id` associations can be detached when resetting an item; the attempt, feedback, schedule and learning evidence are not deleted or retroactively regraded. Finished historical runs are never rewritten to match a later Paper or question edit. Historical display must clearly distinguish old evidence from current content.
3. **Coordinate through Data-owned operations.** Reuse the managed Paper store and the existing question patch planner. UI/API/CLI must not implement their own reset or cascade SQL. Use explicit existing IDs for updates; title, question text and type/prefix are not identity matching heuristics. Correcting `prob-*` to choice/judgment must not rename it to `mq-*`.
4. **Separate update classes.** Manual membership/order changes retain Paper ID but reset only its unfinished execution after an impact preview and explicit confirmation; cancelling is zero-write. Title/description changes preserve progress. Effective no-op edits have no reset effect. Question semantic comparison covers stem/embedded content, option identifiers/text/order, answer key and answering type; only those changes reset that item and its draft in unfinished Papers. Solution/title/KP/difficulty/source-only edits do not. Reset does not alter Paper membership/order. The affected current item rerenders safely; unaffected draft/cursor state stays intact, and the execution cannot complete while the reset item remains pending.
5. **Version stale submissions without hashes.** Reuse readable existing revision mechanisms where reliable, otherwise add monotonic integer generations owned by Data. Paper structure and answering content need separate invalidation boundaries. A stale submit performs zero learning writes, explains the change and refreshes the affected state. Metadata-only changes must not invalidate an answer. Shared JSON/SQLite effects need recoverable coordination; an interrupted update must not silently expose mismatched Paper/progress as usable. Persisted revision checks are required even after restart and across tabs.
6. **Delete containers independently.** Deleting a Paper removes its own unfinished state and drafts, never question rows or attempts. History retains the old label/identity with deleted-container status. Container metadata must remain readable/deletable/repairable even if its live items are missing; starting/exporting reports exact unavailable items instead of silently omitting the Paper.
7. **Delete questions with current-reference cleanup, not historical erasure.** Remove the deleted question from saved Paper memberships, unfinished checkpoints and drafts, preserving every other item's progress. This is the owner-confirmed exception to manual membership-edit reset. Keep an empty Paper visible but unstartable. Use a Data-owned historical/tombstone representation so existing evidence remains renderable without treating the deleted question as active pool content. No direct deletion path may leave current dangling references or delete genuine historical attempts. Existing rollback refusal for dependent learning records remains unless its owning contract is explicitly changed; this proposal does not grant arbitrary destructive rollback.
8. **Dispatch rendering by item payload.** Reuse current choice/judgment/open renderers from each item's validated content. `practice_mode` remains compatibility metadata, not an instruction to convert every item to the same interaction. Objective auto-grading requires a valid answer key; absent keys are explicit unknowns, never fabricated or silently treated as open problems. Preserve existing self-rating timing.

Answering-type invalidation refers to the effective answering payload (`micro_quiz.quiz_type`, options/key and relevant content-mode capability), not the academic `problem_type` classification such as calculation/explanation. Reuse existing normalized payload validation/comparison; do not reset a draft for a source/title/difficulty update whose effective answering content is identical.

## Compatibility and reconciliation

Existing `ps-NNN`, manifests, URLs and request metadata stay compatible. Migrate a healthy legacy unfinished saved-Paper execution into its owning Paper progress without changing item order, attempt associations or evidence. Broken legacy references are diagnosed explicitly; do not silently remap the CO IDs or attach orphan 19-item markers to the new 22-item Paper. The separate FK repair is a prerequisite to reliable migration on affected pools. Existing temporary Paper execution must remain available without silently saving a new managed container.

Proposed schema/field changes must be documented in DATA_MODEL and migrated only via approved incremental ensure/migration boundaries. Do not change current authority files to claim this behavior exists before implementation.

## Acceptance and handoff

### Implementation storage and coordination

Keep `active_practice` and its items as the selected execution. Add a Data-owned `paper_state`
row per saved Paper with an integer structure generation and a parked checkpoint JSON; switching
parks/restores the existing execution shape. Add monotonic execution IDs and question-content
revisions. Selected items store their content revision and answer/choice draft separately from attempts.
All new schema is added through `ensure_workbench_schema`; no normal startup silently migrates a pool.

Question semantic comparison is one pure Domain rule; Data content updates and batch patches invoke
the same revision invalidation inside their existing transactions. Dormant checkpoints reconcile their
stored item revisions before being resumed. Tombstoned question rows reserve their identity and keep
historical foreign keys valid, while active pool queries omit them.

Paper JSON and SQLite changes use a durable pending-file value in `paper_state`. Reset/deletion and
the file intent commit together; file publication is idempotent and retried before Paper access.
An unfinished publication blocks affected Paper use until it can be reconciled. No separate persistence
service, dependency, hash ID or attempt reconstruction is introduced.

Use isolated course copies and explicit operator authorization for real-data changes. Test A/B switching across refresh/server restart, semantic vs metadata edits, deleted items in several Papers, stale submissions and absence of learning-row changes. Full tests, compileall, strict OpenSpec, extraction guard and an independent isolated browser walkthrough are release gates. Record implementation and acceptance evidence in `docs/STATUS-paper-progress-2026-10-17.md`; a planning artifact alone never proves runtime acceptance.
