# Tasks

## 1. Baseline and safety net

- [x] 1.1 Snapshot `pool/c02.db` and dump all 497 rows to a baseline JSON in
  `repair/` (reuse `repair/dump_pool.py`), record the batch ledger and the
  per-batch rollback path before any write.
- [x] 1.2 Record learning-record counts (`problem_progress` 36,
  `problem_attempts` 39, `review_schedule` 36) as the before-image of the
  acceptance diff.
- [x] 1.3 Confirm the gap inventory from the baseline (109 keyless / 3 empty
  solution / 325 short `error_reason`) matches this change's numbers, and
  re-run it as a script so acceptance can diff against it.

## 2. Derive the 109 missing answer keys (source first)

- [x] 2.1 Resolve every keyless row's `source_evidence` citation to an
  existing file under `题库/`, fix the truncated citations by prefix match,
  and report unresolved rows instead of guessing.
- [x] 2.2 Build the 109-row review table (id, quiz_type, options, cited
  source + location, source reading, `solution`【答案】 reading, both
  agree?) — batched sub-agents over the cited source files.
- [x] 2.3 Settle every conflict / low-confidence row manually; nothing
  unresolved enters the manifest (stays keyless and on the report).
- [x] 2.4 Shape-check each settled key against its quiz type
  (yes_no → 是/否, single_choice → one option, multiple_choice → subset of
  options) and write the `source_answer` citation for the deciding leg.
- [x] 2.5 Write the short-tag `error_reason` (≤15 chars, existing style)
  for each of the 109 newly keyed rows.

## 3. Fill the 3 empty solutions

- [x] 3.1 Read each cited source for `c02-ch04-prob-001`,
  `c02-ch13-prob-004`, `c02-ch07-prob-021` and draft a 【答案】【解析】
  solution matching the pool's existing style, with `solution_origin`
  set by actual origin (source-derived vs generated).

## 4. Expand the 325 short error_reasons

- [x] 4.1 Batched sub-agents per chapter: for each short-`error_reason`
  row, extract a specific 20–100 character distractor explanation from
  that row's own `solution` (what the wrong choice gets wrong).
- [x] 4.2 Review pass: reject stand-ins that still read as generic tags
  ("概念辨析易混" etc.), reject text that contradicts the row's
  `solution` or `answer_key`, and re-draft rejects.

## 5. Preflight (superset of the patch gate)

- [x] 5.1 Write the preflight script covering design D5: full
  `validate_payload` per row, key shape per type, `error_reason` non-empty
  and within the style bound, no U+FFFD, markup check on new `solution`
  text, ids exist, no duplicate ids, every row changes something.
- [x] 5.2 Run preflight over all chapter manifests; every manifest green
  before any apply.

## 6. Apply per chapter

- [x] 6.1 Apply ch01 as pilot: `ingest recipe problem-patch --apply`,
  verify row count / keyless count / batch id / backup file, and render
  判断 + 单选 shells on the practice page.
- [x] 6.2 Apply ch02…ch15, one batch each, verifying each batch's counts
  before the next; record batch id, backup path and rollback command per
  chapter in the ledger.

## 7. Acceptance

- [x] 7.1 Gap diff against baseline: keyless = 0, empty `solution` = 0,
  sub-40-char `error_reason` residue on pre-existing rows = 0 (new 109
  short tags excepted), 346 existing keys untouched.
- [x] 7.2 Run `pipeline/scripts/validate-pool.py --db pool/c02.db` and
  `lesson-kit data <ws> audit`; both exit 0.
- [x] 7.3 Learning-record diff: the three tables byte-identical to 1.2's
  before-image; spot-check a keyed row's `problem_attempts` still reads.
- [x] 7.4 Practice-page render spot check: a newly keyed 判断/单选/多选 item
  grades and shows its error reason; a 325-row item shows the expanded
  sentence; one of the 3 new solutions displays.

## 8. Report and handoff

- [x] 8.1 Publish the derivation ledger (id, key, deciding leg, source
  file + location, confidence) and the conflict list with resolutions.
- [x] 8.2 Publish the batch ledger (chapter → batch id → rollback
  command) and the residual report (any row still keyless, with reason).
- [x] 8.3 Check off this change's tasks and run
  `openspec validate ads-answer-gap-repair`.
