## Context

`feedback_events` stores one evaluation as `item_type`, `item_id`, `rating` (1–5
or null), `note`, optional `attempt_id`, and `created_at`. Browser Paper review
already updates the linked problem evaluation in place using expected rating and
note as an optimistic-concurrency guard. The Agent CLI can create evaluations
through `attempts apply` and `feedback`, and can replace Agent-recorded attempts
through `attempts correct`, but it cannot edit or delete an arbitrary evaluation
row, including one the learner wrote in the browser.

The Chinese product term is 「自评」, while the record is now written by both the
learner and the Agent. The rename is a copy change, not a schema change.

## Decisions

### D-1: Rename is Chinese-only

User-visible Chinese copy, live docs, and live spec copy change from 「自评」 to
「评价」. English identifiers (`rating`, `self_rating`, `feedback_events`,
`rating_mode`, DOM ids, localStorage keys, API fields) do not change. The
GLOSSARY entry becomes 「评价 / Self-Rating」 with 「自评」 recorded as the old
name. Historical archives, changelogs, audits, and status snapshots are not
rewritten.

PRODUCT-MANUAL §7.4 previously used 「评价词汇」 for the three learning-status
words; that heading becomes 「学习状态词汇」 so it does not collide with the
renamed evaluation field.

### D-2: One evaluation row, two possible writers

A problem evaluation is the `feedback_events` row linked to the attempt. The
learner writes it in the browser; the Agent writes or edits the same row through
the CLI. The row does not gain an author column. The existing contract against a
grader-identity field is preserved; the Agent acts on the learner's explicit
request.

`feedback add --attempt-id` refuses when that attempt already has an evaluation
and returns the existing event id. This keeps “the same segment of evaluation”
singular for problem attempts instead of appending a second current row.

### D-3: Read-before-write is the only precondition

`feedback update` and `feedback delete` require:

- `--expected-rating 1-5|none`
- `--expected-note <text>` (empty string for no note)

The values come from `feedback get` / `feedback list`. If either differs from the
current row, the command returns a conflict (exit 2 with an error; HTTP 409 is
the equivalent for browser paths) and writes nothing. This is the same
optimistic-concurrency pattern the browser Paper review already uses, applied to
both writers.

`update` accepts new `--rating` and/or `--note`. Omitting both is an error.
Clearing a rating is done by deleting the evaluation; `update` does not accept a
null rating. `--note ""` clears the note.

### D-4: In-place edit and hard delete do not replay projections

`update` rewrites only `feedback_events.rating/note`; `delete` removes only that
row. Signals, current state, problem progress, and schedule are not replayed.
This matches the existing Paper review edit boundary: the evaluation record
changes, the previously derived learning projection does not. A caller that
needs the exact withdraw-and-recompute behavior uses `attempts correct` on an
Agent-recorded attempt.

The consequence is explicit and documented: changing a score through
`feedback update` will not by itself move mastery or the next due date.

### D-5: The Agent may choose the score

When the learner asks the Agent to record, import, or manage an evaluation, the
Agent may choose the 1–5 value without asking the learner for a number. Ordinary
tutoring that does not request a record remains zero-write. The “explicit learner
request” boundary is unchanged; what changes is that the request does not have to
supply the score.

### D-6: CLI backward compatibility

`lesson-kit feedback <workspace> --item problem --id <id> --rating 3` continues to
work as `add`. The new positional action is optional and defaults to `add`.
`list` and `get` print JSON; `add` keeps its existing human-readable change
lines.

## Contract reconciliation

- `review-workbench` `Flexible feedback` is extended, not replaced: the same row
  can be edited by either writer, expected values guard concurrency, and neither
  edit nor delete replays projections.
- `agent-assisted-practice-records` gains a new evaluation-management
  requirement; the existing `attempts` correction requirement remains the
  whole-attempt replacement path.
- `ai-teacher-bridge` gains an Agent-evaluation requirement; the existing
  learner-requested attempt requirement remains unchanged.
- `workbench-ui` changes only the Chinese label 「关闭自评」 → 「关闭评价」.

## Risks

- Hard delete is destructive and leaves the learning projection derived from the
  deleted row in place. The user accepted this; the spec and product manual say
  so explicitly.
- A browser edit and an Agent edit can race. The expected-value guard makes one
  side fail and refresh instead of silently overwriting the other.
- `feedback update` changes the evaluation note, not the attempt's transcription
  note. `attempts correct` changes both the attempt and its linked evaluation.
  The product manual must state the difference.
- The rename touches active visual-language copy tables. Those need a manual pass;
  archived/changelog/status text is deliberately left as written.
