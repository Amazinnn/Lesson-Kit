# delta — workbench-ui（display-redundancy-cleanup）

## MODIFIED Requirements

### Requirement: Redundant state cues

Color SHALL NOT be the only carrier of learning or interaction state. Active
navigation, graph learning states, and errors SHALL retain an outline, position, or
another geometric cue in addition to color. State and status semantics SHALL be
carried by the geometric cue and the host `aria-label`; a surface SHALL NOT add a
separate visible status-text channel that only re-states what the geometric cue and
`aria-label` already express.

#### Scenario: Active navigation

- **WHEN** a navigation item is active
- **THEN** it has both active text styling and a blue structural inset

#### Scenario: Graph state

- **WHEN** a node has a formal learning state
- **THEN** its existing state name remains available while its outline uses the
  corresponding visual role

#### Scenario: Status uses geometry and announcement, not duplicate text

- **WHEN** a milestone, review item, or question-number cell expresses a state
- **THEN** the state is carried by its marker geometry or outline and is announced
  through the host `aria-label`
- **AND** no adjacent visible status text re-states that same state

#### Scenario: A state carries colour and shape

- **WHEN** a Paper status dot, an answer cell, a knowledge-point row or a record
  verdict is shown
- **THEN** it carries a coloured dot in addition to its colour

#### Scenario: A state is not explained in words

- **WHEN** a state is marked on any surface
- **THEN** no explanatory text label is placed beside it to convey that state

Each entry in the left column's review group SHALL carry the redundant state
channel for the state that put it there, and the state SHALL be readable from
the dot's colour **and** its geometry alone. The set of states a review entry
can carry SHALL be fixed and SHALL use the contract words for those states.

#### Scenario: A review entry carries its state

- **WHEN** the learner views the left column's review group
- **THEN** each entry leads with a status dot whose colour and geometry both
  identify why it is there

#### Scenario: The state set is fixed

- **WHEN** the learner sees a review entry's dot
- **THEN** its colour and geometry come from the defined set of review states
  and from no other meaning

## ADDED Requirements

### Requirement: No annotation-type display fields

Practice and shell/navigation surfaces SHALL NOT present annotation-type fields:
provenance or processing metadata addressed to developers or auditors, parenthetical
notes describing how a value was produced, a hardcoded "field-name: value" label
prefix standing in for a natural statement, a restatement of information the same
surface already expresses, a count badge on a group heading, an entry named
identically to its own group heading, or a machine identifier shown where a human
name is the norm. Removing such a field SHALL NOT remove the underlying data,
capability, or persisted provenance.

#### Scenario: Question-number cell carries no extra label

- **WHEN** a learner hovers or focuses a question-number cell that exposes a
  sub-question status card
- **THEN** the cell presents no additional small-text label whose only purpose is to
  describe or restate that status

#### Scenario: Solution paper omits provenance metadata

- **WHEN** a solution or grading view is rendered for a learner
- **THEN** it presents the learner-facing answer, reference, and feedback without a
  developer-facing provenance or processing-origin metadata row

#### Scenario: Answer label carries no processing annotation

- **WHEN** a learner's extracted answer is shown in a solution view
- **THEN** its label names the field without a parenthetical note about the internal
  mechanism that produced it

#### Scenario: Verdict statement is consistent across practice flows

- **WHEN** a practice flow renders a correct or incorrect verdict
- **THEN** it states the verdict as a natural statement and does not prefix it with a
  "field-name:" label, and the wording matches across practice flows

#### Scenario: Source evidence shows value without a field-name prefix

- **WHEN** question-source display is enabled and a source is shown on the current
  question
- **THEN** the source evidence is presented without a hardcoded "field-name:" prefix
- **AND** the existing question-source visibility preference and persisted provenance
  are unchanged

#### Scenario: Session entries omit the metadata row

- **WHEN** an Agent session list renders an entry
- **THEN** the entry presents its status dot, title, and preview without a separate
  metadata line restating provider, date, or running state

#### Scenario: Group headings carry no count badge

- **WHEN** a navigation group heading is rendered
- **THEN** it presents no count badge or other figure adjacent to the heading text

#### Scenario: Settings entry is not named identically to its group

- **WHEN** a settings group heading and its entry are rendered
- **THEN** the entry uses a concrete name rather than repeating the group heading text

#### Scenario: Cards and headers omit annotation kickers and machine ids

- **WHEN** a card, approval, artifact, or workspace header is rendered
- **THEN** it does not present an annotation kicker or "field-name: value" label that
  restates the adjacent title, and it shows a human-facing name rather than a machine
  identifier
