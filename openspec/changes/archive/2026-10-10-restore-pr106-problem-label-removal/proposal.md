# Restore the PR106 problem-label schema contract

## Why

PR106 removed `problems.topic_label` from the problem contract and schema. PR111
retained that column and historical values without authorization. The owner has
explicitly required current and migrated databases to match PR106, while allowing
old database backups for recovery.

## What Changes

- Restore physical removal of `problems.topic_label` during schema ensure;
  rebuilt problem tables omit the field from their DDL and copy projection.
- Supersede the current ordinary-ensure retention requirement. Historical
  retention documents and audits remain historical, not current authority.
- Preserve every other current problem value, learning row and schema object,
  and preserve the independent `flash_cards.topic_label` contract.
- Back up the 17 registered course databases and prove recovery before a
  targeted live migration. The observed c05 `problems_by_chapter` view needs
  only its `p.topic_label` projection removed before the column drop; all its
  other SQL and columns remain unchanged. Other dependencies block migration.

## Impact

The existing schema ensure, migration tests, persistent-field contract and
current OpenSpec requirement change. There is no new CLI, API, dependency,
retention table or hidden replacement field. Live migration and runtime alignment
belong to the operator; the implementation worker uses temporary databases only.
