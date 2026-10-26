# Design

The shared `lkStreak` state machine remains the only counter. Its HTML returns only the transient banner node, and ordinary practice gives that node a zero-height anchor so it adds no resting space. Paper renders no shared streak HTML because its approved `PixelPracticeMotion.combo` uses `streak.count()` to show the separate pixel banner. Remove the counter/flame DOM; reuse the visible question card for the existing short break nudge.

The change is confined to `workbench/server/static/` and presentation contracts. No new component, API or persisted state is needed.
