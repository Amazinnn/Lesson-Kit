## ADDED Requirements

### Requirement: Time view inside the review page

The review page SHALL include an experimental time section: a month grid with
goal deadline cards and a 14-day due-workload bar curve, per the
daily-learning-plan calendar requirement. The section SHALL use the shared
visual tokens, mark heavy days, and keep its prefill action one click away
from the conversation input without sending anything.

#### Scenario: Review page shows the time section

- **WHEN** the learner opens the review page
- **THEN** the time section renders below the due overview with goals on
  their deadline dates and the 14-day curve

#### Scenario: Prefill the conversation

- **WHEN** the learner clicks the reallocation prefill on a heavy day
- **THEN** the Agent conversation input contains the reallocation request
  text and holds focus, and nothing is sent automatically
