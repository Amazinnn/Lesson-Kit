# graph-state-filter-clusters 任务

## 1. 规格

- [x] 定义固定状态、多选并集、淡出/复现和分群边界
- [x] `openspec validate graph-state-filter-clusters --strict` 通过

## 2. 实现

- [x] 工具栏提供四状态多选与一键清除
- [x] 物理层提供确定性状态分群目标
- [x] 排除节点与连线淡出，保留节点移动到分群中心
- [x] Agent 图谱上下文携带多选状态

## 3. 交付

- [x] 补物理层、浏览器和上下文测试
- [x] 同步词汇表、产品手册、架构、动作图谱和 changelog
- [x] 仓库级检查全绿并归档 change
