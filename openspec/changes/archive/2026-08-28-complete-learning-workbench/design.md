## Practice state

The browser stores `practice_content_mode` and `practice_rating_mode` in the
existing workspace-scoped session storage. The start card is disabled until a
knowledge-point scope, one content mode, and one rating mode exist. Pulls send
the content mode and existing `exclude_ids`; the rating mode only controls when
feedback is written. Unmarked legacy problems remain exam-only. A problem with
`options_json` may render choices, but the absence of options is not converted
into a different mode.

## Goals and plan

Goals are stored in `.lessonkit/goals.json` as a small workspace-local JSON
array. The additive API supports list/create/update/delete. The Domain planner
continues to consume facts and returns at most three coarse queue items. The
server writes a versioned plan only on explicit recalculation; the client
replaces the complete plan region, not only its total. Missing goals remain an
honest empty state.

## Agent action envelope

The prompt permits an optional final fenced JSON object with `lessonkit_action`.
The Bridge validates and mirrors it in the completed turn. A
`replace_practice_selection` action is accepted only when the turn request
contains an explicit practice intent flag; the browser then replaces the
workspace selection key and reports the change. Ordinary conversation ignores
the action. Invalid actions are shown as provider text and never mutate state.

## Knowledge views

The list receives a client-side sort selector with stable ascending/descending
toggles. Default order is the source course/chapter order. The graph keeps its
relationship layout by default and can project existing `problem_count`,
`importance`, `state`, or `attraction` into deterministic radial emphasis and
color classes. Projection never changes the underlying graph edges or writes
coordinates.

## Non-goals

No calendar, workload curve, selectable learning model, general plugin installer,
cross-disciplinary graph, automatic candidate generation, or new mastery
claims are implemented by this change.

