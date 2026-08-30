# Atomic learning writes

- Added a nested transaction boundary to the workspace Pool.
- Practice results now commit attempt history, current progress, and scheduling
  together or roll all three back.
- Feedback and direct state changes now commit signals, events, current state,
  progress, and scheduling as one unit.
- Added failure-injection tests proving partial learning records are not left
  behind when the final schedule write fails.
