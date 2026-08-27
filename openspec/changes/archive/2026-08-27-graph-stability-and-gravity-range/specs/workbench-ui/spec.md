## MODIFIED Requirements

### Requirement: Living graph motion and readable labels

The graph SHALL remain fully static after the force simulation settles. It SHALL reheat only after a learner interaction or viewport/model change such as dragging, filtering, focusing, resizing, or changing global gravity. It SHALL NOT apply a continuous idle breathing offset. Labels SHALL remain readable under the existing focus and zoom rules, and raw identifiers SHALL NOT be primary canvas text.

#### Scenario: Settled graph is quiet

- **WHEN** the graph simulation reaches its stable threshold and the learner does nothing
- **THEN** node and label positions remain unchanged and no recurring animation loop is scheduled

#### Scenario: Pause a hidden graph

- **WHEN** the document becomes hidden
- **THEN** any active settling frames stop until a later interaction or visibility change resumes the simulation

#### Scenario: See a quiet living graph

- **WHEN** an ordinary-motion graph finishes active settling and remains visible
- **THEN** its nodes remain still without random or periodic displacement

#### Scenario: Read graph labels

- **WHEN** the learner changes zoom, search, hover, or focus
- **THEN** labels follow the existing readable visibility and emphasis rules

#### Scenario: Read progressively disclosed labels

- **WHEN** the learner changes zoom, search, hover, or focus
- **THEN** the corresponding ranked or explicitly relevant labels remain readable under the defined thresholds

### Requirement: Adjustable graph compactness

The existing 0–100 in-memory center-gravity control SHALL provide a visibly stronger range, with a maximum coefficient of approximately `0.00351` and default value 30. Higher values SHALL draw all nodes more toward the graph center and lower values SHALL let them spread, regardless of whether nodes have connecting edges. The value SHALL NOT be persisted or written to learning records.

#### Scenario: Increase graph gravity

- **WHEN** the learner raises the gravity control
- **THEN** the current simulation reheats with a stronger center force and the graph remains otherwise unchanged

#### Scenario: Lower graph gravity

- **WHEN** the learner lowers the gravity control
- **THEN** the current simulation reheats with a weaker center force and unconnected nodes may spread farther apart
