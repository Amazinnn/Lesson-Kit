# IMPL-GRP05 — 关系线：屏幕恒定线宽 + 方向箭头 + 端点落在点缘（tasks.md 第 5 组）

> 派发单元：**tasks.md 第 5 组**（5.1–5.8）。
> 依赖：**第 1 组**（`nodeScreenRadius()` 与 `--node-d`）与**第 2 组**（新的绘制半径）。
> 下游：本组落地后，第 8 组 8.10 的死规则断言才能最终判过。

## 1. 目标

关系线的**画法**改成 Obsidian 式（design.md D-7）：

- 线宽**屏幕恒定 1.25px**（= `1.25 / scale`）、基础 alpha **0.3**；
- 两端**落在绘制点的边缘**（不是节点盒边缘）；
- **有向的两类关系画箭头**（先修 / 应用），箭头**屏幕尺寸恒定**；
- 非邻接元素的淡化强度调整（边 0.07 → 0.2，二跳 0.38 → 0.4；节点 dim 0.18 → 0.2）。

**只改画法**：拓扑、类型、权重、方向字段一律不动。

## 2. 产物路径清单（唯一可写的产品文件）

| 文件 | 改什么（当前真实行号，2026-10-22 实测） |
|---|---|
| `workbench/server/static/graph-physics-core.js` | `edgeStyle()`（当前 `:1326-1329`）线宽改常数 1.25、alpha 改 0.30（5.2）；`NODE_FACE_INSET`（当前 `:1343`）与 `endpointRadius()`（当前 `:1345-1347`）**标注并处理**（5.1） |
| `workbench/server/static/graph-renderer.js` | `draw()`（当前 `:242-305`）端点回退（5.3）；箭头语义与屏幕恒定尺寸（5.5）；`edgeFocus` 系数（当前 `:276-280`）0.07 → 0.2、0.38 → 0.4（5.6） |
| `workbench/server/static/workbench.css` | `.node-wrap.dim`（当前 `:3717`）opacity 0.18 → 0.2（5.6） |

**只读、不许改**：`EDGE_COLORS`（`graph-renderer.js:15-21`，5.7 要求逐字节不变）。

## 3. 文件所有权

- **独占**：`graph-renderer.js`、`graph-physics-core.js`（**本组独占**）。
- **共享，必须串行**：`workbench.css`（与第 1/2/3/4/6/7/8/10 组共享）。
- **下游依赖本组**：第 8 组（死规则断言要看到 `NODE_FACE_INSET` 已处理）；
  第 10 组（夜纸关系线值是**另一件事**，见坑 4）。

## 4. 不可动的红线（逐字照抄，每组都要带上）

1. **不动图谱的算法**：力模型 / 迭代 / 收敛判据 / 阻尼 / 引力斥力 / 碰撞分离 / 布局种子 /
   邻接与边集合 / 边类型与权重 / 筛选语义 / 投影语义 / 指标计算 / DOM 节点身份与顺序 /
   拖拽与聚焦的行为语义 —— **一条都不许改**。
2. **只许改绘制**：节点形状与颜色、**绘制**半径（与物理半径解耦）、标签绘制与位置、
   边的绘制、缩放补偿。
3. **可执行判据（SI-0）**：同一输入 + 同一初值 + 同一迭代预算 ⇒
   **收敛坐标集合 diff 必须严格为 0**。**diff ≠ 0 即回滚。**
4. **不要动图谱的 12 个裸名**（`--paper` / `--ink` / `--hair` / `--blue` / `--yellow` / `--red` /
   `--shadow` / `--graphite` / `--green` / `--blueSoft` / `--yellowSoft` / `--redSoft`）——
   主线的新 token 层**已经和它们零同名**（`decisions.md` **A-8**），别再引入同名的。
5. **主线那一侧**：`workbench.css` / `workbench.js` 的改动**必须**与主线的图谱页冻结块
   （`body:has(#layout[data-page="graph"])`，当前 `workbench.css:336-407`）兼容 ——
   冻结块保证**图谱页取值在主线改造期间一字不变**。
   ⚠️ **图谱 change 若要改那些取值，必须先解冻**（那是**另一个决定**，不是本轮能顺手做的）。

## 5. 验收标准（可机械判定）

1. `node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json`
   ⇒ `total differences: 0`，退出码 **0**。
   ⚠️ **这是本组最关键的一条**：本组**改了 `graph-physics-core.js`** ⇒ 该文件的 sha256 变了
   ⇒ 工具会打印 `*** WARNING: graph-physics-core.js has changed since this baseline was captured.`
   ⇒ **警告是预期的**（我们只改了绘制辅助函数），**但坐标 diff 必须仍是 0**。
   **判据是坐标 diff，不是文件哈希。**（见坑 1）
