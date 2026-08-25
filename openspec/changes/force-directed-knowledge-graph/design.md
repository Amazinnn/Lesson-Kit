## Context

The graph already reads live SQLite data and uses the workbench's outer right detail panel, but `workbench.js` assigns every filtered node to a percentage grid. The data model exposes bare directed relation rows and does not quantify node problem coverage or edge attraction.

## Decisions

1. `problem_count` counts only formal `problems` rows whose `kp_ids` contain the node; candidates never contribute.
2. An edge exists only when supplied by `knowledge_relations` or a knowledge point's existing `related_kp_ids`. Sharing problems cannot create a new semantic edge.
3. Reverse and repeated edges for the same unordered pair are merged. Explicit strength uses low `0.75`, medium or legacy `1.0`, and high `1.25`. The shared-problem multiplier is capped at `1.5`; the spring target distance is inversely proportional to the square root of the resulting attraction.
4. Node radius is `min(30, 8 + 2.4 * sqrt(problem_count))` CSS pixels. State is conveyed by fill/border color; a separate label preserves readable titles.
5. `graph-physics.js` is a small browser-and-Node-compatible standard-JavaScript module containing deterministic initialization, spring attraction, pairwise repulsion, circular collision, center gravity, damping, stability detection, and radius/distance helpers.
6. The browser uses `requestAnimationFrame`, stops after stability, and reheats after data/filter/size changes or drag. Pointer dragging fixes the selected node during interaction; background pointer movement pans the viewport; wheel and existing buttons zoom; fit resets the transform to current graph bounds.
7. Coordinates remain memory-only. `prefers-reduced-motion` runs bounded synchronous settling and paints once, so it communicates the same topology without animation.

## Risks and Controls

- Pairwise repulsion is quadratic, but the current chapter contains 28 nodes and filtering only reduces that set; no spatial index or dependency is justified.
- A disconnected graph can drift, so center gravity and bounded velocity keep components visible.
- Physics tests assert qualitative invariants and convergence rather than exact pixels, avoiding brittle snapshots.
