## Why

The Agent conversation is useful across the workbench, but its current presentation does not yet provide a clear contract for transient runtime work, explicit rollback consent, or a saved Paper handoff. The accepted Agent UI v1 baseline now needs observable behavior defined across the three stacked implementation PRs so the central learning page stays primary and managed Paper results remain trustworthy.

## What Changes

- Give the existing right Agent rail a conversation-first presentation foundation with compact page/context chips, a growing composer, and central auxiliary-surface containers that reuse the existing Soft Mondrian tokens.
- Map short and sustained provider activity to a replaceable Activity Float or a temporary Bottom Dock while retaining the existing conversation activity/history, respecting an explicit collapse for the current turn, and clearing session-bound runtime state on conversation changes.
- Add an Approval Gate for content-batch rollback, keep the composer editable during a running turn while preventing a second send, and distinguish an unavailable progress poll from a confirmed provider failure.
- Add a validated `paper_artifact` action for a managed saved Paper, render its conversation card and latest-result preview, and require explicit navigation to the Paper page.
- Update the workbench UI and Agent bridge contracts, Agent manual, File Contract, architecture module map, and action graph. Do not add a Paper lifecycle, data schema, API, provider, or parallel task engine.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-ui`: define the Agent rail foundation, transient work surfaces, collapse and session-reset behavior, guarded sending, rollback approval, and managed Paper Artifact presentation.
- `ai-teacher-bridge`: define the validated `paper_artifact` action and require Artifact identity, title, and item count to be verified against the managed Paper record.

## Impact

The presentation touches `workbench/server/pages.py`, the Agent UI static module and stylesheet, and `workbench/server/static/workbench.js`. The bridge action contract touches `workbench/bridge/agent_contracts.py` and `workbench/bridge/conversation_actions.py`; it reads the existing `.lessonkit/practice-sets/ps-NNN.json` managed Paper store. Existing routes and writers remain authoritative. No pool schema or learning-record change is proposed.
