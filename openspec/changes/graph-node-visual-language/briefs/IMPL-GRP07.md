# IMPL-GRP07 — 底噪光斑：保留观感，改绘制方式（tasks.md 第 7 组）

> 派发单元：**tasks.md 第 7 组**（7.1–7.7）。
> 依赖：**无**（底噪与节点形态无关，可与第 2/3/4/6 组并行准备）。
> 下游：本组落地后，第 10 组的夜纸 `.graph-tide` 透明度才有载体。

## 1. 目标

底噪**观感保留**（G-4：所有者说「其实那个还挺好看的」），但**绘制方式**从
「每帧 600 个 alpha 混合光斑」改成「**半分辨率预渲染 + 每帧一次 blit**」。

落地后：每帧的绘制调用从「600 个色斑 + 每节点 18,600 次距离计算」降到「一次 drawImage」。

## 2. 产物路径清单（唯一可写的产品文件）

| 文件 | 改什么（当前真实行号，2026-10-22 实测） |
|---|---|
| `workbench/server/static/workbench.js` | `graphTideState`（当前 `:2554`）加预渲染画布；`graphTideHash()`（当前 `:2565`）保留为种子源；`graphTideSurge()`（当前 `:2572`）改为对 blit 施加（7.4）；`graphTideResize()`（当前 `:2576`）负责重建预渲染（7.1）；`graphTideNodeMask()`（当前 `:2590`）改为「每可见节点一次径向渐变 + `destination-out`」（7.3）；`graphTideEdgeMask()`（当前 `:2607`）同理；`graphTideDraw(t)`（当前 `:2613`）改为一次 `drawImage`（7.2）；`graphTideFrame(now)`（当前 `:2703`）保留 reduced-motion 分支（7.5） |
| `workbench/server/static/workbench.css` | `.graph-tide`（当前 `:3690-3693`）**只读**：7.5 要求「CSS 的 `opacity: .62` 兜底不变」（reduced-motion 分支在 `:3933`）⇒ 本组**不改** CSS |

**不得新建产品文件**（离屏画布用 `document.createElement("canvas")` 内存创建，不落盘）。

## 3. 文件所有权

- **独占**：`workbench.js` 的 `graphTide*` 一族函数（当前 `:2554-2710` 区间）。
- **共享，必须串行**：`workbench.js`（与第 1/2/3/4/5/6/8/9 组共享**同一文件**——
  即使函数区间不重叠，**同文件并行改必冲突** ⇒ 严格按串行总表）。
  ⇒ **本组虽然逻辑上独立，但文件层面仍要排队。**
- **与第 10 组的耦合**：10.6 要在夜纸 token 块里给 `.graph-tide` 单独的透明度
  ⇒ 本组先落地，第 10 组后改。

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
2. **预渲染只建一次**：离屏画布在 `graphTideResize()` 时创建/重建，
   resize 之外**不重建** ⇒ 断言「连续 N 帧内离屏画布的引用不变」。
3. **每帧绘制调用数**：在 `graphTideDraw()` 内埋计数，
   ⇒ 每帧的绘制调用**不随节点数增长**（与色斑数无关）。
4. **节点遮罩开销与节点数成正比、与色斑数无关**：`graphTideNodeMask()` 每帧的渐变次数
   ≤ 可见节点数（31 节点 ⇒ ≤ 31 次），**不是** 600 × 31 = 18,600 次。
5. **观感仍在**：截图里底噪**仍读作极淡纸纹**（不是一片灰雾、不是纯色块）。
6. **不承载数据语义**：除 `graphTideNodeMask` / `graphTideEdgeMask` 外，
   tide 代码**不引用** `sim` 的节点 / 边 / 投影状态。
7. **reduced-motion 仍只画一帧**：`graphTideFrame()`（当前 `:2703`）在
   `prefers-reduced-motion: reduce` 下的行为与改造前一致（断言帧数 = 1）。
8. `.graph-tide` 的 CSS 兜底 `opacity: .62`（当前 `:3933`）**未改**。
9. 四条仓库级检查全绿（见 §8）。

## 6. 已知坑（至少一条来自 design.md / acceptance.md）

1. **「挖洞遮罩是底噪与数据的唯一耦合」**（design.md D-9 的理由段）。
   ⇒ 改预渲染时**不能**把节点挖洞一起省掉——那会让底噪糊住节点。
   ⇒ 挖洞**从「每色斑点 × 每节点的距离计算」改成「每节点一次径向渐变 + `destination-out`」**，
   语义等价、开销降两个数量级。
2. **`mix-blend-mode: multiply` 依赖底下的纸色**（`.graph-tide` 当前 `:3692`）。
   ⇒ 预渲染画布必须是**透明底**（不能烘一张不透明纸纹进去），
   否则 `multiply` 会算错。**先在离屏画布上画色带/尘埃，再 blit 到主画布**。
3. **半分辨率会柔化挖洞边缘**（design.md D-9 代价段：挖洞边缘在 ½ 分辨率下略有柔化）。
   ⇒ 这是**已知且接受**的代价，但**必须**在汇报里点名；
   并且**像素比对协议**要把 tide 画布列为**已知差异区**（D-12.3 / R-6）。
   ⇒ 建议本组同时在 `acceptance.md` 的产出清单里登记这一条（由主会话落）。
4. **「活纸纹」的手感靠缓慢漂移实现**（design.md D-9 的第 2 步：「一次 `drawImage`
   （带缓慢的亚像素漂移，保留现状的「活纸纹」感）」）。
   ⇒ 预渲染**不等于**冻结不动 ⇒ blit 时要带亚像素偏移。
   ⚠️ 但 `prefers-reduced-motion` 下**只画一帧**（7.5）⇒ 漂移也要一起停。
5. **潮涌（surge）语义**：现在 `graphTideSurge(amount)` 让底噪在求解时变密变亮
   （当前 `:2572`，调用点 `:2525`）。
   ⇒ 改成「对 blit 的整体 alpha / 缩放施加」时，**观感要接近**现状
   （acceptance.md M-6：「求解时底噪更密更亮的观感保留」）。
   ⇒ **不要**顺手删掉调用点 `:2525` 的 surge。
6. **`graphTideEdgeMask()`**（当前 `:2607`）也把每色斑 × 每边算一遍距离
   ——本组**只**被要求改节点遮罩（7.3）。
   ⇒ 边的遮罩可以**留原样**（若它已经是每边一次而非每色斑一次），
   **但要在汇报里说明现状的量级**，别默默放过一个同量级的热点。
7. **行号锚点全部过时**（同第 1 组坑 3）。tasks.md 的 `workbench.js:1482-1488`（色带）
   现在是 `:2557-2563`；`:1538-1626`（绘制）现在是 `:2613-2701`；
   `:1515-1530`（节点遮罩）现在是 `:2590-2606`。⇒ **按符号名重新 grep**。

## 7. 诚实汇报要求

- 报「已完成」之前，**必须**贴出 §5 第 1 条 `node tools/graph-layout-diff.js --diff …` 的
  **原样输出**（含 `total differences:` 与退出码）。没有这条输出 = 没验 = 不算完成。
- **必须**报告 §5 第 3/4 条的**实测计数**（每帧绘制调用数、每帧渐变次数），
  给出改造前后的对比数字（改造前的 18,600 次/帧来自 design.md D-9 的实测）。
- **必须**报告坑 3（半分辨率柔化）与坑 5（surge 观感是否保留）的结论。
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
