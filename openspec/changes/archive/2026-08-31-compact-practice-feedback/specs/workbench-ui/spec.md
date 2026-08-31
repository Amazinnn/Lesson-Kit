## ADDED Requirements

### Requirement: Compact per-problem self-rating

In per-problem mode, the revealed feedback area SHALL use a compact
two-surface form: one direct numeric 1–5 input and one optional note surface
with the explicit `记录并下一题` action. It SHALL retain accessible field names
and SHALL NOT expand the rating into five separate choice controls. Rating
validation and feedback-write timing SHALL remain unchanged.

#### Scenario: Enter a compact per-problem rating

- **WHEN** the learner reaches self-rating in per-problem mode
- **THEN** the feedback area shows a direct numeric 1–5 input and an optional
  note in two compact rounded surfaces
- **AND** one explicit `记录并下一题` action records the feedback and advances
- **AND** no five-choice rating group is rendered

#### Scenario: Reject an invalid compact rating in place

- **WHEN** the learner enters a value outside 1-5 in the compact form
- **THEN** the visible card reports the validation error and no feedback request is sent
