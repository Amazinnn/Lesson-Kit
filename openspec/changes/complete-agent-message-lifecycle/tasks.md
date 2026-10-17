## 1. Reliable message acceptance and reads
- [ ] 1.1 Reconcile glossary/live specs, FILE_CONTRACT, affected DATA_MODEL, Architecture, Product Manual and Action Graph; preserve legacy transcript compatibility.
- [ ] 1.2 Persist outgoing identity/text/context before composer clearing and server acceptance before dispatch; deduplicate lost-response retries and distinguish unknown acceptance.
- [ ] 1.3 Return accepted failed/cancelled/pending messages in history with truthful output/status and safe edit/retry controls; never overwrite a newer draft or silently remove the original message.

## 2. Single-worker queue and interruption
- [ ] 2.1 Add ordered accepted pending messages to existing conversation artifacts; one worker per conversation, durable queue and submission-time context.
- [ ] 2.2 Add workspace running-send preference (queue by default), explicit queue/interrupt actions and inspect/edit/remove pending controls.
- [ ] 2.3 Implement A interrupted by D while B/C remain paused; wait for real cancellation acknowledgement, never auto-resume A or auto-replay its writes.
- [ ] 2.4 Pause retained queue on actual failure/unexpected interruption/service recovery; progress-read loss alone remains nonterminal.

## 3. Persistent right rail and real recovery UI
- [ ] 3.1 Mount rail outside middle navigation lifecycle; preserve its DOM/controller/draft/scroll/tasks/queue across all same-workspace middle views and back/forward.
- [ ] 3.2 Refresh context chips for the selected page without changing accepted-message context; dispose/reinitialize only middle-owned resources.
- [ ] 3.3 Complete semantic Tool Call Card/failure-impact/folded-diagnostics interactions using normalized evidence; expose only backend-supported retry/read-only recovery.
- [ ] 3.4 Integrate explicit Paper progress-reset approval, retain existing rollback gate and invalidate obsolete callbacks. Do not implement HTML styling/tuning/preset controls as product features.

Activity progress-surface ownership is handled by the independent `use-collapsible-agent-activity-float` change.

## 4. Independent acceptance
- [ ] 4.1 Reproduce swallowed messages with rejected POST and failed fake provider, then prove persistence across reload, history reopen and navigation.
- [ ] 4.2 Cover idempotent acceptance, cancellation timeout, one-worker queue ordering, failure pause, A/B/C/D priority, restart and legacy success-history deduplication.
- [ ] 4.3 Verify literal rail DOM identity, draft, scroll, focus, streaming and queue retention across views; do not substitute a restored-ID unit test.
- [ ] 4.4 Run required Python/official JS/compileall/strict OpenSpec/extraction gates and independent isolated browser acceptance; archive only after actual implementation acceptance.
