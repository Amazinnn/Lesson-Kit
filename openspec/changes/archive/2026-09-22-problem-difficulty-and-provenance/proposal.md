## Why

The current optional scalar difficulty is unauditable, unused, and coupled to
content ingestion, while `source_kind` mixes source material with generated
micro-quiz form. Pre-release data needs independent provenance and a lazy,
filterable difficulty vector before real study data accumulates.

## What Changes

- **BREAKING:** rebuild `problems.difficulty` as a REAL total derived from four
  stored cognitive dimensions; old scalar values are cleared.
- Add `origin_kind` beside `source_kind` and expose mutually exclusive
  textbook/exam/AI-generated convenience groups.
- Add an explicit transactional `lesson-kit difficulty ... check|apply` flow;
  content ingest never triggers rating.
- Add opt-in provenance/difficulty filters, balanced pulling, and hidden plan
  distribution data without changing default pull order or student UI.

## Capabilities

### New Capabilities

- `problem-difficulty`: lazy four-dimensional rating, computation, invalidation, and explicit filtering.

### Modified Capabilities

- `workbench-content-governance`: content provenance is required and difficulty is removed from ingest.
- `review-workbench`: pull and CLI contracts gain provenance/difficulty operations.
- `daily-learning-plan`: plan data carries hidden difficulty distribution and mix.
- `ai-teacher-bridge`: an Agent may rate only after explicit learner intent.

## Impact

Workbench schema migration, pure domain rules, Data-layer rating transaction,
CLI/API pull surfaces, Agent prompt, and documentation. No dependency or
student-facing filter is added.
