## ADDED Requirements

### Requirement: Practice-page one-click tasks

The practice page SHALL offer one-click explain (讲解) and diagnose (诊断)
task entries for the current problem item. A diagnose entry SHALL carry the
learner's own answer text for that item as task context and SHALL prompt the
learner to answer first when no answer exists. While a task runs its status
SHALL be visible in the practice UI; a validated result SHALL be rendered in
the practice UI in its contracted sections, and a failed task SHALL show its
failure reason. With no provider configured the entries SHALL be shown as
unavailable rather than broken, and every non-AI practice feature SHALL keep
working. Card items SHALL NOT offer these entries (they are keyed by problem
identity).

#### Scenario: Diagnose with the learner's own answer

- **WHEN** the learner answers a problem wrongly and starts a diagnose task
  from the practice page
- **THEN** the task context includes that answer text and the validated
  result renders with the 定位 / 提示 / 溯源 / 追问 sections in the practice UI

#### Scenario: Explain result shown inline

- **WHEN** an explain task started from the practice page passes contract
  validation
- **THEN** the result is rendered in the practice UI and remains retrievable
  again for the same problem

#### Scenario: Task fails

- **WHEN** a task started from the practice page fails contract validation or
  the provider errors
- **THEN** the practice UI shows the failure reason and the result is not
  shown as authoritative

#### Scenario: No provider configured

- **WHEN** no bridge provider is available and the learner opens the practice
  page
- **THEN** the explain and diagnose entries are visibly unavailable while all
  non-AI practice flows work unchanged
