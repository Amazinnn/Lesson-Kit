# problem-search-and-origin-filter

Two keyword domains instead of one haystack, and `origin_kind` promoted from a
scalar to a filter dimension.

| file | what it holds |
|---|---|
| `proposal.md` | Why one search box and one value per axis were wrong, and what replaces them |
| `design.md` | The two domain definitions, the `【…】` rule, the zero-compatibility calls, coexistence with the uncommitted renderer work |
| `tasks.md` | What was touched |
| `specs/review-workbench/spec.md` | The three modified requirements |

## What it is

A search box that cannot say *which* thing you remember, and a filter panel
whose fourth source axis has no checkbox group. Both are fixed by splitting the
question in two:

- **题干关键词 / stem** — `display_title` + `problem_text`
- **来源关键词 / source** — `source_evidence` + `exam_year` + the leading `【…】`
  tag run of `problem_text`

Each box takes several whitespace-separated words and requires **all** of them
in its own domain; both boxes together intersect. The same two functions
(`facets.stem_text`, `facets.source_text`) are what the search endpoint, the
pull engine, and the panel read — there is no second copy of the field list.

`origin_kind` joins `source_kinds`, `exam_years` and `docs` as a real dimension:
the facet census reports it, the panel renders it as 历年原题 / 改编 / AI生成,
and `pull.select` keeps a row matching **any** of the named ways.

## The breaks, on purpose

`?q=`, `--origin-kind`, the single-value `origin_kind` pull field, and the
`wb_practice_filters_` storage key are deleted rather than translated. Each one
either cannot express the new meaning or is a state a click re-creates. See
`design.md` for why the `q` parameter is not mapped onto the stem domain — it
would silently change what a hit means.

## What is not here

Difficulty filtering in the practice panel, and any pool write.
