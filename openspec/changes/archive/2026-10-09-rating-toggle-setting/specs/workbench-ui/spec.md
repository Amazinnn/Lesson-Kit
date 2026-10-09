## ADDED Requirements

### Requirement: Learner settings in the left rail

The workbench's left column SHALL carry a settings section whose preferences
apply across the practice and paper surfaces. Its first preference SHALL be a
checkbox, 「练习与组卷显示自评」, defaulting to on: self-rating behaves exactly
as before. With it off, no self-rating surface SHALL appear anywhere in the
flow — the rating-timing choice is hidden and not required to start, the
feedback panel never renders, a finished round takes the no-session-end path,
and records label the round 关闭自评. The preference SHALL persist per
workspace in the browser across tabs and restarts, and SHALL take effect at the
next round's start; a running round keeps the mode it started with.

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

## MODIFIED Requirements

### Requirement: Compact per-problem self-rating

In per-problem mode with the learner's show-rating preference on, the revealed
feedback area SHALL use a compact two-surface form: one direct numeric 1–5
input and one optional note surface with the explicit `记录并下一题` action. It
SHALL retain accessible field names and SHALL NOT expand the rating into five
separate choice controls. Rating validation and feedback-write timing SHALL
remain unchanged. With the preference off, the feedback area SHALL NOT appear;
an objective problem's verdict and the revealed solution SHALL be followed by a
single explicit `下一题` action that advances without a feedback write, and an
empty or out-of-range rating SHALL be rejected inline at the input.

#### Scenario: Enter a compact per-problem rating

- **WHEN** the learner reaches self-rating in per-problem mode with rating shown
- **THEN** the feedback area shows a direct numeric 1–5 input and an optional
  note in two compact rounded surfaces
- **AND** one explicit `记录并下一题` action records the feedback and advances
- **AND** no five-choice rating group is rendered

#### Scenario: Reject an invalid compact rating in place

- **WHEN** the learner enters a value outside 1-5 — or leaves the input empty —
  in the compact form
- **THEN** the visible card reports the validation error and no feedback
  request is sent

#### Scenario: Off mode advances without a feedback write

- **WHEN** the preference is off and the learner submits a problem, then presses
  `下一题`
- **THEN** the next unseen problem is shown and no feedback request is sent

#### Scenario: Off mode hides the rating surface entirely

- **WHEN** the preference is off and a problem's solution is revealed
- **THEN** no rating input, note surface, or `记录并下一题` action appears
