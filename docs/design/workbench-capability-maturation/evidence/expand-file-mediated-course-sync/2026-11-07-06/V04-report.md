# V04 — F2 profile evidence check (read-only)

Restatement per AGENTS.md: layering Shell → Domain → Data, Content reads artifacts, no reverse
dependency; compatibility boundary — no user data/behavior change is proposed here; scope —
this is a diagnostic verification only, no production code, tests, docs or benchmark were
changed or run. Written file: `tmp/agent-runs/V04-report.md` only.

Artifacts examined: `tmp/agent-runs/f2-profile.json` (594 lines), `tmp/agent-runs/profile_f2.py`
(54 lines), `tmp/agent-runs/f2-profile.log`, and the code paths that produce every reported field
(`workbench/data/course_sync.py` lines noted below, `workbench/domain/course_sync.py`,
`workbench/data/active_practice.py`). A commit that changed the examined behavior landed *after*
the measured run: `9e24990c` at 14:57, run finished 14:51 (`f2-profile.json` mtime). The
profile therefore exercised `5d11d979`-era code.

## 1. Fixture counts — internally consistent, and the asset total reconciles exactly

Fixture body (`profile_f2.py` lines 9, 29–45) versus the DB counts the script itself recorded
(`counts()`, lines 14–16; JSON `source_counts`):

| Claim (fixture dict) | Evidence in `source_counts` | Verdict |
|---|---|---|
| knowledge_points 1000 | `knowledge_points` 1000 (ids `dmath-ch01-kp-0001`…`dmath-ch20-kp-1000`) | matches |
| problems 10000 | `problems` 10000 (ids `…-prob-00001`…`10000`) | matches |
| attempts 10000 | `problem_attempts` 10000 (1 per problem) | matches |
| papers 100 | not a SQLite table; 100 `.lessonkit/practice-sets/*.json` managed files (see reconciliation) | matches by arithmetic |
| unfinished 30 | `paper_state` 30, `practice_execution_ids` 30, `active_practice` 1, `active_practice_items` 100 | matches with caveat below |
| learning_files 500 | `.lessonkit/learning` 500 files (not table rows) | matches by arithmetic |
| attachment_bytes 104857600 | 100 files × `bytes(range(256))*4096` = 100 × 1,048,576 = 104,857,600 | matches exactly |
| chapters 20 | only encoded in id prefixes/kp distribution; no chapter table is counted | claim, not independently counted |

Table rows total **21,161** across 30 tables (30 non-`sqlite_%` tables minus the two excluded by
`counts()`, `profile_f2.py` line 15). Expected `assets` (`export_course` returns `len(assets)`,
`course_sync.py` line 558) decomposes exactly to the reported **24,790**:

- 21,161 row assets, with `active_practice` (1) and `active_practice_items` (100) folded into
  execution assets by `_execution_projection` (`course_sync.py` lines 418–462): −101 +101 = 0
- +29 parked execution headers and 2,900 parked execution items = 2,929 (each 100-item paper
  parks its predecessor; `active_practice.start_saved` → `paper_progress.park`,
  `active_practice.py` line 874, so 30 starts leave 1 selected + 29 parked)
- +700 managed files: 500 learning notes + 100 practice-set JSONs + 100 attachments
  (`_managed_files`, lines 341–382)
- 21,161 + 2,929 + 700 = **24,790** ✓

**Caveat on "unfinished 30":** only one practice run is *active* (`active_practice` 1,
`active_practice_items` 100). The other 29 are parked checkpoints inside
`paper_state.checkpoint_json`, which is the designed representation, not lost fixture data. The
JSON never records a checkpoint count, so the 29 figure is deterministic arithmetic from
`start_saved`'s park-on-new-start behavior, not a directly observed number.

## 2. Phase timings and gates — all three stated gates FAIL

`f2-profile.json` `phases`, and the same values in `f2-profile.log`:

| Phase | Seconds | Gate | Result |
|---|---|---|---|
| fixture | 3.617 | — | — |
| export | 125.441 | 30 s | **FAIL** (4.18× over) |
| initial_check (inspect vs empty target) | 42.837 | (5 s is defined for unchanged inspection) | 8.57× over 5 s |
| receive | 264.865 | 30 s | **FAIL** (8.83× over) |
| repeat_check (unchanged inspection) | 64.175 | 5 s | **FAIL** (12.84× over) |

Sum of phases 500.935 s (~8 m 21 s). Receive costs 2.11× export; the unchanged repeat inspection
is 1.50× *slower* than inspecting the same package against an empty target (64.175 vs 42.837) —
consistent with the target now projecting 21,161 local rows plus 700 files for comparison.

## 3. Receive result — reported success, verified only at count level

`receive_status` "success", `receive_failures` `[]`, `table_counts_equal` `true`; every one of the
30 table counts in `received_counts` is byte-identical to `source_counts` (row-by-row comparison of
the two dicts: 30/30 equal). Values worth noting: `active_practice` 1, `active_practice_items` 100,
`paper_state` 30, `practice_execution_ids` 30 on both sides.

