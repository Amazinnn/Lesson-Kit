# 每日学习计划主线

- 练习页新增课程目标、阶段目标和今日粗粒度队列；每个队列项提供综合、卡片、判断三种既有练习入口。
- 新增确定性计划底座与 `GET /api/w/{workspace}/plan`，按覆盖、到期、重要性和题型事实生成可重复配量，不依赖 Agent。
- 新增 `POST /api/w/{workspace}/plan/recalculate`，支持限幅的显式计划调整并一次性保存当前计划；每日首次打开同一标签页最多触发一次。
- Agent 或调整失败时保留可用基线，不写入学习日志；计划状态仅在当前页面显示。
- 验证：`263 passed`；`node --check workbench/server/static/workbench.js`；`openspec validate daily-learning-plan --strict`；`openspec doctor`；两道 dmath/ch06 pool guard 均 PASS。

## 练习范围纠偏（2026-08-28）

- 知识列表与知识图谱现在共享当前标签页内的显式知识点选择；阅读、导航和查看节点不会暗中改变范围。
- 直接进入练习页且没有范围时只显示交接空状态，不再从薄弱项、全题池或今日计划自动拉题。
- 每轮必须选择且只选择综合题、Flash Card、Yes/No 之一。未显式标记的既有题只进入综合题；其他模式没有合格内容时不回退。
- 长期与阶段目标只展示真实目标卡；今日队列最多三项，不再虚构“完成当前课程”、默认时长或掌握度。
- 队列项目只负责把知识点范围交给练习页，题型仍在启动卡选择。
- Agent 在明确练习意图下直接替换浏览器选择的通道尚未接入，因此 OpenSpec 对应任务保持未完成，不作假完成声明。

验证：`270 passed`；Node 交互测试 `34 passed`；OpenSpec strict validation 通过；`:3081` 三个页面 HTTP 冒烟通过。
