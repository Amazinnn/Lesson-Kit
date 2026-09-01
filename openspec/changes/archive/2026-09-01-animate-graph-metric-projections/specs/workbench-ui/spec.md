## ADDED Requirements

### Requirement: Metric projection morphology

The knowledge graph page SHALL preserve the same visible node elements when the learner switches among relationship structure, formal-problem count, importance, and learning-state projections. A metric projection SHALL map higher values to both a larger node radius and a target nearer the canvas center, while retaining deterministic separation for equal values. Learning-state projection SHALL order completion as `mastered`, `review`, `needs_work`, then unmarked. Each projection SHALL apply a restrained, distinguishable Mondrian palette without changing or persisting learning data.

#### Scenario: Switch to a numeric metric

- **WHEN** the learner changes from relationship structure to formal-problem count
- **THEN** the same nodes move continuously toward deterministic metric targets and higher-count nodes become larger and nearer the center

#### Scenario: Read completion from learning state

- **WHEN** the learner selects learning-state projection
- **THEN** mastered nodes are ranked above review, needs-work, and unmarked nodes for size and radial position

#### Scenario: Return to relationship structure

- **WHEN** the learner returns from a metric projection to relationship structure
- **THEN** the same nodes transition back toward a freshly computed relationship layout without changing graph membership, selection, or stored coordinates

### Requirement: Metric projection transition

Projection changes SHALL reheat the existing in-memory simulation and animate node position and radius toward their new targets with bounded velocity, so nodes appear to bubble inward or outward rather than teleport. A settled projection SHALL become fully static. When reduced motion is requested, the graph SHALL compute and draw the stable projected result synchronously without scheduling animation frames.

#### Scenario: Metric transition settles

- **WHEN** an ordinary-motion learner changes the active graph projection
- **THEN** nodes and incident edges move together until the new projection settles and no recurring animation remains

#### Scenario: Reduced-motion metric switch

- **WHEN** a reduced-motion learner changes the active graph projection
- **THEN** the projected terminal layout is drawn without requesting animation frames
