# 2026-08-16 Migration to D:\Projects and Development Resume

Work location moved from the OneDrive-backed Desktop path
`C:\Users\yanwei\Desktop\Document_In_University\Projects\active\Academic Workflow`
to `D:\Projects\Academic Workflow`. The source tree was copied (not moved); the
Desktop copy remains untouched except for unregistering its `problem-candidate-mvp`
worktree (clean and pushed, re-created at the new location).

## Migration Verification

- Full tree copy verified: 8,361 files / 98,960,472 bytes identical on both
  sides (zero path differences).
- Git state verified at the destination: HEAD `c91f7ba`, 447 tracked files,
  clean working tree, remote `origin` intact.
- Worktree re-registered: `.worktrees/problem-candidate-mvp` on
  `feature/problem-candidate-mvp` @ `6cc1459`.
- Smoke tests at the new location, run from the repository root:
  - `lessonkit.py status` reads runtime state.
  - `guard extract-problems` and `guard problem-set` both PASS.
  - `validate-pool.py` PASS (0 errors, 0 warnings).
  - `pytest tests -q` → 28 passed.

## Merged: Problem Candidate Workflow (fast-forward)

`feature/problem-candidate-mvp` (9 commits, 28 files, +3,289 lines) was merged
into `main` via fast-forward (`c91f7ba..6cc1459`). This brings the
source-grounded practice candidate workflow:

- `pipeline/commands/generate-problem-candidates.md` and
  `pipeline/scripts/candidate_contract.py`, `insert-candidates.py`,
  `gate-candidates.py`, `import-candidates.py`
- `pool/scripts/practice-candidates.py`, `pool/scripts/learner_signals.py`,
  `pool/scripts/pool_schema.py`
- `tests/test_problem_candidates.py` (982 lines) and related test additions

## Pool Schema Upgrade (additive)

`pool/dmath.db` predates the candidate tables. Applied the documented additive
migration:

```bash
python pool/scripts/migrate-progress.py --db pool/dmath.db
```

Added `candidate_problems`, `candidate_attempts`, `learner_signals` (+indexes).
Existing data untouched: 28 knowledge points, 303 durable problems.

## Post-Merge Verification

- `pytest tests -q` → 50 passed (28 baseline + 22 candidate-workflow tests).
- `guard extract-problems` PASS, `guard problem-set` PASS.
- `validate-pool.py --db pool/dmath.db --course dmath --chapter ch06` → PASS.

## Runtime State

`.lessonkit/state.yaml` updated: `extract-problems` is complete and the
`problem-set` view for dmath ch06 is rendered and guard-passed. Suggested next
action: generate source-grounded problem candidates for dmath ch06
(`first_pass_check` or `remediation`) per
`pipeline/commands/generate-problem-candidates.md`, or start a new
course/chapter extraction.

## Operational Notes

- All `lessonkit.py` commands resolve paths relative to the current working
  directory; run them from the repository root (see README).
- `origin` is 10 commits behind `main` (1 pre-migration commit + 9 merged).
  Push when convenient.
