## 1. Visual shell (DSH tokens)

- [ ] 1.1 Rewrite `workbench.css` with DeepSeek Harness design tokens (bg-base, labels, brand #3964fe, borders, pill buttons, radii, shadow-lv3, top bar)
- [ ] 1.2 Top bar (workspace/course/chapter) + left navigation column (workspace dropdown, practice/knowledge points/knowledge graph entries, weak list)
- [ ] 1.3 Right AI conversation column restyled (context bar, action buttons, message list, input row)

## 2. Middle pages

- [ ] 2.1 Practice page as message stream (problem → answer → reveal+feedback box → next; no repeats in session)
- [ ] 2.2 Knowledge point list page (weak order, links to display pages)
- [ ] 2.3 Knowledge point display page (Markdown: math/wiki links/figures; signals with cascade reasons; linked problems)
- [ ] 2.4 Knowledge graph page (rendered artifact via `GET /api/w/{name}/graph`, or generation hint when missing)
- [ ] 2.5 Session-end unified self-rating (minimal: pending list + rating controls + skip-all + practice-similar)

## 3. AI column

- [ ] 3.1 Context follows current problem (display-only priority; agent access unaffected)
- [ ] 3.2 Explain/diagnose one-click, job polling, four-section result rendering, new conversation
- [ ] 3.3 Graceful no-provider message; recording unaffected

## 4. Verification

- [ ] 4.1 Route tests updated (left nav entries, kps list page, graph page, graph endpoint); backend tests stay green
- [ ] 4.2 Walkthrough: top bar, left nav (practice/kps/graph), practice message flow, session-end rating, practice-similar, AI column, kp list/detail, graph page, DSH visual consistency
- [ ] 4.3 openspec validate; small commits; archive the change
