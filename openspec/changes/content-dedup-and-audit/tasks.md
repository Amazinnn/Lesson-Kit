# Tasks

## 1. Content identity (pure rules)

- [ ] 1.1 Failing tests for normalization: case, whitespace, punctuation, `$…$` rendering variants, and export-noise lines all collapse; the whole stem is compared (no truncation); two stems differing beyond those variants stay distinct.
- [ ] 1.2 Implement the normalization and identity functions in `workbench/domain/` (stdlib only, no I/O) as the single shared entry point for the gate and the audit.

## 2. Ingest gate

- [ ] 2.1 Failing gate tests: an item equal to an existing problem is refused with the colliding id and its source evidence; two items of one manifest that share an identity are both refused; rendering variants collide; similar-but-different items both pass; a manifest mixing a duplicate with valid items writes nothing.
- [ ] 2.2 Wire the identity check into the content-bundle gate (and the micro-quiz bundle path) with itemized reasons, preserving the all-or-nothing contract and writing no batch record on refusal.
- [ ] 2.3 Add the new refusal reason to `FILE_CONTRACT.md`.

## 3. Patch validation parity (conformance fix)

- [ ] 3.1 Failing tests: an over-long `display_title`, an over-long `topic_label`, and an HTML tag outside `<sup>`/`<sub>` are refused by `data update problem` and by a `problem-patch` manifest; a valid patch still applies; untouched legacy fields are still not re-validated.
- [ ] 3.2 Route `plan_problem_patch` through the shared label-bound and markup helpers so the patch path refuses exactly what the gate refuses.

## 4. Read-only content audit

- [ ] 4.1 Failing tests over a fixture pool, one per check: `duplicates`, `fragments` (continuation token, prefix/suffix partner, option-label-only row), `unmarked-objective`, `untitled`, `figures` (unresolved reference), `orphan-figures`.
- [ ] 4.2 Tests for the audit's guarantees: zero writes (row counts, contents, and batch list unchanged), exit 0 on a clean pool, non-zero on findings, `--check` selection, machine-readable output.
- [ ] 4.3 Implement the audit queries and the fragment heuristic in `workbench/data/`.
- [ ] 4.4 Add `data <ws> audit [--check <name>]… [--json]` to the CLI with the exit-code contract, and register it in the declared-surface ownership table.
- [ ] 4.5 Document the command in `docs/PRODUCT-MANUAL.md`, the terms (content identity, content audit) in `docs/GLOSSARY.md`, and move dedup out of the deferred list in `docs/FUTURE-DEVELOPMENT-NOTES.md`.

## 5. Verification

- [ ] 5.1 Run the audit over the ADS workspace pool before and after `ads-pool-content-repair` and record both finding sets as that change's conformance evidence.
- [ ] 5.2 Run the full test suite plus the declared-surface audit test (the new command appears in the ownership table and on the CLI side only).

## 6. No stem length bound (implemented with the ADS repair)

- [x] 6.1 Remove the stem length check from `micro_quiz.validate_problem_row` and the `MAX_STEM_CHARS` constant, keeping the option-count and single-knowledge-point rules.
- [x] 6.2 Remove the same check from `plan_problem_patch` so the patch path cannot refuse a long objective item.
- [x] 6.3 Update the bridge contract prompt text (length is no longer a reason to leave an objective item in 综合题).
- [x] 6.4 Update the bound tests: a 5000-character stem is legal, and the gate test no longer counts a long stem as a violation.
- [x] 6.5 Update the docs that state the bound (`REQUIREMENTS.md`, `GLOSSARY.md`, `PRODUCT-MANUAL.md`, both action-graph files).
- [x] 6.6 Run the full suite (674 tests pass).
