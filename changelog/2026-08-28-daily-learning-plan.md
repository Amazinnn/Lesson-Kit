# 每日学习计划主线

- 练习页新增课程目标、阶段目标和今日粗粒度队列；每个队列项提供综合、卡片、判断三种既有练习入口。
- 新增确定性计划底座与 `GET /api/w/{workspace}/plan`，按覆盖、到期、重要性和题型事实生成可重复配量，不依赖 Agent。
- 新增 `POST /api/w/{workspace}/plan/recalculate`，支持限幅的显式计划调整并一次性保存当前计划；每日首次打开同一标签页最多触发一次。
- Agent 或调整失败时保留可用基线，不写入学习日志；计划状态仅在当前页面显示。
- 验证：`263 passed`；`node --check workbench/server/static/workbench.js`；`openspec validate daily-learning-plan --strict`；`openspec doctor`；两道 dmath/ch06 pool guard 均 PASS。
