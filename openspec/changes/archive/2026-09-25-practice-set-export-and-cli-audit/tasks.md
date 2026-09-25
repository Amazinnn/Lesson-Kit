# Tasks

## 1. Confirm contracts

- [x] 1.1 Read this proposal, design, and all spec deltas; inspect the current worktree and preserve other Agents' changes.
- [x] 1.2 Keep the shipped changes additive: `exam_year` covers the pool, the CLI command name stays `pull`, and existing CLI output shapes stay reachable.

## 2. Declared surface (machine-checked)

- [x] 2.1 Add the ownership table for every API route and CLI command with audience and status.
- [x] 2.2 Add the audit test: real command set from the parser, real route set from the route table, declared↔real equality, and both-surface entries implemented on both sides.
- [x] 2.3 Correct the registration document counts and audience marks and point it at the machine authority.

## 3. Exam year (additive)

- [x] 3.1 Failing migration test: the column is added idempotently, legacy rows keep NULL, and row contents do not change.
- [x] 3.2 Add `exam_year` through the additive schema entry and the write paths (`data update problem`, content-bundle validation, ingest-gate contract) with the stated validation.
- [x] 3.3 Expose the prefix filter on `pull`, with the ready-to-paste migration command when the pool predates the column.

## 4. Composition through `pull`

- [x] 4.1 Failing tests for scope, explicit ids, conditional filters, weak/due/wrong drivers, per-problem reasons, and shortage honesty.
- [x] 4.2 Extend the pull engine with explicit ids, exam year, the learner drivers, and the reason annotation; keep the existing session `weak` ordering unchanged and document the difference.
- [x] 4.3 Add the progress read the wrong-problem driver needs.
- [x] 4.4 Make the CLI print full problem rows by default, keep `--ids`, and add the missing include filter.

## 5. Practice set export

- [x] 5.1 Failing tests for the render rules: continuous numbering, no answer or internal id in the student file, `待补` for a missing solution, both files aligned.
- [x] 5.2 Add the pure renderer and the manifest read/validate path.
- [x] 5.3 Add `--plan`, `--print`, `--name`, and the zero-write `check` action, with itemized nonzero errors.

## 6. Audited CLI gaps

- [x] 6.1 `practice`: existence check plus one transaction; failing test proves a failure leaves nothing behind.
- [x] 6.2 `feedback`: card item type and direction.
- [x] 6.3 `goals`: invalidate the cached plan through the same helper the API uses.
- [x] 6.4 `weak`, `due`, `ls`: machine-readable output while the human default stays.
- [x] 6.5 Remove the dead surfaces (`ingest render` target, always-rejected gate/apply entity values) and declare the rest.

## 7. Documents

- [x] 7.1 GLOSSARY: exam year, practice manifest and practice set (existing nouns only, no new user-facing concept).
- [x] 7.2 PRODUCT-MANUAL, ARCHITECTURE, ACTION-GRAPH (entry + L0–L4), REQUIREMENTS.
- [x] 7.3 TASK_ROUTER: route "compose a practice set / print a paper" to the CLI.

## 8. Verification and handoff

- [x] 8.1 Isolated end-to-end on a scratch registry and a copied pool: a cross-chapter set, a wrong-problem set, and a set with one explicitly added problem; inspect both rendered files.
- [x] 8.2 Full Python and Node checks, `compileall`, OpenSpec strict plus this change, `doctor`, and the workspace guards.
- [x] 8.3 Read-only check that the real learning pool is untouched; record outcomes and remaining limits in the handoff.

## What changed

- `workbench/surface.py` (new): every API route and CLI command with its audience
  (Agent / human / both / browser-only), the reason a browser-only capability stays
  there, and the command that serves each Agent-reachable route.
  `tests/workbench/test_cli_surface.py` derives the real sets from `build_parser()`
  and `app.ROUTES` and fails on any difference in either direction.
