# PR117 repair handoff

Date: 2026-10-12

## Scope and result

Repaired only PR117 in `.worktrees/pr117-audit-20261012`. The evaluator now requires a nonblank problem text plus a recognized attempt status, nonblank answer/note, numeric 1–5 rating, or Boolean/SQLite 0–1 verdict. Timestamps and unknown statuses do not qualify. Historical problem matching now uses case-insensitive full-text equality, so `P1` cannot match `P10`. `_pool()` rejects missing and non-file database paths before any SQLite connection. Ordinary `Pool` behavior, stored fields, manifest fields, and the 2/3, 0.75, 4-read baseline remain unchanged.

The contract now identifies retrieval evaluation as a developer-only diagnostic over existing Data readers, with no provider calls, product ordering changes, learner-state writes, or new architecture layer. OpenSpec defines scenario and report behavior; architecture and evaluation documentation record module ownership, manifest fields, outcome validity, report metrics, and the unchanged baseline.

No schema or `DATA_MODEL.md` changes were needed. No other worktree, original checkout, installed runtime, provider configuration, or real database was touched. No push, merge, or archive action was performed.

## Commits

- `524bb48` — `docs: specify retrieval evaluation contract`
- `d9e077a` — `fix: tighten retrieval evaluation evidence`
- `154631b` — `docs: document retrieval evaluator boundary`
- This report is committed separately as the final handoff record.

## Verification evidence

- RED before implementation: `python -m pytest tests/workbench/test_retrieval_eval.py -q -p no:cacheprovider` reported the three expected failures for outcome validity, P1/P10 matching, and missing/non-file databases (`3 failed, 5 passed`).
- GREEN after implementation: the same focused command passed (`8 passed`).
- `python -m compileall -q workbench/experiments/retrieval.py tests/workbench/test_retrieval_eval.py` passed.
- `python -m compileall -q lessonkit.py workbench pipeline pool tests` passed.
- `openspec validate retrieval-evaluation --type spec --strict` passed.
- `openspec validate --specs --strict` passed: 15 specs, 0 failures.
- `git diff --check` passed.

The full test suite, installed-runtime acceptance, and release/archive checks remain pending for the independent acceptance owner. PR118 remains untouched and should be reconciled against this PR117 repair before its stacked evaluator checks.
