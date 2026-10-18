## Why

structure 视图的导引网格完全挂在"有向 prereq 边"上：`hierarchyLevels()` 只认
`type === "prereq"` 且非对称的边，其余一律判为 level 0。这本身是正确的语义
（对称的 related 边不含方向信息，不应凭空造层级，见既有测试
"auxiliary relations do not invent hierarchy"）。

但当池子**还没有任何有向关系**时（真实数据：`高级数据结构与算法分析/pool/c02.db`
有 86 个知识点、`knowledge_relations` 0 行、`related_kp_ids` 全空），整张图退化成
**单层**，`recomputeLayoutGuides()` 就把 86 个点沿着 `BAND_MAX_WIDTH = 2400` 横向
摞成 9 行、`pitch = 155`，得到一个约 2780 × 1268 的细长条带。

实测（86 点 / 0 边，当前 main）：

```
分层: 1 层
舞台: 2720 × 1987
guide 行数: 9
点云: 各向异性 3.49  主轴 25.5°  bbox 2780×1268   → 屏幕上是左上到右下的斜带
```

这不是求解器问题（收敛 239 tick、拥塞遗留 0 对），而是**单层时的布点缺少第二个维度**。
点一多就被拉成条带，学习者看到的是一张"斜线"而不是一簇知识。

## What Changes

- 单层节点数超过阈值（12）且该图**没有结构性层次**（`hierarchyLevels` 只产出 1 层）时，
  该层改用**确定性的二维簇状铺点**（按视口比例排布的网格），而不是继续沿一条横带折行。
- `structureStageSize()` 相应改为按该簇状布点的**实际范围**给舞台尺寸，而不是按行宽估算。
- 阈值以下、以及任何多层的图，行为**完全不变**（照旧折行、照旧舞台尺寸）。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-ui`: structure 投影在"单层且点数超过阈值"时的布点与舞台尺寸。

## Impact

- 只改 `workbench/server/static/graph-physics-core.js` 的两个函数：
  `recomputeLayoutGuides()` 与 `structureStageSize()`。
- **不动**：力律（弹簧 / 斥力 / 碰撞 / 速度衰减 / 速度钳制）、拥塞解析、
  `hierarchyLevels()` 的语义、`bandRows()` 的契约、端口路由、渲染器。
- 既有测试契约必须保持：`auxiliary relations do not invent hierarchy`、
  `wide levels wrap into stacked rows instead of one huge ribbon`、
  `an unwrapped graph keeps the blueprint's single-band stage`。
- 无数据侧改动：不新增字段、不改 schema、不写默认关系。缺少有向关系时布局
  如实表现为"无层次"，只是不再被拉成一条斜带。
