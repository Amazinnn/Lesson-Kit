## MODIFIED Requirements

### Requirement: Component-aware graph presentation

The complete graph SHALL identify connected components and choose deterministic seed coordinates for each nontrivial component from six initial layouts using edge crossings, label collisions, and spatial waste in that order. Those packed seeds SHALL then enter one unified elastic field, while isolates retain separate initial regions. Stronger semantic edges SHALL have shorter targets than weaker edges, every pair of node circles SHALL retain at least 24 pixels of logical clearance, and labels SHALL NOT enlarge physical collision radii. Remaining obstructed edges SHALL use deterministic shallow curves while preserving their semantic endpoints.

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

### Requirement: Neighborhood focus preserves graph context

Selecting a graph node SHALL fully emphasize and gently expand its one-hop neighborhood, secondarily emphasize and expand two-hop neighbors, and fade farther nodes with unrelated edges. Expansion SHALL preserve stronger-edge-before-weaker-edge distance ordering and SHALL NOT recenter the camera. Selecting the background SHALL restore the complete graph and ordinary semantic targets.

#### Scenario: Focus a node neighborhood

- **WHEN** the learner selects a node
- **THEN** one-hop and two-hop neighborhoods expand in place with their emphasis levels while farther topology remains present

#### Scenario: Reset graph focus

- **WHEN** the learner selects the graph background
- **THEN** all nodes and edges return to the complete-graph presentation and ordinary semantic targets
