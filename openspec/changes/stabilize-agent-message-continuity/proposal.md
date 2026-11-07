## Why

消息连续性与极简发送队列 implements the owner's confirmed use cases from Q022/Q025–Q027/Q030/Q042–Q043/Q046–Q047/Q051/Q065/Q069–Q072，S005/S008. The planning baseline covers 103 substantive answers and the supplied learning protocol V3.1. This change has its own observable acceptance boundary in the program tree.

## What Changes

- Accepted messages SHALL persist once in conversation history with captured submission context. Failure, stop and queue waiting SHALL NOT relocate or duplicate the original message. Unknown acceptance SHALL reconcile the same submission identity.
- The ordinary pending list SHALL show only message content, edit and delete controls. It SHALL contain no additional state fields, reorder or send-now controls. Existing configured running-send behavior SHALL remain usable through its settings entry.
- An explicit stop SHALL pause retained pending messages until explicit continuation. An abnormal restart SHALL retain never-started messages without dispatch. Ordinary execution failure SHALL NOT automatically retry the failed message and independent subsequent messages SHALL follow the existing continuation behavior.
- Queued and retried messages SHALL use their original captured course and object context. An explicit failed-message retry SHALL use current edited text, linked retry identity and original context, without overwriting a newer composer draft. Waiting without evidence of failure SHALL remain a brief status with a stop operation.

## Capabilities

### New Capabilities

- `agent-message-continuity` — 消息连续性与极简发送队列, with behavior and scenarios in this change's specification.

### Modified Capabilities

- `workbench-ui` — apply the approved partial-write, retirement or continuity changes while retaining the capability's unrelated behavior.

Current requirement-level changes are supplied as MODIFIED/REMOVED deltas where this package changes existing behavior. The reconciliation ledger is `docs/design/workbench-capability-maturation/contract-reconciliation.md`. The first implementation task verifies these complete blocks against the actual checkout and resolves any newly observed drift before code changes. Added capabilities SHALL NOT silently override another responsibility source.

## Impact

Primary implementation paths are listed in `docs/design/workbench-capability-maturation/packages/wp04.md`. Shell adapters perform no business rules, Domain comparisons perform no IO, Data owns SQLite, and Bridge performs requested external operations. Use existing stdlib and platform facilities.

Acceptance uses CHAT-01–05 plus RELEASE-01–03. This is a planning artifact. Task completion requires actual evidence and the plan's numeric targets remain unmeasured until implementation.
