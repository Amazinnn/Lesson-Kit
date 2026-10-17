## 1. Extract the progress-surface contract

- [x] 1.1 Move Activity Float/Bottom Dock ownership out of `complete-agent-message-lifecycle`; leave a pointer there and preserve the other message-lifecycle requirements.
- [ ] 1.2 Reconcile the live Glossary, Product Manual, and Action Graph for the float-only behavior and dock retirement.

## 2. Implement the bounded Float

- [ ] 2.1 Reuse the existing activity controller and Float for short and sustained work; remove task-progress use of the Bottom Dock.
- [ ] 2.2 Add the compact accessible expand/collapse control and preserve collapse for the same turn through activity updates.
- [ ] 2.3 Verify explicit reopen, new-turn reset, conversation cleanup, idle cleanup, and unchanged middle-page height.

## 3. Focused verification

- [ ] 3.1 Add focused regressions for Float-only sustained activity, collapse/reopen behavior, idle cleanup, and middle-page height.
- [ ] 3.2 Run the focused Agent UI test file and report the result for independent acceptance.
