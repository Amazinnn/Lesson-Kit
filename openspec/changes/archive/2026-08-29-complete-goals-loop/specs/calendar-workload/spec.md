## ADDED Requirements

### Requirement: Goal lifecycle management

The practice page study-arrangement region SHALL manage the full goal
lifecycle: creating goals (existing flow unchanged), editing an existing
goal's title / kind / deadline / description through the same form
(pre-filled, submitted as an update), and deleting a goal behind an explicit
confirmation. Edits and deletions SHALL take effect on the goal cards and
calendar immediately. Goal ids SHALL NOT be shown as primary text. The
calendar-and-workload view itself stays read-only.

#### Scenario: Edit a goal in place

- **WHEN** the learner opens a goal card's edit action and the form loads
  with that goal's current fields
- **THEN** saving submits exactly the changed goal, and the card and month
  grid reflect the update without a full page rebuild

#### Scenario: Delete with confirmation

- **WHEN** the learner activates a goal card's delete action and confirms
- **THEN** the goal is removed and disappears from the cards and the calendar;
  declining the confirmation leaves everything unchanged

#### Scenario: Cancel an edit

- **WHEN** the learner cancels a loaded edit
- **THEN** the form returns to its empty creation state
