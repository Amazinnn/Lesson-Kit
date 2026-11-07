## MODIFIED Requirements

### Requirement: Current page is an anchor rather than a forced turn target

The practice page SHALL identify the visible managed ordinary problem as its page anchor, and Lesson Kit SHALL use it only as a fallback turn focus. Explicit learner intent and continuation of the conversation SHALL take priority over any page-derived focus. Page navigation alone SHALL NOT cancel a conversational task. When the learner's message clearly and affirmatively refers to the immediately preceding problem or recent preceding problems, Lesson Kit SHALL resolve that reference against the ordered active practice before invoking the provider. A negated relative reference, a message that names a competing current problem, or simultaneous previous-and-recent references SHALL retain the page default and leave interpretation to the selected provider. The visible page anchor SHALL remain unchanged even when the turn focus is a preceding problem.

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

## ADDED Requirements
### Requirement: Recent exchanges support continuity rather than replace native history
Turns SHALL include the latest two completed successful exchanges available before the current turn, with original user and assistant text separately labelled as historical material. Native history SHALL remain enabled. Current message and task continuation SHALL override page defaults. A unique explicit proposal followed by affirmative shorthand SHALL be actionable within its original scope; multiple incompatible targets SHALL require clarification. Missing history SHALL not be fabricated.
#### Scenario: Confirm a flash-card proposal
- **WHEN** an Agent offers to save a specific flash card and the learner says yes
- **THEN** the next prompt conveys the offer and confirmation and instructs execution without redundant approval
#### Scenario: Change the page while continuing
- **WHEN** the learner changes page then refers to the preceding discussion
- **THEN** continuity takes priority over the page anchor, without inventing an intention to modify the newly visible item
