## MODIFIED Requirements

### Requirement: Learner settings in the settings view

The workbench's left column SHALL carry a single 「设置」 entry to the settings view, without inline preference controls. The settings view SHALL contain running-send behavior, self-rating visibility and source visibility alongside appearance preferences, retaining their existing workspace browser storage and defaults.
The self-rating preference SHALL be a checkbox, defaulting to on: self-rating behaves exactly
as before. With it off, no self-rating surface SHALL appear anywhere in the
flow — the rating-timing choice is hidden and not required to start, the
feedback panel never renders, a finished round takes the no-session-end path,
and records label the round 关闭评价. The preference SHALL persist per
workspace in the browser across tabs and restarts, and SHALL immediately hide or show eligible self-rating controls in an open ordinary Paper, including a Paper started with rating off. Answer locking, navigation, objective grading and the recorded round mode SHALL remain unchanged. Legacy card/session timing retains its existing round mode.

#### Scenario: The preference survives a restart

- **WHEN** the learner turns the checkbox off and reopens the workbench later
- **THEN** the checkbox is still off and a new round starts without any
  self-rating surface

#### Scenario: Off removes every rating surface

- **WHEN** a round starts with the preference off
- **THEN** the rating-timing fieldset is absent, no feedback panel appears
  during the round, the round ends without the session-end view, and records
  show 关闭评价 for it

#### Scenario: On keeps today's behavior

- **WHEN** the preference is on
- **THEN** the rating-timing choice, per-problem rating, and session-end
  unified rating behave as before

#### Scenario: Reenable optional self-rating during a Paper

- **WHEN** an ordinary Paper started with self-rating off and the learner turns the display preference on after submitting an eligible item
- **THEN** the existing item offers optional self-rating without restarting, duplicating an Attempt or changing its answer lock
