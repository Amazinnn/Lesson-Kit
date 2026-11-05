## Why

The current authored-content mirror supports a limited entity projection, while the owner needs course content and learning state to survive ordinary file transfer between installations. Papers, full asset CRUD, usable version coordination and observable recovery must be planned together to preserve existing learning continuity.

## What Changes

Planning draft grounded in Q001–Q016 and S001 in docs/design/workbench-capability-maturation/decisions.md. Further decisions remain pending; this proposal does not authorize implementation.

- Extend CLI file exchange to course-managed content, Papers, referenced images and confirmed-persisted learning state. Original materials are optionally included with size and missing-file reporting. Conversation continuation is a separate work package.
- Receive additions, edits and explicit deletions through governed validation and mutation boundaries. A missing entity file is reported and cannot silently authorize deletion.
- Automatically coordinate unambiguous one-sided changes in one normal operation. Show genuine two-sided differences and permit explicit side selection, including a choice for a batch of conflicts.
- Preserve independent valid successes when some inputs are invalid. Failed dependency groups retain their prior state and reports identify successful, blocked and failed assets.
- Preserve other items' progress and drafts when deleted problems leave current Papers, and retain historical learning evidence. Knowledge-point deletion requires explicit reassignment or detachment of related problems. Restored problems do not silently rejoin previous Papers.
- Retain existing capabilities and entry points. Existing authored-content projection semantics remain identifiable; learner-state exchange receives its own explicit field and file contract.
- Validate through rule/storage tests, process-level failure scenarios, actual CLI and browser operations, and measured user-task benchmarks. Agents execute all delegable acceptance, including real LLM calls through free testing APIs.

## Capabilities

### New Capabilities

- `file-course-sync` — governed file exchange of course content and persisted learning state, including dependency handling, CRUD, conflict decisions and observable results.

### Modified Capabilities

- `workbench-content-governance` — reconcile file-originated content creation, modification and deletion with existing validation, history and batch boundaries.
- `practice-set-export` — exchange Paper definitions and dependencies while preserving or explicitly coordinating learning continuity.
- `knowledge-figures` — include referenced image bytes and expose missing assets through file-exchange results.
- `review-workbench` — reconcile restored workspace learning state and current practice with existing lifecycle and compatibility contracts.

The exact requirement-level delta ownership will be confirmed by contract reconciliation before writing complete delta specs.

## Impact

Primary owners are workbench CLI adapters, Data mutation/file-exchange modules and pure Domain comparison rules. SQLite migrations, if required, use existing ensure boundaries. No remote synchronization service is required; GitHub is an optional external transport medium.

Reconcile GLOSSARY, DATA_MODEL, FILE_CONTRACT, ARCHITECTURE, PRODUCT-MANUAL, ACTION-GRAPH, interface surfaces and Agent-visible contracts according to their responsibilities. Existing active lifecycle and mirror changes require an explicit overlap ledger before implementation.

Identity handling, receiving into an existing installation, rollback after subsequent learning, exact payload/schema compatibility and numeric benchmark targets remain under discussion. This draft is incomplete for implementation.
