## MODIFIED Requirements

### Requirement: Stable graph interaction

The graph SHALL remain fully static after the force simulation settles. It SHALL reheat only after a learner interaction or viewport/model change such as dragging, filtering, focusing, resizing, or changing global gravity. It SHALL NOT apply a continuous idle breathing offset.

#### Scenario: Settled graph is quiet

- **WHEN** the graph simulation reaches its stable threshold and the learner does nothing
- **THEN** node and label positions remain unchanged and no recurring animation loop is scheduled

### Requirement: Adjustable graph compactness

The existing 0–100 in-memory center-gravity control SHALL provide a visibly stronger range, with a maximum coefficient of approximately `0.00351` and default value 30. Higher values SHALL draw all nodes more toward the graph center and lower values SHALL let them spread, regardless of whether nodes have connecting edges. The value SHALL NOT be persisted or written to learning records.

#### Scenario: Increase graph gravity

- **WHEN** the learner raises the gravity control
- **THEN** the current simulation reheats with a stronger center force and the graph remains otherwise unchanged

#### Scenario: Lower graph gravity

- **WHEN** the learner lowers the gravity control
- **THEN** the current simulation reheats with a weaker center force and unconnected nodes may spread farther apart
