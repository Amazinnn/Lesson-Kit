## Context

The backend contract is archived (main specs: review-workbench 14,
ai-teacher-bridge 10, knowledge-figures 5) and implemented. This change adds
the UI shell only. See proposal.md for motivation; this design covers pages,
routing, assets, and the one additive endpoint.

Constraints: server-rendered pages from `workbench/server/pages.py` (stdlib),
vanilla JS, zero build step, KaTeX assets reused from
`frontend/editable-graph/dist` via `/static/`, single process single port,
Chinese UI, minimal feature set.

## Goals / Non-Goals

Goals:

- Three-column shell: left selector (workspace dropdown + navigation),
  middle page area, right AI column (collapsible).
- Practice page consuming the existing pull/practice/feedback endpoints;
  reveal-then-feedback flow; session-end unified self-rating with "practice
  similar".
- Knowledge point display page (Markdown renderer: LaTeX, wiki links,
  figures; signals with reasons).
- AI column with priority-context display, explain/diagnose one-click,
  polling, rendered results; graceful no-provider message.

Non-Goals: review page, memory cards, agent organization panel, batch reveal,
extended summaries, generate op, Scoropic — all deferred (proposal).

## Decisions

1. **Page routes** (server-rendered, added to `app.py` dispatch):
   - `/` hub (existing) → links to workspaces
   - `/w/{name}/practice` — practice page (message stream)
   - `/w/{name}/kps` — knowledge point list page (weak order)
   - `/w/{name}/kp/{kp_id}` — knowledge point display page
   - `/w/{name}/graph` — knowledge graph page (iframe of rendered artifact or
     generation hint)
   - `/w/{name}/session-end` — session-end unified self-rating
   - `/static/*` serves `workbench/server/static/` first, then
     `frontend/editable-graph/dist` (KaTeX) with path containment
2. **Knowledge graph endpoint**: `GET /api/w/{name}/graph` returns the
   rendered graph HTML artifact
   (`output/{course}/{chapter}/{chapter}-graph.html`); when missing it
   returns 404 with a hint naming the generation command
   (`render-graph-html.py`). The page renders the artifact in an iframe or the
   hint. Display-only in v1.
3. **DSH design tokens** (copied from the live DeepSeek Harness GUI CSS):
   font stack, bg-base #f9fafb, labels #0f1115/#61666b/#81858c, brand
   #3964fe, border rgb(0 0 0/10%), pill buttons (md h36 r18 / sm h28 r14),
   input h32 r8, card r12 + shadow-lv3, state dots — implemented as CSS
   variables in `workbench/server/static/workbench.css`.
4. **API consumption**: all existing endpoints; session-end composes from
   problem_detail per pending problem id (no new endpoint needed).
5. **Session tracking client-side**: practice page keeps session array
   (problem ids + answers) in sessionStorage; exclude_ids sent on each pull;
   closing the browser loses only the in-flight queue — recorded results are
   in the pool.
6. **Wiki links**: renderer converts `[[kp_id]]` to `/w/{name}/kp/{kp_id}`;
   LaTeX via KaTeX; figures via the figures API path.
7. **AI column context**: current + recent problems shown as a priority list;
   the agent's access is unaffected (CLI data interface). Explain/diagnose
   posts to the ai endpoints; polling via ai/jobs; results rendered with the
   four-section contract.

## Risks / Trade-offs

- [Client-side session state lost on refresh] → recorded data is in the pool;
  the in-flight queue is cheap to re-pull.
- [Server-rendered pages limit polish] → accepted by design; API is the
  contract, pages evolve freely.
- [KaTeX dist path drift] → `/static/` pinned to the dist directory; verify
  asset names during walkthrough.

## Migration Plan

None — additive pages and one static route; no data changes.

## Open Questions

None that change the specs or approach.
