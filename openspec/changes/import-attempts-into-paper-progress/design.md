## Context

`problem_attempts` carries no `paper_id`. A Paper's execution identity lives in
two places:

- the single `active_practice` row and its `active_practice_items` when the Paper
  is selected;
- `paper_state.checkpoint_json` when the Paper is parked.

`practice_runs` is an archive written only when a run completes. `attempts apply`
currently inserts attempts and optional feedback but never touches either
execution store, so imported answers cannot appear in a Paper's progress.

The change keeps that data model. It adds a binding step rather than a new
`paper_id` column, a new attempt table, or a second progress store.

## Decisions

### D-1: Manifest-level `paper_id`, not per-item paper references

One manifest binds one Paper. Every item must belong to that Paper's current
ordered items. Cross-Paper batches are split by the caller. This keeps
validation, idempotency, and the binding transaction single-purpose.

Rejected: per-item `paper_id` (allows mixed batches but multiplies conflict and
idempotency states), a CLI-only `--paper` flag (the manifest is the durable
artifact an Agent retries), and no binding (does not solve the request).

### D-2: Binding chooses active, parked, or new in that order

```
active_practice.source_ref == paper_id  -> update active_practice_items
paper_state.checkpoint_json exists      -> update checkpoint
otherwise                               -> create checkpoint
```

A Paper that is not selected is never activated by an import. The selected Paper
is never paused or modified. This is the only way to import into an arbitrary
Paper without disturbing the learner's current session.

A new checkpoint is a valid parked execution: it allocates an `execution_id`
from `practice_execution_ids`, stores the current `paper_generation`, uses
`reveal_timing = on_submit`, and contains the full ordered item list with
`content_revision`. It does not insert `active_practice` and does not write
`practice_runs`. Saving or importing answers is not starting a Practice Run.

### D-3: Re-binding appends instead of overwriting

The attempt table is append-only. If the target item is already `answered` or
`stuck`, the import inserts a new attempt and changes only the item's
`attempt_id` and `state`. The previous attempt remains readable. This matches
the existing rule that re-answering appends an Attempt and the existing Paper
review exception that edits only the linked evaluation row, not history.

Binding clears a pending answer/choice draft and a stuck mark. It does not
invent `reference_viewed = true`: importing a paper answer does not prove the
learner viewed the reference material. The existing reference-view fact, if
any, is preserved.

### D-4: Completion follows the existing execution mode

- Legacy execution (`reveal_timing IS NULL`): once no item is pending, archive
  `completed` and clear the active execution, as `mark` already does.
- `per_item` / `on_submit`: leave the execution in place; the learner must submit.

The import performs one completion check after all bindings, not per item, so a
batch cannot archive halfway through itself.

### D-5: Ungraded import changes Paper execution progress only

`problem_progress`, `learning_current_state`, `learner_signals`, and
`review_schedule` move only through the existing rating flow. An import without
`rating` changes `active_practice_items.state` / checkpoint item state and the
`attempt_id` link, nothing else. This is why the `review-workbench` wording is
narrowed to *learning* progress.

### D-6: `papers append` is a separate governed action

Manual membership/order edits continue to reset unfinished progress after a
confirmed preview. `papers append` is additive: it appends one existing problem
at the end, increments the Paper generation, updates the active or parked
execution's `paper_generation`, and adds one pending item. No existing position
or state moves, so no renumbering is needed.

It is idempotent. A repeated append returns `already_present` without writing.
This makes the Agent's three-step repair safe to retry after a lost response.

Rejected: inserting at the original exam position (requires renumbering active
items, checkpoints, browser positions, and cursor, with a much larger stale-write
surface), and automatic problem creation inside import (content generation,
knowledge-point choice, and source evidence are governed content writes, not
import side effects).

### D-7: `paper_generation` bump is the stale-write boundary

`papers append` increments `paper_state.generation`. Any open browser session
still carrying the previous generation is rejected by the existing
`paper_progress.guard` and must reload. This is the same protection used by
content and structure changes; the change does not add a bypass.

## Contract reconciliation

- `review-workbench` "Durable attempt records for every surface": "progress" is
  changed to "learning progress"; Paper execution progress is explicitly allowed
  through Paper-bound import.
- `agent-assisted-practice-records` "Agent transcription and optional learning
  rating": the no-rating clause is narrowed to learning projections; Paper
  execution progress may change with `paper_id`.
- `practice-set-export` "Paper is the Practice Run boundary" and
  `review-workbench` "Re-assembly after wrong results": the prohibition on
  extending a running Paper in place is scoped to assembly-driven extension.
  Explicit repair append of a missing source problem is the named exception.
- `practice-set-export` "Saved Paper updates preserve container identity" keeps
  its reset rule for manual membership/order edits. `papers append` is a separate
  requirement and does not use that path.

### Reconciliation addendum (2026-11-09, independent review P2)

The delta scenario "Legacy last item archives" originally said "a legacy Paper"
without scoping active/parked, while D-4 and the implementation archive only the
selected (active) execution. Adjudicated per D-4 (the change's own decision):
the requirement and scenario now scope legacy archiving to the selected
execution, and state that the import does not archive a parked execution — a
parked legacy Paper keeps its checkpoint and completes through the existing
legacy rules on later learner action (verified: resume of a fully answered
parked legacy checkpoint does not archive by itself).

## Risks

- An import that fills the last pending item of a legacy selected (active) Paper
  archives it immediately. This is the existing legacy completion rule, not a new
  one; the manifest's `paper_id` makes the target explicit. A parked legacy Paper
  keeps its checkpoint (see the reconciliation addendum).
- Imported attempts get the import time, not the paper-answering time. The
  calendar and schedule will show the import day. Backdating is out of scope.
- Import-created parked progress does not create a records-center run card until
  submission. The saved Paper list shows the progress; this is the same behavior
  as a manually paused Paper.
- The missing-problem repair depends on governed content creation. If the
  learner's source does not establish the problem's content or knowledge point,
  the Agent must stop and ask instead of inventing.
