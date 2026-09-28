## Context

See `proposal.md` — Why. Constraints that shape the approach:

- **Gate style**: ingestion is all-or-nothing. Every reason is reported per
  item and a single invalid item leaves the pool untouched; there are no
  override flags anywhere in the gate vocabulary, and the contract text tells
  the Agent to fix the manifest rather than drop items.
- **Layering**: pure rules live in `workbench/domain/` (no I/O, stdlib only),
  the pool lives in `workbench/data/`, gates in `workbench/ingest/`, and the CLI
  is a thin data interface. Python stdlib first; no non-stdlib dependency may
  be introduced for similarity or hashing.
- **Read-only doctrine**: ordinary conversation may not write. The audit is the
  read-side counterpart of that rule and must be safe to run at any time.
- **Existing requirement**: `micro-quiz-content` already states that the
  contract "SHALL be enforced for the parts the patch touches", while
  `plan_problem_patch` applies neither the label bounds nor the markup check.
  Patch parity is therefore a conformance fix, not a new requirement.
- **Measured motivation** (ADS pool, 896 rows): 14 byte-identical duplicate
  groups / 18 surplus rows; ~134 rows sharing a 120-character stem prefix; 121
  fragment rows; 138 items whose options sit inline in the stem while
  `practice_modes` is empty; `display_title` empty on all 896 rows; 73
  orphaned figure files left by a rolled-back batch. Every one of those classes
  is a check the audit owes.

## Goals / Non-Goals

**Goals:**

- A manifest can no longer store a second copy of a problem that already
  exists, in the same manifest or in the pool, and the refusal says which row
  already covers it.
- One command answers, without writing, what content defects a pool holds and
  how many, grouped by chapter and class, with a non-zero exit suitable for
  gating.
- The in-place edit path cannot store a row state that ingest would refuse.

**Non-Goals:**

- No fuzzy similarity: no embeddings, no simhash/minhash, no edit distance.
  Only the normalization variants are collapsed; everything else is treated as
  a different item on purpose.
- No automatic correction: the audit reports, the repair decides and acts
  through the existing `problem-patch` / `data delete problem` paths.
- No cross-course or cross-workspace comparison; per-workspace pools stay
  independent.
- No new pool column, and no migration.
- No UI surface for the audit in this change; the CLI is the entry point.

## Decisions

### D1 — Identity is the normalized whole stem, never truncated

Normalize with a pure function: Unicode NFKC, case fold, collapse all
whitespace, drop punctuation and markdown scaffolding, canonicalize `$…$`
content (strip `\left`/`\right`, normalize `\le`/`\leq`, drop spacing macros),
and remove export-noise lines (`得分 N分`, `作者`, `单位`, `创建提问`,
`评测结果`, `答案正确/错误`, Pintia submission links). Compare the whole
result.

*Alternatives rejected*: a 400-character prefix key (that is precisely what let
the ADS near-duplicates through, because the differing suffix is what made them
look distinct), and a similarity threshold over shingles (no stdlib-only
implementation, and it would merge genuinely different problems).

### D2 — The check runs in the gate, before any write, over the target scope

The content-bundle gate normalizes the scope's existing rows once (a single
`SELECT problem_text … WHERE problem_id LIKE '<course>-<chapter>-%'`, normalized
in process) and checks each manifest item against that set and against the
items earlier in the same manifest. Micro-quiz bundles reuse the same check.
Cost is linear in scope size; the largest known pool is under a thousand rows.

### D3 — Refusal only, no override flag

A duplicate is refused with the colliding problem id and its source evidence.
There is deliberately no `allow_duplicate` flag: a genuine second copy is
either a source variant that differs in the stem (and therefore passes), or it
is the same problem the pool already holds — in which case the honest move is
to edit the existing row in place rather than store it twice.

*Alternative considered*: an item-level opt-out. Rejected to keep the gate
vocabulary override-free; revisit only if a real need that the in-place path
cannot serve appears.

### D4 — One shared normalizer for gate and audit

The identity function is the single source of truth for both the gate and the
audit's duplicate grouping, so the two can never disagree about what counts as
duplicate. It lives with the other pure rules and is unit-tested on its own.

### D5 — Audit shape: named checks, machine-readable findings, gateable exit code

`lesson-kit data <ws> audit [--check <name>]… [--json]` with checks
`duplicates`, `fragments`, `unmarked-objective`, `untitled`, `figures`,
`orphan-figures` (default: all). Findings are a list of
`{check, chapter, problem_ids, detail}`; the human output groups by check and
chapter. Exit code 0 when nothing is found, 1 when a selected check reports
findings, 2 on usage error — consistent with the CLI's existing failure code.

### D6 — Fragment detection is a report, not a merge

