# review-page Specification

> **DEPRECATED 2026-08-29** — 本能力已被 `consolidate-practice-views` 取代：
> 到期提醒回归练习页合流列表（review-workbench「Forgetting-curve scheduling
> as background」的原始设计位置），方向卡片会话改为闪卡/判断模式内的可选
> 轻会话，第 4 导航页移除。其中 `pull.include_ids`、`feedback.direction`、
> `queries.review_overview` 等 API 要求已收编进 review-workbench 能力，
> 实现保留。

## Purpose

Turn accumulated schedule rows into a reminder surface: a review page that
groups due items by date with type and direction badges, hands off to the
existing practice paths, and runs directional card sessions that write
per-direction schedule rows. The page reminds only - it never locks, hides,
or gates items, and it never exposes scheduler parameters.

## Requirements

### Requirement: Review page as a reminder surface

The workbench SHALL provide a review page listing due schedule rows grouped by
due date (overdue/today, next 7 days, later collapsed to a count). Each row
SHALL show a readable label, a type badge, a direction badge when the row has
a non-empty direction, and a `可以复习` reminder; the page SHALL NOT display
scheduler parameters (ease, interval, repetitions) and SHALL NOT lock, hide,
or gate any item. The page SHALL cap the rendered list (default 100 rows) and
report the remainder as a count.

#### Scenario: Overdue knowledge point

- **WHEN** a knowledge-point schedule row is three days past its due date
- **THEN** it appears in the overdue group with its label and an
  `已过期 3 天` relative note, without any scheduler parameter values

#### Scenario: No due items

- **WHEN** the schedule has no due rows
- **THEN** the page shows an honest empty state with one action pointing to
  the practice page

### Requirement: Review handoff paths

From the review page, a knowledge-point-level due row SHALL hand off through
the existing scope handoff to the practice page, and a problem-level due row
SHALL start practice restricted to that problem via the pull `include_ids`
filter. Both paths SHALL reuse the existing practice session semantics.

#### Scenario: Practice one due problem

- **WHEN** the learner starts a due problem row from the review page
- **THEN** the practice session pulls only that problem within its
  knowledge-point scope and follows the chosen practice and rating modes

### Requirement: Directional card session

The review page SHALL offer a card session over due rows with a non-empty
direction: each card shows the front for its direction, reveals the other
side, and records the chosen 1–5 rating to that row's schedule key
`(item_type, item_id, direction)` through the feedback path. Cards of a
knowledge point SHALL show `contrasts`/`variant_of` neighbors alongside. The
session state SHALL be tab-scoped and restorable on refresh, and finishing
SHALL show an inline summary instead of creating a rating queue.

#### Scenario: Review a reverse-direction card

- **WHEN** the learner completes a reverse card with rating 4
- **THEN** the reverse schedule row advances while the forward row and other
  items are unchanged, and the signal/event semantics stay as for any rating

#### Scenario: Refresh mid-session

- **WHEN** the learner refreshes the tab during a card session
- **THEN** the session resumes at the same remaining cards without
  manufacturing records
