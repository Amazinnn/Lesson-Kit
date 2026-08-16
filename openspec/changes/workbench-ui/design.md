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
   - `/w/{name}/` workspace home: left column + embedded page area; page
     switching is client-side navigation to `/w/{name}/practice`,
     `/w/{name}/kp/{kp_id}`, `/w/{name}/session-end`
   - `/static/*` serves `frontend/editable-graph/dist` (KaTeX js/css/fonts)
     with path containment
2. **API consumption**: all existing endpoints; the session-end view composes
   from `attempts`-rich `problem_detail` responses fetched per problem id —
   no new endpoint needed (each pending problem's detail includes its
   attempts and schedule).
3. **Session tracking client-side**: the practice page keeps a session array
   of problem ids + answers in memory (and sends exclude_ids on each pull);
   closing the browser loses only the in-flight session — recorded results
   are already in the pool (spec R: state in pool).
4. **Wiki links**: renderer converts `[[kp_id]]` to links to
   `/w/{name}/kp/{kp_id}`; LaTeX via KaTeX auto-render; figures via the
   existing figures API path.
5. **AI column context**: `GET /api/w/{name}/problem/{id}` results of current
   + last few problems are shown as a priority list; the agent's access is
   unaffected (CLI data interface). Explain/diagnose posts to the existing
   ai endpoints; polling via ai/jobs.

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
