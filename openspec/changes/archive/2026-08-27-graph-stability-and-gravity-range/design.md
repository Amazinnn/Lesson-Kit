## Decisions

- A settled graph is fully static. Dragging, filtering, resizing, focusing, or changing gravity reheats the simulation.
- The existing 0–100 slider maps to a maximum center-force coefficient of approximately `0.00351` (three times the previous maximum); the default value remains 30.
- Relationship spring distance remains authoritative for semantic edge length. Global gravity only pulls every node toward the canvas center.
- Future learning-oriented graph changes will be specified separately. Candidate direction: morphology based on traceable mastery evidence and a small, explainable selected-node dashboard.

## Non-goals

- No new learning metrics, graph actions, persistence, coordinate storage, or third-party physics library.
