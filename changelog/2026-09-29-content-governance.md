# Content governance: deduplication, audit, and rollback conflicts

## Implemented

- Reuse one stdlib-only content identity rule for duplicate checks at ingest and
  in the read-only pool audit. Compare full stems across the course pool and
  within a manifest; report colliding ids and available source evidence.
- Add `lesson-kit data <workspace> audit`, with selectable hygiene checks,
  JSON output, and a nonzero exit code when findings exist.
- Share markup and label validation between ingest and in-place edits. Objective
  micro quiz stems have no maximum length.
- Snapshot applied content and figure state. A rollback refuses if its target
  changed after apply, before making a new backup or restoring old values.

## Verification and limits

- Targeted workbench tests: 139 passed.
- Full standard-library test discovery: 723 tests ran; 722 passed. The existing
  `ServiceLifecycleTests.test_process_image_identifies_python_and_rejects_others`
  test failed because this container reports an empty process image.
- `compileall` and the `extract-problems` guard passed. `pytest` is not installed.
- Strict OpenSpec validation remains unverified: no local `openspec` executable
  is installed, and the network-backed validator invocation was rejected by the
  automatic approval review because the endpoint could not be verified for
  repository input.
- The ADS workspace pool is not present in this checkout, so the before/after
  corpus audit for `ads-pool-content-repair` remains pending there. No real pool
  was changed.
