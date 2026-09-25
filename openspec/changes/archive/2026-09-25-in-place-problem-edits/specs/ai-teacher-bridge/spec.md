## ADDED Requirements

### Requirement: Explicit in-place problem edit action

The bridge SHALL accept one more governed manifest shape, `problem-patch`, whose
items name existing problems and the attributes to change, and SHALL apply it
through the same prevalidation, backup, transaction, batch id, and
previous-value snapshot as the other content actions. It SHALL be treated as an
edit rather than an append: the bridge SHALL execute it only when the learner
explicitly asks to change existing content, and never because a conversation
merely discussed a change. The next-turn context SHALL report the applied patch
batch and its counts, including how many difficulty ratings the patch cleared,
and the contract SHALL tell the Agent that an in-place patch preserves the id and
every learning record, that a patch batch can be rolled back value for value, and
that options may be lifted verbatim out of a problem's old text instead of
re-importing the problem.

#### Scenario: An explicitly requested conversion runs

- **WHEN** the learner asks to turn named problems into 判断/小测 items and the Agent returns a valid `problem-patch` manifest
- **THEN** those rows change in place under one batch id, and the Agent's next turn sees the batch and counts

#### Scenario: A patch is not automatic

- **WHEN** a reply carries a `problem-patch` manifest that the learner did not ask for
- **THEN** the content boundary's explicit-instruction rule still governs, and ordinary conversation never edits existing content

#### Scenario: The Agent is told what a patch preserves

- **WHEN** a content prompt is composed for an active workspace
- **THEN** it states that in-place patching keeps the problem id and learning records, that the batch can be rolled back, and that splitting options out of an old stem is preferred over deleting and re-importing
