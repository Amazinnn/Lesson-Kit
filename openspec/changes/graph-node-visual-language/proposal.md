# Proposal — graph-node-visual-language

> 视觉语言依据：`openspec/changes/workbench-visual-language-v2/decisions.md` 的
> 「图谱节点重设计」第 1–5 组（G-1…G-24）与「图谱现状的机制性诊断」。
> 事实依据：`tmp/frontend-audit/GRAPH-NODE-PIPELINE.md`（1114 行 / 180+ 处 `文件:行号`）。
> 两者均为**已拍板的输入**，本提案不重新裁决。
> 落地方式见 `design.md`。

---

## Why

图谱节点「丑」不是配色问题，是**缩放补偿缺失**与**视觉语言缺位**两件事叠在一起。

**实证（离线复算 `pool/dmath.db` 的 dmath/ch06：31 节点 / 35 关系）**

- 舞台级 `scale()`（`workbench/server/static/workbench.js:1106`）把节点直径、字号、点径
  **全部按世界像素一起缩小**，零屏幕补偿。Fit 后 scale = 0.17–0.49 ⇒
  **圆直径仅 3–30px、标签 2.0–5.9px、可见标签 0–1 / 31**
  （`workbench.js:1290-1294` 的缩放阈值 + `:1222-1225` 的 Fit 口径）。
  节点成了「看不清的斑点」。
- **学习状态在图上实质不可辨**：唯一承载它的 `.node-wrap.in-scope .status-ring`
  （`workbench.css:1708`）是**死规则**——`graphSyncScope()`（`workbench.js:1077`）是空函数，
  全仓无 `classList.add("in-scope")`。真正在线的只有 7px 世界像素的 `.node-satellite`
  （`workbench.css:1693-1697`，缩放后约 1–2px），而 **28/31 个节点同为 `state-new`**（同一个灰）。
  学习者无法从图上读出「哪个重要、哪个不会」。
- 同一个视觉通道还塞了两个维度：`.metric-track` 的**弧长**编码当前投影指标，
  **弧色**却编码知识点重要度（`workbench.css:1651-1652` 的 `--kind-color`）——
  看图的人无法把颜色和数字对上。
- 与此同时，整块画布每帧重绘约 **600 个 alpha 混合色斑**
  （`workbench.js:1482-1488` / `:1538-1626`），**与图谱数据完全无关**，
  视觉重量压过数据本身。

**结论**：图谱今天既没有「可读」也没有「好看」。**先让它可读（屏幕空间缩放补偿），
再给它一套视觉语言（形态 / 尺寸 / 配色 / 标签）**，而且这套语言必须自带色板——
图谱是数据可视化区，不是操作界面。

---

## What Changes

逐条对应所有者已拍板的 G-1…G-24（`decisions.md:776-888`）。**不新增任何后端字段。**

### 一、节点形态与尺寸

| # | 决策 | 本变更的落点 |
|---|---|---|
| **G-24** | **先修屏幕空间缩放补偿，再落视觉语言** | 新增一层「屏幕像素语义」：节点的绘制直径、字号、环线宽、点径不再跟随舞台 `scale()` 一起缩小；`scale()` 只负责**位置与间距** |
| **G-1** | 两个有层次的同心圆（内核 + 外环） | 节点 DOM 从「五层叠一个圆」（面 / 数字 / 度量弧 / 状态环 / 卫星点）改为**内核圆片 + 外环**两件；读作一枚带边的圆片 |
| **G-2** | **移除度量弧** | 删掉 `.metric-track`（`workbench.css:1664-1670`）与 `--metric-angle` 的写入（`workbench.js:1067`）；指标只用**颜色与大小**承载，语义仍来自既有字段，**不扩充后端能力边界** |
| **G-3 / G-17** | 尺寸体系：连续映射但收窄范围；**半径 14 → 30px**（A-10.1 收窄后） | 绘制半径 = `14 + 16·√score` **屏幕 px**（G-24 的单位），连续、单调、区间收窄（30→16）且下限抬升（10→14）⇒ **量值感仍在且不再挤**；「更强调」改由**同心圆的双层结构 + 色阶**承担，不靠更大直径（A-10.1）。外环线宽随同一个量值映射（1.5–4 屏幕 px），即「大小」含半径与环宽两维。布局用的世界尺寸 = 同一函数换算成世界 px（直径 28–60），物理与间距规则**不变** |
| **G-9** | 圆内只留一个数字 | 圆心恒为该节点的**正式题数**（**所有投影相同**）——投影的量由**大小 + 环宽 + 颜色**承载；名称在下方标签。`importance` 投影的百分号不再被 CSS 吞掉（`.node-unit{display:none}`，`workbench.css:1692`），圆心也不再随投影改写 |

