# IMPL-GRP10 — 夜纸适配（tasks.md 第 10 组）

> 派发单元：**tasks.md 第 10 组**（10.1–10.8）。
> 依赖：**第 3 组**（新色板的 token 已落）与**第 8 组**（`--green` / `--graphite` 已删）。
> 下游：本组落地后，第 11 组的夜纸对照截图（S-N1…S-N6）才有可比对象。

## 1. 目标

让图谱在**夜纸**下用**同色相、更亮更少饱和**的一套值（design.md D-12.1）：

- 图谱的 12 个裸名改名成 `--graph-*`（消除与主线 token 层的同名风险）；
- 新增 `html[data-theme="night"]` 块，重新声明图谱 token 的夜纸值；
- 夜纸下的关系线取**同色相**的夜纸值（图例同步跟随）；
- 夜纸下底噪单独压暗。

**只改配色**。图谱区段仍是自足的，不外泄到别的页面。

## 2. 产物路径清单（唯一可写的产品文件）

| 文件 | 改什么（当前真实行号，2026-10-22 实测） |
|---|---|
| `workbench/server/static/workbench.css` | 图谱 `:root` token 块（当前 `:3574-3587`）12 个裸名改名 `--graph-*` + **全部消费点**改引用；新增 `html[data-theme="night"]` 块声明图谱 token 夜纸值（10.2）；夜纸图例色键（10.4）；夜纸关系线值（10.5）；夜纸 `.graph-tide` 透明度单独给值（10.6） |
| `workbench/server/static/graph-renderer.js` | `EDGE_COLORS`（当前 `:15-21`）的**亮色**取值逐字节不变；夜纸关系线取值需要一个机制（见坑 3）——**与第 5 组同文件 ⇒ 第 5 组先落地** |
| `openspec/changes/graph-node-visual-language/specs/workbench-ui/spec.md` | A-16 与 D-12.1 的张力登记（10.3 的「显式登记」）—— **该 change 的 spec delta 属主会话统一维护的文件**（见坑 5） |

**不得新建产品文件**。

## 3. 文件所有权

- **独占**：无。
- **共享，必须串行**：
  - `workbench.css`（与第 1/2/3/4/5/6/7/8 组共享）⇒ **本组是 CSS 侧的最后一棒**；
  - `graph-renderer.js`（**第 5 组独占**）⇒ 第 5 组先；
  - `specs/workbench-ui/spec.md`（**主会话维护**）⇒ 见坑 5。
- **下游依赖本组**：第 11 组（夜纸对照截图）、第 12 组（产品手册的夜纸段落）。

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
   ⚠️ **本组是唯一被授权改名这 12 个裸名的一组**（design.md D-12.1 的既定决策）：
   改名成 `--graph-paper` / `--graph-ink` / `--graph-hair` / `--graph-blue` /
   `--graph-blue-soft` / `--graph-yellow` / `--graph-yellow-soft` / `--graph-red` /
   `--graph-red-soft` / `--graph-green` / `--graph-graphite` / `--graph-shadow`。
   ⇒ **改名只在本组发生**，且**不许**引入任何与主线 token 同名的变量。
5. **主线那一侧**：`workbench.css` / `workbench.js` 的改动**必须**与主线的图谱页冻结块
   （`body:has(#layout[data-page="graph"])`，当前 `workbench.css:336-407`）兼容 ——
   冻结块保证**图谱页取值在主线改造期间一字不变**。
   ⚠️ **图谱 change 若要改那些取值，必须先解冻**（那是**另一个决定**，不是本轮能顺手做的）。
   ⇒ **本组绝对不许碰 `workbench.css:336-407` 那一块冻结块**。

## 5. 验收标准（可机械判定）

1. `node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json`
   ⇒ `total differences: 0`，退出码 **0**。
2. **改名彻底**：图谱区段内 `var(--paper)` / `var(--ink)` / `var(--hair)` / `var(--blue)` /
   `var(--blueSoft)` / `var(--yellow)` / `var(--yellowSoft)` / `var(--red)` / `var(--redSoft)` /
   `var(--shadow)` **全部为 0 命中**；`--graph-*` 全部命中。
