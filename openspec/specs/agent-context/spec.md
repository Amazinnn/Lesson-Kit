## Purpose

Agent turns receive a small server-rebuilt view of the learner's immediate study context so the provider can follow what the learner is actually referring to without loading an entire practice or trusting browser-authored learning facts.

## Requirements

### Requirement: Current page is an anchor rather than a forced turn target

The practice page SHALL identify the problem currently visible to the learner, and Lesson Kit SHALL use that problem as the default turn target. When the learner's message contains an unambiguous relative reference to the immediately preceding problem or the recent preceding problems, Lesson Kit SHALL resolve that reference against the ordered active practice before invoking the provider. The visible page problem SHALL remain the context anchor even when the resolved turn target is a preceding problem.

Lesson Kit SHALL NOT introduce a second semantic Agent for this resolution. Ambiguous references SHALL remain for the selected provider to interpret from the bounded context it receives.

#### Scenario: Ask about the previous problem

- **WHEN** the learner is viewing a practice problem and asks about “上一题” or an equivalent unambiguous reference
- **THEN** the context identifies the immediately preceding settled ordinary problem as the turn target while preserving the visible problem as the page anchor

#### Scenario: Ask an ordinary question about the visible problem

- **WHEN** the learner's message does not clearly refer to another practice problem
- **THEN** the visible problem remains the default turn target

### Requirement: Practice turns carry bounded recent settled problem context

A practice-page Agent turn SHALL include the visible ordinary problem plus at most four preceding settled ordinary problems from the same active practice. Preceding problems SHALL be selected by practice order, not by database timestamp. Flash cards SHALL NOT occupy these preceding-problem slots.

For each included preceding problem, Lesson Kit SHALL rebuild the durable problem content from the Pool and include the settled attempt and feedback when they exist. The active-practice summary MAY remain more compact than these included problems, and Lesson Kit SHALL NOT expand the whole active practice merely to provide recent context.

#### Scenario: Five or more problems precede the visible problem

- **WHEN** at least five settled ordinary problems precede the visible problem in the active practice
- **THEN** only the four nearest settled ordinary problems are expanded together with the visible problem

#### Scenario: Previous problem has a recorded answer

- **WHEN** an included preceding problem is linked to a recorded attempt
- **THEN** its context includes the managed problem content and available recorded answer/result evidence instead of only the problem id

### Requirement: Browser identifiers never become learning facts

The browser MAY send the visible problem id, the learner's current message, and an explicitly attached unsent draft. Lesson Kit SHALL rebuild problem content, active-practice order, settled state, attempts, and feedback from managed server state. Browser DOM text SHALL NOT become an authoritative learning fact.

#### Scenario: Browser identifies a managed problem

- **WHEN** a practice Agent turn names a visible managed problem
- **THEN** Lesson Kit resolves its content and surrounding practice evidence from the Pool and active practice rather than copying browser-authored problem facts

### Requirement: Reading immediate practice context has no learning side effect

Building the bounded practice context, including resolving a previous-problem reference, SHALL NOT move the active-practice cursor, create or edit attempts, create feedback, or change learning state.

#### Scenario: Ask about an already answered previous problem

- **WHEN** the learner asks the Agent to explain a preceding answered problem
- **THEN** the same active-practice cursor, attempts, feedback, and learning state remain after context construction
