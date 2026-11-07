# Bounded receive commits

2026-11-07, followup todf4118a8, isolated codex/course-sync.

Receive units use native SQLite savepoints inside at most128-unit durable chunks. Per-unit identity/index changes are small ChainMap deltas rather than copying/scanning all mappings. Row/mapping/acknowledgement commit together. Commit failure acknowledges none of its chunk and retains previous chunks; invalid units discard their own side effects while independent neighbors continue. Grouped execution items are owned only by their header transaction, not later empty chunks. File chunks publish before dependent rows; failed publication blocks those dependents. Completed intent clears share a transaction. Atomic JSON writes serialize once before writing.

Focused receive/execution/data checks54 passed in27.87s. New counterexample initially observed309 transactions for300 content rows, then verifies fewer than15 with batching. Fault checks cover partial row writes, middle-chunk commit failure, earlier history preservation, retry deduplication and file publication blocking dependent execution. compileall and diff whitespace checks passed.

Full-size single diagnostic loaded an earlier version of this unit (before removing redundant grouped-item loops): export141.822s, initial inspect72.989s, receive15.854s, repeat inspect58.180s. Counts match, repeat changes/outgoing/errors are empty. Receive is within30s on this one sample; export/unchanged-check still fail. File-byte verification is running separately. No p95 acceptance, whole-package completion, real course cutover or free LLM acceptance is claimed. An independent DeepSeek review is queued after provider recovery.
