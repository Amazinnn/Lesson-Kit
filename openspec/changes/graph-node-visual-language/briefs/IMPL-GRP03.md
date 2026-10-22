# IMPL-GRP03 — 图谱暖色板与四投影色键（tasks.md 第 3 组）

> 派发单元：**tasks.md 第 3 组**（3.1–3.11）。
> 依赖：**第 1 组**（`--node-fill` 的载体与 `--node-d`）与**第 2 组**（`.node-dot` 存在）。
> 下游：第 6 组（悬停/选中的「更实的一档」要靠色阶）、第 8 组（图例色修正在本组之后）。

## 1. 目标

给图谱一套**自有暖色板**，并让**四个投影各带一套色键**：

| 投影 | 色键 | 性质 |
|---|---|---|
| 关系结构 `structure` | **墨阶三档** | 颜色**不承载语义**；关系由边的线型与箭头承载 |
| 题目数量 `problem_count` | **量值橙阶 4 档** | 单色阶 |
| 重要性 `importance` | **量值橙阶 4 档**（同一套） | 单色阶 |
| 学习状态 `state` | **状态四色** | 分类色 |

并把图例改成**两块**：上半 = 关系线型（保留点按隐藏）+ 下半 = 随投影切换的节点颜色键。

**只改颜色与图例**。节点形状/半径是第 2 组，标签是第 4 组。

## 2. 产物路径清单（唯一可写的产品文件）

| 文件 | 改什么（当前真实行号，2026-10-22 实测） |
|---|---|
| `workbench/server/static/workbench.css` | 图谱 `:root` token 块（当前 `:3574-3587`）新增状态四色 / 量值橙阶 / 墨阶三档 / 文字色（3.1–3.4）；图例两块结构（3.8 的 CSS 侧） |
| `workbench/server/static/workbench.js` | `graphUpdateNodeAppearance()`（当前 `:2138-2150`）按当前投影写色键（3.6）；`graphApplyView()`（当前 `:2179-2191`）切图例下半块（3.9） |
| `workbench/server/pages.py` | `graph_page()`（当前 `:661-731`）图例改两块、4 套 `data-legend-for` 内容（3.8）；有向两项补箭头符号（3.10） |

**只读、不许改**：`graph-renderer.js` 的 `EDGE_COLORS`（当前 `:15-21`）——3.5 是**断言零改动**。

## 3. 文件所有权

- **独占**：`pages.py`（本组独占；第 9 组若改图例文字需串行，见下）。
- **共享，必须串行**：`workbench.css`（与第 1/2/4/5/6/7/8/10 组共享）、
  `workbench.js`（与第 1/2/4/5/6/7/8/9 组共享）。
- **下游依赖本组**：第 6 组（换色要色阶）、第 8 组（8.2 修图例「相关」色，**在本组之后**，
  因为本组会重排图例结构）。
- **注意**：第 9 组若要改 `pages.py` 的图例/控件文字 ⇒ 必须**等本组落地后**再改。

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
   ⚠️ 第 10 组会按 design.md D-12.1 把这 12 个**改名**为 `--graph-*`。
   ⇒ **本组新增的色键 token 必须从一开始就叫 `--graph-*`**（如 `--graph-state-work`、
   `--graph-scale-3`、`--graph-ink-2`、`--graph-label`、`--graph-value-ink`），
   **不要**再用 `--blue` / `--red` / `--yellow` 这类裸名或主线名。
5. **主线那一侧**：`workbench.css` / `workbench.js` 的改动**必须**与主线的图谱页冻结块
   （`body:has(#layout[data-page="graph"])`，当前 `workbench.css:336-407`）兼容 ——
   冻结块保证**图谱页取值在主线改造期间一字不变**。
   ⚠️ **图谱 change 若要改那些取值，必须先解冻**（那是**另一个决定**，不是本轮能顺手做的）。

## 5. 验收标准（可机械判定）

1. `node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json`
   ⇒ `total differences: 0`，退出码 **0**。
2. **色值逐字核对**（design.md D-4 的表，亮纸 / 夜纸两列全部）：
   - 状态四色：`#8a8377` / `#b08a12` / `#d4702f` / `#b03a2a`；
   - 量值橙阶：`#b25d24` / `#a15421` / `#8a4519` / `#7d2f12`；
   - 墨阶三档：`#2f2b24` / `#6f6759` / `#9c9184`；
   - 标签文字 `#5c5549`；圆心数字（亮纸）`#fffdf7`。
   夜纸值见 design.md D-4 表；**本组只落亮纸值 + 夜纸 token 声明**，
   夜纸值集的整体切换由第 10 组落。
3. **对比度门槛**（D-4 的验收线）：节点填充色对纸面 **≥ 3:1**；
   圆心数字对其填充色 **≥ 4.5:1**；标签文字对纸面 **≥ 4.5:1**。
   用 `tools/verify_tokens.py` 或等价脚本给出实测值。
4. **分档阈值校验**（3.7）：在 dmath/ch06 的真实 score 分布上确认
   `.25 / .5 / .75` 四档**不空置**；若某档空置 ⇒ 改用分位数分档（**不改「单色阶」规格**），
   且分档边界写成**常量**而非散落字面量。
