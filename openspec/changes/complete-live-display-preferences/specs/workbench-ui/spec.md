## MODIFIED Requirements

### Requirement: Learner settings in the left rail

The workbench's left column SHALL carry a settings section whose preferences
apply across the practice and paper surfaces. Its first preference SHALL be a
checkbox, 「练习与试卷显示自评」, defaulting to on: self-rating behaves exactly
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

## ADDED Requirements

### Requirement: Question source display preference

The settings view and left rail SHALL expose the same per-workspace self-rating and question-source preferences, synchronize both entry points and browser tabs, and preserve explicit stored values. Question sources SHALL be hidden by default. Turning source display off or on SHALL immediately hide or show an available source on the current question without navigation, restarting or losing inputs. Hiding a source SHALL NOT remove its persisted provenance.

#### Scenario: Source starts hidden and can be toggled on the current question
- **WHEN** a workspace has no explicit source preference and a question has source evidence
- **THEN** the source is hidden by default
- **AND** enabling, disabling and reenabling the preference updates that same question immediately

#### Scenario: Explicit preferences and both entry points agree
- **WHEN** the learner changes either preference in the left rail, settings view or another tab for that workspace
- **THEN** both entry points and the visible question reflect that value without changing another workspace's preferences
