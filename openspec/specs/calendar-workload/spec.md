# calendar-workload Specification

## Purpose

An experimental, read-only time view inside the review page: goals placed on
a month grid by deadline and a 14-day histogram of due work, so overload is
visible before it is felt. The view writes nothing and reschedules nothing;
a heavy day offers a pre-filled reallocation request for the Agent instead
of automatic replanning.
## Requirements
### Requirement: Calendar and workload view

The workbench SHALL offer an experimental, read-only time view on the practice
page, parallel to the study arrangement section (stacking below it on narrow
viewports): a month grid placing goals on their deadline dates (multiple goals
per day stack, never merged), today highlighted, and a 14-day bar curve of due
schedule rows per day (each direction counted as one item). Days whose count
reaches twice the nonzero daily average SHALL be marked as heavy, with one
action that pre-fills a reallocation request into the Agent conversation input
without sending it. The view SHALL NOT reschedule, write, or alter any
learning data, and SHALL render honest empty states when there is nothing
scheduled.

#### Scenario: Goals on one deadline

- **WHEN** two goals share the same deadline date
- **THEN** both goal cards stack in that day's cell and remain independently
  readable

#### Scenario: Heavy day with reallocation prefill

- **WHEN** a day's due count reaches the heavy threshold
- **THEN** the day is marked heavy and one click pre-fills the reallocation
  request into the conversation input without sending it

#### Scenario: Nothing scheduled

- **WHEN** there are no goals and no due rows in the visible window
- **THEN** the view shows one honest empty-state sentence and no controls

### Requirement: Goal lifecycle management

The practice page study-arrangement region SHALL manage the full goal
lifecycle: creating goals (existing flow unchanged), editing an existing
goal's title / kind / deadline / description through the same form
(pre-filled, submitted as an update), and deleting a goal behind an explicit
confirmation. Edits and deletions SHALL take effect on the goal cards and
calendar immediately. Goal ids SHALL NOT be shown as primary text. The
calendar-and-workload view itself stays read-only.

#### Scenario: Edit a goal in place

- **WHEN** the learner opens a goal card's edit action and the form loads
  with that goal's current fields
- **THEN** saving submits exactly the changed goal, and the card and month
  grid reflect the update without a full page rebuild

#### Scenario: Delete with confirmation

- **WHEN** the learner activates a goal card's delete action and confirms
- **THEN** the goal is removed and disappears from the cards and the calendar;
  declining the confirmation leaves everything unchanged

#### Scenario: Cancel an edit

- **WHEN** the learner cancels a loaded edit
- **THEN** the form returns to its empty creation state

