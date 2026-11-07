# Implementation checkpoint

Source branch `codex/course-sync`, based on `c5a9c642`. Isolated source root `D:/.codex/worktrees/course-sync/lesson-kit`. Main checkout and real course data remain separate.

## Completed focused unit

Pure `plan_exchange` comparison and nine targeted regression checks. The initial collection failed with ModuleNotFoundError. After implementation `python -m pytest tests/workbench/test_course_sync.py -q` reports 9 passed. Checks cover one-sided additions/updates, equal convergence, conflicts, deletion vs edits, missing assets, source-identity history union, per-question drafts, transitive invalid dependencies, valid dependency cycles and referenced deletion. This is focused verification, not package acceptance.

## Worker execution

DeepSeek Harness `0.1.5-rc.1`, provider `opencode-go`, model `deepseek-v4.1-flash`. Separate per-run overlays and session headers, no credential values in project files. P00 read AGENTS, executed a shell command, and wrote a probe JSON. D01/I01 failed on their first request with 429 overloaded before product output and were reassigned to the coordinator. G01 Git transport and P01 preferences continue. Maximum worker concurrency is four. Provider stop-dispatch started around 11:02.

The headless entry creates a fresh persisted session, and exposes no resume flag. No claim of tested native session continuation is made. Task briefs and disk checkpoints enable explicit recovery, and SDK continuation remains to verify if needed.

## Outstanding

Full Data export/reception, cross-device integer identity mapping, per-question unfinished Paper projection, CLI registration, Git composition, hourly task, free-LLM Tutor acceptance and full real-environment acceptance are not complete. New pure comparison code is not a delivered synchronization feature.

The first full pytest invocation without PYTHONUTF8 exited 1 with a truncated log and no final summary. It is incomplete evidence. A subsequent UTF-8 run collected 1,332 tests and passed all in 285.90 seconds. That run includes the focused course comparison/projection tests present at collection time, and predates completion of G01/P01. Full post-integration acceptance is outstanding.

## Projection implementation checkpoint

Committed database projection and bundle reader now have 11 targeted checks, with the pure planner bringing the focused total to 20 passed. No installed CLI exposure or receive-side completion is claimed. Read/write is isolated to temporary fixtures. Exact rows, original answers and file bytes are preserved, unknown tables and missing references are errors, path escapes and Windows aliases are rejected, and interrupted export publication leaves the previously published manifest and bytes intact. Origins are persisted before publication.

Each export publishes immutable generation paths before swapping its manifest. Generation garbage collection and F2 performance measurements remain outstanding. Durable receive identity/reference remapping, execution/draft normalization, and all covered-class F1/F4 validation remain prerequisites for marking task 2.3 complete.

## Integer provenance checkpoint

Declared integer record identifiers and attempt/execution references now export stable origin identities, including declared stored-JSON references. A simulated local ID remap produces identical exported assets and preserves raw answers. Dangling declared references fail explicitly. Focused planner/projection checks total 22 passed. Receive allocation and complete nested snapshot coverage remain outstanding.

The read-only real legacy database backup copy exported 469 assets and reread without errors. `legacy-projection.json` records exact table/column coverage and timing. This verifies projection only, not F4 receive/migration acceptance. `field-inventory.json` records the freshly generated trusted schema and static writer/consumer candidates, not exhaustive dynamic SQL analysis.

## Read-only preflight checkpoint

Repeated export no longer advances the shared base. Read-only inspect validates course identity, target primary keys and columns while retaining independent valid assets. It does not initialize installation metadata or course state. Baseline mismatch is explicitly blocked pending complete common-baseline/acknowledgement handling. Focused planner/projection/preflight checks total 26 passed. This is internal foundation, not task 2.4 completion.

At 11:32 the user chose to retain the existing two DeepSeek workers and wait for successful recovery probes before further dispatch. The second six-call probe again returned five 200 responses followed by a 429. No provider substitution or new implementation worker is authorized by that answer.
