# Agent learning evidence query — 2026-10-12

The installed `lesson-kit evidence <workspace> kp <kp-id> [--limit N]` command reads a bounded, newest-first set of attempts with readable problem text and the learner outcomes actually stored. It defaults to 8 rows, accepts limits from 1 through 20, and reports `has_more`. The text comes from current authored content, not a snapshot of the question at attempt time. The query does not infer learner traits.

Both `data.evidence.for_kp` and the installed CLI reject a missing or non-file workspace database before connecting to SQLite. The read leaves an absent path absent and does not change an existing database; ordinary Pool and writer behavior are unchanged.

Retrieval measurement history is retained in `2026-10-12-retrieval-evaluation.md`: the original PR118 fixture measured 3/3 with valid `P1` evidence, though the evaluator could false-green timestamp-only or substring cases. After PR117 corrected the outcome and full-text rules, the generic history read measured 2/3 (recall 0.75, 4 reads). With the evidence query and corrected evaluator, the current fixture measures 3/3 (recall 1.0, 4 reads).

Focused retrieval/evidence tests, targeted compile, and strict OpenSpec validation passed. Full-suite, isolated-environment, installed-runtime, and release/archive acceptance remain with the independent acceptance runner.
