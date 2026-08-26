# Agent session list information architecture

Replace the always-open Agent control console with a compact list, provider picker, and conversation view. Provider choice is immutable after creation. Lesson Kit stores only a local mirror and never deletes the external CLI session.

## Scope

- Add a title and title source to conversation mirrors.
- Add rename and local-delete endpoints.
- Remove automatic daily creation and provider switching from the visible UI.
- Accept an optional explicit title from the first successful provider result.

## Non-goals

- No remote Paseo service.
- No provider fallback, provider deletion, or new learning log.
