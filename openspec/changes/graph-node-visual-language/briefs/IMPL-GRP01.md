# IMPL-GRP01 — 屏幕空间缩放补偿（tasks.md 第 1 组）

> 派发单元：**tasks.md 第 1 组**（1.1–1.10）。
> 依赖：**无**（本组是所有视觉任务的前置，见 tasks.md「实施口径」）。
> 后续可并行：本组落地后，第 2 / 4 / 6 / 7 / 9 组可启动（各自仍受文件串行约束，见 IMPLEMENTATION-LOG.md 的串行总表）。

## 1. 目标

把节点的**绘制几何**从「世界像素」改成「**屏幕像素**」：`scale()` 只负责**位置**，
绘制半径、字号、点下间距、线宽不再随相机缩小。落地后：

- Fit 后节点直径落在 **10–26 屏幕 px**（不再是 3–30px）；
- 标签字号恒 **12 屏幕 px**（不再是 2.0–5.9px）；
- 可见标签从 0–1/31 变成「基本全可见，重叠让位由第 4 组管」。

**只做绘制补偿**，不做形态/配色/标签策略——那些是第 2 / 3 / 4 组。

## 2. 产物路径清单（唯一可写的产品文件）

| 文件 | 改什么（当前真实行号，2026-10-22 实测） |
|---|---|
| `workbench/server/static/graph-physics.js` | runtime 门面（当前 `:244-299`）新增 `nodeScreenRadius(node)`（1.2） |
| `workbench/server/static/workbench.js` | `graphApplyView()`（当前 `:2179-2191`）写 `--stage-scale` / `--inv-scale`（1.1）；写 `--label-alpha`（1.8）；`graphPaintNodes()`（当前 `:2371-2402`）写 `--node-d` / `--node-box`（1.3） |
| `workbench/server/static/workbench.css` | `.node`（当前 `:3728-3731`）改盒尺寸（1.4）；新增 `.node-dot` 几何骨架（1.5）；`.label`（当前 `:3779-3784`）字号 / `max-width` 屏幕化（1.6）；`.node-value`（当前 `:3755-3760`）字号屏幕化（1.6）；`.node-wrap`（当前 `:3712-3716`）`gap` 改 5 屏幕 px（1.7）；`.label` 透明度挂 `--label-alpha`（1.8） |

**不得新建产品文件**。本组**不碰** `pages.py` / `graph-physics-core.js` / `graph-renderer.js`。

## 3. 文件所有权

- **独占**：`graph-physics.js`。
- **共享，必须串行**：`workbench.js`（与第 2/3/4/5/6/7/8/9 组共享）、`workbench.css`（与第 2/3/4/5/6/7/8/10 组共享）。
  共享同一文件 ⇒ **必须按 IMPLEMENTATION-LOG.md「串行总表」的顺序落地**，不得两同时改。
- **下游依赖本组**（本组不回滚，下面这些组才能开工）：
  - 第 2 组要 `nodeScreenRadius()`（2.2 / 2.7）；
  - 第 4 组要 `--inv-scale` / `--label-alpha`（1.6 / 1.8）；
  - 第 5 组要 `nodeScreenRadius()` 做端点回退（5.3 / 5.4）；
  - 第 6 组要 `--node-d`（点放大倍率）；
  - 第 3 组要 `--node-fill`（见 §6 坑 1）。

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
   （第 10 组会按 design.md D-12.1 把这 12 个**改名**为 `--graph-*`，那是设计权威；**本组不得碰**。）
5. **主线那一侧**：`workbench.css` / `workbench.js` 的改动**必须**与主线的图谱页冻结块
   （`body:has(#layout[data-page="graph"])`，当前 `workbench.css:336-407`）兼容 ——
   冻结块保证**图谱页取值在主线改造期间一字不变**。
   ⚠️ **图谱 change 若要改那些取值，必须先解冻**（那是**另一个决定**，不是本轮能顺手做的）。

## 5. 验收标准（可机械判定）

1. `node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json`
   ⇒ `total differences: 0`，退出码 **0**。
2. `grep -n "nodeScreenRadius" workbench/server/static/*.js` ⇒ **恰 1 处定义**
   （在 `graph-physics.js`），且 `workbench.js` 与 `graph-renderer.js` 都从它取值。
3. `grep -cE "var\(--size\)" workbench/server/static/workbench.css` ⇒ 图谱区段 **0**
   （`--size` 是世界像素，`.node` 与 `.node-value` 都不再用它）。
4. `getComputedStyle(label).fontSize × 当前 scale` ≈ **12 屏幕 px**；
   `.node-value` 的**视觉**字号 ≈ 12 屏幕 px。
