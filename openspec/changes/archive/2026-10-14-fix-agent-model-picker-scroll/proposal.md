## Why

On desktop, a long Agent model list grows beyond the provider picker and is clipped by the right column, so native wheel input cannot reach the hidden options. The existing picker already provides a dedicated place to choose a model; this change restores usable scrolling there.

## What Changes

- Keep the visible provider picker within its available height and let its options list scroll natively.
- Keep the picker heading and helper text visible while the list scrolls.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-ui`: define scroll behavior for a long visible new-conversation provider picker.

## Impact

- Affected: `workbench/server/static/workbench.css`, the `workbench-ui` behavior specification, and the matching provider-picker paragraph in the product manual.
- No API, session, data, or dependency changes.
