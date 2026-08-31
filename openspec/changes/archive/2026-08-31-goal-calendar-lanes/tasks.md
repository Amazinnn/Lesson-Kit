# goal-calendar-lanes 任务

## 1. 规格

- [x] 定义「目标时间跑道」并补 calendar-workload / ai-teacher-bridge delta
- [x] `openspec validate goal-calendar-lanes --strict` 通过

## 2. 实现

- [x] goals.json / CLI / 表单 / Agent 助填支持可选 start_date
- [x] 月历按周切段并为重叠目标分配并列跑道
- [x] 阶段目标、长期目标与逾期状态有清楚且不过度的视觉区分
- [x] 数据、CLI、页面、交互测试覆盖旧目标兼容与重叠分轨

## 3. 交付

- [x] 更新 PRODUCT-MANUAL、ACTION-GRAPH 与交接记录
- [x] 跑仓库级检查并归档 change
