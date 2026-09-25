# Tasks

## 1. Confirm contracts

- [x] 1.1 Read the proposal, design, and spec deltas; reproduce the reported failure (the live service was still running the pre-change prompt, and three statements in the current tree still pointed at a one-chapter-per-turn rule).
- [x] 1.2 Keep the change additive: no pool schema change, no new user-facing noun, no automatic turn, and existing rows keep their value.

## 2. Contract parity (one turn really carries several chapters)

- [x] 2.1 Failing tests: an inline block naming itself `type: content-bundle` applies; a staged file carrying only the lists applies; an unknown kind keeps its explicit refusal.
- [x] 2.2 Accept the wrapper spellings an Agent actually writes (`kind`, `type`, a nested `manifest`, bare lists inline or staged).
- [x] 2.3 Tell the truth about chapters: delete the dead workspace-chapter argument, refuse an item that resolves no chapter with a reason that says the workspace chapter is not used, and update the prompt, docstring and tests.
- [x] 2.4 Rewrite the contract as v2: the exact inline shape, per-chapter batches vs whole-manifest precheck, every block applied, the three practice modes, keyless objective items, and the `problem_type` clarification.
- [x] 2.5 Next-turn notice: continue the chapters the learner asked for instead of waiting for another 「继续」.
- [x] 2.6 Fix the duplicate result card (a single-action turn recorded both `action` and `actions` and rendered twice).

## 3. Choosing the 题型 at ingestion

- [x] 3.1 Failing tests: a keyless 判断题/单选题 applies with its mode and a `keyless` count, a keyed item still needs `error_reason`, a keyless choice item still needs options, a plain item declaring a micro mode is refused with the exact fix, `["exam"]` is a no-op.
- [x] 3.2 `micro_quiz`: `has_answer_key` plus the key-shape rule split out of the payload rule (`validate_answer_key`), so a key filled in later is checked for shape only.
- [x] 3.3 Gate: accept an absent/`null` key, keep `error_reason` mandatory only when a key is present, count keyless items per batch and in the registry.
- [x] 3.4 Refuse a plain problem that declares a micro/yes/no `practice_modes` without a `quiz_type`, naming the fields it needs.
- [x] 3.5 `answer_key` becomes an editable problem field (`data update problem`), patched into the item's own payload, validated against its quiz type, empty clears it.
- [x] 3.6 Practice page: no verdict from a missing key, an honest 「本题未录入答案键」 line, reveal and session-end cards show the same, and a `keyless` count in the result card.

## 4. Documents

- [x] 4.1 FILE_CONTRACT (bundle shape, chapter rule, per-chapter batches, keyless items).
- [x] 4.2 GLOSSARY (题型 = practice mode vs `problem_type`; the keyless objective item).
- [x] 4.3 PRODUCT-MANUAL (one turn finishes the requested chapters; the three modes; keyless items and how to fill keys later).
- [x] 4.4 REQUIREMENTS, ARCHITECTURE, ACTION-GRAPH L1/L3/L4.

## 5. Verification

- [x] 5.1 Repository checks on the working tree (see Evidence).
- [x] 5.2 Isolated acceptance on `%TEMP%/lk-parity` (a **copy** of the physics pool, scratch registry, port 3091): one real Pi turn importing two chapters with keyless objective items.
- [x] 5.3 Mode pulls, the fill-a-key path, and the next-turn notice on that copy.
- [x] 5.4 The real pools, the real registry, and the user's own server untouched.

## What changed

- `bridge/conversations.py`: `_implied_manifest_kind` + `_looks_like_content_block`
  (wrapper spellings), contract v2 in `_prompt`, the continuation sentence and the
  `未录答案键` label in `_content_outcome`/`_COUNT_LABELS`.
- `bridge/conversations.py` (UI): the restore path renders `actions` first and falls
  back to `action`, so one turn shows one card.
- `server/static/workbench.js`: `quizHasKey`, ungraded `gradeMicroQuiz`, the keyless
  line, honest reveal/session-end text, `keyless` in the asset summary.
- `ingest/__init__.py`: chapter rule (no workspace fallback, dead argument removed),
  keyless acceptance + `keyless` counts, the practice-mode refusal.
- `domain/micro_quiz.py`: `has_answer_key`, `validate_answer_key`; `data/content.py`:
  the `answer_key` update path.
