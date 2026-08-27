## ADDED Requirements

### Requirement: Adjustable graph compactness

The graph page SHALL provide one compact range control for global center gravity. Changing it SHALL reheat the current in-memory simulation so higher values draw all nodes more toward the graph center and lower values allow them to spread, regardless of whether nodes have connecting edges. The value SHALL NOT be persisted or written to learning records.

#### Scenario: Increase graph gravity

- **WHEN** the learner raises the gravity control
- **THEN** the current graph simulation reheats with a stronger center force and the graph remains otherwise unchanged

#### Scenario: Lower graph gravity

- **WHEN** the learner lowers the gravity control
- **THEN** the current graph simulation reheats with a weaker center force and unconnected nodes may spread farther apart
