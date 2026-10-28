## Context

See proposal.md — Why. Current `practice_sets.update_saved` calls `paper_progress.reset` for any membership/order edit. Reset clears the parked checkpoint and deletes the active resource without preserving that execution. `content.update` currently changes answering content under the same ID. `content.delete` already retains a question through `deleted_at` but drops its unfinished item reference. Existing Paper generation, execution IDs, content revisions and pending file publication provide concurrency and recovery machinery to reuse.

The read-only incident audit found 23 pre-reset Attempts still present, two post-restart Attempts, a 72→71 item proposal and no archived ch01 question. This is evidence for a regression fixture, not proof that all old drafts are recoverable. No production repair is part of this change.

## Goals / Non-Goals

**Goals:** One Data-owned lifecycle used by every writer; current containers automatically reconcile while evidence remains attributable; persisted dependency invalidation is cheap and recomputation occurs only on use.

**Non-Goals:** No user-facing version browser, background refresh service, new dependency, hash identity, historical regrading, automatic adaptive selection, physical purge command, or inferred production-history reconstruction. Ordinary Paper problems are covered; flash-card-specific semantics remain unchanged.

## Decisions

### 1. Lifecycle operations belong in the existing Data boundary

Extend existing content, Paper, progress and records modules rather than introducing a generic revision platform. Domain's existing answering-content comparison decides semantic equivalence; IO, identity allocation and transactions stay in Data. Shell validates requests and forwards only. Use current normalizers; do not invent a heuristic that treats potentially meaningful wording as formatting. Existing identity-targeted ingest dedup must exclude the explicitly replaced predecessor from self-conflict while continuing to reject unrelated duplicates.

Keep existing update/delete entrypoints. Delete receipts explicitly report archive semantics. Add `data … restore problem <id>` and `papers … restore <id>` alongside existing commands, plus corresponding restore routes in the existing API families. Current list/get/search/pull remain current-only; historical reads use an explicit history/archive path, never a hidden fallback into current access. Updating an archived ID fails until explicitly restored.

Semantic update receipts add `replaced_problem_id`, `problem_id` (new ID), affected Paper IDs, pending item locations and stale-result targets; ordinary updates retain their existing identity field. Paper receipts add preserved/pending/removed counts and retained-history references. Reads returning required derived results either return refreshed values or an explicit unavailable/conflict response. No new command is needed just to invalidate caches.

### 2. Use additive retention and provenance, not mutable historical references

Reuse `problems.deleted_at` for archived questions and existing readable sequential allocation for successors. Add one replacement provenance row per old→new pair, containing operation identity, effective-time/cutoff and inherited question-level projection/schedule baseline. Predecessor/successor are immutable references; no automatic redirects for submissions or historical reads. Repeated replacements form a bounded traversable lineage; IDs are never reused.

Extend `paper_state` with archive timestamp and retained definition JSON. Archive keeps the same Paper ID, definition and checkpoint but removes its current published JSON through the existing pending publication intent. Restore republishes that same ID after reconciling current availability and replacement mappings. Archived Paper definitions are reconciled lazily at restore; no archived question is resurrected.

Add a retained execution-item history table keyed by readable execution identity plus local monotonic history sequence. It stores original item identity, Paper association, position, content snapshot, state, Attempt link, draft/sequence, reveal/stuck facts, reason and time of retirement. Capture before removing or replacing a live item; reorder alone adds no history row. Preserve the existing execution ID for an adaptive change. An empty execution remains representable with cursor zero and no current item; it is neither cleared nor completed. Paper archive parks the active execution and preserves its checkpoint before clearing the active slot.

New submissions and first durably saved drafts capture their answering-content snapshot, including actual option text. Retired-item history preserves that snapshot and the latest confirmed draft. Completed run snapshots retain those same facts. Existing Attempts and child references are not rebuilt or moved. Missing legacy snapshots are shown as unrecorded; the migration must not fabricate historical content from today's row. Ordinary metadata edits must not rewrite existing historical snapshots.

### 3. Reconcile by identity and preserve guarded execution

For current Paper edits, construct old/new identity maps inside the write transaction. Copy surviving execution records by question ID, assign new positions, and initialize only added/replacement identities pending. Saved Paper validation already forbids duplicate IDs; preserve that constraint. Removed states move to retained history. Cursor follows its old question if retained, otherwise the next surviving old position, otherwise the preceding survivor, otherwise the first added item or zero for empty. Preserve the run's reveal/rating preferences and all other item states.

Bump structural generation for membership changes; update the retained execution/checkpoint's expected generation atomically. A semantic replacement substitutes the new ID at each current Paper position and creates pending state there, without rewriting completed runs. Item-only operations must preserve unrelated Paper generations. Parked and active executions use the same transformation. Saved archived Papers apply this transform during restoration.

Keep preview as an inspectable impact report and expected-state guard, not a second authorization gate. Mutation requests provide expected generation/execution/content and monotonic draft state; any mismatch causes zero writes. Valid requests mutate state and queue all affected file intents in one immediate transaction, then publish idempotently. Readers finish pending publications through existing recovery. A delayed old submit is rejected, never rebound by position or redirected to a successor. Existing identical request retries return their original receipt without replaying effects.

Only durably saved input can be guaranteed by server archival. Browser-only unsent input remains in the existing outbox on conflict and is labelled locally recoverable; do not silently import it into a new identity.

### 4. One-time learning inheritance and dependency-driven refresh

