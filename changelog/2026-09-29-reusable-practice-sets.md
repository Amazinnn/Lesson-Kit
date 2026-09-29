# Reusable saved practice sets

**日期：** 2026-09-29

## 变化

- 在 `.lessonkit/practice-sets/` 下管理稳定 ID 的可复用试卷（`ps-001`…）。
- 继续复用现有 `practice-set` manifest、check 与 render 规则，不另造组卷引擎。
- 支持列表、创建、读取、改名/替换有序题目、删除、render 与从试卷开始练习。
- 从试卷开始时只把题目顺序复制进唯一 active practice；试卷自身不保存 cursor/progress/attempt。
- 删除试卷不删除任何 `problem_attempts`。

## API

- `GET/POST /practice-sets`
- `GET/PATCH/DELETE /practice-sets/{id}`
- `GET /practice-sets/{id}/render`
- `POST /practice-sets/{id}/start`

## 边界

本变更不增加组卷编辑 UI，也不实现目标绑定。
