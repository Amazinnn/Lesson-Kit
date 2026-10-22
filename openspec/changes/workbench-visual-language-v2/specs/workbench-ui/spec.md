## ADDED Requirements

### Requirement: Paper levels and elevation

The workbench SHALL present every surface at exactly one of four paper levels
(纸面层级): base, card, raised, or ink block. The base level SHALL be the warm
cream page ground, the card level a page panel, the raised level a surface that
reads as lifted above its parent, and the ink block the dark level used for code
surfaces and selected items. Levels SHALL be separated by the shared 12px corner
radius and a soft warm shadow, and SHALL NOT be separated by hairline borders.
Surfaces at the same level SHALL be visually interchangeable, and the page ground
SHALL carry no pattern, texture or noise.

#### Scenario: A panel sits on the page ground

- **WHEN** a learner opens a page that groups content into panels
- **THEN** each panel reads as exactly one level above the warm cream page
  ground, separated by rounded corners and a soft shadow rather than a border line

#### Scenario: Code and selected items read as the ink block

- **WHEN** a code surface or a selected item is shown
- **THEN** it renders on the darkest paper level, at the same 12px corner radius
  as the surrounding panels

#### Scenario: The page ground carries no texture

- **WHEN** any workbench page is inspected at full size
- **THEN** the ground is a flat warm cream with no pattern, noise or vignette
  laid over it

### Requirement: Theme preference and the night paper value set

The visual language SHALL have two value sets: the warm cream ground and the
night paper (夜纸), a warm deep brown. The night paper SHALL be a second value
set of the same three accent roles, not a new colour family; the accent roles
SHALL be reused there with circular grounds desaturated and lightened. No new
accent hue SHALL be introduced by either value set, and the night paper SHALL
NOT read as a separate dark island inside a light page. The theme preference
(主题偏好) that chooses between them SHALL be a browser preference stored per
workspace, SHALL NOT write to the pool and SHALL NOT affect any learning fact.

Switching between the two value sets SHALL be presented as the lamp transition
(台灯转场): a desk lamp leans out and lights up, the ground change ripples
outward from it, and the lamp withdraws. The ripple SHALL NOT block interaction
and SHALL NOT change the order or timing of any request.

#### Scenario: Switch to the night paper

- **WHEN** the theme preference selects the night paper
- **THEN** every workbench surface takes the night paper values, the accent
  roles stay the same three, and this value set does not restyle the knowledge
  graph page, whose own night values are governed separately

#### Scenario: No new hue appears at night

- **WHEN** the night paper value set is active
- **THEN** the accent colours are the same three role colours used in the warm
  cream set, only their values differ, and no fifth accent appears

#### Scenario: The change is narrated by the lamp

- **WHEN** the theme preference changes
- **THEN** a desk lamp leans out and lights up, the ground change ripples
  outward from it, and the lamp withdraws

#### Scenario: The theme preference writes nothing to the pool

- **WHEN** the learner changes the theme preference
- **THEN** no pool record, learning fact or statistics row is written or changed

### Requirement: Reading face and interface face

The visual language SHALL use three type families with distinct duties. Reading
surfaces — knowledge-point bodies, problem statements, revealed solutions and
other long-form text — SHALL use the reading face (阅读字面). Navigation,
buttons, tabs, tables, status chips and numerals SHALL use the sans-serif
interface face. Monospace SHALL remain a separate third family for code.

Switching the reading face SHALL change the type family only: body size, line
height and measure SHALL NOT change with it, and interface surfaces SHALL NOT
switch away from the sans-serif interface face. The reading face is a browser
preference stored per workspace; the assignment of families to surfaces is fixed
by this visual language.

#### Scenario: Interface chrome stays sans-serif

- **WHEN** the reading face is switched
- **THEN** navigation entries, buttons, tables, status chips and numerals keep
  the sans-serif interface face

#### Scenario: Switching the reading face changes only the family

- **WHEN** the reading face is switched from serif to sans-serif
- **THEN** long-form body text keeps its 17px size, its 1.75 line height and its
  38em measure

#### Scenario: Code keeps its own family

- **WHEN** a code surface is rendered inside a reading surface
- **THEN** the code is set in the monospace family, not in the reading face

### Requirement: Motion system and reduced-motion downgrade

