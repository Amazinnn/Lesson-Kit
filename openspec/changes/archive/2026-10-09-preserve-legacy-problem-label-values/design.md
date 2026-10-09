# Design

Remove the unconditional DROP COLUMN from the existing ensure path. Retain the
existing compatible rebuild's copy of `topic_label`; do not create a replacement
field or sidecar. New problem validation and display remain retired as approved.
The legacy column is storage compatibility, not an active writing interface.

Tests seed nonempty values in temporary legacy and migrated schemas, preserve
the same problem IDs and learning rows, then run ensure twice to prove retention
and idempotence. Real-course verification uses read-only connections and SQLite
backups into temporary directories; source course pools are never migrated.

Any future field deletion requires its own explicit migration specification,
recoverable before-image and acceptance. That operation is outside this change.
