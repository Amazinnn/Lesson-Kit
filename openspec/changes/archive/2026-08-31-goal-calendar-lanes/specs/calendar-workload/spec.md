## MODIFIED Requirements

### Requirement: Calendar and workload view

The workbench SHALL offer an experimental, read-only time view on the practice
page, parallel to the study arrangement section (stacking below it on narrow
viewports): a month grid rendering each dated goal as a timeline lane from its
optional start date through its deadline. Goals without a start date SHALL
remain compatible and render as a one-day lane on their deadline. Overlapping
goals SHALL occupy parallel lanes and a goal crossing a week boundary SHALL be
split visually without becoming separate goals. Today SHALL remain highlighted.
The same view SHALL retain its 14-day bar curve of due schedule rows per day
(each direction counted as one item). Days whose count reaches twice the
nonzero daily average SHALL be marked as heavy, with one action that pre-fills
a reallocation request into the Agent conversation input without sending it.
The view SHALL NOT reschedule, write, or alter any learning data, and SHALL
render honest empty states when there is nothing scheduled.

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

#### Scenario: Heavy day with reallocation prefill

- **WHEN** a day's due count reaches the heavy threshold
- **THEN** the day is marked heavy and one click pre-fills the reallocation request into the conversation input without sending it

#### Scenario: Nothing scheduled

- **WHEN** there are no goals and no due rows in the visible window
- **THEN** the view shows one honest empty-state sentence and no controls

### Requirement: Goal lifecycle management

The practice page study-arrangement region SHALL manage the full goal
lifecycle: creating goals, editing an existing goal's title / kind / optional
start date / deadline / description through the same form, and deleting a goal
behind an explicit confirmation. Edits and deletions SHALL take effect on the
goal cards and calendar immediately. Goal ids SHALL NOT be shown as primary
text. The calendar-and-workload view itself stays read-only.

#### Scenario: Edit a goal period in place

- **WHEN** the learner edits a goal with a start date and deadline
- **THEN** both dates load into the shared form and the saved period appears on the timeline after refresh

#### Scenario: Edit a goal in place

- **WHEN** the learner opens a goal card's edit action and the form loads with that goal's current fields
- **THEN** saving submits exactly the changed goal, and the card and month timeline reflect the update without a full page rebuild

#### Scenario: Delete with confirmation

- **WHEN** the learner activates a goal card's delete action and confirms
- **THEN** the goal is removed and disappears from the cards and the calendar; declining the confirmation leaves everything unchanged

#### Scenario: Cancel an edit

- **WHEN** the learner cancels a loaded edit
- **THEN** the form returns to its empty creation state
