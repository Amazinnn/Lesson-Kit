## ADDED Requirements

### Requirement: Practice records page

The three-column shell SHALL gain a 做题记录 navigation entry rendering the
learner's practice history server-side: newest first, each row showing the
problem (linked), an honest verdict badge (对 / 错 / 未判定), the rating as
stars when one is linked, the note, the answer excerpt, and the time. The view
SHALL degrade to an honest empty state when no attempts exist, and SHALL
support isolating one problem's history via the URL.

#### Scenario: A fresh workspace shows an honest empty state

- **WHEN** no attempt exists in the pool
- **THEN** the records page says so instead of rendering an empty list

#### Scenario: One problem's history is isolatable

- **WHEN** the records page is opened with a problem identifier
- **THEN** only that problem's attempts are listed

### Requirement: Problem fields render math wherever they render text

Every surface that renders a problem field as rich text SHALL run the same
math pipeline over it — including objective-item options and the live verdict
line's error reason, which previously escaped (or worse, concatenated) their
text. A field rendered escaped-only elsewhere SHALL NOT appear rendered in one
place and raw in another on the same screen.

#### Scenario: Options render their math

- **WHEN** a choice item's option text contains `$…$` math
- **THEN** the option label renders the formula with KaTeX, the same string the reveal renders

#### Scenario: The verdict line is safe and rendered

- **WHEN** an objective answer is graded wrong and the error reason carries math or markup
- **THEN** the reason is escaped-then-rendered, never injected raw

### Requirement: In-chat model switcher

The chat header SHALL offer a model select listing the model entries of the
conversation's own harness, marking the conversation's current model; choosing
one switches the conversation's model for the next turn and is reflected on
reload. Switching SHALL be refused while a turn is running, and a raw model id
no entry names SHALL be shown as the current choice so the state is never
silent.

#### Scenario: The switcher reflects and changes the model

- **WHEN** a conversation is opened and the learner picks another entry
- **THEN** the conversation records the new model, the next turn runs on it, and reloading shows the new selection
