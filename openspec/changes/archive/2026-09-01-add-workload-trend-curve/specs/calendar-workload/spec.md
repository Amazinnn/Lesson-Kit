## MODIFIED Requirements

### Requirement: Calendar and workload view

The workbench SHALL offer an experimental, read-only time view on the practice
page, parallel to the study arrangement section (stacking below it on narrow
viewports): a month grid rendering each dated goal as a timeline lane from its
optional start date through its deadline. Goals without a start date SHALL
remain compatible and render as a one-day lane on their deadline. Overlapping
goals SHALL occupy parallel lanes and a goal crossing a week boundary SHALL be
split visually without becoming separate goals. Today SHALL remain highlighted.
The same view SHALL retain its 14-day bars of exact due schedule-row counts per
day (each direction counted as one item) and SHALL overlay a smooth trend line
computed only from those 14 counts. The line SHALL communicate trend rather
than prediction, preserve the exact bar values, mark heavy days, expose a
readable chart label, and render no line when every count is zero. Days whose
count reaches twice the nonzero daily average SHALL be marked as heavy, with
one action that pre-fills a reallocation request into the Agent conversation
input without sending it. The view SHALL NOT reschedule, write, or alter any
learning data, and SHALL render honest empty states when there is nothing
scheduled.

#### Scenario: Overlapping goal periods

- **WHEN** two goals overlap on one or more visible dates
- **THEN** their time bars occupy separate parallel lanes and both titles remain identifiable

#### Scenario: Goals on one deadline

- **WHEN** two deadline-only goals share the same deadline date
- **THEN** both one-day lanes occupy separate tracks and remain independently readable

#### Scenario: Existing deadline-only goal

- **WHEN** a stored goal has a deadline but no start date
- **THEN** it remains readable as a one-day lane on its deadline without a migration step

#### Scenario: Goal crossing a week boundary

- **WHEN** a goal period extends across two calendar weeks
- **THEN** the calendar draws a segment in each week while preserving one goal identity

#### Scenario: Workload trend over exact bars

- **WHEN** one or more of the 14 days has due work
- **THEN** exact daily bars remain visible and a smooth, read-only trend line is drawn from the same counts with heavy days identifiable

#### Scenario: No workload to fit

- **WHEN** all 14 daily counts are zero
- **THEN** no trend line is drawn and the existing honest empty state remains available

#### Scenario: Heavy day with reallocation prefill

- **WHEN** a day's due count reaches the heavy threshold
- **THEN** the day is marked heavy and one click pre-fills the reallocation request into the conversation input without sending it

#### Scenario: Nothing scheduled

- **WHEN** there are no goals and no due rows in the visible window
- **THEN** the view shows one honest empty-state sentence and no controls
