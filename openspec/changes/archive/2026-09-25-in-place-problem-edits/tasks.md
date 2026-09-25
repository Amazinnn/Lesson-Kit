# Tasks

## 1. Confirm contracts

- [x] 1.1 Read the proposal, design, and spec deltas; reproduce the reported workload with read-only measurements on both real pools.
- [x] 1.2 Confirm by reading the code that the id suffix carries no read-time meaning, that no consistency check fires on a conversion, and that learning rows key on `problem_id` alone.

## 2. Stem bound

- [x] 2.1 Failing tests: an 801-character stem is refused, an 800-character stem is accepted.
- [x] 2.2 `MAX_STEM_CHARS` 200 → 800 with a comment that the bound is a ceiling now, not a design statement; prompt, spec, and docs updated.

## 3. One authority for in-place patches

- [x] 3.1 Failing tests: convert an existing row (options lifted out of the stem), derive the mode from the payload, clear the payload back to 综合题, refuse two knowledge points / a bad option / a bad mode / a mode without payload / an unknown field / a difficulty field, keep the rating on a mode edit and clear it on a stem edit.
- [x] 3.2 `content.plan_problem_patch(row, data, course)` — pure planning (unknown fields, identity, mode resolution, payload contract, stem bound, difficulty clearing) plus `decode_problem` and the `_answer_key_errors` shorthand.
- [x] 3.3 `data update problem` writes through the plan; `PROBLEM_PATCH_FIELDS` gains `practice_modes`, `micro_quiz`, `source_evidence`, `source_answer`, `solution_origin`; `_db_value` passes NULL through instead of writing `"null"`.
- [x] 3.4 Honesty fixes: an unknown field name is an error (never a silent drop), `data delete` on an unknown id exits 2, a missing `--input` says so.

## 4. Bulk channel

- [x] 4.1 Failing tests: one batch converts several rows without changing ids, a bad item leaves the pool untouched, the gate names every reason, a foreign-course id is refused, an item with nothing to change is refused, rollback restores every column of the previous values, a patch survives learning records, a patch batch cannot be rolled back twice, and the recipe writes only with `--apply`.
- [x] 4.2 `_gate_problem_patch` / `_apply_problem_patch` / `_rollback_problem_patch`: existing rows only, one backup, one transaction, one batch id with a `previous` snapshot, `rowcount == 1` per row, and counts `problems` + `difficulty_cleared` (rows whose rating actually existed).
- [x] 4.3 `rollback_batch` gained the restore branch, skipping the learning-record blocker because it deletes nothing; the row keeps its original `ingest_batch_id`.
- [x] 4.4 Wired into `apply_batch` (bridge path) and `recipe` / the CLI `ingest recipe` choices.

## 5. The Agent's path

- [x] 5.1 Failing test: a `problem-patch` action from a reply converts the row, reports `kind`, and appears in the next-turn notice.
- [x] 5.2 `problem-patch` joins the bridge's manifest kinds and the contract-error text.
- [x] 5.3 Contract v2 gained the patch paragraph: what a patch preserves, that a batch rolls back, that options may be lifted out of the old stem, the 800-character bound, and the writable field list; `_COUNT_LABELS` gained `difficulty_cleared`.

## 6. Documents

