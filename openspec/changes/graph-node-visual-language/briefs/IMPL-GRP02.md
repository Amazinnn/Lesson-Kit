# IMPL-GRP02 — 节点形态与尺寸映射（tasks.md 第 2 组）

> 派发单元：**tasks.md 第 2 组**（2.1–2.9）。
> 依赖：**第 1 组必须先落地**（2.2 / 2.7 的 `nodeScreenRadius()` 由第 1 组定义）。
> 下游：本组落地后，第 3 组（给 `.node-dot` 上色）、第 6 组（焦点环画在哪一层）才能开工。

## 1. 目标

把节点从「五层叠一个圆」改成「**单层实心圆 + 可选数字 + 交互态描边环**」，
并把**绘制半径**做成物理半径的单调映射（与物理半径**解耦**）。

落地后：

- 常态节点读作**一枚平涂的实心点**：无描边、无投影、无内高光、无渐变、无可见 halo；
- 绘制半径落在 **5–13 屏幕 px**（两个数值投影 **6.5–13**，随量映射）；
- 结构 / 学习状态投影**没有圆心数字**，题目数量 / 重要性投影**有**（= 该投影的量）。

## 2. 产物路径清单（唯一可写的产品文件）

| 文件 | 改什么（当前真实行号，2026-10-22 实测） |
|---|---|
| `workbench/server/static/workbench.js` | `graphCreateNodes()`（当前 `:2032-2129`）改节点子层（2.3）；`graphProjectionDisplay()`（当前 `:2130-2136`）改圆心数字规则（2.6）；`STATE_SHORT`（当前 `:1653`）删单字分支（2.6） |
| `workbench/server/static/workbench.css` | `.node-face`（当前 `:3743-3754`）整块换成 `.node-dot`（2.4）；`.node` 命中区下限 24 屏幕 px（2.5）；`.node-value`（当前 `:3755-3760`）z-index / 位置（2.8） |
| `workbench/server/static/graph-physics.js` | `nodeScreenRadius(node)` 的**公式**（2.2 / 2.7）——与第 1 组同文件，**必须串行** |

**只读、不许改**：`graph-physics-core.js`（2.1 是**护栏**：确认 `sizeFor()` 零改动）。

## 3. 文件所有权

- **独占**：无（本组三个文件全部与别组共享）。
- **共享，必须串行**：
  - `graph-physics.js` ⇒ **必须等第 1 组落地后再改**（同一个 runtime 门面对象）。
  - `workbench.js` ⇒ 与第 3 / 4 / 5 / 6 / 7 / 8 / 9 组共享。
  - `workbench.css` ⇒ 与第 1 / 3 / 4 / 5 / 6 / 7 / 8 / 10 组共享。
- **下游依赖本组**：第 3 组（`.node-dot` 要有底色可填）、第 6 组（焦点环要挂在 `.node` 内）。

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
2. **物理半径护栏**：`git diff workbench/server/static/graph-physics-core.js` ⇒ **空**
   （`sizeFor()` / `labelWidth()` / `footprint()` 一行未改）。
3. `grep -c "metric-track\|status-ring" workbench/server/static/workbench.js` ⇒ **0**
   （DOM 创建已删）。
4. `grep -nE "5 \+ 2\.2|5 \+ 8|6\.5 \+ 6\.5" workbench/server/static/*.js`
   ⇒ **定义点恰 1 处**（其余全是调用）。
5. `nodeScreenRadius()` 的区间与单调性（用 `tools/graph-layout-diff.js` 用的同一份
   `graph-physics-core.js` 输入做一次离线自检）：
   - 结构投影：`5 + 2.2·√degree` ⇒ 落在 **5–13**；
   - 学习状态投影：`5 + 8·√score`（score = `stateAttention`）⇒ 落在 **5–13**；
   - 题目数量 / 重要性：`6.5 + 6.5·√score` ⇒ 落在 **6.5–13**；
   - 四个投影都**单调**（相等量值 ⇒ 相等半径）。
6. 圆心数字：结构 / 学习状态投影下 `.node-value` 的 `textContent` 为**空**；
   题目数量投影下 = 正式题数；重要性投影下 = `Math.round(importance × 100)`（**不含 `%`**）。
7. 常态节点的 computed style：`border-width` = 0、`box-shadow` = none、`background-image` = none。
8. 命中区：`elementFromPoint` 在可见圆盘外缘 ±2px 处**仍命中该节点**（下限 24 屏幕 px）。
9. 四条仓库级检查全绿（见 §8）。

