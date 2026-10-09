# Tasks

## 1. Content identity (pure rules)

- [x] 1.1 Tests for normalization: case, whitespace, punctuation, `$…$` rendering variants, and export-noise lines all collapse; the whole stem is compared (no truncation); two stems differing beyond those variants stay distinct.
- [x] 1.2 Implement the normalization and identity functions in `workbench/domain/` (stdlib only, no I/O) as the single shared entry point for the gate and the audit.

## 2. Ingest gate

- [x] 2.1 Gate tests cover existing items, intra-manifest duplicates, rendering variants, similar-but-different stems, and all-or-nothing refusal.
- [x] 2.2 Wire the identity check into the content-bundle gate (and the micro-quiz bundle path) with itemized reasons, preserving the all-or-nothing contract and writing no batch record on refusal.
- [x] 2.3 Add the new refusal reason to `FILE_CONTRACT.md`.

## 3. Patch validation parity (conformance fix)

- [x] 3.1 Tests cover label bounds and disallowed markup for both direct edits and `problem-patch`, while untouched legacy fields remain accepted.
- [x] 3.2 Route `plan_problem_patch` through the shared label-bound and markup helpers so the patch path refuses exactly what the gate refuses.

## 4. Read-only content audit

- [x] 4.1 Fixture tests cover each audit check: `duplicates`, `fragments`, `unmarked-objective`, `untitled`, `figures`, and `orphan-figures`.
- [x] 4.2 Tests cover zero writes, clean/finding exit codes, check selection, and machine-readable output.
- [x] 4.3 Implement the audit queries and the fragment heuristic in `workbench/data/`.
- [x] 4.4 Add `data <ws> audit [--check <name>]… [--json]` to the CLI with the exit-code contract, and register it in the declared-surface ownership table.
- [x] 4.5 Document the command in `docs/PRODUCT-MANUAL.md`, the terms (content identity, content audit) in `docs/GLOSSARY.md`, and move dedup out of the deferred list in `docs/FUTURE-DEVELOPMENT-NOTES.md`.

## 5. Verification

- [x] 5.1 Registered ADS pool compared read-only with its896-row before-image on2026-10-09:19→1 duplicate groups,100→1 fragments,896→0 untitled; full current audit108 findings. The real-pool runner proves zero source writes, report/exit behavior, guarded refusal and rollback on copies. Residual data findings remain explicit; no clean-pool claim or source repair.
- [x] 5.2 Full unittest discovery (including the declared-surface audit): 723 tests ran; 722 passed and one existing process-image test failed because this container returns an empty image name. `pytest` is not installed in this runtime.

## 6. No stem length bound (implemented with the ADS repair)

- [x] 6.1 Remove the stem length check from `micro_quiz.validate_problem_row` and the `MAX_STEM_CHARS` constant, keeping the option-count and single-knowledge-point rules.
- [x] 6.2 Remove the same check from `plan_problem_patch` so the patch path cannot refuse a long objective item.
- [x] 6.3 Update the bridge contract prompt text (length is no longer a reason to leave an objective item in 综合题).
- [x] 6.4 Update the bound tests: a 5000-character stem is legal, and the gate test no longer counts a long stem as a violation.
- [x] 6.5 Update the docs that state the bound (`REQUIREMENTS.md`, `GLOSSARY.md`, `PRODUCT-MANUAL.md`, both action-graph files).
- [x] 6.6 Run the full suite (674 tests pass).
