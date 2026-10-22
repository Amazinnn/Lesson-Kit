# IMPL-GRP09 — 相机与 auto-fit（tasks.md 第 9 组）

> 派发单元：**tasks.md 第 9 组**（9.1–9.7）。
> 依赖：**第 1 组**（`--inv-scale` / 屏幕化）——
> 初始相机改成 Fit 口径后，屏幕尺寸才是稳定的参照系。
> 下游：本组落地后，第 11 组走查的 S-L8（控制卡展开）与 Fit 判定才成立。

## 1. 目标

只改**相机**，不改**世界坐标**（design.md D-11）：

- **初始相机**从硬编码 `{ scale: .7, panX: 52, panY: -18 }` 改成「按 Fit 口径算出来」，
  ⇒ 首帧就是整图可见（现在 31 个节点里 23 个落在画布外）；
- **Fit** 改用「节点圆盘包围盒 + 固定屏幕边距」，不再用「含标签留白的 `footprint()` 包围盒」
  ⇒ 整图缩放从约 0.37 升到约 0.41–0.47，节点间距整体放大约 20–35%；
- **缩放条语义**变（「放大 = 拉开间距」），但**量纲与上限不动**；
- **布局种子格式零改动**。

## 2. 产物路径清单（唯一可写的产品文件）

| 文件 | 改什么（当前真实行号，2026-10-22 实测） |
|---|---|
| `workbench/server/static/workbench.js` | 初始相机 `graphView`（当前 `:1778`）改由 `graphFit()` 口径算出（9.1）；`graphFit()`（当前 `:2278-2301`）改用节点圆盘投影 + 固定屏幕边距（9.2）；加一段口径注释说明「中栏宽度变则整图缩放变」是 fit-to-viewport 的固有性质（9.4）；缩放条 `title` 文案（9.5，DOM 在 `pages.py`，本组改文案来源需与第 3 组串行） |
| `workbench/server/pages.py` | 缩放条按钮的 `title` 文案（当前 `:719-722`）改成反映「拉开间距 / 看整体」（9.5）—— **与第 3 组同文件 ⇒ 串行** |
| `docs/PRODUCT-MANUAL.md` | 知识图谱页章节（当前 `:152-182`）同步缩放语义（9.5）—— **与第 12 组同文件 ⇒ 串行** |

**只读、不许改**：`graph-physics.js` 的布局种子读写（当前 `:43-48`、`:55-75`、`:344-388`）——
9.6 要求**键名与序列化格式逐字不变**。

## 3. 文件所有权

- **独占**：`docs/PRODUCT-MANUAL.md`（本组只改缩放语义那一段；第 12 组改图谱章节 ⇒ **本组先**）。
- **共享，必须串行**：`workbench.js`（与第 1/2/3/4/5/6/7/8 组共享）、
  `pages.py`（与第 3 组共享 ⇒ **第 3 组先**）。
- **下游依赖本组**：第 11 组（走查）、第 12 组（产品手册的图谱章节要写「缩放 = 拉开间距」）。

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
2. **首帧可见性**：进入图谱页的第一帧截图里，**31/31 节点全部在画布内**。
3. **Fit 不写世界坐标**：点 Fit 前后取每个节点的 `(x, y)` ⇒ **逐节点相同**（SI-3 的一部分）。
4. **Fit 不 reheat**：`graphFit()` **不**调 `reheat()`；
   `workbench.js` 的「Camera movement never reheats the solver」注释与行为保持
   （当前 `graphApplyView()` 在 `:2179-2191`）。
5. **Fit 口径**：`graphFit()` **不再调用** `GraphPhysics.footprint(node)`
   （当前 `:2283`），改用节点圆盘投影（`node.size`）+ 固定屏幕边距；
   ⇒ `grep -c "footprint" workbench/server/static/workbench.js` 的图谱段 ⇒ **0**。
6. **`footprint()` / `labelWidth()` 在核心里零改动**：`git diff graph-physics-core.js` ⇒ **空**。
7. **缩放量纲与上限逐字不变**：`+` 每次 **+0.09**、上限 **1.6**（当前 `:2960`）、
   滚轮下限 **0.38**、步长 **×0.92 / ×1.08**（当前 `:2837`）—— 一律不动。