The workbench SHALL animate across four surfaces — interaction feedback, the data
layer, view transition, and milestone ceremony — and SHALL NOT add a global
background canvas, cursor tracking, parallax, or cursor glow. Interaction
feedback SHALL complete within 120–180ms and scene motion within 240–520ms. A
confirmed answer SHALL use a squash-and-stretch rebound; newly revealed content
SHALL rise and fade in; a newly loaded middle page SHALL show a container-level
transition together with a skeleton of grey blocks crossed by a travelling
highlight.

Completing a round SHALL be celebrated in layers: an ordinary completion gets a
rolling number and a progress band, and a milestone — a fully correct round, a
new record, a chapter completed for the first time — adds geometric bursts and
paper flutter on top. A run of consecutive correct answers SHALL be shown by a
three-tier counter whose tone changes as the run grows, and SHALL interject one
banner at five and at ten in a row; the banner SHALL be a single parameterised
banner rather than one banner per number. The streak progress SHALL itself be
animated so that it grows visibly with the run. Answering wrong while the run is
above four SHALL give an explicit negative signal rather than silence.

Motion SHALL NOT change request timing, ordering or payload, and SHALL stay
within a budget that keeps the interface responsive to input. When the motion
preference (动效偏好) is off, every motion SHALL degrade to a direct state
change. When the system asks for reduced motion and the learner has made no
explicit choice, the motion preference SHALL follow that request and every
motion SHALL likewise degrade to a direct state change: the ground changes
directly, a celebration lands on its final state, and a streak counter updates
without animating. An explicit learner choice to enable motion SHALL take
precedence over the system setting.

#### Scenario: An answer is confirmed

- **WHEN** the learner submits an answer and a verdict appears
- **THEN** the confirmed element gives a squash-and-stretch rebound within the
  interaction duration band

#### Scenario: A new middle page arrives

- **WHEN** the learner navigates to another middle page
- **THEN** the page area transitions as one container and shows a skeleton of
  grey blocks with a travelling highlight before the content settles

#### Scenario: An ordinary completion is celebrated lightly

- **WHEN** a round finishes with at least one wrong answer
- **THEN** the completion shows rolling numbers and a progress band without
  geometric bursts or paper flutter

#### Scenario: A milestone is celebrated fully

- **WHEN** a round finishes fully correct, or a chapter is completed for the
  first time
- **THEN** the completion adds geometric bursts and paper flutter on top of the
  rolling numbers and the progress band

#### Scenario: The streak reaches five in a row

- **WHEN** the learner answers five consecutive items correctly
- **THEN** one streak banner is shown, and the same banner is reused for the run
  of ten with a different count

#### Scenario: The streak breaks

- **WHEN** the learner answers wrongly while the run of consecutive correct
  answers is above four
- **THEN** an explicit negative signal is shown and the run counter is reset

#### Scenario: Reduced motion is requested

- **WHEN** the operating system asks for reduced motion, or the learner turns the
  motion preference off
- **THEN** the ground changes directly, the celebration lands on its final state,
  and the streak counter updates without animating

#### Scenario: Motion does not change what is sent

- **WHEN** the learner confirms an answer while a celebration is playing
- **THEN** the request and its payload are the same as when no motion is
  enabled

### Requirement: Focus visibility and contrast floors

Every interactive control SHALL show a visible focus indicator when it receives
keyboard focus, and that indicator SHALL NOT be suppressed by the control's own
focus styling. Body text SHALL reach a contrast ratio of at least 4.5:1 against
the surface it sits on. Secondary text, control boundaries and non-text state
markers SHALL reach at least 3:1 against their surroundings. Both floors SHALL
hold in the warm cream ground and in the night paper.

#### Scenario: Keyboard focus on a form control

- **WHEN** the learner tabs to a select, a text input or a button
- **THEN** that control shows a visible focus indicator

#### Scenario: Focus is not suppressed by the control itself

- **WHEN** a focused select or text input is styled by its own focus rule
- **THEN** the focus indicator remains visible on that control

#### Scenario: The contrast floors hold in both themes

- **WHEN** any workbench page is measured for contrast in the warm cream ground
  and again in the night paper
- **THEN** body text measures at least 4.5:1 and secondary text, control
  boundaries and state markers at least 3:1 in both

### Requirement: Density zoning

