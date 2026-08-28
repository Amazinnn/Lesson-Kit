# calendar-workload 提案

## Why

长期与阶段目标目前只有练习页上的两张卡片，截止日期缺少一个「什么时候该完成什么」
的空间感；同时 `review_schedule` 里每天有多少到期项从未被可视化，过载只有
做了才知道。既有记录（daily-learning-plan / complete-learning-workbench）都把
「目标日历 + 任务量曲线」列为既定方向、前端形态待定。UX 走查确认练习页顶部
已较满，这个视图需要自己的位置。

## What Changes

- 复习页内新增「时间安排」区块（不新增导航页）：本月月历格按截止日摆放
  目标卡（可重叠、绝不合并为一张总卡），今天高亮。
- 未来 14 天到期项数柱状条（`review_schedule.due_at` 只读直方图），
  高于日均 2 倍的日期标记为「偏重」，行内提供一键把
  「最近几天任务偏重，帮我重排一下」预填进右侧对话输入框；
  不做任何自动重排。
- 新端点 `GET /api/w/{name}/calendar`：返回目标列表与 14 天直方图，
  纯读取零写入。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `daily-learning-plan`: 新增「日历与工作量视图」需求（只读、实验性、
  不改变计划与学习写入语义）。
- `workbench-ui`: 复习页包含时间安排区块的需求（目标卡/月历/曲线/预填）。

## Impact

改动限于 `workbench/`（queries/api/pages/JS/CSS）与测试、OpenSpec。
零学习写入、零调度改动；目标读取复用既有 goals 存储。数据不足时（无目标、
无到期项）渲染诚实空状态。实验性定性沿用既有记录：不追求排程优化，
只提供看得见的密度。
