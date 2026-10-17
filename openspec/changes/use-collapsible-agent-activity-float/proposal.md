# Collapsible Activity Float for Agent work

## Why

The Bottom Dock opens across the bottom of the learning page during sustained
work. The owner has approved one bounded top-right Activity Float for both
short activity and long-running milestones, with a small accessible control
that keeps explicit reopen available after collapse.

## What Changes

- Use the replaceable Activity Float for short activity and sustained
  milestones; retire the Bottom Dock for task progress.
- Keep the Float bounded and leave the middle page at its existing usable
  height.
- Provide a small keyboard-accessible expand/collapse button with a truthful
  label and `aria-expanded` state.
- Preserve collapse through all activity updates in the same user turn, allow
  explicit reopening, and reset automatic presentation on a new turn.
- Remove the Float and its reopening control when no runtime activity remains.
- Keep conversation history authoritative and Artifact preview/approval as
  separate interactions.

## Capabilities

### Modified Capabilities

- `workbench-ui`: task progress presentation and same-turn Float collapse.

## Scope

Reuse the existing Agent surface and normalized activity flow. This change
does not add persistence, backend behavior, dependencies, or a second activity
history.
