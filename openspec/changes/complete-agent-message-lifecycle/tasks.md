## 1. Reliable message acceptance and reads

Owned by `preserve-agent-messages-and-tool-outcomes`. This change depends on its accepted-turn history and idempotent acceptance; it adds no duplicate implementation tasks here.

## 2. Single-worker queue and interruption

Owned by the focused `queue-agent-messages-and-interrupt` change; its implementation tasks and evidence live there.

## 3. Persistent right rail and real recovery UI

The base navigation lifecycle and context refresh are delivered by `preserve-agent-rail-across-navigation`. The tasks below retain only their remaining message/queue integration and recovery obligations; do not reimplement the delivered navigation.

- [x] 3.1 Mount rail outside middle navigation lifecycle; preserve its DOM/controller/draft/scroll/tasks/queue across all same-workspace middle views and back/forward — delivered by `preserve-agent-rail-across-navigation`.
- [x] 3.2 Refresh context chips for the selected page without changing accepted-message context; dispose/reinitialize only middle-owned resources — delivered by `preserve-agent-rail-across-navigation`.
- 3.3 Semantic Tool Call Card and message recovery are owned by `preserve-agent-messages-and-tool-outcomes`.
- [ ] 3.4 Integrate explicit Paper progress-reset approval, retain existing rollback gate and invalidate obsolete callbacks. Do not implement HTML styling/tuning/preset controls as product features.
- [ ] 3.5 Persist a proposed Paper update and pending approval in the existing turn/conversation store; pause queue dispatch before the proposing worker hands off, without keeping a provider running for human input.
- [ ] 3.6 Add page-driven approval/cancellation using existing Paper preview/update logic; show exact impact, reject stale confirmation without writing, refresh impact and require another click. Prevent duplicate reset on repeated/uncertain submission.
- [ ] 3.7 Restore pending approval across reload/reopen/recovery; keep the composer usable and all new messages queued while approval is pending. Block queue continuation until resolution; after approval/cancellation leave it paused for manual continuation.
- [ ] 3.8 Reconcile FILE_CONTRACT, live specs, Product Manual and Action Graph in the implementation PR; preserve the existing rollback input-replacement behavior.

Activity progress-surface ownership is handled by the independent `use-collapsible-agent-activity-float` change.

## 4. Independent acceptance
- [x] 4.1 Reproduce swallowed messages with rejected POST and failed fake provider, then prove persistence across reload, history reopen and navigation — owned and delivered by `preserve-agent-messages-and-tool-outcomes`.
- [x] 4.2 Cover idempotent acceptance, cancellation timeout, one-worker queue ordering, failure pause, A/B/C/D priority, restart and legacy success-history deduplication — focused conversation/API and Pi cancellation tests pass.
- [x] 4.3 Verify literal rail DOM identity, draft, scroll, focus, streaming and queue retention across views — isolated Chromium acceptance passed.
- [ ] 4.4 Run the required gates and isolated browser acceptance for the remaining Paper approval implementation; earlier queue CI does not complete this pending work.
- [ ] 4.5 Cover approval/cancel writes, A-to-B/C pause before handoff, pending-message acceptance, blocked early continuation, stale-progress refresh/reconfirmation, reload/recovery, wrong-conversation callbacks and duplicate-click/unknown-response behavior; prove attempts/ratings, questions and other Papers remain unchanged.
