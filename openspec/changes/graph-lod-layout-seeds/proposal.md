## Why

Large knowledge graphs need a lighter viewport paint path, and reopening an unchanged graph benefits from its last settled arrangement. These are browser-side presentation aids; the graph model and learner records remain authoritative in their existing sources.

## What Changes

- Keep viewport culling and label/meta LOD in the existing graph renderer. They affect paint only and preserve graph membership, selection, and priority labels.
- Keep one optional settled layout seed per workspace in browser storage. Read it only for an exact readable node-and-relation identity, use it as temporary Worker anchors, then release and reheat the existing solver.
- Reconcile both live graph specifications and the glossary, data model, architecture, product manual, Action Graph, ADR 0028, and changelog.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-ui`: specify paint-only viewport/label LOD and the optional exact-identity settled layout seed while preserving every current graph scenario.
- `knowledge-figures`: reconcile graph-coordinate clauses with the optional local seed while retaining projection, topology, and reduced-motion behavior.

## Impact

- Browser modules: `workbench/server/static/graph-renderer.js` and `graph-physics.js`.
- Live specifications: `openspec/specs/workbench-ui/spec.md` and `openspec/specs/knowledge-figures/spec.md`.
- Documentation: glossary, DATA_MODEL, architecture, product manual, Action Graph, ADR 0028, and changelog.
- No SQLite schema, backend API, CLI, FILE_CONTRACT, dependency, or authored-content change.
