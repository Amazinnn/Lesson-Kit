# IMPL-GRP04 — 标签系统与重叠让位（tasks.md 第 4 组）

> 派发单元：**tasks.md 第 4 组**（4.1–4.10）。
> 依赖：**第 1 组**（`--inv-scale` / `--label-alpha` / `--node-d`）与**第 2 组**（`.node-dot` 存在）。
> 下游：本组落地后，第 8 组 8.8 删 `.meta`、第 9 组改 Fit 包围盒。

## 1. 目标

把标签从「按缩放阈值硬隐藏」改成「**常态可见 + 重叠让位**」：

- 标签**默认可见**，只在与更高优先级标签重叠、或超出可见标签预算时隐藏；
- 隐藏按 **半径降序 → 重要度降序 → 节点 id 升序** 的确定性顺序让位；
- 选中 / 悬停 / 1 跳邻居的标签**永不隐藏**；
- 标签**不截断**（换行显示），字号 **12 屏幕 px** 恒定；
- 节点上**不再出现任何状态文字**。

## 2. 产物路径清单（唯一可写的产品文件）

| 文件 | 改什么（当前真实行号，2026-10-22 实测） |
|---|---|
| `workbench/server/static/workbench.js` | 删 `LABEL_MIN_RADIUS_PX`（当前 `:2365`）与 `labelScaleThreshold()`（当前 `:2367-2369`）；`graphPaintNodes()`（当前 `:2371-2402`）的 `labelVisible` 判定改「默认可见」；新增 `graphResolveLabelCollisions()`（4.4–4.7）；`graphProjectionDisplay()`（当前 `:2130-2136`）不再返回状态单字（4.9，与第 2 组 2.6 同处，需串行） |
| `workbench/server/static/workbench.css` | `.label`（当前 `:3779-3784`）颜色 / 光晕减薄 / 不截断（4.2 / 4.3）；`.meta`（当前 `:3785-3788`）由第 8 组删，本组**不改** |

**只读、不许改**：`graph-physics-core.js`（`labelWidth()` / `footprint()` 冻结）。
**不得新建产品文件**。

## 3. 文件所有权

- **独占**：无。
- **共享，必须串行**：`workbench.js`（与第 1/2/3/5/6/7/8/9 组共享）、
  `workbench.css`（与第 1/2/3/5/6/7/8/10 组共享）。
- **与第 2 组的冲突点**：`graphProjectionDisplay()`（4.9 与 2.6 都在改）。
  ⇒ **第 2 组先落地**，本组随后只做「不再返回状态单字」的收尾。
- **与第 8 组的冲突点**：`.meta` 的删除（8.8）**在本组之后**——
  本组先确认状态文字从节点上消失，第 8 组再删 `.meta` 整个元素与其写入。
- **与第 9 组的冲突点**：第 9 组改 Fit 包围盒（不再含标签留白），**在本组之后**。

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
2. `grep -c "LABEL_MIN_RADIUS_PX\|labelScaleThreshold" workbench/server/static/workbench.js` ⇒ **0**。
3. 触发时机**只有 4 类**：相机变化（缩放/平移）、布局收敛、投影切换、选中变化。
   ⇒ 断言 `graphResolveLabelCollisions()` 的调用点集合**恰为这 4 类**，不是每帧。
4. 排序键可逐条指认：**半径降序 → 重要度降序 → 节点 id 升序**。
5. 隐藏项同时带 `opacity: 0` **且** `aria-hidden="true"`；恢复时二者一起回来。
6. **永不隐藏清单**：选中节点、悬停节点、其 **1 跳邻居**的标签始终可见。
   ⇒ 断言：把某节点的标签人为制造重叠后，选中它 ⇒ 标签立刻回来（`opacity` 回到 1）。
7. **可见标签预算**：`floor(画布面积 / 9000)`；dmath/ch06 的 31 个节点**不触顶**；
   构造 120 节点场景时标签数被预算截住。
8. 节点上**看不到**「新 / 练 / 复 / 熟 / 重点练习 / 可以复习 / 已掌握 / 未标记」任何一个字。
9. `grep -c "line-clamp\|text-overflow" workbench/server/static/workbench.css` ⇒ 图谱区段 **0**。
10. 四条仓库级检查全绿（见 §8）。

## 6. 已知坑（至少一条来自 design.md / acceptance.md）

