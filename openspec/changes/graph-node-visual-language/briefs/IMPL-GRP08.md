# IMPL-GRP08 — 死规则清理（tasks.md 第 8 组）

> 派发单元：**tasks.md 第 8 组**（8.1–8.11）。
> 依赖：**第 2 组**（`.metric-track` / `.status-ring` 的 DOM 已删）、
> **第 3 组**（图例结构已重排）、**第 6 组**（焦点环已就位）。
> 下游：本组是第 11/13 组走查的前置。

## 1. 目标

删掉**能证明永不生效**或**已被新形态取代**的代码与样式（design.md D-10），
且**只删这些**。

清理后图谱区段里**不该再有**：
`.metric-track` / `.node-satellite` / `.node-unit` / `.meta` / `status-ring` /
`in-scope` / `.warning` / `.node-face` 这些名字。

## 2. 产物路径清单（唯一可写的产品文件）

| 文件 | 改什么（当前真实行号，2026-10-22 实测） |
|---|---|
| `workbench/server/static/workbench.css` | 删 `.node-wrap.in-scope .status-ring`（当前 `:3777`）；`.legend i.rel` 色改 `#757068`（当前 `:3865`）；删 `.metric-track`（当前 `:3733-3738`）；删 `.node-satellite`（当前 `:3762-3766`）；删 `.node-unit`（当前 `:3761`）；删 `.node-wrap.warning`（当前 `:3722`）；删 `--green` / `--graphite` 声明（当前 `:3584-3585`）；删 `.meta`（当前 `:3785-3788`）；删 `.status-ring`（当前 `:3740-3741`）与 `.node-face` 整套（当前 `:3743-3754`） |
| `workbench/server/static/workbench.js` | 删空函数 `graphSyncScope()`（当前 `:2152`）；删 `--metric-angle` 写入（当前 `:2142`）；删 `.node-unit` 写入（当前 `:2145`）；删 `.meta` DOM 创建（当前 `:2073-2076`）、写入（当前 `:2146-2149`）、可见性判定（当前 `:2400`）；删 `.metric-track` / `.status-ring` / `.node-satellite` 的 DOM 创建（当前 `:2049-2063`，若第 2 组已删则本组只做收尾） |

**只读、不许改**：`graph-physics-core.js` / `graph-renderer.js` / `pages.py` / `graph-physics.js`。

## 3. 文件所有权

- **独占**：无。
- **共享，必须串行**：`workbench.css`（与第 1/2/3/4/5/6/7/10 组共享）、
  `workbench.js`（与第 1/2/3/4/5/6/7/9 组共享）。
- **必须在这些组之后**：第 2 组（`.metric-track` / `.status-ring` DOM）、
  第 3 组（图例结构重排 —— 8.2 改 `.legend i.rel` 的色）、
  第 4 组（`.meta` 的状态文字）、第 6 组（`.node-face` 的 hover/selected 规则）。
  ⇒ **本组是 CSS/JS 侧的最后一棒**（第 10 组只改 token 块，仍在后面）。

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
   ⇒ **本组删 `--green` / `--graphite`（8.7）时，不要顺手改名其它 10 个**——
   那是第 10 组的活，**且第 10 组在本组之后**。
5. **主线那一侧**：`workbench.css` / `workbench.js` 的改动**必须**与主线的图谱页冻结块
   （`body:has(#layout[data-page="graph"])`，当前 `workbench.css:336-407`）兼容 ——
   冻结块保证**图谱页取值在主线改造期间一字不变**。
   ⚠️ **图谱 change 若要改那些取值，必须先解冻**（那是**另一个决定**，不是本轮能顺手做的）。

## 5. 验收标准（可机械判定）

1. `node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json`
   ⇒ `total differences: 0`，退出码 **0**。
2. **死规则断言**（8.10）：
   ```
   grep -cE "\.metric-track|node-satellite|node-unit|\.meta\b|status-ring|in-scope|\.warning|\.node-face" \
        workbench/server/static/workbench.css   # 图谱区段 ⇒ 0
   ```
   同名在 `workbench/server/static/workbench.js` ⇒ **0**。
3. `grep -c "graphSyncScope" workbench/server/static/workbench.js` ⇒ **0**。
4. `grep -c "in-scope" workbench/server/static/workbench.css workbench/server/static/workbench.js` ⇒ **0**。
5. `grep -c -- "--green\|--graphite" workbench/server/static/workbench.css` ⇒ **0**。
6. **图例「相关」色与画布一致**：`.legend i.rel` 的背景 = **`#757068`**；
   `graph-renderer.js` 的 `EDGE_COLORS.related` = `[117/255, 112/255, 104/255]` ⇒ 同值。
   ⇒ 截图取色比对必须一致。
7. **结构不变量**（SI-1 / SI-2 / SI-4）：节点 id 集合、边四元组集合、
   `scoreFor()` 的量值与投影映射**全部不变**。
