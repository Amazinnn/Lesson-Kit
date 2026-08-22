# 2026-08-22 Linked problem summaries

## Final state

- Knowledge-point linked problems retain their topic groups and concise titles.
- Each linked-problem row now shows a cleaned, one-line problem summary capped at 56 characters.
- Raw problem IDs no longer appear in linked-problem rows.

## Verification

- `python -m pytest tests/workbench/test_ui_routes.py -q` — `22 passed in 18.34s`
- `python -m pytest tests -q` — `173 passed in 38.45s`
- `node --check workbench/server/static/workbench.js`
- `openspec validate workbench-ui --strict`
- Both dmath pool guards passed.
- A fresh server on `:3082` returned the knowledge-point page with title and summary markup and without a raw linked-problem ID.
