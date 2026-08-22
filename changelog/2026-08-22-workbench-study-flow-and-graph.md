# 2026-08-22 Workbench study flow and graph

## Final state

- The 303 durable dmath problems now have concise display titles and one topic label; the empty candidate pool has the same additive fields ready for later entries.
- Weak knowledge points and related problems lead with readable names, titles, and grouped topics; stable IDs remain secondary context.
- The graph is a native workbench view backed by the live SQLite model, with search, state filtering, zoom, focus, knowledge-point detail, explicit content save, and current-state editing. It no longer embeds the old graph shell.
- Practice begins only after the learner chooses immediate or end-of-session self-rating. Sessions show one reading card at a time, exclude already seen problems, support skip and early end, and use one 1–5 score input with an optional note.
- Only explicit ratings, graph-state edits, and knowledge-point content saves persist. Navigation, reveal, drafts, skips, and session control remain browser-session state.

## Verification

- `python -m pytest tests -q` — `173 passed in 44.91s`
- `node --check workbench/server/static/workbench.js`
- `openspec validate workbench-study-flow-and-graph --strict`
- `python lessonkit.py guard extract-problems --course dmath --chapter ch06`
- `python lessonkit.py guard problem-set --course dmath --chapter ch06`
- Live smoke on `http://127.0.0.1:3081/`: practice, knowledge list/detail, native graph, session end, and graph model all returned 200; mode selection, canvas-without-iframe, and grouped related problems were present.
