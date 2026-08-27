## Context

The graph currently settles each connected component independently, packs it into a fixed 1200 by 800 region, and reheats only the component containing a dragged node. Title length expands every node's collision radius. These choices minimize crossings but make the graph uniform, locally frozen, and bounded.

## Goals / Non-Goals

The graph must preserve deterministic readable starts while becoming elastic, semantically spaced, freely draggable, and quietly alive. It must remain zero-dependency and memory-only. Community detection, graph findings, persisted coordinates, a general physics framework, and new learning controls are excluded.

## Decisions

### One runtime simulation after deterministic seeding

The existing six-start component search remains because it gives repeatable low-clutter initial coordinates. Packing produces initial positions only. A single simulation then owns every visible node and edge, so drag and spring changes propagate across the full graph. Keeping component-local runtime simulations was rejected because it preserves the reported frozen behavior.

### Separate semantic distance from collision clearance

For attraction `a`, normalize with `clamp((a - 0.75) / 1.125, 0, 1)`. The semantic gap is `144 - 72 * normalized`, and an edge's center target is the two node radii plus that gap. Collision independently enforces 24 pixels of circle-to-circle clearance. Labels do not enlarge physical radii; their visibility is managed by presentation rules.

### Unbounded coordinates and a bounded camera

Node coordinates are never clamped to the layout rectangle. Fit, zoom, pan, and drag modify only the camera transform. Near-edge dragging pans the camera so a node may be placed anywhere. On release the location becomes a weak in-memory anchor: strong enough to preserve intent, weak enough to transmit spring response. Refresh discards anchors.

### Three animation states

Active layout uses the normal force field until stable. Stable graphs receive a deterministic 12-to-18-second breathing force capped at four pixels from their stable bases and draw at no more than 30 frames per second. Hidden pages pause. Reduced-motion computes a bounded stable layout and draws once, with no breathing.

### Progressive labels and deterministic edge routing

Rank labels by core importance, descending formal-problem count, then identifier. Show 6 below 0.8 zoom, 12 from 0.8 below 1.1, and all at 1.1 or above. Hovered, searched, selected, and one-hop labels override the limit. Straight edges remain straight when clear; obstructed candidates compare deterministic left and right shallow curves and select the lower node-obstruction and crossing score.

### Focus expands rather than changes the camera

Selection multiplies one-hop semantic gaps by 1.15 and two-hop gaps by 1.08, reheats gently, and preserves strong-before-weak distance ordering. The camera does not recenter. Clearing selection removes the multipliers and reheats.

## Risks / Trade-offs

- Continuous motion can distract → cap displacement, frequency, and frame rate; honor visibility and reduced motion.
- Unbounded dragging can lose nodes → retain fit as a camera-only recovery action.
- Labels may obscure structure → progressive visibility replaces label-sized collision bodies.
- O(n²) repulsion does not scale indefinitely → the verified chapter has 31 nodes; defer spatial indexing until measured need.
- Soft anchors can distort topology → use weak attraction and keep them session-only.

## Migration Plan

Ship the read-only `importance` projection and browser behavior together. No database migration is required. Rollback is a code revert because no durable state changes.