2. `git diff workbench/server/static/graph-renderer.js` 里 `EDGE_COLORS` 块 ⇒ **零改动**。
3. `git diff workbench/server/static/graph-physics-core.js` 里
   `NEIGHBOR_WEIGHT`（当前 `:32`）、`baseGapForStrength()`（当前 `:68`）、
   `sizeFor()`（当前 `:60`）⇒ **零改动**。
4. `edgeStyle()` 的 diff **只有两行**（width / baseOpacity），返回值恒为
   `{ width: 1.25, baseOpacity: .30 }`。
5. 屏幕线宽实测：`style.width / scale` ⇒ 任意缩放下**屏幕**宽度恒为 **1.25px**。
6. 端点：线头与**绘制点的边缘**相接，无缝隙也无插入点内。
   ⇒ 放大 4 倍截图检查线头与点**零缝隙**。
7. 箭头：先修 / 应用**有向**且 `direction !== "symmetric"` 时画；
   对比 / 相关 / 隐含**不画**；箭头屏幕尺寸**不随缩放变化**。
8. 边集合不变（SI-2）：`(source, target, type, direction)` 四元组全集与改造前**逐项相同**。
9. 四条仓库级检查全绿（见 §8）。

## 6. 已知坑（至少一条来自 design.md / acceptance.md）

1. **「物理核心零 diff」不能当门禁**（本组与门禁的正面冲突，实测已确认）。
   `tools/graph-baseline/README.md` 的「越界告警」写着：任何对
   `graph-physics-core.js` / `graph-physics.js` 的改动都要**重跑 `--capture`**，
   否则「SI-0 失效」。
   **但本组按 design.md D-7.2 必须改 `edgeStyle()`**（它在 `graph-physics-core.js` 里）。
   实测（在 `/tmp` 的**隔离副本**上做的，未碰仓库）：
   - 只把 `edgeStyle()` 改成 `{ width: 1.25, baseOpacity: .30 }`、并把 `NODE_FACE_INSET` 改成 `0`，
   - 坐标 diff = **0**、seed diff = **0**、id 差 = **0**、`total differences: 0`、退出码 **0**，
   - **但** sha256 从 `c4e9e8e5…` 变成 `38225398…`，工具打出
     `*** WARNING: graph-physics-core.js has changed since this baseline was captured.`
   ⇒ **结论：坐标 diff 是真正的判据；文件哈希只是「核心动过」的信号。**
   ⇒ **本组不得重跑 `--capture` 覆盖基线**（那会毁掉「改造前」的证据）。
   ⇒ 本组交付时，**在 `tools/graph-baseline/EVIDENCE.md` 里追加一节**，
   写明「本次只改了 `edgeStyle()` 与 `NODE_FACE_INSET`（纯绘制辅助函数），
   坐标 diff 仍为 0」，并把新的 sha256 记进去。
   **这条必须写进汇报**（它决定第 13 组怎么判门禁）。
2. **端点回退在**渲染层**，不在物理核心**（design.md D-7.1 的明文）。
   理由：`scale()` 不知道物理核心，物理核心（Worker）不知道缩放；
   把缩放推进物理核心 ⇒ 缩放会 reheat 求解器 ⇒ 违反
   `workbench.js`「Camera movement never reheats the solver」。
   ⇒ `graph-renderer.js` 的 `draw()` 已经拿到了 `scale`（当前 `:267` `stageScale(stage)`），
   端点回退在**采样点**上做：按采样点从两端向节点中心回退，直到与节点中心的距离
   ≥ 新的端点半径（= 绘制半径 ÷ scale）。
   ⇒ **不要**去改 `edgePath()`（核心 `:1349`）里的端口几何。
3. **`NODE_FACE_INSET` 与 `.node-face` 的 `inset: 7%` 是一对 coupled 的**
   （核心 `:1343` 的注释明说「If the face's inset ever changes, this constant has to change with it」）。
   第 2 组删掉 `.node-face` ⇒ 这个常量就**失去了它所耦合的那个东西**。
   ⇒ 5.1 要求「标注并处理」它：要么删，要么留注释说明它现在只服务端口几何。
   **但** `endpointRadius()` 是 `edgePath()`（核心 `:1349`）算端口落点时用的，
   删了会改**边的几何**（不是节点坐标）⇒ 坐标 diff 仍是 0，但**边的形状会变**。
   ⇒ **选哪个由你定，但必须在汇报里说明选择与理由**，并且
   **端点回退之后线必须仍落在绘制点边缘**（验收第 6 条会抓住「双扣」或「没扣」）。
   ⚠️ 特别提醒：`graph-renderer.js` 在 attach 时把 `runtime.edgePath` 换成了
   返回 `"M 0 0"` 的桩（当前 `:356`）——**渲染器自己用的是 attach 前捕获的 `routePath`**
   （当前 `:179`），**不是**那个桩。改端点时**改 `routePath` 用的那条路径**，
   别被桩函数误导。