### 二、颜色与图例

| # | 决策 | 本变更的落点 |
|---|---|---|
| **G-7 / G-16** | 图谱有**自己的色板**，不受全站「蓝/黄/红三角色」配额约束 | 图谱专属暖色板（见 `design.md` D-4 的完整色值表与对比度实算）。理由：图谱是数据可视化区，不是操作界面（所有者原话） |
| **G-8 / G-12** | 四个投影各有自己的色键；**分类用色，量值用单色阶** | 关系结构 / 学习状态 = 分类色；题目数量 / 重要性 = 同一色相的明度阶。两个同心圆**同色相两档**，不是两个色 |
| **G-13** | **内核淡、外环深** | 内核 = 色相底调（最轻），外环 = 同色相实色（最实） |
| **G-20 / G-21 / G-22** | 量值色相 = **橙**；状态四色 = **未学=中性灰 / 复习=琥珀 / 掌握=橙 / 需突破=砖红**；关系结构投影下节点色 = **墨阶三档** | 落在 `design.md` D-4 的色值表；四色与三档在两套纸面下的对比度均已实算 |
| **G-11 / G-14** | 必须有「什么颜色对应什么类型」的标注，且**随投影切换** | 底部图例改为两块：上半保留关系线型（现状），下半为**节点颜色**，随当前投影切换 |

### 三、标签、状态与交互

| # | 决策 | 本变更的落点 |
|---|---|---|
| **G-5** | 标签**常态可见但不抢眼**：字号略放大、**不截断**（换行显示全文）、完整标题由悬浮 / 键盘聚焦承载、降低对比度 | 标签改为**屏幕像素字号**（12px）、对比度下调但仍 ≥4.5:1、**不截断**（换行显示全文，不设行数上限、无省略号）、完整标题继续由悬浮与键盘聚焦承载（A-10.3：取「不截断」的一支 ——「两行上限」与既有 `Complete primary learning text` 正面冲突） |
| **G-6** | **节点上不允许任何状态文字** | 删除节点上的状态文字：`.meta` 行（`workbench.js:1072-1073`）与 `state` 投影写入圆心的单字「练/复/熟/新」（`workbench.js:578`、`:1060`）一并去掉。状态名仍保留在**学习看板、悬浮提示与无障碍名**里（不渲染为可见文字） |
| **G-23** | 标签重叠时**自动隐藏次要标签**（按节点大小与重要度排序让位），**不靠缩放** | 取代现有的「按缩放阈值隐藏标签」规则（`workbench.js:1290-1294`、`:1319-1321`） |
| **G-15** | 选中 / 悬停 / 聚焦：**外环加粗变实 + 节点轻微放大**；不再用阴影与卫星点光晕 | 去掉 `.node-face` 的 `box-shadow` 与 `.node-satellite` 的光晕（`workbench.css:1678`、`:1696`、`:1707`） |

### 四、底噪与连带修改

