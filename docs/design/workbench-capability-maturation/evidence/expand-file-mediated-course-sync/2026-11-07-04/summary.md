# WP01 resumed implementation — 2026-11-07

Working tree: `D:/.codex/worktrees/course-sync/lesson-kit`, branch `codex/course-sync`, starting HEAD `c4995aba`. Main checkout and live course data are not switched.

DeepSeek Go recovery probes passed 6/6 at 14:13–14:14 and again 6/6 at 14:31–14:32. R02, S02 and C02 ran as bounded read-only audits, max concurrency2 in this wave. C03 is reviewing the subsequent incremental-checkpoint correction. No local decision model or real course writes were used.

## Implemented, verification in progress

- Durable receive acknowledgements/source mappings, incremental checkpoint compaction and file publication intents; rollback discards only failed transaction state. No success-batch undo or approval gate.
- Unwritable file isolation, post-commit retry deduplication, missing-sidecar lineage protection and standalone schema helper parity.
- Conflict/incomplete receive prevents remote publication; transport errors retain receipts; readable Tutor files and obsolete envelope deletions are staged; readable remote edits are materialized; simple remote-only ancestry fast-forwards.
- Notification argv correctness and re-arming after resolution.

## Evidence and current limits

New database/file fault checks and existing receive/projection/execution checks: 41 passed. Standalone migration/bootstrap plus data checks: 73 passed. Prior broader course-sync combination: 100 passed before the later normalization/Tutor follow-up. Node preferences12 passed; compileall, live specs21/21 and extract-problems guard passed earlier this turn.

An intermediate full-suite run failed7 with1410 passing (418.28s): standalone migration imported the older installed main module instead of the new helper. The dependency was removed; the 73-test targeted run passes. A fresh full-suite run against the revised source is in progress; no full-suite pass is yet claimed here.

Diagnostic100/300/1000-row timings are in receive-scaling-pilot.json. They are one-off pilots under concurrent activity, not F2 or p95 acceptance. F2, browser, dedicated real remote, real task lifecycle and free-LLM acceptance remain open. Auditors' reports are snapshots with unverified hypotheses, not new authority. In particular S02's installed-source observation must be rechecked in a neutral process before scheduling/cutover.

R02 identified still-open nested reference paths (`run_id`, previous_states values, attempt_ids[], grading request_json[0], submitted part attempt IDs inside drafts), idempotency-cache remapping and device-bound grading job provenance. Each requires writer-backed reconciliation and tests before WP01 release. C02 led to the lineage, isolation, normalized persistence and standalone schema corrections; C03 review remains pending.

## Subsequent verified checkpoint

Standalone dependency correction passed the full suite:1420 passed in449.21s (pytest-resume.xml/log retained under tmp/agent-runs). After later concurrency/input-validation corrections, the full course-sync combination passed108 tests in153.79s. C03's malformed-item, stale-inspection and overwritten-pending-intent findings now have checks/corrections; schema parity was added before C03 finished reading. Full-suite results predate these last narrow changes, so latest full acceptance is not claimed.

F03's independently executed round-trip failures remain open. A full-size F2 diagnostic (1000KPs/10000problems/100Papers/10000attempts/30unfinished/500learningfiles/100MiBattachments) has begun; first export125.441s, above the30s target. Remaining phases were still running at this checkpoint. It is a single profile, not p95 acceptance.
