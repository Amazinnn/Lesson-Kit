## Why

诊断、针对性练习与复习接线 implements the owner's confirmed use cases from Q003/Q021/Q028–Q029/Q032–Q041/Q044/Q066/Q074–Q077/Q086–Q091/Q103/Q107，S009. The planning baseline covers 103 substantive answers and the supplied learning protocol V3.1. This change has its own observable acceptance boundary in the program tree.

## What Changes

- The learning workflow SHALL use the stated target, course range and observed evidence to prioritize relevant existing questions and past papers. Supplementary generated items SHALL carry truthful provenance and unresolved questionable mappings SHALL be excluded.
- A focused weakness session SHALL begin with a small diagnostic step. A full new chapter SHALL support distributed coverage that can accumulate fifteen to twenty-five items and shrink with sufficient evidence or limited time. Item count SHALL NOT become a mechanical prerequisite.
- The workflow SHALL distinguish unfamiliar knowledge, inability to apply knowledge, uncertainty, revealed answers and unsupported conclusions. User correction SHALL directly change the next practice arrangement while retaining original answers and observations.
- Help SHALL begin with minimal requested hints and deepen only as needed. The workflow SHALL preserve mainline and return position across interruptions, adjust to actual time and exam goals, and close at natural interaction points.
- Follow-up review SHALL use existing legitimate feedback and scheduling writers and remain adjustable. Appropriate reassessment can reuse recent questions, and independent new items SHALL measure transfer. LLM unavailability SHALL leave independently supported ordinary practice usable.

## Capabilities

### New Capabilities

- `evidence-guided-learning` — 诊断、针对性练习与复习接线, with behavior and scenarios in this change's specification.

### Modified Capabilities

Current requirement-level changes are supplied as MODIFIED/REMOVED deltas where this package changes existing behavior. The reconciliation ledger is `docs/design/workbench-capability-maturation/contract-reconciliation.md`. The first implementation task verifies these complete blocks against the actual checkout and resolves any newly observed drift before code changes. Added capabilities SHALL NOT silently override another responsibility source.

## Impact

Primary implementation paths are listed in `docs/design/workbench-capability-maturation/packages/wp06.md`. Shell adapters perform no business rules, Domain comparisons perform no IO, Data owns SQLite, and Bridge performs requested external operations. Use existing stdlib and platform facilities.

Acceptance uses LEARN-01–05、LP-03–06 plus RELEASE-01–03. This is a planning artifact. Task completion requires actual evidence and the plan's numeric targets remain unmeasured until implementation.
