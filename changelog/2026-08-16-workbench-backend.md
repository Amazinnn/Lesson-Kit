# 2026-08-16 Workbench Backend v1 (review-workbench-v1)

## What landed

The review workbench backend, per OpenSpec change `review-workbench-v1`
(proposal → specs → design → tasks), implemented TDD-first in task groups:

1. **Schema (additive)**: `review_schedule` (PK item_type+item_id+direction),
   `feedback_events`, `knowledge_points.figure_paths`, `problems.figure_paths`,
   `problem_attempts.answer_text` via `ensure_workbench_schema`;
   `migrate-progress.py` now also applies `ensure_course_network_schema`
   (real-pool gap: `knowledge_relations` was missing).
2. **Data layer** `workbench/data/`: `Pool` (only SQLite touchpoint, path
   resolution for figures/explain/jobs) + `queries` (hub stats, due list,
   problem/kp detail, figures list).
3. **Domain layer** `workbench/domain/` (pure rules, unit-tested):
   - `weak`: signal weight × due boost × session repeat penalty + cascade
     boosts (prerequisite/applies_to/part_of, reverse, depth ≤ 2, ×0.5/hop,
     strength-weighted, explainable reasons).
   - `pull`: durable problems → `gate_passed` candidates → shortage report,
     never invents content; modes weak/random/all.
   - `feedback`: 1–5 mapping + keyword→signal_type rules, signals stay
     evidence-only, events logged, schedule updated.
   - `schedule`: SM-2 variant `after_result(state, result, now)`; skip never
     regresses.
4. **Registry + config**: user-level `~/.lessonkit-workbench/workspaces.json`
   and `bridges.json` (JSON for stdlib purity), `LESSONKIT_WB_HOME` override.
5. **Bridge**: jobs lifecycle (`job-001` sequential ids, task.json/task.md/
   status.json/stdout.log), providers (env contract
   `LESSONKIT_JOB_DIR`/`LESSONKIT_OUTPUT_PATH`), contract validation
   (explain 结论/逐步拆解/易错点/回源指向; diagnose 定位/提示/溯源/追问),
   teacher instruction rendering with conduct rules, `runner` orchestration
   (no provider → graceful failed).
6. **CLI `wb`**: init/ls/open/serve/weak/due/pull/practice/feedback/schedule/
   ai/bridge/guard — data-only, zero teaching semantics.
7. **Server**: single-port HTTP, JSON API (hub, weak, due, pull, practice,
   feedback, problem/kp detail, figures with path containment, ai jobs),
   minimal server-rendered pages.

## Verification

- `python -m pytest tests -q` → **141 passed** (50 baseline + 91 workbench).
- `openspec validate review-workbench-v1 --strict` → valid.
- Guards (extract-problems, problem-set) → PASS; `validate-pool` → PASS.
- Real-pool smoke (`wb` on `pool/dmath.db`): ls (28 kp / 303 problems),
  weak (all 0.2 with no signals), practice wrong → schedule relearning due
  today, feedback rating 2 → signals on linked KPs → weak top (2.0), due
  shows the problem, `wb ai explain` without provider fails gracefully with
  a clear message.

## Known limitations / next steps

- `wb serve` is wired but not exercised end-to-end in this session; the API
  layer is fully tested via ephemeral-port tests. Frontend pages are minimal
  (hub + workspace home); the interactive practice/review UI is the next
  frontend task.
- No real provider configured yet: `wb bridge add claude --command claude ...`
  then `wb ai ... explain <problem-id>` will run the first real teacher task.
- Deferred by design: `generate` bridge operation, Scoropic mode, teacher
  memory consumer, figures management tools (ADR 0021, tasks.md).
