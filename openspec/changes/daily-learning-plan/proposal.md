## Why

Students need a clear first action each day without depending entirely on an Agent. The workbench should derive a coarse queue from course goals and current progress, then let the Agent adjust it when natural-language feedback adds context.

## What Changes

- Add a deterministic, read/write-safe baseline plan for the active workspace.
- Show long-term goals, stage goals, and today's short queue together on the practice page.
- Allow students to choose the existing exam, Flash Card, or Yes/No practice path for a queue item.
- Allow explicit Agent recalculation and daily-first-open recalculation with visible status and baseline fallback.
- Keep calendar, workload curves, selectable learning models, plugin ecosystem, cross-disciplinary graph, and AI-generated content as later experiments.

## Capabilities

### New Capabilities

- `daily-learning-plan`

### Modified Capabilities

- `workbench-ui`: practice page includes coarse plan cards, queue actions, and Agent status.
- `review-workbench`: plan generation uses course goals and progress without changing learning-write semantics.
- `ai-teacher-bridge`: Agent may adjust a plan through an explicit bounded batch and report status events.

## Impact

Changes are limited to `workbench/`, tests, OpenSpec, and documentation. Existing routes, storage keys, learning APIs, provider compatibility, and state-machine vocabulary remain compatible. No background service runs while the application is closed.
