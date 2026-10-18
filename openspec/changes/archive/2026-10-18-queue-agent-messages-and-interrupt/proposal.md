## Why

The existing bridge accepts only one turn and refuses another send while it runs, so the editable composer cannot reliably accept follow-up work. This change carries the approved queue and Interrupt and Send behavior from [`complete-agent-message-lifecycle`](../complete-agent-message-lifecycle/design.md) into a focused implementation contract; accepted-message durability and rail navigation already have separate owners.

## What Changes

- Accept additional messages into a per-conversation FIFO while one provider turn runs; keep each accepted context snapshot and process ordinary queued work after successful turns.
- Add explicit Interrupt and Send behavior that waits for the captured running turn's terminal acknowledgement, retains the new message, and leaves older queued work paused afterward.
- Pause retained work on failure or service recovery, with an explicit continue action; keep pending messages editable/removable until execution begins.
- Add a workspace browser preference for the default running-send action, with explicit queue and interrupt choices available from the composer.
- Keep the current Agent rail and streamed turn intact when another message is accepted into the queue.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ai-teacher-bridge`: accepted queue ordering, interruption acknowledgement, pause/recovery, and pending-message mutation.
- `workbench-ui`: running-send preference, per-send choices, pending controls, and composer availability while a turn runs.

## Impact

Uses existing `.lessonkit/jobs/conv-NNN/turn-NNN.json` artifacts, conversation ownership lock, provider worker, and cancellation interfaces. Extends existing turn and queue API routes plus the native JavaScript Agent rail; stores the default preference in the existing workspace-scoped browser settings. No new dependency, SQLite schema, scheduler, or provider capability is introduced. Paper approval behavior in the source lifecycle proposal remains out of scope.
