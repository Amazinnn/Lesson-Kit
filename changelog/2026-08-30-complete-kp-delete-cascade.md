# Complete knowledge-point deletion cascade

- Knowledge-point deletion now removes owned flash cards and their feedback,
  schedule, current-state, and signal rows in the same SQLite transaction.
- Legacy companion questions, question progress, and KP progress no longer
  survive as orphan rows after their knowledge point is deleted.
- Added a regression test covering every dependent table.
