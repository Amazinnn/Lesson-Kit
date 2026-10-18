## 1. 布点：单层超阈值时改二维簇状

- [x] 1.1 `recomputeLayoutGuides()` 的 structure 分支加"平坦层"判据：整图只有 1 层且
      可见节点数 > 12 时，不再走 `bandRows()` + 横向折行
- [x] 1.2 平坦层按视口比例排成确定性网格（列数取 `round(sqrt(n × 1.35))`，
      行内按 `targetSize` 降序、同级按 id 排序保证确定性）
- [x] 1.3 网格围绕 `state.center` 居中，间隔取 `labelWidth`/`targetSize` 的最大脚印
      （复用同一套间距常量，不新造间距公式）
- [x] 1.4 每个节点仍然写 `guideX/guideY` 与 `rowIndex`（下游 `structureOrdering`
      与层级带约束依赖它们）

## 2. 舞台尺寸

- [x] 2.1 `structureStageSize()` 在同样的平坦层判据下，按簇状布点的实际范围给尺寸
      （宽高各留一行/一列脚印的余量），不再走 `BAND_MAX_WIDTH + 320`
- [x] 2.2 平坦层的舞台尺寸不得小于既有下限（`1800 × 1550`），避免小图被压

## 3. 回归

- [x] 3.1 `node --test tests/workbench/graph_physics.test.js` 14 条全绿
      （含 `wide levels wrap into stacked rows…` 与
      `an unwrapped graph keeps the blueprint's single-band stage`）
- [x] 3.2 `node --test tests/workbench/` 全部 JS 测试无回归（11 个文件 / 224 条全绿）
- [x] 3.3 真实数据验收（86 点 / 0 边）：各向异性 3.49 → **1.62**、
      bbox 2780×1268 → 1841×949、收敛 169 tick、拥塞遗留 0 对
- [x] 3.4 多档规模验收（12 / 13 / 40 / 86 点单层）：13 点 7.76→1.34、
      40 点 10.05→1.08、86 点 4.23→1.30；12 点走原路径不变
- [x] 3.5 有 prereq 的多层图验收：4 组夹具（3 层链 / 23 点混合 / 5 层×4 点 /
      含 legacy 隐藏）的舞台、guide、收敛位置与 main **逐字节一致**

## 4. 记录

- [x] 4.1 `openspec validate cluster-flat-knowledge-graph-levels` 通过
- [x] 4.2 浏览器实测：workbench `graph-preview` 工作区（86 点 / 0 边）渲染正常，
      舞台 2240×1550、节点 86、求解器"已收敛"
- [x] 4.3 只在本分支提交，不合并 main、不推 PR（等用户看过效果再定）
