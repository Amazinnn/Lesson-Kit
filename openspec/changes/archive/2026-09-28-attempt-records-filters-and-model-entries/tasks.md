# Tasks

## 1. Records: what the browser actually did

- [x] 1.1 Failing tests: the migration rebuilds the status CHECK and adds `verdict`/`choices` idempotently, a migrated pool keeps every existing row, and an unmigrated pool degrades to a plain row instead of erroring.
- [x] 1.2 `pool/scripts/pool_schema.py`: `_widen_problem_attempts_status_check` rebuilds with the column intersection of the live shape and widens `status` with `answered`; `ensure_columns` then adds `verdict`/`choices`.
- [x] 1.3 `workbench/data/pool.py` + `workbench/data/attempts.py`: `insert_attempt(..., verdict, choices)` and `record_browser_attempt` probe columns so an unmigrated pool writes what it can.
- [x] 1.4 `POST /attempts` (`api.attempt_record`) validates the payload and returns `attempt_id`; `POST /feedback` accepts and ownership-checks `attempt_id`, and `domain/feedback._apply` refuses an attempt belonging to another item.
- [x] 1.5 `workbench.js`: a submission POSTs one attempt with the answer text, the chosen options, and the objective verdict; the deck remembers `attempt_id`, which rides the rating.
- [x] 1.6 Only the rating still writes signals, state, progress, and schedule — a submission that is never rated changes no projection.

## 2. Records: the two views

- [x] 2.1 Failing tests: `records_overview` returns the linked rating/note, filters by problem, and the page renders a verdict badge, stars, the answer excerpt, and an honest empty state.
- [x] 2.2 `queries.records_overview(pool, limit, problem_id)` decorates attempt rows with the linked feedback.
- [x] 2.3 `pages.records_page` (nav entry 做题记录, newest first, 100 rows, `?problem=` filter, verdict badges 对/错/未判定) + `GET /records`.
- [x] 2.4 The practice reveal renders the already-returned `detail.attempts` as a 「历史作答 N 条」 section; nothing is re-derived.

## 3. Source filters: one rule, three surfaces

- [x] 3.1 Failing tests: OR within a dimension and AND across dimensions, case-insensitive substring evidence, year prefixes, and the document-key rule folding both pools' evidence formats.
- [x] 3.2 `domain/pull.py` gains list-valued `source_kinds`/`exam_years`/`evidence_docs`; the single-value parameters stay compatible and union with the lists.
- [x] 3.3 `domain/facets.py` (new): `document_key` + `pool_facets` with per-value counts read from the pool.
- [x] 3.4 `GET /pull-facets`, `GET /search/problems?q=`, and `POST /pull` accepting `filters` plus the previously missing single-value `exam_year`.
- [x] 3.5 CLI: repeatable `--source-kind`, repeatable `--source-evidence`, the existing `--exam-year`.
- [x] 3.6 The practice page's 来源筛选 popup: one checkbox group per dimension with counts, a search box that picks problems into `include_ids`, an active-count badge, clear-all, and sessionStorage persistence per workspace.

## 4. Models: a name is not a harness

- [x] 4.1 Failing tests: entries win when present and fall back to one-per-harness when absent; a missing harness skips its entry; a raw model id resolves; a name with a space that names no entry is refused; the conversation's model overrides the provider dict for the turn; switching discards the cached RPC process; a running turn refuses the switch; a refused cross-model resume starts a fresh session and says so.
- [x] 4.2 `registry.load_models`/`add_model` and `bridges.json`'s optional `models` list; `bridge add-model <name> --provider <harness> --model <string>`; `bridge list` prints the entries.
- [x] 4.3 `conversation_providers.discover_entries`/`get_entry`; `/ai/providers` returns `{name, provider, model}`.
- [x] 4.4 `conversations.create(..., model)`, `_resolve_model`, `set_model` (409 while running, discards the cached Pi process), the per-turn override, and the fresh-session fallback with an honest notice in the stream.
- [x] 4.5 The chat header select lists only the conversation's harness entries with the current model marked; a raw model id no entry names shows as the current choice, and the switch notice survives the reload.

## 5. Rendering

