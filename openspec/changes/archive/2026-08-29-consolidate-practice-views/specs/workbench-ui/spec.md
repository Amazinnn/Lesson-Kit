## REMOVED Requirements

### Requirement: Review page with card sessions

**Reason**: 第 4 导航页与记录在案的三页导航决定相抵触；到期以练习页候选区的
按需建议形式出现（workbench-ui 新增需求），方向卡 UI 全拆（调度语义保留在
review-workbench）。

## ADDED Requirements

### Requirement: Practice page staged list and on-demand suggestions

The practice page SHALL show one staged practice list that is a row view of the
current explicit knowledge-point selection: each row SHALL carry the knowledge
point name and a remove action, and removing a row SHALL deselect that point
with the knowledge list, graph, and practice page kept in sync. The page SHALL
offer one on-demand suggestion entry labeled with the current suggestion count;
expanding it SHALL show candidate rows of `knowledge point name · one phrase ·
join action`, sourced from the daily plan queue and due scheduling state,
deduplicated to one row per knowledge point with at most one human-readable
reason phrase (overdue phrases take precedence over plan phrases). Knowledge
points already in the selection SHALL NOT appear as candidates, and candidate
rows SHALL NOT show badges, dates, numbers, or raw scheduler parameters. The
practice page SHALL also show the time view section (goal deadline month grid
and 14-day workload bars) parallel to the study arrangement section, stacking
below it on narrow viewports. Empty states SHALL be one sentence with at most
one action.

#### Scenario: A due knowledge point appears as an on-demand suggestion

- **WHEN** a schedule row is overdue by three days for a knowledge point that
  is not currently selected
- **THEN** expanding the suggestion entry shows that point with a single
  reason phrase such as `拖了 3 天` and a join action, with no badge, date, or
  scheduler parameter

#### Scenario: Joining a suggestion stages it for practice

- **WHEN** the learner joins a suggested knowledge point
- **THEN** it appears in the staged practice list, disappears from the
  suggestions, and the suggestion count decreases by one

#### Scenario: Removing a staged row deselects it everywhere

- **WHEN** the learner removes a staged row on the practice page
- **THEN** the knowledge point is deselected and its checkbox in the knowledge
  list and graph is unchecked in sync

#### Scenario: Time view sits beside the study arrangement

- **WHEN** the learner opens the practice page on a wide viewport
- **THEN** the study arrangement and the time view render as parallel
  sections, stacking vertically on narrow viewports

#### Scenario: Nothing staged and nothing to suggest

- **WHEN** the learner opens the practice page with no selection and no plan
  or due suggestions
- **THEN** the staged list shows one sentence with one action, and the
  suggestion entry states there is nothing to add