Reading surfaces SHALL be generous: body text keeps a 17px size, a 1.75 line
height and a 38em measure, and paragraphs are separated by space rather than by
rules. List and data surfaces SHALL be tight: rows, record entries, session
entries and option lists use compact spacing and smaller type, so that counts
stay comparable at a glance. The density of a surface SHALL be decided by the
kind of content it carries, not by the page it sits on.

#### Scenario: A reading surface is generous

- **WHEN** a learner reads a knowledge body or a revealed solution
- **THEN** the text is set at the reading size and the paragraphs are separated
  by space rather than by a dividing rule

#### Scenario: A data surface is compact

- **WHEN** the learner opens a list of records, sessions or options
- **THEN** the entries are set close together at a smaller type so that many
  entries fit one screen

### Requirement: Shared reading typographic layer

Long-form rendered content — knowledge-point bodies, problem statements,
revealed solutions, Agent messages and experience notes — SHALL share one
reading typographic layer, so that headings, paragraphs, lists, quotations, code,
images and tables are set the same way wherever they appear and whichever
renderer produced them. The server-rendered Markdown and the client-rendered
Markdown SHALL produce the same HTML for the same input, so that a document
rendered on the server and the same document rendered in the browser are
indistinguishable. Raw HTML SHALL remain escaped or rejected.

#### Scenario: The same Markdown rendered on both sides

- **WHEN** the same Markdown source is rendered by the server and by the client
- **THEN** both renderings produce the same elements with the same styling, so
  the two are indistinguishable to the learner

#### Scenario: A knowledge body carries the reading layer

- **WHEN** a knowledge point is opened
- **THEN** its headings, paragraphs, lists and tables are set by the shared
  reading layer rather than by the browser default

#### Scenario: Rich content keeps its safe feature set

- **WHEN** a reading surface contains a table, mathematics, an image or a code
  block
- **THEN** the table, the formula, the image and the code are all rendered
  inside the shared layer, and raw HTML in the source stays escaped

### Requirement: Interface copy voice

Interface copy SHALL be written in one consistent Chinese voice, SHALL NOT mix
Chinese and English within one label or one sentence, and SHALL follow the
minimal-annotation principle (少字原则): an annotation that could be replaced by
the shape or the colour of an element SHALL be removed rather than restyled. An
empty state SHALL consist of a still-life illustration (静物插画), one sentence,
and a full-width primary button whose label is the action itself.

#### Scenario: An empty state offers an action

- **WHEN** a learner opens a view that has nothing in it yet
- **THEN** the view shows a still-life illustration, one sentence, and a
  full-width primary button labelled with the action it performs

#### Scenario: An annotation is removed rather than restyled

- **WHEN** a piece of interface text only restates what the shape or the colour
  of the element already shows
- **THEN** the text is not shown, and no replacement sentence is added

#### Scenario: One language per label

- **WHEN** any label, button, empty-state sentence or column heading is read
- **THEN** it is written in Chinese only, with no English word mixed into the
  same label or sentence

### Requirement: Workspace card information hierarchy

The hub SHALL show the most recently used workspaces first as larger cards and
the remaining workspaces in a grid below them. Each workspace card SHALL give
its name the largest type on the card and SHALL show its knowledge-point count,
its problem count and its due-for-review count on one line in smaller type,
each count introduced by a small colour dot. The count colours SHALL be drawn
from the accent roles, and the dot SHALL be the redundant state channel for that
count rather than a colour applied to the whole card.

#### Scenario: The hub opens on recent work

- **WHEN** the learner opens the hub
- **THEN** the most recently used workspaces are shown first as larger cards
  and the rest are shown in a grid below

#### Scenario: A card shows its counts with dots

- **WHEN** a workspace card is shown
- **THEN** its name is the largest text on the card and its three counts sit on
  one line in smaller text, each introduced by a small coloured dot

#### Scenario: A count is not colour-only

- **WHEN** a count dot is shown on a workspace card
- **THEN** the count is still readable in text next to the dot, and the dot
  carries the colour rather than replacing the number

## MODIFIED Requirements

### Requirement: Soft Mondrian visual foundation

