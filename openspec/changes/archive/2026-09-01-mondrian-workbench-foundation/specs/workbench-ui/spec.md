## ADDED Requirements

### Requirement: Soft Mondrian visual foundation

The workbench SHALL use warm paper surfaces, dark structural rules, and restrained
blue, yellow, and red accents. Blue SHALL represent primary action and selection,
yellow SHALL represent current/review emphasis, and red SHALL represent needs-work
or failure emphasis. Most screen area SHALL remain paper or neutral.

#### Scenario: Ordinary workbench page

- **WHEN** a learner opens any core page
- **THEN** the shell is structured by paper surfaces and dark rules with only compact
  red, yellow, and blue accents

#### Scenario: Primary action

- **WHEN** a primary action is enabled
- **THEN** it is blue with a dark outline and remains identifiable by its label

### Requirement: Redundant state cues

Color SHALL NOT be the only carrier of learning or interaction state. Active
navigation, graph learning states, and errors SHALL retain text, outline, position,
or another geometric cue in addition to color.

#### Scenario: Active navigation

- **WHEN** a navigation item is active
- **THEN** it has both active text styling and a blue structural inset

#### Scenario: Graph state

- **WHEN** a node has a formal learning state
- **THEN** its existing state name remains available while its outline uses the
  corresponding visual role
