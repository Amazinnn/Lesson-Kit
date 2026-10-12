# Agent contract disclosure repair — 2026-10-12

PR116 now gives the compact `problem_type` map only the stored English enum,
with `proof = 证明题` kept as a separate display explanation. The detailed
content topic states the one-knowledge-point rule for new micro quizzes and
in-place conversions, and the scalar/list answer-key shapes. The existing
`commands` topic documents the read-only evidence query route and its 8/20
limits; the five existing topics and installed module route stay unchanged.

Glossary, architecture, product manual, and action-graph entries now describe
the installed read-only module. Chapter wording is reconciled to the current
OpenSpec and `FILE_CONTRACT.md`: missing item and bundle chapters are refused,
with no fallback to the workspace's current chapter. The ingest validator is
unchanged. A focused fixture also exposed that a localized `problem_type` can
pass on the micro-quiz branch; this pre-existing validation gap is recorded as
pending conformance work in `openspec/changes/ingest-integrity-and-observability/tasks.md` §1.4.

Verification: focused contract/conversation tests passed (71); scoped ingest,
micro-quiz, and content-bundle tests passed (95); compileall passed; strict
OpenSpec validation passed (19/19); a temporary venv install listed and read all
five topics from an empty working directory. Focused test runs used
`PYTHONUTF8=1`. Full-suite and release acceptance remain with the independent
acceptance owner.
