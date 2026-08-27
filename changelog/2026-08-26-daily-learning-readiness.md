# 2026-08-26 daily learning readiness

- Added composable `wb ingest` preparation, execution, gate, apply, render, and recipe commands. Provider choice is explicit, recipes are zero-write by default, and qualified formal recovery is transactional.
- Completed independent solution and mapping audit for the current chapter. The active pool now contains 303 formal problems with non-empty solutions, 31 knowledge points, and the 13 approved mapping corrections; `pool/dmath-pre-readiness-2026-08-26.db` is the recoverable pre-switch copy.
- Restored tab-scoped practice mode, current card, seen ids, and unified-rating queues. Knowledge-point pages now provide one scoped practice entry, mobile layouts use navigation and conversation drawers, and student pages show concise action reminders instead of internal signal or scheduling parameters.
- Reworked the native graph into deterministic component layouts with multi-start selection, packed isolates, curved edges, neighborhood focus, drag/zoom/filter support, and reduced-motion behavior. Live browser rendering shows 31 nodes and 35 edges.
- Added the read-only `mastery v0` experiment with evidence-based categories and reasons. Its tests verify that evaluation does not change SQLite contents or row counts.
- Problem and conversation rich text safely renders limited Markdown plus balanced attribute-free `sup`/`sub` elements while continuing to escape unknown HTML.
- Knowledge-point-scoped practice now distinguishes a same-scope refresh from a new handoff: matching sessions restore their current card and queue, while a different scope starts cleanly.
- The deterministic content gate rejects unknown HTML with attributes. The current dmath ch06 recovery gate also requires the exact approved three knowledge points and thirteen mappings until that recovery reaches its final state; generic solution-only ingestion remains available outside that pending recovery.

Verification evidence:

- `python -m pytest tests -q`: 255 passed.
- `node --check workbench/server/static/workbench.js` and `graph-physics.js`: passed.
- `openspec validate daily-learning-readiness-audit --strict` and `openspec doctor`: passed.
- `guard extract-problems` and `guard problem-set` for `dmath/ch06`: PASS.
- SQLite: 303 problems, 0 empty solutions, 31 knowledge points, `PRAGMA integrity_check = ok`.
- Chrome acceptance at 375px, 1024px, and 1440px covered practice restoration, scoped practice, mobile drawers, safe problem markup, graph rendering/focus, and application console errors.
- Independent read-only code and contract review returned `READY` after the three material findings were fixed and re-reviewed.
