## Why

The workbench is about to enter real use, but live specifications and entry
documents still describe removed candidate, review-page, and explain/diagnose
flows. The active conversation mirror also has a Windows read/replace race
that can fail while the browser polls a running Agent turn.

## What Changes

- Serialize all in-process conversation-mirror reads and writes without
  changing the JSONL polling protocol.
- Remove retired review-page, candidate, and explain/diagnose requirements
  from the live contract while retaining historical archives.
- Make current entry documents route only to supported workbench and Check
  flows, and add a small regression check for retired language.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ai-teacher-bridge`: active mirror reads remain valid while turn files are updated.
- `review-workbench`: the Agent data CLI and context contract describe only current entities and free conversation.
- `workbench-ui`: the obsolete one-click explain/diagnose surface is removed from the live specification.
- `review-page`: the deprecated capability is removed from the live specification.

## Impact

Conversation mirror I/O, documentation tests, live OpenSpec files, and the
repository's current-entry documentation. No learning data or public route is
changed.
