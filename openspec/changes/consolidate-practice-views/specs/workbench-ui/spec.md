## REMOVED Requirements

### Requirement: Review page with card sessions

**Reason**: 第 4 导航页与记录在案的三页导航决定相抵触，其功能合流回练习页
（统一「今天」列表 + 模式内卡片轻会话）。到期提醒、卡片会话与时间安排的
要求分别移入练习页与 review-workbench 的需求文本。

## ADDED Requirements

### Requirement: Practice page today list and time view

The practice page SHALL show one merged today list ordered by plan weight:
each row SHALL carry a readable name, a human-readable reason (coverage low,
due review with relative days, or a last-result phrase), and a direct action;
due schedule rows SHALL appear in this list with their own reasons instead of
on a separate page. The practice page SHALL also show the time view section
(goal deadline month grid and 14-day workload bars) parallel to the study
arrangement section. Scheduler parameters SHALL NOT be displayed, and the
scope-selection empty state SHALL offer inline guidance rather than pointing
to another page.

#### Scenario: A due knowledge point appears with a human reason

- **WHEN** a schedule row is overdue by three days for a knowledge point in
  today's scope
- **THEN** the merged today list shows that row with a reason phrase such as
  `可以复习 · 拖了 3 天` and a direct handoff action

#### Scenario: Time view sits beside the study arrangement

- **WHEN** the learner opens the practice page on a wide viewport
- **THEN** the study arrangement and the time view render as parallel
  sections, stacking vertically on narrow viewports
