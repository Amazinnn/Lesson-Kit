# IMPL-GRP12 — 契约协调（tasks.md 第 12 组）

> 派发单元：**tasks.md 第 12 组**（12.1–12.9）。
> 依赖：**第 9 组**（缩放语义，产品手册要同步）、
> **第 10 组**（夜纸值集，产品手册要同步）。
> 下游：本组落地后，第 11 组走查的 §0.1 G-5 复核才有据。

## 1. 目标

把本变更的**用户可观察行为**同步到职责文件，并处理与 `workbench-visual-language-v2`
的两处 delta 冲突：

- `docs/PRODUCT-MANUAL.md` 知识图谱页章节同步新视觉语言；
- `docs/GLOSSARY.md` **不引入新的正式设计名词**（12.5）；
- `docs/ACTION-GRAPH.md` 复核后写明「无变更」（12.6）；
- 登记既有契约漂移（12.7）；
- 执行 **A-10.2 的归档顺序**（先合 v2，再 re-base 本变更的两块）。

## 2. 产物路径清单

| 路径 | 产物 |
|---|---|
| `docs/PRODUCT-MANUAL.md` | 知识图谱页章节（当前 `:152-182`）同步：节点形态、屏幕尺寸、标签规则、关系线与箭头语义、选中态、图例两块结构、夜纸表现、缩放语义（12.4） |
| `docs/GLOSSARY.md` | **不加新名词**；若实现中确需新词，走 `docs/PENDING-DEFINITIONS.md`（12.5） |
| `docs/PENDING-DEFINITIONS.md` | 只有在 12.5 判定确需新词时才写（当前**无**本变更遗留） |
| `docs/ACTION-GRAPH.md` | 复核后写明「无变更」；**注意**当前 `:29` 已有 2026-10-22 的一条图谱条目，**看它是否已经覆盖**（见坑 3） |
| `openspec/changes/graph-node-visual-language/specs/workbench-ui/spec.md` | 12.2 的 re-base（**主会话统一维护 ⇒ 见坑 4**）；12.7 的漂移登记 |
| `openspec/changes/graph-node-visual-language/specs/graph-visual-language/spec.md` | 12.7 的漂移登记（同上） |

**不得改**：产品代码（`workbench/` / `pool/` / `pipeline/` / `lessonkit.py`）。

## 3. 文件所有权

- **独占**：`docs/GLOSSARY.md`、`docs/PENDING-DEFINITIONS.md`、`docs/ACTION-GRAPH.md`。
- **共享，必须串行**：`docs/PRODUCT-MANUAL.md`
  （第 9 组 9.5 改缩放语义段 ⇒ **第 9 组先**；本组随后改图谱章节）。
- **主会话维护、本组不得擅改**：
  `openspec/changes/graph-node-visual-language/specs/**`
  （12.2 的 re-base 与 12.7 的登记都落在这里）——见坑 4。
  `openspec/changes/workbench-visual-language-v2/**`（**绝不许碰**）。
- **下游依赖本组**：第 11 组（§0.1 G-5 的职责文件同步复核）、第 13 组（门禁复核看 spec 一致性）。

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
2. **产品手册能逐条对上本变更的用户可观察行为**：
   - 节点形态：单层实心圆、半径 **5–13 屏幕 px**、无描边无投影；
   - 标签：点下方 **5px**、**12px** 恒定、**不截断**、重叠让位、**缩放 < 0.5 时按对数淡出**、
     **无状态文字**；
   - 关系线：屏幕恒定 **1.25px**、箭头语义、非邻接 **alpha 0.2**；
   - 选中态：**换色 + 1px 环 + 放大 + 标签提亮**；
   - 图例**两块**结构与随投影切换、夜纸表现、缩放语义（放大 = 拉开间距）。
   ⇒ 每条都能在手册里**找到对应句子**。
3. **`docs/GLOSSARY.md` 未引入新正式名词**：
   `git diff docs/GLOSSARY.md` ⇒ **只允许删除/澄清既有条目**，**不许新增 `###` 名词条目**。
4. **`docs/PENDING-DEFINITIONS.md` 里没有本变更遗留的未定义名词**（若 12.5 判定不需要新词 ⇒ 该文件**零改动**）。
5. **`docs/ACTION-GRAPH.md` 有对应记录**（哪怕是「无变更」的显式记录）。
6. **三条漂移在 delta 里有对应改写**（12.7）：
   ① `.meta` 的存在 vs `workbench-ui` 的「label/meta LOD」措辞 ⇒ delta 去掉 `meta`；
   ②「Node labels SHALL always display their complete text」vs 实现的简称截断
   ⇒ delta 改写成「显示时呈现的是它自己的完整文本」；
   ③ 量值投影半径读法（A-34）⇒ 两份 delta 口径一致（**下限 6.5px / 直径 13px，随量映射**）。
   ⇒ 且 **`Complete primary learning text`（`workbench-ui:697`）不被破坏**。
7. **A-10.2 的归档顺序**：先归档 `workbench-visual-language-v2`，再归档本变更；
   归档本变更前**逐字复核**两块需求的最终文本 = 「v2 的版本 + 本变更的图谱例外段落」。
8. **不许**改动 `openspec/changes/workbench-visual-language-v2/**` 的任何文件。
9. 四条仓库级检查全绿（见 §8）。

