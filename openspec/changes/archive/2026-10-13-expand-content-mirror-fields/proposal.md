## Why

The v1 JSON content mirror implementation now projects logical figure references and objective problem difficulty, but its declared allowlist and current capability contracts do not yet describe that projection. This change makes the existing extension explicit and safe, including the narrow cases where a complete explicit replacement rating accompanies a content edit and where a tracked owner's logical references change without creating figure bytes. Content-only rating invalidation and gated figure-byte creation remain in force.

## What Changes

- Add knowledge-point and problem `figure_paths` references to the v1 JSON projection, gated by the existing logical-path validation contract.
- Add the problem's four objective difficulty dimensions and derived total/model as a complete nullable group; recompute derived values through the existing zero-write difficulty checker.
- Specify additive revision adoption for older v1 workspaces, including the exact next-revision convergence case and unchanged-revision counterexamples.
- Require read-only preflight to reject invalid references or unavailable explicit rating groups before any writes, and require stale difficulty clearing to touch only columns present in the pool.
- Reconcile the current difficulty and figure capabilities with those existing mirror behaviors while retaining the content-only rating-clear scenario and the gated byte-hash policy.
- Update the existing mirror field and action documentation without adding a CLI action, pool migration, image transport behavior, path-generation rule, or broader layering exception.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-content-governance`: Define the approved figure-reference and objective-difficulty extensions to the JSON content projection, their validation and schema-compatibility behavior, and safe revision adoption.
- `problem-difficulty`: Keep content-only edits clearing ratings while allowing a complete, explicitly supplied replacement vector in the same JSON mirror revision.
- `knowledge-figures`: Distinguish reference-only JSON projection for tracked owners from gated figure-byte creation, without deciding a repository-wide naming policy.

## Impact

- `workbench/data/content_mirror.py`, the existing pure figure-path validation authority, and focused content-mirror tests.
- `FILE_CONTRACT.md`, `docs/DATA_MODEL.md`, `docs/ARCHITECTURE.md`, `docs/PRODUCT-MANUAL.md`, the existing authored-content entry in `docs/GLOSSARY.md`, existing mirror action registrations, and a dated changelog.
- A scoped OpenSpec change under `workbench-content-governance`, `problem-difficulty`, and `knowledge-figures`; no dependency, SQLite migration, CLI surface, byte transport, or global figure naming decision.
