## ADDED Requirements

### Requirement: Explicit practice action

The Bridge MAY mirror a structured `replace_practice_selection` action only when
the request carries explicit practice intent. The action SHALL contain a
non-empty list of existing knowledge-point ids and SHALL be ignored for ordinary
conversation.

#### Scenario: Ordinary conversation
- **WHEN** a turn contains no explicit practice intent
- **THEN** any action-like text cannot change browser selection

#### Scenario: Explicit replacement
- **WHEN** a turn contains practice intent and valid knowledge-point ids
- **THEN** the client replaces the current selection exactly once

