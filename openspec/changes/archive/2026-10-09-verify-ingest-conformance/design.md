## Context

The approved requirements already cover recipe batch provenance and whole-batch
rollback (`workbench-content-governance`, Batch provenance and rollback), atomic
duplicate refusal (`content-dedup-and-audit`), and consistent escaped math rendering
(`workbench-ui`). This follow-up supplies evidence, not new normative behavior.

## Decisions

1. Accept an explicit registered workspace name. Resolve its path through the
   registry without calling any registration or update method. Import helpers from
   this repository and print their actual module paths.
2. Open the source with SQLite `mode=ro` and `query_only`. Capture schema, table rows
   and ledger before/after in memory. Backup to a TemporaryDirectory workspace, then
   run the actual schema ensure only on the copy. Compare existing content IDs,
   text, historical topic labels and learning records through that baseline migration.
3. Make clearly labeled verification-only KP/problem/card inserts based on real
   content, with unique verification text. Use explicit distinct scratch backup
   paths. Check recorded chapter batch stamps, original rows, malformed/duplicate
   all-or-nothing refusal, and content/learning restoration after rollback. The
   rolled-back ledger entry remains as required; this is not whole-file restoration.
4. Select unchanged math fragments from actual stored fields. Run the real server
   renderer and existing Node helper against those same fragments, parse math span
   text, and require raw expression preservation and server/client HTML parity.
   Verification-only inserted content cannot substitute this real-source evidence.
5. Compare ADS pre-repair and current audit findings using the current code and
   original check meanings. Historical figure-tree parity is unavailable, so figure
   findings are an after-state only. Findings and failed original acceptance remain
   visible; later practice counts do not refute a historical learning-row ledger.
6. The sanctioned legacy `apply` gate-report path must also stamp newly inserted
   KPs. Reproduce the omission in an existing temporary fixture with the migrated
   `ingest_batch_id` column, then add the allocated batch ID to that insert using
   the existing schema-aware row helper. Preserve old-column compatibility, existing
   rows and transaction/rollback behavior; do not run recovery on a real course.

## Boundaries

No source migrations, apply, rollback, repair, deletes, figure writes or registry
writes. Direct edits/problem-patch do not gain creation provenance. Pipeline
insertion doctrine, new gaps, #110 and parked work remain pending. Full repository
verification and independent acceptance belong to the separate final task.
