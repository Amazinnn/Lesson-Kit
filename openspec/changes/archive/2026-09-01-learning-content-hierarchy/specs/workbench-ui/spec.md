## ADDED Requirements

### Requirement: Learning content is the visual anchor

An active practice question and a knowledge-point body SHALL use the primary reading
rhythm of at least 17px text with generous line height. Each SHALL use one structural
accent edge and SHALL avoid decorative shadow emphasis. Controls and metadata SHALL
remain visually secondary.

#### Scenario: Active question

- **WHEN** a practice item is shown
- **THEN** the question text is the strongest surface and the answer composer follows
  as a distinct action area

#### Scenario: Knowledge body

- **WHEN** a knowledge point is opened
- **THEN** its prose forms the primary reading surface before reminders and related
  problems

### Requirement: Supporting learning surfaces remain quiet

Mode selection, revealed solutions, and related-problem navigation SHALL use secondary
backgrounds, text, or spacing. They SHALL NOT add another competing primary action or
change the current practice choreography.

#### Scenario: Reveal solution

- **WHEN** a learner reveals a solution
- **THEN** it appears attached beneath the question with secondary text styling

#### Scenario: Browse related problems

- **WHEN** a learner reaches the related-problem section
- **THEN** the section is separated from the knowledge body and topics remain compact
