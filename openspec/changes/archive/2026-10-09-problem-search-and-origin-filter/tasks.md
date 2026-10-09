# Tasks

All items are done in this change; the list is the record of what was touched.

## 1. Shared keyword rules (one definition, three readers)

- [x] 1.1 `workbench/domain/facets.py`: add `_TAGS`, `keyword_words`,
  `matches_all`, `stem_text`, `source_text`
- [x] 1.2 `workbench/data/queries.py`: import the rules; rewrite `search_problems`
  as `(pool, stem_q=None, source_q=None, limit=20)`; return `stem` in each hit
- [x] 1.3 `workbench/data/content.py`: `search` splits on whitespace and keeps
  only rows carrying every word

## 2. `origin_kind` becomes a dimension

- [x] 2.1 `pool_facets` returns a fourth dimension, same `[{value, count}]` shape
- [x] 2.2 `pull.select`: `origin_kind` → `origin_kinds` (set, any hit); the
  keyword groups join the `conditional` flag
- [x] 2.3 `pull.select`: `stem_keywords` / `source_keywords` filter the candidate
  list in the existing whole-table Python style
- [x] 2.4 `workbench/server/api.py`: pull body takes `origin_kinds` (string list)
  and `filters.origin_kinds`; both feed one `select` call

## 3. Routes and CLI

- [x] 3.1 `GET /search/problems` takes `stem` and `source`; `q` deleted
- [x] 3.2 `--origin-kind` → `--origin-kinds` (`action="append"`, same choices)
- [x] 3.3 `--search-stem` / `--search-source` added; `_compose_plan`,
  `_selection_given`, and the manifest's `request` record updated

## 4. Practice page

- [x] 4.1 `filterState` gains `origin_kinds`; storage key becomes
  `wb_practice_filters_v2_<ws>` (old key not read, not migrated)
- [x] 4.2 `filterDimension` renders the origin group as 历年原题 / 改编 / AI生成
- [x] 4.3 `applyFiltersToPullBody` sends `origin_kinds` with the other dimensions
- [x] 4.4 one search box → two (`#filter-search-stem`, `#filter-search-source`);
  `runSearch` sends one parameter per box; a result row shows the stem summary
  and the source line; the checkbox still names the problem for `include_ids`
- [x] 4.5 `workbench.css`: the two boxes share a row and wrap; a hit row is a
  full-width two-line block

## 5. Tests

- [x] 5.1 `tests/workbench/test_queries.py`: empty query, AND inside a domain,
  the domains stay separate, the `【…】` head rule, the limit
- [x] 5.2 `tests/workbench/test_facets.py`: the fourth dimension; keyword
  splitting; both domain texts
- [x] 5.3 `tests/workbench/test_pull.py`: `origin_kinds` keeps any named way;
  both keyword groups narrow, and intersect when both are given
- [x] 5.4 `tests/workbench/test_conversation_api.py`: search over `source`, the
  empty case, the `origin_kinds` dimension and top-level list, the 400
- [x] 5.5 `tests/workbench/workbench_ui_interactions.test.js`: the origin group
  renders in the learner's words; the pull body carries `origin_kinds`; the two
  boxes send one parameter each; a hit row shows both lines and picks by id;
  two empty boxes clear instead of listing

## 6. Docs

- [x] 6.1 `docs/GLOSSARY.md` — 筛选维度 gains `origin_kinds`; 选题 pulls in the
  two keyword groups; a new entry for the two keyword domains
- [x] 6.2 `docs/PRODUCT-MANUAL.md` §2.4 pull flags and §2.4.1 the panel
- [x] 6.3 `docs/REQUIREMENTS.md` — the search endpoint's parameters, the
  dimensions, the pull flags
- [x] 6.4 `docs/ACTION-GRAPH.md` + `docs/action-graph/L2`–`L4`
- [x] 6.5 `docs/design/view-layer-design.md`
- [x] 6.6 `C:\Users\yanwei\.zcode\skills\pool-pipeline\SKILL.md` — pull and
  difficulty filtering, plus a 查询/筛选 CLI 用法 section
- [x] 6.7 `changelog/2026-10-06-problem-search-and-origin-filter.md`

## Not in this change

- Difficulty filtering in the practice panel (its own change;
  `docs/REQUIREMENTS.md` line 189)
- Reintroducing a single combined search parameter
- Migrating `wb_practice_filters_` state
- Any pool write, and any restart of the daemon on port 3081
