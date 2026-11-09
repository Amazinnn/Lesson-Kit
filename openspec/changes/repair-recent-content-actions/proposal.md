## Why

2026-11-09 review reproduced five regressions after WP02/WP03: corrected bundles duplicate auto-ID knowledge points, cross-chapter dependencies are rejected, malformed micro-quiz neighbours crash validation, method associations retain obsolete difficulty, and transient legacy-action failures become permanent invalid inputs. Six active-change validations also fail after recent spec integration.

## What Changes

- Reconcile an unchanged auto-ID knowledge point by exact current authored content within its chapter; report an existing entity and resolve its local key without rewriting it. Ambiguous matches fail explicitly.
- Apply new knowledge points before dependent problems/cards across chapters, retaining readable per-chapter batches and dependency-safe failure boundaries.
- Preserve partial errors through the public ingest receipt, conversation mirror, next-turn context and existing result cards; zero writes cannot claim success.
- Filter only validated micro-quiz items and reuse the common problem update path for method associations.
- Preserve legacy pending actions on operational errors, while reporting genuine invalid/stale inputs.
- Rebase missing scenarios in active deltas without erasing their planned requirements; remove the empty directory left by an already archived change.

## Capabilities

### Modified Capabilities
- `knowledge-content-operations`: independent units, corrected retry and method associations.
- `direct-project-actions`: transient-error recovery of legacy actions.

## Impact

Work stays in workbench, tests and the affected contract documents. No new dependency, schema migration, approval gate, real-course write, or frozen-layer behavior change.
