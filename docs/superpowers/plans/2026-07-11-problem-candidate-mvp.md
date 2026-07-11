# Problem Candidate MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a source-grounded candidate-problem workflow that can be gated, practiced, converted into durable problems, and used to update learner signals without trusting generated questions as official assets by default.

**Architecture:** Candidate data lives in separate tables inside the existing course SQLite pool. Agent-authored manifests and audit reports cross the agent/script boundary; dependency-free Python scripts own structural validation, persistence, practice records, signal updates, and import into the unchanged `problems` table. Focus Map reads current learner signals from SQLite by default and retains signal-map JSON only as a compatibility input.

**Tech Stack:** Python 3 standard library, SQLite, JSON manifests, `unittest`.

## Global Constraints

- Keep the MVP dependency-free and course-scoped.
- Do not add an `answer` field; answers and explanations belong in `solution`.
- Generated candidates are never official `Problem` rows until both structure and semantic audit gates pass.
- Learners may practice `gate_passed` candidates without approving or reviewing them first.
- MVP purposes are `first_pass_check` and `remediation`; exam simulation is out of scope.
- Candidate interactions are `single_choice`, `true_false`, or `free_response`.
- Candidate origin is `source_problem`, `adapted_problem`, or `generated_grounded`; free-form ungrounded generation is out of scope.
- Formal `problems` schema remains unchanged. Import renders structured candidate content into `problem_text` and `solution`.
- Wrong and stuck attempts raise current learner signals. Mastery never clears a signal automatically.

---

### Task 1: Document the candidate boundary

