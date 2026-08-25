## 1. Specification

- [x] 1.1 Record data governance, provider sessions, context, trace, UI, and compatibility contracts.
- [ ] 1.2 Add failing schema, Data CLI, cascade, provider, conversation, API, context, and browser tests.

## 2. Governed Agent data plane

- [x] 2.1 Add readable content sequences and Data-layer CRUD/history/state transactions.
- [x] 2.2 Add `wb data` JSON commands, candidate gate delegation, and gate-only promotion.
- [x] 2.3 Verify zero-write reads, gate reset, readable IDs, and full physical cascades.

## 3. Provider-native conversation bridge

- [ ] 3.1 Add PATH discovery and optional provider overrides.
- [ ] 3.2 Add provider-locked conversation storage, native new/resume commands, normalized events, cancellation, and successful transcript mirroring.
- [ ] 3.3 Add authoritative page-context reconstruction and internal conversation HTTP endpoints.

## 4. Right-column conversation UI

- [ ] 4.1 Replace visible task shortcuts with provider/session/free-message controls and recent-session recovery.
- [ ] 4.2 Add polling, partial/event display, cancel, daily local-date option, recent objects, optional draft attachment, and controlled refresh.
- [ ] 4.3 Verify free conversation on every page, context boundaries, one running turn, failure truthfulness, and narrow layout.

## 5. Delivery

- [ ] 5.1 Run full tests, production syntax checks, strict OpenSpec validation, both pool guards, and :3081 acceptance.
- [ ] 5.2 Run real Codex acceptance; report Claude as discovered-only without invoking it per the user's latest instruction.
- [ ] 5.3 Write changelog, archive, commit, and push main.
