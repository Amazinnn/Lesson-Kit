## Context

See `proposal.md` — Why. Constraints that shape the approach:

- **Pool**: `pool/c02.db` of the ADS workspace. 896 `problems` rows, all written
  by one apply (`created_at` 2026-09-25 15:44:30Z), batches `batch-018` …
  `batch-032` (one per chapter). `problem_progress`, `problem_attempts`,
  `review_schedule`, `learner_signals` are **empty** — no learning record
  exists yet.
- **Available write paths** (all already shipped, no new code needed):
  `ingest recipe problem-patch --input <manifest> --apply` (cross-chapter,
  one transaction, one batch id, rollback restores old values),
  `data <ws> delete problem <id>` (transactional physical deletion, cascades
  over that problem's learning records), `ingest batches`, `ingest rollback
  --batch`. `problem-patch` cannot delete rows and cannot change `problem_id`;
  `data delete problem` is the only removal path.
- **Patch-side validation is weaker than ingest**: `plan_problem_patch`
  re-validates only the touched fields and does **not** apply
  `LABEL_FIELD_LIMITS` (topic_label 40 / display_title 80 / display_summary 200)
  or the markup gate. The repair therefore validates its own manifests before
  submitting them.
- **Rendering surface**: the practice page renders a Markdown subset
  (`#`..`###`, lists, `>`, GFM tables, fenced code, `$…$`/`$$…$$` via KaTeX,
  images, `**bold**`, inline code, `<sup>/<sub>` only) after HTML-escaping;
  indentation outside fenced code collapses. `display_title` is the practice
  header and falls back to 未命名题目; `topic_label` groups the knowledge-point
  page and falls back to 未分类; `display_summary` is rendered nowhere.
- **Source material**: `题库/期中` (6 md) + `题库/期末` (43 md) are the
  conversions actually ingested (15 of them contributed all 896 rows);
  `题库原料/**` holds the originals — 31 HTML/MHTML, 7 text-layer PDFs, 3
  image-only PDFs, 3 pure images, 4 md-only, 1 duplicate md. Figures live in
  `题库/*/assets/**` and `.lessonkit/figures/c02/**`.
- **Answer material**: the pintia answer-sheet exports under
  `题库原料/期末/*.html|mhtml` carry each item's `checked` radio state plus the
  grading verdict; `CC98_topic6342400`'s 答案正确/答案错误 marks are the
  original student's results, not keys.

## Goals / Non-Goals

**Goals:**

- Every one of the 896 rows reads as a complete, displayable problem: one copy
  of each formula, no fragment rows, options in the options field, no export
  noise, a filled `display_title` and `topic_label`.
- The practice mode of each row matches its real answering form, so 判断/小测
  shells actually receive the items that belong to them.
- No duplicates under the stated identity rule; ids and learning records
  preserved.
- Figures resolve and belong to the problem that references them.
- Answer keys present where the source答卷 supports deriving them, each with
  its origin recorded; absent (keyless) elsewhere — never invented.
- The whole operation is per-chapter batch-rollbackable and reviewable.

**Non-Goals:**

- No changes to lesson-kit code, schema, gates or CLI surface. Tool-side gaps
  are proposed in `content-dedup-and-audit`.
- No paraphrasing: wording, numbers, options and answering form stay the
  source's; only structure is restored (see Decisions).
- No authoring of content that never existed in any source (84 rows whose
  options never landed in any file stay option-less and are reported).
- No re-import / delete-all-then-reimport.
- No difficulty rating (a separate `lesson-kit difficulty` pass).

## Decisions

### D1 — Repair in place with `problem-patch`, never re-import

Ids are the row identity and everything a learner records hangs off them; the
repository's own doctrine after `364f138` is *never by deleting and
re-importing*, and the two earlier delete-and-reimport waves each made the bank
worse. Deletions are limited to rows that are duplicates, fragments whose
content moved into a surviving row, and non-question shells.

*Alternative rejected*: rebuild a clean bundle and re-import — loses ids,
re-runs the extractor that caused the damage, and needs a 3rd full re-import.

### D2 — Re-extract formulas from the originals, no heuristic un-doubling

Each `<math>` block in the HTML/MHTML originals contains the structured MathML
**and** a raw LaTeX text sibling; the converter took both. The repair reads one
copy deterministically: `<annotation encoding="application/x-tex">` when
present, otherwise the text after `</mrow>` inside `<math>` (equivalently the
`katex-html` span text); text-layer PDFs are re-read with `pdftotext` and are
single-copy by construction. 21 sources are affected (19 HTML/MHTML + 2
text-layer PDFs).

*Alternative rejected*: detect `$A A$` repeats and halve them — measured false
positives on legitimate ellipsis lists (`a=(a_1,a_2,\ldots,a_j,\ldots)`), and
it cannot decide which copy is authoritative.

### D3 — One row is one practice unit; fragments merge into their parent

A multi-part question (6-1/6-2/6-3, (I)(II)(III), a 程序填空 with several
blanks) is **one** row carrying the whole stem, its sub-questions and its
options. Only items that the original paper numbers as separate problems get
separate rows. Rows that the import split off (`where …`, dangling `A.`,
`![](`-leading option-only rows, sub-question rows) are merged back into their
parent and then deleted.

*Rationale*: the CLI has no parent/child relation, so a split-off sub-question
is an unanswerable row — which is exactly what the 121 fragment rows are.

### D4 — Practice mode follows the answering form

判断题 → `quiz_type: "yes_no"` (options omitted; the CLI derives the default
是/否 pair). 选择题 → `single_choice` / `multiple_choice` with 2–6 unique
options moved out of the stem into `options`; `practice_modes` is derived by
the CLI from `quiz_type`. Items that genuinely are not objective
(程序填空/证明/建模/long scenario) keep no `quiz_type` and stay 综合题.
`problem_type` keeps its contract meaning (judgement/single-choice items are
`other`); it is **not** the practice-mode field.