1. **`labelWidth()` 依赖 `shortTitle`，而标签要显示全文**（design.md D-6 的契约漂移段）。
   核心里 `labelWidth(title)`（`graph-physics-core.js:83`）与 `footprint()`
   （`:93-101`）用的是 `node.shortTitle || node.title`，
   而 `graphShortTitles()`（`workbench.js:1894`）会按 `graphTitleCut()`（`:1883`）
   在**第一个标点处截断**标题。
   ⇒ **本组只改「显示什么」**（不截断、换行），**绝不改 `shortTitle` 的产生**——
   改了它就会改 `labelWidth()` → 改 `footprint()` → **改布局物理** ⇒ **SI-0 直接红**。
   design.md D-6 的明文：「本变更**不删简称**（删了会让标签长 2–3 倍，且 `labelWidth()` 依赖
   `shortTitle` ⇒ 改布局物理，越界）」。
   ⇒ 标签显示**全文**与物理层**仍按简称**占位，可以同时成立：
   **显示**用 `node.title`，**占位**仍用 `node.shortTitle`。
   ⚠️ 但注意：`graphPaintNodes()` 现在写的是 `label.textContent` 在创建时设定
   （`workbench.js:2069` `node.shortTitle || node.title`）——
   本组若要显示全文，**要改这一行的读取对象**，这是**绘制层**改动，不是改 `shortTitle` 的**产生**。
   这一条**必须在汇报里说清**，因为它最容易被误读成「改了简称截断」。
2. **`--label-alpha`（第 1 组写的对数淡出）与本组的 `opacity: 0` 是两条独立通道**。
   design.md D-6.5：「隐藏（`opacity: 0` + `aria-hidden`）**优先于**淡出」。
   ⇒ 两个通道必须**相乘**而不是互相覆盖，且「永不隐藏」清单要**绕过两者**。
   实现上建议：`.label { opacity: var(--label-alpha) }` 作为底，
   隐藏时另加一个类/属性控制 `opacity: 0` 与 `aria-hidden`。
   **不要**用同一条 `opacity` 声明表达两件事。
3. **`getBoundingClientRect()` 会触发强制回流**（design.md D-6 代价段）。
   ⇒ 必须**一次批量读**全部标签（先循环读完，再统一写 hidden），
   **禁止**在读-写交替的循环里读。
4. **标签矩形要跟「点下缘 5px」对齐**（design.md D-6）。
   标签盒的上缘与点下缘之间是 **5 屏幕 px**（第 1 组 1.7 的 `.node-wrap` gap），
   而**不是** 0 ⇒ 去冲突时的矩形要按真实盒算，别拿点的中心当标签的锚。
5. **标签让位于邻点**（design.md D-6 代价段〔推断〕）：
   标签矩形 ∩ 邻点圆盘 ⇒ **先藏标签**；标签超出画布 ⇒ **先藏**。
   ⇒ 圆盘半径要用**绘制半径**（第 1/2 组的 `--node-d`），不是物理半径。
6. **`graphTitleCut` 的停用词表**（`workbench.js:1881`）与「不截断」是**两件事**：
   前者是物理占位用的简称生成，后者是显示层的截断策略。
   ⇒ 本组**不碰** `GRAPH_TITLE_STOP`。
7. **行号锚点全部过时**（同第 1 组坑 3）。tasks.md 的 `workbench.js:1290-1294`
   现在是 `:2365-2369`；`workbench.css:1710-1715` 现在是 `:3779-3784`。⇒ **按符号名重新 grep**。
8. **`label.title` / `button.title` 现在已是完整标题**（`workbench.js:2071-2072`）
   ⇒ 4.8「完整标题仍可达」**已成立**，本组只需**确认**没破坏它，不要重写。

## 7. 诚实汇报要求

- 报「已完成」之前，**必须**贴出 §5 第 1 条 `node tools/graph-layout-diff.js --diff …` 的
  **原样输出**（含 `total differences:` 与退出码）。没有这条输出 = 没验 = 不算完成。
- **必须**明确报告「显示用全文 / 占位用简称」这条取舍的实现位置，
  并附上 `git diff graph-physics-core.js` 为**空**的证明（证明没碰 `labelWidth()`）。
- 一旦 diff ≠ 0：**立刻停手**、定位越界改动、**回退**，不许用「差异很小」解释掉。
- 若 §2 的真实行号与汇报时的工作区**对不上**：**先 rebase，再重新 grep 定位**。
- 拿不准的（尤其「显示全文会不会改 `labelWidth()`」）：**停下来报告**，写清疑问与两个候选，**不许**硬做。
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