| # | 决策 | 本变更的落点 |
|---|---|---|
| **G-4** | 底噪光斑（`.graph-tide`）**保留**（所有者：「其实那个还挺好看的」） | 保留观感，改**绘制方式**：每帧 600 个 alpha 混合光斑 → 静态预渲染 / 降频（`design.md` D-9） |
| **G-18** | 关系线端点**接到外环边缘** | 节点改形后的**必要连带修改**：WebGL 端点半径改按新外环半径计算（`graph-renderer.js`）；**关系线本身的线型、粗细、颜色不改**（`workbench.js:607-609` / `graph-physics-core.js:1326-1329` / `graph-renderer.js:15-21`） |
| **G-10** | 只改节点外观（形态 / 尺寸 / 配色 / 标签），**布局物理、关系线、交互、投影语义一律不动** | 本变更的边界，见下节 Non-Goals |
| **G-19** | 夜纸下的分类色：**同一色相、提亮降饱和** | 图谱的 12 个自有裸名 token（`workbench.css:1505-1518`）新增夜纸值集（`design.md` D-12） |

### 五、顺带清理的死规则（不改行为，只删无效代码）

- `.node-wrap.in-scope .status-ring`（`workbench.css:1708`）与空函数 `graphSyncScope()`
  （`workbench.js:1077`）——`in-scope` 永不命中。
- 图例「相关」色 `#aaa399`（`workbench.css:1796`）与 WebGL 实际线色
  `rgb(117,112,104)` = `#757068`（`graph-renderer.js:15-21`）**不一致** ⇒ 图例改为实况值。
- `--green` / `--graphite` 两个裸名 token 全仓无 CSS 引用（`workbench.css:1515-1516`）。

---

## Capabilities

### New Capabilities

- **`graph-visual-language`**：知识图谱**节点视觉语言**的自足契约，覆盖五件事——
  ① 屏幕空间可读性（节点绘制尺寸 / 字号 / 线宽的屏幕像素语义）；
  ② 同心圆节点形态（内核淡 + 外环深 + 单一数值）；
  ③ 尺寸映射（连续、收窄、半径 14→30px）；
  ④ 四个投影各自的色键与随投影切换的图例；
  ⑤ 标签策略（常态可见、屏幕像素字号、**不截断**、重叠按重要度隐藏、无状态文字）
  ＋ 图谱自有暖色板与夜纸值集。
  **立为新能力而不是塞进 `workbench-ui` 的理由**：既有 `workbench-ui` 的图谱需求
  （`Metric projection morphology` 等）只约束了「半径随指标变大」这一条，
  从未定义节点的**形态、配色、图例与标签**；这四件事有独立的可观察契约
  （谁在什么投影下是什么颜色、什么被隐藏、什么字不许出现），
  放在一个能力里才有一个可验收的整体。

### Modified Capabilities

