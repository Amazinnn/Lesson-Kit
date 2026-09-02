## MODIFIED Requirements

### Requirement: Calendar and workload view

The workbench SHALL offer an experimental, read-only time view on the practice
page, within the study arrangement region rendered below the daily plan as a
full-width block. Its month grid SHALL use quiet structural lines and render
each dated goal as a thin timeline track from its optional start date through
its deadline. Goals without a start date SHALL remain compatible and render as
a one-day track on their deadline. Overlapping goals SHALL occupy compact
parallel lanes. A goal crossing a week boundary SHALL be split visually without
becoming separate goals, SHALL show its title only once in its first suitable
visible segment, and SHALL expose its identity and full date range on every segment.
Today SHALL emphasize the date numeral rather than the whole cell.

Below the calendar, the same view SHALL render 14 days of exact due schedule-row
counts (each direction counted as one item) under the title “未来 14 天复习负荷”.
It SHALL explain the measure, summarize the total, peak date/count, and overdue
count, align every date on one fixed axis, place each nonzero exact value above
its bar, and render zero as no bar. The peak SHALL be visually distinct. Days
whose count reaches twice the nonzero daily average SHALL additionally be
marked as heavy, with one action that pre-fills a reallocation request into the
Agent conversation input without sending it. The chart SHALL NOT overlay a
smoothed or predictive line. The view SHALL NOT reschedule, write, or alter any
learning data, and SHALL render honest empty states when there is nothing
scheduled.

#### Scenario: Overlapping goal periods

- **WHEN** two goals overlap on one or more visible dates
- **THEN** their thin tracks occupy separate parallel lanes and both titles remain identifiable

#### Scenario: Goals on one deadline

- **WHEN** two deadline-only goals share the same deadline date
- **THEN** both one-day tracks occupy separate lanes and remain independently readable

#### Scenario: Existing deadline-only goal

- **WHEN** a stored goal has a deadline but no start date
- **THEN** it remains readable as a one-day track on its deadline without a migration step

#### Scenario: Goal crossing a week boundary

- **WHEN** a goal period extends across two or more calendar weeks
- **THEN** the calendar draws a continued segment in each week, renders the title once in the first suitable visible segment, and preserves one accessible goal identity throughout

#### Scenario: Exact workload on a fixed axis

- **WHEN** one or more of the 14 days has due work
- **THEN** exact daily values appear above bars whose dates share one fixed baseline, with total and peak summaries and no smoothed line

#### Scenario: Zero workload day

- **WHEN** a day has no due rows
- **THEN** its date remains on the shared axis without a fake minimum-height bar or value label

#### Scenario: Heavy day with reallocation prefill

- **WHEN** a day's due count reaches the heavy threshold
- **THEN** the day receives the heavy marker and one click pre-fills the reallocation request into the conversation input without sending it

#### Scenario: Nothing scheduled

- **WHEN** there are no goals and no due rows in the visible window
- **THEN** the view shows one honest empty-state sentence and no controls
