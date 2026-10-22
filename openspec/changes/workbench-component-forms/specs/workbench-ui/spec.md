> **本 delta 的范围**：B 类四条组件形态（`component-spec.md` §4.30）引入的**新的用户可观察行为**。
>
> | § | 组件 | 选定形态 | 落成 |
> |---|---|---|---|
> | 4.7 | 自绘下拉 | `select-spec` | ADDED 第 1 条 |
> | 4.16 | 分段进度条 | `steps-num` | ADDED 第 2 条 |
> | 4.24 | 对话框 | `dialog-spec` | ADDED 第 3 条 |
> | 4.25 | 工具调用卡 | `tool-line` | ADDED 第 4 条 |
>
> **为什么全是 ADDED、没有 MODIFIED**：这四条**不改写**任何既有需求的**行为**，
> 只**新增**此前没有任何界面承载的行为。
> `Provider activity cards show evidenced outcomes` ·
> `Failed activities expose a concise error summary` ·
> `Pi activities are conversation messages` · `Chapter switch in the top bar` ·
> `Focus visibility and contrast floors` 在本 delta 落地后**逐字继续成立**
> ⇒ 按 AGENTS.md 的契约协调纪律，**不把它们整块复制过来再改写**。
>
> **两条红线**（来自 `workbench-visual-language-v2/acceptance.md` §0）：
> **G-1** 请求序列与载荷不得变（第 1 条逐字写死）·
> **G-8** 焦点顺序不得被打乱（第 1 条与第 3 条逐字写死）。
>
> **不写死尺寸**：所有视觉尺寸都可调；唯一不可让步的是**命中区 ≥ 44×44 CSS px**
> 与**焦点环不被压死**（A-115.2 / §4.30.2）。

## ADDED Requirements

### Requirement: Custom select replaces the native select

Every single-choice selection control in the workbench SHALL be presented as one
self-drawn control: a trigger that shows the current value, and a panel of
options that opens over the page. The control SHALL be operable with the
keyboard alone: the arrow keys move the active option, `Home` and `End` move it
to the first and last option, `Enter` and `Space` commit the active option,
`Escape` dismisses the panel without changing the value, and typing a letter
moves the active option to the next option whose label begins with that
letter. The trigger SHALL be exposed as a combobox with its expanded state and
the panel as a listbox, and the active option SHALL be reported to assistive
technology while the panel is open.

Opening the panel SHALL NOT move focus off the trigger, and the control SHALL
occupy exactly one stop in the page's tab order. Closing the panel SHALL leave
focus on the trigger. The value the control reports SHALL be carried by a
hidden field — a hidden input — that keeps the original field name and the
original option values, so that the requests the workbench issues, the method
and path of each request, and the set of payload keys are the same as they were
before the control was drawn. The options offered SHALL be the same options as before, and
the control SHALL NOT display any figure the options did not carry before. When
scripting is unavailable, the control SHALL offer the same options and report
the same value as a native select would.

The control's visible size SHALL be adjustable, but its hit area SHALL be at
least 44 by 44 CSS pixels, and its focus indicator SHALL NOT be suppressed.

#### Scenario: Open the options with the keyboard

- **WHEN** the learner focuses a select trigger and presses `Enter`, `Space`,
  `Up` or `Down`
- **THEN** the option panel opens with the currently selected option active,
  and focus stays on the trigger

#### Scenario: Move to an option and choose it

- **WHEN** the panel is open and the learner presses `Down` and then `Enter`
- **THEN** the active option moves to the next option, choosing it closes the
  panel, the trigger shows the chosen option, and focus stays on the trigger

#### Scenario: Leave without choosing

- **WHEN** the panel is open and the learner presses `Escape`
- **THEN** the panel closes, the reported value is unchanged, and focus remains
  on the trigger

#### Scenario: Jump to an option by its first letter

- **WHEN** the panel is open and the learner types a letter
- **THEN** the active option moves to the next option whose label starts with
  that letter

#### Scenario: The tab order is not disturbed

- **WHEN** the learner tabs through the page
- **THEN** the select occupies exactly one stop, opening the panel adds no
  stop, and closing the panel leaves focus on the trigger

#### Scenario: The reported field is unchanged