- [x] 6.1 FILE_CONTRACT (the patch kind, the writable fields, the identity rule).
- [x] 6.2 GLOSSARY (原地改题, 拆选项, the micro-quiz entry's bound and keyless note).
- [x] 6.3 PRODUCT-MANUAL (in-place editing, what it preserves, the bound).
- [x] 6.4 REQUIREMENTS, ARCHITECTURE, ACTION-GRAPH L1/L3/L4.

## 7. Verification

- [x] 7.1 Repository checks on the working tree (see Evidence).
- [x] 7.2 Isolated acceptance on a **copy** of the real ADS pool: `--apply` gate, in-place conversion of real 单选题 with the options lifted out, mode pulls, byte-exact rollback.
- [x] 7.3 A real Pi turn doing the same by explicit instruction, then rolled back and compared against the batch snapshot.
- [x] 7.4 The real pools only ever read; the scratch server stopped; the two live Pi processes (both from the learner's own server) left alone.

## What changed

- `workbench/domain/micro_quiz.py`: `MAX_STEM_CHARS` = 800.
- `workbench/data/content.py`: `plan_problem_patch` / `plan_problem_update` / `decode_problem` as the single validation authority, `_update_problem`, `PROBLEM_PATCH_FIELDS`, `CONTENT_AXES`, `DIFFICULTY_COLUMNS`, unknown-field refusal, NULL-safe `_db_value`, delete/`--input` honesty.
- `workbench/ingest/__init__.py`: `PROBLEM_PATCH_KIND`, `_gate_problem_patch`, `_problem_previous`, `_apply_problem_patch`, `_rollback_problem_patch`, the rollback branch, `apply_problem_patch`, `apply_batch` dispatch, recipe wiring.
- `workbench/cli/main.py`: the recipe choice, `_json_input` guard.
- `workbench/bridge/conversations.py`: the action kind, the contract paragraph, the count label.
- Docs: FILE_CONTRACT, GLOSSARY, PRODUCT-MANUAL, REQUIREMENTS, ARCHITECTURE, ACTION-GRAPH.

## Evidence (2026-09-25)

Repository checks on the working tree: pytest **674** (654 before this change; +20 new), Node
**119** (+1), `compileall` exit 0, `openspec validate --specs --strict` **13 passed**,
`openspec validate in-place-problem-edits --strict` valid, `doctor` all checks passed, both
workspace guards PASS.

New coverage: `test_problem_patch.py` (+13) — the apply/convert path, option splitting out of a
long stem, the cleared-rating count, all-or-nothing bulk behaviour, every gate reason (typo,
difficulty, mode-without-payload, two kps, bad key), a foreign-course id, an item with nothing to
change, byte-exact value-for-value rollback (including a rating), a patch over existing learning
records, double rollback, and the `--apply` gate. `test_data_cli.py` (+6) — in-place conversion of
an existing problem, mode derivation and clearing, the enforced micro contract, unknown-field and
difficulty refusals, rating kept on a mode edit and cleared on a stem edit, delete/`--input`
honesty. `test_micro_quiz.py` (+1 assertion pair) — the 800/801 boundary. `test_conversations.py`
(+1) — a `problem-patch` action from a reply. `workbench_ui_interactions.test.js` (+1) — a
converted `-prob-` row renders and grades exactly like an imported `-mq-` item.

Isolated acceptance (`%TEMP%/lk-patch`: a **copy** of the learner's ADS pool taken at 23:35,
scratch registry, port 3091):

- `recipe problem-patch` without `--apply` reported `applied: false` and wrote nothing; with
  `--apply` it converted two real 单选题 in place — `c02-ch05-prob-017` and `c02-ch07-prob-011` —
  `counts = {problems: 2, difficulty_cleared: 0}`, `batch-018`.
- The options were lifted **verbatim** out of the stored text (`['not smaller', 'not larger',
  'smaller', 'larger']` and the `*O*(n log n)` family), the stems kept their question sentences,
  the ids did not change, and `pull --mode micro` returned them while `pull --mode exam` did not.
- `ingest rollback --batch batch-018` reported `{problems: 2}` and **0 columns differed** from the
  values captured before the patch.
- **A real Pi turn** (235.8s, explicit request to convert three named problems) submitted a valid
  `problem-patch`: `counts = {problems: 3, difficulty_cleared: 0}`, `batch-019`; the stored rows
  show `practice_modes ["micro"]`, the option lists lifted from the real Pintia-style text
  (including LaTeX such as `$T\left(n\right)…$`), the original `source_evidence` kept, and no
  fabricated answer key. `pull --mode micro` returned them, `pull --mode exam` did not.
- Rolling that batch back reported `{problems: 3}`; comparing every touched column against the
  batch snapshot's `previous` values gives **0 mismatches**.
- The real pools were only read: their own recent changes (c01 204 problems / 11 live batches,
  c02 896 problems / 31 live batches, both still growing during this work) come from the learner's
  own imports, not from this acceptance. No backup or batch file of mine exists in either real
  workspace; my writes all landed in the `%TEMP%` copy. The scratch server was stopped and the two
  live Pi RPC processes (created 23:12/23:13, i.e. before my server started) belong to the
  learner's own workbench and were left untouched.

## Remaining limits

- The tool does not author content: the Agent or the learner supplies the stem and the options.
  For the ADS pool that is the bulk of the work — only a minority of the remaining rows can be
  converted by mechanically lifting an option block; the rest need a human or the Agent to decide
  the options, and some (multi-problem rows, >800-character stems) cannot become micro items
  without splitting or shortening the text first.
- A patch cannot change a `problem_id`. Converting a row the other way (micro → formal) clears the
  payload and the marking; it does not rewrite the content.
- Difficulty stays a separate command, and a patch that touches a content axis (kp_ids,
  problem_text, solution, problem_type) clears the rating group — reported in the counts, and
  restored by a rollback.
- The bulk channel writes through the same SQLite transaction as everything else; a patch batch is
  recorded like other batches, so the registry keeps growing with fine-grained history rather than
  one row per editing session.
