## MODIFIED Requirements

### Requirement: Directional schedule entries

Each direction (for example English-to-Chinese and Chinese-to-English) of a
memory-recall knowledge point SHALL be a distinct learning action with its own
schedule entry, and practicing one direction SHALL NOT advance the other. The
workbench SHALL expose direction controls only inside a learner-selected Flash
Card practice session. It SHALL NOT provide a standing card-session page,
system-initiated card prompts, or a direction prompt when another practice mode
was selected.

#### Scenario: Two directions schedule independently

- **WHEN** a memory-recall knowledge point is practiced in both directions
- **THEN** each direction has its own schedule state and due date, and practicing one direction does not advance the other

#### Scenario: No system-initiated card session

- **WHEN** the learner starts a non-flash-card practice mode with due directional rows in scope
- **THEN** the workbench starts the requested mode directly without offering or requiring a card session

#### Scenario: Explicit flash-card direction controls

- **WHEN** the learner explicitly selects Flash Card practice
- **THEN** direction controls belong to that session and do not create a fourth navigation page