The workbench SHALL apply Soft Mondrian v2 (柔和蒙德里安 v2): a warm, modern,
rounded visual language. The page ground SHALL be warm cream and the ink SHALL be
warm charcoal. Buttons, cards, labels and inputs SHALL share one 12px corner
radius. Surfaces SHALL be separated by paper level (纸面层级) and by soft warm
shadow, and SHALL NOT be separated by hairline borders or by background texture.
Blue, yellow and red SHALL remain the only accent roles, at a more saturated
tonality than before, and no fifth accent role SHALL be introduced. Blue SHALL
represent primary action, links and current selection; yellow SHALL represent
the current item, review emphasis and streak progress; red SHALL represent
failure and blocked states. Yellow SHALL carry area and shape only and SHALL NOT
carry body text. Most screen area SHALL remain paper or neutral. Learning state
SHALL NOT be carried by colour alone: every state SHALL also carry a redundant
state channel (冗余状态通道) in addition to its colour.

Navigation graphics SHALL depict the thing they stand for and SHALL be derived
from the surrounding visual rules under the contextual-graphic principle
(图案适配原则), rather than added as a decorative layer on top of them. This
foundation SHALL leave the knowledge graph page's appearance unchanged: the
token values the knowledge graph depends on — including the sheet surface it
reads as paper — SHALL keep their current values. That guarantee is scoped to
this foundation only; the knowledge graph page's own visual language is
governed separately and may be restyled by a separate change.

#### Scenario: Ordinary workbench page

- **WHEN** a learner opens any core page
- **THEN** the shell is structured by warm cream paper surfaces separated by
  rounded corners and soft shadow, with only compact red, yellow and blue
  accents

#### Scenario: Primary action

- **WHEN** a primary action is enabled
- **THEN** it is blue, carries the shared 12px corner radius, and remains
  identifiable by its label

#### Scenario: Accent roles stay scarce

- **WHEN** a list of cards is shown and only one of them is the current item or
  is due for review
- **THEN** only that card carries a yellow area, and no card carries a
  decorative colour band

#### Scenario: A navigation graphic depicts its target

- **WHEN** the left column shows its navigation entries
- **THEN** each entry carries a pictogram of the thing it opens, drawn on a
  rounded coloured ground taken from the accent roles, and the pictogram is not
  an abstract placeholder shape

#### Scenario: This foundation leaves the knowledge graph page unchanged

- **WHEN** the learner opens the knowledge graph page after this foundation is
  applied
- **THEN** this foundation has left the graph page's appearance and the token
  values it depends on unchanged

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

Body text on a reading surface — knowledge-point body, question stem and revealed
solution alike — SHALL be set at 17px with a 1.75 line height and a measure of
38em, so that a line carries about 38 Chinese characters. The reading size SHALL
NOT be reduced below the current size on any surface. Within the question
surface, text that is not the stem — the item's source line and the answer
composer's label — SHALL step down one step to 16px. Each reading surface SHALL
keep one single-side structural rule and SHALL avoid decorative shadow emphasis;
controls and metadata SHALL remain visually secondary.

The question stem SHALL sit on its own paper level and carry a large item
number; the revealed solution SHALL sit on a peer paper level rather than as a
smaller, greyed-down footnote; the answer area SHALL be marked off as a separate
block by a rule and a label.

#### Scenario: The reading rhythm is measurable

- **WHEN** a knowledge body, a question stem or a revealed solution is measured
- **THEN** its body text is 17px with a 1.75 line height and a 38em measure

#### Scenario: The question surface has its own level

- **WHEN** a practice item is shown with its answer area
- **THEN** the stem sits on its own paper level with a large item number, the
  revealed solution sits on a peer level, and the answer area is a separately
  marked block

#### Scenario: Secondary text inside a question steps down

- **WHEN** the question surface shows its source line and its answer composer's
  label beside the stem
- **THEN** those lines are set at 16px while the stem keeps the reading size

### Requirement: Redundant state cues

Color SHALL NOT be the only carrier of learning or interaction state. Active
navigation, graph learning states, and errors SHALL retain text, outline, position,
or another geometric cue in addition to color.

#### Scenario: Active navigation

- **WHEN** a navigation item is active
- **THEN** it has both active text styling and a blue structural inset

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

### Requirement: Records center

The three-column shell SHALL expose a 记录 navigation entry as a dedicated
server-rendered history center. It SHALL provide overview, practice/paper runs,
attempt details, and wrong/stuck views. Attempt rows SHALL retain the linked
problem, honest verdict (对 / 错 / 未判定), linked rating, note, answer excerpt,
and time. Overview statistics and charts SHALL be derived from durable attempts
and feedback at read time and SHALL NOT write cached statistics.

