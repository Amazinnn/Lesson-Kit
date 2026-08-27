## Why

Sidebar dragging must consume only the flexible middle column, and chat mode must not reserve space for hidden session controls.

## What Changes

- Keep both sidebar outer edges fixed to the viewport while resizing.
- Preserve a 420px minimum middle column.
- Hide the entire session-controls region in chat mode so messages and input fill the right column.

## Impact

Client markup, CSS, tests, and documentation only. No API or learning-record changes.
