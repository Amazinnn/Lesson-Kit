## MODIFIED Requirements

### Requirement: Component-aware graph presentation

The complete graph SHALL identify connected components and choose deterministic seed coordinates for each nontrivial component from six initial layouts using edge crossings, label collisions, and spatial waste in that order. Those packed seeds SHALL then enter one unified elastic field, while isolates retain separate initial regions. Stronger semantic edges SHALL have shorter targets than weaker edges, every pair of node circles SHALL retain at least 24 pixels of logical clearance, and labels SHALL NOT enlarge physical collision radii. Remaining obstructed edges SHALL use deterministic shallow curves while preserving their semantic endpoints. A settled simulation SHALL stop updating until an explicit interaction or model/viewport change reheats it, and no idle breathing displacement SHALL be applied. Coordinate reuse SHALL follow the optional exact-identity local layout seed contract in the workbench-ui graph requirement.

#### Scenario: Interaction reheats a quiet graph

- **WHEN** the learner drags a node or changes the graph view controls
- **THEN** the unified simulation resumes from its current in-memory positions and settles again; any local layout seed is updated only after settlement and does not become authored graph data

#### Scenario: Separate disconnected components

- **WHEN** a chapter graph has multiple components and isolated nodes
- **THEN** deterministic component layouts provide readable initial regions before all visible nodes enter one runtime field

#### Scenario: Choose a deterministic readable start

- **WHEN** the same component and viewport are laid out repeatedly
- **THEN** the same candidate wins the lexicographic crossing, collision, and waste comparison

#### Scenario: Preserve semantic distance and clearance

- **WHEN** connected edges have different attraction and nodes have different radii
- **THEN** stronger edges have shorter center targets while every node pair retains the minimum circle clearance

#### Scenario: Respect reduced motion

- **WHEN** reduced motion is requested
- **THEN** the unified field computes a stable layout and is drawn once without progressive or idle animation

### Requirement: Existing-metric projections

The graph MAY project existing `problem_count`, `importance`, `state`, or edge `attraction` into visual emphasis. The structural relationship layout SHALL remain the default, projections SHALL be deterministic, and projection selection SHALL NOT be persisted. Coordinate reuse SHALL follow the optional exact-identity local layout seed contract in the workbench-ui graph requirement.

#### Scenario: Switch projection

- **WHEN** the learner selects an existing-metric projection
- **THEN** the graph changes visual emphasis without changing its edges, selection, authored content, or learning data; any settled coordinate seed remains tied to the current graph identity
