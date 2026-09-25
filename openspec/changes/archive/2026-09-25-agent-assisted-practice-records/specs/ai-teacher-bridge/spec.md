## ADDED Requirements

### Requirement: Learner-requested Agent attempt recording

The Agent MAY inspect accessible workspace material and use the public
`lesson-kit attempts` CLI to record or correct a problem attempt when the
learner requests that action. The Agent SHALL receive the focused practice
context and the CLI's structured result. Reading a page, a draft, an image, or
an existing attempt SHALL NOT itself write a learning record. The Bridge SHALL
NOT silently turn an ordinary conversation into an attempt or rating.

#### Scenario: Discuss a draft without recording

- **WHEN** the learner asks about the current solution without asking to record or grade it
- **THEN** the Agent can read the focused content but no attempt or feedback is added

#### Scenario: Record a photographed solution

- **WHEN** the learner asks the Agent to transcribe and grade local answer images
- **THEN** the Agent may read them with existing file tools and submit one checked attempt manifest through the CLI
