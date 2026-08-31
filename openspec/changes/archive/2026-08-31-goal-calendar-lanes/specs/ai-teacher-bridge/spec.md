## MODIFIED Requirements

### Requirement: Goal-form assist action

When a learner explicitly starts a goal-form assistance turn, the Agent MAY
return a `prefill_goal_form` action containing a title, goal kind, optional
start date, optional deadline, and description. The server SHALL accept this
action only under goal intent, validate its bounded field contract, and return
the cleaned fields for in-place form population. The action SHALL NOT create or
update the goal until the learner submits the form. Ordinary conversation SHALL
NOT populate goal fields.

#### Scenario: Agent supplies a goal period

- **WHEN** a goal-assistance response contains valid `start_date` and `deadline` values
- **THEN** both values populate the visible goal form and remain subject to learner confirmation

#### Scenario: One-line goal request fills the form

- **WHEN** the learner submits a one-line goal description from the goal form and the agent's reply carries a valid `prefill_goal_form` action
- **THEN** the form fields fill in place with a notice that the agent filled them, and nothing is saved until the learner submits

#### Scenario: Ordinary conversation cannot fill the form

- **WHEN** a turn without goal intent contains an action-like block
- **THEN** no goal-form action is applied

#### Scenario: No provider or no active conversation

- **WHEN** the goal-assist control is used with no provider configured or no active conversation
- **THEN** the UI states honestly what is missing and every manual goal feature keeps working
