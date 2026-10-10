# Tasks

The original PR recorded the check. Follow-up
`implement-kp-text-typesetting-check` implements required sections 1–4; checked
items below mean implementation with focused evidence, not final acceptance.
Section 4.5 remains pending independent repository/isolated acceptance. Sections
5–6 are deliberately deferred/outside scope and remain unchecked; they are not
required implementation work and must be carried forward before archive.

## 1. The measurement rule

- [x] 1.1 One shared module holding the paragraph split and the visible-character count (strip `$$…$$`, `$…$`, backticked code), used by both hosts so the two cannot drift.
- [x] 1.2 The band 40–300 as named constants, with a comment pointing at the spec requirement rather than at the calibration numbers.
- [x] 1.3 Exclude paragraphs whose visible count is zero from the short-paragraph test.
- [x] 1.4 Apply the band to `body` only; `fragile` and `learning_action` are excluded, as specified by the approved requirement. The report reads id/body only; this reconciles the original task's extra 'read for report' phrase with that requirement.

## 2. The two hosts

- [x] 2.1 Bundle-side: read the content bundle in `workbench/ingest` and produce findings before apply. `workbench/` is the sanctioned layer for new code (`AGENTS.md`), so no frozen-layer exception is involved. Decide where in the existing bundle check it attaches, and confirm that a finding does not turn into a refusal.
- [x] 2.2 Pool-side: add one read-only check to `pipeline/scripts/validate-pool.py`, emitted at an advisory level so the exit code is unchanged (`:16-19`). This is the only place the granted frozen-layer exception is spent.
- [x] 2.3 A scope with no bundle reports that it had nothing to check, modelled on `validate-pool.py:273`'s handling of a missing `coverage-check.md`.
- [x] 2.4 `body` is selected by the dedicated read-only Data adapter; the frozen legacy gate's seven-column query stays intact.

## 3. The report

- [x] 3.1 Two sections, over-long first, short second; omit a section entirely when it is empty.
- [x] 3.2 One row per knowledge point, carrying the count past each bound plus the longest and shortest measured paragraph. A point violating both bounds appears once, in the over-long section, with both counts.
- [x] 3.3 A closing line with the scope's knowledge point count, paragraph count, visible-character percentiles, and each side's count and share.
- [x] 3.4 Wording discipline, checked before merge: no target length, no recommended section names, no suggested split point, no template. Every number recomputable from the stored text.
- [x] 3.5 Feed the pool-side findings into the existing `04_checks/pool-validation-report.md` and the existing `--json` output rather than writing a second report file. The existing textual report can be captured at that path as before; the validator creates no file.

## 4. Proof

- [x] 4.1 A test for a body whose only short paragraph is a display formula or a code block — it must not be reported as too short.
- [x] 4.2 A test that the check writes nothing: row counts, row contents and the batch list identical before and after.
- [x] 4.3 A test that a body violating both bounds appears exactly once, in the over-long section.
- [x] 4.4 A test that a scope with no bundle is distinguishable from a clean scope.
- [x] 4.5 Run the repository checks `AGENTS.md` requires before a PR:
      `python -m pytest tests -q`,
      `node --test tests/workbench/*.test.js`,
      `python -m compileall -q lessonkit.py workbench pipeline pool tests`,
      `openspec validate --specs --strict`.

## 5. Parked, deliberately

- [ ] 5.1 The seam boundary — whether one line holds several structural units. Its measurement was found to be unsound while preparing this change (see `design.md` §7) and the marker set's coverage is unproven, so it is a separate decision.
- [ ] 5.2 Whether `fragile` and `learning_action` need bands of their own. Their measured lengths do not fit the body band; giving them one is a new decision, not a follow-through.
- [ ] 5.3 Whether the bounds should be adjustable per course. v1 does not expose them, on the grounds that they mark departure rather than target a style.

## 6. Outside this change

- [ ] 6.1 Rewriting the existing `ncmc` bodies is course work in that workspace, not a repository change. It must not use `--upsert` on rows it does not intend to reset: `insert-knowledge-points.py:254-259` writes 11 columns and NULLs the rest, which would blank `figure_paths` and `ingest_batch_id` on the rows it touches. That is P0-2 of `ingest-integrity-and-observability`, itself parked as `DOCTRINE`.
- [ ] 6.2 Until that defect is settled, any body repair has to carry the full row in the manifest, or route through a path that does not rebuild the row.
