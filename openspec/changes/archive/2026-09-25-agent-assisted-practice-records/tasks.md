# Tasks

## 1. Confirm contracts

- [x] 1.1 Read this proposal, design, and all spec deltas; inspect the current worktree and preserve other Agents' changes.
- [x] 1.2 Update GLOSSARY, PRODUCT-MANUAL, ARCHITECTURE, ACTION-GRAPH, and CLI usage when implementation changes behavior.

## 2. Attempt data and CLI

- [x] 2.1 Write failing tests for attempt list/get, manifest validation, zero-write check, 1–N atomic apply, ungraded attempts, and same-request retries.
- [x] 2.2 Add an idempotent, additive attempt-operation record and associate new Agent feedback with its attempt without changing legacy rows.
- [x] 2.3 Reuse the existing 1–5 feedback rules inside one transaction with attempt insertion; leave all projections untouched for ungraded attempts.
- [x] 2.4 Expose `lesson-kit attempts <workspace> list|get|check|apply` with JSON input/output and nonzero itemized errors.
- [x] 2.5 Add tests for correction, replacement rating, removal of a rating, stale-projection conflict, and no partial writes; then implement `correct` using guarded pre/post-effect snapshots.
- [x] 2.6 Add CLI configuration of user-chosen answer-image source directories; do not copy/index images or store per-image attempt paths.

## 3. Focused page context

- [x] 3.1 Add a failing interaction/context test for the active problem, unsent text/choice/note draft, and currently visible images on a practice-page Agent turn.
- [x] 3.2 Pass bounded draft content as ephemeral context while rebuilding authoritative problem facts from SQLite; keep other pages' context unchanged.
- [x] 3.3 Prove discussing a draft without an attempt CLI call creates no learning write or durable answer-image attachment.

## 4. Verification and handoff

- [x] 4.1 Test several pages for one answer, one page with multiple problems, partial ungraded work, retry after lost response, and valid/invalid corrections in isolated workspaces.
- [x] 4.2 Run affected and full Python/Node checks, compileall, OpenSpec strict, doctor, and relevant guards; perform isolated real-Agent acceptance.
- [x] 4.3 Record exact outcomes, remaining limits, and the CLI usage in the handoff; archive only after implementation and required acceptance pass.

## What changed

- `pool/scripts/pool_schema.py`: additive `attempt_operations` table (request id,
  attempt id, kind, rating, two content fingerprints, the returned result, and the
  pre/post-effect projection snapshots) plus `feedback_events.attempt_id` and its
  index. No backfill, no rewrite of legacy rows.
- `workbench/data/attempts.py` (new, Data layer): manifest validation with a strict
  field allowlist and per-item errors, zero-write `check`, one-transaction `apply`
  for 1–N attempts, `correct` with the snapshot guard, `list`/`get`, and the
  snapshot/restore helpers. Rated items call the existing
  `domain.feedback.apply(..., attempt_id=…)` inside the same transaction (never the
  categorical `practice` mapping); ungraded items only write the attempt row.
- `workbench/domain/feedback.py` + `workbench/data/pool.py`: optional `attempt_id`
  threaded to `feedback_events`, `pool.attempt`, `pool.feedback_event_for_attempt`,
  and `insert_attempt` now returns its row id.
- `workbench/cli/main.py`: `lesson-kit attempts <workspace> list|get|check|apply|correct`
  (`--input <file|->`, JSON output, itemized JSON errors, nonzero exit) and
  `attempts sources add|list|remove --path`; `registry.py` gained the per-workspace
  `answer-sources.json` (directory paths only).
- `workbench/server/context.py`: the practice page's draft (answer, note, choices,
  visible image references) is passed as bounded ephemeral turn input under the
  existing `include_draft` switch; other pages are unchanged.
- `workbench/server/static/workbench.js`: the practice page sends that draft, its
  selected options, and the images its current question card shows.
- `workbench/bridge/conversations.py`: the teacher contract now names
  `lesson-kit attempts check|apply|correct` and `sources list`, states that only
  those write, and forbids putting image paths or image content into a manifest.
- Current docs: GLOSSARY (5 new terms + attempt redefinition), PRODUCT-MANUAL
  (6.8 and the Agent chapter), ARCHITECTURE (module, tables, contracts),
  ACTION-GRAPH (entry log, L0–L4), REQUIREMENTS, TASK_ROUTER.

## Evidence (2026-09-24)

