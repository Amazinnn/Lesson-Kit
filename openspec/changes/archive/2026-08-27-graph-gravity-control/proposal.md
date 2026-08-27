## Why

Learners need a simple way to choose between a compact overview and a more spacious relationship view without changing the graph's semantic edges or saving layout state.

## What Changes

- Add one compact graph-toolbar range control for global center gravity.
- Apply its value only to the current in-memory force simulation.
- Keep all existing routes, graph data, coordinates, and learning records unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-ui`: the graph toolbar exposes an in-memory global gravity control.

## Impact

Only the graph page markup, CSS, browser physics, and tests change. No backend API, database, dependency, or persistent setting is added.
