# Design notes

## The two domains, and why they are defined once

A problem row carries provenance in four places, and they answer different
questions:

| field | question |
|---|---|
| `display_title` / `problem_text` | what the problem **says** |
| `source_kind` | what **material** it came from (textbook / quiz / midterm / final / makeup / other) |
| `origin_kind` | how it was **produced** (历年原题 / 改编 / AI生成) |
| `exam_year` | which **sitting** |
| `source_evidence` | which **document** |

A learner recalling a problem reaches for the first group; a learner who knows
the paper they got it from reaches for the second. Matching them as one string
makes the second group's words match the first group's rows and vice versa, with
no way to tell why a row hit.

**The `【…】` run is the sixth place, and it is a real one.** `source_evidence`
and `exam_year` are nullable and postdate the populated pools: an imported
past-paper problem often carries its paper identity *only* as a leading tag run
on `problem_text`, e.g. `【2023期末·真题】【合集A】计算 1+2+3 的和`. Two rules
follow, and they pull in opposite directions:

- it belongs to the **source** domain, so a search for `合集A` finds it;
- it does **not** stop the tag run from being part of the **stem** text — the
  stem haystack is the whole `problem_text`, tags included. A stem search for
  `期末` therefore also reaches that row. This is accepted: the tags are
  characters of the problem's own text, and dropping them would mean rewriting
  the stored string.

The regex is anchored and only reads the head: `^\s*((?:【[^】]*】)+)`. A `【…】`
appearing mid-problem is body text and stays stem-only — that is what
`test_tags_only_count_at_the_head_of_the_text` pins.

**One definition, three readers.** `workbench/domain/facets.py` owns
`keyword_words`, `matches_all`, `stem_text`, `source_text`. `queries.search_problems`
and `pull.select` both call them; nothing re-lists the fields. The alternative —
a copy in each module — is exactly the drift that made the old single-haystack
search wrong in the first place. `data/content.py` uses the same two keyword
helpers for its generic whole-row search, so the "space-separated words, all of
them" rule is written once in the repository.

## Why AND inside a domain

The multi-value dimensions have always been OR-within / AND-across, and a
keyword *list* is the same shape: naming two words says "this and this", which
narrows. The old single-needle search could only widen (any substring) or match
nothing. With AND inside a domain, `期末 计数` means "an exam-paper problem about
counting" rather than the literal character sequence, and the learner does not
have to know which of the two words lives in which field.

`matches_all` short-circuits on the first missing word, so a pool scan costs
one `str.__contains__` per word in the common miss case.

## `origin_kind` → `origin_kinds`, and why no alias

Three of the four provenance axes already had a multi-value form
(`source_kinds`, `exam_years`, `evidence_docs`); `origin_kind` was the odd one
out, and it was the one axis the practice page could not offer as a checkbox
group because `GET /pull-facets` never listed it. A learner who wants "past
papers and adaptations, not AI-generated" has no way to say that with a scalar.

Zero compatibility is the deliberate call, consistent with this repository's
pre-release state:

- `pull.select(origin_kind=…)` → `origin_kinds` (a set, any hit);
- CLI `--origin-kind` → `--origin-kinds` (repeatable);
- pull API body `origin_kind` (single value) → `origin_kinds` (string list),
  unioned with `filters.origin_kinds` so the panel and an Agent can use either.

An alias would keep two spellings of one rule alive forever, and the old
spelling could not express the reason the change happened.

## The `q` parameter is deleted, not mapped

`GET /search/problems?q=` searched one haystack. `?stem=&source=` searches two.
Mapping `q` onto `stem` would silently change what a hit means — a caller
asking for `合集A` would start missing problems whose evidence holds it — and
mapping it onto both would return nothing. A request carrying only `q` now finds
nothing, which is the honest outcome: the parameter is not recognised.

## Two empty boxes mean nothing, not everything

`search_problems(pool)` with no parameters returns `{count: 0, problems: []}`.
The alternative — treating "no filter" as "no constraint" — would make a
malformed request (a dropped query string, a renamed parameter, a fetch that
lost its `?`) return the first 20 problems of the pool as if they were matches.
An empty result is the shape a learner can tell is wrong; a plausible-looking
list of 20 is not. The same rule is asserted on the panel side: clicking search
with both boxes empty clears the list.

## Storage key `v2`

The saved state is `{source_kinds, origin_kinds, exam_years, docs, picked}`.
The previous key holds the same object **without** `origin_kinds`, so a filter
state written before this change would load with `origin_kinds` undefined —
harmless in `applyFiltersToPullBody` (it guards on `.length`) but in
`filterActiveCount` it would throw. The key moves to
`wb_practice_filters_v2_<ws>`: the old key is not read and not migrated, and a
learner who reloads once re-clicks what they wanted. The alternative is a
`?? []` guard plus a migration nobody asked for, against a state a click
re-creates.

## Field names: `origin_kinds` everywhere, not `origin_kind`

`pool_facets` returns `source_kinds` / `exam_years` / `docs`, and those keys are
used verbatim as `filters` keys in the pull body. The fourth dimension is named
`origin_kinds` for the same reason: the dimension name *is* the wire key, and a
singular key in a bag of plurals would need a translation at every hop. The
values stay the stored enum (`source_problem`, `adapted_problem`,
`generated_grounded`) because they are read back out of the column unchanged;
only their **labels** are translated, in the browser.

## Result shape

Each hit carries `problem_id`, `title` (the display title, or the first 60
characters of the text — the label a picked problem is remembered by), `stem`
(the first 80 characters of the text with runs of whitespace collapsed) and
`source_evidence`. The panel renders the stem summary and the source line on
two rows, because a single line of "what matched" is the thing the old list
could not show. `stem` is truncated and whitespace-collapsed in the data layer
so the browser does not have to decide how a card-sized summary is cut.

## Coexistence with the uncommitted renderer change

`practice-flow.js` and `pages.py` also carry an unrelated uncommitted change
from another session (an option-block de-duplication in the practice card, and
math/markdown rendering in `pages.py`). Their hunks sit at
`practice-flow.js:377-509` and `:666`, and at `pages.py:736-1018`; this change
touches `practice-flow.js:1093-1237` and one `workbench.css` block. There is no
overlap, and nothing here reverts, stashes, or checks out the other work.

## Verification

```
python -m pytest tests -q          # 822 passed
node --test tests/workbench/*.test.js   # 127 passed
python -m compileall -q lessonkit.py workbench pipeline pool tests
```
