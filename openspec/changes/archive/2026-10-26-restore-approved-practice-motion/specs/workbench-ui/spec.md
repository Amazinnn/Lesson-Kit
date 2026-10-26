## ADDED Requirements

### Requirement: Approved Combo appearance is frozen across practice flows

Paper and ordinary practice SHALL use one Combo presenter ported from the approved revision-7 webpage's A-variant component. Its warm-white rectangle, yellow left block, blue bottom strip, red corner square, original italic vector lettering, SVG paintbrush and entrance/writing/exit timeline SHALL match the preserved approved source at the same viewport and timestamp. Approved source extracts and keyframe comparison evidence SHALL be kept in the repository. Changes to this appearance SHALL require explicit learner approval. Existing five-correct milestones, no resting badge, motion preference and confirmed-event boundaries SHALL remain in effect.

#### Scenario: Both practice flows reach a milestone
- **WHEN** Paper or ordinary practice reaches a five-answer streak milestone
- **THEN** the same approved banner component appears with that milestone number

#### Scenario: Fifth answer save fails and is retried
- **WHEN** saving a fifth ordinary-practice answer fails and the same request is retried
- **THEN** the failed save does not count or celebrate, and its successful acknowledgement counts once in original answer order

### Requirement: Rounded pixel progress with radial comet-head pulses

The Paper pixel progress track SHALL keep its current 26px thickness and use rounded ends without a black outline. Its end head SHALL be a borderless square whose side equals the track thickness, composed of pixel blocks with a light ivory base. When a travelling density pulse reaches the head, its center SHALL light first, followed by outward pixel rings; the head SHALL return to its ivory base between arrivals. The head SHALL remain integrated with progress and track the actual filled endpoint. No filled pixel SHALL protrude beyond the head's right edge. Effective reduced motion SHALL show a stable base-colored head without flashing.

#### Scenario: Pulse reaches the head
- **WHEN** a density pulse arrives at the filled endpoint
- **THEN** the center brightens first, the bright front expands outward and the head returns to its dim state before the next pulse

## MODIFIED Requirements

### Requirement: Consecutive-correct feedback appears only at milestones

Paper and ordinary practice SHALL NOT display a persistent consecutive-correct number or flame badge beside questions. They SHALL keep counting confirmed consecutive objective correct answers within the current run. At each five-answer milestone, Paper and ordinary practice SHALL show the same approved shared Combo banner. Non-milestone answers SHALL NOT reveal a streak number. Incorrect answers SHALL reset the streak according to existing verdict rules. This presentation change SHALL NOT create requests or learning records.

#### Scenario: Ordinary answers do not show a badge
- **WHEN** a learner opens a question or confirms one through four consecutive correct answers
- **THEN** no persistent streak number or flames occupy the question card

#### Scenario: Milestone keeps its banner
- **WHEN** a fifth consecutive objective correct answer is confirmed
- **THEN** one transient combo banner shows the milestone count and the next question has no persistent badge