5. `getComputedStyle(wrap).getPropertyValue('--node-d')` 返回带 `px` 的**屏幕**直径；
   860×460 画布 Fit 后落在 **10–26px**。
6. `.node-wrap` 的 computed `gap` × 当前 scale ≈ **5 屏幕 px**。
7. `--label-alpha` 在 `s ≥ 0.5` 时为 **1**；`s = 0.25` 时为 **0**；`s = 0.3` 时明显 < 1。
8. `graph-physics-core.js` **零改动**（`git diff --stat` 该文件为空）——
   本组**只**改门面 `graph-physics.js`，不改核心。
9. 四条仓库级检查全绿（见 §7）。

## 6. 已知坑（至少一条来自 design.md / acceptance.md）

1. **`--node-fill` 是第 3 组的活**（design.md D-2 的 `.node-dot` 规则）。
   tasks.md 1.5 让本组写 `background: var(--node-fill)`，但**定义**由第 3 组 3.6 落地。
   ⇒ 本组交付后 `.node-dot` 的底色会短暂解析失败（`var()` 未定义 ⇒ 该声明失效）。
   这是设计文档的有意分家，**不是 bug**；但走查时若看到「节点无底色」，先确认第 3 组是否已落地。
   **不要**在本组擅自定义 `--node-fill`（那是第 3 组的色键所有权）。
2. **design.md D-1 的"现状表"是旧测量**。D-1 那张表（scale 0.17–0.49、圆直径 3–30px、
   标签 2.0–5.9px）取自 `tmp/frontend-audit/GRAPH-NODE-PIPELINE.md` 对**旧版**布局的离线复算。
   当前 `graphFit()`（`workbench.js:2278-2301`）的取景公式已变（`.38` 下限改成 `.1`、
   上下限改成 1.05、包围盒用 `footprint()`）。⇒ **本组落地后必须重测一次实际数字**，
   不要拿 D-1 的表当验收基线；偏差 >10% 走 design.md R-5（回看设计）。
3. **行号锚点全部过时**。tasks.md 给的 `workbench.css:1659-1663`（`.node`）、
   `workbench.js:1296-1325`（`graphPaintNodes`）、`workbench.js:1104-1107`（`graphApplyView`）、
   `graph-physics.js:254-300`（runtime 门面）等**都是主线 v2 改造前的行号**，现在全错位。
   ⇒ **开工第一步：按符号名重新 grep 定位，不要照抄行号**（真实行号见 §2）。
4. **`--inv-scale` 必须是无单位数字**。CSS 里要写 `calc(12px * var(--inv-scale))`，
   所以 `--inv-scale` 只能写 `2.04` 这种**纯数字**，写 `2.04px` 会让整条 `calc()` 失效
   （`calc()` 里 px × px 非法）。同理 `--stage-scale` 写纯数字。
5. **`--inv-scale` 写在 `.graph-stage` 上**（design.md D-1），而 `.node-wrap` 是
   `.graph-stage` 的子元素（`workbench.js:2120` `graphStage.appendChild(wrap)`）⇒ 继承得到。
   **别**写到 `document.documentElement` 或 `body`——那会让取值路径和冻结块纠缠。
6. **`--node-box` 用 CSS `calc()` 表达，不要在 JS 里算除法**（tasks.md 1.3 的要求）：
   `calc(var(--node-d) * var(--inv-scale))`，两处不得各算一份。
7. **`.node-value` 现在是 `.node-face` 的子元素**（`workbench.js:2058-2059`
   `face.appendChild(value); face.appendChild(unit);`）。第 2 组会拆掉 `.node-face`。
   本组改 `.node-value` 的**字号**时，**只改字号**，不要顺手改它的 DOM 归属。

## 7. 诚实汇报要求

- 报「已完成」之前，**必须**贴出 §5 第 1 条 `node tools/graph-layout-diff.js --diff …` 的
  **原样输出**（含 `total differences:` 与退出码）。没有这条输出 = 没验 = 不算完成。
- 落地过程中**一旦发现 diff ≠ 0**：**立刻停手**，按 tasks.md 14.5 定位越界改动并**回退**，
  不许用「差异很小」「四舍五入」解释掉，并在汇报里写清楚「改了什么 / 为什么回退」。
- 若 §2 里的真实行号与汇报时的工作区**对不上**（别的 agent 在并行改 `workbench.css` /
  `workbench.js`）：**先 rebase，再重新 grep 定位**，不要在旧行号上打补丁。
- 拿不准的（尤其是「这个值到底算绘制层还是物理层」）：**停下来报告**，写清你的疑问与两个候选，
  **不许**硬做并把它伪装成完成。
- 汇报里必须包含：改了哪些文件、每处改动对应 tasks.md 的哪一条、验证命令与原样输出、
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
