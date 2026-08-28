## MODIFIED Requirements

### Requirement: Practice page
The practice page SHALL consume only the non-empty knowledge-point selection
explicitly made in the knowledge graph/list or explicitly replaced by an Agent
after a practice-intent request. It SHALL require exactly one of `exam`,
`flash_card`, or `yes_no` before pulling. A direct `/practice` with no selection
SHALL show an empty handoff state and SHALL NOT auto-select weak items, the full
pool, or a daily-plan item.

#### Scenario: Start without a scope
- **WHEN** the learner opens practice with no selected knowledge points
- **THEN** the page shows the empty handoff state and performs no problem pull

#### Scenario: Select one mode
- **WHEN** the learner chooses a mode and starts with a non-empty scope
- **THEN** every pull uses that scope and mode until the session ends

#### Scenario: Mode has no eligible content
- **WHEN** the selected mode has no explicitly eligible problems in scope
- **THEN** the page shows an empty state and asks for another mode without falling
  back or mixing modes

#### Scenario: Start with a selected mode
- **WHEN** the learner opens a new practice session
- **THEN** no problem is pulled until exactly one rating mode is selected and the
  learner starts with a non-empty scope

#### Scenario: Restore an active card
- **WHEN** the learner refreshes practice in the same tab with an active card
- **THEN** the same titled card and mode return without clearing seen IDs or
  pending unified ratings

#### Scenario: Practice with reveal-then-feedback
- **WHEN** a learner submits an answer in per-problem mode
- **THEN** the card reveals its non-empty solution before rating is accepted

#### Scenario: No repeats in a session
- **WHEN** the page pulls a later problem
- **THEN** every prior seen ID is excluded and no card repeats

#### Scenario: Reject an invalid rating in place
- **WHEN** the learner enters a value outside 1-5
- **THEN** the visible card reports the validation error and no feedback request
  is sent

#### Scenario: End a unified-rating session early
- **WHEN** the learner ends a unified-rating session before exhaustion
- **THEN** completed cards enter unified self-rating without a persistent write
  before each rating submission

### Requirement: Knowledge point selection handoff
The knowledge graph and list SHALL share one explicit tab-scoped selection. View
navigation and reading clicks SHALL not select points; a named handoff action
SHALL carry the selected IDs to practice.

#### Scenario: Share selection across views
- **WHEN** the learner checks points in one knowledge view and opens the other
- **THEN** the same checked scope is visible without adding unselected points

#### Scenario: Agent replaces scope intentionally
- **WHEN** an Agent receives an explicit practice-intent request with new IDs
- **THEN** it replaces the current selection; ordinary conversation leaves the
  selection unchanged