- **WHEN** the learner changes a selection and the containing form is submitted
- **THEN** the submitted payload carries the same field name and the same
  option values as before, and the workbench issues the same requests with the
  same methods, paths and payload keys as before

#### Scenario: The options are announced

- **WHEN** a learner reaches the control with a screen reader
- **THEN** the trigger is announced as a combobox that reports whether its
  options are open, and the panel is announced as a listbox whose options
  report which one is selected

#### Scenario: Without scripting the options are still offered

- **WHEN** scripting is unavailable
- **THEN** the control still offers the same options and reports the same value
  as a native select would

### Requirement: Segmented progress shows numbered steps

A discrete multi-step progress SHALL be shown as a row of numbered steps joined
by a connector, so that the learner can count the steps instead of estimating a
proportion. Each step SHALL carry its own number, and the state of each step
SHALL be shown by shape as well as by colour, distinguishing a step that is
done, a step that is current, a step that has not started, and a step that
failed.

The indicator SHALL report the completed step count and the total step count
to assistive technology. It SHALL NOT be an interactive control: it SHALL NOT
be in the page's tab order, SHALL NOT change any value, and SHALL NOT cause
any request. When the number of steps exceeds what the row can show without
crowding, the indicator SHALL collapse to a compact summary that still states
how many steps are done and how many there are in total.

The figures the indicator shows SHALL be the ones the surrounding surface
already holds; the indicator SHALL NOT introduce a new statistic, a rate, or a
score, and SHALL NOT write anything to the pool. With motion off or reduced,
the indicator SHALL appear directly in its final state.

#### Scenario: Count the steps

- **WHEN** a discrete multi-step progress is shown
- **THEN** the steps appear as numbered points joined by a connector, and each
  step's number is readable

#### Scenario: The state is not carried by colour alone

- **WHEN** the steps are shown and one of them is done, one is current, one has
  not started, and one has failed
- **THEN** those four states differ by shape as well as by colour

#### Scenario: The indicator is not a control

- **WHEN** the learner tabs through the page and reaches the indicator
- **THEN** the indicator is skipped, and activating it does nothing and causes
  no request

#### Scenario: Too many steps collapse into a summary

- **WHEN** the number of steps exceeds what the row can show without crowding
- **THEN** the indicator collapses to a compact summary that states how many
  steps are done and how many there are in total

#### Scenario: No new figure is invented

- **WHEN** the indicator is shown
- **THEN** its figures are the ones the surrounding surface already holds, and
  nothing is written to the pool

#### Scenario: Without motion the final state is the same

- **WHEN** the indicator is shown with motion off or reduced
- **THEN** it appears directly in the same final state it would reach with
  motion enabled

### Requirement: Modal dialog interrupts and owns focus

When an action needs to interrupt the learner, the workbench SHALL present it
in a modal dialog: a panel over a dimmed page. The dialog SHALL be exposed as
a modal dialog with a title, and the rest of the page SHALL be unavailable to
the pointer and to assistive technology while the dialog is open.

The dialog SHALL own the keyboard while it is open. `Escape` SHALL close it.
`Tab` and `Shift+Tab` SHALL move focus among the dialog's own controls and
SHALL NOT reach the page behind it. Opening the dialog SHALL move focus to the
dialog's first focusable control, which by default is the control that
abandons the action. Closing the dialog SHALL return focus to the control that
opened it; when that control no longer exists, focus SHALL move to the region
that contained it and SHALL NOT be left on the document body.

Closing the dialog SHALL require an explicit action: one of the dialog's own
buttons, or the `Escape` key; a pointer press on the dimmed backdrop SHALL NOT
close it. While the action the dialog asks for is still running, the dialog
SHALL stay open, SHALL mark itself as busy, and SHALL NOT change the value it
was opened with. When the action fails, the dialog SHALL stay open and report
the failure inside itself, and focus SHALL stay inside the dialog.

The confirmations the workbench already asks for — deleting a paper, deleting
a goal, deleting a learning experience, deleting a local Agent conversation,
discarding an unfinished practice round, and rolling back a content batch —
SHALL be asked in this dialog rather than in the browser's own confirmation.
The Agent's inline approval card SHALL remain an inline card in the
conversation and SHALL NOT become a modal dialog.

