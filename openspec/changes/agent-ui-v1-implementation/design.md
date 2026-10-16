## Context

The accepted Agent UI v1 baseline keeps the central Lesson Kit page primary, the right rail conversation-first, and auxiliary work surfaces temporary. Existing contracts already define the Agent rail, provider activity, failure summaries, and managed saved Papers. This change adds presentation behavior around those existing contracts and records the three stacked PR stages in the proposal and tasks.

The browser shell remains responsible for rendering and sending user actions. Provider activity continues to arrive through the existing Bridge and conversation mirror. Managed Papers continue to use the existing writer and `.lessonkit/practice-sets/ps-NNN.json` records. No new pool schema, Paper lifecycle, or provider API is needed.

## Goals / Non-Goals

**Goals:**

- Keep transient Agent UI state tied to one conversation and one user turn.
- Keep the existing provider event/history path and managed Paper store as the sources for durable facts.
- Make approval, pending sends, and live Paper previews behave predictably across asynchronous events and reloads.

**Non-Goals:**

- Introduce a task engine, queue, new retry framework, persistent UI database, or second Paper store.
- Change provider/session semantics, saved-Paper write semantics, learning records, or current navigation routes.
- Turn the Adaptive Split into a full Paper editor or replace the conversation's activity history.

## Decisions

### Reuse the existing presentation and runtime owners

Keep the Agent UI module responsible for the rail presentation, context chips, composer sizing, transient surfaces, Approval Gate, and Artifact preview. The existing workbench runtime remains responsible for provider events, turn creation, polling, actions, and session selection. This preserves the one-way Shell → Domain → Data direction and avoids a second runtime coordinator. A separate task dashboard or provider-specific UI was considered and rejected because it would duplicate the conversation history and provider contracts.

### Scope transient state to the active conversation and turn

Activity Float, Bottom Dock, collapse suppression, approvals, and polling position belong to the active conversation. A new turn resets the current-turn collapse suppression. A conversation switch clears all of that conversation's transient presentation state and invalidates late callbacks from its earlier requests. The visible conversation history remains available through the existing successful mirror.

The send gate starts when the first submit is accepted by the client, before the create-turn request returns its turn id. Click and Enter use the same gate. The textarea stays editable while work runs, but neither input path can create a second turn. No queue behavior is added.

A progress GET failure is an unknown progress state, not a provider terminal failure. Keep the current turn identity and send gate until an authoritative terminal response or cancellation arrives. This avoids duplicate turns without adding a new polling or retry protocol.

### Keep Approval Gate narrow and reuse the rollback path

Only the low-reversibility content-batch rollback uses Approval Gate in v1. The gate presents the batch, reason, and impact and temporarily replaces the composer. Approval calls the existing rollback operation once; cancellation makes no request. A conversation switch clears the gate and invalidates both callbacks, so a stale approval cannot act on the old batch. A generic confirmation for normal reversible activity was rejected.

### Preserve the distinction between live surfaces and conversation history

Activity Float replaces its short-lived content. Bottom Dock summarizes current multi-step milestones. Both remain presentation surfaces; the conversation continues to own activity history and detailed output disclosures. Confirmed failures use the existing semantic failure path. The contract intentionally does not add a numeric duration threshold between short and sustained activity.

An Artifact card is a presentational handoff attached to the successful conversation mirror. It does not create another Paper record. A new Artifact opens a temporary Adaptive Split unless the learner has collapsed auxiliary work for that turn; the current Lesson Kit page remains present and the saved-Paper page opens only through an explicit native link.

### Resolve Artifact identity from the managed Paper record

A successful `lesson-kit papers save` receipt is required to establish that the save operation succeeded. Its `practice_set_id` must resolve to a record in the selected workspace's existing managed Paper store. The normalized Artifact takes its id, title, and item count from that record; model-provided title/count are never authoritative. An optional summary is presentation text only. Any model-provided URL is discarded; the UI derives the native `/w/<workspace>/practice-sets` destination from the active workspace.

The saved-Paper store and receipt were chosen over model-only claims or a new Artifact schema because they already define the managed Paper lifecycle and identity. If the record cannot be resolved, the conversation receives no Artifact card; the saved Paper remains discoverable from the existing Paper list.

### Restore only a live preview, not historical navigation

When a newly completed Artifact preview is still open, retain its conversation id and Paper id in tab-scoped session state so a reload of the same tab and current route can restore that preview. Clear this state on explicit collapse, a new user turn, a conversation switch, or native navigation. Replaying historical Artifact cards rebuilds the cards but never opens a split by itself. This keeps the current live handoff useful across refresh without making old conversation history take over the page.

### Keep acceptance evidence separate from implementation tasks

The OpenSpec change remains active across PR135–137. Its full delta describes the accepted target behavior, while each stacked PR updates the live specs and product/action documentation only for behavior delivered at that stage. All task checkboxes remain open until the combined implementation passes independent review and the required final gates; archive follows that acceptance and is outside this documentation pass.

## Risks / Trade-offs

- **A missing or mismatched managed Paper record prevents an Artifact card.** The existing saved-Paper list and record remain authoritative, and the user can open that page directly.
- **Tab-scoped preview state does not survive closing the tab or switching conversations.** The successful conversation mirror still restores the historical Artifact card.
- **Progress transport loss can leave a turn gated until authoritative status is available.** The UI reports unavailable progress rather than risking a duplicate turn or falsely claiming provider failure.
- **The short-versus-sustained activity boundary remains qualitative.** No numeric time/count threshold is added to the user contract.

## Migration Plan

There is no data migration. Merge PR135's foundation documentation into PR136, then PR136 into PR137, and update the live specs and supporting documents at each stage. The final change stays open until the combined branches receive independent review and the full required gates. Reverting the UI code needs no data rollback; a managed Paper already saved remains available through the existing store and route.
