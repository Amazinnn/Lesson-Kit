# Change: Force-directed native knowledge graph

## Why

The native graph currently places knowledge points on a fixed grid. It does not express semantic closeness, shared-problem reinforcement, or the relative learning surface of each node, so the graph behaves like a decorated list rather than a navigable knowledge structure.

## What Changes

- Enrich the live graph model with formal-problem counts and explicit edge attraction metadata.
- Merge reverse duplicate semantic edges and use shared formal problems only to reinforce an existing relation.
- Replace grid placement with a zero-dependency force simulation driven by animation frames.
- Render circular nodes whose area grows with formal-problem count, plus external readable labels and state color.
- Preserve search, state filter, focus, detail editing, pan, zoom, fit, and reduced-motion behavior without storing coordinates or browsing logs.

## Capabilities

- `workbench-ui`
- `review-workbench`

## Impact

Read-only graph-model enrichment, one browser physics module, existing graph UI integration, CSS, and tests. No route, SQLite schema, relation meaning, learning record, or generated graph artifact contract changes.