A completed or explicitly replaced/cleared active practice SHALL leave one
minimal durable run snapshot containing its source kind/reference/label,
practice/rating modes, item order/final states, and timestamps. A saved paper
run SHALL therefore remain identifiable as that paper without copying problem
text, solutions, ratings, or other learning evidence into the run snapshot.

#### Scenario: A fresh workspace shows an honest empty state

- **WHEN** no attempt or archived run exists in the pool
- **THEN** the records center shows zero/empty views instead of fabricated activity

#### Scenario: A saved paper is completed

- **WHEN** an active practice started from a saved paper finishes
- **THEN** the run view shows one completed paper run with its saved title and item progress while the attempts remain the per-problem evidence

#### Scenario: Overview is read-only

- **WHEN** the records overview renders its 14-day volume, accuracy, and rating distribution
- **THEN** those values are aggregated from existing records and no learning or statistics row is written

#### Scenario: One problem's history is isolatable

- **WHEN** the records page is opened with a problem identifier
- **THEN** only that problem's attempts and attempt-derived statistics are shown

The records centre SHALL present as a data surface. The overview's summary
figures SHALL be shown as dashboard cards of unequal weight, each carrying a
miniature chart. The activity calendar SHALL be a compact grid of small squares
in which intensity is encoded by fill and by height, so that it no longer reads
as a disabled spreadsheet and no longer occupies a whole screen. The attempt
list SHALL be a stream of rounded cards separated by whitespace and soft shadow
rather than a bordered table. The wrong-problem view SHALL be a stream of rounded
cards, each carrying the problem and a summary of why it went wrong.

The four summary figures — attempt count, completed practices, objective-question
accuracy and mean self-rating — SHALL keep their present values and their
present definitions; a difference in what any of them counts is registered as
separate drift and SHALL NOT be altered here. Every record surface SHALL carry
the redundant state channel, so that a verdict is conveyed by colour and by a
geometric cue together.

#### Scenario: The overview shows dashboard cards

- **WHEN** the records overview is opened
- **THEN** the summary figures are shown as dashboard cards of unequal weight,
  each carrying a miniature chart

#### Scenario: The activity calendar is compact and decodable

- **WHEN** the activity calendar is shown
- **THEN** it is a compact grid of small squares whose intensity is encoded by
  fill and by height, and it does not occupy a whole screen

#### Scenario: The attempt list is a card stream

- **WHEN** the attempt list is shown
- **THEN** each attempt is one rounded card separated by whitespace and soft
  shadow rather than a row of a bordered table

#### Scenario: The summary figures keep their present values

- **WHEN** the records overview is compared before and after this change
- **THEN** the attempt count, the completed-practice count, the objective
  accuracy and the mean self-rating report the same numbers as before

### Requirement: Learner settings in the left rail

The workbench's left column SHALL carry a settings section whose preferences
apply across the practice and paper surfaces. Its first preference SHALL be a
checkbox, 「练习与组卷显示自评」, defaulting to on: self-rating behaves exactly
as before. With it off, no self-rating surface SHALL appear anywhere in the
flow — the rating-timing choice is hidden and not required to start, the
feedback panel never renders, a finished round takes the no-session-end path,
and records label the round 关闭自评. The preference SHALL persist per
workspace in the browser across tabs and restarts, and SHALL take effect at the
next round's start; a running round keeps the mode it started with.

#### Scenario: The preference survives a restart

- **WHEN** the learner turns the checkbox off and reopens the workbench later
- **THEN** the checkbox is still off and a new round starts without any
  self-rating surface

#### Scenario: Off removes every rating surface

- **WHEN** a round starts with the preference off
- **THEN** the rating-timing fieldset is absent, no feedback panel appears
  during the round, the round ends without the session-end view, and records
  show 关闭自评 for it

#### Scenario: On keeps today's behavior

- **WHEN** the preference is on
- **THEN** the rating-timing choice, per-problem rating, and session-end
  unified rating behave as before

