## Decisions

Use existing unit savepoints and the shared problem updater. Exact same-chapter authored-field equality is content reuse, not inferred request identity; local keys are never treated as global IDs. Repeated entities are reported as existing, excluded from newly applied counts, and may supply dependencies. Different content is not silently merged; ambiguous equal rows are refused.

Cross-chapter new-KP references connect chapters into dependency components. Within each component insert all KPs before problems/cards; per-unit validation/write failures affect only the item and its dependents. Each applied chapter still owns one batch. A provenance/snapshot failure rolls back the uncommitted component, including copied figures, so no surviving chapter can reference a rolled-back KP; disconnected components continue. No failed operation is automatically retried. Reserve batch IDs in chapter order; rejected chapters may leave gaps. Track new figures before copying, and retain an outer list of successfully staged files until SQLite commit; partial copy and final commit failures remove only newly created files.

Legacy action reconciliation catches only known input-validation errors as terminal invalidity. A Data-owned `UnknownPracticeSet` exception distinguishes an absent target from ordinary publication `FileNotFoundError`. Operational failures propagate, preserving the original pending artifact and confirmation. A later normal recovery revalidates it; existing confirmation checks prevent duplicate writes.

Keep `ok/partial/errors` across both existing public result allowlists. Reuse existing result cards and activity feedback for partial and zero-write failures, retaining actual reasons for the next turn.

Active planning deltas retain their intended text and gain omitted current scenarios verbatim. They are not promoted to implementation facts.

## Verification

Add failing regressions for all five defects, both cross-chapter directions/cycles, dependency insertion failure and late batch failure. Run focused suites, all repository checks and strict validation of all specs/changes. Record implementation evidence separately from independent acceptance.
