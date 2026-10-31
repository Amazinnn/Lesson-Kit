# Implementation status

Workspace: `C:/Users/yanwei/.codex/worktrees/agent-part-grading/lesson-kit`
Branch: `codex/agent-part-grading`
Base: `2d1242b9317dcd220ede37dfca9cb5d2d304242a`

## Contract reconciliation

- `practice-review/Mode-specific answer reveal and locking` is explicitly replaced by this change's delta: independent live submission granularity plus unchanged run-level reveal policy; confirmed early submissions lock even if their results remain hidden.
- Legacy `problem_attempts.verdict` remains objective-only and empty for subjective attempts. New derived grading stores answer/process conclusions separately; the old sentence “comprehensive text with no verdict” does not prevent a separate grading record.
- `attempts correct` still replaces an eligible original Attempt and recomputes effects under its own contract. This change's grade revisions never call that operation.
- Existing evaluation CRUD remains a separate feedback-row operation. A subjective grade does not synthesize a rating or learning effects.
- Governed content revisions use current `answering_content` and Paper continuation rules. This change must include structured parts in answering semantics, preserve historical records and reset only affected unfinished work. No older change's unchecked tasks are counted as complete here.
- Existing live display preferences are reused; new submission granularity is not the self-rating visibility preference or the run's reveal timing.
- Current formal-content gates still require a solution. Missing part-specific references may be Agent-derived with provenance; this does not bypass formal-content readiness.

## Verification

- Focused checks actually run in this worktree on 2026-10-31:
  - `python -m pytest tests/workbench/test_part_practice.py tests/workbench/test_part_grading_store.py tests/workbench/test_grading_bridge.py -q`: 33 passed.
  - `node --test tests/workbench/part_practice.test.js`: 3 passed.
  - `python -m pytest tests/workbench/test_part_practice.py -q`: 7 passed.
  - Earlier focused runs also covered `test_schema_migration.py`, `test_content_mirror.py`, `test_content_governance.py`, plus compileall, strict OpenSpec specs validation, and the dmath ch06 extract-problems guard; exact full-suite and browser evidence remain with the parent acceptance stage.
- What these focused checks cover: mixed-part fixtures, immutable per-part Attempts, hidden grading disclosure, bad-batch zero writes, learning-effect isolation, grading revision/withdrawal history, Bridge retry/recovery, and subjective status projection.
- Not claimed here: full `python -m pytest tests -q`, real-browser acceptance, installed runtime behavior, or live-model grading. No test writes went to a real user pool.

## Implemented storage and surface handoff

- New part submissions bind immutable Attempt IDs to `part_attempt_context` snapshots, content revision and execution; new unsplit subjective submissions use virtual `whole`, while historical nullable identities and standalone objective paths remain unchanged.
- `problems.parts` is governed authored JSON; `part_grading_revisions` is append-only including withdrawal tombstones; `part_grading_jobs` preserves asynchronous transport state. See DATA_MODEL for exact fields and FILE_CONTRACT for mutation JSON.
- Browser adapters are `practice/part-draft` and `practice/part-submit`; Agent adapters are GET/POST `grading`, `lesson-kit grading` and installed `agent_contracts grading`. No dependency or configuration system was added.
- Submission granularity reuses workspace browser settings; reveal timing remains fixed to the execution. Grading output and references are projected separately from original submissions. Background conversation isolation is being hardened during independent review.
- This is an implementation handoff, not release acceptance. Full suite, isolated API/browser integration, installed runtime and live-provider results must be recorded by the parent acceptance stage. No main-spec synchronization or archive is claimed here.

## Verification ledger

Planning strict validation passed before implementation. Implementation checks and actual outcomes will be recorded here after code is available; no GUI or live-provider pass is claimed yet. No user pool is used for test writes.