- `workbench/domain/pull.py`: `select` gained `explicit_ids` (always included, never
  filtered or capped away), `exam_year` (prefix match), `drivers` (weak via
  `domain.weak.weak_kp_ids`, due, wrong), `coverage` (coverage-first ordering before
  the `n` cap, replacing the session order for composed sets), and `with_reasons`.
  The session ordering (`mode=weak` = knowledge-point hit count) is unchanged and now
  documented as distinct from the weakness driver. A membership bug (filtering against
  the driver dict instead of the union of its sets) was found by the new tests.
- `workbench/domain/weak.py`: `weak_kp_ids(ranked)` — the explicit filter for "carries
  weakness evidence", which ranking alone never did.
- `workbench/domain/practice_set.py` (new): pure rendering — continuous numbering, a
  student sheet without answers or internal identifiers, `待补` for a missing solution,
  an aligned solution sheet, and a `leaks` scan.
- `workbench/data/practice_sets.py` (new): manifest build/read/write, validation
  (unknown, duplicate, unsupported field), replay, the zero-write preview report
  (count, missing solutions, leaks, figure base) and the two rendered sheets.
- `workbench/data/pool.py`: `problem_progress_rows()`, `latest_attempt_statuses()`.
- `workbench/data/content.py`: `exam_year_error` / `normalize_exam_year` /
  `exam_year_column_error`, `exam_year` in the problem's editable fields, validation on
  create and update.
- `workbench/data/goals.py`: `plan_path` / `invalidate_plan` owned here so the API and
  the CLI drop the cached plan through one helper.
- `workbench/data/attempts.py`: `record_result` — the single-transaction practice write
  both the HTTP handler and the CLI now use.
- `pool/scripts/pool_schema.py`: additive `problems.exam_year` (nullable, no default,
  no backfill).
- `workbench/ingest/__init__.py`: `exam_year` accepted and validated in the
  content-bundle and micro-quiz paths, written only when the pool has the column, with
  the migration command when it does not; shared validator from `data.content`.
- `workbench/cli/main.py`: `pull` composes (six ways in), prints rows by default with
  `--ids` for the old shape, and gained `--include`, `--exam-year`, `--problem`,
  `--weak/--due/--wrong`, `--plan`, `--input`, `--check`, `--print/--base/--title`;
  `practice` validates and writes atomically; `feedback` accepts cards and directions;
  `goals` drops the stale plan; `weak/due/ls` gained `--json`; `ingest render`'s ignored
  positional and the always-rejected `gate/apply` entity values are gone; an unknown
  workspace name is a readable refusal instead of a traceback.
- `workbench/bridge/conversations.py`: the teacher contract names the composition
  command and its flags, and states that `exam_year` is optional and must not be invented.
- Docs: GLOSSARY (exam year, practice manifest, practice set, selection, declared
  surface), PRODUCT-MANUAL (how to fix, print and re-run a practice set), ARCHITECTURE
  (modules and the new column), ACTION-GRAPH (entry log, L0–L4, the W6 workflow), L2
  (counts corrected to 32 routes / 22 commands, machine authority named), REQUIREMENTS,
  TASK_ROUTER.

## Evidence (2026-09-25)

Repository checks on the working tree: pytest **621** (583 before this change; +38 new
tests), Node **115**, `compileall` exit 0, `openspec validate --specs --strict`
**11 passed**, `openspec validate practice-set-export-and-cli-audit --strict` valid,
`doctor` all checks passed, `guard extract-problems` PASS, `guard problem-set` PASS.

