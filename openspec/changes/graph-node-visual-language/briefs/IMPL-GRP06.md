# IMPL-GRP06 — 选中 / 悬停 / 聚焦：换色 + 1px 描边环 + 点放大 + 标签提亮（tasks.md 第 6 组）

> 派发单元：**tasks.md 第 6 组**（6.1–6.9）。
> 依赖：**第 2 组**（`.node-dot` / `.node-focus-ring` 的 DOM 已建）与**第 3 组**（色阶已定）。
> 下游：本组落地后，第 8 组 8.10 的死规则断言才能最终判过。

## 1. 目标

交互态的强调方式换成 Obsidian 式的**四通道**（design.md D-8）：

| 状态 | 点 | 环 | 标签 |
|---|---|---|---|
| 常态 | 绘制半径 5–13，投影色 | **无** | 常亮度 |
| 悬停 | **× 1.06** + 换色（更实的一档） | **1 屏幕 px** 描边环 | 提亮（字重 700） |
| 选中 | **× 1.12** + 换色（最实的一档） | **1 屏幕 px** 描边环 | 提亮（字重 700） |

并且**彻底删掉**「用阴影/光晕表示抬起」的做法。

## 2. 产物路径清单（唯一可写的产品文件）

| 文件 | 改什么（当前真实行号，2026-10-22 实测） |
|---|---|
| `workbench/server/static/workbench.css` | `.node-dot` 常态基线（2.4 已建，本组补「无描边无阴影」断言）；新增 `.node-focus-ring` 规则（6.2）；`.node:hover .node-face`（当前 `:3767-3770`）删 translateY 与阴影（6.7）；`.node-wrap.selected .node-face`（当前 `:3771-3774`）删纸色光晕（6.7）；`.label` 字重 650 → 700（6.5，当前 `.label` 在 `:3779-3784`） |
| `workbench/server/static/workbench.js` | 悬停/选中的**绘制半径倍率**（×1.06 / ×1.12，6.4）—— 落点见坑 3；`.node-wrap.dragging { z-index: 6 }`（当前 `:3719`）**保留**（6.8） |

**只读、不许改**：`graphApplyVisibility()`（当前 `:2154-2177`）的**判定逻辑**
（6.6 要求「一行不改」——**哪些元素被强调**是冻结的交互语义）。

## 3. 文件所有权

- **独占**：无。
- **共享，必须串行**：`workbench.css`（与第 1/2/3/4/5/7/8/10 组共享）、
  `workbench.js`（与第 1/2/3/4/5/7/8/9 组共享）。
- **与第 3 组的耦合**：6.3 的「更实的一档 / 最实的一档」**必须用第 3 组定的色阶**，
  ⇒ **第 3 组先落地**。
- **与第 4 组的耦合**：6.5 的标签字重与第 4 组的 `.label` 规则**同一块** ⇒ 串行。
- **与第 8 组的耦合**：8.9 删 `.node-face` 整套规则 ⇒ **第 8 组在本组之后**。

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
2. **常态基线**：截图里节点是**一枚平涂实心点**；computed `border-width` = 0、
   `box-shadow` = none、`background-image` = none。
3. **焦点环**：`.node-focus-ring` 常态 **`display: none`**（**不得**用 `opacity: 0` 的常驻环
   —— 那是 halo，不是环）；悬停/选中时 `display: block`；
   `border-width` 在**任意缩放下都等于 1 屏幕 px**。
4. **点放大**：悬停 / 选中时**绘制半径**分别为基线的 **1.06 / 1.12 倍**；
   ⇒ 断言：**选中前后的节点世界坐标 `(x, y)` 完全相同**（只改绘制，物理半径不动）。
5. **标签提亮**：悬停 / 选中时 `.label` 的 `font-weight` = **700**；
   **标签颜色与常态完全相同**（不靠改色强调）。
6. **删除阴影与光晕**：`grep -n "box-shadow" workbench/server/static/workbench.css` 的
   **图谱节点规则**里 **0** 处；`:3767-3770` 与 `:3771-3774` 的阴影与 `translateY(-1px)` 全删。
