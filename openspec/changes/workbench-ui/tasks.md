## 1. Static assets and shell

- [x] 1.1 Add `/static/*` route serving `frontend/editable-graph/dist` with path containment
- [x] 1.2 Three-column shell HTML (left selector: workspace dropdown + nav entries; middle page area; right AI column, collapsible)
- [x] 1.3 Base CSS (minimal utilitarian style) and shell JS (column collapse, page switching)
- [x] 1.4 KaTeX auto-render wired from `/static/` assets

## 2. Practice page

- [x] 2.1 Practice page pulls problems (weak or by kp selection) with session de-dup (exclude_ids)
- [x] 2.2 Problem card renders LaTeX, answer box for open problems, auto-grade display for option-bearing problems
- [x] 2.3 "Show answer" reveals solution as blocks; feedback box (1鈥?, note, stuck-step marker) appears with the reveal; skip allowed
- [x] 2.4 Recording: practice + feedback posts to existing endpoints; session array maintained in memory

## 3. Session-end unified self-rating

- [x] 3.1 Session-end view lists only problems without feedback, with rating controls and skip-all
- [x] 3.2 "Practice similar" single button pulls the same weak KP groups and starts a new round

## 4. AI column

- [x] 4.1 Priority context display (current + recent problems from problem_detail), display-only
- [x] 4.2 Explain/diagnose one-click with current problem + answer text + stuck marker; job polling; result rendering (four sections); new-session button
- [x] 4.3 Graceful no-provider message; recording unaffected

## 5. Knowledge point display page

- [x] 5.1 Markdown renderer: LaTeX, wiki links 鈫?kp page navigation, figures, tables, code blocks
- [x] 5.2 KP page shows body, linked problems, signals with cascade reasons, schedule state

## 6. Verification

- [x] 6.1 Backend tests stay green; add API tests if any endpoint was touched
- [x] 6.2 Walkthrough: serve on 3081, practice flow with real dmath data, session-end rating, practice similar, AI explain (graceful without provider), kp page wiki navigation
- [x] 6.3 openspec validate; small commits; archive the change

