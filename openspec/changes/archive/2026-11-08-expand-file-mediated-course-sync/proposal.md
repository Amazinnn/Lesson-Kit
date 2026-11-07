## Why

完整课程交换与外部 Tutor 交接 implements the owner's confirmed use cases from Q002/Q005–Q020/Q080/Q082–Q083/Q097/Q099–Q102/Q105–Q106；S007–S010. The planning baseline covers 103 substantive answers and the supplied learning protocol V3.1. This change has its own observable acceptance boundary in the program tree.

## What Changes

- A Course Exchange Bundle SHALL cover every managed course content, source attachment, Paper, learning fact, unfinished draft, non-sensitive preference and Course Learning File listed in the exchange matrix. The default full-course operation SHALL disclose unsupported or missing assets and SHALL NOT report complete success while any required class is absent.
- The receiver SHALL support additions, updates, explicit deletions and restoration, validate course origin and dependencies, and register a genuinely new course in one receive operation. A missing file alone SHALL NOT authorize deletion.
- One-sided and identical changes SHALL reconcile automatically. Genuine two-sided changes SHALL expose differences and accept a single or batch side choice. Independent attempt facts SHALL merge without duplication. Different-question draft updates SHALL merge while same-question differences require side choice.
- The receiver SHALL apply Independent Valid Mutation Units, retain invalid items and their dependents, and report actual per-item outcomes. Retrying interrupted input SHALL NOT duplicate completed facts or re-execute accepted operations. Explicit successful-batch undo SHALL be retired.
- The same configured CLI SHALL coordinate file exchange and Git transport and SHALL support hourly operating-system scheduling for all registered courses with configured media. A quiet success and a single short conflict notification SHALL reflect actual outcomes. Git publication SHALL be reported independently from local reception.
- External Tutor Handoff SHALL carry original question and answer identities, unanswered items, reveal facts, goals and continuation position. Receiving Tutor output SHALL preserve raw learner answers and distinguish interpretations from observed facts.

## Capabilities

### New Capabilities

- `file-course-sync` — 完整课程交换与外部 Tutor 交接, with behavior and scenarios in this change's specification.

### Modified Capabilities

Current requirement-level changes are supplied as MODIFIED/REMOVED deltas where this package changes existing behavior. The reconciliation ledger is `docs/design/workbench-capability-maturation/contract-reconciliation.md`. The first implementation task verifies these complete blocks against the actual checkout and resolves any newly observed drift before code changes. Added capabilities SHALL NOT silently override another responsibility source.

## Impact

Primary implementation paths are listed in `docs/design/workbench-capability-maturation/packages/wp01.md`. Shell adapters perform no business rules, Domain comparisons perform no IO, Data owns SQLite, and Bridge performs requested external operations. Use existing stdlib and platform facilities.

Acceptance uses SYNC-01–08、FS-01–11、LP-01/02 plus RELEASE-01–03. This is a planning artifact. Task completion requires actual evidence and the plan's numeric targets remain unmeasured until implementation.
