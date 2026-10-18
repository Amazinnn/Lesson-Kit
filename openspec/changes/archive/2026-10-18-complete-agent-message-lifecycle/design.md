## Context

The original message-loss and rail-navigation investigation motivated this aggregate change. Accepted-message durability, persistent navigation and the single-worker queue have since shipped in their focused changes. The remaining work is Paper progress-reset approval. The desktop HTML demonstrates behavior, not a visual or layout contract.

## Goals / Non-Goals

**Goals:** durable visible messages regardless of execution result; a persistent right rail within one workspace; truthful tool/failure/approval UI. Queue lifecycle is owned by `queue-agent-messages-and-interrupt`.

**Non-Goals:** concurrent provider tasks in one conversation, a new task scheduler/service, automatic resurrection of stopped work, aesthetic reproduction, a design-control panel, unrestricted replay of arbitrary tool commands or exposing private reasoning.

## Decisions

1. **Accepted message durability and idempotent retry.** Owned by `preserve-agent-messages-and-tool-outcomes`; this lifecycle change relies on its stable submitted identity, captured context, and durable accepted-turn history.
2. **History and failure recovery.** Owned by `preserve-agent-messages-and-tool-outcomes`; focused queue implementation and evidence are owned by `queue-agent-messages-and-interrupt`. This aggregate retains only the end-to-end lifecycle contract and acceptance.
3. **Queue and interruption ownership.** `queue-agent-messages-and-interrupt` owns queue ordering, interruption, recovery and running-send preferences. This aggregate does not duplicate that contract.
6. **Keep the rail mounted.** Introduce a workspace navigation boundary which updates the middle content and its owned lifecycle while preserving the existing right-rail controller/DOM. Support internal practice/Paper/KP/graph/records navigation, query-state changes and back/forward; a canonical deep link or full refresh remains supported. Do not recreate the rail, rerender its history, lose focus/draft/scroll, reset polls or hide it behind the list for middle-only navigation. Update page-context chips for the new middle page; capture new-message context at submission. Dispose old middle-view listeners/graph workers before initializing the new middle view. Reuse server-rendered middle markup and existing page modules rather than introducing a frontend framework or iframe. Workspace changes keep their existing conversation/data isolation.
7. **Tool outcome display and basic recovery.** Owned by `preserve-agent-messages-and-tool-outcomes`; queue/interrupt controls are delivered by `queue-agent-messages-and-interrupt`. This change adds only the remaining Paper approval integration, not a generic approval gate.
8. **Reuse governed approvals.** Existing rollback approval stays intact. Paper structure updates use the impact preview/confirmation defined by the Paper contract. The Paper-specific decisions below reconcile the original generic input-replacement design with the user's confirmed choice; rollback still replaces the composer.
9. **Activity progress surfaces have a separate owner.** The Activity Float/Bottom Dock selection, collapse/reopen behavior, idle cleanup, and Dock retirement are specified only by `use-collapsible-agent-activity-float`.

## Paper approval decisions confirmed 2026-10-18

1. **Human click performs the update.** The Agent emits a proposed update for one explicit existing Paper, without applying it. Reuse `practice_sets.preview_update` and `update_saved`; show the Paper, membership/order change, affected completion count and draft count. The page's approval request delegates to the existing Data writer after revalidation. Existing preview confirmation is a content/progress snapshot, not evidence of a human click. Do not expand this into a general CLI permission system or change the documented manual CLI workflow.
2. **Pause before handoff.** Persist the pending approval and pause this conversation's queue before the proposing turn can hand off to B/C. The provider does not stay running while waiting for the learner. Pending approval blocks dispatch and manual queue continuation until resolved; approving or cancelling leaves B/C paused for explicit manual continuation. Other conversations are unaffected.
3. **Keep composing available.** The Paper approval is a distinct decision surface alongside the ordinary composer. Messages submitted while it is pending retain their submission context and join the paused queue; sending or choosing interrupt does not authorize the Paper update or bypass the pending decision. Do not reuse the rollback input-replacement rule for this action.
4. **Revalidate rather than ask the Agent again.** Approval binds workspace, conversation, proposing turn, Paper and operation revision. If the Paper or execution/progress snapshot changed, perform no update or reset; recompute the same proposed update's current impact, show it, and require another click. If the target is unavailable or the proposed update is invalid, report that state without recreating the Paper. Repeated clicks or a lost response must not cause a second reset.
5. **Restore pending decisions.** Reuse existing conversation/turn artifacts for the immutable proposal and pending/resolved outcome, not a new database or approval service. Reload, page reopen and service recovery restore a pending approval and paused queue without approving or launching providers. Middle navigation preserves the same decision. Switching conversations invalidates old UI callbacks; any restored decision must be bound anew to its owning conversation, never applied to the newly selected one.
6. **Preserve established Paper semantics.** Retain Paper ID and questions; reset only the target Paper's unfinished progress/drafts when its membership/order effectively changes. Preserve historical attempts/ratings and other Papers. Title/description/no-op edits, question-level resets and direct Paper UI operations retain their owning contracts; do not add approval to every tool or re-ingest questions.

Implementation must synchronize FILE_CONTRACT for the actual approval artifact/API shape, Product Manual and Action Graph for the new actions, and owning live specs in the same implementation PR. This preparation does not add live API fields or claim the UI has shipped.

## Compatibility and rollout

Preserve provider/model ownership, native-session continuation and current working-directory contracts. Same-conversation simultaneous turns remain forbidden. Existing exported artifacts and successful transcripts remain readable. Inventory supported provider cancellation behavior; no provider may advertise resumable suspension merely because it supports abort. Bridge must persist message acceptance before any provider launch, including launch failure. UI clients must use the accepted-message identity and queue dispatch contracts from their owning changes.

Document new artifacts/status fields in FILE_CONTRACT and any affected DATA_MODEL ownership; reconcile live specs and Action Graph in the implementation PR. No real course conversations or provider processes are mutated by specification preparation.

## Acceptance

Use fake providers and isolated registries for message acceptance, provider failure, double-click/retry and legacy transcript reads; queue ordering, cancellation and recovery acceptance is recorded by `queue-agent-messages-and-interrupt`. Browser checks must assert actual rail DOM/controller identity and input/scroll/poll retention, not merely restored conversation ID. Independently run required repository gates and isolated browser acceptance.
