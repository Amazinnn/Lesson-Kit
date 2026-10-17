## ADDED Requirements

### Requirement: Paper items render from their own answering content
A Paper containing choice, judgment and open problems SHALL render each from its own validated content payload, including after an identity-preserving type correction. A legacy whole-run `practice_mode` SHALL NOT replace objective controls with a free-text form. Objective auto-grading SHALL use a valid supplied key; an absent key SHALL be shown as unknown and SHALL NOT produce a fabricated verdict. Existing rating-timing rules SHALL remain independent of item rendering.

#### Scenario: Resume a mixed Paper originally started as exam
- **WHEN** an unfinished Paper with legacy mode `exam` contains valid choice, judgment and open items
- **THEN** each shows its own appropriate answering controls and the Paper identity/order and unaffected item progress remain unchanged

#### Scenario: Correct an open item to choice in place
- **WHEN** a question is corrected to a validated choice payload under its original ID
- **THEN** its unfinished occurrence becomes pending with choice controls, without recreating the question or its containing Paper