5. `git diff workbench/server/static/graph-renderer.js` ⇒ **空**
   （`EDGE_COLORS` 亮色取值逐字节不变）。
6. 图例 DOM：存在 **4 套** `data-legend-for="structure|problem_count|importance|state"`；
   上半的 5 个关系项与改造前**逐字一致**（含 `data-edge-type` / `aria-pressed` / `title`）。
7. 切四个投影，图例下半块**随之切换**；切换只改 `hidden` / `display`，
   **不写任何学习数据**（不新增请求、不改状态、不改成员）。
8. 四条仓库级检查全绿（见 §8）。

## 6. 已知坑（至少一条来自 design.md / acceptance.md）

1. **`importance` 在数据里只有两个值**（实测 `pool/dmath.db`：
   `importance` 分布 = `core` 17 / `supplementary` 14）。而 `graphBuild()`
   （`workbench.js:1941`）把 `importance` 映射成 **`0.55` 或 `1`** 两个数值。
   ⇒ **重要性投影实际只有两档**，不是连续量。
   这对 3.7 的分档校验是硬约束：`.25/.5/.75` 四档在 importance 投影上**必然空两档**。
   ⇒ **按 design.md D-5 的明文**：某档空置 ⇒ 改用**分位数分档**。
   **不要**为了「四档都满」去改 `graphBuild()` 的映射（那是投影语义，冻结）。
   ⇒ **这一点必须在汇报里明确报告给主会话**（这是规格与数据现实之间的落差，不是实现者能自行消解的）。
2. **结构投影的圆心数字现在显示的是「度数」**（`workbench.js:2132`
   `sim.state.degreeCount.get(node.id)`），而第 2 组 2.6 已把结构投影的圆心数字**清空**。
   ⇒ 本组写色键时**不要**依赖 `graphProjectionDisplay()` 的返回值来分档，
   要用**自己的**量（结构投影的墨阶三档按 `scoreFor()` 的归一化度数分档）。
3. **`--kind-color` 的 core/support 区分在新形态下失去意义**（design.md D-3 表注：
   「core / support 的视觉区分在四个投影中全部消失」）。
   ⇒ 本组是**唯一**有权改节点填充色来源的一组：
   把 `.node-face` 的 `color-mix(var(--kind-color)…)` 换成 `--graph-*` 色键。
   **第 8 组不要**顺手改这块。
4. **图例「相关」色现在与画布不一致**：图例 `#aaa399`（`workbench.css:3865`）
   vs WebGL 实况 `rgb(117,112,104)` = `#757068`（`graph-renderer.js:19`）。
   ⇒ **这是第 8 组 8.2 的活**（tasks.md 3.11 明说 ④ 由 8.2 收口）。
   本组改图例**结构**时，**保留** `#aaa399` 原样，等第 8 组改。
5. **状态色与「重要度」的语义纠缠**：`.node-wrap.state-work` 用 `--red`、
   `.node-wrap.state-mastered` 用 `--blue`（`workbench.css:3723-3726`）——
   这是**现状**。新色键里「掌握」是**橙** `#d4702f`、「需突破」是**砖红** `#b03a2a`。
   ⇒ 本组改填充色时，**`.node-wrap.state-*` 这几行也要一并接管**
   （否则会出现「填充色是橙的、但 `--state-color` 还指向蓝」的不一致）。
   但**第 10 组**会改这些 token 的**名字**（裸名 → `--graph-*`）⇒ 串行。
6. **行号锚点全部过时**（同第 1 组坑 3）。tasks.md 的 `pages.py:462-467` 现在是 `:713-718`；
   `workbench.js:1063-1075` 现在是 `:2138-2150`。⇒ **按符号名重新 grep**。
7. **`graphApplyView()` 是相机函数**（当前 `:2179-2191`），它每次相机变化都跑。
   在里面切图例可见套**可行但浪费**（图例只在投影切换时变）。
   ⇒ 优先在投影切换的入口做（`sim.setView()` 之后的 `graphUpdateNodeAppearance()` 循环处，
   `workbench.js:2857`），并在 `graphApplyView()` 里保留一次幂等同步兜底。
   **不要**因此改动 `graphApplyView()` 的相机语义。

## 7. 诚实汇报要求

- 报「已完成」之前，**必须**贴出 §5 第 1 条 `node tools/graph-layout-diff.js --diff …` 的
  **原样输出**（含 `total differences:` 与退出码）。没有这条输出 = 没验 = 不算完成。
- **必须**报告 3.7 的分档实测分布（四档各多少节点），以及「importance 只有两个取值」
  这个落差（见坑 1）——**不许**把它悄悄糊过去。
- **必须**报告每个色值与 design.md D-4 表的**逐字对照结果**；有一个对不上就停下来报告。
- 若 §2 的真实行号与汇报时的工作区**对不上**：**先 rebase，再重新 grep 定位**。
- 拿不准的（尤其「某档空置该怎么办」「`.node-wrap.state-*` 归谁管」）：
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