The dialog's visible size SHALL be adjustable, and with motion off or reduced
it SHALL appear directly in its final state.

#### Scenario: Open a modal dialog

- **WHEN** an action needs to interrupt the learner
- **THEN** a titled modal panel appears over a dimmed page, the page behind it
  is unavailable, and focus moves into the dialog to its first control

#### Scenario: Escape closes the dialog

- **WHEN** the dialog is open and the learner presses `Escape`
- **THEN** the dialog closes and focus returns to the control that opened it

#### Scenario: Focus stays inside the dialog

- **WHEN** the dialog is open and the learner presses `Tab` and `Shift+Tab`
  repeatedly
- **THEN** focus cycles among the dialog's own controls and never reaches the
  page behind the dialog

#### Scenario: The backdrop does not dismiss the dialog

- **WHEN** the learner presses the dimmed backdrop
- **THEN** the dialog stays open and focus stays inside it

#### Scenario: A failure is reported in place

- **WHEN** the action the dialog asks for fails
- **THEN** the dialog stays open, reports the failure inside itself, and keeps
  focus inside the dialog

#### Scenario: The existing confirmations use the dialog

- **WHEN** the learner deletes a paper, deletes a goal, deletes a learning
  experience, deletes a local Agent conversation, discards an unfinished
  practice round, or rolls back a content batch
- **THEN** the confirmation is the workbench's own modal dialog rather than the
  browser's own confirmation, and no request is issued until the learner
  confirms

#### Scenario: The Agent approval stays inline

- **WHEN** the Agent asks the learner to approve an action
- **THEN** the approval remains a card inside the conversation and is not a
  modal dialog

#### Scenario: Without motion the dialog is simply there

- **WHEN** the dialog is shown with motion off or reduced
- **THEN** it appears directly in the same final state it would reach with
  motion enabled

### Requirement: Tool call card is one line

A tool call, command, search, or other deterministic action SHALL be shown in
the conversation as a single-line head carrying a status marker, the action's
name, the time the action took, and a control that opens the detail. The
bounded summary of the action SHALL stay readable without expanding, and the
detail beyond it SHALL be closed by default. The control that opens the detail
SHALL be reachable and operable from the keyboard alone, SHALL report whether
the detail is open, and the opened detail SHALL be a labelled region of its
own.

The time the card shows SHALL come from the activity's own reported evidence.
When no duration is reported, the card SHALL show no duration rather than an
invented one. The action name, the actual state, and any result or impact
SHALL remain the ones the surrounding evidence supports; an impact that is not
known SHALL be shown as unknown and SHALL NOT be inferred from the action's
name. A failed action SHALL be shown by its status marker and a bounded
summary, and SHALL NOT be shown as a sentence coloured as the failure.

The card's visible size SHALL be adjustable, its hit area SHALL be at least 44
by 44 CSS pixels, and with motion off or reduced the running card SHALL appear
directly in its final state.

#### Scenario: One line carries the summary

- **WHEN** a tool call is shown in the conversation
- **THEN** it appears as a single-line head carrying a status marker, the
  action's name and the time it took, with the bounded summary readable below
  it and the detail closed

#### Scenario: Open the detail with the keyboard

- **WHEN** the learner focuses the card's opening control and presses `Enter`
  or `Space`
- **THEN** the detail opens as a labelled region below the head and the
  control reports that it is open, and activating it again closes the detail

#### Scenario: The time comes from evidence

- **WHEN** the activity reports no duration
- **THEN** the card shows no duration rather than an invented one

#### Scenario: Unknown impact stays unknown

- **WHEN** the activity carries no evidence of what it changed
- **THEN** the card states that the impact is unknown and does not infer
  success from the action's name

#### Scenario: Failure is carried by the marker

- **WHEN** the action failed
- **THEN** the card shows the failure through its status marker and a bounded
  summary, and no sentence inside the card is coloured as the failure

#### Scenario: The card is announced

- **WHEN** a learner reaches the card with a screen reader
- **THEN** the opening control is announced with its name and reports whether
  the detail is open or closed

#### Scenario: Without motion the running card is simply there

- **WHEN** a running card is shown with motion off or reduced
- **THEN** it appears directly in the same final state it would reach with
  motion enabled
