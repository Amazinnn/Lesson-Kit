## Why

Two course-ingest jobs completed in the last four days — `ncmc`
(全国大学生数学竞赛, 17 papers 2009–2025 plus a textbook, 8 chapters) and `c04`
(宏观经济学（甲）, 8 textbook chapters plus 16 past-paper batches). Neither could
report whether its knowledge-point bodies were typeset in a readable way, and one
of them is not.

**The convention already exists and has no mechanism behind it.**
`pipeline/commands/extract-chapter.md:102` requires that definitions, conditions,
formulas, examples and common mistakes in `body`, `fragile` and
`learning_action` be separated by blank lines, and that multi-level content
"must not be compressed into one line". `:107` lists that as a workflow Blocker.
`pipeline/scripts/validate-pool.py` has no corresponding check — its only text
check is the type of `fragile` (`:232-239`).

**What that costs, measured read-only.** A paragraph is a run of text between
blank lines; its length is counted in *visible characters* (inline math and
backticked code removed for counting, nothing else). Paragraph totals were
cross-checked against an independent run (514 / 3830 / 141, all matching):

| | ncmc | c04 | dmath |
|---|---|---|---|
| knowledge points | 100 | 324 | 31 |
| paragraphs | 514 | 3830 | 141 |
| visible characters p50 | 374 | 64 | 35 |
| visible characters p90 | 737 | 194 | 80 |
| visible characters max | 2258 | 473 | 267 |
| bodies over 300 | **100%** | 8.3% | 0% |
| bodies under 40 | 0% | **72.8%** | **83.9%** |
| either | 100% | 76.5% | 83.9% |

`ncmc-ch03-kp-006`「换元积分法与分部积分法」is 7439 characters across **7 lines**:
its four section labels are already separated by blank lines, but each section
below the label is a single unbroken line of 1212–3584 characters — the second
level of the same violation `:102` forbids.

**The unit decides whether any number means anything.** Counting total
characters overstates an `ncmc` paragraph by 1.76× (659 vs 374 median) because
44% of that text is LaTeX source, while overstating a `c04` paragraph by 1.09×;
counting 汉字 instead is meaningless for `dmath`, which is an English course
(15 汉字 in a 51-character paragraph). This repository has already paid for that
mistake once — a course-local validator measured `len()` against a "汉字"
specification and passed 100/100 rows whose real CJK median was 353
(`ingest-integrity-and-observability` P1-27).

## What Changes

- **A read-only typesetting check, not a gate.** `docs/GLOSSARY.md:513-516`
  defines 门禁/Gate as a check that rejects the whole batch on failure. This
  check never rejects, so it is not a gate and does not take that name.
- **Measurement rule.** Paragraphs are runs between blank lines, measured in
  visible characters; a band of **40 to 300** applies to `body` only. Zero-visible
  paragraphs (pure math or pure code) do not count as too short. `fragile` and
  `learning_action` are excluded: `learning_action`'s visible median is already
  40–42, and a `fragile` note reaches 576 in `c04`.
- **Advisory by construction.** The check reports, never refuses; writes nothing;
  alters no text; and states no preferred typesetting — no target length, no
  recommended section vocabulary, no suggested split point. Not triggering it
  means nothing is wrong; 41 characters is as acceptable as 300.
- **One report shape at two points.** Before apply, over the content bundle
  (`workbench/ingest`, the sanctioned layer — no frozen-layer exception needed);
  after apply, over the pool (`pipeline/scripts/validate-pool.py`, under the
  narrow exception granted for this one read-only check). The over-long section
  is printed before the short one, because the lower bound fires on 73–84% of
  otherwise well-typeset courses and would otherwise bury the rarer, more
  consequential long paragraphs.
- **A scope with nothing to check says so**, rather than reporting nothing —
  matching how `validate-pool.py:273` already reports a missing
  `coverage-check.md`.
- **The bounds live in this spec**, not only in an implementation constant, so a
  later change can move them deliberately.
- **No seam boundary in this change.** Whether one line holds several structural
  units is a separate question and is deferred.
- **One glossary entry set and one ADR**: 排版检出 and 可见字符 in
  `docs/GLOSSARY.md`, and an ADR recording the three doctrines (no length ceiling,
  no scripted text rewriting, report-don't-prescribe).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-content-governance`: adds one requirement — the knowledge-point
  body paragraph typesetting check.

The requirement is a statement about the quality of content that enters the
pool, which is what this capability owns. The post-apply check is *hosted* in the
legacy `pipeline/scripts/validate-pool.py` because that is where a per-chapter
pool report already runs; hosting is not ownership. This distinction matters
because `openspec/changes/archive/2026-09-20-optional-problem-difficulty-gate/specs/workbench-content-governance/spec.md:13-14`
places the legacy pipeline's own defaulting behaviour outside spec scope — this
requirement is not about that behaviour, and the check it specifies changes no
default and refuses nothing.

## Impact

- **Code**: none in this PR. `tasks.md` is the queue for a follow-up change.
  That change touches `workbench/ingest` (bundle-side, sanctioned layer) and
  `pipeline/scripts/validate-pool.py` (pool-side, one read-only check under the
  granted exception).
- **Docs**: `docs/GLOSSARY.md` gains 排版检出 and 可见字符; `docs/adr/0023` records
  the three doctrines.
- **Data**: none. No pool is written, and every measurement in `design.md` was
  taken in SQLite read-only mode.
- **Tests**: none in this PR; the follow-up needs a regression test for a
  zero-visible paragraph and one proving the check writes nothing.
- **Compatibility**: none. No stored text changes and no command's exit code
  changes, because the check never raises above an advisory finding.
- **Known cost, accepted**: the lower bound fires on 72.8% of `c04` and 83.9% of
  `dmath` knowledge points, both of which are otherwise well-typeset. The check
  is a reminder, not a verdict, and most such findings will be read and
  dismissed. The report's two-section order exists so this does not hide the
  rarer over-long paragraphs.
- **Dependency**: repairing existing rows through the documented path
  ("fix the manifest, then re-apply") requires `--upsert`, whose
  `INSERT OR REPLACE` writes only 11 columns and resets the rest to NULL
  (`pipeline/scripts/insert-knowledge-points.py:254-259`). That is P0-2 of
  `ingest-integrity-and-observability`, itself parked as `DOCTRINE`. **Rewriting
  the existing `ncmc` bodies that way would blank `figure_paths` and
  `ingest_batch_id` on the rows it touches.** That repair is course work outside
  this repository and must wait for, or route around, that defect.
