## MODIFIED Requirements

### Requirement: Practice page

The practice page SHALL require a non-empty selected knowledge-point scope, one
content mode (`exam`, `flash_card`, or `yes_no`), and one rating mode
(`immediate` or `batch`) before pulling a problem. The content mode SHALL remain
fixed for the session and the rating mode SHALL determine only when feedback is
written.

#### Scenario: Missing mode
- **WHEN** scope, content mode, or rating mode is missing
- **THEN** start remains disabled and no pull request is sent

#### Scenario: Unified rating
- **WHEN** the learner selects `batch` and submits several answers
- **THEN** answers remain in the tab session and no feedback is written until
  the final review explicitly saves a rating

#### Scenario: Structured choices
- **WHEN** a selected problem supplies valid options and a correct option id
- **THEN** the card renders those options with an accessible answer control
- **AND** missing options never cause a mode fallback

#### Scenario: Start with a selected mode
- **WHEN** the learner opens a new practice session
- **THEN** no problem is pulled until exactly one rating mode is selected and the learner starts

#### Scenario: Restore an active card
- **WHEN** the learner refreshes practice in the same tab with an active card
- **THEN** the same titled card and mode return without clearing the seen ids or pending unified ratings

#### Scenario: Practice with reveal-then-feedback
- **WHEN** a learner submits an answer in per-problem mode
- **THEN** the card reveals its non-empty solution before rating is accepted

#### Scenario: No repeats in a session
- **WHEN** the page pulls a later problem
- **THEN** every prior seen id is excluded and no card repeats

#### Scenario: Reject an invalid rating in place
- **WHEN** the learner enters a value outside 1-5
- **THEN** the visible card reports the validation error and no feedback request is sent

#### Scenario: End a unified-rating session early
- **WHEN** the learner ends a unified-rating session before exhaustion
- **THEN** completed cards enter unified self-rating without a persistent write before each rating submission

## ADDED Requirements

### Requirement: Knowledge view sorting

The list view SHALL default to course/chapter source order and SHALL provide
stable ascending and descending sorting for each exposed computed column. The
graph SHALL default to relationship layout and SHALL expose only projections
based on existing data.

#### Scenario: Toggle sort
- **WHEN** the learner activates the same sort key repeatedly
- **THEN** order alternates ascending, descending, ascending without changing
  selection or writing a learning record
