## MODIFIED Requirements

> ⚠️ **应用顺序**：本 delta 以 `openspec/changes/workbench-visual-language-v2/specs/workbench-ui/spec.md`
> 的**当前文本**为底（那三条 requirement v2 已改过），在其上叠加 V1 收敛项。
> ⇒ **归档顺序：先 v2，后本 change**（否则本 change 的整块会覆盖 v2 的段落）。

### Requirement: Three-column shell with navigation

The workbench SHALL render a three-column desktop layout: a left navigation column with workspace and study navigation, a primary middle page, and a collapsible right Agent conversation column, with the workspace name and the chapter lens in the top bar (the machine course identifier SHALL NOT be shown there). At narrow widths the middle page SHALL remain the single primary column; the left and right columns SHALL become dismissible drawers opened by two compact icon controls in the top bar. Switching workspaces or pages SHALL preserve recorded pool state.

#### Scenario: Navigate from the left column

- **WHEN** the learner clicks a navigation entry in the left column
- **THEN** the middle area shows the corresponding page for the current workspace

#### Scenario: Open mobile navigation

- **WHEN** a learner at a narrow viewport activates the navigation icon
- **THEN** the left column opens as a drawer without hiding the middle page permanently

#### Scenario: Open mobile Agent conversation

- **WHEN** a learner at a narrow viewport activates the conversation icon
- **THEN** the right column opens as a drawer and can be dismissed back to the middle page

#### Scenario: Switch workspace without losing state

- **WHEN** the learner switches the workspace dropdown
- **THEN** the new workspace loads and previously recorded attempts, feedback, and signals remain intact in their original pool

#### Scenario: The top bar shows the name, not the identifier

- **WHEN** a workspace's course is an automatically allocated code and its name is the folder name
- **THEN** the top bar shows the workspace name, and the code does not appear there

#### Scenario: The chapter context lives in the lens control

- **WHEN** a chapter is active
- **THEN** the top bar shows it through the chapter lens control rather than repeating it beside the workspace name

The three-column geometry SHALL have one source of truth: the widths, the
reservations and the collapse behaviour of the left column, the middle page and
the right column SHALL be decided in one place and SHALL NOT be overridden
afterwards by a later rule. The left column SHALL show each navigation entry as
a pictogram together with its label, and the selected entry SHALL be marked by a
rounded block spanning the whole row. The top bar SHALL be arranged in three
parts — the brand, the current identity, and the actions. The middle page SHALL
NOT reserve space for any retired surface: no unclaimed strip SHALL remain
beside the page title or under the title band.

#### Scenario: One geometry decides the columns

- **WHEN** the shell is laid out and the left, middle and right columns are
  resized or collapsed
- **THEN** their widths and their collapse behaviour come from a single
  definition and do not change again afterwards

#### Scenario: The selected navigation entry reads as a block

- **WHEN** the learner views the left column
- **THEN** the selected entry is marked by a rounded block spanning the whole
  row and the other entries are not

#### Scenario: No dead reservation in the middle page

- **WHEN** the learner views a middle page with a title band
- **THEN** no unclaimed strip remains beside the title or under the title band

The shell SHALL lay out in four viewport tiers, and the tier — not the page —
SHALL decide the columns. At 1440 pixels and wider the left, middle and right
columns stand at 280 pixels, the remaining width, and 420 pixels. From 1280 to
1439 they stand at 248, the remaining width, and 380. From 1024 to 1279 the
left column stands at 232 and the right column leaves the grid and becomes a
dismissible overlay drawer, so the middle column widens by the width the rail
vacated. From 768 to 1023 the left column becomes a dismissible overlay
drawer as well and the middle page takes the full width. Below 768 both
drawers take the full width. While the three columns stand, the middle column
SHALL keep at least 420 pixels of width. The middle column's own padding SHALL
be 24/32/48 at 1440 and wider, 28/28/64 from 1280, 24/24/64 from 1024,
24/18/48 from 768 and 16/12/40 below 768. No tier SHALL produce a horizontal
scrollbar.

#### Scenario: The columns narrow at the second tier