3. **区段外零引用**（10.7 的断言，按**当前**图谱区段边界算）：
   ```
   awk 'NR<3566 || NR>3954' workbench/server/static/workbench.css \
     | grep -cE 'var\(--(paper|ink|hair|blue|blueSoft|yellow|yellowSoft|red|redSoft|green|graphite|shadow)\)'
   ```
   ⇒ **0**。
   ⚠️ **必须用带右括号的严格正则**（见坑 1）。
4. **零全局依赖**：图谱区段内 `var(--lk-*)` / `var(--dsw-*)` / `var(--surface-*)` /
   `var(--role-*)` / `var(--ink-*)` / `var(--rule-*)` / `var(--r-*)` / `var(--asset-*)` ⇒ **0 命中**。
5. **夜纸块限定在图谱作用域**：新增的 `html[data-theme="night"]` 块里**所有**变量名
   都带 `--graph-` 前缀 ⇒ 断言该块内无一个非 `--graph-` 的变量声明。
6. **夜纸值逐字核对**（design.md D-4 夜纸列）：
   纸面 `#1c1a16`、墨 `#efe8db`；状态四色 `#9a938a` / `#d9a441` / `#e58a4f` / `#d4695a`；
   橙阶 `#be752d` / `#cd8a45` / `#dca067` / `#eba87a`；墨阶 `#efe8db` / `#9b9384` / `#78705f`；
   标签 `#c9c2b5`；圆心数字（夜纸）墨色 `#1c1a16`；关系线 `#7d9ad8` / `#cbb463` /
   `#d08a83` / `#9b958a` / `#4e4941`。
7. **夜纸下的对比度**：节点填充色对夜纸 **≥ 3:1**；圆心数字对其填充色 **≥ 4.5:1**；
   标签对夜纸 **≥ 4.5:1**。
8. **关系线的亮色取值逐字节不变**：`git diff graph-renderer.js` 里 `EDGE_COLORS` 块 ⇒ **空**。
9. **图例跟随**：夜纸下图例色块与节点实况**一致**（截图取色比对）。
10. **夜纸底噪单独给值**：夜纸下的 `.graph-tide` 透明度**不是**亮纸的 `opacity: .92` 沿用值；
    截图里底噪仍读作**极淡纸纹**，不是一片灰雾。
11. 四条仓库级检查全绿（见 §8）。

## 6. 已知坑（至少一条来自 design.md / acceptance.md）

1. **10.1 的验证命令（design.md D-12.1 原文）现在会给出 170 而不是 0**。
   实测：`awk 'NR<1497||NR>1884' workbench.css | grep -cE 'var\(--(paper|ink|...)\b'` ⇒ **170**。
   两个原因叠加：
   - **行号边界过时**：图谱区段现在在 `:3566-3954`，不是 `:1497-1884`
     （§5 第 3 条已给修正版命令）；
   - **正则用 `\b` 过宽**：`var(--ink-strong)` 之类会被 `\b` 匹配上
     （主线 v2 的 `--ink-strong` / `--ink-muted` / `--ink-faint` 等**不是**图谱的 12 个裸名）。
   ⇒ **必须用带右括号的严格正则**（§5 第 3 条）。
   ⇒ **在汇报里明确报告**：用**修正版**命令测得区段外 = **0**；
   用**原版**命令测得 170，原因是行号过时 + 正则过宽，**不是**有引用漏改。
   **这条会被第 13 组的门禁复核看到，必须写清。**
2. **图谱的 `:root` 块是全局 `:root`**（当前 `:3574`），不是图谱专属作用域
   —— 所以这 12 个裸名**全局可见**（虽然全仓**消费点**只在图谱区段）。
   ⇒ 改名时**只改消费点**（全仓 33 处 `var(--NAME)`，全部在 `:3566-3954` 内）
   + **声明处**（`:3575-3586`）；**不许**漏改，也**不许**把声明搬出 `:root`。