Limitation: equality is `count(*)` per table only. No content digest, checksum or per-row
comparison exists in the profile, and the `TemporaryDirectory` (line 17) is deleted by the time of
this review, so the received database can no longer be inspected. "success" also means
`failed == []`; `applied` count is not recorded in the JSON.

## 4. Repeat-check anomaly — reproducible mechanism, explained by the later fix

Observed on the repeat inspection of the same, unchanged bundle (`profile_f2.py` line 50):
`repeat_changes` 0, `repeat_outgoing` 0, and **100 errors**, all
`code: "missing_asset"`, `message: "tracked asset is absent without an explicit deletion"`, for
identities `file/attachments/original-001.bin` … `original-100.bin` (100 entries, JSON lines
92–593). No other error codes appear.

Mechanism (code, not inference from the JSON alone):
- That message is emitted only by `plan_exchange` when `identity in base and (identity not in
  local or identity not in incoming)` — `workbench/domain/course_sync.py` lines 99–102.
- The identities are in `base` (the receiver acknowledged 100 file units,
  `course_sync.py` lines 903, 937) and in `incoming` (the bundle still holds them; a missing bundle
  file would instead produce `"asset file is absent"` from `read_exchange`, line 1360, and none was
  reported).
- Therefore the receiver's own `local` projection lacked them. At the measured revision,
  `_managed_files` scanned only `goals.json`, `course-preferences.json`,
  `.lessonkit/practice-sets`, `.lessonkit/learning`, referenced figures and the *local* config's
  `managed_paths`. The receiving course has no `.lessonkit/course-sync/config.json`, because
  `course-sync` paths are deliberately non-portable (`course_sync.py` line 394), so `attachments/`
  was never scanned even though `_write_file` had written the payloads. The learning notes and
  practice-set JSONs were not flagged only because those folders are scanned unconditionally.

Consequence had the run continued: `export_course` would have silently dropped those 100 tracked
assets — invisible in `receive_status "success"` and in the row-count equality, since files are not
table rows. The 0-changes/0-outgoing repeat result is therefore **not** a clean convergence signal.

Reconciliation with the follow-up fix: commit `9e24990c` ("fix: retain received course files and
deletion records across exchanges", 14:57, six minutes after the run) adds exactly the missing
piece — `_managed_files(..., tracked=state["base"])` now re-adds base-tracked file assets
(lines 383–390) — plus an export guard that raises on tracked-but-absent managed assets
(lines 495–498). On the current tree I re-ran the same receive→inspect sequence at tiny scale
(no benchmark; `TemporaryDirectory`, one row + one 1 MiB-class attachment, and again 3 knowledge
points + 3 problems + 3 attempts + saved paper + draft + learning note + 3 attachments): export
success, 0 inspection errors, receive success, 0 failed, attachments present in the target, repeat
inspection 0 changes / 0 outgoing / **0 errors**. So the F2 anomaly is pre-fix behavior, and the
failure is not reproducible at small scale at HEAD.

## 5. What is NOT established (limits of this evidence)

- One run, one machine, one cold sequence; no p95, no repeat variance. The brief's framing "one
  diagnostic, not formal percentile acceptance" is correct.
- Timing cannot be attributed to HEAD: the measured tree predates `9e24990c` and `5d11d979`'s
  post-run tree also carries unrelated coordinator edits. Gate verdicts apply to the measured
  revision only; HEAD timing is unmeasured (rerun prohibited by the brief).
- No CPU/memory/disk telemetry in the JSON; the run shares the machine with concurrent agent work,
  and earlier notes recorded ~70.5% memory in use, so absolute timings may be inflated by external
  load. `fixture` (3.617 s) shows the DB inserts themselves were cheap, which points the cost at
  export/receive/inspect rather than at fixture construction.
- `chapters` 20 and `papers` 100 are asserted by the fixture script, not counted by `counts()`;
  they are supported only by the exact asset-total reconciliation above.
- 30 tables were compared; `course_sync_checkpoint` and `course_sync_units` are excluded by design
  and were not verified.
- The 100 missing-asset errors were not reconstructable from disk (temp dir gone). The mechanism is
  read from code at the measured revision plus the later fix's diff; the tiny HEAD probes show the
  repaired path works, not that the F2 case now converges.
- No file content, attachment byte equality or per-asset receive success was verified — the profile
  stores none of it.

## Bottom line

Fixture composition (1,000 KP / 10,000 problems / 10,000 attempts / 100 papers / 30 started runs /
500 notes / 100 MiB attachments) is internally consistent, and `asset_count` 24,790 reconciles
exactly against 21,161 rows + 2,929 parked-execution assets + 700 managed files. Export 125.441 s,
receive 264.865 s and unchanged inspection 64.175 s all fail the 30 s / 30 s / 5 s gates by 4.2×,
8.8× and 12.8×. The receive reported success with equal table counts, but the follow-up inspection
found 100 tracked attachments absent from the receiver's projection — a pre-`9e24990c` receive
defect that the coordinator's existing fix addresses; the fix is present and passes a tiny
round-trip probe at HEAD, while the F2-scale rerun remains outstanding.
