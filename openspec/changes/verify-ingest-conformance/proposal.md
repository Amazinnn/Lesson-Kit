## Why

The existing ingest-integrity register requires real-pool regression evidence for
batch provenance and server/client math rendering. Fixture checks cannot establish
that the sanctioned paths preserve historical course content and learning rows.

## What Changes

- Add an explicitly invoked check using a registered workspace and SQLite backup
  copies in a temporary workspace; source databases and the registry stay read-only.
- Verify existing content-bundle stamping, atomic refusal, rollback, and rendering
  requirements, and reconcile task evidence with the measured ADS repair residuals.
- Fix the reproduced legacy gate-report KP insertion omission under the existing
  batch provenance requirement; existing problem updates already stamp the batch.
- Keep historical pipeline provenance, NEW-GAP, DOCTRINE, and data repair work pending.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. `skip_specs: true`: this is conformance repair, runnable verification and evidence reconciliation
for existing `workbench-content-governance`, `workbench-ui`, and content-dedup
requirements. No requirement, schema, manifest, or product policy changes.

## Impact

`tests/workbench/real_pool_conformance.py` is outside automatic fixture discovery.
It uses Python's standard library, existing governed ingest and schema helpers,
and the existing Node renderer parity helper. Evidence contains counts, sample IDs
and math values, not full course or learner text. No real data, figures, registry,
dependencies, pipeline behavior, or backup policy changes.
The only production change is `workbench/ingest/__init__.py`'s legacy new-KP insert
clause, with a focused regression in `tests/workbench/test_ingest.py`.
