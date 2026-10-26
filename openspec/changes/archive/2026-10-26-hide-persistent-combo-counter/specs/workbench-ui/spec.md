## ADDED Requirements

### Requirement: Consecutive-correct feedback appears only at milestones

Paper and ordinary practice SHALL NOT display a persistent consecutive-correct number or flame badge beside questions. They SHALL keep counting confirmed consecutive objective correct answers within the current run. At each five-answer milestone, Paper SHALL show its pixel combo banner and ordinary practice SHALL show its existing shared combo banner. Non-milestone answers SHALL NOT reveal a streak number. Incorrect answers SHALL reset the streak according to existing verdict rules. This presentation change SHALL NOT create requests or learning records.

#### Scenario: Ordinary answers do not show a badge
- **WHEN** a learner opens a question or confirms one through four consecutive correct answers
- **THEN** no persistent streak number or flames occupy the question card

#### Scenario: Milestone keeps its banner
- **WHEN** a fifth consecutive objective correct answer is confirmed
- **THEN** one transient combo banner shows the milestone count and the next question has no persistent badge
