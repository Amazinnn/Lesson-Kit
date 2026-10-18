## Context

The user message currently survives only as an optimistic DOM bubble until a successful exchange is appended to `transcript.jsonl`. Failed turns do not produce that exchange; a fresh history read therefore loses their user text. Startup also recreates the list view on full-document navigation. The desktop HTML demonstrates behavior, not a visual or layout contract. See the dated investigation for code evidence.

## Goals / Non-Goals

**Goals:** durable visible messages regardless of execution result; a persistent right rail within one workspace; truthful tool/failure/approval UI. Queue lifecycle is owned by `queue-agent-messages-and-interrupt`.

**Non-Goals:** concurrent provider tasks in one conversation, a new task scheduler/service, automatic resurrection of stopped work, aesthetic reproduction, a design-control panel, unrestricted replay of arbitrary tool commands or exposing private reasoning.

## Decisions

1. **Accepted message durability and idempotent retry.** Owned by `preserve-agent-messages-and-tool-outcomes`; this lifecycle change relies on its stable submitted identity, captured context, and durable accepted-turn history.
2. **History and failure recovery.** Owned by `preserve-agent-messages-and-tool-outcomes`; focused queue implementation and evidence are owned by `queue-agent-messages-and-interrupt`. This aggregate retains only the end-to-end lifecycle contract and acceptance.
3. **Queue and interruption ownership.** `queue-agent-messages-and-interrupt` owns queue ordering, interruption, recovery and running-send preferences. This aggregate does not duplicate that contract.
6. **Keep the rail mounted.** Introduce a workspace navigation boundary which updates the middle content and its owned lifecycle while preserving the existing right-rail controller/DOM. Support internal practice/Paper/KP/graph/records navigation, query-state changes and back/forward; a canonical deep link or full refresh remains supported. Do not recreate the rail, rerender its history, lose focus/draft/scroll, reset polls or hide it behind the list for middle-only navigation. Update page-context chips for the new middle page; capture new-message context at submission. Dispose old middle-view listeners/graph workers before initializing the new middle view. Reuse server-rendered middle markup and existing page modules rather than introducing a frontend framework or iframe. Workspace changes keep their existing conversation/data isolation.
7. **Tool outcome display and basic recovery.** Owned by `preserve-agent-messages-and-tool-outcomes`. This lifecycle change adds only queue/interrupt controls and retains the existing rollback and Paper approval contracts; it does not add a generic approval gate.
8. **Reuse governed approvals.** Existing rollback approval stays intact. Paper structure updates requiring progress reset use the impact preview/confirmation defined by the Paper change. Do not add a generic approval gate to every normal tool. Scope callbacks by workspace/conversation/message and operation revision; cancellation or switching conversation invalidates stale approvals.
9. **Activity progress surfaces have a separate owner.** The Activity Float/Bottom Dock selection, collapse/reopen behavior, idle cleanup, and Dock retirement are specified only by `use-collapsible-agent-activity-float`.

## Compatibility and rollout

Preserve provider/model ownership, native-session continuation and current working-directory contracts. Same-conversation simultaneous turns remain forbidden. Existing exported artifacts and successful transcripts remain readable. Inventory supported provider cancellation behavior; no provider may advertise resumable suspension merely because it supports abort. Bridge must persist message acceptance before any provider launch, including launch failure. UI clients must use the accepted-message identity and queue dispatch contracts from their owning changes.

Document new artifacts/status fields in FILE_CONTRACT and any affected DATA_MODEL ownership; reconcile live specs and Action Graph in the implementation PR. No real course conversations or provider processes are mutated by specification preparation.

## Acceptance

Use fake providers and isolated registries for message acceptance, provider failure, double-click/retry and legacy transcript reads; queue ordering, cancellation and recovery acceptance is recorded by `queue-agent-messages-and-interrupt`. Browser checks must assert actual rail DOM/controller identity and input/scroll/poll retention, not merely restored conversation ID. Independently run required repository gates and isolated browser acceptance.
