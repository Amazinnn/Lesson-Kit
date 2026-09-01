# Change: Improve knowledge-graph relationship readability

## Why

The relationship view already chooses deterministic low-clutter layouts, but every
relationship is drawn as the same flat line. Dense areas therefore hide relationship
strength and do not provide the pipe-like depth requested by the product direction.

## What Changes

- Add a finite deterministic swap pass that reduces avoidable crossings after each
  candidate layout settles.
- Map existing attraction strength to line width and darkness.
- Render every relationship as shadow, body, and highlight layers.
- Draw weak relationships first and strong relationships last.

No relationship data, learning state, or graph coordinate is persisted.