Repository checks on the working tree: pytest **583** (was 549; +34 new),
Node **115** (was 114), `compileall` exit 0, `openspec validate --specs --strict`
**11 passed**, `openspec validate agent-assisted-practice-records --strict` valid,
`doctor` all checks passed, `guard extract-problems` PASS.
`guard extract-chapter` FAILs on a missing pipeline artifact
(`intermediate/dmath/extraction/ch06/04_checks/pool-validation-report.md`) that is
absent from this checkout and unrelated to this change.

New coverage in `tests/workbench/test_attempts.py` (30 tests): manifest validation
(unsupported field, unknown problem, bad/boolean rating, duplicate problem, empty
text, non-object), zero-write `check` previews, 1–N atomic apply, ungraded items
leaving every projection untouched, identical-retry replay, request-id reuse with
different content, one bad item protecting the batch, unmigrated-pool guidance,
correction (replacement rating, rating removal, adding a rating, retry),
correction conflicts (later attempt, later graph-state edit, later rated attempt)
all with zero writes, legacy/unknown attempts not correctable, list/get, source
directories, multi-page + one-page-two-problems scenarios, and workspace isolation.
`tests/workbench/test_schema_migration.py` covers the additive migration and that
legacy attempt rows are untouched; `test_agent_context.py` covers the bounded draft
(truncation) and that a draft turn writes no learning row;
`workbench_ui_interactions.test.js` asserts the practice turn's payload and that no
`/practice` or `/feedback` call leaves the page.

Isolated real-Agent acceptance (`%TEMP%/lk-attempts`, scratch registry via
`LESSONKIT_WB_HOME`, scratch pool, port 3091, real `pi` with
`deepseek/deepseek-v4-flash`; no real pool touched):

- **Record / discuss / correct** (one conversation): the agent found the CLI via
  `--help`, staged the manifest, ran `check` then `apply`, and reported attempt id 1
  with due 2026-09-26; the DB showed one attempt (status `reviewing`, the answer
  text verbatim, the agent's note), one `feedback_events` row with `attempt_id=1`
  and rating 3, one signal (evidence 1), `problem_progress=reviewing`, states
  `review`, schedule repetitions 1 / ease 2.6 / interval 1. A follow-up turn that
  only asked about the answer left all seven tables byte-identical. A third turn
  asking to change the rating to 2 ended with the same attempt id, the same answer
  text, a replaced note, **one** event (rating 2, `attempt_id=1`), the signal
  recomputed to evidence 1, and the schedule restarted from the default ease
  (repetitions 0 / ease 2.3 / due today) — the old rating's effect was withdrawn,
  not stacked.
- **Practice page walkthrough** (real browser, scratch server): started a normal
  session, typed an unsent answer, and sent a chat message; the POST body carried
  `include_draft`, `draft_answer`, `draft_note`, `draft_choices`, and
  `draft_images: ["/api/w/scratch/figures/dmath/ch12/problem-figure.png"]` — the
  image actually shown on the card. Pi's own session store shows the server-rebuilt
  context for that turn: authoritative `submitted_attempts`, `schedule`, and
  `state` from SQLite next to the bounded `draft`. The discuss-only turn changed no
  learning table.
- **Photographed answer**: told the agent the photos live in its configured source
  directory and that it could use the machine's offline OCR, it ran
  `attempts scratch sources list`, wrote its own easyocr script, transcribed the
  OCR text **verbatim** (keeping its misreads), added a Chinese note, ran `check`
  (`valid=true`, `writes=0`) and `apply`, and reported attempt id 2 with due
  2026-09-26. The DB shows attempt 2 with the raw OCR text, one event linked to it
  (`attempt_id=2`), and the schedule advanced from the corrected row while the
  earlier attempt kept its own record.

## Remaining limits

- The `photos` path needs an Agent that can actually read images or an offline OCR.
  The configured Pi model (`deepseek/deepseek-v4-flash`) declares text-only input,
  so it reported "Current model does not support images" and fell back to OCR;
  Claude and Codex could not reach their APIs from this machine, so the vision path
  itself is unverified end to end.
- `correct` intentionally refuses any attempt that is not the problem's latest or
  whose projections moved afterwards; it also refuses attempts recorded by the
  browser or by the older `practice`/`feedback` commands (no operation link). Those
  stay readable, and the learner records a fresh attempt instead.
- Correction overwrites one JSON manifest object at a time by design; there is no
  batch correction and no correction history.
- Concurrency is process-level only: two simultaneous `apply` calls with the same
  request id can race, and the loser fails on the primary key instead of replaying.
- A pool created before this change needs
  `python pool/scripts/migrate-progress.py --db pool/<course>.db`; the CLI says so
  when the schema is missing.