- **WHEN** the viewport is 1280 pixels wide
- **THEN** the left column is 248 pixels, the right column is 380 pixels and
  the middle column takes the width that is left

#### Scenario: The Agent rail becomes a drawer at the third tier

- **WHEN** the viewport is 1024 pixels wide
- **THEN** the right column is no longer part of the grid, the middle column
  widens by the width the rail vacated, and the top bar keeps an Agent
  control that opens the rail as a drawer

#### Scenario: The navigation becomes a drawer at the fourth tier

- **WHEN** the viewport is 768 pixels wide
- **THEN** the left column becomes a dismissible drawer and the middle page
  keeps the full width

#### Scenario: No tier produces a horizontal scrollbar

- **WHEN** the shell is viewed at 1440, 1280, 1024 and 768 pixels wide
- **THEN** the document does not scroll horizontally at any of them

The left column SHALL be organised as three groups: a **study group** holding
the study entries (practice, paper sets, knowledge points, knowledge graph,
records), a **settings group** holding the learner's preferences, and a
**review group** holding the items the learner is asked to revisit. The
workspace identity SHALL be shown in the top bar's current-identity part
together with the chapter lens, and SHALL NOT take a separate section of the
left column.

#### Scenario: The study group leads the left column

- **WHEN** the learner views the left column
- **THEN** its first group is the study group, and it holds the study entries
  with a pictogram and a label each

#### Scenario: The workspace identity is not a rail section

- **WHEN** the learner views the left column
- **THEN** no separate workspace section occupies the top of the rail, because
  the workspace identity is shown in the top bar

### Requirement: Agent rail presentation keeps the learning page primary

The Agent rail SHALL remain a conversation surface within the existing workbench shell, and the current Lesson Kit page SHALL remain the primary learning surface. The rail SHALL show compact chips for the current page and available page context without changing the context sent to the provider. Its text composer SHALL grow to fit entered text within the rail. Agent presentation SHALL reuse the existing workbench visual tokens; an idle rail SHALL NOT leave an auxiliary work surface open.

#### Scenario: Read the current Agent context

- **WHEN** the learner opens an Agent conversation on a workbench page
- **THEN** the rail shows the current page and available page context as compact chips while the current Lesson Kit page remains visible

#### Scenario: Enter a longer message

- **WHEN** the learner enters multiple lines in the Agent composer
- **THEN** the composer grows to show the entered text without replacing the conversation with a task dashboard

#### Scenario: No runtime activity is present

- **WHEN** the Agent is idle and no Artifact preview is active
- **THEN** the central page remains unobstructed by an Activity Float or Bottom Dock

The rail's session list SHALL have its own scrolling container, so that a long
list stays reachable instead of being cut off by the rail's own bounds. The
rail's messages SHALL be shown as a stream of rounded cards, and the composer
SHALL sit against the bottom of the rail. At narrow widths the rail opens as a
drawer that keeps the same session-list, message and composer structure as the
docked rail, and SHALL NOT collapse into one long unbroken document in which the
composer scrolls away with the messages.

#### Scenario: A long session list stays reachable

- **WHEN** the learner has more sessions than the rail can show at once
- **THEN** the session list scrolls on its own and every session can be reached

#### Scenario: The narrow-width drawer keeps the rail structure

The session list SHALL group its entries by recency — sessions from today,
sessions from yesterday, and sessions older than that — so that a learner can
find a recent conversation without reading the whole list. Each group SHALL
carry a plain heading, and the grouping SHALL NOT add a count, a statistic or
any other figure beside a session.

#### Scenario: Sessions are grouped by recency

- **WHEN** the learner opens the Agent rail's session list
- **THEN** the entries are grouped under headings for today, yesterday and
  earlier, in that order

#### Scenario: A group heading carries no figure

- **WHEN** the learner reads a session-list group heading
- **THEN** it shows only the recency wording, and no count or statistic

### Requirement: Redundant state cues

Color SHALL NOT be the only carrier of learning or interaction state. Active
navigation, graph learning states, and errors SHALL retain text, outline, position,
or another geometric cue in addition to color.

#### Scenario: Active navigation

- **WHEN** a navigation item is active
- **THEN** it has both active text styling and a blue structural edge

