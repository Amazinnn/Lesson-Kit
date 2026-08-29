## REMOVED Requirements

### Requirement: Directional card practice for memory recall

**Reason**: 方向卡 UI 全拆（无卡片页、无系统导向会话，DISCUSSION-RECORD
专题 19 第 4 条）；其数据级承诺由新需求「Directional schedule entries」
以更窄的形式继承（每方向独立调度键），API 语义由「Directional feedback
key」继承。

## MODIFIED Requirements

### Requirement: Forgetting-curve scheduling as background

The system SHALL maintain per-item scheduling state (repetitions, ease,
interval, due date) updated on practice results. Scheduling SHALL influence
ordering and on-demand suggestions only; it SHALL never hide, lock, or refuse
items, and due items SHALL NOT be surfaced as a standing due list or through a
separate review page. Due knowledge points SHALL be reachable as on-demand
suggestions inside the practice page's staged-list flow, each with at most one
human-readable reason phrase.

#### Scenario: Due items are reminded

- **WHEN** the workspace home is opened with due schedule rows whose knowledge
  points are not currently selected
- **THEN** the practice page's suggestion entry shows their count, and
  expanding it lists each due knowledge point with one human reason phrase,
  never raw scheduler parameters

#### Scenario: Schedule state updates after practice

- **WHEN** a problem result is recorded
- **THEN** its repetitions, ease, interval, and due date are updated in the
  scheduling table

## ADDED Requirements

### Requirement: Directional schedule entries

Each direction (for example English-to-Chinese and Chinese-to-English) of a
memory-recall knowledge point SHALL be a distinct learning action with its own
schedule entry, and practicing one direction SHALL NOT advance the other. The
workbench SHALL NOT provide a standing card-session page or system-initiated
card prompts; card-shaped UI for directional rows is deferred until real usage
exists.

#### Scenario: Two directions schedule independently

- **WHEN** a memory-recall knowledge point is practiced in both directions
- **THEN** each direction has its own schedule state and due date, and
  practicing one direction does not advance the other

#### Scenario: No system-initiated card session

- **WHEN** the learner starts any practice mode with due directional rows in
  scope
- **THEN** the workbench starts the requested mode directly without offering
  or requiring a card session

### Requirement: Scoped include filter

A scoped pull MAY carry `include_ids`; returned problems SHALL then be
restricted to those identifiers within the requested knowledge-point scope.
Combining `include_ids` with the unscoped `all` mode SHALL be rejected, and
the shortage report SHALL keep reflecting the remaining unfilled demand.

#### Scenario: Pull one due problem

- **WHEN** a scoped pull carries `include_ids` with one durable problem id
- **THEN** only that problem is returned

#### Scenario: Include filter with unscoped all mode

- **WHEN** a pull carries `include_ids` together with `mode: all`
- **THEN** the request is rejected with 400 and nothing is pulled

### Requirement: Directional feedback key

Feedback MAY carry an optional `direction`; when present, the rating SHALL
update the schedule row keyed by `(item_type, item_id, direction)` while
signal, event, progress, and current-state semantics SHALL remain unchanged.

#### Scenario: Reverse card rating

- **WHEN** feedback for a knowledge point carries `direction: reverse` with
  rating 4
- **THEN** only the reverse schedule row advances and the forward row stays
  unchanged
