## ADDED Requirements

### Requirement: Durable attempt records for every surface

Every submitted answer SHALL become a durable, append-only attempt row regardless
of the surface that produced it — the browser practice flow, the CLI, or an
Agent manifest. A browser-submitted attempt SHALL store the answer text, the
chosen option texts when the item has options, and the objective verdict when
the item carries a usable answer key; a comprehensive answer SHALL store its
text with no verdict. An attempt row alone SHALL NOT move progress, schedule,
signals, or current state; those still move only through the rating flow, which
SHALL link its event back to the attempt (`attempt_id`) after validating that
the attempt belongs to the rated item. A pool that predates the columns SHALL
still accept the attempt (degraded, without verdict or choices) instead of
failing the practice flow.

#### Scenario: A browser answer is durable

- **WHEN** the student submits an answer on the practice page
- **THEN** one attempt row persists the answer text, the chosen options, and the objective verdict, and no learning projection changes until the rating lands

#### Scenario: The rating links back

- **WHEN** the session's rating is recorded for an item that submitted an attempt
- **THEN** the feedback event carries that attempt's id, and the attempt reads back with its rating

#### Scenario: A mismatched attempt id is refused

- **WHEN** a rating names an attempt that belongs to another item
- **THEN** the rating is refused with zero writes

### Requirement: Practice history is readable in the product

The workbench SHALL surface the practice history to the learner: a server-
rendered records view in the navigation listing recent attempts newest first —
problem link, verdict badge, rating, note, answer excerpt, time — filterable by
problem; and the practice reveal SHALL render the problem's past attempts (with
their linked ratings) from the already-served problem payload.

#### Scenario: The records view lists the history

- **WHEN** the learner opens the records view
- **THEN** recent attempts appear newest first with verdict and rating, and one problem's history can be isolated

#### Scenario: The reveal shows past attempts

- **WHEN** the student reveals a solution for a problem attempted before
- **THEN** the past attempts (bounded to the latest few) render with their verdicts and ratings

### Requirement: Multi-dimension source filters

Problem selection SHALL accept list-valued source dimensions alongside the
single-value ones: `source_kinds` (exact), `exam_years` (prefix), and
`evidence_docs` (case-insensitive substring over the free-text source
evidence). Within one dimension the values SHALL union; across dimensions they
SHALL intersect. The system SHALL derive each dimension's offered values from
the pool's actual rows with row counts, folding source evidence into one
document key per source document (an `.md`-style path verbatim, textbook rows
into 教材, otherwise the leading segment), and SHALL expose that census as a
read-only endpoint plus repeatable CLI flags (`--source-kind`, the new
`--source-evidence`). The pull API SHALL also accept `exam_year`, which it
previously ignored.

#### Scenario: Dimensions union within and intersect across

- **WHEN** a selection names two source kinds of which one matches nothing, and an exam year
- **THEN** the rows matching the other kind and the year are returned, and rows matching the year but a different kind are not

#### Scenario: Evidence matching is fragment-friendly

- **WHEN** an evidence filter names a distinctive fragment of a document's name in any letter case
- **THEN** every row whose evidence contains that fragment is selected, whichever pool format wrote it

#### Scenario: Facets come from the pool

- **WHEN** the filter dimensions are requested
- **THEN** every offered value exists on at least one row, carries its row count, and one value per source document is offered

### Requirement: Source filter panel on the practice page

The practice page SHALL offer a filter panel, opened from a launch button and
rendered as a floating panel: one checkbox group per filter dimension (values
and counts derived from the pool), a search box that finds problems by their
text, title, label, or evidence and lets the learner pick them into the
selection, and a clear-all action. Active filter selections SHALL persist per
workspace for the session, the launch button SHALL show the active count, and
the next pull SHALL combine the dimensions (and the picked problems) with the
existing scope and mode.

#### Scenario: Dimensions and picked problems reach the pull

- **WHEN** the learner ticks a document, a year, and picks two problems from the search results, then starts a round
- **THEN** the pull request carries those dimensions and the picked problem ids, and the returned items all match

#### Scenario: Filters persist and clear

- **WHEN** the learner reloads the page with filters active and later presses clear-all
- **THEN** the badge and the panel restore exactly, and the cleared state sends no filter dimensions