4. **夜纸关系线取值是另一件事**（design.md D-12.2 / tasks 10.5）。
   `EDGE_COLORS` 是**亮色**取值，本组**一行不动**。
   夜纸的 5 条关系线值（同色相、更亮）由**第 10 组**在夜纸 token 块里落。
   ⇒ 本组**不要**顺手给 `EDGE_COLORS` 加夜纸分支——那是第 10 组 + `graph-renderer.js` 的活，
   而 `graph-renderer.js` 是本组独占文件 ⇒ **本组做完，第 10 组才能碰 `graph-renderer.js`**。
   **这条串行关系必须写进汇报**。
5. **强关系画在上层**是现状硬约束（`graph-renderer.js:261-265` 按 strength 升序排、
   blend 让后画的压前面）。design.md D-7.4 明确保留。
   ⇒ 端点回退**不要**打乱这个排序。
6. **虚实节奏保留**：`contrast` 与 `legacy` 虚线，其余实线（`graph-renderer.js:293-295`）。
   ⇒ 本组只改线宽/透明度/箭头/端点，**不动 dash 节奏**。
7. **节点侧的 dim 现在有两套机制**：
   - CSS `.node-wrap.dim .label, .node-wrap.dim .meta { opacity: .18 }`（当前 `:3717`）
     —— 但 `graphPaintNodes()` 每帧写 `elements.label.style.opacity`（当前 `:2399`），
     **行内样式盖过样式表** ⇒ 这条 CSS 规则**当前基本无效**；
   - 真正起作用的是 `node.opacity`（由 `graphApplyVisibility()` 的 `weight` 决定，
     当前 `:2163-2165`：选中 1 / 1 跳 .92 / 2 跳 .48 / 其余 .12）。
   ⇒ 5.6 的「节点 dim 0.18 → 0.2」到底改哪一处，**必须实测确认**，
   改完要能在截图上看出效果。**在汇报里写清你改的是哪一处、为什么**。
   ⚠️ 「非邻接元素 alpha 0.07 → 0.2」说的是**边**（`edgeFocus`），
   「节点 dim 0.18 → 0.2」说的是**节点**——两者是不同的数，别混。
8. **行号锚点全部过时**（同第 1 组坑 3）。tasks.md 的 `graph-renderer.js:274`（edgeStyle 消费点）
   现在是 `:275`；`:288-298`（虚线节奏）现在是 `:293-295`；`:299`（箭头）现在是 `:300`。
   ⇒ **按符号名重新 grep**。

## 7. 诚实汇报要求

- 报「已完成」之前，**必须**贴出 §5 第 1 条 `node tools/graph-layout-diff.js --diff …` 的
  **原样输出**（含 `*** WARNING: …` 那一段、`total differences:` 与退出码）。
  **只贴「0 条差异」而不贴 WARNING 段 = 隐瞒 = 不算完成。**
- **必须**报告 §5 第 3 条的「三个冻结量零改动」证明。
- **必须**报告坑 1 的结论（sha256 变了、坐标 diff 仍为 0、基线**未**被覆盖）。
- **必须**报告坑 3 的选择（`NODE_FACE_INSET` / `endpointRadius()` 怎么处理）与理由。
- **必须**报告坑 7 的实测结论（节点 dim 改的是哪一处、为什么）。
- 一旦坐标 diff ≠ 0：**立刻停手**、定位越界改动、**回退**，不许用「差异很小」解释掉。
- 若 §2 的真实行号与汇报时的工作区**对不上**：**先 rebase，再重新 grep 定位**。
- 拿不准的：**停下来报告**，写清疑问与两个候选，**不许**硬做。
- 汇报里必须包含：改了哪些文件、每处对应 tasks.md 哪一条、验证命令与原样输出、
  以及**你发现但没改**的问题清单。

## 8. 验证

```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
openspec validate graph-node-visual-language --strict
node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json   # 必须 0 条差异
```
