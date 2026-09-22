## Why

Pi already emits useful tool and command events, but the workbench hides them
inside one execution-plan card. Real use needs concrete read/write/search/CLI
actions to appear in conversation order without exposing reasoning or building
a second streaming protocol.

## What Changes

- Render Pi's concrete activities as independent compact messages while they run.
- Give file, search, shell, and Lesson Kit CLI operations specific readable labels.
- Split live assistant text at intervening activities, fold all outputs by default,
  and retain only successful coalesced activities.
- Keep Codex/Claude presentation and the 350ms polling transport unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ai-teacher-bridge`: Pi emits only bounded, sanitized concrete activity records.
- `workbench-ui`: Pi activities become ordered conversation messages.

## Impact

Pi normalization, conversation mirror activity filtering, native workbench JS/CSS,
and provider/UI tests. No provider command, dependency, or API transport changes.