## 6. 已知坑（至少一条来自 design.md / acceptance.md）

1. **A-10.2 是硬性且不可颠倒的顺序**（design.md D-14.2 的「A-10.2 的硬性归档顺序」）。
   本变更的 `specs/workbench-ui/spec.md` 里 `Redundant state cues` 与
   `Soft Mondrian visual foundation` 两块**目前写的是「v2 之前的基线文本」**，
   文件头已标注「须在 v2 合入后 re-base 到 v2 的版本」。
   ⇒ **v2 未合入前，这两块无法 re-base** ⇒ **本组的 12.2 会被阻塞**。
   ⇒ **不要**为了「本组能做完」而自己编一版 re-base 文本。
   ⇒ 正确做法：把「等 v2 合入」作为**显式前置条件**写进报告，
   并把**当前能做的部分**（12.4 / 12.5 / 12.6 / 12.7 的漂移登记）做完。
   ⚠️ 而且 **12.3（退役 v2 的场景）必须等 v2 归档之后**才做（tasks.md 明写）。
2. **12.3 引用的场景名与行号与 v2 的实际文件对不上**（实测）：
   tasks.md 说「退役 v2 里的场景「The knowledge graph page is unchanged」（v2
   `specs/workbench-ui/spec.md:367-371`）」。
   实测 `openspec/changes/workbench-visual-language-v2/specs/workbench-ui/spec.md`：
   - `:367-371` **不是**那个场景（那里是「The transition survives the content being replaced」）；
   - 真正的场景叫「**This foundation leaves the knowledge graph page unchanged**」，
     在 **`:720`**；
   - 同一断言的**需求正文**在 `:686-691`（"This foundation SHALL leave the knowledge graph
     page's appearance unchanged"）。
   ⇒ **不要照抄 `:367-371`**；退役时按**场景标题**定位，并**连同需求正文里的那句一起处理**
   （否则正文还在说「leave the graph page unchanged」，与退役后的世界矛盾）。
   ⇒ **这条必须写进汇报**并提请主会话修正 tasks.md 的引用。
3. **`docs/ACTION-GRAPH.md` 当前 `:29` 已经有 2026-10-22 的图谱条目**，
   内容含「同心圆节点形态」——那是 **A-24 的旧形态**；
   最终形态是 **A-28 的单层实心圆**。
   ⇒ 12.6 说「复核后写明无变更」，但**那条已有的描述与最终形态不符** ⇒
   **需要更新那一条的描述**（动作集确实无新增/无退役/无改级，**但描述要改**）。
   ⇒ 在报告里写清「动作集无变更，但既有条目的描述按 A-28 校正」。
4. **`docs/PRODUCT-MANUAL.md` 当前 `:162-171` 描述的还是旧形态**
   （「同心圆节点」「淡色内核套一圈同色相的实色外环」「圆心只有一个数字…四个投影下都是同一个数」
   「节点越大、外环越粗」「选中的节点外环加粗变实」）。
   ⇒ 12.4 要把这几处**全部**改成 A-28/A-34 的最终形态
   （单层实心圆、无环、圆心数字按投影、选中是换色+1px 环+放大+标签提亮）。
   ⇒ 逐条列出改了哪几句。
5. **不许引入新的正式设计名词**（design.md D-14.5 / tasks 12.5）。
   「实心小圆点 / 绘制半径 / 物理半径 / 色键」是**几何与实现描述词**，**不是契约名词**。
   ⇒ 若实现时用了新词 ⇒ 进 `docs/PENDING-DEFINITIONS.md`，**不许**进 GLOSSARY 冒充契约名词。
6. **`workbench-ui` 的 `Redundant state cues` 与 `Soft Mondrian visual foundation`
   被两个变更同时改**（design.md D-14.2 第 2 条）。
   ⇒ 归档时**必须**先合 v2。
   ⇒ 本组**不许**碰 `openspec/changes/workbench-visual-language-v2/**`。
7. **图谱区的存量漂移还有一条**（本组顺手登记即可，不必改代码）：
   `docs/PRODUCT-MANUAL.md:170` 说「节点填充、**外环**、连线与标签」，最终形态**没有外环**。
8. **行号锚点**：本组的行号引用（`docs/PRODUCT-MANUAL.md:152-182`、
   `docs/ACTION-GRAPH.md:29`、v2 spec `:367-371` / `:720`）里，
   **v2 spec 的两处已被实测证伪**（坑 2）；产品手册的行号是**实测值**，可直接用。

## 7. 诚实汇报要求

- 报「已完成」之前，**必须**贴出 §5 第 1 条 `node tools/graph-layout-diff.js --diff …` 的
  **原样输出**（含 `total differences:` 与退出码）。没有这条输出 = 没验 = 不算完成。
- **必须**逐条列出产品手册改了哪几句（before / after），以及它们对应 design.md 的哪条决策。
- **必须**报告：12.2 / 12.3 因 A-10.2 顺序**被阻塞**的事实与前置条件（坑 1），
  **不许**把没做的部分报成做了。
- **必须**报告坑 2 的实测（v2 spec 的真实场景名与行号）。
- **必须**报告坑 3（ACTION-GRAPH 既有条目的描述需要校正）。
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
