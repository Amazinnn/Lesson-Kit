# 2026-08-16 Frontend Phase 0: P0 fixes (workbench UI)

Per `docs/frontend-optimization-plan.md` (v3, three-way converged: coordinator / Claude Code / read-only advisor), Phase 0 fixes the five P0 breaks in the practice flow. No backend behavior contracts touched (domain/data/bridge/cli unchanged).

## Fixes

1. `.hidden { display: none !important; }` added to workbench.css — the rule was missing entirely, so every classList visibility toggle in the practice flow was a no-op (all controls always visible; clicking 看答案 without a problem threw a TypeError).
2. `loadNext` now resets `answerBox.disabled` — the answer box stayed disabled from problem 2 onward.
3. `bindFeedback` now receives the just-appended message element and scopes `.feedback` / `.solution-block` queries to it — previously `:last-of-type` always resolved to the FIRST message's feedback, so ratings and stuck-step clicks on problems 2+ did nothing (and stuck-step binding never found its blocks).
4. The 去会话末统一自评 button moved out of `#composer` into `#session-end-entry` (always visible) — previously it was hidden together with the composer at pool exhaustion and unreachable mid-session.
5. New raw-HTML route `/api/w/{name}/graph/artifact` (app.py `_send_graph_artifact`, text/html); the graph page iframe now points at it — previously the iframe loaded the JSON API response and showed raw JSON instead of the graph.

## Regression tests added (tests/workbench/test_ui_routes.py)

- CSS serves the `.hidden` rule
- practice page: session-end entry outside composer, always visible, no `outline hidden` markup
- graph page iframe points at `/graph/artifact`, not the JSON route
- artifact route: 200 + text/html with artifact body; 404 when missing

## Verification

- `python -m pytest tests -q` → **157 passed** (152 baseline + 5 new)
- `openspec validate workbench-ui` → valid
- Smoke on :3099 (workspace lesson-kit): /, practice, kps, kp detail, graph, session-end, static css/js/katex all 200; artifact route 200 text/html with real graph HTML; old hidden-button markup absent; composer still starts hidden
- `node --check workbench.js` → syntax OK

Commits: `bfb3c53` (docs: plan v3), `792caeb` (fix: phase-0 P0 fixes).

## Next step

Phase 1 per plan (P1 items: KP-page KaTeX init, rating message/attempt semantics, session-end unrated filter, practice-similar queue reset, async AI task in api.py, collapsible AI column, next-without-feedback entry, decision items: AI recent-problems context, auto-grade).