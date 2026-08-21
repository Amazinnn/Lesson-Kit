## 1. Visual shell (DSH tokens)

- [x] 1.1 Rewrite `workbench.css` with DeepSeek Harness design tokens (bg-base, labels, brand #3964fe, borders, pill buttons, radii, shadow-lv3, top bar)
- [x] 1.2 Top bar (workspace/course/chapter) + left navigation column (workspace dropdown, practice/knowledge points/knowledge graph entries, weak list)
- [x] 1.3 Right AI conversation column restyled (context bar, action buttons, message list, input row)

## 2. Middle pages

- [x] 2.1 Practice page as message stream (problem 鈫?answer 鈫?reveal+feedback box 鈫?next; no repeats in session)
- [x] 2.2 Knowledge point list page (weak order, links to display pages)
- [x] 2.3 Knowledge point display page (Markdown: math/wiki links/figures; signals with cascade reasons; linked problems)
- [x] 2.4 Knowledge graph page (rendered artifact via `GET /api/w/{name}/graph`, or generation hint when missing)
- [x] 2.5 Session-end unified self-rating (minimal: pending list + rating controls + skip-all + practice-similar)

## 3. AI column

- [x] 3.1 Context follows current problem (display-only priority; agent access unaffected)
- [x] 3.2 Explain/diagnose one-click, job polling, four-section result rendering, new conversation
- [x] 3.3 Graceful no-provider message; recording unaffected

## 4. Verification

- [x] 4.1 Route tests updated (left nav entries, kps list page, graph page, graph endpoint); backend tests stay green
- [x] 4.2 Walkthrough: top bar, left nav (practice/kps/graph), practice message flow, session-end rating, practice-similar, AI column, kp list/detail, graph page, DSH visual consistency
- [x] 4.3 openspec validate; small commits; archive the change

