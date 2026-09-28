# Tasks

## 1. Baseline and safety net

- [x] 1.1 Dump all live rows of `pool/c02.db` to a baseline JSON and record per-chapter counts, `practice_modes` distribution, `figure_paths` and figure-reference resolution (`repair/dump_pool.py`).
- [x] 1.2 Snapshot the pool file before any write step, and record the batch ledger (`ingest batches --json`) including the rollback path for each batch.
- [x] 1.3 Confirm zero learning records for the target rows (`problem_progress`, `problem_attempts`, `review_schedule`, `learner_signals`), and re-check per row with `data <ws> history problem <id>` before each deletion.
- [x] 1.4 Snapshot the Temp-only image cache into `repair/figure-rescue/` with a manifest mapping cache file → pool reference (done for the current cache state; re-run if the cache changes).

## 2. Re-extraction tooling

- [x] 2.1 Implement the HTML/MHTML formula extractor that takes exactly one copy per formula: `application/x-tex` annotation when present, else the text after `</mrow>` inside `<math>` (never the whole `<math>` textContent).
- [x] 2.2 Self-check the extractor on the four sources that carry `application/x-tex` (`Jan 1 2025`, `Jun 21 2022`, `Jun 22 2022`, `Jun 23 2022`): extracted formula count equals annotation count, and no formula appears twice.
- [x] 2.3 Implement the text-layer PDF path (`pdftotext`) for the two damaged PDF-derived sources, and assert the PDF text is single-copy for the sampled items.
- [x] 2.4 Implement the source→item matcher: map each pool row to its source document and question position using `source_evidence` plus normalized-stem matching; emit a damage map (which rows have doubled formulas, fragments, or a lost figure binding) and flag unmatched rows for manual review.

## 3. ch01 pilot

- [x] 3.1 Re-extract the ch01 rows whose formulas are damaged and produce per-row before/after text pairs.
- [x] 3.2 Produce per-item review cards for all 161 ch01 rows (batched sub-agents): stem completeness, option set, sub-question merge target, answering form, knowledge-point binding, figure ownership, derivable answer key, confidence.
- [x] 3.3 Build the five manifests for ch01 — `problem-patch`, delete (duplicates and merged fragments), retype (判断/小测/综合), `display_title` + `topic_label`, answer keys — each row carrying its reason and source reference.
- [x] 3.4 Run the preflight validator over the manifests (exactly one `kp_ids` for micro, 2–6 unique options, `answer_key` matching an option or 是/否, label bounds 40/80, no HTML beyond `<sup>/<sub>`, no U+FFFD, non-empty `source_evidence`).
- [x] 3.5 Apply the ch01 patch batch and verify: 896 → (896 − ch01 deletions) rows, ids unchanged, `ingest batches` shows one new batch, patch counts match the manifest.
- [x] 3.6 Present the ch01 deletion list to the user, execute the approved deletions, and verify each victim still has no learning record at deletion time.
- [x] 3.7 Render check for ch01: practice page in each of 判断 / 小测 / 综合题 plus the knowledge-point page; confirm titles, clickable options, KaTeX, figures, tables, code fences; capture screenshots.
- [x] 3.8 Pilot review with the user: freeze the judge rules as-is, or revise and re-run ch01 before the remaining chapters.

## 4. Remaining chapters

- [x] 4.1 ch02 — re-extract, review, manifests, preflight, patch, deletions, render check.
- [x] 4.2 ch03 — same shape.
- [x] 4.3 ch04 — same shape.
- [x] 4.4 ch05 — same shape.
- [x] 4.5 ch06 — same shape (contains the `ch06-mq-003/004` vs `ch06-prob-004` duplicate group and the `(6)` sub-question fragment).
- [x] 4.6 ch07 — same shape.
- [x] 4.7 ch08 — same shape.
- [x] 4.8 ch09 — same shape.
- [x] 4.9 ch10 — same shape (contains the cross-chapter duplicate with ch02).
- [x] 4.10 ch11 — same shape.
- [x] 4.11 ch12 — same shape (contains `c02-ch12-prob-001` vs `-003` duplicates).
- [x] 4.12 ch13 — same shape (contains the cross-chapter duplicate with ch14).
- [x] 4.13 ch14 — same shape.
- [x] 4.14 ch15 — same shape.
- [x] 4.15 Run the duplicate and fragment checks across all chapters after the last batch, so cross-chapter duplicates are judged once, not per chapter.

## 5. Figures

- [x] 5.1 Rebuild the figure→problem binding from source document order and rewrite the affected `problem_text` references to the logical paths already on disk.
- [x] 5.2 Verify every remaining image reference resolves to a file under `.lessonkit/figures/`, and that `figure_paths` agrees with the Markdown reference.
- [x] 5.3 Classify the figure files that no surviving row references (delegated vision pass), list the information-free ones with their evidence, and — after the user reviews the list — remove them.

## 6. New sources (after the repair is frozen)

- [x] 6.1 Build one content bundle for the three never-imported clean sources: the 15-16 paper (text-layer PDF), the 分治法 screenshot item (stem, options and the checked answer transcribed), and the 张国川班 answer paper's objective items (which carry real keys).
- [x] 6.2 Ingest that bundle as a separate batch with its own figures, then verify chapter/knowledge-point bindings and that it is independently rollbackable.

## 7. Report and handoff

- [x] 7.1 Publish the before/after distribution table (rows, practice modes, duplicates, fragment classes, formula damage) with per-chapter counts.
- [x] 7.2 Publish the unrecoverable list with problem ids, source references and the reason each row cannot be repaired from text.
- [x] 7.3 Publish the deletion ledger (group, survivor, victims, reason) and the answer-key derivation ledger (row, key, source file, paper number, signal used).
- [x] 7.4 Hand the judge criteria produced here — the normalization key, the defect classes and their measured sizes — to `content-dedup-and-audit` as the audit's input contract.
