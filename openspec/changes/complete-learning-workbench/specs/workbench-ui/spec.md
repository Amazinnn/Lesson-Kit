## MODIFIED Requirements

### Requirement: Practice startup

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

### Requirement: Knowledge view sorting

The list view SHALL default to course/chapter source order and SHALL provide
stable ascending and descending sorting for each exposed computed column. The
graph SHALL default to relationship layout and SHALL expose only projections
based on existing data.

#### Scenario: Toggle sort
- **WHEN** the learner activates the same sort key repeatedly
- **THEN** order alternates ascending, descending, ascending without changing
  selection or writing a learning record

