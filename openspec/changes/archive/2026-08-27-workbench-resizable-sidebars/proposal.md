## Why

Learners need to adjust the side-column reading space, and long Agent conversations must be scrollable with the mouse wheel.

## What Changes

- Add in-memory pointer-drag resize handles to the left and right columns.
- Constrain resizing to readable desktop ranges and leave mobile drawers unchanged.
- Make the Agent chat a constrained flex column so its message list owns vertical scrolling.

## Impact

Only workbench markup, CSS, client interaction, tests, and documentation change. No API, storage, or learning behavior changes.
