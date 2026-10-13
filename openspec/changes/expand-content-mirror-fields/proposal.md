## Why

The v1 JSON content mirror implementation now projects logical figure references and objective problem difficulty, but its declared allowlist still excludes them and its validation, upgrade, and partial-schema behavior is incomplete. This change makes that existing extension explicit and safe while keeping the JSON schema version and separate binary-figure workflow unchanged.

## What Changes

- Add knowledge-point and problem `figure_paths` references to the v1 JSON projection, gated by the existing logical-path validation contract.
- Add the problem's four objective difficulty dimensions and derived total/model as a complete nullable group; recompute derived values through the existing zero-write difficulty checker.
- Specify additive revision adoption for older v1 workspaces, including the exact next-revision convergence case and unchanged-revision counterexamples.
- Require read-only preflight to reject invalid references or unavailable explicit rating groups before any writes, and require stale difficulty clearing to touch only columns present in the pool.
- Update the existing mirror field and action documentation without adding a CLI action, pool migration, image transport behavior, path-generation rule, or broader layering exception.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-content-governance`: Define the approved figure-reference and objective-difficulty extensions to the JSON content projection, their validation and schema-compatibility behavior, and safe revision adoption.

## Impact

- `workbench/data/content_mirror.py`, the existing pure figure-path validation authority, and focused content-mirror tests.
- `FILE_CONTRACT.md`, `docs/DATA_MODEL.md`, `docs/ARCHITECTURE.md`, `docs/PRODUCT-MANUAL.md`, the existing authored-content entry in `docs/GLOSSARY.md`, existing mirror action registrations, and a dated changelog.
- A scoped OpenSpec change under `workbench-content-governance`; no dependency, SQLite migration, CLI surface, or binary synchronization change.
