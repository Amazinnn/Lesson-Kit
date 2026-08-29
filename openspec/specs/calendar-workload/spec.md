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

