# 灵动知识图谱与开发阶段冻结

- 六起点分量布局现在只生成确定性种子，31 个真实节点随后进入同一个无边界弹性力场；拖拽响应不再被分量边界截断。
- 语义边长由既有 `attraction` 映射为 72–144px 间隙并叠加端点半径，圆形碰撞独立保留至少 24px 净空；标签不再撑大物理节点。
- 节点支持边缘自动平移、任意坐标拖放和页面内软锚；fit 只调整镜头。聚焦原地展开一跳和二跳关系。
- 默认只显示排序后的 6 个标签，缩放后显示 12 个或全部；搜索、悬停和聚焦覆盖限制。
- 稳定图以不超过 30fps、4px 的确定性呼吸继续轻微运动；后台和 reduced-motion 停止持续动画。
- 图谱占满中栏剩余高度，无遮挡边保持直线，遮挡边才使用浅曲线。坐标、软锚、导航和动画均不写入学习记录。
- 本变更归档后冻结主动功能开发；后续只响应真实学习使用中发现的问题。

## 验证

- `python -m pytest tests -q`：255 passed。
- `node --check workbench/server/static/workbench.js` 与 `graph-physics.js`：通过。
- `openspec validate living-knowledge-graph-phase-close --strict` 与 `openspec doctor`：通过。
- `extract-problems` 与 `problem-set` 两道 dmath/ch06 guard：PASS。
- 重启 `:3081` 后真实图谱页返回 200；实时模型返回 31 节点、35 边，全部节点包含既有 `importance`。
