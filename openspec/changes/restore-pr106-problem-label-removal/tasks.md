## Implementation

- [x] 1. Specify the replacement for ordinary-ensure label retention.
- [x] 2. Observe failing temporary-database tests for legacy and current schemas.
- [x] 3. Restore physical deletion without changing flash-card labels.
- [x] 4. Synchronize DATA_MODEL, architecture, product manual and action history.
- [x] 5. Run focused schema/data/ingest tests, compile and strict OpenSpec checks.
- [x] 6. Commit the owned paths and write the implementation handoff.

## Operator and acceptance

- [ ] 7. Back up all 17 registered databases; prove migration and recovery on copies.
- [ ] 8. Remove the c05 view's target projection, then drop only the target column
  under a live lock/transaction, preserving all other rows and schema objects.
- [ ] 9. Align runtime to verified code and independently review/accept the result.
