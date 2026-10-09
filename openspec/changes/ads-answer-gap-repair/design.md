## Context

See `proposal.md` — Why. Constraints that shape the approach:

- **Pool**: `pool/c02.db`, 497 rows. Gap inventory measured read-only:
  109 keyless micro-quiz rows (65 `yes_no` without options, 42
  `single_choice`, 2 `multiple_choice`), 3 rows with empty `solution`, 325
  keyed rows whose `error_reason` is under 40 characters (p50 = 6; the most
  common value is the generic "概念辨析易混").
- **The answers already exist twice.** All 109 keyless rows carry a
  `solution` with an explicit 【答案】 segment (e.g. `A：O(log n) for
  INSERTION…`, `是（True）`, `b、c`), and every row's `source_evidence`
  points into `题库/期中` (6 md) or `题库/期末` (43 md), the conversions
  that were actually ingested. `题库原料/` holds the originals: the pintia
  answer-sheet exports under `题库原料/期末/*.html|mhtml` carry each item's
  `checked` radio state plus the grading verdict, and the CC98 答案页 PDFs
  carry the answer page of the same paper.
- **Known trap in the sources**: per `ads-pool-content-repair` design,
  `CC98_topic6342400`'s 对/错/答案错误 marks are the original student's
  results, not keys — 40 of the 109 keyless rows cite that file.
- **Write path (already shipped)**: `ingest recipe problem-patch --input
  <manifest> --apply` — one transaction per batch, per-batch manifest
  snapshot with `previous` values, DB backup, `ingest rollback --batch`.
  The gate rejects unknown ids/fields, no-change rows, duplicate ids, and
  validates the touched fields (`validate_answer_key`, `validate_payload`,
  markup on `solution`).
- **Patch-gate weakness**: like `ads-pool-content-repair` before us, we
  validate our own manifests in full before submitting (the gate re-runs
  only what the patch touches, and does not re-check labels — we do not
  touch labels anyway).
- **Learning records now exist**: `problem_progress` 36,
  `problem_attempts` 39, `review_schedule` 36. Unlike the earlier repair
  (0 records), this run must never delete rows — it does not; every write
  is an in-place UPDATE keyed by unchanged `problem_id`.

## Goals / Non-Goals

**Goals:**

- 0 keyless micro-quiz rows: every objective row carries a shape-valid
  `answer_key`, a short-tag `error_reason`, and a `source_answer` saying
  where the key came from.
- 0 empty `solution` rows.
- No keyed row keeps a sub-40-character generic `error_reason`; each reads
  as a specific 20–100 character sentence about why a learner picks wrong.
- Every batch is independently rollbackable; the learning records and all
  untouched fields survive byte-identical.

**Non-Goals:**

- No code, schema, gate or CLI changes (`skip_specs: true`).
- No rewriting of stems, options, `source_evidence`, knowledge-point
  bindings, difficulty columns, or labels.
- No touching the 346 existing answer keys.
- No backfilling anything that has no evidence in source or solution —
  a row that survives neither leg of the derivation chain stays keyless
  and goes on the report instead.

## Decisions

- **D1 — Two-leg derivation chain, source first.**
  `source_evidence` → read the cited `题库/` md (and, where it helps,
  the matching `题库原料/` original: checked radio state, answer page) to
  determine the key. If the source cannot determine it, fall back to the
  row's own `solution` 【答案】 segment. `source_answer` records which leg
  decided, the file and location, so a reviewer can replay it. Chosen over
  "source only" (would leave rows keyless for no reason) and "solution
  only" (ignores the answer pages the user asked us to read).
- **D2 — Dual verification, conflicts never auto-write.** Every one of the
  109 keys is computed from both legs where the source speaks. A mismatch
  lands on a manual review list with both readings; only a human-settled
  value enters the manifest. Student 对/错 marks in
  `CC98_topic6342400` are never key evidence (D1 trap above).
- **D3 — Two `error_reason` styles, per user decision.** The 109 newly
  keyed rows get a short tag (≤15 characters, e.g. "摊还界与最坏界关系")
  matching the existing 346. The 325 pre-existing short ones are expanded
  into specific 20–100 character sentences extracted from each row's own
  `solution` — what the distractor gets wrong, not "概念辨析易混".
- **D4 — One batch per chapter, preflight → apply → verify.** 15 patch
  batches (ch01…ch15), each produced from its chapter's review table,
  preflighted, applied, then checked before the next chapter starts. Every
  batch id, backup path and rollback command is recorded in the ledger.
- **D5 — Preflight is a superset of the gate.** Before apply: full
  `validate_payload` per row, key shape per quiz type (yes_no ∈ {是,否},
  single ∈ options, multi ⊆ options), `error_reason` non-empty and within
  the D3 bound, no U+FFFD, markup validation on new `solution` text, every
  `problem_id` exists, no duplicate ids, every row actually changes
  something. Nothing reaches `--apply` without a green preflight.
- **D6 — Cross-check against existing keys as ground truth for style.**
  The 346 rows that already have keys were derived by
  `ads-pool-content-repair` from checked state + grading verdict; their
  `source_answer` format (`题库原料/…（判断第1题 T）`) is the format the
  new `source_answer` values follow.

## Risks / Trade-offs

- [A derived key is wrong and the learner is graded wrongly] — D2 dual
  verification + conflict review; per-batch `ingest rollback --batch`
  reverts a bad batch in one command.
- [Source files cited by `source_evidence` are missing or truncated in the
  citation] — D5 checks every citation resolves to an existing file before
  derivation starts; unresolved rows go to the report, not to a guess.
- [Expanded `error_reason` sentences are generic or drift from the
  solution] — they are extracted per row from that row's `solution`;
  acceptance checks count residual "概念辨析易混" stand-ins and sample
  each chapter.
- [437 touched rows in a pool that now has learning records] — UPDATE-only
  patches keyed by unchanged ids; acceptance diff proves learning-record
  tables byte-identical before/after.
- [The 109 short tags look inconsistent next to the 325 expanded
  sentences] — accepted: the user chose short tags for new keys and
  expansion for the existing 325; the split is recorded here so the next
  audit does not read it as drift.

## Migration Plan

1. Baseline: pool snapshot + dump + batch ledger + learning-record counts.
2. Derive (read-only): resolve source citations, build the 109-row review
   table, dual-check, settle conflicts; build the 325-row expansion table;
   draft the 3 solutions.
3. Preflight all manifests; only green manifests proceed.
4. Apply ch01 first as a pilot (its batch is verified end-to-end before
   the rest), then ch02…ch15.
5. Acceptance: counts (keyless 0, empty solution 0, short error_reason
   residue), `validate-pool.py`, `data audit`, practice-page spot render
   in 判断/单选/多选 shells, learning-record diff, ledger published.
6. Rollback strategy: per-chapter `ingest rollback --batch <id>`; full
   revert = roll back batches in reverse order to the baseline snapshot.

## Open Questions

None — scope, derivation authority, `error_reason` styles and openspec
record were all decided by the user before this design was written.
