## Why

当前用户可见的中文术语是「自评」，但这条记录已经不只是学习者给自己打分：Agent 会代学习者转录、批改并写入 1–5 评分。术语与实际所有权不一致。同时，Agent 只能修改自己记录的最近一条 Attempt，不能修改用户在同一道题上写下的同一行评价，也没有 CLI 的列表/删除入口。用户要求 Agent 与用户编辑同一行评价，唯一限制是写入前必须先读取当前值。

## What Changes

- 用户可见中文术语「自评」统一改为「评价」；`rating`、`self_rating`、`feedback_events.rating/note`、DOM id、localStorage key、API 字段和英文 spec 术语保持不变。GLOSSARY 保留「自评」为旧称别名。
- `lesson-kit feedback` 扩展为 `add` / `list` / `get` / `update` / `delete`，保持旧的无 action 调用兼容。
- `feedback update` / `delete` 对任何来源、任何 item 类型（problem / kp / card）开放，包括浏览器写的和 Agent 写的评价。
- 写前读取是硬约束：`update` / `delete` 必须带 `--expected-rating` 和 `--expected-note`（从 `feedback get` 取得）。值不匹配时返回 409、零写入；`none` 表示该行没有评分，空备注用空字符串。
- `update` 原位改写 `feedback_events.rating/note`；`delete` 硬删除该行。两者都不重放信号、当前状态、进度、排期。
- `attempts correct` 保留为“整条 Attempt 替换并精确撤回/重算投影”的路径；只改评价行走 `feedback update/delete`。
- Agent 可以在用户要求记录、导入或管理评价时自行选择或修改评分，不要求用户先给 1–5；普通教学问答仍不静默写入。
- `feedback add --attempt-id` 遇到该 Attempt 已有评价时拒绝并返回现有 event id，提示改用 `update`。
- 所有注入给 Agent 的提示词与按需契约同步更新。

## Capabilities

### New Capabilities

无。本 change 扩展既有反馈、记录管理与设置文案。

### Modified Capabilities

- `agent-assisted-practice-records`：新增评价记录的列表、新增、修改、删除能力；跨 writer 编辑同一行；写前读取与硬删除语义。
- `review-workbench`：`Flexible feedback` 明确同一行评价可由学习者或 Agent 编辑；expected 值做乐观并发；改/删不重放投影。
- `ai-teacher-bridge`：Agent 可在用户要求记录或管理评价时自行评分/改分，改前必须读取。
- `workbench-ui`：设置视图中的「关闭自评」文案改为「关闭评价」。

## Impact

- UI：`workbench/server/pages.py`、`static/practice-flow.js`、`static/paper-practice.js`、`server/records.py`、`domain/mastery.py`、预览 fixture 与相关测试断言。
- CLI/Data：`workbench/cli/main.py`、`workbench/data/pool.py`、新增 `workbench/data/evaluations.py`。
- Agent 契约：`workbench/bridge/agent_contracts.py`、`workbench/bridge/conversations.py`。
- 文档：`docs/GLOSSARY.md`、`docs/DATA_MODEL.md`、`docs/PRODUCT-MANUAL.md`、`docs/REQUIREMENTS.md`、`docs/ARCHITECTURE.md`、`docs/ACTION-GRAPH.md` 与 `docs/action-graph/L3`。
- 不新增表/列；不改英文标识；不重写 archive/changelog/audit 历史文档。