- Docs: FILE_CONTRACT, GLOSSARY, PRODUCT-MANUAL, REQUIREMENTS, ARCHITECTURE,
  ACTION-GRAPH L1/L3/L4.

## Evidence (2026-09-25)

Repository checks on the working tree: pytest **654** (639 before this change; +15
new), Node **118** (+2), `compileall` exit 0, `openspec validate --specs --strict`
**11 passed**, `openspec validate ingest-mode-choice-and-contract-parity --strict`
valid, `doctor` all checks passed, `guard extract-problems` PASS, `guard problem-set`
PASS.

New coverage: `test_content_bundle.py` (+5) — a keyless 判断/单选题 bundle lands with
its mode marking, a null key and `counts["keyless"]`, a keyed item still needs its
error reason, a keyless choice item still needs options, a plain problem declaring
`micro` is refused naming `quiz_type`, and `["exam"]` is a no-op.
`test_micro_quiz.py` (+2) — an absent/empty key validates for all three types and
`has_answer_key` says so, while a supplied key keeps its shape and reason rules.
`test_data_cli.py` (+3) — filling a key on a keyless item (with no error reason),
clearing it, a key that does not fit the item's quiz type, and a key on a non-micro
problem. `test_conversations.py` (+4) — the prompt states the chapter rule, the three
modes, the keyless rule and its version; an inline `type` bundle and a staged
lists-only file both apply; a wrong shape keeps its explicit refusal; and a real
keyless import reaches the next turn's notice as 「未录答案键 1」 plus the continuation
sentence. `workbench_ui_interactions.test.js` (+2) — a keyless item is never graded
and says so (before and after revealing), and a restored single-action turn renders
exactly one result card.

Isolated acceptance (`%TEMP%/lk-parity`: scratch registry, a **copy** of the user's
physics `c01.db`, server on **3091**, never the user's 3081; provider = the real Pi):

- One Pi turn (48.3s) imported **both** chapters from a single cross-chapter
  manifest: `batch-012` (ch18: 1 KP + 5 problems, 4 keyless) and `batch-013` (ch19:
  1 KP + 2 problems, 2 keyless), `counts = {knowledge_points 2, problems 7, keyless 6}`
  — no second learner message, no per-chapter round trip.
- The rows carry the right modes: three `["yes_no"]` 判断题, one `["micro"]` 单选题
  (`single_choice`, options 米/牛/焦/瓦) and one plain 综合题, all with
  `answer_key: null` and no `error_reason`.
- Mode pulls at the same lens: 判断 3 items, 小测 1 item, 综合题 1 item.
- The next-turn notice read back from the mirror: 「…批次 batch-012（ch18）、
  batch-013（ch19）…未录答案键 6…不要让学生再说一次「继续」」.
- Filling a key on a real imported row (`data update problem c01-ch18-mq-001
  --input '{"answer_key": "是"}'`) stored the key without demanding an error reason;
  the problem API then served it as gradable.
- **Two real-agent findings were fixed during this acceptance**: the Agent staged the
  manifest body with no wrapper key (lists only) and it wrote the natural inline
  `{"type": "content-bundle", …}` — both are now accepted, with tests.
- The real pools (`c01.db` mtime 21:36, `pool/dmath.db` Sep 20), the real
  `bridges.json` (Sep 17) and the user's running server were not touched; the scratch
  server was stopped and no orphan Pi process remained.

## Remaining limits

- The 806 problems already in the two real pools stay exam-only. Converting a stored
  `-prob-NNN` row into a micro item in place is impossible (its readable id would
  change), so the learner re-imports those chapters; this change is what makes that
  re-import land as 判断/小测 in one turn.
- A keyless item is practised without a verdict. That is the honest consequence of a
  lost answer key; the alternative (guessing one) would fabricate learning signal.
- The gate still refuses an item whose chapter cannot be resolved from the item or
  the manifest. That is deliberate (`必须强制规定哪一些知识点是哪一章`) and it is now
  stated in the prompt instead of contradicting it.
- `error_reason` is optional for keyless items, so a keyless item that later gets a
  key without a reason stays as it is: the reason is required at ingestion, not
  retroactively.
- The contract version line helps a resumed provider session notice a change, but a
  session that already believes otherwise may still need one fresh conversation; the
  prompt says the current contract wins.