- [x] 5.1 Failing tests: option math renders through `richText`; the verdict line escapes then renders its error reason.
- [x] 5.2 `optionHtmlFor` and `verdictLine` go through the same rich-text/math pipeline as the reveal.
- [x] 5.3 FILE_CONTRACT: exported practice sets keep `$…$` verbatim and need a math-capable viewer.

## 6. Documents

- [x] 6.1 GLOSSARY: 判定, 做题记录, 筛选维度, 文档键, 模型条目, 对话内切换模型; 题目尝试 and 工作台 updated (four pages, submission lands a row).
- [x] 6.2 PRODUCT-MANUAL: 2.4.1 the filter popup, 2.2.1 the CLI flags, 6.3/6.4 the submission-records correction, 7.1.1/7.1.2 records, 8 the model entries and the in-chat switch.
- [x] 6.3 REQUIREMENTS: 做题记录, 来源筛选, the model/switcher rules, four-page scope, `pull` filter flags.
- [x] 6.4 ACTION-GRAPH L2 (route/command counts, the new routes, `pull`/`bridge` rows), L3 (five new action rows + changelog), L4 (W7 + accident rows 24–29).

## 7. Verification

- [x] 7.1 Repository checks on the working tree (see Evidence).
- [x] 7.2 Isolated acceptance on a **copy** of the real ADS pool (scratch registry, port 3091): the migration, the filter semantics across the whole course, the records flow, the shim model switch, the browser walkthrough.
- [x] 7.3 The real pools were only read; the scratch server was stopped.

## What changed

- `pool/scripts/pool_schema.py`: the `problem_attempts` widen-with-intersection rebuild, `verdict`/`choices`.
- `workbench/data/{pool,attempts,queries}.py`: column-aware attempt inserts, `record_browser_attempt`, `records_overview`, `search_problems`.
- `workbench/domain/{pull,facets,feedback}.py`: list filter dimensions, the document key and facets, the attempt-ownership check.
- `workbench/server/{api,pages}.py` + `static/workbench.{js,css}`: `POST /attempts`, `GET /records`, `GET /pull-facets`, `GET /search/problems`, `filters`/`exam_year` on pull, the records page and its nav entry, the reveal history section, the filter popup, option/verdict rich text, the chat model switcher.
- `workbench/bridge/{conversation_providers,conversations}.py` + `registry.py` + `cli/main.py`: model entries, the per-conversation model, `set_model`, `bridge add-model`.
- `workbench/surface.py` + `docs/action-graph/L2-interfaces.md`: route/command ownership for everything new.
- Tests: `test_facets.py` (new), plus `test_attempts`, `test_pull`, `test_conversation_api`, `test_conversations`, `test_conversation_providers`, `test_ui_routes`, `workbench_ui_interactions.test.js`.

## Evidence (2026-09-28)

Repository checks on the working tree: pytest **704**, Node **126**, `compileall` exit 0,
`openspec validate --specs --strict` **13 passed**, `openspec validate
attempt-records-filters-and-model-entries --strict` valid, `doctor` all checks passed, both
workspace guards PASS.

New coverage: `test_facets.py` (+5) — the document key over both real evidence shapes and the
pool-derived facets. `test_attempts.py` (+6) — the browser submission, its column-aware
degradation, and the verdict/choices round trip. `test_pull.py` (+4) — OR within a dimension,
AND across dimensions, case-insensitive evidence substrings, year prefixes. `test_conversation_api.py`
(+3) — the attempt/rating record pair, an unknown problem refused, the filter dimensions and search
feed, the 409 while a turn runs. `test_conversations.py` (+4) — the stored model, the whitespace
refusal, the entry name resolving to its model, the turn launching with the conversation's model,
the cached RPC process discarded on switch, and the fresh-session fallback with its notice.
`test_conversation_providers.py` (+4) — entries beating the fallback, a missing harness skipping its
entry, the raw-id resolution. `test_ui_routes.py` (+4) — the records page, the model switcher
markup, the new nav entry. `workbench_ui_interactions.test.js` (+8) — option math, the
submission→rating link, the filter popup loading facets and rendering every dimension with counts,
the saved dimensions riding the next pull, the model switcher (entries, switch, raw id, hidden when
the harness has none).

