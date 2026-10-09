## MODIFIED Requirements

### Requirement: Provenance-filtered problem pull

Problem pull SHALL accept `source_kind`, a derived mutually exclusive
`source_group`, and `origin_kinds` as a list of the ways a row may have been
produced (`source_problem`, `adapted_problem`, `generated_grounded`); a row is
kept when its `origin_kind` is **any** of the named ways. `ai_generated`
contains generated origin; `exam` contains non-generated
quiz/midterm/final/makeup sources; `textbook` contains non-generated textbook
sources; all remaining rows are `other`. Multiple filters intersect. Pull MAY
also filter by `exam_year`, matched as a prefix so that a value such as `2023`
selects every problem whose recorded year starts with it.

Pull SHALL additionally accept two keyword groups, `stem_keywords` and
`source_keywords`. Each group splits its input on whitespace, casefolds, and
keeps only rows carrying **every** one of its words in that domain's own text.
The two domains SHALL be defined once and read by every surface: the **stem**
domain is `display_title` + `problem_text`; the **source**
domain is `source_evidence` + `exam_year` + the leading run of `【…】` tags at
the head of `problem_text` (`^\s*((?:【[^】]*】)+)`), which is where pools
imported before the provenance fields existed still keep their source label.
When both groups carry words, the groups intersect. The single-value
`origin_kind` parameter SHALL NOT remain: a caller that cannot express more
than one way would be the only way this axis is used.

#### Scenario: AI exam-grounded problem stays in AI group

- **WHEN** a generated problem is grounded in final-exam material
- **THEN** the AI group includes it and the exam convenience group does not

#### Scenario: Combine source axes

- **WHEN** pull requests textbook material and adapted origin
- **THEN** only rows satisfying both values are returned

#### Scenario: More than one origin at a time

- **WHEN** pull names `source_problem` and `adapted_problem`
- **THEN** rows of both origins are returned and generated rows are not

#### Scenario: Select one exam year

- **WHEN** a pull carries an exam year
- **THEN** only problems whose recorded year starts with that value are returned

#### Scenario: Several stem words narrow together

- **WHEN** the stem group carries two words and only one problem carries both
- **THEN** that problem alone is returned

#### Scenario: A source label carried only in the 【…】 prefix

- **WHEN** a problem's `source_evidence` and `exam_year` are empty and its
  `problem_text` opens with `【2023期末】【合集A】`
- **THEN** a source keyword naming either tag selects it, and the tags are not
  read as source text anywhere but at the head of the text

### Requirement: Multi-dimension source filters

Problem selection SHALL accept list-valued source dimensions alongside the
single-value ones: `source_kinds` (exact), `exam_years` (prefix),
`evidence_docs` (case-insensitive substring over the free-text source
evidence), and `origin_kinds` (any of the named production ways). Within one
dimension the values SHALL union; across dimensions they SHALL intersect. The
system SHALL derive each dimension's offered values from the pool's actual rows
with row counts, folding source evidence into one document key per source
document (an `.md`-style path verbatim, textbook rows into 教材, otherwise the
leading segment), and SHALL expose that census as a read-only endpoint plus
repeatable CLI flags (`--source-kind`, `--origin-kinds`, the new
`--source-evidence`). The pull API SHALL also accept `exam_year`, which it
previously ignored. The generic content search SHALL split its query on
whitespace and keep only rows carrying every one of its words.

#### Scenario: Dimensions union within and intersect across

- **WHEN** a selection names two source kinds of which one matches nothing, and an exam year
- **THEN** the rows matching the other kind and the year are returned, and rows matching the year but a different kind are not

#### Scenario: Evidence matching is fragment-friendly

- **WHEN** an evidence filter names a distinctive fragment of a document's name in any letter case
- **THEN** every row whose evidence contains that fragment is selected, whichever pool format wrote it

#### Scenario: Facets come from the pool

- **WHEN** the filter dimensions are requested
- **THEN** every offered value exists on at least one row, carries its row count, and one value per source document is offered

#### Scenario: Origin is a dimension like the others

- **WHEN** the filter dimensions are requested
- **THEN** the response carries a fourth dimension listing each production way
  present in the pool with its row count, in the same shape as the other three

#### Scenario: A content search with several words

- **WHEN** a content search is given two words and only one row carries both
- **THEN** that row alone is returned

### Requirement: Source filter panel on the practice page

The practice page SHALL offer a filter panel, opened from a launch button and
rendered as a floating panel: one checkbox group per filter dimension (values
and counts derived from the pool), two search boxes — one for the **stem**
domain and one for the **source** domain — that find problems and let the
learner pick them into the selection, and a clear-all action. The origin
dimension SHALL be labelled in the learner's words: 历年原题, 改编, AI生成. Each
search box SHALL accept several whitespace-separated words, every word of which
must be found in that box's own domain, and a result row SHALL show the stem
summary together with its source line. Active filter selections SHALL persist
per workspace for the session under a versioned storage key, the launch button
SHALL show the active count, and the next pull SHALL combine the dimensions (and
the picked problems) with the existing scope and mode. The search endpoint SHALL
take one query parameter per domain and SHALL NOT accept a single combined
parameter: there is no alias for the retired one, because its meaning — one
haystack — is what the two domains replace. A search with no word in either box
SHALL return nothing rather than list the pool.

#### Scenario: Dimensions and picked problems reach the pull

- **WHEN** the learner ticks a document, a year, an origin, and picks two problems from the search results, then starts a round
- **THEN** the pull request carries those dimensions — including the origin — and the picked problem ids, and the returned items all match

#### Scenario: Two boxes, two domains

- **WHEN** the learner types a word in the stem box and another in the source box and searches
- **THEN** the request carries one parameter per box, and a problem matching only one of the two words is not returned

#### Scenario: Filters persist and clear

- **WHEN** the learner reloads the page with filters active and later presses clear-all
- **THEN** the badge and the panel restore exactly, and the cleared state sends no filter dimensions
