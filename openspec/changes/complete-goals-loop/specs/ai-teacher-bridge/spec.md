## ADDED Requirements

### Requirement: Goal-form assist action

The bridge MAY mirror a second structured action, `prefill_goal_form`, only
when the request carries explicit goal intent (a goal-assist request from the
goal form). The action SHALL carry at most the fields title, kind, deadline,
and description, validated server-side against the goal contract; invalid or
missing fields SHALL be dropped, and an action without a usable title SHALL
be discarded entirely. The client SHALL apply the action in place by filling
the goal form — submission remains an explicit human action. Ordinary
conversation SHALL NOT fill the goal form, and no goal is ever created or
modified by the action itself.

#### Scenario: One-line goal request fills the form

- **WHEN** the learner submits a one-line goal description from the goal form
  and the agent's reply carries a valid `prefill_goal_form` action
- **THEN** the form fields fill in place with a notice that the agent filled
  them, and nothing is saved until the learner submits

#### Scenario: Ordinary conversation cannot fill the form

- **WHEN** a turn without goal intent contains an action-like block
- **THEN** no goal-form action is applied

#### Scenario: No provider or no active conversation

- **WHEN** the goal-assist control is used with no provider configured or no
  active conversation
- **THEN** the UI states honestly what is missing and every manual goal
  feature keeps working