Isolated acceptance (`%TEMP%/lk-records`: a **copy** of the learner's ADS pool, 497 problems,
scratch registry, port 3091, claude shimmed by a local script):

- **Migration**: `ensure_workbench_schema` on the copy reported
  `['problem_attempts_status_answered']`, the columns became
  `id/problem_id/status/note/answer_text/verdict/choices/created_at`, the row count was unchanged
  (0), `PRAGMA foreign_key_check` was empty, and a second run reported `[]`.
- **Filter semantics** (whole course, n=60, 39 items in scope): `doc=CC98 midterm` → 11,
  `doc=2020-21 final sim` → 1, both docs → 12 with both subsets contained and 0 overlap (OR);
  `kind=midterm` → 17, `midterm+final` → 39 (OR); `kind=midterm AND year=2025` → 3, a strict subset
  (AND); the fragment `starstone3` → 21 covering both final documents, and `cc98` matched
  case-insensitively. An unknown dimension is a 400 naming it.
- **Facets**: 38 documents, `final` 367 / `midterm` 130, six year buckets — all read from the pool.
- **Records flow** (API): a submission returned `{attempt_id: 1, status: answered,
  verdict_recorded: true}` and wrote **no** signal/progress/schedule; the rating carrying that
  `attempt_id` then logged the event and wrote the four-piece set; `GET /records` returned one row
  reading 「AVL 删除 14 后判断错误说法 · verdict 0 · ★★☆☆☆ · 集合运算搞混了」. Refusals held:
  unknown problem 400, non-boolean verdict 400, bad choices 400, a foreign `attempt_id` 400.
- **Records views**: the page rendered the nav entry, the verdict badge 对/错, the stars, the answer
  excerpt and the note; an unmatched `?problem=` rendered the honest empty state.
- **Browser walkthrough** (real page on the copy): the 来源筛选 popup opened with 来源类型
  (final 367 / midterm 130), 考查年份 (2015-2016春夏 125 …), 来源文档 (38 entries with counts) and
  the search box; starting a 小测 session rendered all four options through KaTeX (`.katex` spans in
  every option label); submitting the wrong option produced 「回答错误」 plus the why, and the
  submission landed in the pool with its chosen option text.
- **Model switch** (live, shim): `/ai/providers` returned the learner's own names 小模型 A / 小模型 B
  (not `claude · …`); turn 1 ran on A and the shim logged `{"model": "shim-model-a", "resume": null}`;
  switching to B, turn 2 ran on B **resuming** `shim-session-1`; a switch while a turn was running
  returned 409 and changed nothing; the mirror kept all four messages. The chat header showed the
  entry name with the current one marked, and the in-page dropdown switched back with
  「模型已切换，下一轮生效。」
- **CLI**: `pull --source-evidence CC98 --ids`, the repeatable `--source-kind`/`--exam-year`
  combination, and `bridge list` printing the two entries all behaved as specified.
- The real pools were only read: the ADS pool still reports 497 problems / 0 attempts with the old
  `problem_attempts` column shape. All writes landed in the `%TEMP%` copy. The scratch server on
  3091 was stopped.

## Remaining limits

- Records are append-only: there is no edit or delete, in the UI or the CLI. Correcting a
  misclicked answer means answering again and re-rating.
- The 综合题 verdict stays empty by design (the workbench does not grade formal problems); only
  判断/小测 carry 对/错, and only when the item has an answer key.
- An unmigrated pool silently degrades submissions to a row without verdict/choices — honest, but
  `doctor` only hints; there is no forced migration yet.
- The filter popup lives on the practice page only, and its selection lives in sessionStorage: a new
  tab starts clean. Flash-card pulls ignore the dimensions.
- The model switch takes effect on the **next** turn (a running turn is refused, not interrupted),
  and only within the same harness — changing the harness still means a new conversation.
- 38 of the ADS pool's items carry math in micro-quiz options (80 pool rows overall); the fixes
  cover the rendering surfaces found, but a pool-wide pass over *stems* was not part of this change.

