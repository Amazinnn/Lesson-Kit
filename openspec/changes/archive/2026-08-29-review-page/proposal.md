# review-page 提案

## Why

调度数据一直在积累（`review_schedule` 现含 kp/problem/方向三个维度的到期行），
但学生没有任何一个能看到「今天该复习什么」的地方——到期信息只以
「复习已到期」几个字挤在练习页队列的原因文案里。UX 走查（2026-08-29）同时
发现练习进行中页面不聚焦、到期项没有直达入口。本变更把到期复习变成
一个提醒面 + 一条最短的动手路径，并让「方向」这个调度维度第一次可见、可用。

## What Changes

- 新增第 4 个导航页「复习」（`/w/{name}/review`）：到期项按 逾期/今天/
  未来 7 天 分组列表，行内只有标签、类型徽标、方向徽标与 `可以复习` 提示，
  绝不展示 ease/间隔等调度参数（遵守 action-oriented reminders 红线）。
- 两条动手路径：知识点级到期项经既有 queue-handoff 写入选区去练习；
  题目级到期项经 pull 新增的 `include_ids` 直接练指定的题。
- 定向卡片会话（集成在复习页内，不新增第 5 个页面）：到期方向行进入
  正面→揭示→1–5 自评的卡片流，按 `(item_type, item_id, direction)`
  写调度；`contrasts`/`variant_of` 邻居并列展示；会话状态 tab 级可恢复。
- API additive：`due` 返回 `direction` 并支持 `limit`；`pull` 支持可选
  `include_ids`；`feedback` 支持可选 `direction`（缺省 `""`，现有调用
  与语义全部不变）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `review-workbench`: 新增「复习页提醒面」「定向卡片会话」需求；
  pull 增加可选 include 过滤；feedback 可携带方向。
- `workbench-ui`: 导航从三入口扩为四入口（练习/知识点/复习/知识图谱），
  新增复习页布局与卡片会话需求。

## Impact

改动限于 `workbench/`（queries/api/pages/JS/CSS）、`pool_schema` 零变化
（direction 列已存在）、测试与 OpenSpec。学习写入语义 additive（新参数
全部可选且缺省为现状）；调度仍只影响排序、永不锁定（提醒面红线）。
兼容边界：旧客户端不传新参数时行为与今天完全一致。
