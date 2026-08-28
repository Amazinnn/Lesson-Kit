## MODIFIED Requirements

### Requirement: Forgetting-curve scheduling as background

The system SHALL maintain per-item scheduling state (repetitions, ease,
interval, due date) updated on practice results, and SHALL surface due items as
reminders. Scheduling SHALL influence ordering only; it SHALL never hide,
lock, or refuse items. Due items SHALL be surfaced on the workspace home
(practice page) inside the merged today list, each with a human-readable
reason; a separate review page SHALL NOT be used.

#### Scenario: Due items are reminded

- **WHEN** the workspace home is opened
- **THEN** it shows a due-items summary computed from scheduling state, alongside (never instead of) the weak-point list

#### Scenario: Schedule state updates after practice

- **WHEN** a problem result is recorded
- **THEN** its repetitions, ease, interval, and due date are updated in the scheduling table

### Requirement: Directional card practice for memory recall

A knowledge point with `knowledge_type = memory-recall` SHALL be practiced as a
card: prompt on the front, recall, reveal on the back. Cards SHALL carry a
direction (for example English-to-Chinese and Chinese-to-English), each
direction is a distinct learning action with its own schedule entry, and
related knowledge points connected by `contrasts` or `variant_of` edges SHALL
be shown alongside during card practice. The card session SHALL be offered as
an optional light session inside the Flash Card or Yes/No modes when the
selected scope contains due directional rows; it SHALL never be required, and
rating a card SHALL record through the feedback path with the row's direction.

#### Scenario: Two directions schedule independently

- **WHEN** a memory-recall knowledge point is practiced in both directions
- **THEN** each direction has its own schedule state and due date, and practicing one direction does not advance the other

#### Scenario: Confusable words are shown together

- **WHEN** a card's knowledge point has a `contrasts` neighbor
- **THEN** the neighbor is displayed on the card page as a compare hint, without merging the two into one item

#### Scenario: Offered, never required

- **WHEN** a selected scope contains due directional rows and the learner starts
  the Flash Card or Yes/No mode
- **THEN** the workbench offers an optional first flip over the due cards and
  proceeds with the normal mode flow if declined

## ADDED Requirements

### Requirement: Scoped include filter

A scoped pull MAY carry `include_ids`; returned problems SHALL then be
restricted to those identifiers within the requested knowledge-point scope.
Combining `include_ids` with the unscoped `all` mode SHALL be rejected, and
the shortage report SHALL keep reflecting the remaining unfilled demand.

#### Scenario: Pull one due problem

- **WHEN** a scoped pull carries `include_ids` with one durable problem id
- **THEN** only that problem is returned

#### Scenario: Include filter with unscoped all mode

- **WHEN** a pull carries `include_ids` together with `mode: all`
- **THEN** the request is rejected with 400 and nothing is pulled

### Requirement: Directional feedback key

Feedback MAY carry an optional `direction`; when present, the rating SHALL
update the schedule row keyed by `(item_type, item_id, direction)` while
signal, event, progress, and current-state semantics SHALL remain unchanged.

#### Scenario: Reverse card rating

- **WHEN** feedback for a knowledge point carries `direction: reverse` with
  rating 4
- **THEN** only the reverse schedule row advances and the forward row stays
  unchanged
