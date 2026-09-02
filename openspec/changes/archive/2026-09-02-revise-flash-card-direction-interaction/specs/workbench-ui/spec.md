## ADDED Requirements

### Requirement: Flash card stacked presentation

Every flash card in a session SHALL render as two fully overlapped card
faces: the prompt face on top and the other face completely hidden behind
it, with no edges visible before the reveal. Selecting Flash Card SHALL
offer exactly a forward or reverse session preference, forward by default,
chosen once before the first pull and fixed for the whole session. The
workbench SHALL NOT offer a direction switch during the session, and every
saved card rating SHALL carry the session direction. One explicit reveal
action SHALL disclose the hidden face: the top face SHALL drift a short
distance counterclockwise and settle, and the bottom face SHALL drift a
short distance clockwise before sliding out beneath it, fully visible with
a slight tilt, while the page grows to fit both faces. Reduced-motion
preferences SHALL show the same final state directly without positional
animation.

#### Scenario: Reveal the hidden face

- **WHEN** the learner activates the single reveal action on an unrevealed card
- **THEN** the prompt face settles tilted aside, the other face becomes fully visible beneath it with a slight tilt, and no third control appears

#### Scenario: Direction is fixed per session

- **WHEN** a session starts with the reverse preference
- **THEN** every card prompts from the back, the forward preference cannot be changed until the session ends, and no swap control exists

#### Scenario: Reduced motion reveal

- **WHEN** reduced motion is requested and the learner reveals a card
- **THEN** both faces are shown in their final positions without animation frames
