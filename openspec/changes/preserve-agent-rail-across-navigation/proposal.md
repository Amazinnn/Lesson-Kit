## Why

Same-workspace page navigation currently reloads the shell, recreating the
Agent rail and losing its live DOM state. This change implements only the
persistent-navigation slice already approved in
`complete-agent-message-lifecycle` (requirements 3.1–3.2 and acceptance 4.3).

## What Changes

- Replace same-workspace middle navigation with server-rendered middle content
  inside the existing shell, including browser back/forward navigation.
- Keep the existing Agent rail DOM and controller mounted; refresh only the
  page context used for future sends.
- Dispose and mount route-owned view behavior as middle content changes.
- Keep external, cross-workspace, modified-click, download, and explicitly
  targeted navigation native.

Queue, recovery, and message-lifecycle behavior remains in
`complete-agent-message-lifecycle`.

## Capabilities

### Modified Capabilities

- `workbench-ui`: preserve the Agent rail during same-workspace middle
  navigation.