New coverage: `test_cli_surface.py` (5) — declared ↔ real commands, declared ↔ real
routes, Agent-reachable routes name a real command, browser-only entries carry a reason,
both-surface entries exist on both sides; `test_practice_sets.py` (22) — scope and
conditional filters, whole rows vs `--ids`, explicit ids surviving filters and the cap,
exam-year prefix matching, each driver, drivers as a union inside the scope, include,
honest shortage, unmigrated-pool message, manifest record/replay, invalid manifests
(unknown, duplicate, empty, unsupported field), `--input` vs selection flags, render
rules (no answer/internal id, aligned numbering, `待补`, cross-chapter naming, figure
reference kept + base reported), zero-write `check`, tampered manifest;
`test_cli_parity.py` (10) — unknown problem refused with zero writes, a mid-write
failure leaving no partial record (patched writer raising), skip recording nothing, card
feedback with direction, unknown item and bad direction refused, rating-or-note required,
CLI goal write dropping the cached plan, listing not dropping it, `--json` for
weak/due/ls with unchanged text defaults, and the removed arguments now failing to parse.
`test_schema_migration.py` gained the exam-year migration test (idempotent, legacy rows
untouched). Three existing CLI tests were updated where the printed shape changed by
design (rows instead of ids, with the reason).

Isolated acceptance (`%TEMP%/lk-set`; scratch registry; a **copy** of the real
`c01.db`; port 3091; the real pool never opened for writing):

- The copy migrated cleanly (`problems.exam_year` added, 76 problems intact). Evidence
  was then created *on the copy* through shipped commands: three problems marked wrong
  with `practice`, one agent-recorded rated attempt with `attempts apply`, three
  problems tagged with an exam year through `data update problem` (a bad value was
  refused with the reason).
- **Cross-chapter set**: with the chapter lens off, `pull --source-kind textbook --n 8
  --plan --print` produced a manifest and two sheets; the first attempt exposed a real
  flaw — the session ordering handed back eight problems from one chapter — and after
  moving coverage-first ordering ahead of the cap, the set spans chapters by id order
  (ch12 5 / ch13 3 for n=8). The student sheet numbers 1–8, contains no internal id or
  answer, keeps the figure reference relative, and the solution sheet mirrors all eight
  numbers with `待补` for the five problems without a stored solution.
- **Wrong-problem set**: `pull --wrong --n 20` selected exactly the four problems whose
  progress or latest attempt is wrong, across all three chapters, each with reason
  `wrong`.
- **Explicit addition**: `pull --kp <kp with no matching problem> --source-kind final
  --n 1 --problem c01-ch14-prob-011` returned only that problem with reason `explicit`;
  writing it to a manifest, `--input … --check` reported `valid: true, writes: 0`, and
  re-printing from the manifest produced the same one-problem sheet.
- **Exam year**: `pull --exam-year 2024` matched the `2024-2025春夏` value by prefix.
- **Browser smoke test** on the migrated copy: the practice page pulled and rendered a
  real problem card (习题12-1 with its source line and typeset math), and the answer box
  behaved; `/pull` still returns rows without the composition-only `reason` key.
- The real pool was then re-read read-only: 76 problems, 0 attempts, 0 feedback events,
  8 batches, still **no** `exam_year` column, mtime unchanged (2026-09-23 23:24) — the
  copy took every write.

## Remaining limits

- A whole-course set covers **knowledge points** first, so its chapter mix follows which
  problems cover the most uncovered points (the accepted 8-problem set was 5/3 ch12/ch13
  and skipped ch14). Even chapter balance is not a rule; compose per chapter with `--kp`
  lists when that matters.
- `--exam-year` needs the additive column: the real pool does not have it yet, so the
  first use prints the exact `migrate-progress.py` command. Nothing else needs the
  migration.
- The printed sheets keep figure references relative; the bytes stay in
  `.lessonkit/figures/` and only their base directory is reported (no copying, no
  embedding).
- Flash-card pulls and every conversation route stay browser-only — now declared with a
  reason in `workbench/surface.py` instead of being implied by silence.
- Storing a practice set and practising *from* one are still out of scope (design
  non-goals): a manifest is an input, not a record.
- Concurrency remains process-level; two simultaneous prints into one directory can
  interleave writes.
