# Minimal Agent chat view

Reduce the Agent column to a clear session list and a quiet conversation view. Remove legacy client initialization and controls that imply automatic sessions, provider switching, or a second task console.

## Scope

- Keep history list, explicit provider picker, immutable provider per session, local rename/delete, free conversation, stop, and server-built context.
- In chat view retain only an icon back action, messages, input, and the running stop action.
- Rename and delete are list-row menu actions.

## Non-goals

- No provider API changes, external-session deletion, Paseo service, or new learning log.