On replacement, resolve the predecessor's effective projections first if needed; snapshot question progress/current learning state and direction-specific schedule as the successor's initial baseline, including cutoff and provenance. This read is a genuine consumer of stale state. Do not copy Attempts, feedback or learner signals. The successor's later projection rebuild starts from its inherited baseline plus its own subsequent evidence, so a cache rebuild cannot erase inheritance. A restored predecessor resumes its own state; subsequent evidence does not flow across lineage.

KP calculations consume original evidence IDs once, using their recorded target/contribution rather than treating inherited projections as new evidence. A replacement's identical KP membership does not itself create new learning evidence. KP reassociation affects current counts and affected dependency results without rewriting historical target attribution. Historical self-rating overwrite keeps its existing no-replayed-learning-effects boundary.

Add a small persisted derived-result state table keyed by existing result kind and target, with dependency generation and computed generation. Existing materialized projection rows remain their current stores. Existing on-demand statistics need no duplicate cache: compute when requested against current data. Data mutation helpers mark only affected targets in the same transaction; no global invalidation pass or background scheduler. Domain formulas remain unchanged.

Dependency rules: Paper membership affects its own count/completion summaries; current availability/KP association affects old/new KP available counts and assembly candidates; answering semantics affects the replacement and referencing current executions; actual new evidence affects the existing problem/KP learning and scheduling dependencies. Archive alone does not invalidate historical evidence or force unchanged knowledge mastery to change. Presentation metadata does not invalidate answering state. Derived KP weakness/availability consumers that depend on changed inputs must be marked, even if learning evidence itself did not change.

All consumers (UI reads, CLI state/due/weak/pull, plans, Agent context and evidence surfaces) pass through a shared Data freshness boundary. Recompute requested stale targets with a stable dependency generation, publish projection and computed generation together, and refuse publication if dependencies changed. Failure leaves the stale marker and returns a truthful error; no old result may drive a decision. Fresh reads are cheap. Retain source event order and existing scheduling formulas; no invented historical event or new judgement is permitted.

### 5. Current presentation and historical evidence have separate routes

Current Paper views always join the current membership to latest question content. A selected completed run stays completed and does not claim new/replacement questions were answered. Its historical item records remain accessible as original content and actual submissions/drafts, not as selectable content versions. Archive inspection and restore are supported authoring/CLI/API operations; no student assembly controls are reintroduced.

Retire the ordinary `paper_update_proposal` pause/approval path in favor of authorized guarded tool execution. Existing pending legacy approvals are shown obsolete and inert; allow cancel or explicit resubmission. Never autoapply them, never auto-resume their paused queues. Other approval and rollback gates remain unchanged.

### 6. Explicit reconciliation ledger

| Current contract | Required replacement and owner |
|---|---|
| Manual structure edit resets progress | Adaptive membership transform; practice-set-export, DATA_MODEL, FILE_CONTRACT |
| Correction preserves question ID, discards stale drafts | New successor ID with retained evidence/drafts; content-governance, review-workbench |
| Historical row is not restorable | Explicit archive restore; GLOSSARY, DATA_MODEL, PRODUCT-MANUAL |
| Paper deletion removes unfinished state | Retained archived definition/checkpoint; practice-set-export, DATA_MODEL |
| Paper reset approval pauses dispatch | Clear instruction authorizes guarded operation; ai-teacher-bridge, workbench-ui, ACTION-GRAPH |
| Unconditional replay of archived saved-Paper items | Start/retry saved Paper uses latest membership; original run remains history; review-workbench |
| Batch patch always changes one existing row | Ordinary patch remains in place; semantic replacement records mappings and safe inverse; FILE_CONTRACT, content-governance |

The lifecycle delta wins only after implementation, main-spec synchronization and matching responsibility-document updates. This proposal does not silently redefine today's runtime. Audit remaining ID/approval/reset wording across responsibilities and active changes before delivery; overlapping changes must explicitly adopt this contract rather than pick whichever file is newer.

## Risks / Trade-offs

- Retained snapshots grow storage → accepted cost of preserving user data; no purge introduced.
- Global replacement touches several files → reuse transactional intents and test recovery after commit and partial publication.
- New IDs affect external authored projections → report exact mapping; mirror/export must replace the current file under the new ID and must not reactivate predecessor content on repeated sync.
- Stale events race with replacement → guarded identity/version writes, recoverable local outbox, no silent redirect.
- Legacy missing drafts/lineage → expose absence; migrate only mechanically proven facts, never infer run links from timestamps.
- Inherited baselines accidentally counted as evidence → regression across A→B→C, restoration and lazy refresh; count original evidence identities once.

## Migration Plan

1. Implement and verify with temporary fixture databases only. Add fields/tables through existing ensure_* migration, retaining inbound foreign keys and child rows. Normal startup does not migrate pools.
2. Existing deleted rows remain archived/restorable but gain no invented predecessor relation. Existing current Papers remain current; no historical generation is converted into a user-visible version. Existing incomplete and complete runs keep their identities and evidence.
3. Deliver CLI/API/Agent/browser changes together after contract reconciliation. Back up a target pool and Paper directory before an explicitly scheduled real-workspace rollout; this planning delivery does not authorize that rollout.
4. If rollback is needed after successor IDs or archive records are written, stop writers and restore a coherent DB/Paper backup together. Old binaries must not write new-schema lifecycle data. Never restore only one file or erase post-backup evidence silently; first preserve it for separate reconciliation.

## Planning Handoff

2026-10-28: proposal/specs/design/tasks only. No runtime code or course data changed. Implementation and real-environment acceptance remain unchecked tasks. Production ps-006 progress recovery remains separate and unattempted. No unresolved product decision remains.
