## Why

The first real import in the `大学物理乙II` workspace exposed limits that the
pre-release fixtures did not cover. The conversation prompt tells the Agent to
produce only 3–6 items, browser keyword regexes decide whether structured
actions may run, and the conversation path offers no governed formal-problem
or figure operation. As a result, 29 originally non-choice textbook exercises
were forced into single-choice micro quizzes, one exercise was omitted, and no
figures were copied.

Micro Quiz itself is not the defect. The project formalized it on 2026-08-28
from the earlier wish for simple generated judgement/choice practice, and the
owner later retained it beside the other problem types. The scope drift was
using that first supported generation type as the universal import path for
source exercises.

The same run showed two presentation/runtime gaps: Pi's Markdown tables render
as literal pipes, and each Pi turn starts a new visible Windows process even
though Pi 0.85.1 provides a persistent RPC integration mode.

## What Changes

- Keep Micro Quiz and the existing four practice entries unchanged; add the
  missing governed formal-problem path and preserve every requested source type.
- Replace inline 3–6 item replies with a conversation-staged content bundle
  containing knowledge points, problems/cards, and required figures; validate
  and apply the complete bundle under one atomic batch id.
- Remove browser keyword gating. A valid append-only content action executes
  automatically; updates, deletes, rollback, and difficulty still require an
  explicit learner instruction.
- Preserve source evidence and source answers, mark on-demand AI explanations,
  copy original figure bytes into the existing chapter figure area, and show
  those facts in the workbench.
- Complete the shared safe Markdown subset with GFM tables.
- Run one hidden Pi RPC process per conversation and hide every provider child
  process on Windows.

## Capabilities

### Modified Capabilities

- `ai-teacher-bridge`: action routing, staged bundles, and Pi RPC lifecycle.
- `workbench-content-governance`: atomic multi-asset imports and source fidelity.
- `workbench-ui`: result/source labels and complete safe rich text.
- `knowledge-figures`: atomic source-image import and rollback cleanup.

## Impact

Conversation action contracts, content schema/gates, batch rollback, provider
process management, both Markdown renderers, product documentation, and real
workspace remediation. Runtime remains stdlib-only; no embedded AI kernel or
Markdown dependency is introduced.

