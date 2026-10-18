## ADDED Requirements

### Requirement: Flat knowledge levels cluster instead of stretching into a band

When the structure projection produces exactly one hierarchy level and that level holds
more than twelve visible knowledge points, the layout SHALL place those points on a
deterministic two-dimensional cluster grid centered on the stage rather than continuing
to wrap them along a single horizontal band. Node spacing SHALL reuse the existing
readability footprint so clustered guides never overlap. The stage dimensions SHALL
follow the clustered extent, and the clustered grid SHALL stay inside the sized stage.

A graph with two or more hierarchy levels, and a flat level of twelve or fewer points,
SHALL keep the existing row wrapping unchanged. Whether a graph has hierarchy SHALL
continue to be decided only by directed prerequisite relations; an auxiliary relation
SHALL NOT introduce a level.

#### Scenario: A pool with no directed relations is clustered

- **WHEN** the visible points form a single level and there are more than twelve of them
- **THEN** their guides occupy more than one row and more than one column
- **AND** the resulting stage is wider and taller than the single-band stage

#### Scenario: A small flat level is untouched

- **WHEN** a single level holds twelve or fewer visible points
- **THEN** the guides and the stage keep the existing row-wrapped result

#### Scenario: Hierarchy still decides itself from prerequisites only

- **WHEN** the only relations are symmetric or auxiliary
- **THEN** every point stays in one level, and clustering is still bound by the
  readable footprint rather than by invented structure

#### Scenario: A clustered flat graph settles

- **WHEN** the clustered layout runs the force simulation to rest
- **THEN** the simulation converges and leaves no overlapping pair behind
- **AND** every guide plus its footprint stays inside the sized stage

#### Scenario: Clustering is deterministic

- **WHEN** the same points are laid out twice
- **THEN** the guide positions and the stage dimensions are identical