**Files:**
- Modify: `CONTEXT.md`
- Modify: `FILE_CONTRACT.md`
- Create: `docs/adr/0008-problem-candidates-and-learner-signals.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: the approved design decisions in this plan.
- Produces: canonical definitions for `Problem Candidate`, `Candidate Practice Session`, `Problem Origin`, `Interaction Type`, and `Learner Signal`.

- [ ] Add glossary entries that distinguish candidate lifecycle from durable problem progress.
- [ ] Define candidate manifest and audit report locations under `intermediate/{course}/problem_generation/{chapter}/`.
- [ ] Record the single-course-DB decision, double-PASS import rule, signal current-state policy, and legacy JSON compatibility in ADR 0008.
- [ ] Update README architecture, pool list, and command examples.
- [ ] Run `rg -n "Problem Candidate|Learner Signal|candidate_problems" CONTEXT.md FILE_CONTRACT.md README.md docs/adr/0008-problem-candidates-and-learner-signals.md` and confirm every term is documented.
- [ ] Commit with `docs: define problem candidate workflow`.

### Task 2: Add candidate and learner-signal schema

**Files:**
- Modify: `pool/scripts/pool_schema.py`
- Modify: `pool/scripts/migrate-progress.py`
- Modify: `pipeline/scripts/create-tables.py`
- Create: `tests/test_problem_candidates.py`

**Interfaces:**
- Produces: `ensure_problem_candidate_schema(conn) -> list[str]`.
- Produces tables: `candidate_problems`, `candidate_attempts`, and `learner_signals`.

- [ ] Write a failing migration test that calls `ensure_problem_candidate_schema` twice and asserts the three tables, enum constraints, indexes, and idempotence.
- [ ] Run `python -m unittest tests.test_problem_candidates.ProblemCandidateSchemaTests -v` and confirm failure because the helper does not exist.
- [ ] Implement constants and `ensure_problem_candidate_schema` in `pool_schema.py`.
- [ ] Update fresh database creation and the existing migration entry point to apply the schema.
- [ ] Run the focused schema tests and the full suite.
- [ ] Commit with `feat: add problem candidate schema`.

### Task 3: Insert candidates and enforce the double gate

**Files:**
- Create: `pipeline/scripts/insert-candidates.py`
- Create: `pipeline/scripts/gate-candidates.py`
- Create: `pipeline/templates/candidate-insert-manifest.md`
- Create: `pipeline/templates/candidate-audit-report.md`
- Modify: `tests/test_problem_candidates.py`

**Interfaces:**
- Produces: `insert_candidates(db_path, manifest_path, upsert=False) -> tuple[int, int, list[str]]`.
- Produces: `gate_candidates(db_path, audit_path, candidate_ids=None) -> tuple[int, int, list[str]]`.
- Candidate options are JSON objects with `id`, `text`, `explanation`, and optional `error_lure`.
- An `error_lure` contains `signal_type`, `target_type`, `target_id`, and optional `note`.

- [ ] Write failing tests for a valid manifest, invalid IDs/enums/KP links, choice-option structure, source evidence, and readable text blocks.
- [ ] Run the insertion tests and confirm failure because the module is absent.
- [ ] Implement manifest loading, validation, and draft insertion.
- [ ] Run insertion tests until green.
- [ ] Write failing tests showing that structure PASS plus audit PASS yields `gate_passed`, while either failure yields `needs_revision`.
- [ ] Implement structural gate checks and semantic audit report ingestion.
- [ ] Verify focused and full tests.
- [ ] Commit with `feat: add candidate insertion and gates`.

### Task 4: Record candidate practice and learner signals

**Files:**
- Create: `pool/scripts/learner_signals.py`
- Create: `pool/scripts/practice-candidates.py`
- Modify: `tests/test_problem_candidates.py`

**Interfaces:**
- Produces: `upsert_learner_signal(conn, target_type, target_id, signal_type, note, practice_kind, practice_ref) -> str`.
- Produces: `record_candidate_attempt(db_path, candidate_id, status, selected_option_id=None, note="") -> dict`.
- First wrong/stuck evidence creates medium weight; the second raises it to high; later mastery does not lower it.

- [ ] Write failing tests for gate eligibility, choice correctness, append-only attempts, default `weak_node` signals, structured lure signals, and weight escalation.
- [ ] Run focused tests and confirm missing-module failures.
- [ ] Implement current-state signal upsert logic.
- [ ] Implement candidate-attempt recording and a thin interactive CLI that uses the same function.
- [ ] Run focused and full tests.
- [ ] Commit with `feat: record candidate practice signals`.

### Task 5: Import eligible candidates into durable problems

**Files:**
- Create: `pipeline/scripts/import-candidates.py`
- Modify: `tests/test_problem_candidates.py`

**Interfaces:**
- Produces: `import_candidates(db_path, candidate_ids=None) -> tuple[list[str], list[str], list[str]]`.
- Renders stem plus options into official `problem_text` and answer plus explanations into `solution`.
- Migrates one summary attempt and current status from the candidate attempt history.

- [ ] Write failing tests for double-PASS eligibility, deterministic problem IDs, rendered options/solutions, imported lifecycle state, summary progress migration, and idempotence.
- [ ] Write failing duplicate tests: block same-KP normalized or near-identical stems and warn for strongly homogeneous stems below the block threshold.
- [ ] Run focused tests and confirm failure because import behavior is absent.
- [ ] Implement rendering, ID allocation, duplicate checks, transaction handling, and summary migration.
- [ ] Run focused and full tests.
- [ ] Commit with `feat: import gated candidates as problems`.

### Task 6: Connect formal practice and Focus Map to DB signals

**Files:**
- Modify: `pool/scripts/record-problem.py`
- Modify: `pool/scripts/query-focus-map.py`
- Modify: `pool/scripts/serve-graph.py`
- Modify: `tests/test_problem_progress.py`
- Modify: `tests/test_course_network.py`

**Interfaces:**
- Produces: `fetch_learner_signals(conn, course, chapter) -> list[dict]`.
- `build_focus_map(..., signals=None)` loads DB signals when `signals` is omitted; explicit signals remain an override/compatibility path.

- [ ] Write a failing test that formal wrong/stuck practice updates `weak_node` signals for every linked KP.
- [ ] Implement formal-practice signal updates through `learner_signals.py`.
- [ ] Write failing tests that Focus Map and the local server read SQLite signals without a JSON file.
- [ ] Implement DB signal loading and preserve optional `--signals` compatibility.
- [ ] Run focused and full tests.
- [ ] Commit with `feat: feed practice signals into focus map`.

### Task 7: Validate the complete workflow

**Files:**
- Modify: `pipeline/scripts/validate-pool.py`
- Modify: `README.md`
- Modify: `FILE_CONTRACT.md`

**Interfaces:**
- Pool validation checks candidate foreign references, lifecycle/gate consistency, imported IDs, and learner-signal targets without requiring candidate rows to exist.

- [ ] Write failing validator tests for a gate-passed candidate missing double PASS and an imported candidate missing its official problem.
- [ ] Implement candidate and signal validation gates.
- [ ] Create a temporary course DB and run create, insert, gate, practice-record, import, validate, and Focus Map commands end to end.
- [ ] Run `python -m unittest discover -s tests -v` and require zero failures.
- [ ] Run `python -m compileall lessonkit.py pipeline/scripts pool/scripts tests` and require exit 0.
- [ ] Run `git diff --check` and inspect `git status --short`.
- [ ] Request an independent code review, fix critical and important findings, then repeat all verification commands.
- [ ] Commit with `feat: complete problem candidate MVP` if any final integration changes remain.
