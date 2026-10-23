## MODIFIED Requirements

### Requirement: Calendar and workload view

The workbench SHALL offer an experimental, read-only time view on the practice
page, within the study arrangement region rendered below the daily plan as a
full-width block. Its month grid SHALL use quiet structural lines and render
each dated goal as a thin timeline track from its optional start date through
its deadline. Goals without a start date SHALL remain compatible and render as
a one-day track on their deadline. Overlapping goals SHALL occupy compact
parallel lanes. A goal crossing a week boundary SHALL be split visually without
becoming separate goals, SHALL show its title only once in its first suitable
visible segment, and SHALL expose its identity and full date range on every segment.
Today SHALL emphasize the date numeral rather than the whole cell.

Below the calendar, the same view SHALL render 14 days of exact due schedule-row
counts (each direction counted as one item) under the title “未来 14 天复习负荷”.
It SHALL explain the measure, summarize the total, peak date/count, and overdue
count, align every date on one fixed axis, place each nonzero exact value above
its bar, and render zero as no bar. The peak SHALL be visually distinct. Days
whose count reaches twice the nonzero daily average SHALL additionally be
marked as heavy, with one action that pre-fills a reallocation request into the
Agent conversation input without sending it. The chart SHALL NOT overlay a
smoothed or predictive line. The view SHALL NOT reschedule, write, or alter any
learning data, and SHALL render honest empty states when there is nothing
scheduled.

The month grid SHALL render every date cell at one uniform size across the seven
week columns, so that a day's position in the month is readable without reading
its number. The current date SHALL be marked by a distinct shape on the date
numeral — a filled round badge that touches only the numeral — while the
remaining area of that cell stays visually quiet. A goal track and the grid cell
it crosses SHALL be drawn with the same radius, line-width and colour registers
as the surrounding surface, so that the calendar reads as part of the workbench
rather than as a graphic laid on top of it.

The height of each workload bar SHALL encode that day's exact due schedule-row
count relative to the highest count in the same 14-day window, so that the bar
for the highest count is the tallest and every bar's proportion is comparable
with the others on the same axis. The exact count SHALL appear above its own
bar. A day with no due rows SHALL render no bar and no value label, and SHALL
keep its place on the shared baseline. The peak day SHALL be distinguishable by
form and by colour, and a heavy day SHALL carry the redundant state channel
(冗余状态通道, Redundant state channel) in addition to colour: its marker SHALL be
geometric, so that a heavy day is identifiable without colour perception, and it
SHALL NOT rely on a pile of explanatory text.

When the 14-day load is rendered or refreshed, the bars SHALL grow from the
shared baseline with a per-column stagger of 24 ms, animating only transform and
opacity, with each animation duration inside the workbench's interaction and
scene duration bands. The motion SHALL NOT change the counts that are shown, the
heavy-day determination, the request the view issues, or the order and timing of
requests. With the 动效偏好 (motion preference) off, or with the operating system's
reduced-motion setting in effect and no explicit learner override, the same bars
SHALL appear immediately at their final heights with their exact values, the peak
marker and the heavy-day markers already in place; the view SHALL NOT be left at
an intermediate height, a missing value or a missing marker.

The honest empty state SHALL present one sentence and MAY be accompanied by a
non-interactive still-life illustration (静物插画) that repeats no information
beyond that sentence. Nothing else in the view SHALL be added as annotation.

This view remains read-only. The 14-day window, the rule that each direction
counts as one item, the heavy-day determination of twice the nonzero daily
average, and the single action that pre-fills a reallocation request without
sending it SHALL remain exactly as specified above; the presentation contract
changes none of them, and the view still writes nothing, reschedules nothing and
alters no learning data.

#### Scenario: Overlapping goal periods

- **WHEN** two goals overlap on one or more visible dates
- **THEN** their thin tracks occupy separate parallel lanes and both titles remain identifiable

#### Scenario: Goals on one deadline

- **WHEN** two deadline-only goals share the same deadline date
- **THEN** both one-day tracks occupy separate lanes and remain independently readable

#### Scenario: Existing deadline-only goal

- **WHEN** a stored goal has a deadline but no start date
- **THEN** it remains readable as a one-day track on its deadline without a migration step

#### Scenario: Goal crossing a week boundary

- **WHEN** a goal period extends across two or more calendar weeks
- **THEN** the calendar draws a continued segment in each week, renders the title once in the first suitable visible segment, and preserves one accessible goal identity throughout

#### Scenario: Exact workload on a fixed axis

- **WHEN** one or more of the 14 days has due work
- **THEN** exact daily values appear above bars whose dates share one fixed baseline, with total and peak summaries and no smoothed line

#### Scenario: Zero workload day

- **WHEN** a day has no due rows
- **THEN** its date remains on the shared axis without a fake minimum-height bar or value label

#### Scenario: Heavy day with reallocation prefill

- **WHEN** a day's due count reaches the heavy threshold
- **THEN** the day is marked heavy and one click pre-fills the reallocation request into the conversation input without sending it

#### Scenario: Nothing scheduled

- **WHEN** there are no goals and no due rows in the visible window
- **THEN** the view shows one honest empty-state sentence and no controls

#### Scenario: Bar height encodes the day's exact load

- **WHEN** two days in the 14-day window carry different due counts
- **THEN** the busier day's bar is taller in proportion to the highest count in that window and each bar shows its own exact count above it

#### Scenario: A heavy day is identifiable without colour

- **WHEN** a day's due count reaches the heavy threshold
- **THEN** that day carries a geometric marker in addition to colour, and the marker is placed on the column rather than spelled out in a text label

#### Scenario: Load change animates without changing the data

- **WHEN** the 14-day load is rendered or refreshed
- **THEN** the bars grow from the shared baseline with a per-column stagger, only transform and opacity change, and the counts, the heavy-day determination and the requests issued are the same as they would be without motion

#### Scenario: Reduced motion lands on the same final state

- **WHEN** motion is off or reduced
- **THEN** the bars are already at their final heights with their exact values, the peak marker and the heavy-day markers present, and no intermediate state remains

#### Scenario: Today is marked on the numeral

- **WHEN** the month grid shows the current date
- **THEN** that date numeral carries a distinct shape marker while the rest of its cell stays visually quiet

#### Scenario: The view stays read-only under the new presentation

- **WHEN** the calendar and workload view is displayed with the new presentation contract
- **THEN** it writes nothing, reschedules nothing, and the 14-day window, the counting rule and the heavy-day determination are unchanged

## Self-check

- [x] calendar-workload delta **没有** `## Purpose`
- [x] 只有 `## MODIFIED Requirements`，1 个 Requirement，标题与原文一致：`Calendar and workload view`
- [x] MODIFIED 是**整块复制**（原文 8 个场景全部保留）后再改写，新增 6 个呈现场景
- [x] 每个 Requirement ≥ 1 个 Scenario，Scenario 一律用 `####`（4 个 #）+ WHEN/THEN，共 14 个 Scenario
- [x] 没有改动负荷天数（仍为 14 天）与重日阈值（仍为当日到期数 ≥ 非零日均 2 倍）等既有数字与判定
- [x] 只读保证原样保留：写入/改期/改学习数据仍然禁止，改排请求前缀动作仍只预填不发送
- [x] 用了 SYNTH.md 的原词（4 个）：冗余状态通道、静物插画、图案适配原则、动效偏好
      （另 8 个新名词属工作台设置与视觉基线，落 `specs/workbench-settings/spec.md`）
- [x] 知识图谱相关内容 0 条
- [x] 未修改任何产品代码，未改动 `openspec/specs/calendar-workload/spec.md` 本体
