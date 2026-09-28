## Why

The ADS workspace pool holds 896 problems imported through the agent bridge on
2026-09-25, and the bank cannot be practised as it stands:

- **Practice mode lost.** 649 of 896 items carry no `practice_modes`, so
  `_eligible_for_mode` only ever offers them in 综合题 — including 138 items
  whose options sit inline in the stem and are objectively 单选/多选. The
  practice forms 判断 / 小测 / 综合题 are decided by `quiz_type`, not by
  `problem_type`, and the import never set it for them.
- **Formulas are doubled.** The extractor copied each `<math>` block twice
  (structured MathML plus the raw LaTeX sibling), so 158 items read
  `$O(N)O\left(N\right)$`. The damage is deterministically reversible: the
  original HTML/MHTML carries the authoritative LaTeX (four sources even carry
  `application/x-tex` annotations), and the text-layer PDFs are clean.
- **Items are not items.** 121 rows are fragments of a parent question
  (`where …` half-sentences, a dangling `A.`, `![](`-leading option-only rows,
  sub-questions `(I)/(1)` split into their own rows); 34 rows were split off
  from the row above them.
- **Duplicates.** 14 groups are byte-identical (18 surplus rows, including
  cross-chapter duplicates such as `ch06-mq-003/004` vs `ch06-prob-004`) and
  about 134 rows share a stem prefix. The build script's text dedup ran before
  its secondary splitting, so splitting re-created duplicates.
- **Nothing is displayable.** `display_title` is empty on all 896 rows, so the
  practice header reads 未命名题目 and the knowledge-point page groups
  everything under 未分类. Some figures are bound to the wrong problem, and the
  sources that were never ingested include a whole paper and a fully readable
  single-item screenshot.

The pool has **no learning records yet** (`problem_progress`,
`problem_attempts`, `review_schedule` are empty), which is what makes an
in-place repair cheap right now: once practice starts, deletion cascades over
the learner's records and batch rollback is refused for dependent batches.

## What Changes

- Repair the existing rows **in place** with `problem-patch` (ids unchanged):
  one copy of each formula, fragments merged back into the parent item, options
  moved out of the stem into `micro_quiz.options`, export noise removed,
  display titles and topic labels filled, verified knowledge-point bindings,
  figures re-bound to the problem that references them.
- Set the practice mode that matches the item's real answering form
  (判断题 → `quiz_type: "yes_no"` with the default 是/否 options; 选择题 →
  `single_choice`/`multiple_choice` with 2–6 options), so objective items leave
  the exam-only fallback.
- Deduplicate by a stated rule: byte-identical duplicates and same-stem /
  same-subquestion rows collapse to one surviving row; stems that merely look
  alike stay (per `docs/FUTURE-DEVELOPMENT-NOTES.md`: strict on real
  duplicates, keep similar-but-different items). Every deletion is listed with
  its reason before it is executed.
- Derive answer keys where the source答卷 allows it (checked radio state plus
  the grading verdict), record the key's origin on the row, and leave the rest
  keyless.
- Remove what is not a question (two Pintia submission links, information-free
  figures) and report the items that cannot be repaired from text (84 rows
  whose options never reached any file) instead of inventing content.
- Ingest the three never-imported clean sources as one separate later batch,
  after the repair is frozen.
- No tool behaviour changes and no code changes in this repository. This change
  records the operation, the invariant list the repaired pool is judged by, and
  the acceptance checks; the capability gaps it exposes are proposed in
  `content-dedup-and-audit`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. A content repair pass changes data, not system behaviour, so no
requirement changes; `skip_specs: true` is declared in `.openspec.yaml`. The
invariants the repaired pool must satisfy are written in `design.md`, and the
audit that will check them is specified in `content-dedup-and-audit`.

## Impact

- **Data**: `pool/c02.db` of the ADS workspace (896 problems; 0 learning
  records), `.lessonkit/figures/c02/**`, and the repair workspace
  `repair/` inside the course folder (baseline dump, manifests, reports,
  scripts).
- **Source material**: `题库/**` is read-only reference; a snapshot of the
  Temp-only image cache was taken into `repair/figure-rescue/` before anything
  else, because that cache is the only other copy of 34 referenced figures.
- **Tool**: none. The repair uses `ingest recipe problem-patch --apply`,
  `data <ws> delete problem`, `ingest batches` and `ingest rollback --batch`,
  all of which already exist.
- **Risk**: row deletion is not reversible (each step is preceded by a pool
  snapshot and a reviewed deletion list); the repair must not run after the
  learner starts practising.
