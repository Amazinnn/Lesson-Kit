# Paper / Agent investigation and decisions - 2026-10-17

Status: investigation and specification preparation only. No product implementation, real course repair, migration, re-import or service restart has been performed. Live OpenSpec and responsibility documents remain authoritative for current behavior; active changes describe proposed behavior.

## Evidence and limits

Checkout: `5cd6f61755eae19ba1aeab04a125085e02161f80`. Registration selects the Computer Organization workspace and `pool/co.db`; all course SQLite connections used URI `mode=ro`. Read-only inspection also covered managed Paper JSON, ingest manifests and selected course audit/backup files. Prior memory was a search hint, not current database evidence.

### CO incident

- `batch-095` records 70 original IDs `co-ch02-prob-126` through `co-ch02-prob-195`; none remain in the current formal pool. `batch-096` holds 70 replacement IDs `co-ch02-mq-042` through `co-ch02-mq-111`. All 70 source keys and source-evidence values match between manifests: the source questions were re-created rather than edited in place.
- Active execution still references `ps-001`, its old 70-question title, `practice_mode=exam`, cursor 19 and all 70 missing original IDs. Items have 19 `stuck` markers and 51 `pending` markers.
- Current `ps-001.json` instead describes a 22-question / 100-point Paper with replacement IDs; none of its 22 references are missing. The Paper ID was retained, but its old execution was not reconciled.
- `problem_attempts` and `problem_progress` are empty; 19 schedule rows remain. The 19 old attempt references are not 19 surviving attempts. Do not claim the attempts migrated or attached to the new Paper.
- A dated course inventory reports that the original attempts/progress existed at its snapshot. The deleting operation is unproven. Both batch records are not marked rolled back; ordinary recorded rollback is not established as the cause.
- Selected `pre-bundle-riscv-ch02*` backups inspected here contain no original 70 rows or attempts. This does not exhaust other recovery sources. Do not fabricate attempts from checkpoint markers.

### Code defects and gaps

1. `data.practice_sets.update_saved` retains the Paper ID but only updates JSON; it does not reset/reconcile unfinished execution after membership/order changes. `delete_saved` also ignores execution state.
2. `get_saved` validates all live problem references before returning the container. Updating/deleting uses this reader, so missing questions can prevent container repair/deletion. `list_saved` silently hides invalid records. Container readability and startability need separation.
3. One workspace singleton currently carries resumable execution; switching Papers replaces/archives instead of retaining separate unfinished progress.
4. `problem-patch` / `data.content.plan_problem_patch` already supports identity-preserving `micro_quiz` and content-mode edits. Reuse it; reconcile semantic-edit invalidation across writers rather than inventing another importer.
5. Execution carries a legacy whole-run content mode, insufficient for the confirmed per-item mixed-type rendering contract.

### Independent migration defect

Live `active_practice_items.attempt_id` references nonexistent `problem_attempts_widening_old`. Read-only `PRAGMA foreign_key_check` reports violations. The existing `_widen_problem_attempts_status_check` renames the parent, creates a replacement, copies attempts and drops the temporary parent; SQLite rewrites child references to the temporary name.

An in-memory reproduction ran that existing function: the attempt row survived but the child's foreign key targeted `problem_attempts_widening_old` and failed the integrity check. This proves a reference-rewrite bug, **not** that the function deleted the live attempts. Track structural repair separately; preserve rows and report unresolved missing-parent data instead of inventing it.

### Agent and HTML findings

- Live `workbench.js` / `agent-ui.js` bytes match the checkout. A stale install is not established as the explanation.
- Middle-page navigation creates a new document. Startup shows the list first, then asynchronously restores the selected conversation. This fails the owner's literal persistent-right-rail requirement.
- `aiSendMessage` inserts an optimistic bubble and empties the composer before POST success. It does not persist a recoverable outgoing message.
- `start_turn` persists turn status/timestamps without the user message. `get` rebuilds history from successful exchanges in `transcript.jsonl`; `_store_answer` writes the exchange only on success. Rejected sends and provider failures can therefore lose the user's text after reload. A fake-provider browser reproduction remains an implementation test, not a completed acceptance claim.
- `C:\Users\yanwei\Desktop\lesson-kit-agent-ui-original-palette-playground.html` is a **functional demonstration**, explicitly not an aesthetic/layout reference. Tuning controls, presets and copy-brief are not product requirements.
- Float/Dock/chips/composer/managed Artifact behavior exists. Unified Tool Call Card, failure impact/recovery, additional confirmed-action approval integration and reliable running-message behavior remain incomplete. A demonstration button does not prove an executable backend operation.

