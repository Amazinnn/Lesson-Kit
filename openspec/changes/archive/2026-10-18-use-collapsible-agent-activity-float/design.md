# Design

## Decision

Use the existing Activity Float as the single task-progress surface for both
short and sustained Agent work. Do not open the Bottom Dock or reserve
middle-page height. Keep its summary bounded and keep detailed activity in the
conversation.

The Float's compact button controls expansion with a truthful accessible name
and `aria-expanded`. Once collapsed, later activity in the same turn updates
the underlying summary without reopening it. An explicit button action opens
the current Float. A new user turn clears the suppression. When activity ends
or the conversation changes, remove the Float and its control.

Artifact preview and approval remain independent auxiliary interactions.

## Implementation boundary

Reuse the current Agent UI controller, DOM, and CSS tokens. Keep the behavior
in the browser presentation layer; no data, API, provider, or service changes
are needed.