A row is reported as a fragment when its normalised stem is a prefix or suffix
of another row's stem, or when it starts with a continuation token (`where`,
`then`, `for example`, `given that`, `such that`, `and`, `or`, `and thus`) or
holds only an option label or a lone image reference with no interrogative
content. Findings carry the suspected parent id when one exists. Merging stays
a repair decision made through `problem-patch`; the audit never edits.

### D7 — Figure checks resolve logical paths both ways

`figures` resolves every Markdown image reference in `problem_text` and every
`figure_paths` entry against the declared area
`.lessonkit/figures/<course>/<chapter>/`; unresolved targets are findings.
`orphan-figures` lists files under `.lessonkit/figures/<course>/**` that no
problem and no knowledge point references — the class that a rolled-back batch
leaves behind.

### D8 — Patch parity keeps the touch-only rule

`plan_problem_patch` calls the same label-bound and markup helpers the ingest
gate uses, for the fields the patch touches. Untouched legacy fields are still
not re-validated, exactly as the in-place-edit design states, so a repair is
never blocked by damage it did not introduce.

### D9 — No stem length bound for objective items

The micro-quiz contract carried `MAX_STEM_CHARS` (800 since 2026-09-25, 200
before that) as a "sanity ceiling". It is removed rather than raised again: the
ADS repair measured 14 objective rows over it, and the ceiling was the single
reason real 判断题/单选题 sat in 综合题. Length is not an answering-form property —
the option-count bound (2–6) and the one-knowledge-point rule already keep micro
cards practice-shaped, and a learner-facing card can render a long stem.

*Alternative rejected*: raising the bound to 1300. Any finite number repeats the
same failure on the next paper that is slightly longer; the author's own note on
the constant already said it was a ceiling, "not a design statement". Length is
also not what makes a question answerable.

*Alternative rejected*: shortening the stems to fit. That edits the source
question (dropping assertions or scenario text), which the repair's fidelity
rule forbids.

The patch path, the ingest gate, and the bridge contract text are all updated in
the same change, so no path accepts what another refuses.

## Risks / Trade-offs

- **[A legitimate second copy is refused]** → the refusal names the existing
  row and its source evidence; the deliberate path is in-place editing of the
  existing row, and an item whose stem genuinely differs still passes.
- **[Near-duplicates that differ only after the point of comparison are missed]** →
  the whole-stem identity removes the truncation blind spot; anything beyond
  that is a similarity question and is deliberately out of scope, so the audit
  reports only exact-after-normalization groups.
- **[Fragment heuristic flags a legitimate short problem]** → findings are
  advisory and carry their evidence; the audit never edits, and the exit code is
  scoped by `--check` so a caller can gate on the checks it trusts.
- **[Audit cost on a large pool]** → checks read one scope at a time and can be
  selected individually; no check writes, so a partial run is always safe.
- **[Two places could drift on label bounds]** → both call the same helpers,
  and the parity test asserts that the patch path refuses exactly what the gate
  refuses.

## Migration Plan

1. Land the pure identity rules with their tests.
2. Wire the gate check and the patch parity fix; the ADS repair waits on this
   ordering only for its *verification* step, not for its execution.
3. Add the audit command, then run it over the ADS pool before and after the
   repair to record the finding counts as conformance evidence.
4. Update `FILE_CONTRACT.md`, `docs/GLOSSARY.md`, `docs/PRODUCT-MANUAL.md`, and
   move dedup out of the deferred list in `docs/FUTURE-DEVELOPMENT-NOTES.md`.
   No schema migration, so rollback is a plain revert; a manifest that used to
   store a duplicate will now be refused, which is the intended change.

### D10 — Measured input contract (from the ADS repair, 2026-09-26)

The repair pass produced the real numbers this change's normalization and audit
must handle, and the reusable write-up of how they were measured:

- 896 imported rows → 497 after the repair; 399 rows were byte-identical
  duplicates, split fragments, or non-questions (two Pintia submission links).
- Byte-identical duplicate groups after the per-chapter passes: 63 groups / 85
  surplus rows — all of them **cross-chapter** (each chapter only dedups within
  itself), which is why the final pass has to run pool-wide.
- Fragment classes seen: a stem starting with a connective (`where`, `then`,
  `For example`, `given that`), a row holding only an option label, a row
  starting with an image reference, sub-questions split into their own rows.
- The proof-of-absorption rule that worked: normalize away `$…$` and `` `…` ``
  and HTML tags, compare the fragment's alphanumeric skeleton (30 characters is
  the reliable probe length) against the target's stem **and** its options.
  Two classes defeat it and must go to a human list: fragments whose content is
  a pure formula, and fragments that are really one option of the target.
- The full write-up, including the errors made along the way and what worked,
  lives with the repaired course under
  `repair/经验文档-题库批量修复.md`; the final numbers are in
  `repair/report-final.md`.
