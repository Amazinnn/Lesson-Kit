## 1. Schema migrations (additive)

- [x] 1.1 Add `ensure_workbench_schema` to `pool/scripts/pool_schema.py`: `review_schedule` table (PK item_type+item_id+direction, SM-2 fields), `feedback_events` table, `knowledge_points.figure_paths`, `problems.figure_paths`, `problem_attempts.answer_text` — idempotent, additive
- [x] 1.2 Call `ensure_workbench_schema` from `pool/scripts/migrate-progress.py`
- [x] 1.3 Test: migration on a copy of `pool/dmath.db` is idempotent (run twice), existing counts unchanged, `validate-pool.py` still PASS

## 2. Data layer (`workbench/data/`)

- [x] 2.1 `pool.py`: `Pool` class — open/close, query helpers, brief write helpers, path resolution for `.lessonkit/figures` and `.lessonkit/explain`
- [x] 2.2 `queries.py`: hub stats, weak list (domain-computed ordering applied), due list, problem detail, kp detail, figures listing
- [x] 2.3 Tests for pool.py + queries.py against a temp DB seeded with minimal fixtures

## 3. Domain layer (`workbench/domain/`, pure rules)

- [x] 3.1 `weak.py`: weakness score (signal weight × due boost × in-session repeat penalty) + cascade boosts (prerequisite/applies_to/part_of, reverse, depth ≤ 2, ×0.5/hop, strength-weighted) with explainable reasons
- [x] 3.2 `pull.py`: pull engine — problems by kp_ids, weakness-ordered, session de-dup, fallback to `gate_passed` candidates, shortage reporting
- [x] 3.3 `feedback.py`: 1–5 rating mapping + keyword→signal_type table; writes signals (evidence-only) + feedback_events; never clears signals
- [x] 3.4 `schedule.py`: SM-2 variant `after_result(state, result, now)`, due computation, per-direction entries for memory-recall cards
- [x] 3.5 Unit tests per domain module (test_weak, test_pull, test_feedback, test_schedule)

## 4. Registry and config

- [x] 4.1 `registry.py`: `~/.lessonkit-workbench/workspaces.json` load/save/register/list/get; folder validation (pool/*.db or lessonkit.py)
- [x] 4.2 bridges config: load/save provider config (command/args/cwd_mode/timeout) — JSON, stdlib-only
- [x] 4.3 Tests for registry round-trip and validation

## 5. Bridge (`workbench/bridge/`)

- [x] 5.1 `jobs.py`: task lifecycle queued→running→done/failed; job dir layout `.lessonkit/jobs/<job-id>/` (task.json/task.md/status.json/stdout.log)
- [x] 5.2 `providers.py`: spawn external CLI (cwd=workspace, timeout, capture stdout, non-zero exit → failed with reason)
- [x] 5.3 `contracts.py`: `validate(kind, text)` — explain (four sections + source reference) and diagnose (定位/提示/溯源/追问), parseable Markdown
- [x] 5.4 `teacher.py`: render task instructions for explain and diagnose with conduct rules (baseline question, concise explanation, comprehension check, never guess, cite source; diagnose: locate-first, hints not full solutions)
- [x] 5.5 Tests: contracts validation (missing section → fail), jobs state transitions, teacher instruction contains conduct rules

## 6. CLI (`workbench/cli/main.py`)

- [x] 6.1 `wb` commands: init, ls, open, serve, weak, due, pull, practice, feedback, schedule, ai (explain/diagnose/status), bridge add, guard — all wiring to domain/data/bridge/registry, zero teaching semantics
- [x] 6.2 Smoke: `wb ls`, `wb weak`, `wb due`, `wb pull --kp ...`, `wb practice`, `wb feedback`, `wb schedule` against `pool/dmath.db` (repo root as workspace)

## 7. Server (`workbench/server/`)

- [x] 7.1 `app.py`: BaseHTTPRequestHandler routing, single port, path-containment for figure/static serving, JSON vs HTML dispatch
- [x] 7.2 `api.py`: endpoints per spec — hub/workspaces, weak, due, pull, practice, feedback, schedule, problem detail, kp detail, figures, ai jobs (create/status)
- [x] 7.3 `pages.py`: minimal server-rendered pages (hub + workspace home) reusing KaTeX assets from `frontend/editable-graph/dist`; AI panel showing explain/diagnose results
- [x] 7.4 API tests via ephemeral-port test client covering the WHEN/THEN scenarios (weak order, pull shortage, feedback mapping, schedule update, figure 404, job lifecycle)

## 8. Verification and handoff

- [x] 8.1 Full verification: `python -m pytest tests -q`, `openspec validate review-workbench-v1 --strict`, both guards on dmath
- [x] 8.2 End-to-end smoke on dmath: weak → pull → practice → feedback → due → explain task fails gracefully without provider
- [x] 8.3 Commit per task group (`feat:`); update changelog with implementation summary
