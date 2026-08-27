## MODIFIED Requirements

### Requirement: Unified live graph simulation

The graph SHALL use the existing unified force field and deterministic seeds, but a settled simulation SHALL stop updating until an explicit interaction or model/viewport change reheats it. No idle breathing displacement SHALL be applied to graph coordinates or rendering.

#### Scenario: Interaction reheats a quiet graph

- **WHEN** the learner drags a node or changes the graph view controls
- **THEN** the unified simulation resumes from its current in-memory positions and settles again without persisting coordinates
