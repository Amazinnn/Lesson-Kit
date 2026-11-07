## Why

内容与知识点能力成熟化 implements the owner's confirmed use cases from Q006/Q010–Q012/Q039–Q045/Q059–Q062/Q078–Q079/Q084–Q096/Q098/Q103–Q104. The planning baseline covers 103 substantive answers and the supplied learning protocol V3.1. This change has its own observable acceptance boundary in the program tree.

## What Changes

- Knowledge-point queries SHALL filter existing knowledge_type values and search titles, bodies, experience summaries and provenance text. Basic bulk reads SHALL return knowledge-point content and classification. Associated-problem queries SHALL match any selected associated knowledge point and deduplicate problems.
- Within the stated course scope, the Agent SHALL support persistent authorization to create reusable methods and models with explicit applicability, prioritize reuse of existing equivalent knowledge points, and append applicable original-problem associations while retaining valid existing associations.
- A Knowledge-point Chapter Move SHALL support same-course reassignment while preserving stable identity, associated problems, formal relations, experience and learning history. Old identifiers SHALL remain resolvable.
- Bulk direct edits and governed content input SHALL commit independent valid units, retain invalid units and their dependents, and support corrected retries without duplicate content. Explicit successful-batch undo SHALL be unavailable.
- Content preparation SHALL preserve source meaning and specified scope, distinguish structural validity from semantic verification, and exclude unresolved questionable items from the targeted practice set while allowing independent verified items.

## Capabilities

### New Capabilities

- `knowledge-content-operations` — 内容与知识点能力成熟化, with behavior and scenarios in this change's specification.

### Modified Capabilities

- `ai-teacher-bridge` — governed content actions report partial completion and retire successful-batch undo.
- `flash-card` — apply the approved partial-write, retirement or continuity changes while retaining the capability's unrelated behavior.
- `knowledge-figures` — apply the approved partial-write, retirement or continuity changes while retaining the capability's unrelated behavior.
- `micro-quiz-content` — apply the approved partial-write, retirement or continuity changes while retaining the capability's unrelated behavior.
- `workbench-content-governance` — apply the approved partial-write, retirement or continuity changes while retaining the capability's unrelated behavior.

Current requirement-level changes are supplied as MODIFIED/REMOVED deltas where this package changes existing behavior. The reconciliation ledger is `docs/design/workbench-capability-maturation/contract-reconciliation.md`. The first implementation task verifies these complete blocks against the actual checkout and resolves any newly observed drift before code changes. Added capabilities SHALL NOT silently override another responsibility source.

## Impact

Primary implementation paths are listed in `docs/design/workbench-capability-maturation/packages/wp02.md`. Shell adapters perform no business rules, Domain comparisons perform no IO, Data owns SQLite, and Bridge performs requested external operations. Use existing stdlib and platform facilities.

Acceptance uses DATA-01–05、CONTENT-01、FLOW-03 plus RELEASE-01–03. This is a planning artifact. Task completion requires actual evidence and the plan's numeric targets remain unmeasured until implementation.