## Owner-confirmed rules

1. Resetting a Paper clears its execution progress/drafts only; real attempts, ratings and question learning state survive. Other Papers sharing questions stay independent.
2. Membership/order changes reset that Paper's unfinished progress. Title/description changes do not. Show exact impact and require confirmation; cancelling writes nothing. Saving an edit returns it to not started, without auto-start.
3. Stem/options/answer-key/answering-type edits keep question ID and Paper membership/order, but reset only that question in unfinished progress and discard its stale draft. Explanation/title/KP/difficulty/source-only edits do not reset it. Never auto-regrade historical attempts.
4. Each Paper retains one unfinished progress record across switching and refresh, including unsubmitted draft text/choices. Drafts are not attempts; only one Paper is active at once.
5. Delete Paper: remove container/unfinished progress, retain questions, learning evidence and completed historical runs; show that the historical Paper was deleted.
6. Corrected imports explicitly name existing Paper/question targets. No title/text similarity overwrite. Reuse patching; creating and updating are separate actions.
7. Render each mixed Paper item by actual question type; a legacy whole-Paper mode must not force objective questions into free-text answering.
8. Delete question: allowed, automatically clean its current references/drafts; retain other-item progress and historical attempts/ratings/runs, and label deleted content without requiring an active question. The detailed confirmed exception is recorded below.
9. Running-message default: queue, with explicit interrupt-and-send; configurable in settings. Earlier concurrent-turn wording was corrected: **one running turn per conversation**, never simultaneous Agent work for multiple messages.
10. Interrupt-and-send stops the current turn, preserves completed effects, processes the new message and never auto-resumes the old task. Failure/unexpected interruption pauses and retains the queue until user action.
11. Middle navigation preserves the rail instance, conversation, composer draft, scroll, running work and queue. Chips/new messages follow current middle-page context; running work keeps original context. Queued messages capture context at user submission, not later dispatch.
12. A failed user message remains recoverable with a failed/unknown status as appropriate. An error line without the original message is insufficient.
13. Runtime progress uses only the top-right Activity Float for short and sustained work. Retire automatic Bottom Dock presentation because it obstructs the middle page. This later decision supersedes the HTML's long-task Dock example and old progress-surface baseline, not the separate explicit result-preview interaction.
14. Add a small explicit Float expand/collapse button. Collapsing retains its compact reopening control; later activity in the same turn cannot force expansion. Keep the Float bounded/collapsible and avoid an idle placeholder panel.

## Final owner decisions

- Deleting a question removes only that item and its draft/progress from affected Papers; other-item progress survives. This is an explicit exception to a manual Paper membership/order edit resetting that Paper's unfinished progress. An empty Paper remains an empty container and cannot start until items are added.
- Interrupt-and-send pauses the older queue. For running A, queued B/C and interrupting D: stop A, run D only after A is confirmed stopped, leave B/C retained and paused. Neither A nor B/C resumes automatically.
- The owner reiterated that Papers must not be completed serially: A can remain unfinished while B is practiced, with separate durable progress/drafts for each. Switching is not abandonment, replacement or completion. At most one selected Paper does not mean at most one unfinished Paper.

## Engineering defaults and handoff

Document local outgoing-message preservation, durable server acceptance and idempotent request identity; distinguish unaccepted/unknown send status from accepted provider failure. Preserve queues across refresh and pause after interrupted service recovery. Offer only real, backend-supported recovery actions. These defaults are proposed engineering choices, not additional owner questionnaire answers.

Existing data recovery is separate and unexecuted. No automatic old/new ID remap or transfer of the 19 orphan markers is approved. This conversation owns investigation/definitions/OpenSpec only; another agent owns implementation/focused tests, and independent acceptance owns full-suite, isolated walkthrough and release/archive. Document validation never marks implementation tasks complete.
