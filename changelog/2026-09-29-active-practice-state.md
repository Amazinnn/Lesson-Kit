# One active practice per workspace

**日期：** 2026-09-29

## 变化

- 新增 workspace 当前练习的 singleton SQLite 状态：一组固定、有序的 problem/card item，加一个可恢复 cursor。
- 同一 workspace 默认拒绝创建第二个未完成练习；只有显式 `replace` 才能覆盖执行状态。
- 覆盖或完成练习只清除执行状态，不删除任何 `problem_attempts`。
- 浏览器 answer 与 legacy practice result 可携带 `practice_position`，在同一个 SQLite transaction 中写 attempt 并推进 active practice。
- “不会”继续复用既有 `stuck` 学习语义，不新增第二套 skip/unknown 状态。
- 新增 `GET/POST/PATCH/DELETE /api/w/{name}/practice/current`。

## 边界

本变更只建立执行状态与 API；练习页仍由现有前端驱动。恢复 UI、固定题量与启动冲突交互留给下一层变更。