Hard bounds respected: a micro item needs exactly one `kp_ids` entry and 2–6
unique options. There is **no** stem length bound — the 800-character ceiling was
removed while repairing this pool (`content-dedup-and-audit`), because it had
diverted 14 real objective items, this chapter's long multi-assertion questions
among them, into 综合题 purely by length.

### D5 — Dedup identity rule, with a reviewed list before any deletion

Normalize (lowercase, collapse whitespace, drop punctuation, canonicalize
`$…$` formulas, strip `(N分)`-style noise) and compare the **whole** stem —
no truncation (the build script's `norm()[:400]` is why near-duplicates
survived). Then:

- byte-identical stems → one survivor;
- same stem **and** same sub-question/option set → one survivor (the row with
  the complete stem, the correct chapter/knowledge-point binding, and the
  smaller id wins);
- same stem but a **different** sub-question/option set → different problems,
  both stay;
- similar-but-not-identical stems stay (per
  `docs/FUTURE-DEVELOPMENT-NOTES.md`).

Cross-chapter duplicates are a binding bug as much as a duplicate: the
survivor keeps the chapter its content belongs to. Every deletion is reported
with the group, the survivor and the reason, and the user reviews the list
before it is executed.

### D6 — Answer keys: derive only where the source答卷 proves them

Rule: a `checked` radio state plus `答案正确` yields that option as the key; for
判断题 a `答案错误` verdict yields the opposite of `checked` (two-valued).
Single-choice items are only derivable when the verdict is `答案正确` (a wrong
verdict only excludes one option). Matching is by normalized stem plus option
text — never by question number, because the same paper's numbering differs
between the md, the HTML export and the PDF, and the 多班合集 repeats stems.
The key goes to `micro_quiz.answer_key`; its origin (source file + paper
number + which signal was used) goes to `source_answer` so the row documents
the derivation instead of silently asserting it. Items without a derivable key
stay keyless — which the contract explicitly allows (they show 本题未录入答案键).

### D7 — Titles: `display_title` from the stem, `topic_label` from the binding

`display_title` (≤ 40 characters, Chinese) states what the item asks, e.g.
「AVL 树删除后判断结点关系」; `topic_label` (≤ 40) is the bound knowledge
point's short name. `display_summary` is left empty — nothing renders it.

### D8 — Figures: re-bind by source, keep the file, fix the reference

A row's stem must reference only figures that belong to it. The binding is
rebuilt from the source document's own ordering (the figure that follows the
stem belongs to it), and the reference is rewritten in `problem_text` to the
logical path already on disk (`c02/chNN/<sha256>.<ext>`). No figure file is
re-ingested; files that no surviving row references and that carry no
information are removed as files, with the list reviewed first.

### D9 — Per-chapter batches, ch01 first

Each chapter is one `problem-patch` batch (own transaction, own batch id) plus
its own reviewed deletion step, so a chapter can be rolled back on its own.
`ch01` (161 rows, the heaviest MathJax and 判断题 mix) runs first as a pilot;
the user reviews the before/after sample, the rendered screenshots and the
deletion list before the remaining 14 chapters are processed.

### D10 — The repair validates its own manifests

Because `problem-patch` does not apply the label-length or markup rules, a
preflight script checks every manifest item against the ingest contract before
submission: non-empty stem, ≤ 800 characters when the item carries a
`micro_quiz`, exactly one `kp_ids` entry for micro items, 2–6 unique string
options, `answer_key` identical to one of the options (or 是/否 for
`yes_no`), `topic_label` ≤ 40 / `display_title` ≤ 80, no HTML other than
`<sup>/<sub>`, no U+FFFD, and a non-empty `source_evidence`.

## Risks / Trade-offs

- **[Deletion is not reversible]** → pool snapshot before each step, per-chapter
  batches, deletion lists reviewed before execution, and `data history problem`
  checked per victim to confirm no learning record exists.
- **[Repair after practice starts would lose records]** → the repair must finish
  before the learner practises; batch rollback is refused for batches with
  dependent records, so the window is now-or-never.
- **[Source-derived text may still be damaged where no clean original exists]**
  → the six image-only sources carry zero formula damage today; if a damaged
  item's original turns out to be image-only, the item is left as-is and listed
  instead of guessed at.
- **[84 rows have no options anywhere in text]** → they stay as stem-only 综合题
  and are listed with ids; no content is invented.
- **[Micro bounds force some objective items to stay 综合题]** (more than 6
  options, stem over 800 characters) → accepted; the report lists each one with
  its blocking bound.
- **[Figure ownership is semantic]** — a figure can resolve while belonging to
  another problem; only source-order reconstruction finds these, so the audit
  proposed in `content-dedup-and-audit` cannot replace the manual pass.
- **[A large edit surface in one chapter]** → the pilot chapter is the
  smallest-risk place to discover a wrong judge rule before 14 chapters depend
  on it.

## Migration Plan

1. Snapshot the pool and the Temp-only image cache (done before analysis).
2. Pilot: ch01 — re-extract, per-item review, manifest preflight, `problem-patch`,
   reviewed deletions, UI check.
3. Remaining 14 chapters in the same shape, one batch each.
4. Freeze the repaired bank, then ingest the three never-imported sources as a
   separate batch.
5. Publish the report (before/after distributions, deletion ledger, the
   unrecoverable list, reusable scripts) in the workspace's `repair/`.

Rollback: `ingest rollback --batch <chapter batch>` restores the pre-patch
values of that chapter; deletion steps are recovered from the pre-step
snapshot, which is why they are snapshotted per chapter.
