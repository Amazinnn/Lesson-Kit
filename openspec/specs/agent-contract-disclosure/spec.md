## Purpose

Keep ordinary tutoring turns focused on the learner's current question while preserving exact, discoverable operational contracts for the less-common actions an external Agent may need to perform.

## Requirements

### Requirement: Ordinary turns receive a small context map rather than the full operation manual

Every external-Agent turn SHALL receive the rebuilt Lesson Kit context, the learner message, the read/write boundary, and a compact map of available Lesson Kit capabilities. Detailed manifests and mutation schemas SHALL NOT need to be repeated in full on every ordinary tutoring turn.

The compact map SHALL tell the Agent how to discover the installed detailed contracts at runtime. Contract discovery SHALL work from a learner workspace without requiring access to the Lesson Kit source checkout.

#### Scenario: Ordinary tutoring question

- **WHEN** the learner asks a question that does not require a specialized mutation or composition contract
- **THEN** the provider receives the compact map and current Lesson Kit context without the complete detailed content/attempt/practice manuals

#### Scenario: Specialized action needs exact rules

- **WHEN** the Agent needs the exact contract for commands, attempts, practice composition, UI actions, or managed content
- **THEN** it can load that contract on demand from the installed Lesson Kit runtime before performing the action

### Requirement: Read scope may expand proactively while writes remain intent-gated

The Agent SHALL be told that it may proactively read relevant Lesson Kit data without first asking the learner for permission. The page is a context anchor rather than a hard search boundary, and a resolved turn focus SHALL take precedence over the page anchor when deciding what the learner is asking about.

Lesson Kit mutations SHALL remain gated by explicit learner intent and the relevant operation contract.

#### Scenario: Question needs information outside the current page

- **WHEN** answering the learner requires another knowledge point, problem, recent practice, or historical learning record
- **THEN** the Agent may read the relevant Lesson Kit data and widen its search scope without asking for read permission

#### Scenario: Ordinary question does not request a write

- **WHEN** the learner is only asking for explanation or analysis
- **THEN** the Agent does not create learning attempts, ratings, or content mutations merely because write tools exist

### Requirement: Historical learner claims use understandable evidence

When the Agent makes a claim about the learner's past performance, recurring mistakes, weak areas, or progress, it SHALL ground that claim in actual Lesson Kit learning records. Learner-facing evidence SHALL use understandable study facts such as the problem/topic, the learner's relevant answer or result, and the practice time or situation when useful.

Internal ids, hashes, database keys, internal file names, and implementation-only paths SHALL NOT be used as the primary learner-facing evidence. The amount and strength of evidence SHALL match the strength of the claim; the Agent SHOULD summarize first and cite only a small number of representative examples.

#### Scenario: Repeated-error claim

- **WHEN** the Agent says the learner has repeatedly made a certain mistake
- **THEN** the claim is based on queried records and is supported with a concise aggregate plus representative, human-understandable examples rather than a list of opaque ids

#### Scenario: Evidence is sparse

- **WHEN** available records do not support a strong historical conclusion
- **THEN** the Agent weakens the conclusion or states that the records are insufficient instead of generalizing from one isolated event
