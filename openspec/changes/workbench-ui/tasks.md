## 1. Static assets and shell

- [ ] 1.1 Add `/static/*` route serving `frontend/editable-graph/dist` with path containment
- [ ] 1.2 Three-column shell HTML (left selector: workspace dropdown + nav entries; middle page area; right AI column, collapsible)
- [ ] 1.3 Base CSS (minimal utilitarian style) and shell JS (column collapse, page switching)
- [ ] 1.4 KaTeX auto-render wired from `/static/` assets

## 2. Practice page

- [ ] 2.1 Practice page pulls problems (weak or by kp selection) with session de-dup (exclude_ids)
- [ ] 2.2 Problem card renders LaTeX, answer box for open problems, auto-grade display for option-bearing problems
- [ ] 2.3 "Show answer" reveals solution as blocks; feedback box (1–5, note, stuck-step marker) appears with the reveal; skip allowed
- [ ] 2.4 Recording: practice + feedback posts to existing endpoints; session array maintained in memory

## 3. Session-end unified self-rating

- [ ] 3.1 Session-end view lists only problems without feedback, with rating controls and skip-all
- [ ] 3.2 "Practice similar" single button pulls the same weak KP groups and starts a new round

## 4. AI column

- [ ] 4.1 Priority context display (current + recent problems from problem_detail), display-only
- [ ] 4.2 Explain/diagnose one-click with current problem + answer text + stuck marker; job polling; result rendering (four sections); new-session button
- [ ] 4.3 Graceful no-provider message; recording unaffected

## 5. Knowledge point display page

- [ ] 5.1 Markdown renderer: LaTeX, wiki links → kp page navigation, figures, tables, code blocks
- [ ] 5.2 KP page shows body, linked problems, signals with cascade reasons, schedule state

## 6. Verification

- [ ] 6.1 Backend tests stay green; add API tests if any endpoint was touched
- [ ] 6.2 Walkthrough: serve on 3081, practice flow with real dmath data, session-end rating, practice similar, AI explain (graceful without provider), kp page wiki navigation
- [ ] 6.3 openspec validate; small commits; archive the change
