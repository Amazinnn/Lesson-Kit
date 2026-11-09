## Why

审批与显式批次撤销退役 implements the owner's confirmed use cases from Q098/S008，协调 Q031/Q057/Q062/Q067 旧批准要求. The planning baseline covers 103 substantive answers and the supplied learning protocol V3.1. This change has its own observable acceptance boundary in the program tree.

## What Changes

- Actions that formerly required project approval SHALL proceed by default after validating actual inputs, without approval cards, extra confirmation clicks, waiting approval states or approval-driven dispatch pauses. Conflict-side choices and unresolved targets SHALL be treated as missing operation input.
- Recovery of a legacy pending approval SHALL revalidate its current target and execution identity and SHALL execute a still-valid unapplied action at most once. Stale callbacks SHALL NOT reapply or target another conversation. Invalid inputs SHALL be reported truthfully.
- Explicit rollback of successfully applied content batches SHALL be retired from CLI, Agent suggestions and result controls. Ordinary direct repair and data-consistent failed-unit handling SHALL remain available.
- A prepared and verified runtime or data change SHALL perform its normal cutover without waiting for another project approval. It SHALL record actual version identity, migration result and any failed acceptance.

## Capabilities

### New Capabilities

- `direct-project-actions` — 审批与显式批次撤销退役, with behavior and scenarios in this change's specification.

### Modified Capabilities

- `ai-teacher-bridge` — apply the approved partial-write, retirement or continuity changes while retaining the capability's unrelated behavior.
- `practice-set-export` — apply the approved partial-write, retirement or continuity changes while retaining the capability's unrelated behavior.
- `workbench-ui` — apply the approved partial-write, retirement or continuity changes while retaining the capability's unrelated behavior.

Current requirement-level changes are supplied as MODIFIED/REMOVED deltas where this package changes existing behavior. The reconciliation ledger is `docs/design/workbench-capability-maturation/contract-reconciliation.md`. The first implementation task verifies these complete blocks against the actual checkout and resolves any newly observed drift before code changes. Added capabilities SHALL NOT silently override another responsibility source.

## Impact

Primary implementation paths are listed in `docs/design/workbench-capability-maturation/packages/wp03.md`. Shell adapters perform no business rules, Domain comparisons perform no IO, Data owns SQLite, and Bridge performs requested external operations. Use existing stdlib and platform facilities.

Acceptance uses FLOW-01–03、RELEASE-02 plus RELEASE-01–03. This is a planning artifact. Task completion requires actual evidence and the plan's numeric targets remain unmeasured until implementation.
