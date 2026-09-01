## ADDED Requirements

### Requirement: Layered knowledge relationships

The structure projection SHALL draw each visible relationship as a layered pipe
consisting of a soft shadow, a body, and a narrow highlight. Existing attraction
strength SHALL monotonically control body width and darkness. Weak relationships
SHALL be drawn before strong relationships so strong evidence remains visually
prominent. These visual channels SHALL NOT alter relationship data or learning state.

#### Scenario: Compare weak and strong relationships

- **WHEN** two visible relationships have different attraction strength
- **THEN** the stronger relationship is wider, darker, and drawn above the weaker one

#### Scenario: Relationship remains attached during motion

- **WHEN** connected nodes move through the force simulation
- **THEN** all three layers follow the same straight or curved path

### Requirement: Finite crossing optimization

Each deterministic candidate layout SHALL receive a finite deterministic position-swap
pass before candidates are compared. A swap SHALL be retained only when it improves
the lexicographic layout score: crossings, label collisions, total edge length, then
occupied area. The optimization SHALL schedule no recurring background work.

#### Scenario: Avoidable crossing

- **WHEN** swapping two node positions reduces the crossing count
- **THEN** the improved positions are retained

#### Scenario: Stable result

- **WHEN** the same graph and canvas dimensions are laid out twice
- **THEN** the selected positions and relationship ordering are identical