The left column SHALL keep this section for learning-behaviour preferences.
Appearance preferences SHALL NOT live there: the theme preference (主题偏好),
the reading face (阅读字面), the motion preference (动效偏好) and the
sound preference (声音偏好) SHALL be held by the workbench settings view
(工作台设置视图), which the left column's settings section opens and closes. All
of these preferences SHALL be stored per workspace in the browser, SHALL NOT
write to the pool, and SHALL NOT affect any learning fact.

#### Scenario: The settings view opens from the left column

- **WHEN** the learner activates the settings control in the left column
- **THEN** the workbench settings view opens in the middle page and closes again
  on the same control

#### Scenario: Appearance preferences are stored per workspace

- **WHEN** the learner changes an appearance preference in one workspace and
  later opens another workspace
- **THEN** the other workspace keeps its own appearance preferences

#### Scenario: Appearance preferences write nothing to the pool

- **WHEN** the learner changes an appearance preference
- **THEN** no pool record, learning fact or statistics row is written or changed

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

- **WHEN** the learner opens the Agent rail as a drawer at a narrow width
- **THEN** the drawer shows the session list, the messages and the composer in
  the same structure as the docked rail, with the composer still reachable

### Requirement: Accessible Paper status dots

A compact numbered status-dot panel SHALL navigate to every item. Whole-Paper mode before submission SHALL distinguish unanswered, filled and stuck without showing correctness. Per-item mode SHALL show correct/wrong only with usable verdicts, and distinguish filled-but-unsubmitted from submitted-without-verdict. Current item SHALL have an outline or equivalent non-color cue. Statuses SHALL have readable accessible names, not color alone; many items SHALL not obscure the question or navigation.

#### Scenario: No premature grading cues
- **WHEN** answers are filled in whole-Paper mode before submission
- **THEN** colors, text, badges and summaries show filled status without exposing right/wrong

#### Scenario: Jump and read status
- **WHEN** any numbered dot is activated
- **THEN** the question appears with accessible status and a distinct current-item indicator

Every dot SHALL carry the redundant state channel: the dot's colour states the
status and a geometric difference states it a second time, so that the panel is
readable without colour. The panel SHALL be laid out as a compact rounded grid
that does not obscure the question surface or the navigation around it, and each
item's number SHALL be shown as a large numeral so that the learner can tell
which item they are on without counting.

#### Scenario: A dot states its status twice

- **WHEN** the Paper status panel shows a filled item and an unanswered item
- **THEN** the two differ by colour and by shape, so the difference survives
  without colour

#### Scenario: The panel stays compact

- **WHEN** a Paper has many items and the status panel is shown
- **THEN** the panel occupies a compact rounded block and does not cover the
  question or the navigation

### Requirement: Same-workspace middle navigation preserves the Agent rail

Navigating between pages and query states within one workspace SHALL update
only the middle page content and its route-owned lifecycle. The existing
`#ai-column` DOM and Agent controller SHALL remain mounted. Browser back and
forward SHALL follow the same behavior. Navigation SHALL update current page
context for future submissions while preserving the context already captured
by accepted work. External, cross-workspace, modified-click, download, and
explicitly targeted links SHALL keep native browser navigation.
The server-rendered `#ai-column` SHALL have the same structure on graph and
non-graph pages. Graph-only dashboard content SHALL belong to the graph middle
page, and selecting a graph node SHALL NOT hide or replace the Agent chat.

#### Scenario: Navigate within the workspace

- **WHEN** the learner follows a same-workspace page link from navigation, a
  page card, or middle content
- **THEN** the middle page changes while the existing Agent rail and its
  controller remain in place

#### Scenario: Navigate back or forward

- **WHEN** the learner uses browser Back or Forward after a same-workspace
  navigation
- **THEN** the middle page and its route-owned behavior change without
  rebuilding the Agent rail

#### Scenario: Send after navigating

- **WHEN** the learner sends a new message after changing the middle page
- **THEN** the request uses the current page context while previously accepted
  work retains its submitted context

#### Scenario: Enter and leave the graph page

- **WHEN** the learner enters or leaves the graph page within the same workspace
- **THEN** the graph dashboard mounts or disposes with the middle page while the
  same Agent rail remains visible and usable

#### Scenario: Follow a native navigation

- **WHEN** the learner uses a modified click, download, external link, or link
  to another workspace
- **THEN** the browser performs its normal navigation without middle-page
  interception

