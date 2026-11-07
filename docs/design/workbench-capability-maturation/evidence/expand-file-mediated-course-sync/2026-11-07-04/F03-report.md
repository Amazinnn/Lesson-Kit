# F03 — File lifecycle regression audit (bounded, LIGHT)

Scope: independent probe of export → receive → re-export file/row lifecycle in
`workbench/data/course_sync.py`. No source/docs/tests were edited, nothing staged or committed.
Owned artifacts: this report, `tmp/agent-runs/F03-probe.py`, `tmp/agent-runs/F03-results.json`.

## Environment and method

- Probe: `python tmp/agent-runs/F03-probe.py` (run from repo root, single run, no pytest suites).
- Temporary only: `tempfile.mkdtemp()` courses; `LESSONKIT_WB_HOME` forced to a throwaway
  directory before importing `workbench`; no real course DB, registry, network or OS tasks.
- Reused `tests.workbench.test_course_sync_receive.make_course` and the same
  `export_course / inspect_exchange / apply_exchange` calls the receive tests use. Seeds:
  1 KP, 1 problem, 1 attempt, optionally 1 `practice_runs` history row.
- Tombstones were forged by rewriting the package envelope exactly as the existing tests do
  (`{"kind":"row","deleted":true}`; file envelope with `deleted: true`), since export does not
  produce them. Actual output kept in `F03-results.json`.

## Observed results

### 1. Raw attachment via `config.json` `managed_paths`, A → B → C

| step | observed |
|---|---|
| A export (`managed_paths: ["attachments/raw.bin"]`) | `success`, package has `file/attachments/raw.bin` |
| B receive | `success`; `b_file_landed: true`, bytes `52415700415454414348` (= `RAW\x00ATTACH`) |
| B device config copied? | `b_has_device_config: false` |
| B export | `success`, `b_package_has_attachment: false` |
| C receive of B's package | `success`, `c_file_landed: false` |

The attachment travels exactly one hop. B stores it but cannot re-publish it: export builds file
assets only from B's own `.lessonkit/course-sync/config.json` and the fixed
`.lessonkit/{goals.json,course-preferences.json,practice-sets/**,learning/**}` set, never from
files it received. C therefore never sees the attachment.

### 2. Explicit file tombstone received by B, then B re-exports

Three variants, all with B already holding the file (`first_receive: success`):

| variant | plan changes | receive | file after tombstone | B export mentions file | B export deleted assets |
|---|---|---|---|---|---|
| raw `attachments/raw.bin`, `deleted` + content | `[]` | `success` | still present (`true`) | `false` | `[]` |
| `.lessonkit/practice-sets/ps-002.json`, `deleted` + content | `["file/.lessonkit/practice-sets/ps-002.json"]` | `success` | deleted (`false`) | `false` | `[]` |
| raw `attachments/raw.bin`, minimal `{"kind":"file","deleted":true}` | `[]` | `success` | still present | `false` | `[]` |

So: (a) a file tombstone is applied only when the receiving device itself projects that path
(standard managed folder worked; a config-declared raw attachment did not — the plan was empty and
the receive still reported `success`); (b) in every case the tombstone does **not** survive a
re-export — the file identity is simply **missing** from B's package, with no `deleted` marker.
A third device receiving B's package has no way to learn the file was deleted.

Fixture limitation: the intended "C already holds the file, then receives B's package" check is
invalid in this run — C was created after the tombstone was forged, so `holder_file_before: false`.
The decisive fact is the missing identity in B's export, not the C replay.

### 3. KP explicit deletion round-trip, histories retained

Initial state on A and B identical: KP `kp-1`, problem `prob-1`, attempt `answer-1`,
`practice_runs` history row.

| step | observed |
|---|---|
| A export → B receive | both `success` |
| B receives forged `row/knowledge_points/["kp-1"]` tombstone | `success`; counts `{kp:0, problems:1, problem_attempts:1, practice_runs:1}` |
| B re-export | `success`; `b_export_has_kp_tombstone: false`, `export_deleted_assets: ["row/problems/[\"prob-1\"]"]`, attempts `true`, practice_runs `true` |
| A receives B's re-export | `success`, `failed: []`; A counts unchanged `{kp:1, problems:1, attempts:1, practice_runs:1}` |

Histories survive the deletion on the receiver (rows are retained; only the KP and its grade-like
side tables are removed — consistent with `test_an_imported_deletion_keeps_the_writer_side_effects`).
Round-trip back to A does not propagate the deletion: A still has the KP. Notably B's package
instead carries a tombstone for the still-present `problems` row, and A accepted the package with
`success` without deleting its own `prob-1`; the reason for that asymmetry was not traced.

### 3b. Local deletion → export (no forged package)

A exports once (baseline), then deletes the KP locally and exports again:
`post_delete_has_kp_row: false`, `post_delete_deleted_assets: []`. The deletion is published as
"row absent", with no tombstone, so even the origin device cannot tell a remote peer that the KP
was deleted.

## Source evidence (read-only)

- `workbench/data/course_sync.py:391-403` `_projection`: assets = DB projection +
  `_managed_files(...)` + `pending_files`; nothing re-emits a previously received or locally
  removed asset as deleted.
- `workbench/data/course_sync.py:336-388` `_managed_files`: file set comes solely from the local
  `.lessonkit/course-sync/config.json` `managed_paths` and the fixed
  goals/preferences/practice-sets/learning paths; received raw attachments are outside that set.
- `workbench/data/course_sync.py:467-473` `_execution_projection`: the only place tombstones are
  synthesized, and only for superseded execution/parked-checkpoint assets.
- `workbench/data/course_sync.py:476-499` `export_course`: reuses a destination's previous
  manifest for lineage/identity continuity; nothing observed there regenerates deletions.
- Receiver-side tombstone application matches the existing tests
  (`tests/workbench/test_course_sync_receive.py:373-448`, `:512-555`), so the receive behaviour
  above is the same contract those tests exercise, not a probe artifact.

## Limitations / not claimed

- No full test suite, no pytest run; `openspec validate`, compileall and guards were out of scope.
- The "raw attachment tombstone ignored" explanation is inferred from an empty
  `plan.changes`; the exact filter in inspection/apply was not traced in code.
- The `problems` tombstone appearing in B's re-export and A's silent non-application are recorded
  as observed anomalies, not diagnosed.
- Nothing here asserts a design fix or delivery; the parent owns `course_sync.py` and decides
  whether these are intended one-hop semantics or a regression.
