## Baseline planning

The planner reads course goals, stage goals, active workspace scope, coverage, existing progress, deadline distance, and available formal problem types through existing Data queries. It returns a deterministic plan with coarse queue items; it does not create new mastery states or write learning events.

Each queue item identifies a readable goal, related knowledge-point IDs, an aggregate target quantity, a broad difficulty mix, and a reason. Missing numeric values use stable type-appropriate defaults. The planner is repeatable for the same inputs.

## Agent adjustment

The Agent receives the baseline plan and explicit student feedback. It may adjust plan values within the current workspace and returns one atomic batch result. A completed batch is persisted and causes affected cards to refresh. Internal CLI/tool events are status-only and are not durable learning logs. If Agent execution fails, the baseline remains the usable plan.

## UI

The practice page renders long-term goals, stage goals, and today's coarse queue as vertically ordered cards. The page keeps one obvious primary action and offers exam, Flash Card, or Yes/No entry choices without exposing internal algorithm provenance. The Agent header contains the current friendly status and the stop control beside the existing return control.

## Triggering

On the first opening of a workspace each local calendar day, the server may request one recalculation. Explicit student requests may request another. No process runs while the application is closed, and no new visible state-machine values are introduced.
