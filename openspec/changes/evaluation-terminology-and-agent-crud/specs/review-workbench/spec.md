## MODIFIED Requirements

### Requirement: Flexible feedback

Feedback SHALL preserve a natural-language note and optional 1–5 learning
rating. A learner self-rating or a learner-requested Agent rating MAY record a
learning conclusion. A rating SHALL use the same signal and schedule rules,
independent of who submitted it. Navigation and unfinished work SHALL NOT
request or create a feedback log.

The same evaluation row MAY be edited by the learner in the browser or by the
Agent on the learner's request. Browser and CLI edits SHALL use the current
rating and note as expected values; a mismatch SHALL write nothing. Updating or
deleting an evaluation SHALL NOT replay signals, current states, progress, or
schedule. Hard deletion SHALL remove only the evaluation row and leave derived
projections as previously computed. `attempts correct` remains the whole-attempt
replacement path that withdraws and recomputes the linked effects.

#### Scenario: Rate mastery without text

- **WHEN** the learner submits a rating of 2 without a note
- **THEN** the corresponding knowledge-point signal is raised and one feedback event is appended

#### Scenario: Describe a weakness in words

- **WHEN** the learner submits a rating with a natural-language note about a confusion
- **THEN** the note is preserved verbatim, mapped through existing signal rules, and one event is appended

#### Scenario: Skip feedback entirely

- **WHEN** the learner leaves a problem without submitting a rating or requesting Agent recording
- **THEN** the session continues without a new feedback, attempt, signal, progress, or schedule write

#### Scenario: Describe a weakness with a submitted rating

- **WHEN** the learner submits a rating and a natural-language note
- **THEN** the note is preserved verbatim and mapped through the existing signal rules

#### Scenario: The learner and the Agent edit the same row

- **WHEN** the Agent edits or deletes an evaluation the learner first saved in the browser
- **THEN** the browser and CLI target the same evaluation row, and the expected rating and note prevent either side from silently overwriting a newer value

#### Scenario: Stale evaluation write is refused

- **WHEN** an update or delete carries expected values that no longer match the row
- **THEN** the write is refused with zero changes and the caller must read the evaluation again

#### Scenario: Editing a score does not replay mastery

- **WHEN** an existing evaluation's rating is changed without replacing its attempt
- **THEN** the evaluation row changes while the previously derived learner state, signals, progress, and schedule remain as computed
