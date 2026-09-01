# animate-graph-metric-projections 任务

## 1. 规格

- [x] 定义投影大小、径向顺序、色谱和减少动态效果行为
- [x] `openspec validate animate-graph-metric-projections --strict` 通过

## 2. 实现

- [x] 图谱物理层支持目标位置、目标半径与连续过渡
- [x] 投影切换保留节点元素、选择和焦点，不再整图重建
- [x] 四种视图使用可辨识的蒙德里安色谱
- [x] reduced-motion 直接绘制稳定终态

## 3. 验证与文档

- [x] 补物理层和浏览器交互测试
- [x] 同步词汇表、产品手册、架构与动作图谱
- [x] 仓库级检查全绿并归档 change
