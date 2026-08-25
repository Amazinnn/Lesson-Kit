# 原生力导向知识图谱

## 最终行为

- 知识图谱使用零依赖力导向模拟，根据语义边执行弹簧牵引、节点斥力、标签碰撞、中心引力、阻尼与稳定停止。
- 正式关系与既有 `related_kp_ids` 形成边；反向重复边合并，共同正式题只增强已有边。
- 图谱模型为节点返回正式题数，为边返回显式强度、共同题数和牵引权重。
- 节点使用圆形和外置名称；圆半径随正式关联题数增长，学习状态由颜色表达。
- 搜索与状态筛选会重建布局；节点拖拽、画布平移、滚轮/按钮缩放和适应画布均在内存中完成。
- 减少动态效果环境同步计算稳定布局并一次绘制，不保存坐标或浏览记录。

## 验证证据

- `python -m pytest tests -q`：181 passed。
- `node --check workbench/server/static/graph-physics.js`：通过。
- `node --check workbench/server/static/workbench.js`：通过。
- `openspec validate force-directed-knowledge-graph --strict`：通过。
- `:3081` 真实模型：28 个节点、30 条去重边、28 个节点均有正式题计数，最大题数 77，全部边具有牵引权重。
- Chrome 真实页面验收：动态图谱和 reduced-motion 稳定布局均完成渲染；节点大小、外置标签、关系线、状态色和自动适应画布可见。