#### Scenario: Graph state

- **WHEN** a node has a formal learning state
- **THEN** its existing state name remains available while its outline uses the
  corresponding visual role

Every learning state SHALL additionally carry a redundant state channel (冗余状态通道):
a geometric cue — a coloured status dot — in addition to its colour. The
redundant state channel SHALL be used for Paper status dots, answer cells,
knowledge-point states and record verdicts, and SHALL NOT be replaced by a
written explanation of the state.

#### Scenario: A state carries colour and shape

- **WHEN** a Paper status dot, an answer cell, a knowledge-point row or a record
  verdict is shown
- **THEN** it carries a coloured dot in addition to its colour

#### Scenario: A state is not explained in words

- **WHEN** a state is marked on any surface
- **THEN** no explanatory text label is placed beside it to convey that state

Each entry in the left column's review group SHALL carry the redundant state
channel for the state that put it there, and the state SHALL be readable from
the dot's colour **and** its geometry alone. The set of states a review entry
can carry SHALL be fixed and SHALL use the contract words for those states.

#### Scenario: A review entry carries its state

- **WHEN** the learner views the left column's review group
- **THEN** each entry leads with a status dot whose colour and geometry both
  identify why it is there

#### Scenario: The state set is fixed

- **WHEN** the learner sees a review entry's dot
- **THEN** its colour and geometry come from the defined set of review states
  and from no other meaning

## ADDED Requirements

### Requirement: Top bar actions

The top bar's third part — the actions part — SHALL carry the controls that
act on the shell as a whole, and SHALL be present at every viewport width.
It SHALL carry a control that opens or hides the Agent conversation column,
a control that switches between the warm and the night value set, a control
that switches the Agent rail between its session-list view and its
conversation view, and a way to search. A control SHALL be reachable by
keyboard, SHALL expose an accessible name, and SHALL NOT change the request
sequence or the data the provider receives.

#### Scenario: The actions part is never empty

- **WHEN** the learner views the workbench at any viewport width
- **THEN** the top bar's third part carries its controls, and the part is not
  left empty

#### Scenario: Open or hide the Agent column

- **WHEN** the learner activates the Agent control in the top bar
- **THEN** the Agent conversation column is shown or hidden, and the middle
  page widens by the width the column vacated

#### Scenario: Switch the value set

- **WHEN** the learner activates the theme control in the top bar
- **THEN** the shell switches between the warm and the night value set, and
  the choice is remembered for that workspace

#### Scenario: Switch the rail between its two views

- **WHEN** the learner activates the rail-view control in the top bar
- **THEN** the Agent rail shows its session list or its conversation, and the
  request sequence and the provider's context are unchanged

#### Scenario: Every action control is reachable and named

- **WHEN** the learner tabs through the top bar
- **THEN** each control receives focus in turn and exposes an accessible name

### Requirement: Display preferences take effect at once

The shell SHALL offer the learner's display preferences — whether the
self-rating surface is shown, and whether a question's source line is shown —
in the settings view. The preferences that the left rail has always carried
SHALL stay there as well, so that a place the learner can see is not moved
without a word. Both entry points SHALL drive the same stored value. Changing
either preference SHALL take effect on the page the learner is looking at,
without the learner leaving the current paper and starting it again. Sources SHALL default to hidden while retaining explicit stored preferences. Both hiding and reenabling eligible source/self-rating surfaces in an ordinary Paper SHALL take effect immediately, including when the Paper started with rating off; recorded round modes and answer locking SHALL remain unchanged.

#### Scenario: The settings view carries the display preferences

- **WHEN** the learner opens the settings view
- **THEN** it offers a control for the self-rating surface and a control for
  the question's source line

#### Scenario: The two entry points share one value

- **WHEN** the learner changes a display preference in one place
- **THEN** the other place shows the same value

#### Scenario: A change takes effect at once

- **WHEN** the learner turns a display preference off while a paper is open
- **THEN** the corresponding surface disappears from the page in front of the
  learner, and no reload or restart is needed

#### Scenario: The next paper follows the new preference

- **WHEN** the learner starts the next paper after changing a display
  preference
- **THEN** that paper follows the new preference
