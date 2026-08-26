# Graph learning dashboard

## ADDED Requirements

### Requirement: Graph detail is a learning dashboard
Selecting a graph node SHALL show its readable title, current state, formal problem count, neighbor/relationship summary, signals, schedule, and a link to the formal knowledge-point page.

#### Scenario: Node selection opens the dashboard
- **WHEN** a student selects a node
- **THEN** the right panel shows the node metrics and one link to its formal knowledge-point page

### Requirement: Graph state editing remains covered
The dashboard SHALL update only the selected knowledge point's current state through the existing coverage-based graph state behavior.

#### Scenario: State update is coverage based
- **WHEN** a student saves a selected node state
- **THEN** the existing graph state behavior updates current state and schedule without adding a feedback event

### Requirement: Graph does not duplicate content editing
The graph panel SHALL NOT render knowledge-point body textareas, fragile-note editors, complete linked-problem content, or per-problem save controls.

#### Scenario: Deep reading uses the formal page
- **WHEN** a student needs the full body or linked problem text
- **THEN** the graph panel offers the formal knowledge-point link instead of duplicate editors
