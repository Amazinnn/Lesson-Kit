# Design notes

## Follow the current data model

The current problem contract has no `topic_label` column and its write gate
rejects that field. Problem-facing specifications, file contracts, and Agent
instructions must list only fields that the problem path accepts. The existing
`flash-card` capability continues to own its separate optional
`flash_cards.topic_label` field.

## Keep this documentation-only at runtime

No ingestion behavior or schema change is needed. The implementation change is
limited to the Agent's problem-field lists. A focused prompt test checks that
the new-problem and problem-patch sections omit `topic_label` while the
flash-card section retains it.
