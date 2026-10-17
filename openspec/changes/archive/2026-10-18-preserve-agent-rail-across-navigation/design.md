# Design

Fetch the destination's normal server-rendered page, then replace only the
middle page wrapper. Keep the `#ai-column` and its controller untouched, along
with the existing scope tray, Activity Float, and Agent auxiliary surfaces.
The server emits the same Agent rail on graph and non-graph pages. The graph
learning dashboard belongs to the graph middle page and is mounted and disposed
with that page; selecting graph nodes never hides or replaces the Agent chat.
Update the existing layout metadata, active navigation state, scope names, and
browser URL, then rerender context chips for the next submission. A request's
already captured context does not change.

The one-time workbench/Agent setup remains mounted. Add an explicit
middle-view mount/dispose boundary so route-local handlers, PracticeFlow
timers, and graph workers are released before replacement and initialized for
the new page. Server-rendered markup remains the source for each destination.

## Scope

This change implements only `complete-agent-message-lifecycle` requirements
3.1 and 3.2 and browser acceptance 4.3. Message acceptance, queue policy,
recovery controls, and provider behavior remain in that change.
