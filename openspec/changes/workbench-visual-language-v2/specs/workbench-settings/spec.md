## Purpose

The workbench settings view is a dedicated view in the middle column that holds the
learner's appearance preferences — theme, reading face, motion and sound — so that
presentation can be tuned without touching the pool, the learning records, or the
scheduling of any study item.

## ADDED Requirements

### Requirement: Workbench settings view

The workbench SHALL provide a 工作台设置视图 (Workbench settings view) as a distinct
view in the middle column, opened and closed from a control in the left navigation
rail. The view SHALL carry appearance preferences only: it SHALL NOT host learner
settings that change learning behaviour, and it SHALL NOT create, alter or remove
any learning fact.

Opening, using or closing the settings view SHALL leave the Agent column and the
conversation inside it mounted as the same instance, so that a learner can tune
presentation without losing an ongoing conversation, its scroll position or its
draft input.

The settings view SHALL follow the 少字原则 (Minimal-annotation principle): every
preference is presented as a control that carries its own name and its current
value, and prose that merely restates a control SHALL be omitted.

#### Scenario: Open the settings view

- **WHEN** the learner activates the settings control in the left navigation rail
- **THEN** the middle column shows the settings view and the appearance preferences it offers

#### Scenario: Close the settings view

- **WHEN** the learner closes the settings view
- **THEN** the middle column returns to the view it showed before it was opened

#### Scenario: The Agent column survives a settings toggle

- **WHEN** the learner opens the settings view, changes a preference, and closes the settings view again
- **THEN** the Agent column and the conversation in it are the same instance as before, with no re-creation and no lost scroll position or draft input

#### Scenario: Only appearance preferences are hosted

- **WHEN** the learner inspects the settings view
- **THEN** it offers theme, reading face, motion and sound preferences and no control that changes learning behaviour or learning records

### Requirement: Appearance preferences are browser preferences stored per workspace

The theme preference, the reading face, the motion preference and the sound
preference SHALL be stored as browser preferences scoped to the workspace that is
open. They SHALL be kept in the same workspace-scoped preferences record as the
workbench's existing per-workspace browser settings, so that one workspace's
preferences are independent of any other workspace's. They SHALL survive a reload
and a browser restart.

The preferences SHALL NOT be written to the pool, SHALL NOT appear as pool content,
and SHALL NOT travel between workspaces. Removing the stored preferences SHALL
restore the default state of every preference, including the warm-paper theme.

#### Scenario: Preferences are independent per workspace

- **WHEN** the learner sets a theme preference in one workspace and then opens a different workspace
- **THEN** the second workspace shows its own theme preference, not the first workspace's

#### Scenario: Preferences survive a restart

- **WHEN** the learner sets appearance preferences and later reopens the same workspace in a fresh browser session
- **THEN** the same preferences are in effect

#### Scenario: Clearing the preferences restores the default theme

- **WHEN** the stored preferences for a workspace are removed
- **THEN** that workspace returns to the warm-paper theme and the default state of the remaining preferences

#### Scenario: Nothing reaches the pool

- **WHEN** the learner changes any appearance preference
- **THEN** no pool record is created or modified and no preference value appears as study content

### Requirement: Theme preference switches the night paper value set

The theme preference SHALL switch the workbench between the warm-paper value set and
the night paper (夜纸) value set. The night paper set is the dark value set of
柔和蒙德里安 v2 (Soft Mondrian v2), the workbench's visual language. Both value sets
SHALL share one structural set — spacing, radius, elevation, type scale, motion
scale and stacking order — so that only surface and ink values change between them.
The night paper set SHALL NOT introduce a new hue family, and the warm-paper ground
SHALL NOT be replaced by a neutral or a cool ground.

Changing the theme SHALL re-derive every surface's 纸面层级 (Paper level) — ground,
card, raised and ink block — from the active value set, and the ink colour SHALL
invert with it. Body and secondary text in the night paper set SHALL keep a contrast
ratio of at least 4.5:1 against the surface behind it.

Changing the theme preference SHALL be presented as the 台灯转场 (Lamp transition):
the desk lamp leans out and lights up, the ground colour change ripples outward
from it, and the lamp withdraws.

#### Scenario: Switch to night paper

- **WHEN** the learner sets the theme preference to night paper
- **THEN** every surface in the workbench adopts the night paper values and body and secondary text keep at least 4.5:1 contrast against the surface behind them

#### Scenario: Switch back to warm paper

- **WHEN** the learner sets the theme preference back to warm paper
- **THEN** the workbench returns to the warm-paper values and the paper levels are re-derived from them

#### Scenario: No new hue appears at night

- **WHEN** the night paper value set is active
- **THEN** the accent colours are the same three role colours used in the warm-paper set, only their values differ

#### Scenario: The change is narrated by the lamp

- **WHEN** the theme preference changes
- **THEN** the desk lamp leans out, lights up, the ground change ripples outward from it, and the lamp withdraws

### Requirement: Reading face preference selects the reading type family

