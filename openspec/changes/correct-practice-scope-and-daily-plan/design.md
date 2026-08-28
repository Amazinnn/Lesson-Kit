## Scope handoff

The knowledge view (graph and list) owns the practice scope. Explicitly checked
knowledge-point IDs are stored in the existing tab-scoped `sessionStorage` and
shared by both views. Clicking a node or row for reading does not select it.
The practice page consumes this state; it does not derive scope from the weak
rail, the full pool, a daily queue, or a previous session.

An Agent replacement is a distinct intent-bearing operation. The request must
state that the user wants to practice and provide the replacement IDs. The
result replaces the current selection atomically, with no append or hidden
normalization. Ordinary discussion, navigation, and plan explanation are
read-only with respect to selection.

## Practice modes

The start card accepts one of `exam`, `flash_card`, or `yes_no`. The selected
mode is fixed for the session and is sent with each pull together with the
selected scope and `exclude_ids`. If the chosen mode has no explicitly
eligible content, the UI shows an empty state and asks the learner to choose a
different mode; it never silently falls back or mixes modes. Existing unmarked
problems remain eligible for `exam` only.

## Plan truthfulness

Planning reads real persisted long-term and stage goals, coverage, progress,
deadlines, and available formal content. A goal card is shown only for a real
goal and defaults to title, coverage progress, and deadline; description and
scope are on demand. The daily queue is independent, coarse-grained, and has
at most three items. With no goals, it reports due/available work without
creating a fictional course goal, duration, or mastery claim. Queue handoff
seeds the same explicit selection state before the mode picker.

All selection, navigation, drafting, skipping, and plan viewing remain
zero-write. Only the existing explicit rating/content/state operations create
learning records.