3. **关系线的夜纸值需要一个机制**（design.md D-12.2 的裁决只给了**值**，没给**机制**）。
   `EDGE_COLORS`（当前 `:15-21`）是 **JS 里的常量**，不是 CSS 变量 ⇒
   纯 CSS 夜纸块**改不到它**。
   ⇒ 可选机制：(a) 让 renderer 在夜纸下换一组常量；
   (b) 改成从 CSS 变量读（需要 `getComputedStyle`，每帧或每主题切换时读一次）。
   ⇒ **你选哪个都行，但必须在汇报里写清机制**，并且
   **亮色取值必须逐字节不变**（10.5 的硬要求）。
4. **A-16 与 D-12.1 的张力**（tasks.md 10.3 要「显式登记」）：
   v2 的 A-16 写「图谱纸面 token 恒为 `#fffdf7`、不参与夜纸换值」，
   而本变更 D-12.1 取夜纸纸面 `#1c1a16`。
   ⇒ 定稿口径是「**v2 不碰图谱（A-8）⇒ 夜纸适配整体归本变更 ⇒ 图谱纸面在夜纸下取 `#1c1a16`**」。
   ⇒ 登记要**显式**（不能靠时间戳或代码现状静默选边）。
   ⚠️ 但登记的落点是 **change 的 spec delta**，而那是主会话维护的文件（坑 5）。
5. **change 自己的 spec delta 由主会话统一维护**。
   10.3 要在 `openspec/changes/graph-node-visual-language/specs/workbench-ui/spec.md` 里
   显式登记 A-16 的张力。
   ⇒ **开工前先向主会话确认**：是本组直接改该 delta，还是本组产出**待登记文本**交主会话落盘？
   ⇒ **不许**自己决定改或不改。**没确认就不动这个文件**，其余部分照做。
6. **`html[data-theme="night"]` 的特异性**（design.md D-12.1）：
   它是 `(0,1,1)`，**高于** `:root` 的 `(0,1,0)` ⇒ 能压过图谱的 `:root` 块。
   ⇒ 这就是为什么夜纸块要用 `html[data-theme="night"]` 而不是 `:root`。
   ⇒ 但主线**已经有一个** `html[data-theme="night"]` 块（当前 `:253-…`）！
   ⇒ 你新增的块**必须落在同一个选择器上**，且**只声明 `--graph-*`**；
   **不许**动主线那个块里的任何一行。
7. **不许碰图谱页冻结块**（`workbench.css:336-407`）。红线第 5 条明写：
   「图谱 change 若要改那些取值，必须先解冻」。
   ⇒ 冻结块钉住的是主线的 `--surface-*` / `--ink-*` / `--role-*` / `--r-*` 等值
   （**不是**图谱的 12 个裸名）⇒ 本组的改名**不碰**冻结块，**天然兼容**。
   ⇒ 但**在汇报里要确认这一点**（证明你的 diff 没碰到 `:336-407`）。
8. **夜纸下的底噪**（10.6）：亮纸是 `opacity: .92` + `mix-blend-mode: multiply`
   （当前 `.graph-tide` 在 `:3690-3693`）；夜纸**不能沿用 multiply 的结果**，要单独给值。
   ⇒ 具体值由你定（design.md Open Questions 第 4 条允许就地定稿），
   但**必须显式给出**，并在截图里确认「仍读作极淡纸纹」。
9. **行号锚点全部过时**（同第 1 组坑 3）。tasks.md 的 `workbench.css:1505-1518` 现在是 `:3575-3586`；
   `workbench.css:1497-1884` 现在是 `:3566-3954`。⇒ **按符号名重新 grep**。

## 7. 诚实汇报要求

- 报「已完成」之前，**必须**贴出 §5 第 1 条 `node tools/graph-layout-diff.js --diff …` 的
  **原样输出**（含 `total differences:` 与退出码）。没有这条输出 = 没验 = 不算完成。
- **必须**报告坑 1：**修正版**命令的实测值（应为 0）+ **原版**命令的实测值（170）
  + 两者差异的原因拆解。**不许只报 0 而不提原版命令跑出 170**——
  第 13 组会照原版命令复跑。
- **必须**报告坑 3 选的关系线夜纸机制。
- **必须**报告坑 5 的处置（谁落的登记）。
- **必须**确认 `git diff` 未触及 `workbench.css:336-407`（冻结块）。
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
