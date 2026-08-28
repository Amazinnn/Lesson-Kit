# Task 1 报告：练习范围与每日计划纠偏

日期：2026-08-28

## 修改文件

- `openspec/changes/correct-practice-scope-and-daily-plan/.openspec.yaml`
- `openspec/changes/correct-practice-scope-and-daily-plan/proposal.md`
- `openspec/changes/correct-practice-scope-and-daily-plan/design.md`
- `openspec/changes/correct-practice-scope-and-daily-plan/tasks.md`
- `openspec/changes/correct-practice-scope-and-daily-plan/specs/daily-learning-plan/spec.md`
- `openspec/changes/correct-practice-scope-and-daily-plan/specs/workbench-ui/spec.md`
- `openspec/changes/correct-practice-scope-and-daily-plan/specs/review-workbench/spec.md`
- `docs/REQUIREMENTS.md`
- `docs/frontend-optimization-plan.md`
- `docs/FUTURE-DEVELOPMENT-NOTES.md`（仅追加纠偏补充，保留既有原话）
- 本报告文件

本 Task 未修改 Python、JavaScript、CSS、数据库、pipeline、pool 脚本或
`lessonkit.py`。现有 `openspec/changes/archive/` 未删除或改写。

## 验证

命令：

```text
openspec validate correct-practice-scope-and-daily-plan --strict
```

输出：

```text
Change 'correct-practice-scope-and-daily-plan' is valid
```

## 纠偏覆盖

- 知识图谱/列表是唯一显式练习范围；Agent 仅能在明确练习意图下替换。
- 无范围显示空交接状态；弱项、全池和每日计划不隐式抓题。
- 会话固定一种模式；Flash Card / Yes-No 只有显式元数据和可用题目时才可用，未宣称已实现。
- 真实长期/阶段目标卡与独立最多三项粗粒度今日队列；无目标不虚构目标、时长或掌握度。
- 选择、导航、草稿、跳题、计划查看保持零写入。

## 遗留疑问

- 代码实现、API 具体字段和浏览器验收属于后续 Task 2–4，本报告未提前判断其完成状态。
- Flash Card / Yes-No 的正式内容元数据字段仍由实现任务确定；本轮只固定“显式标注后方可用”的边界。

## 实施补充（2026-08-28）

已实现并验证显式知识点范围、单一内容模式、无回退拉题、真实目标卡、最多三项今日队列和版本化计划读取。完整测试结果为 `270 passed`，浏览器生产脚本测试为 `34 passed`，严格 OpenSpec 校验通过。

尚未实现的是“Agent 在明确练习意图下直接替换当前标签页选择”。该能力涉及服务端会话结果与浏览器 `sessionStorage` 的明确交接，继续保留为活动变更中的未勾选任务，不通过解析自然语言回复来猜测。
