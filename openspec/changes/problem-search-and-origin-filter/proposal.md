## Why

One search box, one haystack, and one value per filter dimension. Three defects
follow from that shape, all of them visible to a learner trying to find *one*
question they half-remember.

**A single `q` cannot separate "what the problem says" from "where it came
from".** `workbench/data/queries.py` joined `display_title`, `problem_text`,
`source_evidence` into one string and matched it as one substring. Typing `合集A` in the practice page's filter panel found a problem by
its evidence; typing `计数` found one by its text; there was no way to say "the
2023 finals *about* counting", and no way to keep a source word from matching a
stem word. Worse, the two answers were indistinguishable — a hit list cannot
tell you *why* a row matched.

**One word, not several.** The needle was a single `casefold().strip()` of the
whole query. `期末 计数` matched nothing unless that exact pair of characters
appeared in that order inside one field. The multi-value dimensions
(`source_kinds`, `exam_years`, `docs`) had been OR-within/AND-across for months;
the search box had not caught up.

**`origin_kind` was the one source axis with no way to ask for more than one.**
It is one of four recorded provenance fields — `source_kind` (what material),
`origin_kind` (how it was produced), `exam_year` (which sitting),
`source_evidence` (which document) — and the other three all had a multi-value
form. `origin_kind` alone was a single string in `pull.select`, a single-choice
CLI flag, and **absent from `GET /pull-facets` entirely**, so the practice page
could not offer it as a checkbox group the way it offers the other dimensions. A
learner who wants "past papers and adaptations, but not AI-generated" had no way
to say so.

**Where the older pools keep their source label.** `source_evidence` and
`exam_year` are optional and were added after the pools were populated: a
problem imported from a past paper often carries its paper identity *only* as a
leading `【…】` run on `problem_text` (`【2023期末·真题】【合集A】…`). Treating
`problem_text` as pure stem text makes that label unreachable from the source
side, and treating it as source text makes every problem match every word in its
own stem. The two domains have to be defined once and read by both the search
endpoint and the pull engine, or a problem ends up searchable by one rule and
filterable by another.

## What Changes

- **Two keyword domains, defined once.** `workbench/domain/facets.py` grows
  `stem_text` / `source_text` plus the two rules that consume them
  (`keyword_words`, `matches_all`). The stem domain is `display_title` +
  `problem_text`; the source domain is `source_evidence` +
  `exam_year` + the leading `【…】` run of `problem_text`
  (`^\s*((?:【[^】]*】)+)`). Both `queries.search_problems` and `pull.select` read
  these functions — there is no second copy of the field list.
- **Whitespace-separated words, AND inside a domain, AND across domains.**
  `search_problems(pool, stem_q=None, source_q=None, limit=20)` splits each
  parameter on whitespace, casefolds, and requires every word in that domain's
  text. Two empty parameters return `{count: 0, problems: []}` — a search with
  no words is not a request to list the pool.
- **`origin_kind` becomes `origin_kinds`, and joins the facet census.**
  `pool_facets` returns a fourth dimension in the same shape as the other three
  (`[{value, count}]`, most common first), and `pull.select` keeps a row when its
  `origin_kind` is any of the named ways.
- **`GET /search/problems` takes `stem` and `source`.** The `q` parameter is
  **deleted, not mapped**: a request carrying only `q` searches nothing. There is
  no alias and no deprecation path, because the old parameter's meaning (one
  haystack) is the thing being removed.
- **The practice page's panel grows a fourth checkbox group and a second search
  box.** The group renders as 历年原题 / 改编 / AI生成. The search row shows the
  stem summary and the source line per hit, and the checkbox still names the
  problem for `include_ids`.
- **The CLI reaches all of it.** `--origin-kind` becomes the repeatable
  `--origin-kinds`; `--search-stem` and `--search-source` carry the two keyword
  domains; `data search` splits its query into words and requires all of them.
- **The panel's saved state moves to `wb_practice_filters_v2_<ws>`.** The old key
  is not read and not migrated: the state it holds is keyed by the old dimension
  names, and translating it would be a compatibility path this change explicitly
  refuses.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-ui`: the filter panel's dimensions, its search box, and the
  search endpoint's parameters.
- `review-workbench`: the practice-pull engine's `origin_kinds` and its two
  keyword domains.

## Impact

- **Code**: `workbench/domain/facets.py` (shared rules + fourth dimension),
  `workbench/domain/pull.py` (`origin_kinds`, `stem_keywords`, `source_keywords`),
  `workbench/data/queries.py` (two-parameter search), `workbench/data/content.py`
  (`search` word AND), `workbench/server/api.py` (search params, pull body),
  `workbench/cli/main.py` (three flags), and the practice page's
  `practice-flow.js` / `workbench.css`.
- **Compatibility**: deliberately none. `q`, `--origin-kind`, the single-value
  `origin_kind` pull field, and the `wb_practice_filters_` storage key are all
  gone rather than translated.
- **Data**: none written. The pool schema is untouched; `origin_kinds` reads a
  column that already exists on every row.
- **Known cost, accepted**: a learner who reloads the page after this change
  loses the filter selections they had made under the old key. That is the price
  of not writing a migration for state that a click re-creates.
- **Shared file**: `practice-flow.js` and `pages.py` also carry an unrelated
  uncommitted renderer change from another session. This change edits only the
  filter block; those edits coexist by line range, and nothing here reverts them.
