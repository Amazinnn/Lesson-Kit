# Complete Learning Workbench Design

## Decision

Finish the daily-use loop before adding experimental research surfaces. A
practice session has two independent choices: what kind of content is being
practised and when the learner self-rates. Knowledge views remain the only
manual scope selector. Goals are real workspace data, while the deterministic
planner remains the fallback. Agent actions are structured, explicit-intent
only, and reflected back into the browser instead of silently mutating state.

## Deliberate deferrals

Calendar, workload curves, learning-model selection, graph multi-axis layouts,
automatic AI question generation, cross-disciplinary views, and third-party
plugin installation remain future experiments. They have no visible controls in
this implementation unless an existing empty contract is already required;
such a contract must show an honest unavailable state.

## Verification boundary

Every implemented behavior gets a failing test first. The final gate is the
full pytest suite, Node browser tests, strict OpenSpec validation, both pool
guards, and an HTTP smoke check. The active OpenSpec is not archived until all
tasks are green.