7. **`.node-wrap.dragging { z-index: 6 }`**（当前 `:3719`）**仍在**；拖拽中的节点仍在最上层。
8. `graphApplyVisibility()`（当前 `:2154-2177`）的**判定逻辑**零改动
   （`git diff` 只允许出现与 opacity 系数有关的行）。
9. 四条仓库级检查全绿（见 §8）。

## 6. 已知坑（至少一条来自 design.md / acceptance.md）

1. **放大只作用于绘制半径**（design.md D-8：「物理半径不动（A-26 / A-28.4）⇒ 布局不因
   选中/悬停而变」）。
   ⇒ 物理半径 `node.size` **一个字节都不许动**；
   放大必须落在**绘制**那一侧（第 1 组的 `--node-d` / `--node-box` 或第 2 组的
   `.node-dot` 尺寸）。
   ⇒ **验收第 4 条的「世界坐标完全相同」是这条的机械判据**，别跳过。
2. **「外环加粗」这条路在新形态下已经不存在**（design.md D-8 的「否则」段）。
   常态点无环 ⇒ 必须换一条通道 ⇒ 换色 + 细环 + 放大 + 标签提亮四通道。
   ⇒ 旧规则 `.node-wrap.selected .node-face { box-shadow: … 0 0 0 2px var(--paper) }`
   （当前 `:3773`）是**纸色光晕**，必须删；**不要**把它改成 1px 环来充数。
3. **1px 环要**屏幕**恒定** ⇒ 必须用 `calc(1px * var(--inv-scale))` 这类写法
   （第 1 组落的 `--inv-scale`），不能写死 `1px`。
   同理环的外扩 `inset` 也要按 `--inv-scale` 折算。
   ⇒ **实测**：在 0.25× / 0.5× / 1× / 2× 四个缩放下量环的屏幕宽度，都必须是 1px。
4. **环挂在哪一层**：`.node-focus-ring` 必须是 `.node` 的**兄弟子元素**（与 `.node-dot` 并列），
   且**绝对定位**相对 `.node`（`.node` 现在 `position: relative`）。
   ⇒ 若它被塞进 `.node-dot` 里，环会被 `border-radius: 50%` + `overflow` 裁掉。
5. **常态不得有常驻环**（design.md D-8 明文：「不得有 `opacity: 0` 的常驻环
   —— 那是「halo」，不是环」）。
   ⇒ 断言 `display: none`，不是 `opacity: 0`。
6. **`.node-face` 的整套规则由第 8 组 8.9 删**（当前 `:3743-3754`）。
   ⇒ 本组改 `.node:hover .node-face`（`:3767-3770`）与
   `.node-wrap.selected .node-face`（`:3771-3774`）时，
   **这些选择器在第 8 组之后就不存在了** ⇒ 本组要么把 hover/selected 的效果
   **改挂到 `.node-dot` / `.node-focus-ring`**（推荐，且与第 8 组不冲突），
   要么在第 8 组之后回来补。**推荐前者**，并在汇报里说明选择。
7. **`--state-color` 与「掌握 = 橙 / 需突破 = 砖红」的新映射**（第 3 组落的色键）。
   6.3 的「换色」要走**色阶**，不是 `--state-color`。
8. **行号锚点全部过时**（同第 1 组坑 3）。tasks.md 的 `workbench.css:1701-1703`
   现在是 `:3771-3774`；`:1707` 现在是 `:3776`；`:1709` 现在是 `:3773`。⇒ **按符号名重新 grep**。

## 7. 诚实汇报要求

- 报「已完成」之前，**必须**贴出 §5 第 1 条 `node tools/graph-layout-diff.js --diff …` 的
  **原样输出**（含 `total differences:` 与退出码）。没有这条输出 = 没验 = 不算完成。
- **必须**报告「点放大落在哪一层」的实测（选中前后世界坐标相同 + 绘制半径变了 1.12 倍）。
- **必须**报告坑 6 的选择（hover/selected 效果挂到哪个选择器上），以及它与第 8 组的先后。
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
