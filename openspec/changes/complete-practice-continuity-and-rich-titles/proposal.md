## Why

未完成练习与标题呈现 implements the owner's confirmed use cases from Q048–Q050/Q052/Q056–Q058/Q060–Q061/Q064，S004/S005/S008. The planning baseline covers 103 substantive answers and the supplied learning protocol V3.1. This change has its own observable acceptance boundary in the program tree.

## What Changes

- Every unfinished Paper execution SHALL be discoverable at practice start without a count or age eviction limit. Reopening a Paper SHALL continue the same unfinished execution by default. Explicit clear SHALL remove only that execution and its drafts.
- All content-title display surfaces SHALL support the existing safe Markdown and LaTeX feature set. Editing, renaming, cancellation and unchanged saving SHALL preserve the authored source rather than rendered DOM text.
- Default startup SHALL restore the last course and recoverable learning position and explicit targets SHALL take precedence. Unaffected practice SHALL continue during content edits without input loss.

## Capabilities

### New Capabilities

- `practice-continuity-presentation` — 未完成练习与标题呈现, with behavior and scenarios in this change's specification.

### Modified Capabilities

Current requirement-level changes are supplied as MODIFIED/REMOVED deltas where this package changes existing behavior. The reconciliation ledger is `docs/design/workbench-capability-maturation/contract-reconciliation.md`. The first implementation task verifies these complete blocks against the actual checkout and resolves any newly observed drift before code changes. Added capabilities SHALL NOT silently override another responsibility source.

## Impact

Primary implementation paths are listed in `docs/design/workbench-capability-maturation/packages/wp05.md`. Shell adapters perform no business rules, Domain comparisons perform no IO, Data owns SQLite, and Bridge performs requested external operations. Use existing stdlib and platform facilities.

Acceptance uses PRACTICE-01–04 plus RELEASE-01–03. This is a planning artifact. Task completion requires actual evidence and the plan's numeric targets remain unmeasured until implementation.
