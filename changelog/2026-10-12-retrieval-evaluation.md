# Retrieval evaluation repair — 2026-10-12

The developer-only retrieval evaluator now counts historical problem evidence only when the row has nonblank problem text and a concrete outcome. Blank or unrecognized statuses, timestamps alone, and blank answer/note text do not qualify; recognized attempt statuses, numeric 1–5 ratings, and false/true verdicts do. Malformed status values such as lists or objects are ignored safely.

Historical problem matching now compares the complete text case-insensitively, so `P1` cannot match `P10`. The evaluator refuses a missing or non-file workspace database before connecting, preventing a read from creating a database file. With those PR117 corrections, the existing generic history read measured 2/3 scenarios, recall 0.75, and 4 primitive reads; this is the dated pre-evidence baseline.

The PR118 evidence query replaces the history scenario's generic read. The current fixture now passes 3/3 scenarios with recall 1.0 and 4 primitive reads. The earlier 3/3 result from the uncorrected evaluator was a false green and is not treated as a valid baseline.

The current OpenSpec and architecture describe this as a developer diagnostic over existing Data readers. It makes no learner-state writes, provider calls, or product-ordering changes.

Focused verification passed:

- `python -m pytest tests/workbench/test_retrieval_eval.py -q -p no:cacheprovider` — 8 passed.
- `python -m compileall -q workbench/experiments/retrieval.py tests/workbench/test_retrieval_eval.py` — passed.
- `openspec validate --specs --strict` — 15 specs passed.
- `git diff --check` — passed.

Full-suite, installed-runtime, and release/archive acceptance remain with the independent acceptance runner and should be checked against the final commit.