The workbench settings view (工作台设置视图) is a middle page like any other:
opening it and closing it SHALL preserve the Agent rail instance in the same
way as any other same-workspace navigation, and SHALL NOT rebuild, replace or
reset it.

#### Scenario: Open the settings view

- **WHEN** the learner opens the workbench settings view from the left column
- **THEN** the middle page shows the settings view while the existing Agent rail
  and its controller remain in place

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

## Self-check

- [x] 所有 MODIFIED 都整块复制了既有需求（不是片段）——9 条 MODIFIED 全部从
      `openspec/specs/workbench-ui/spec.md` 的对应 `### Requirement:` 块整段复制后再改写：
      既有正文与既有 Scenario 全部保留原文，只有被新基线取代的措辞（描边、纸纹、衬线仿古
      取向）按 decisions.md「收口：最终基线」改写，并追加新条款与新 Scenario。
- [x] MODIFIED 的 Requirement 标题与原文一致：
      `Soft Mondrian visual foundation` / `Learning content is the visual anchor` /
      `Redundant state cues` / `Records center` / `Learner settings in the left rail` /
      `Agent rail presentation keeps the learning page primary` /
      `Accessible Paper status dots` /
      `Same-workspace middle navigation preserves the Agent rail` /
      `Three-column shell with navigation`。
- [x] 没有 `## Purpose`（既有能力 delta 不写 Purpose）。
- [x] 每个 Requirement ≥ 1 个 Scenario：MODIFIED 9 条、ADDED 9 条，共 18 条 Requirement。
- [x] 所有 Scenario 用 `####`（4 个 #）+ `- **WHEN** …` / `- **THEN** …`。
- [x] 没有触碰任何图谱相关 Requirement：`Knowledge graph page`、`Living graph motion and
      readable labels`、`Metric projection *`、`State cluster layout`、`Layered knowledge
      relationships`、`Finite crossing optimization`、`Graph detail is a learning dashboard`
      等一律未出现在本 delta。唯一提到图谱的地方有两处**保护性条款**
      （`Soft Mondrian visual foundation` 与 `Theme preference and the night paper value set`
      各一句「图谱页观感不变 / 图谱依赖的 token 值不变」），它们不改动任何既有图谱条款，
      只保证新 token 层不牵连图谱。两处条款都**限定在「本变更不改变知识图谱页」这一范围内**：
      既不改写任何既有图谱条款，也不宣称图谱页此后永远不变——图谱自身的视觉语言由
      `graph-node-visual-language` change 另行规定，两者落地后不冲突。
- [x] 13 个新名词全部用了 SYNTH.md 的原词：柔和蒙德里安 v2 / Soft Mondrian v2、
      纸面层级 / Paper level、夜纸 / Night paper、冗余状态通道 / Redundant state channel、
      主题偏好 / Theme preference、阅读字面 / Reading face、动效偏好 / Motion preference、
      声音偏好 / Sound preference、工作台设置视图 / Workbench settings view、
      静物插画 / Still-life illustration、台灯转场 / Lamp transition、
      少字原则 / Minimal-annotation principle、图案适配原则 / Contextual-graphic principle。
- [x] 没有写 class 名 / 函数名 / 实现步骤：既有需求原文里的 `#ai-column` 属既有条款原文保留，
      新增条款一律用可观察行为表述（纸面、圆点、滚动容器、圆角卡片流、对比度、时长带、
      按钮文案即动作）。
- [x] 未修改任何产品代码，也未改动 `openspec/specs/workbench-ui/spec.md` 本体。
- [x] 视觉基线取自 `decisions.md`「# 收口：最终基线」：暖色 + 现代圆润、12px 圆角、
      浅奶油 `#fdf8ef` / 夜纸 `#1c1a16`、暖炭褐 `#221f1a`、四层纸面靠圆角与柔影不用描边、
      三角色更饱和（蓝=主按钮+链接+当前选中 / 黄=当前+复习强调+连对进度 / 红=失败+阻塞）、
      彩色圆点冗余状态通道、具象静物图标与静物插画、台灯转场、分层庆祝、
      连对三级计数器与 5/10 连插播、连对 >4 的负反馈、动效偏好与 `prefers-reduced-motion` 降级。
      旧方向的仿古提法（发丝描边分隔、极淡噪点纸纹、发光描边主按钮、作答明细真表格）
      一律未采用；作答明细按第 6 组定案写为圆角卡片流。