8. `git diff` 里**没有**任何一行落在 D-13.1 的禁止清单上。
9. 四条仓库级检查全绿（见 §8）。

## 6. 已知坑（至少一条来自 design.md / acceptance.md）

1. **只删「能证明永不生效」或「被 A-24/A-28 明确取代」的代码**
   （design.md D-10 的规则段：「任何「可能由外部脚本触发」的怀疑都要停下来核实」）。
   ⇒ 本仓库是单页应用、作用域封闭；**每一条都要带 grep 证据**。
   ⇒ **不要**顺手删任何看起来「可能有用」的代码。
2. **`.meta` 与第 4 组的状态文字是同一件事的两端**：
   第 4 组 4.9 说「节点上不出现任何状态文字」，本组 8.8 说「删 `.meta` 的 DOM + 写入 + 可见性判定」。
   ⇒ **第 4 组先落地**（它把状态文字从节点上拿掉），**本组再删整个 `.meta` 元素**。
   ⇒ 两组都动 `graphUpdateNodeAppearance()`（当前 `:2138-2150`）⇒ **同函数 ⇒ 严格串行**。
3. **`.node-face` 的删除与第 6 组的 hover/selected 规则冲突**：
   6.7 要删 `.node:hover .node-face`（当前 `:3767-3770`）与
   `.node-wrap.selected .node-face`（当前 `:3771-3774`）里的阴影，
   而 8.9 要删 `.node-face` 整套（当前 `:3743-3754`）。
   ⇒ **第 6 组先**，本组后。⇒ 本组删完后，节点的 hover/selected 效果**必须仍然可见**
   （验收：截图上悬停/选中仍能看出换色 + 环 + 放大 + 标签提亮）。
   **若第 6 组把效果挂到了 `.node-dot` / `.node-focus-ring` 上，本组删 `.node-face` 就不影响它**
   ——这是本组最省事的路径。
4. **`.node-wrap.warning` 的死证据**：`grep -rn '"warning"\|node-wrap.warning' workbench/server/static/*.js`
   ⇒ **0 命中**（`workbench.js` 从不给 wrap 加 `warning` 类；
   `wrap.className = "node-wrap " + node.kind + " state-" + node.state`（当前 `:2043`），
   `node.kind` 只有 `core` / `support`）。
   ⇒ 删它是**有证据的**。
5. **`--green` / `--graphite` 零引用**：实测全仓只有声明（当前 `:3584-3585`），
   无任何 `var(--green)` / `var(--graphite)` 消费点 ⇒ 删得掉。
   ⇒ 但**它们在图谱区段外也是 0 引用**（图谱 `:root` 是全局 `:root`，所以这两个名字是全局可见的，
   删它们要确认**全仓**无引用，不止图谱区段）。
6. **`.node-wrap.in-scope .status-ring`**（当前 `:3777`）与空函数 `graphSyncScope()`
   （当前 `:2152`）是一对：CSS 规则等一个**永远不会被加上的类**，
   而唯一的加类者 `graphSyncScope()` **是空函数**。
   ⇒ 两条一起删（design.md D-10 第 1 项明写「两处一起删」）。
7. **`.meta` 的可见性判定在 `graphPaintNodes()` 里**（当前 `:2400`），
   而**行内 `opacity` 每次每帧都被重写** ⇒ 删的时候三处（DOM 创建 / 写入 / 可见性）**一起删**，
   漏一处就会留一个每帧写空值的死路径。
8. **`.node-unit` 的 `%` 从未显示过**：`{ display: none }`（当前 `:3761`）⇒ 写 `%` 是死写入。
   ⇒ 删它**不会**改任何可见行为。
9. **行号锚点全部过时**（同第 1 组坑 3）。tasks.md 的 `workbench.css:1664-1670` 现在是 `:3733-3738`；
   `:1693-1697` 现在是 `:3762-3766`；`:1716-1719` 现在是 `:3785-3788`；
   `workbench.js:998-1001` 现在是 `:2073-2076`；`:1072-1073` 现在是 `:2146-2149`；
   `:1322` 现在是 `:2400`。⇒ **按符号名重新 grep**。

## 7. 诚实汇报要求

- 报「已完成」之前，**必须**贴出 §5 第 1 条 `node tools/graph-layout-diff.js --diff …` 的
  **原样输出**（含 `total differences:` 与退出码）。没有这条输出 = 没验 = 不算完成。
- **必须**逐条列出删掉的每一项**及其 grep 证据**（design.md D-10 要求「每条都配了 grep 证据」）。
- **必须**报告：删完之后截图上悬停/选中**仍然看得出强调**（坑 3）。
- 一旦坐标 diff ≠ 0：**立刻停手**、定位越界改动、**回退**，不许用「差异很小」解释掉。
- 若 §2 的真实行号与汇报时的工作区**对不上**：**先 rebase，再重新 grep 定位**。
- 拿不准的（尤其「这条是不是真的永不生效」）：**停下来报告**，写清疑问与两个候选，**不许**硬做。
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
