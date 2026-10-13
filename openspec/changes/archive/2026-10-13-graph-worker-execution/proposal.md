## Why

The knowledge graph has adopted Worker-only browser execution, but the live page contract does not say what happens when Worker support or graph physics loading is unavailable. The parser-inserted core can also become the public synchronous API before the Worker adapter takes effect, while an asynchronous Worker error can keep requesting steps indefinitely.

## What Changes

- Require browser Worker support for the knowledge graph and define a readable failure when graph execution cannot start.
- Make a Worker error stop that graph run, terminate the Worker, stop further solver steps and repeated solver frames, and report the failure through the graph status surface.
- Preserve the existing graph interface and semantic layout rules; coordinates remain in memory and failures do not write authored or learning data.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- workbench-ui: define the browser Worker prerequisite and visible terminal failure behavior for the knowledge graph page.

## Impact

The graph page script order and Worker adapter in workbench/server/pages.py and workbench/server/static/graph-physics.js, the graph loop and status surface in workbench/server/static/workbench.js, focused graph tests, and the architecture, ADR, product manual, and dated changelog. No persistent data model, API, or file contract changes.