## 6. 已知坑（至少一条来自 design.md / acceptance.md）

1. **`sizeFor()` 是物理半径，`nodeScreenRadius()` 是绘制半径——两个不同的量**。
   design.md D-3 明确：物理半径（世界直径 20–80）**一字不改**，
   绘制半径（屏幕 5–13）**另算**。
   ⇒ **绝对不许**把 `sizeFor()` 改成 28–60（旧设计就是这么越界的，A-26 冻结线）。
   `graph-physics-core.js:60-61` 一个字节都不许动。
2. **结构投影的公式用「度数」不是「归一化 score」**（design.md D-3 表注）。
   核心里 `scoreFor('structure')` 返回的是**归一化**度数（`norm(degreeRaw…)`，
   `graph-physics-core.js:1465`），而公式要的是**原始度数**。
   ⇒ `nodeScreenRadius()` 里要用 `state.degreeRaw`（加权原始度）而不是 `scoreFor()` 的归一化值；
   但**同序性**要求它与物理半径同源 ⇒ 二者都取 `degreeRaw` 派生的量，别一个用加权、一个用计数。
   ⚠️ 注意核心里有两个 map：`degreeRaw`（按边强度加权，`core:1419-1424`）与
   `degreeCount`（纯边数，`core:1425-1426`）。**design.md D-3 说的是「度数」，
   且物理半径来自 `scoreFor()`（用 `degreeRaw` 归一化）** ⇒ 用 `degreeRaw`。
3. **`--kind-color` 的 core/support 区分会随新形态消失**（design.md D-3 表注「〔推断〕」）。
   现在 `.node-wrap.core` / `.support`（`workbench.css:3720-3721`）给 `--kind-color` 赋值，
   `.node-face` 用它做渐变。新形态下单层实心圆**不再有内外两圈** ⇒
   `.node-face` 整块删掉后，`--kind-color` 的消费者只剩 `.node-value` 的
   `color-mix(... var(--kind-color) 68%, #302d28)`（`workbench.css:3758`）。
   ⇒ **第 3 组会重写 `.node-value` 的取色**（纸色/墨色数字，design.md D-4）。
   本组改 `.node-value` 时**只管 z-index 与位置**，别动 `color`。
4. **`STATE_SHORT`（`workbench.js:1653`）被两组点名**：本组 2.6 删它，第 4 组 4.9 也提它。
   ⇒ **本组删**（2.6 是形态的归属），第 4 组只做验收断言。
5. **`.node-value` 现在挂在 `.node-face` 里**（`workbench.js:2058-2059`）。
   2.3 把 `.node-face` 换成 `.node-dot` 时，**`.node-value` 必须重新安置**——
   design.md D-2 的表说 `.node-value` 是「独立于 `.node-dot` 的一层」（要压在点上面）。
   ⇒ 结构建议：`.node` 内并列 `.node-dot` + `.node-value` + `.node-focus-ring`，
   `.node-value` 绝对定位居中。**别**把 `.node-value` 塞进 `.node-dot` 里
   （`.node-dot` 要 `border-radius:50%` + 无 overflow 裁剪，塞进去数字会被圆裁掉）。
6. **行号锚点全部过时**（同第 1 组坑 3）。tasks.md 的 `workbench.css:1676-1687`（`.node-face`）
   现在是 `:3743-3754`；`workbench.js:957-1053` 现在是 `:2032-2129`。
   ⇒ **按符号名重新 grep**。
7. **`.node` 的 `width/height: var(--size)`（`workbench.css:3729`）在第 1 组之后已经失效**
   （第 1 组把 `.node` 改成 `var(--node-box)`）。本组改命中区时要在**当前**代码上改。

## 7. 诚实汇报要求

- 报「已完成」之前，**必须**贴出 §5 第 1 条 `node tools/graph-layout-diff.js --diff …` 的
  **原样输出**（含 `total differences:` 与退出码）。没有这条输出 = 没验 = 不算完成。
- **物理半径零改动**是本组的硬护栏：`git diff graph-physics-core.js` 必须为空。
  一旦发现它有 diff，**立刻回退**并在汇报里说明。
- 若 §2 的真实行号与汇报时的工作区**对不上**：**先 rebase，再重新 grep 定位**。
- 拿不准的（尤其「某个半径该用 `degreeRaw` 还是 `degreeCount`」「`.node-value` 该挂哪」）：
  **停下来报告**，写清疑问与两个候选，**不许**硬做。
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
