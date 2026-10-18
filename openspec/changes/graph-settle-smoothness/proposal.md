## Why

结构投影的落座过程有四处可测的缺陷，全部用真实载荷量过
（`dmath` 31 点 / 35 边，`c02` 86 点 / 0 边，脚本见 tasks.md）：

1. **首帧瞬移**：种子螺旋离每个点自己的引导位置 p50 666px（最大 1135px），而
   第一帧与它之间的唯一机制是 `enforceHierarchyBands`，它把 `y` 直接设成
   `guideY ± band`（band 默认约 49px）。实测首帧瞬移 **953px**（dmath）/ **1074px**（c02）。
2. **舞台在替物理做决定**：把电荷强度从 200 提高 56 倍到 11200，平均边长只从 638
   动到 758，包围盒卡在 1636——而舞台的可用宽度是 1560。绑定的约束是边界钳制，
   不是力场。
3. **每帧位移顶格**：速度钳制 7px/tick 让最活跃的 5% 节点长期顶格（实测 p95 = 7.0）。
4. **重开页面就重播一遍**：ADR 0028 把种子坐标当锚点恢复、`reheat(.34)`、两帧后
   释放锚点、再 `reheat(.28)`——为了回到学习者已经看过的那张图，硬跑三轮运动。

这四条都不改变任何语义（层级、可读性下限、拥塞、端口路由、四种投影），只改变
"怎么落座"和"落座要不要重播"。

## What Changes

- **落座起点**从种子螺旋改为引导网格本身；`enforceHierarchyBands` 的带宽随 α 收紧
  （α 高时 ×5，α 归零时回到原值），于是重新求解（拖拽、切投影、调重力）也有余量。
- **电荷**从 O(n²) 点对循环换成 Obsidian 的 Barnes–Hut（`visitCharge` 口径：
  `d² · θ² ≥ size²` 折叠子树，`θ = 0.9`，`distanceMin2 = 30`）。强度按"与旧式在实测
  典型点距处相等"标定，并使阻尼变化同步重标。
- **积分器**改用 Obsidian 的 `complete(x, y, 0.6)`：阻尼 0.6，**取消速度钳制**。
- **α 冷却**改用 Obsidian 的速率 `1 − 0.001^(1/300)`。
- **舞台**从布局硬约束降级为坐标盒：边界钳制移除；`graphFit()` 本来就按节点范围拟合，
  `.graph-edges` 本来就是 `overflow: visible`，故无观感回归。
- **恢复的布局**（本地布局种子）**被采纳而不是重新求解**：坐标照旧经锚点送入 Worker，
  Worker 随即丢弃锚点并停机。部分命中（有缓存点、有无缓存点）仍走原求解路径。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-ui`: 结构投影的落座起点、层级带松紧、电荷律、积分器与冷却速率。
- 本地布局种子的恢复语义（`docs/GLOSSARY.md`「本地布局种子」条目随之修订）。

## Impact

- 只改 `workbench/server/static/graph-physics-core.js`、`graph-physics.js`、
  `graph-physics-worker.js` 三个文件。
- **不动**：`hierarchyLevels`、`readabilityFloor`、`resolveCongestion`、
  `congestionStats`、`computePortSlots`、`edgePath`、`edgeStyle`、`visibleEdges`、
  `setView`、`setGravity`、`clusterCenters`、四种投影模式的语义，以及全部导出纯函数。
- **协议变更**：`reheat` 消息新增可选 `settle` 字段。原因：`reheat()` 只能抬高 α
  （`α = max(α, next)`），原有消息无法表达"用这组坐标然后停下"。
- **契约变更**：`tests/workbench/graph_layout_seed.test.js` 原先断言旧的三段式
  （设锚点、排一帧、两帧后清锚点、第二条 reheat）。已改为断言采纳路径，并新增
  一条覆盖"部分命中仍求解"。
- **仍未做（阻塞于枢纽节点结构）**：采用 Obsidian 的真实电荷量级（其界面默认 repel
  为 10³）。实测在行网格下增大电荷只会横向拉宽（各向异性 1.49 → 3.18），因为
  `enforceHierarchyBands` 钉住 y 而 x 自由。同理"可见的生长"也要等座位从压死的
  行网格变成簇之后才有余量。
