## Purpose

Agent turns receive a small server-rebuilt view of the learner's immediate study context so the provider can follow what the learner is actually referring to without loading an entire practice or trusting browser-authored learning facts. The practice page anchor identifies the visible managed problem; the turn focus identifies the problem or problems selected for this message; the recent practice working set supplies bounded evidence from the same active practice.

## Requirements

### Requirement: Current page is an anchor rather than a forced turn target

The practice page SHALL identify the visible managed ordinary problem as its page anchor, and Lesson Kit SHALL use it as the default turn focus. When the learner's message clearly and affirmatively refers to the immediately preceding problem or recent preceding problems, Lesson Kit SHALL resolve that reference against the ordered active practice before invoking the provider. A negated relative reference, a message that names a competing current problem, or simultaneous previous-and-recent references SHALL retain the page default and leave interpretation to the selected provider. The visible page anchor SHALL remain unchanged even when the turn focus is a preceding problem.

When the visible browser id does not resolve to a managed ordinary problem, Lesson Kit SHALL NOT construct a problem turn focus from that id.

Lesson Kit SHALL NOT introduce a second semantic Agent for this resolution. Ambiguous references SHALL remain for the selected provider to interpret from the bounded context it receives.

#### Scenario: Ask about the previous problem

- **WHEN** the learner is viewing a practice problem and asks about “上一题” or an equivalent unambiguous reference
- **THEN** the context identifies the immediately preceding settled ordinary problem as the turn target while preserving the visible problem as the page anchor

#### Scenario: Negative learning state still refers to a previous problem

- **WHEN** the learner is viewing a practice problem and says “上一题我不会做” or “上一题为什么做不出来”
- **THEN** the immediately preceding settled ordinary problem remains the turn focus

#### Scenario: Reject or compare a relative target

- **WHEN** the learner says “不是上一题，是这题”, “不要解释上一题，只解释当前这题”, “前几题不用管，只讲这题”, or “上一题和这题有什么区别”
- **THEN** the visible problem remains the turn focus and the bounded recent context remains available to the provider

#### Scenario: Recent reference describes difficulty

- **WHEN** the learner is viewing a practice problem and says “前几题我都没理解”
- **THEN** the available preceding settled ordinary problems remain the turn focus

#### Scenario: Ask an ordinary question about the visible problem

- **WHEN** the learner's message does not clearly refer to another practice problem
- **THEN** the visible problem remains the default turn target

### Requirement: Practice turns carry bounded recent settled problem context

A practice-page Agent turn SHALL include the visible ordinary problem plus at most four preceding settled ordinary problems from the same active practice. Preceding problems SHALL be selected by practice order, not by database timestamp. Flash cards SHALL NOT occupy these preceding-problem slots.

For each included preceding problem, Lesson Kit SHALL rebuild the durable problem content from the Pool and include the settled attempt and feedback when they exist. The active-practice summary MAY remain more compact than these included problems, and Lesson Kit SHALL NOT expand the whole active practice merely to provide recent context.

#### Scenario: Five or more problems precede the visible problem

- **WHEN** at least five settled ordinary problems precede the visible problem in the active practice
- **THEN** only the four nearest settled ordinary problems are expanded together with the visible problem

#### Scenario: Visible managed problem is outside the active practice

- **WHEN** the visible managed problem is not an item in the active practice
- **THEN** the context includes that problem as the page anchor without borrowing preceding items from the active practice cursor

#### Scenario: Previous problem has a recorded answer

- **WHEN** an included preceding problem is linked to a recorded attempt
- **THEN** its context includes the managed problem content and available recorded answer/result evidence instead of only the problem id

### Requirement: Browser identifiers never become learning facts

The browser MAY send the id of the visible practice item, the learner's current message, and an explicitly attached unsent draft. Lesson Kit SHALL use that id as a problem reference only when it resolves to a managed ordinary problem, and SHALL rebuild problem content, active-practice order, settled state, attempts, and feedback from managed server state. Browser DOM text SHALL NOT become an authoritative learning fact.

#### Scenario: Browser identifies a managed problem

- **WHEN** a practice Agent turn names a visible managed problem
- **THEN** Lesson Kit resolves its content and surrounding practice evidence from the Pool and active practice rather than copying browser-authored problem facts

#### Scenario: Browser id is unknown or identifies a flash card

- **WHEN** a practice Agent turn supplies an id that does not resolve to a managed ordinary problem
- **THEN** the id is not presented as a problem focus and the active practice cursor does not supply preceding problem context

### Requirement: Reading immediate practice context has no learning side effect

Building the bounded practice context, including resolving a previous-problem reference, SHALL NOT move the active-practice cursor, create or edit attempts, create feedback, or change learning state or schedules.

#### Scenario: Ask about an already answered previous problem

- **WHEN** the learner asks the Agent to explain a preceding answered problem
- **THEN** the same active-practice cursor, attempts, feedback, and learning state remain after context construction
