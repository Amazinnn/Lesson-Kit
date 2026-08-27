## Why

The graph still appears to twitch when idle, and the existing compactness range has too little visible effect on a real graph. A calm, Obsidian-like graph should settle and stay still until the learner interacts with it.

## What Changes

- Remove post-settle breathing and continuous idle animation.
- Increase the in-memory center-gravity range while preserving the existing slider.
- Keep the graph's relationship forces, free dragging, labels, zoom, and non-persistent coordinates unchanged.
- Record a separate future direction for learning-oriented graph morphology without implementing speculative controls now.

## Capabilities

### Modified Capabilities

- `workbench-ui`
- `knowledge-figures`

## Impact

Only graph browser physics, interaction scheduling, tests, and documentation change. No database, API, learning record, dependency, or external-provider behavior changes.