8. **缩放条文案**已反映新语义（标题 + `aria-label` 同步），产品手册对应段落已同步。
9. **布局种子零改动**：`graph-physics.js` 的 `lk_graph_layout_v1_<workspace>` 键名与
   `writeLayoutSeed()` 的序列化格式**逐字不变**；用改造前的旧种子能加载成功。
10. 四条仓库级检查全绿（见 §8）。

## 6. 已知坑（至少一条来自 design.md / acceptance.md）

1. **相机变化不 reheat 求解器**是硬约束（`workbench.js` 现有注释「Camera movement never
   reheats the solver」，当前 `:2182-2184`；`workbench-ui` 规格 `workbench-ui:155-158`
   「Fit without rewriting layout」）。
   ⇒ 9.1 / 9.2 都**只改相机**，**不许**顺手 `reheat()`。
   ⇒ 9.1 用 Fit 口径算初始相机时，**不能**触发求解器重启。
2. **`footprint()` 与 `labelWidth()` 是物理量，冻结**（design.md D-11.2 明写：
   「`footprint()` 与 `labelWidth()` **本身不动**（它们是物理量，被碰撞分离使用）；
   改的只是 **`graphFit()` 用哪个包围盒**——**相机**」）。
   ⇒ 9.2 是**改调用点**，**不是**改函数。
   ⇒ **绝对不许**改 `graph-physics-core.js`（改了会改碰撞间距 ⇒ 改布局 ⇒ SI-0 红）。
3. **9.1 的时序**：初始相机要在**节点创建完**之后算（`graphCreateNodes()` 之后、
   `graphApplyView()` 之前）。现在 `graphApplyView()` 在 `workbench.js:1995` 被调，
   `graphCreateNodes()` 在 `:2001` ⇒ 顺序要调。
   ⇒ 还要确认 `graphCanvas.clientWidth/Height` 此时**已是最终值**（画布已布局），
   否则算出来的 scale 会是 0 或错值。**先量再改**，并在汇报里给出首帧的实测 scale。
4. **「中栏宽度变则整图缩放变」是 fit-to-viewport 的固有性质，不是缺陷**
   （design.md D-11.3）。9.4 只要求**登记这个口径**（加注释），**不许**去「修」它。
   ⚠️ 这条是 graph-isolation.md 的 **F-22**，主线也关心 ⇒ 注释要写清楚，别让后人当 bug 改。
5. **缩放量纲不能动**（design.md D-11.4：「不改缩放档位（会改变 `workbench-ui` 的交互契约，
   且没有必要）」）。
   ⇒ `+` 0.09 / 上限 1.6 / 滚轮 0.38 / ×0.92 / ×1.08 —— **一个都不许改**，
   只改 `title` 文案。
6. **初始相机与 `graphCenterOn()` 是两回事**：`graphCenterOn(node, zoom)`（当前 `:2251-2258`）
   是「聚焦到某个节点」的相机动作，**不是** 9.1 的初始相机。⇒ 别改错函数。
7. **9.1 的 scale 值**：design.md D-11.2 的「0.37 → 0.41–0.47」是**离线估算**，
   基于旧版 `footprint()` 口径。当前代码的 Fit 公式（当前 `:2278-2301`）已经与那版不同
   ⇒ **实测为准**，并在汇报里给出实际值。偏差 >10% 触发 design.md R-5（回看设计）。
8. **行号锚点全部过时**（同第 1 组坑 3）。tasks.md 的 `workbench.js:1203-1229` 现在是 `:2278-2301`；
   `workbench.js:703` 现在是 `:1778`；`workbench.js:1885` 现在是 `:2958-2971`。
   ⇒ **按符号名重新 grep**。

## 7. 诚实汇报要求

- 报「已完成」之前，**必须**贴出 §5 第 1 条 `node tools/graph-layout-diff.js --diff …` 的
  **原样输出**（含 `total differences:` 与退出码）。没有这条输出 = 没验 = 不算完成。
- **必须**报告：首帧的实测 scale、31/31 节点在画布内的实测、Fit 前后的世界坐标逐点比对结果。
- **必须**报告坑 7 的实测值与 design.md 估算的偏差（>10% 要说明）。
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
