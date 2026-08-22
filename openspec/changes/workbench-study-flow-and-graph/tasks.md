## 1. Specification and metadata

- [x] 1.1 Validate this change and update human-facing requirements, architecture, and v5 UI design record.
- [x] 1.2 Add failing migration/data tests for problem metadata and current learning state.
- [x] 1.3 Add additive schema, data access, legacy-state derivation, and reviewed metadata backfill.

## 2. Live graph and readable knowledge views

- [x] 2.1 Add failing domain/API tests for live graph model and overwrite-only state edits.
- [x] 2.2 Implement graph model/state operations without changing existing APIs or Bridge behavior.
- [x] 2.3 Replace the graph iframe and raw-ID knowledge views with native graph/detail and grouped titled problem presentation.

## 3. Explicit practice sessions

- [x] 3.1 Add failing production-JS interaction tests for mode selection, de-duplicated pulls, zero-write skips, immediate rating, and batch rating.
- [x] 3.2 Implement the smallest card-based session flow using existing feedback writes only on explicit score submission.
- [x] 3.3 Update route/SQLite tests for persistence boundaries and compatibility.

## 4. Verification and handoff

- [ ] 4.1 Run full pytest, JavaScript syntax, OpenSpec strict validation, pool guards, and local smoke checks.
- [ ] 4.2 Record final evidence in a dated changelog and archive the OpenSpec change after validation.
