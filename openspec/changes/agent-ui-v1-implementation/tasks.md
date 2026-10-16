# Tasks

## 1. PR135 — Agent rail foundation

- [ ] 1.1 Preserve the existing conversation-first rail, provider/session semantics, and primary Lesson Kit page while adding compact context chips and an autosizing composer.
- [ ] 1.2 Add the transient Activity Float, Bottom Dock, and Artifact Split containers with existing visual tokens and explicit collapse controls; keep runtime activation outside this foundation stage.
- [ ] 1.3 Update the live `workbench-ui` spec, Product Manual, Architecture module map, and action graph for the delivered foundation.
- [ ] 1.4 Run `openspec validate --specs --strict` on the PR135 worktree.

## 2. PR136 — Runtime surfaces and approval

- [ ] 2.1 Map normalized provider activity to a replaceable Activity Float or milestone Bottom Dock while preserving conversation activity history and collapsed output disclosures.
- [ ] 2.2 Keep the composer editable while a turn runs and make click/Enter submission single-flight before the server returns the turn id.
- [ ] 2.3 Treat progress-fetch failure as unknown status; keep turn identity and send gating until authoritative completion or cancellation.
- [ ] 2.4 Clear activities, poll position, transient surfaces, and Approval Gate state on conversation changes; invalidate stale callbacks.
- [ ] 2.5 Require Approval Gate consent before content-batch rollback and update the live spec, Product Manual, and action graph.
- [ ] 2.6 Run `openspec validate --specs --strict` on the PR136 worktree.

## 3. PR137 — Managed Paper Artifact handoff

- [ ] 3.1 Accept `paper_artifact` only after a successful managed-Paper save receipt and resolve its id against the selected workspace's managed record.
- [ ] 3.2 Populate Artifact identity, title, and item count from the managed record; discard model URLs and derive the native workspace destination.
- [ ] 3.3 Render one Artifact card per managed Paper per conversation; support a latest live preview that survives same-tab reload while historical cards stay closed and do not navigate.
- [ ] 3.4 Update the live `workbench-ui` and `ai-teacher-bridge` specs, FILE_CONTRACT, Product Manual, and action graph.
- [ ] 3.5 Run `openspec validate --specs --strict` on the PR137 worktree and `openspec validate --all --strict` for the combined change.

## 4. Combined acceptance and handoff

- [ ] 4.1 Independently review the combined PR135–137 implementation against this change and resolve any code/contract drift.
- [ ] 4.2 Complete the required combined repository gates and record their exact results.
- [ ] 4.3 Reconcile every task checkbox with review and gate evidence, then archive the change only after acceptance.