- **`workbench-ui`**：六条既有需求的**可观察行为**发生变化，逐条理由如下。
  （`openspec/specs/workbench-ui/spec.md` 的行号）
  1. `Knowledge graph page`（`:121`）——节点绘制尺寸与字号改为屏幕像素语义；
     现有条款「Viewport culling and label/meta LOD SHALL affect paint only」仍然成立，
     但**标签的可见性判据从「缩放阈值」改为「重叠让位」**（G-23），且节点不再有 `meta` 行。
  2. `Living graph motion and readable labels`（`:464`）——现有条款
     「label/meta LOD」与「Node labels SHALL always display their complete text」
     需要与 G-5 / G-6 对齐：标签常态可见、屏幕像素字号、不截断；
     **只在重叠让位或超出可见标签预算时隐藏**，不再按缩放阈值隐藏；
     **节点上不再出现状态文字**，完整标题继续由悬浮与键盘聚焦承载。
  3. `Metric projection morphology`（`:591`）——现有条款
     「A metric projection SHALL map higher values to both a larger node radius and a target
     nearer the canvas center」中的**半径区间**改为 A-10.1 收窄后的 **14→30 屏幕像素**
     （由新能力 `graph-visual-language` 的 `Screen-space sizing` 承载），
     并补上「外环粗细」这一条量值通道；「restrained, distinguishable Mondrian palette」
     改为**图谱自有暖色板**（G-7 / G-12 / G-16 / G-20…G-22）；
     同时明确**圆心恒为正式题数**、节点上不画进度弧或仪表。
  4. `Redundant state cues`（`:749`）——现有条款
     「graph learning states … SHALL retain text, outline, position, or another geometric cue」
     与 G-6「节点上不许有状态文字」需要协调：**冗余通道改为几何（半径序）+ 图例 +
     学习看板 + 无障碍名**，颜色不再是唯一载体，节点上也不再有状态文字。
  5. `Soft Mondrian visual foundation`（`:731`）——现有条款要求
     「restrained blue, yellow, and red accents」「Blue SHALL represent primary action…
     yellow… red…」。图谱的暖色板（琥珀 / 橙 / 砖红 / 中性灰 + 墨阶）是对三角色配额的
     **一处显式、限域的例外**，需要在该能力里写明例外范围。
     ⚠️ **并行冲突登记**：`workbench-visual-language-v2` 的 `workbench-ui` delta
     **已经 MODIFIED 了这一条**（`specs/workbench-ui/spec.md:317`，含场景
     「The knowledge graph page is unchanged」，`:367-371`）。该场景在本变更落地后
     **不再成立**，两处 delta 必须协调（建议：先合入 `workbench-visual-language-v2`，
     本变更在其之上追加「图谱例外」段落并退役该场景）。
     📎 **「亮色逐像素不变」这条约束不落在本变更头上**：
     `workbench-visual-language-v2/acceptance.md:22` 的 G-5 原文已写明
     「图谱**不在本变更的验收范围内**…零差异不是一条待达成的门禁，
     而是『本变更根本没碰它』的证明」⇒ 它是**那个变更**的否定式断言。
     本变更真正要守住的是它背后的意图：**图谱的 token 层不得被全站 token 层牵连**
     （图谱区段对全局 token 的引用必须保持 0 次）。
  6. `Graph detail is a learning dashboard`（`:406`）——**行为不变**，
     但学习看板成为 G-6 之后**唯一**在页面上呈现学习状态名称的位置之一，
     需在 delta 中点明，避免被误读为「状态被删了」。

  **不动**的既有图谱需求（不在本变更的 delta 里）：
  `State cluster layout`（`:643`）、
  `Layered knowledge relationships`（`:662`）、`Finite crossing optimization`（`:680`）、
  `Metric projection transition`（`:610`）、`Adjustable graph compactness`（`:510`）、
  `Knowledge view sorting`（`:560`）、`Graph state editing remains covered`（`:420`）、
  `Graph does not duplicate content editing`（`:434`）——它们的可观察行为不变。

  ⚠️ **一处修正**：`Multi-state graph filtering`（`:624`）**已在本变更的 delta 里
  MODIFIED**（此前被误列在「不动」清单里）。这次 MODIFIED **仅限保全式表述**：
  筛选**只改成员、不改外观**（存活节点保持同心圆形态与当前投影的配色，
  离场节点淡出而不变色），并加一条「筛选不新增状态通道」的保全条款 ——
  **筛选语义本身不变**（可选状态集合、可见节点的并集、边的保留规则、
  筛选状态仍是页面级），因此与「筛选语义不变」不冲突。

- **`review-workbench`**：**不动**。`Semantic graph attraction`（`:361`）约束的是
  图谱**模型**（正式题计数、关系去重、共现不臆造关系），与节点外观无关。
  本变更不新增任何关系、不改任何模型字段 ⇒ 无需 delta。

---

## Impact

### 代码（本次变更不写产品代码；以下为实现时必须触及的清单）