The reading face preference SHALL select which type family the reading surfaces use:
the bundled serif face or the sans-serif interface face. It SHALL apply only to
reading surfaces — problem statements, knowledge-point body text, solutions,
long-form text and figure captions — and SHALL NOT change navigation, buttons, form
controls, tables, status chips, tab labels or numerals. The monospace family SHALL
remain a separate third family under either setting of the preference.

#### Scenario: Choose the serif reading face

- **WHEN** the learner selects the serif reading face
- **THEN** problem statements, knowledge-point body text, solutions, long-form text and figure captions are set in the serif family while navigation, buttons, tables, status chips and numerals keep the sans-serif family

#### Scenario: Choose the sans-serif reading face

- **WHEN** the learner selects the sans-serif reading face
- **THEN** the same reading surfaces are set in the sans-serif family and no interface surface changes

#### Scenario: The monospace family is untouched

- **WHEN** the learner changes the reading face preference
- **THEN** code, identifiers and numeric code displays keep the monospace family under both settings

### Requirement: Motion preference and system reduced motion

The motion preference SHALL default to following the operating system's reduced-motion
setting. An explicit learner choice SHALL take precedence over the system setting.

Neither the motion preference nor the system setting SHALL change the order or the
timing of any request the workbench issues, SHALL NOT intercept pointer or keyboard
hit-testing, and SHALL NOT change what a surface finally shows. When motion is off
or reduced, the affected surface SHALL present the same final state the animated
version would have ended at, and SHALL NOT be left at an intermediate or partial one.

#### Scenario: The system asks for reduced motion

- **WHEN** the operating system requests reduced motion and the learner has made no explicit choice
- **THEN** motion degrades to direct state switches and every surface reaches the same final state it would have reached with motion on

#### Scenario: The learner overrides the system

- **WHEN** the operating system requests reduced motion and the learner explicitly enables motion
- **THEN** motion is restored, restricted to the surfaces that allow it, and no request is reordered by doing so

#### Scenario: The learner turns motion off

- **WHEN** the learner explicitly turns motion off while the operating system allows motion
- **THEN** the workbench presents the same final states without animation

#### Scenario: Motion never changes what is requested

- **WHEN** any view animates
- **THEN** the sequence of requests the workbench issues and the content it finally shows are the same as they would be with motion off

### Requirement: Sound preference limits audio to key feedback

The sound preference SHALL switch the short audio cues that accompany key feedback
on and off. While it is on, audio SHALL be limited to key feedback — a correct
answer, an incorrect answer, a completed round and a milestone — and each cue SHALL
be shorter than 200 ms. No other surface, event or state change SHALL produce sound.
While it is off, no cue SHALL be produced.

Turning the sound preference off SHALL take effect without a reload, and SHALL NOT
remove or alter any visual feedback: the same feedback remains visible.

#### Scenario: Key feedback is audible

- **WHEN** the sound preference is on and the learner gets an answer right, gets one wrong, finishes a round, or reaches a milestone
- **THEN** exactly one short cue of less than 200 ms plays for that event and nothing else sounds

#### Scenario: The preference silences the workbench

- **WHEN** the learner turns the sound preference off and then produces the same four events
- **THEN** no cue plays and the visual feedback for each event is unchanged

#### Scenario: The switch takes effect immediately

- **WHEN** the learner changes the sound preference
- **THEN** the new state applies without reloading the page

### Requirement: Appearance preferences never change learning facts

No appearance preference SHALL write to the pool, create or modify a learning record,
change a learner signal, alter a scheduled review, or change any learning fact. No
appearance preference SHALL change the content of any view, the order of any list,
the value of any count, or the timing of any scheduled work.

Reloading the page or restarting the workbench SHALL affect presentation only. A
round that is in progress when a preference changes SHALL keep the state it had.

#### Scenario: A theme change leaves the records alone

- **WHEN** the learner changes the theme preference and then reloads the page
- **THEN** the records, counts and schedule are identical to what they were before the change

#### Scenario: A running round is unaffected

- **WHEN** the learner changes an appearance preference during a round
- **THEN** the round keeps its state and its schedule and only the presentation changes

#### Scenario: No preference adds a request

- **WHEN** the learner changes an appearance preference
- **THEN** the workbench issues no additional request to the server and writes nothing back

## Self-check

- [x] workbench-settings 以 `## Purpose` 开头且 50+ 字符（实际 278 字符）
- [x] workbench-settings 只有 `## ADDED Requirements`，7 个 Requirement（≥6）
- [x] 每个 Requirement ≥ 1 个 Scenario，Scenario 一律用 `####`（4 个 #）+ WHEN/THEN，共 25 个 Scenario
- [x] 外观偏好全部声明为「不写池、不改学习事实、不改调度」
- [x] 用了 SYNTH.md 的原词（10 个）：柔和蒙德里安 v2、纸面层级、夜纸、主题偏好、阅读字面、
      动效偏好、声音偏好、工作台设置视图、台灯转场、少字原则
- [x] 另 3 个新名词（冗余状态通道、静物插画、图案适配原则）属于呈现契约，
      落在 `specs/calendar-workload/spec.md`，本文件不硬塞
- [x] 未改负荷天数与重日阈值等既有数字与判定（本能力不涉及）
- [x] 未修改任何产品代码，未改动 `openspec/specs/` 下的既有能力本体
