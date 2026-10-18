## MODIFIED Requirements

### Requirement: Layered knowledge relationships
The structure projection SHALL seed each solve on the guide grid rather than on a
seed spiral. The hierarchy band SHALL tighten as alpha cools, so that a hot solve
has room and a settled layout keeps the same band it had before.

#### Scenario: The first frame does not teleport
- **WHEN** the structure projection builds its layout
- **THEN** no point starts further from its own guide than the band at that alpha

#### Scenario: A settled layout keeps its band
- **WHEN** alpha reaches zero
- **THEN** the band equals its unramped value

#### Scenario: A re-solve still has room
- **WHEN** the learner drags a node, switches projection or changes gravity
- **THEN** the solve restarts with the wide band and tightens as it cools

### Requirement: Charge is foldable
The structure projection SHALL compute repulsion through a Barnes-Hut tree rather
than every pair: a subtree SHALL stand for its members as one point charge when
`d2 * theta^2 >= size^2`, with `theta = 0.9` and a near-field floor of
`distanceMin2 = 30`. Node ordering and layout semantics SHALL NOT change.

#### Scenario: Distant clusters fold
- **WHEN** a subtree is far enough relative to its own extent
- **THEN** its members act as one point charge at their centroid

#### Scenario: Coincident points do not hang the solve
- **WHEN** two points occupy the same position
- **THEN** they share a leaf and the tree does not recurse forever

### Requirement: Frame motion is continuous
The structure projection SHALL limit per-frame motion through velocity damping
rather than a fixed speed ceiling, so that the fastest nodes are not pinned at a
cutoff, and no node position SHALL be set outside the integration step except by
the hierarchy band and the congestion resolver.

#### Scenario: No speed ceiling
- **WHEN** a node accumulates velocity from a large force
- **THEN** its step is scaled by the damping, not clamped to a fixed constant

#### Scenario: Settling decelerates
- **WHEN** the solve runs to rest
- **THEN** per-frame displacement decreases monotonically and directions rarely
  reverse

### Requirement: A restored layout is adopted, not re-solved
When the cached layout seed matches the visible graph exactly, the workbench SHALL
place the points at their cached coordinates and stop, rather than re-solving from
them. A partially matching seed SHALL still be solved. Clearing or failing to read
the cache SHALL only cost the previous layout.

#### Scenario: Reopening the graph
- **WHEN** the learner reopens the graph page with a matching cache
- **THEN** the layout appears at the cached coordinates without further motion

#### Scenario: A partial cache
- **WHEN** only some points have cached coordinates
- **THEN** those points start where they were and the solve runs

#### Scenario: The graph changed
- **WHEN** node ids or relation endpoints, types or directions differ from the cache
- **THEN** the cache does not apply and the graph is solved from scratch

### Requirement: The stage is a coordinate box, not a layout wall
The structure projection SHALL NOT constrain node positions to the stage rectangle.
The stage SHALL only place the projection centre and size the DOM and SVG box; the
view SHALL fit the node extent.

#### Scenario: A free layout finds its own extent
- **WHEN** a force setting asks for a wider layout than the stage
- **THEN** the points spread as the physics dictates and the view fits them
