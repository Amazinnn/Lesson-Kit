## Why

The approved removal of problem topic grouping dropped `problems.topic_label`
from the current schema and rejects it on problem writes. Several current
authorities still advertise that field, and the Agent's content instructions
ask for it on new and patched problems. The Agent can therefore produce a
manifest that the same repository rejects.

## What Changes

- Remove `topic_label` from the problem and micro-quiz field contracts and from
  the in-place problem-edit documentation.
- Clarify that the problem table supports `display_title` and
  `display_summary`, while `topic_label` remains an optional flash-card field.
- Align the content-bundle and problem-patch prompt sections with those
  contracts, and add a regression test for both sides of that boundary.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `micro-quiz-content`: problem manifests and edits no longer include
  `topic_label`; flash-card support is unchanged.

## Impact

- **Docs**: `openspec/specs/micro-quiz-content/spec.md`, `FILE_CONTRACT.md`,
  `docs/ARCHITECTURE.md`, and the problem-edit entry in `docs/GLOSSARY.md`.
- **Agent instructions**: `workbench/bridge/conversations.py`.
- **Tests**: `tests/workbench/test_conversations.py` verifies problem
  instructions omit the field and flash-card instructions retain it.
- **No runtime contract change**: ingestion already rejects problem
  `topic_label`; no schema, gate, or flash-card change is part of this work.
