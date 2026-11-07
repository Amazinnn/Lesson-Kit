## MODIFIED Requirements

### Requirement: Learner settings in the settings view

The workbench's left column SHALL carry a single 「设置」 entry to the settings view, without inline preference controls. The settings view SHALL contain running-send behavior, self-rating visibility and source visibility alongside appearance preferences, retaining their existing defaults and browser mirror. Explicit non-sensitive course learning preferences SHALL also be confirmed through the course preference writer and restored from received course files. Device appearance and Provider credentials remain owned by their existing storage contracts.
The self-rating preference SHALL be a checkbox, defaulting to on: self-rating behaves exactly
as before. With it off, no self-rating surface SHALL appear anywhere in the
flow — the rating-timing choice is hidden and not required to start, the
feedback panel never renders, a finished round takes the no-session-end path,
and records label the round 关闭自评. The preference SHALL persist per
workspace in the browser across tabs and restarts, and SHALL immediately hide or show eligible self-rating controls in an open ordinary Paper, including a Paper started with rating off. Answer locking, navigation, objective grading and the recorded round mode SHALL remain unchanged. Legacy card/session timing retains its existing round mode.

#### Scenario: The preference survives a restart

- **WHEN** the learner turns the checkbox off and reopens the workbench later
- **THEN** the checkbox is still off and a new round starts without any
  self-rating surface

#### Scenario: Off removes every rating surface

- **WHEN** a round starts with the preference off
- **THEN** the rating-timing fieldset is absent, no feedback panel appears
  during the round, the round ends without the session-end view, and records
  show 关闭自评 for it

#### Scenario: On keeps today's behavior

- **WHEN** the preference is on
- **THEN** the rating-timing choice, per-problem rating, and session-end
  unified rating behave as before

#### Scenario: Reenable optional self-rating during a Paper

- **WHEN** an ordinary Paper started with self-rating off and the learner turns the display preference on after submitting an eligible item
- **THEN** the existing item offers optional self-rating without restarting, duplicating an Attempt or changing its answer lock

#### Scenario: Received course preferences win over an old browser mirror

- **WHEN** a course with confirmed learning preferences is received and opened in a browser with stale workspace preferences
- **THEN** new practice uses the received saved values while any existing execution retains its frozen reveal timing

#### Scenario: Preference persistence fails

- **WHEN** the course preference writer rejects or cannot persist a change
- **THEN** the UI reports a minimal save failure and the value is not described as confirmed or included as saved export data