| 文件 | 落点 |
|---|---|
| `workbench/server/static/workbench.css` | 图谱专用区段 `:1497-1884`：图谱自有 `:root`（`:1505-1518`，新增夜纸值集）；节点规则（`:1643-1719`：`.node-wrap` / `.node` / `.metric-track` / `.status-ring` / `.node-face` / `.node-value` / `.node-satellite` / `.label` / `.meta`）；图例（`:1780-1799`）；缩放条（`:1800-1807`） |
| `workbench/server/static/workbench.js` | `graphCreateNodes()`（`:957-1053`，节点 DOM 重构）；`graphProjectionDisplay()`（`:1055-1061`）；`graphUpdateNodeAppearance()`（`:1063-1075`）；`graphSyncScope()`（`:1077`，空函数）；`graphApplyView()`（`:1104-1107`，写出缩放比）；`graphFit()`（`:1203-1229`）；`graphPaintNodes()`（`:1296-1325`，尺寸 / 标签可见性判定）；`graphTide*()`（`:1479-1660`，底噪改静态 / 降频） |
| `workbench/server/static/graph-physics-core.js` | `sizeFor()`（`:60-61`，半径区间）；`labelWidth()` / `footprint()`（`:82-101`）；`endpointRadius()`（`:1345-1347`，配合新外环）；`edgeStyle()`（`:1326-1329`）**不改** |
| `workbench/server/static/graph-renderer.js` | `EDGE_COLORS`（`:15-21`，**亮色主题不改**）；`draw()`（`:242-300`，端点按新外环半径收束） |
| `workbench/server/pages.py` | `graph_page()`（`:410-481`）：图例改为两块（`:462-467`）、`aria-label` 与无障碍名随节点语义更新 |

### 不改

- **后端 / 数据层**：`pool/`、`pipeline/`、`workbench/data/` 一行不动。
  **不新增任何学习事实、不新增任何持久字段、不改任何 API 请求序列与载荷。**
- **布局物理**：力模型、吸引强度、端口与车道、24px 逻辑间距、Worker 求解流程
  （`graph-physics-core.js` / `graph-physics-worker.js`）**语义不变**。
  只有节点**尺寸映射的取值**按 G-17 调整。
- **关系线**：线型、粗细、透明度、箭头方向、绘制顺序**不改**。
- **交互**：搜索、筛选、缩放、平移、Fit、拖拽、聚焦、聚拢滑杆、详情看板**不改**。
- **图谱以外的页面**：`workbench-visual-language-v2` 已把图谱从它的范围里摘出去
  （A-8），本变更同样**不碰图谱以外的任何页面**。

### 同一交付里必须同步的职责文件

- `docs/PRODUCT-MANUAL.md` —— 知识图谱页章节（图谱的配色、图例、标签规则、夜纸表现）。
- `docs/GLOSSARY.md` —— 若引入新名词（如「同心圆」「投影色键」），
  必须先在 `docs/GLOSSARY.md` 建条目；未定义的概念只能进 `docs/PENDING-DEFINITIONS.md`。
  **本提案暂未引入新正式名词**（沿用「指标投影」「冗余状态通道」「夜纸」
  「柔和蒙德里安 v2」等既有词），故 GLOSSARY 暂无强制改动；
  若 design.md 落地时确需新词，按纪律登记。
- `docs/ACTION-GRAPH.md` —— 本变更**不新增、不退役、不改级**任何动作，
  预计无需改动（实现时复核）。
- `openspec/specs/review-workbench/spec.md` —— 不动（见上）。

### 并行变更的协调点

| 并行项 | 关系 | 处理 |
|---|---|---|
| `workbench-visual-language-v2` 的 `workbench-ui` delta | 同改 `Soft Mondrian visual foundation` 与 `Redundant state cues` | 本变更在其**之后**落地，追加「图谱例外」段落；退役其「The knowledge graph page is unchanged」场景。**A-10.2 硬性顺序**：先合入 v2，再把本变更的这两块 **re-base 到 v2 的版本**；归档时逐字复核这两条需求的最终文本 |
| `workbench-visual-language-v2` 的 `design-notes/graph-isolation.md` | **移交清单**：把图谱的实测事实、22 条硬事实、像素级比对方案交给本变更 | 本变更**继承**其 §4（不可动的取值）、§5（自检清单）、§6（比对协议）；见 `design.md` D-12 |
| `workbench-visual-language-v2` 的夜纸值集 | 全站夜纸（`#1c1a16`）由它定 | 本变更的图谱夜纸值集**以它的夜纸基色为准**，不另立 |
