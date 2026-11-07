## Why

The current authored-content mirror supports a limited entity projection, while the owner needs course content and learning state to survive ordinary file transfer between installations. Papers, full asset CRUD, usable version coordination and observable recovery must be planned together to preserve existing learning continuity.

## What Changes

Planning draft grounded in the 100 effective answers recorded through Q104 and revisions S001–S009 in docs/design/workbench-capability-maturation/decisions.md. The owner-provided learning protocol V3.1 is mapped in docs/design/workbench-capability-maturation/learning-protocol-v3.1.md. Additional teaching-continuity payload scope remains unresolved. Design, delta specs and tasks are not yet complete.

- Extend CLI file exchange to course-managed content, Papers, referenced images and confirmed-persisted learning state. Original materials are optionally included with size and missing-file reporting. Conversation continuation is a separate work package.
- Receive additions, edits and explicit deletions through governed validation and mutation boundaries. A missing entity file is reported and cannot silently authorize deletion.
- Automatically coordinate unambiguous one-sided changes in one normal operation. Show genuine two-sided differences and permit explicit side selection, including a choice for a batch of conflicts.
- Preserve independent valid successes when some inputs are invalid. Failed dependency groups retain their prior state and reports identify successful, blocked and failed assets.
- Preserve other items' progress and drafts when deleted problems leave current Papers, and retain historical learning evidence. Knowledge-point deletion requires explicit reassignment or detachment of related problems. Restored problems do not silently rejoin previous Papers.
- Merge independently added attempt records by their actual identities without duplication. Merge independent changes to different questions' unfinished drafts. Show genuine same-question draft conflicts and deletion-versus-concurrent-edit conflicts for side selection.
- Exchange confirmed-persisted, non-sensitive learning preferences such as submission granularity and reveal timing through their actual writers and consumers.
- Provide one normal CLI operation that coordinates the configured Git checkout, file exchange, commit and push. Preserve file-only use independently of Git transport. Validate local exchange and remote publication as distinct outcomes.
- Schedule the same CLI hourly through the Windows task scheduler for all registered courses with configured media. Successful runs are quiet. A conflict needing side selection produces one short system notification and remains unresolved until a side is supplied.
- Apply S008 to relevant operations by retiring explicit successful-batch undo and approval gates. Actions previously requiring approval proceed directly. Independent valid changes complete while invalid items and their dependents retain prior state. Conflict-side selection supplies missing operation input.
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

Receiving and course-identity behavior are decided by Q017/Q018. Detailed payload/schema compatibility, stable cross-device record identities, migration of persisted preferences and numeric benchmark baselines still require design and evidence. The new learning protocol adds candidate goal/resource/teaching-continuity documents whose first-phase exchange scope is pending. This draft is incomplete for implementation.


## Scope refinement through Q104 and the V3.1 reference

This change is the immediate implementation priority after planning, within the whole-project maturation program. Keep only the latest complete synchronization result. S008 supersedes the previous successful-batch rollback workflow. Content mistakes are repaired through ordinary scoped edits. The first delivery includes complete governed data exchange and Git transport with hourly scheduling. Frontend and new teaching-engine work have separate packages.

The V3.1 reference motivates a portable learning context made of goals, sources, demonstrated understanding, corrected misconceptions, references and teaching position. Existing goals, experience and evidence modules are reuse candidates. The owner has authorized reference analysis. Whether additional teaching-continuity files join this change is an explicit pending scope decision in the planning tree. The reference's approval cards, automatic fallback and terminology do not become project contracts by being included in an attachment.
