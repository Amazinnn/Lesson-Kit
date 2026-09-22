# Design — pre-release contract reconciliation

## Conversation mirror

The service is single-process, so one re-entrant lock is the smallest complete
boundary. JSON replacement, event sequence allocation/appending, transcript
append/read, and their readers share that lock. Atomic replacement remains;
sleep/retry loops are not used to hide the race.

## Documentation authority

Live specifications and current entry documents contain only current facts.
OpenSpec archives, `docs/DISCUSSION-RECORD.md`, and Git retain history. The
pipeline-era design files stay in place but identify themselves as frozen base
contracts; workbench additions point to `docs/ARCHITECTURE.md` and live specs.

The retired `review-page` requirements are removed after their surviving API
contracts are confirmed in `review-workbench`. Candidate and explain/diagnose
language is removed from current requirements, routing, and file contracts.

## Verification

A deterministic synchronization test holds a mirror read open and proves a
writer cannot replace the file until the read ends. A documentation test scans
only live/current files, never historical archives.
