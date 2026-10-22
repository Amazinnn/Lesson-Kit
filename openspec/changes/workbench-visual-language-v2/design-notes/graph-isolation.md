# 知识图谱页移交清单（graph-isolation）

> **性质（2026-10-22 按 `decisions.md` **A-8** 改写）**：本文件原先是一份**隔离工程** ——
> 它的前提是「本变更要改 token，图谱必须被隔离」，因此列出 22 条禁止改动项（F-1…F-22）、
> 15 条静态断言、12 条运行时断言、6 条视觉断言与一整套像素级比对方案。
> **A-8 裁定「本变更不触碰图谱」**（夜纸下的图谱适配与图谱节点视觉重设计都归独立 change
> `graph-node-visual-language`），前提消失，本文件随之
> **从「隔离工程」变为「移交说明」**。
>
> **它现在的目的**：把图谱页的**实测事实**完整交给图谱 change —— 哪些 token 图谱在用、
> 图谱区段对 `--lk-*`/`--dsw-*` 的引用恰好是 0 次、哪些规则是死的、
> `--surface-sheet` 为什么必须恒为 `#fffdf7`、图例色与 WebGL 实际线色为什么不一致、
> 以及一旦被牵连会沿哪条链路传导。
>
> **执行与验收归 `graph-node-visual-language`**：§4 的禁止改动清单、§5 的自检清单、
> §6 的像素级比对方案**原文保留**，但它们的**执行主体**从「本变更的实现者」
> 变成「图谱 change 的实现者」。本变更只借用其中与「不误伤」有关的那一小部分
> （`acceptance.md` G-5 的否定式断言：改造前后图谱页截图必须无差异）。
>
> **本文件不提出任何图谱页的改动建议。**（这句保留：图谱的形态由 G-1…G-24 裁决，
> 不在本文件内另起炉灶。）
>
> **依据**：`decisions.md` **A-8**（图谱的夜纸适配并入图谱 change；本变更不碰图谱）、
> `decisions.md` G-10 / G-18 / G-19（节点重设计归独立 change）、
> `proposal.md`「Explicitly out of scope」、
> `acceptance.md` §0 **G-5**（否定式断言：本变更不得产生任何图谱观感变化）、
> `tasks.md` 1.1 / 1.2（本变更对图谱的唯一约束：零同名 + 不误伤）、
> `design-notes/night-paper-tokens.md` §1.2（图谱不在本变更范围内）、
> `decisions.md`「# 收口：最终基线」。
>
> **所有行号与数值均为实测**（`grep -n` / `sed -n` 于 2026-10-22 的工作区状态），
> 文件路径相对仓库根 `D:\Projects\Academic Workflow\lesson-kit`。
> 实测命令在每一节末尾给出，可逐条复现。
>
> **本文件不改动任何产品代码。**

---

## 移交清单摘要 — 图谱 change 接手时**必须知道**的硬事实

> 这一节是全文的入口。**执行与验收归 `graph-node-visual-language`**；
> 本变更只负责「不误伤」。

| # | 硬事实 | 实测依据 | 详见 |
|---|---|---|---|
| **H-1** | **图谱在用 12 个自己的裸名 token**（`--paper` `#fffdf7` / `--ink` `#191816` / `--hair` `#ddd8cd` / `--blue` `#2457c5` / `--blueSoft` / `--yellow` `#f2c94c` / `--yellowSoft` / `--red` `#d6453d` / `--redSoft` / `--green` `#4f9870` / `--graphite` `#2a2926` / `--shadow`），声明在 `workbench.css:1505-1518` | `grep -nE '^\s*--(paper\|ink\|…)\s*:' workbench.css` → 恰好 12 行，行号 ∈ [1506,1517] | §3.1 / §3.2 |
| **H-2** | **图谱专用区段（`workbench.css:1497-1884`）对全局 token 的引用恰好是 0 次** —— 14 种 `var()` 全部是图谱自有的 12 个裸名或 4 个本地变量（`--kind-color` / `--state-color` / `--size` / `--metric-angle`） | `awk 'NR>=1497&&NR<=1884' workbench.css \| grep -cE 'var\(--(lk\|dsw)-'` → `0` | §3.4（C-8） |
| **H-3** | **两套命名空间今天不相交**，图谱 `:root` **并不覆盖**任何全局值；它之所以安全，靠的是「同特异性 + 后写者赢」这条**顺序**（M-1…M-6） | 逐条机制分析 | §3.3 |
| **H-4** | **危险全部集中在 L2 外壳与区段外那 25 行**（顶栏 / 左栏 / 右栏 / 页面底色 / 字体栈 / 三栏几何 / 详情面板与关系行），共 **14 个全局 token 落点** | `grep -nE 'graph' workbench.css \| awk -F: '$1<1497\|\|$1>1884'` → 26 行，减 `:1047` 注释行 = 25 行 | §2.2 B / §3.2 / §3.5 |
| **H-5** | **图谱区段内零全局依赖，危险只有两类失败模式**：类型 I（L1 被污染：新层用了图谱裸名 / 在 `:1518` 后追加 `:root` / 用 `html[data-theme=…]` 压过）· 类型 II（L2 被改） | C-8 + M-4 / M-5 | §3.4 第 3 点 |
| **H-6** | **死规则**（声明了但永不生效，可安全清理）：① `--green` / `--graphite` 全仓**无 CSS 引用**（仅声明）；② `.node-wrap.in-scope .status-ring`（`workbench.css:1708`）永不命中，因为 `graphSyncScope()`（`workbench.js:1077`）是**空函数** | §3.2 末两行；`grep -n 'graphSyncScope' workbench.js` → `:1052` 调用 / `:1077` 空函数体 | §3.2 / §8 Q-10 |
| **H-7** | **图谱专用纸面 token 必须恒为 `#fffdf7`**，且**不能**用会随主题变的 `--surface-card`（夜纸值 `#232019`）顶上。命名存在漂移：`--surface-sheet`（design.md / tasks.md / decisions.md / component-spec.md / asset-spec.md / SYNTH.md）· `--surface-card`（原 night-paper-tokens §1.2）· `--surface-graph-sheet`（现 night-paper-tokens §3.1）—— **三个名字，同一个语义** | 逐文件比对 | §7.3（Q-6） |
| **H-8** | **图例色与 WebGL 实际线色不一致**：图例「相关」色 `#aaa399`（`workbench.css:1796`）与 SVG 边 `.graph-edge.related`（`:1636`）同值，但 WebGL 接管后 SVG 边被隐藏（`graph-renderer.js:148`），实际画出来的是 `EDGE_COLORS.related = [117/255, 112/255, 104/255]` = **`rgb(117,112,104)` = `#757068`** | `graph-renderer.js:15-19` | §8 Q-9 |
| **H-9** | **图谱缩放补偿缺失是「丑」的主因，不是配色**：舞台级 `scale()` 把所有排版单位一起缩小，实测 Fit 后 scale = 0.17–0.49 ⇒ 圆直径 3–30px、标签 2.0–5.9px、可见标签 0–1/31 | `decisions.md` 图谱现状的机制性诊断（G-24） | `decisions.md` |
| **H-10** | **像素级比对有三处天然不可比源**（时间驱动的环境色 canvas / Worker 物理迭代 / `localStorage` 布局缓存），必须各自冻结；`prefers-reduced-motion: reduce` 是**可复现的必要条件**，不是便利 | 三处冻结手段与实测 | §6.1 / §6.3 |

---

## 0. 修订记录（本轮实测复核后的更正）

> **A-8 之后的读法**：本节记录的是**实测复核**的结果（8 处不实引用的更正），
> 与 A-8 无关 —— 那些行号证据在图谱 change 接手时**照样成立**，一律保留。

上一轮因 provider 故障中断，本轮对既有 642 行逐条复核，**发现并更正 8 处不实引用**。
按 `AGENTS.md`「数值与行号必须实测核实」的要求，此处显式登记，不静默改写。

| # | 原引用 | 实测 | 性质 | 影响 |
|---|---|---|---|---|
| **C-1** | `workbench.css:1031-1032` = `code`/`pre` 底 | 实为 **`:1035-1036`**（`:1031` 是 `a:hover`，`:1032` 是 `ul`） | 行号错 | §3.1 落点更正 |
| **C-2** | `workbench.css:1189` = `#left-column/#ai-column` 的 `transition: transform 160ms ease` | `:1189` 是 `box-shadow: var(--dsw-shadow-lv3)`；该 `transition` 在 **`:1190`** | 行号错 | §3.7 / F-9 落点更正 |
| **C-3** | `workbench.css:442` = `.detail-block` 用 `--dsw-radius-lg` | `:442` 确是 `border-radius: var(--dsw-radius-lg)`（属 `.scope-tray-panel`）；而 `.detail-block` 在 **`:490`** 且用的是 **`--dsw-radius-sm`** | 归属错 | §3.4 落点更正 |
| **C-4** | `pages.py:68-109` = `shell()` | 实为 **`:68-110`**（`:110` 是 `return _base(...)`） | 行号错 | §1.1 更正 |
| **C-5** | F-4 称「表单控件在 Chrome UA 样式里**不继承** `font-family`，图谱搜索框字体由 UA 决定，与 `--dsw-font-family` 无关」 | **错**。`workbench.css:416` 的 `textarea, input[type="text"], input[type="number"], input:not([type])` 在 **`:423`** 写了 `font-family: inherit`；`:368` 的 `button` 在 **`:376`** 写了 `font-family: inherit`；`:327` 的 `select` 在 **`:334`** 写了 `font-family: inherit` | 事实错（结论加强） | 图谱搜索框/`.seg button`/`.icon-btn`/`.chip` **确实**继承 `--dsw-font-family` → F-4 的危险度被低估，理由重写 |
| **C-6** | F-5 称「字形与字宽全变 → 标签换行、节点间距观感变 → **整幅图谱重排**」 | **错**。`graph-physics-core.js:83-85` 的 `labelWidth(title)` = `Math.min(168, Math.max(62, Array.from(title).length * 12 + 18))` —— **按字符数估算，不读字体度量**；`:93-100` 的 `footprint()` 只用 `labelWidth` 与 `node.size` | 事实错（结论收窄） | 改字体**不会**让物理布局重排；但会改 `.label` 在 `max-width:168px` 内的换行与字形像素 → F-5 理由重写为「像素变，布局不变」 |
| **C-7** | §6.3 截图流程第 3 步等待 `#graph-solver-text` 的 `textContent === '已收敛'` | **无效谓词**：`pages.py:454` 服务端渲染的初始文本就是 `已收敛`，页面刚载入即满足 | 流程错 | §6.4 换成「`.solving` 类消失 + DOM 静止签名」双条件 |
| **C-8** | 「图谱专用区段 `:1497-1884` 一行不改」是唯一断言 | 实测：该区段内 **`var(--lk-*)` / `var(--dsw-*)` 命中 0 次**（`awk 'NR>=1497&&NR<=1884' workbench.css \| grep -cE 'var\(--(lk\|dsw)-'` → `0`） | 新增发现 | §2.4 确立「L1 零全局依赖」这一可断言的隔离性质 |

> **结论**：既有 642 行的**结构性结论全部成立**（图谱区段行号、12 个裸名、机制分析、
> 20 条 F 项、比对口径、待核项）。本轮**新增** 4 类内容：
> ① §2.4「L1 零全局依赖」实测；② §3.2「L2 的 14 个精确落点」实测表；
> ③ §4.9「六项硬边界」收尾专章；④ §5.4 单命令自检脚本 + §6.3 冻结三源 + §7 夜纸一致性核对。
> 同时把 F-4 / F-5 的**理由**按 C-5 / C-6 更正（结论不变，理由更准）。
>
> **A-8 之后**：这些更正**全部保留** —— 它们是图谱 change 接手时的实测底账，
> 与「谁负责改图谱」无关。

---

## 1. 一句话契约

> **图谱页不是一个独立页面，它是一条从服务端模板到 WebGL 画布的纵切链路；
> 这条链路上任何一环被全局 token 牵动，整页截图就不再像素一致。**
>
> 本次改造可以换掉整张设计语言，但**不能换掉这条链路上的任何一个取值**——
> 除非该取值在图谱作用域内被**重新钉回原值**。

**A-8 之后的读法**：上面这段仍然是图谱 change 动手时的**第一原则**。
差别只在**谁负责**：本变更不碰图谱，所以这句话现在约束的是
「本变更的 token 层不得牵连图谱」（`tasks.md` 1.1 / 1.2、
`acceptance.md` G-5 的否定式断言）；而「图谱自己怎么改、夜纸下长什么样」
归 `graph-node-visual-language`。

隔离分两层，两层都必须成立（实测口径不变）：

| 层 | 范围 | 隔离方式 | 实测依赖数 |
|---|---|---|---|
| **L1 图谱自身** | 画布、节点、边、图例、控制卡、缩放、toast、详情面板（节点/标签/边/控制卡） | 图谱专用 `:root`（`workbench.css:1505-1518`）+ 图谱专用区段（`:1497-1884`）——**一行不改** | **对全局 token 的引用 = 0 次**（C-8） |
| **L2 外围外壳** | 顶栏 / 左栏 / 右栏 / 页面底色 / 字体栈 / 三栏几何 / 详情面板与关系行 | 与全站共享 token——**必须为图谱页重新钉回当前取值**，否则 G-5 整页比对必 FAIL | **14 个精确落点**（§3.2） |

> **移交要点**：这两个数（**0 次** 与 **14 处**）是图谱 change 接手时必须先知道的。
> L1 天然自足 ⇒ 危险**全部**集中在 L2 与区段外那 25 行。

---

## 2. 移交清单 A：图谱页完整影响面清单（实测）

> **A-8 之后的读法**：这一节是**移交价值最高**的部分 —— 它是图谱 change
> 动手前必须先读完的「图谱由什么构成」的全量清单（68 行服务端 HTML + 388 行专用 CSS
> + 25 行区段外规则 + 6 个 JS 模块 + 4 个 API 端点）。
> 内容与实测命令**原样保留**，只是执行主体变了。

### 2.1 服务端渲染（HTML 结构）

**`workbench/server/pages.py`**

| 位置 | 内容 |
|---|---|
| `pages.py:410-481` | `graph_page()` 全体（`:410` 签名 → `:481` 闭括号） |
| `pages.py:415-416` | `_page_header(...)` → 标题「知识图谱」，副标题「约束布局 · 纸质图谱 · 蒙德里安」 |
| `pages.py:417` | `.page-content.graph-content` 容器 |
| `pages.py:418` | `header.graph-topbar` |
| `pages.py:419-420` | `#graph-search`（搜索框，`<input id='graph-search'>` **无 `type` 属性** → 命中 `input:not([type])`） |
| `pages.py:421-426` | `.seg#graph-views` — 4 个视图按钮（structure / problem_count / importance / state），默认 `.active` 在 structure |
| `pages.py:427` | `#graph-focus` 聚焦按钮 |
| `pages.py:428` | `#graph-fit` 适应画布按钮 |
| `pages.py:430` | `.graph-workspace#graph-workspace[data-dashboard='collapsed']` — **看板默认收起是像素基线的组成部分** |
| `pages.py:431` | `section.graph-shell#graph-canvas[tabindex=0]` |
| `pages.py:432` | `.floating.controls#graph-controls[data-collapsed='true']` — **控制卡默认收起** |
| `pages.py:433-435` | `#graph-controls-toggle` / 「图谱控制」 |
| `pages.py:437` | `.control-note`「保留原版语义」 |
| `pages.py:438-443` | `.filter-row#graph-filters` + 5 个 `.chip`（全部 / 重点练习 / 可以复习 / 已掌握 / 未标记） |
| `pages.py:444-447` | `#graph-gravity`（range，默认 85）/ `#graph-gravity-value` / `.hint` 文案 |
| `pages.py:448-451` | `.distance-scale` 三格（`#graph-strong-gap` / `#graph-medium-gap` / `#graph-weak-gap`） |
| `pages.py:452-458` | `#graph-solver-state`+`.solver-dot` / `#graph-solver-text` / `#graph-readability-state` / `#graph-edge-budget` |
| `pages.py:460` | `canvas.graph-tide#graph-tide` — **持续动画的环境色 canvas**（见 §6.3 A-1） |
| `pages.py:461` | `.graph-stage#graph-stage > svg.graph-edges#graph-edges` — SVG 边（被 WebGL 接管后隐藏，见 `graph-renderer.js:148`） |
| `pages.py:462-467` | `.legend#graph-legend` + 5 个 `.legend-item`（先修 / 相关 / 应用 / 对比 / 隐含） |
| `pages.py:468-471` | `.zoom` + `#graph-zoom-out` / `#graph-zoom-in` / `#graph-reset` |
| `pages.py:472` | `.toast#graph-toast` |
| `pages.py:474-477` | `aside#graph-detail-panel.graph-dashboard` — 学习看板（收起时 `display:none`，见 `workbench.css:1544`） |
| `pages.py:475-476` | `<p class='side-label'>学习看板</p>` + `<h2>` + `<p class='muted'>` — **`.muted` 类在图谱页可见**（F-13 的落点） |
| `pages.py:478-481` | 调 `shell(..., "graph", graph_mode=True, page_type="graph", ...)` |
| `pages.py:68-110` | `shell()` 全体——图谱页与其它页共用外壳（C-4 更正） |
| `pages.py:71-84` | `topbar` 字符串（顶栏三段式的改造点，F-12） |
| `pages.py:85` | `left = _left_column(workspace, workspaces, weak_items, active_nav)`（左栏改造点，F-12） |
| `pages.py:91` | `ai = _ai_column(workspace["name"], graph_mode, page_type)` — 图谱页右栏 |
| `pages.py:94-95` | `#layout[data-page='graph']` — **图谱页的唯一 CSS 作用域开关** |
| `pages.py:96` / `:98` | `#left-resizer` / `#right-resizer` — 列宽拖拽把手（在图谱页可见，见 `workbench.css:551`） |
| `pages.py:97` | `<main id='middle'> … <div id='middle-page'>` — 三栏骨架与视图转场容器 |
| `pages.py:100-102` | **仅图谱页注入**三个脚本：`graph-physics-core.js` → `graph-renderer.js` → `graph-physics.js` |
| `pages.py:1101-1103` | 样式表装载顺序：`workbench.css` → `agent-ui.css` → `katex.min.css` |

**`workbench/server/app.py`**

| 位置 | 内容 |
|---|---|
| `app.py:236` | 路由形态注释 `/w/{name}/{practice\|kps\|kp/{id}\|graph\|session-end}` |
| `app.py:260-265` | `page == "graph"` → `pages.graph_page(...)` |
| `app.py:85-87` | `GET /api/w/{name}/graph/model`、`POST /api/w/{name}/graph/state`、`POST /api/w/{name}/graph/kp` |
| `app.py:103` | `GET /api/w/{name}/graph`（raw artifact） |
| `app.py:145-146` | 走 `/graph/artifact` 分支 → `self._send_graph_artifact(path)` |
| `app.py:214-232` | `_send_static()` — **不发 `Cache-Control` / `ETag` / `Last-Modified`**（F-18） |
| `app.py:341-352` | `_send_graph_artifact()` |

> ⚠️ **F-18 的实测依据**：`app.py:224-231` 的成功分支只发 `Content-Type` 与 `Content-Length`
> 两行头就 `end_headers()` 了。没有任何缓存指令 → 浏览器启发式缓存可能把「改造后」的页面
> 配上「改造前」的 CSS。**截图前必须硬刷新**（§6.2）。

### 2.2 CSS

**A. 图谱专用区段：`workbench/server/static/workbench.css:1497-1884`（388 行，一行不改）**

| 区段 | 行 | 内容 |
|---|---|---|
| 区段注释 | `1497` / `1499-1503` | 「Knowledge graph V2 — constrained semantic layout, paper Mondrian skin.」 |
| 图谱专用 `:root` | `1505-1518` | 12 个图谱 token（清单见 §3） |
| 页面胶水 | `1520-1560` | `#layout[data-page="graph"] #middle`（`:1522`）/ `#middle-page`（`:1525`）/ `.page-header`（`:1526`）/ `.page-summary`（`:1527`）/ `.graph-content`（`:1528`）/ `.graph-workspace`（`:1529`）/ `.graph-dashboard`（`:1555-1560`）/ 看板收起（`:1541-1544`） |
| 顶栏 | `1562-1593` | `.graph-topbar`（`:1563`）及其 `.search`（`:1569`）/ `input`（`:1570-1573`）/ `.seg button`（`:1581`）/ `.icon-btn`（`:1589`） |
| 画布外壳 | `1595-1639` | `.graph-shell`（`:1597`，背景 `:1599-1602` = 两层 radial-gradient + `var(--paper)`）、`::before` 网格纹理（`:1604`）、`::after` 点阵、`.graph-tide`、`.graph-stage`、`.graph-edges` + 5 条边色 |
| 节点 | `1641-1719` | `.node-wrap` / `.metric-track` / `.status-ring` / `.node-face`（`:1674`）/ `.node-value`（`:1686`）/ `.node-satellite` / `.label`（`:1710`）/ `.meta`（`:1716`） |
| 浮动控制卡 | `1721-1776` | `.floating`（`:1723-1727`，阴影 `var(--shadow)` 在 `:1726`）/ `.controls`（`:1728`）/ `.control-toggle` / `.chip`（`:1751`）/ `.slider-block` / `.solver-line` / `.distance-scale` |
| 图例 / 缩放 / toast | `1778-1813` | `.legend` / `.legend-item`（`:1786`）/ `.zoom` / `.toast` + `graph-pulse` 关键帧（`:1772`） |
| 详情面板 | `1815-1859` | `#graph-detail-panel` 全部子规则 |
| 降级 | `1861-1867` | `@media (prefers-reduced-motion: reduce)` — `.graph-tide{opacity:.62}` 等 |
| 窄屏 | `1869-1884` | `@media (max-width:900px)` / `@media (max-width:640px)` |

**B. 图谱区段**之外**的图谱相关规则（最容易漏掉的一批 —— 不在 1497-1884 内，但同样属于图谱页）**

实测命令：

```bash
grep -nE 'graph' workbench/server/static/workbench.css \
  | awk -F: '$1<1497 || $1>1884'
```

命中 **26 行**，其中 `:1047` 是含 "choreography" 字样的无关注释（`/* visibility choreography (practice flow) … */`），非图谱规则。
**有效图谱规则 = 25 行**，分布在 4 段：

| 位置 | 选择器 | 依赖的全局 token |
|---|---|---|
| `workbench.css:509` | `.graph-content { max-width: none; }` | — |
| `workbench.css:510` | `#layout[data-page="graph"] #middle` | — |
| `workbench.css:511` | `#layout[data-page="graph"] .page-header` | — |
| `workbench.css:512` | `#layout[data-page="graph"] .page-summary` | — |
| `workbench.css:513` | `#layout[data-page="graph"] .graph-content` | — |
| `workbench.css:536-537` | `#graph-detail-panel` / `h2` | — |
| `workbench.css:538-547` | `#graph-detail-panel .graph-dashboard-metrics` | `:543` `--dsw-border-l1`（border）、`:544` `--dsw-radius-sm`（border-radius）、`:546` `--dsw-border-l1`（background） |
| `workbench.css:552-563` | `.graph-dashboard-metrics > div / span / strong` | `:557` `--dsw-bg-layer-1`（background）、`:560` `--dsw-label-secondary`（color） |
| `workbench.css:564-565` | `.graph-dashboard-note` / `.graph-dashboard-link` | — |
| `workbench.css:567-593` | `.graph-relations-panel` … `.graph-relation-row*` | `:575` `--dsw-border-l1`、`:576` `--dsw-radius-sm`、`:577` `--dsw-bg-layer-1`、`:580` `--dsw-label-tertiary`、`:585` `--dsw-label-secondary`、`:590` **`--lk-blue`**、`:591` **`--lk-red`** |
| `workbench.css:594-595` | `#graph-detail-panel label` / `select` | `:594` `--dsw-label-secondary` |
| `workbench.css:1167-1171` | `.graph-kp-selection` | — |
| `workbench.css:1572` | `.graph-topbar .search input { … outline: 0; … }` | — （`outline: 0` 是图谱自己的，**不得被全局焦点环清理顺手删掉**） |

> ⚠️ `workbench.css:1572` 的 `outline: 0` 不匹配任务 2.4 的 `grep -c "outline: *none"`
> （`outline: none` 只出现在 `338` / `427` / `833`）。但如果实现者把 grep 放宽成
> `outline:\s*(none|0)`，就会误删 `1572` → 图谱搜索框会突然出现全局焦点环 → 像素变化。

**C. 图谱运行时注入的样式**

| 位置 | 内容 |
|---|---|
| `graph-renderer.js:142-152` | `addStyle()` 动态创建 `<style id="graph-renderer-style">` |
| `graph-renderer.js:147` | `.graph-renderer-layer{position:absolute;left:0;top:0;z-index:1;pointer-events:none}` |
| `graph-renderer.js:148` | `#graph-canvas.graph-renderer-active .graph-edges{display:none}` — WebGL 接管后隐藏 SVG 边 |
| `graph-renderer.js:328` / `:352` | `graph-renderer-active` 类的增删 |

**D. 图谱自带的衬线字族栈（全仓库仅此 5 处，全部在图谱区段内）**

| 位置 | 声明 |
|---|---|
| `workbench.css:1688` | `.node-value { font-family: Georgia, "Songti SC", "STSong", "SimSun", serif; font-weight: 700; … }` |
| `workbench.css:1712` | `.label { font-family: Georgia, "Songti SC", "STSong", "SimSun", serif; … }` |
| `workbench.css:1742` | `.control-toggle strong { font-family: Georgia, "Songti SC", "SimSun", serif; … }` |
| `workbench.css:1748` | `.control-head strong { font-family: Georgia, "Songti SC", "SimSun", serif; … }` |
| `workbench.css:1823` | `#graph-detail-panel h2, h3 { font-family: Georgia, "Songti SC", "STSong", "SimSun", serif; … }` |

实测命令：`grep -n 'Georgia' workbench/server/static/workbench.css` → 恰好 5 行，行号如上。

> 这 5 处是**硬编码字族栈**，不引用任何 token。任务 3.2 引入 `--font-reading` 时若「顺手统一
> 全站衬线栈」，就会改到这 5 行 → 节点数字与标签的字形像素全变。
> **按 C-6 更正**：这**不会**让物理布局重排（`labelWidth` 按字符数算，见 §3.4 的实测），
> 但会让 `.label` 在 `max-width:168px` 内的换行行数变化 → 标签块高度变化 → 标签与邻点
> 的重叠关系变化。**像素变，布局不变。**

**E. 样式表装载顺序（`workbench/server/pages.py:1101-1103`）**

```
/static/workbench.css   →  /static/agent-ui.css   →  /static/katex/katex.min.css
```

`agent-ui.css` 在 `workbench.css` **之后**装载，因此 `agent-ui.css` 中的
`--lk-paper`（`:17 :39 :152 :165 :231 :368 :400 :424`，共 8 处）、
`--lk-paper-shade`（`:142`）、`--dsw-bg-layer-1`（`:5 :58`）、
`--dsw-radius-sm`（`:141`）、`--dsw-radius-md`（`:207 :241`）
同样落在图谱页的右栏上。

**F. 静态资源服务（`workbench/server/app.py:214-232`）**

`_send_static()` **不发送 `Cache-Control`、不发送 `ETag`、不发送 `Last-Modified`**。
→ 截图前必须显式绕过浏览器缓存（见 §6.2），否则「改造后」可能拿到「改造前」的 CSS。

### 2.3 JavaScript

| 文件 | 行数 | 角色 | 图谱页上的作用 |
|---|---|---|---|
| `workbench/server/static/graph-physics-core.js` | 1603 | DOM-free 的约束语义布局求解器；被 worker `importScripts` | 无 DOM 依赖 → 天然不受 CSS 影响。**但它读的 `stageWidth/stageHeight` 来自 DOM 测量**（`graph-physics.js:326-327`），所以 CSS 改画布尺寸 → 布局变 |
| `workbench/server/static/graph-physics-worker.js` | 100 | Worker 外壳 | `importScripts`（`:3`）、`self.onmessage`（`:60`）、`step` 分支（`:86-91`，单条消息最多 `8` 步在 `:88`） |
| `workbench/server/static/graph-physics.js` | 398 | 公共模块 + Worker 宿主 | `LAYOUT_CACHE_VERSION = 1`（`:28`）、`layoutStorageKey()`（`:43-48`）、`storage()`（`:50-53`）、`readLayoutSeed()`（`:55-67`）、`writeLayoutSeed()`（`:69-86`）、`new Worker("/static/graph-physics-worker.js")`（`:302-304`）、调用 `readLayoutSeed`（`:344`） |
| `workbench/server/static/graph-renderer.js` | 379 | WebGL2 边渲染器 | `addStyle()`（`:142-152`）、`attach()`（`:154`）、reduced-motion 判定（`:156-157`）、`resizeCanvas()`（`:188-197`，dpr 夹 1..2）、`applyLod()`（`:223-240`）、`draw()`（`:242`）、`render()`（`:307-314`） |
| `workbench/server/static/workbench.js` | 4888 | 图谱页的全部 DOM 侧逻辑 | `mountGraphPage()`（`:531-1941`，其中 `disposeGraphPage` 闭包 `:1927-1941`）；`mountMiddlePage()`（`:4871`）调 `graphPageDispose = mountGraphPage()`（`:4874`） |
| `workbench/server/static/middle-navigation.js` | — | 同工作区 SPA 换页 | `ensureGraphScripts()`（`:31-43`）、`installPage()`（`:68-80`，图谱分支 `:73-78`）、`installPageContent()`（`:82-93`，**`:87` `middlePage.innerHTML = nextPage.innerHTML;`**） |

**图谱页的关键运行时状态**（截图可比性的来源，见 §6.3）：

| 状态 | 位置 | 含义 |
|---|---|---|
| `graphTideState` | `workbench.js:1479` | 环境色 canvas 的动画状态；`reduced` 决定是否走 rAF 无限循环 |
| `graphTideState.reduced` | `workbench.js:1639` | `matchMedia("(prefers-reduced-motion: reduce)").matches` |
| `graphTideFrame()` | `workbench.js:1628-1636` | `:1634` `graphTideDraw(graphTideState.reduced ? 0 : now/1000)`；`:1635` 非 reduced 才重新排 rAF |
| `graphStartTide()` | `workbench.js:1638-1661` | `:1659` reduced 时只调 `graphTideFrame(0)` 一次；`:1660` 否则排 rAF |
| `graphTideResize()` | `workbench.js:1501-1513` | 用 `graphCanvas.getBoundingClientRect()` 定 tide 画布尺寸，dpr = `Math.min(2, devicePixelRatio)` |
| 求解收敛判定 | `workbench.js:1434`（`solving = sim.graph.alpha > 0`）、`graph-physics-core.js:1246-1260`（alpha 衰减 `:1246`；连续 15 帧稳定后 `settled = true` `:1260`；`:1252-1254` 是 120 轮安全阀） | **无随机数**（`graph-physics-core.js` / `graph-physics.js` 全无 `Math.random`）→ 收敛终点确定 |
| 求解态指示器 | `workbench.js:717-720` `graphSolver(solving)` | `:719` `classList.toggle("solving", …)`；`:720` 文本置「约束求解中」/「已收敛」。**调用点 `:1412-1413`** |
| 布局缓存 | `graph-physics.js:43-48`（key `lk_graph_layout_v1_<workspace>`）、`:69-86` `writeLayoutSeed()` | 落盘到 `localStorage`；**二次访问直接采纳缓存、不再重解**（`:344-369`） |
| 画布 resize | `graph-renderer.js:188-197` | backing store = `stageWidth × dpr`（dpr 夹 1..2） |
| 首次自动适配 | `workbench.js:1406-1411` | 收敛后**恰好一次** `graphFit()` → 决定整幅图谱的缩放（见 §4 F-22） |
| 渲染循环停泊 | `workbench.js:1460` | `if (solving || graphRenderDirty) graphEnsureLoop();` → 收敛且无脏标记即**停泊**，画面冻结 |

### 2.4 影响面小结（数量）

| 类别 | 数量 | 实测命令 |
|---|---|---|
| 服务端 HTML 行（图谱） | 68 行（`pages.py:410-481`）+ 3 行脚本注入（`pages.py:100-102`） | `sed -n '410,481p'` |
| CSS 图谱专用区段 | 388 行（`workbench.css:1497-1884`） | `sed -n '1497,1884p'` |
| CSS 图谱区段外的图谱规则 | **25 行**（`:509-513`、`:536-547`、`:552-565`、`:567-595`、`:1167-1171`） | `grep -nE 'graph' workbench.css \| awk -F: '$1<1497\|\|$1>1884'` → 26 行，减 `:1047` 注释行 |
| **CSS 图谱区段内的全局 token 引用** | **0 次**（C-8） | `awk 'NR>=1497&&NR<=1884' workbench.css \| grep -cE 'var\(--(lk\|dsw)-'` → `0` |
| **CSS 图谱区段外的全局 token 落点** | **14 处**（§3.2） | 见 §3.2 表 |
| CSS 运行时注入 | 2 行（`graph-renderer.js:147-148`） | `sed -n '142,152p'` |
| CSS 图谱区段内硬编码 hex | **83 处** | `sed -n '1497,1884p' workbench.css \| grep -cE '#[0-9a-fA-F]{3,6}'` → `83` |
| CSS 图谱自带衬线栈 | 5 处（`:1688/1712/1742/1748/1823`） | `grep -n 'Georgia' workbench.css` |
| JS 模块 | 6 个文件 | — |
| API 端点 | 4 个（`app.py:85-87`、`:103`） | `sed -n '85,87p;103p'` |

---

## 3. 移交清单 B：图谱专用 `:root` 与「零全局依赖」机制（实测）

### 3.1 图谱专用 `:root` 定义了什么（`workbench.css:1505-1518`）

```css
:root {                                   /* workbench.css:1505 */
  --paper: #fffdf7;                       /* :1506 */
  --ink: #191816;                         /* :1507 */
  --hair: #ddd8cd;                        /* :1508 */
  --blue: #2457c5;                        /* :1509 */
  --blueSoft: #edf2ff;                    /* :1510 */
  --yellow: #f2c94c;                      /* :1511 */
  --yellowSoft: #fff7cf;                  /* :1512 */
  --red: #d6453d;                         /* :1513 */
  --redSoft: #fff0ed;                     /* :1514 */
  --green: #4f9870;                       /* :1515 */
  --graphite: #2a2926;                    /* :1516 */
  --shadow: 0 7px 18px rgba(61, 52, 37, .06), 0 1px 2px rgba(61, 52, 37, .05);  /* :1517 */
}
```

### 3.2 引用点实测（全部落在 `1558-1850`，即 L1 之内）

| 变量 | 引用点 | 图谱上的表现 |
|---|---|---|
| `--paper` | `1559`（看板底）、`1567`（顶栏底）、`1602`（画布底）、`1676`（节点面渐变终点）、`1695`（卫星点描边）、`1704`（选中环外圈）、`1713`（标签 text-shadow） | **画布底色 = `#fffdf7`** |
| `--ink` | `1572`（搜索框文字）、`1817`（详情面板文字） | 详情面板主文字色 `#191816` |
| `--hair` | `1558`、`1566`、`1759`、`1832` | 面板/顶栏分隔线 `#ddd8cd` |
| `--blue` | `1587`、`1651`、`1656`、`1708`、`1756-1757`、`1762`、`1771`、`1848` | 先修边、核心节点、已掌握卫星点、激活 chip、滑杆强调色、求解中圆点 |
| `--blueSoft` | `1756`、`1848` | chip 激活底、关系标签底 |
| `--yellow` | `1652` | 支撑节点 `--kind-color` |
| `--yellowSoft` | `1850` | 关系标签底 |
| `--red` | `1653`、`1654`、`1849` | 警示节点、待办卫星点、关系标签 |
| `--redSoft` | `1849` | 关系标签底 |
| `--shadow` | `1726` | `.floating` 控制卡阴影 |
| `--green` | **无 CSS 引用**（仅声明） | — |
| `--graphite` | **无 CSS 引用**（仅声明） | — |

### 3.3 「为什么能覆盖全局值」—— 机制澄清（**这里与常见误解不同，必须照抄执行**）

> **实测结论：今天图谱的 `:root` 并不需要「覆盖」任何全局值，因为两套 token 的
> 命名空间完全不相交。**

| 层 | 变量名形态 | 声明位置 |
|---|---|---|
| 全局层 | `--lk-*`（8 个）、`--dsw-*`（30 个） | `workbench.css:4-46` |
| 图谱层 | `--paper` `--ink` `--hair` `--blue` `--blueSoft` `--yellow` `--yellowSoft` `--red` `--redSoft` `--green` `--graphite` `--shadow`（12 个） | `workbench.css:1505-1518` |

两套**没有同名项**。所以「图谱 `:root` 覆盖全局」这个说法在当前代码里是**不成立的**；
它之所以「看起来覆盖了」，是因为图谱的规则**只**引用自己的 12 个变量（如
`workbench.css:1602` 的 `var(--paper)`，而不是 `var(--lk-paper)`）。

**真正的机制与真正的风险：**

| # | 机制 | 事实 |
|---|---|---|
| M-1 | **特异性相同** | `:root` 是伪类，特异性 `(0,1,0)`。图谱 `:root`（`:1505`）与全局 `:root`（`:4`）**完全同级**。 |
| M-2 | **同特异性 → 后写者赢** | 若同名，图谱 `:root` 因在文件更后（`:1505` > `:4`）而**赢**。今天正是靠这条顺序「侥幸安全」。 |
| M-3 | **作用域是文档级，不是页面级** | `:root` 挂在 `<html>` 上。图谱的 12 个变量**在图谱页之外也生效**（只是没有规则引用它们）。这意味着：**任何页面新增一条引用 `var(--ink)` / `var(--paper)` 的规则，都会意外继承图谱的值**——新 token 层如果照抄 `--ink` 这个名字给别的语义用，会在图谱页之外静默串色。 |
| M-4 | **属性选择器 + 元素选择器会直接压过 `:root`** | `html[data-theme="night"]` 的特异性是 `(0,1,1)`，**高于** `:root` 的 `(0,1,0)`。**无论它写在哪一行**，都会覆盖 `workbench.css:1507` 的 `--ink: #191816`。 |
| M-5 | **文件末尾追加 `:root` 会反转顺序** | `workbench.css` 末尾是 `:1903`。若新 token 层在 `:1518` 之后（哪怕就在文件最末 `:1904`）追加任何 `:root` 块，它与图谱 `:root` 同特异性 → **后写者赢 → 图谱的 12 个值被顶掉**。 |
| M-6 | **`:root` 里的自定义属性没有作用域逃逸** | `var(--ink)` 在 `workbench.css:1572` 解析时向上找 `html` 上的 `--ink`。一旦 `html` 上的 `--ink` 变了，`1572` 的文字色就变。 |

**结论（给实现者的一句话规则）：**

> **新 token 层必须保证 `html` 元素上的 `--paper` / `--ink` / `--hair` / `--blue` /
> `--blueSoft` / `--yellow` / `--yellowSoft` / `--red` / `--redSoft` / `--green` /
> `--graphite` / `--shadow` 这 12 个自定义属性的取值，在图谱页上与今天完全一致。**
>
> 最安全的做法：**新 token 层不要使用这 12 个裸名**（改用 `--lk-*` / `--dsw-*` 前缀，或
> `--role-*` / `--surface-*` / `--color-*` 之类带前缀的族名）。任务 1.2 已经写了
> 「墨色 `--ink:#221f1a`」——**这个裸名与图谱的 `--ink:#191816` 直接冲突**，
> 是本次最容易踩的坑（见 §4 F-1 与 §5.1 断言 2）。

### 3.4 「零全局依赖」—— L1 的自足性（C-8 新增实测）

```bash
awk 'NR>=1497 && NR<=1884' workbench/server/static/workbench.css \
  | grep -oE "var\(--[a-zA-Z-]+" | sort | uniq -c | sort -rn
```

实测输出（**全部 14 种，无一条 `--lk-*` 或 `--dsw-*`**）：

```
      9 var(--paper          ← 图谱自有
      9 var(--blue           ← 图谱自有
      6 var(--kind-color     ← 图谱区段内本地定义（:1651-1653）
      4 var(--hair           ← 图谱自有
      3 var(--red            ← 图谱自有
      3 var(--size           ← JS 运行时写入（workbench.js:1309）
      2 var(--state-color    ← 图谱区段内本地定义（:1654-1657）
      2 var(--ink            ← 图谱自有
      2 var(--metric-angle   ← JS 运行时写入（workbench.js:1067）
      2 var(--blueSoft       ← 图谱自有
      1 var(--yellowSoft     ← 图谱自有
      1 var(--yellow         ← 图谱自有
      1 var(--shadow         ← 图谱自有
      1 var(--redSoft        ← 图谱自有
```

**这意味着什么（重要）：**

1. **L1 完全自足。** 图谱专用区段不引用任何全局 token。只要不动 `1505-1518` 这 12 个裸名的
   取值，**图谱自身的画布、节点、边、图例、控制卡、缩放、toast 就绝不会因全局 token 变化而变**。
   这是本次隔离最强的一条保证，也是 §5.1 断言 1 与断言 2 的依据。
2. **危险全部集中在 L2 与那 25 行区段外规则。** 图谱的「外壳」（顶栏 / 左栏 / 右栏 /
   页面底色 / 字体栈 / 三栏几何）与**详情面板 / 关系行**（区段外的 `:536-595`）是仅有的两处
   全局耦合点。
3. **「图谱页观感不变」的失败模式因此只有两类**：
   - 类型 I：**L1 被污染** —— 新层用了图谱的 12 个裸名之一（`--ink` / `--paper` / `--shadow` …），
     或在 `:1518` 之后追加了 `:root`（M-5），或用 `html[data-theme=…]`（M-4）压过。
   - 类型 II：**L2 被改** —— 底色 / 字体栈 / 圆角 / 描边 / 几何 任一变化。
   两类的完整清单在 §4。

### 3.5 图谱继承的全局 token 清单（L2 口径）

判定口径：**「改它会不会让图谱页的像素发生变化？」会 → 必须保持不变。**

#### 3.5.1 背景与纸面

| 全局 token | 定义 | 图谱页上的落点 | 判定 | 理由 |
|---|---|---|---|---|
| `--lk-paper` `#fffdf7` | `workbench.css:5` | `--dsw-bg-base`（`:16`）→ `body` 背景（`:67`）；`agent-ui.css:17/39/152/165/231/368/400/424` → 右栏 | **必须保持不变** | 改值 → 整页底色变 → 整页像素变 |
| `--lk-paper-shade` `#f3f1ea` | `:6` | `--dsw-sidebar-fill`（`:19`）→ `#left-column` 背景（`:168`）；`agent-ui.css:142` | **必须保持不变** | 改值 → 图谱页左栏底色变 |
| `--dsw-bg-layer-1` `#fffefa` | `:17` | `#topbar` 背景（`:102`）；`agent-ui.css:5 :58` `#ai-column` 背景；`workbench.css:557 :577`（详情面板指标格与关系行底） | **必须保持不变** | 改值 → 顶栏 + 右栏 + 详情面板变 |
| `--dsw-bg-layer-2` `#f3f1ea` | `:18` | `code`/`pre` 底（**`:1035-1036`**）；`agent-ui.css:208`；`workbench.css:490` `.detail-block` | **必须保持不变** | 改值 → 图谱页内代码块/详情块变（右侧栏可能含代码） |
| `--dsw-bg-base` | `:16`（别名 `var(--lk-paper)`） | `body` 背景（`:67`） | **必须保持不变（值）** | 同 `--lk-paper` |

> 现状备注：`--dsw-bg-layer-1` 与 `--lk-paper` 的差是 `rgb(0,-1,-3)`（`proposal.md:8-9` 已实测），
> 肉眼几乎不可分。**但像素比对会判 FAIL**——所以「肉眼没变」不是放行理由。

#### 3.5.2 墨色与文字

| 全局 token | 定义 | 图谱页上的落点 | 判定 |
|---|---|---|---|
| `--lk-ink` `#171717` | `:7` | `#topbar` 下边框（`:103`，2px）；`#left-column` 右边框（`:167`）；`#ai-column` 左边框（`:237`）；`agent-ui.css:11` `#ai-chat-head` 下边框 | **必须保持不变** |
| `--dsw-label-primary` | `:20`（别名 `var(--lk-ink)`） | `body` 文字色（`:66`）→ 图谱顶栏/图例/控制卡全部继承文字 | **必须保持不变** |
| `--dsw-label-secondary` `#61666b` | `:21` | `workbench.css:560 :585 :594`（图谱区段**外**：指标格说明、关系文本、详情面板 label）；`agent-ui.css:143` | **必须保持不变** |
| `--dsw-label-tertiary` `#81858c` | `:22` | `workbench.css:580`（`.graph-relation-type`）；`agent-ui.css` 多处 | **必须保持不变** |
| `--dsw-label-caption` `#adb2b8` | `:24` | `.topbar-separator`（`:127`） | **必须保持不变** |
| `--dsw-label-dimmed` `#e1e5ee` | `:23` | `::placeholder`（`:428`）→ 图谱搜索框占位符 | **必须保持不变** |
| `--dsw-border-l1` `rgb(0 0 0 / 4%)` | `:31` | `workbench.css:543 :546 :575`（图谱区段**外**） | **必须保持不变** |
| `--dsw-border-l2` `rgb(0 0 0 / 10%)` | `:32` | `agent-ui.css:19 :29 :52 :55 :140`（右栏） | **必须保持不变** |
| `--dsw-brand-accent` | `:27`（别名 `var(--lk-blue)`） | `workbench.css:551` `.column-resizer:hover`（左右列宽把手，图谱页可见） | **必须保持不变**（hover 态不在默认截图内，但 hover 态也归 G-5 管辖） |

#### 3.5.3 描边 / 分隔线

| 全局 token | 定义 | 判定 | 理由 |
|---|---|---|---|
| `--lk-ink`（作边框） | `:7` | **必须保持不变** | 三栏分隔线是图谱页构图的一部分；新基线「不用描边」的策略一旦落到 `#left-column`/`#ai-column`/`#topbar`，图谱页三栏边界形态改变 |
| `--dsw-border-l3` | `:33` | **本次允许改** | 图谱页无引用（实测 `grep -n 'var(--dsw-border-l3)' workbench.css` 命中行均在区段外且非图谱规则） |

#### 3.5.4 圆角

| 全局 token | 定义 | 图谱页上的落点 | 判定 |
|---|---|---|---|
| `--dsw-radius-sm` `6px` | `:43` | `workbench.css:544 :576`（图谱区段**外**：详情面板指标格、关系行）；`agent-ui.css:141`（右栏输入类）；`workbench.css:332`（`select`）、`:421`（`input`）、`:490`（`.detail-block`） | **必须保持不变** |
| `--dsw-radius-md` `6px` | `:44` | `agent-ui.css:207 :241`（右栏）；`workbench.css:202`（`.scope-tray-panel`）；`workbench.css:374`（`button` 全局 `border-radius: 18px` 是硬编码，不受影响） | **必须保持不变** |
| `--dsw-radius-lg` `22px` | `:45` | `workbench.css:442`（`.scope-tray-panel`）；图谱页无直接引用，但右栏若复用 `.detail-block`（`:490`，用 `--dsw-radius-sm`）则受影响 | **本次允许改**（图谱页无引用；**按「必须保持不变」执行更安全**） |

> **图谱自身的圆角全部硬编码**（`border-radius` 共 25 处，取值只有
> `4px` / `3px` / `2px` / `5px` / `999px` / `50%` 六种，
> 实测：`awk 'NR>=1497&&NR<=1884' workbench.css | grep -c 'border-radius'` → `25`；
> 行号 `1571 1579 1582 1591 1665 1672 1675 1694 1726 1736 1752 1766 1770 1774 1782 1789 1795 1803 1810 1829 1831 1838 1844 1847 1855`），
> **不引用 `--dsw-radius-*`**。因此「圆角统一 12px」（任务 1.3）**不会**直接改动图谱控件的圆角——
> 但会改动**图谱页外壳**（右栏 `agent-ui.css:141/207/241`、详情面板 `:544/:576`）的圆角。

> **C-3 更正**：`.detail-block` 在 `:490`，用的是 `--dsw-radius-sm`（不是 `--dsw-radius-lg`）。
> `--dsw-radius-lg` 在 `:45` 定义、`:442` 使用（`.scope-tray-panel`）。两者归属不同。

#### 3.5.5 字体（**按 C-5 更正，此项危险度被低估**）

| 全局 token | 定义 | 图谱页上的落点 | 判定 |
|---|---|---|---|
| `--dsw-font-family` | `:11-13` | `body { font-family: var(--dsw-font-family) }`（`:63`）→ 图谱顶栏、`.seg button`（`:1581`）、`.icon-btn`（`:1589`）、`.legend`（`:1780`）、`.chip`（`:1751`）、`.hint`（`:1763`）、`.solver-line`（`:1767`）等**全部非 Georgia 文字** | **必须保持不变** |
| **表单控件继承链** | `:334`（`select`）、`:376`（`button`）、`:423`（`textarea, input[type="text"], input[type="number"], input:not([type])`）均写 `font-family: inherit` | 图谱搜索框 `pages.py:420` 的 `<input id='graph-search'>` **无 `type` 属性** → 命中 `input:not([type])` → **继承 body 的 `--dsw-font-family`**；`.seg button` / `.icon-btn` / `.chip` 都是 `<button>` → 继承；`.legend-item`（`:1788` `font: inherit`）→ 继承 | **必须保持不变**（这条是 C-5 的更正，原文误判为「UA 字体，与 token 无关」） |
| `--dsw-font-code` | `:14-15` | `code`/`pre`（`:1035-1036`） | **本次允许改**（图谱画布不渲染代码；右栏若含代码块则受影响） |
| 图谱自带 Georgia 栈 | `:1688 :1712 :1742 :1748 :1823` | 节点数字、节点标签、控制卡标题、详情面板标题 | **必须保持不变**（硬编码，不改这 5 行） |
| 新 `--font-reading`（任务 3.2） | 待建 | 若实现「全站衬线统一」会改到上面 5 行 | **禁止施加于图谱区段** |

> ⚠️ **C-5 的实测证据**（原文说图谱搜索框「字体由 UA 决定，与 `--dsw-font-family` 无关」）：
> ```bash
> sed -n '416,426p' workbench/server/static/workbench.css
> # 416: textarea, input[type="text"], input[type="number"], input:not([type]) {
> # 423:   font-family: inherit;
> ```
> **图谱搜索框确实继承全局字体栈。** 改 `--dsw-font-family` 会让搜索框的字形/字宽变化 → 像素差。

#### 3.5.6 阴影

| 全局 token | 定义 | 图谱页上的落点 | 判定 |
|---|---|---|---|
| `--dsw-shadow-lv1` | `:36` | `workbench.css:189`（`.scope-tray-trigger`，图谱页已无此元素） | **本次允许改**（图谱页无可见落点） |
| `--dsw-shadow-lv2` | `:37` | 图谱页无引用 | **本次允许改** |
| `--dsw-shadow-lv3` | `:38-39` | `workbench.css:1189`（窄屏抽屉）；`agent-ui.css` 右栏浮层 | **必须保持不变**（右栏在图谱页可见） |
| 图谱 `--shadow` | `:1517` | `.floating` 控制卡（`:1726`） | **必须保持不变** |

#### 3.5.7 动效 / 时长 / 缓动

| 全局 token / 规则 | 定义 | 图谱页上的落点 | 判定 |
|---|---|---|---|
| `@media (prefers-reduced-motion: reduce)` 全局降级 | `workbench.css:1126-1131` | `transition: none !important; animation: none !important` 作用于**全部元素** | **必须保持不变** | 删掉它 → 图谱页 `.node-face` 的 `transition: transform .18s…`（`:1680`）、`.label` 的 `transition: opacity .16s`（`:1714`）、`.meta` 的 `transition: opacity .16s`（`:1718`）、`.toast`（`:1810`）恢复 → 截图时序敏感、像素不可比 |
| `graph-pulse` 关键帧 | `workbench.css:1771-1772` | 求解中圆点脉冲（`1s ease-in-out infinite`） | **必须保持不变** |
| 图谱 reduced-motion 区段 | `workbench.css:1861-1867` | `.graph-tide{opacity:.62}` / `.node-wrap,.node-face,.label,.meta,.toast{transition:none}` / `.solver-state.solving .solver-dot{animation:none}` | **必须保持不变** | 它是 §6.3 冻结方案的技术基础 |
| `#layout { transition: grid-template-columns 200ms ease }` | `workbench.css:161` | 三栏宽度过渡 | **必须保持不变（值）** | 任务 4.1 要求把它收编到 `--motion-*` token；**值必须仍是 200ms**，否则截图时若列宽在动，图谱画布尺寸会漂 |
| `#left-column/#ai-column { transition: transform 160ms ease }` | `workbench.css:1190`（C-2 更正） | 窄屏抽屉 | **必须保持不变（值）** |

#### 3.5.8 布局 / 结构 token

| 项 | 定义 | 图谱页上的落点 | 判定 |
|---|---|---|---|
| `#layout` 三栏几何 `280px minmax(0,1fr) 420px` | `workbench.css:160` | 图谱页中栏宽度 → 画布宽度 → **auto-fit 缩放** | **必须保持不变（值）**；任务 11.1「改为 CSS 变量驱动」**可以改写法，但值不能变** |
| `.page-header, .page-content { max-width: 800px }` | `workbench.css:252-253` | 被 `.graph-content{max-width:none}`（`:509`）覆盖 | **必须保持不变** |
| `#middle-page > .page-header { padding-right: 128px }` | `workbench.css:255` | 图谱页 `.page-header` 在 `#middle-page` 内 → **生效** | **必须保持不变**（任务 11.2 要删它 → 会让图谱页标题右移 → 像素变。**必须为图谱页保留**） |
| `#middle { padding: 34px 40px 48px }` | `workbench.css:175` | 图谱页中栏内边距 → 画布可用宽 | **必须保持不变** |
| `.graph-workspace { gap: 12px; padding-top: 12px }` | `workbench.css:1529-1537` | 图谱区段内 | **必须保持不变** |
| `#middle { overflow: hidden }` | `workbench.css:510 :1523` | 图谱页中栏不滚动 | **必须保持不变** |

#### 3.5.9 判定汇总

| 类别 | 必须保持不变 | 本次允许改 |
|---|---|---|
| 背景 / 纸面 | 5 | 0 |
| 墨色 / 文字 / 描边 | 9 | 1 |
| 圆角 | 3 | 0（`--dsw-radius-lg` 无图谱落点，仍按不变处理） |
| 字体 | 3（+ 图谱自带 5 行硬编码） | 1 |
| 阴影 | 2 | 2 |
| 动效 / 时长 | 6 | 0 |
| 布局 / 结构 | 6 | 0（可改写法不可改值） |
| **合计** | **34 项** | **4 项** |

---

## 4. 移交清单 C：图谱 change 接手时必须遵守的硬事实（F-1…F-22）

> **A-8 之后的读法**：这 22 条原是「**本变更的**禁止改动清单（可执行）」——
> 它们防的是「新 token 层牵连图谱」。A-8 之后本变更不碰图谱，
> 它们因此变成**图谱 change 接手时必须知道的硬事实**：
> 哪些取值不能动、动了会沿哪条链路传导、正确做法是什么。
> **执行与验收归 `graph-node-visual-language`**；
> 本变更只借用 F-1 / F-2（零同名）作为「没有误伤」的证据。
>
> 表中出现的「任务 N.N」是历史锚点引用（指向本变更各阶段的编号），
> **引用保留**以免丢失出处；A-8 之后它们的执行主体已变。
>
> 每行的「替代做法」都是**不改图谱**的合规路径。表中的「位置」是**必须核对的锚点**。

| # | 改动点 | 位置 | 为什么危险 | 替代做法 |
|---|---|---|---|---|
| **F-1** | 新 token 层定义裸名 `--ink` | 新 `:root`（`workbench.css:4-46` 内） | **与图谱 `--ink:#191816`（`:1507`）同名**。同特异性后写者赢；图谱 `:root` 在 `:1505` 更靠后，今天侥幸赢；一旦有人在 `:1518` 之后追加 `:root`（M-5），或写 `html[data-theme="night"] { --ink: … }`（M-4，特异性更高，**无视顺序**），图谱详情面板文字（`:1817`）与搜索框文字（`:1572`）色立刻变 | 给新墨色取带前缀的族名（`--role-ink` / `--color-ink` / `--lk-ink-v2`），**不要用 `--ink`**。若已用 `--ink`，则在夜纸块里显式重钉 `--ink:#191816` |
| **F-2** | 新 token 层定义裸名 `--paper` / `--shadow` / `--blue` / `--red` / `--yellow` / `--hair` / `--*Soft` / `--green` / `--graphite` | 同上 | 12 个图谱 token 全部裸名（`workbench.css:1506-1517`），撞一个改一个。其中 `--paper` → 画布底色（`:1602`）、`--shadow` → 控制卡阴影（`:1726`）、`--blue` → 先修边与核心节点色（`:1651/1656/1708/1756/1762/1771/1848`）、`--red` → 警示节点（`:1653/1654/1849`） | 新层一律用带前缀族名（`--surface-*` / `--role-*` / `--shadow-*` / `--hair-*`）。落地前用 §5.1 的 grep 断言 12 个名字各只声明一次 |
| **F-3** | 全局圆角变量 `--dsw-radius-sm/md/lg` 改值 | `workbench.css:43-45`（任务 1.3 要改） | 图谱页**外壳**用它：`agent-ui.css:141`（`--dsw-radius-sm`）、`:207 :241`（`--dsw-radius-md`）、`workbench.css:544 :576`（图谱区段**外**的详情面板指标格/关系行）、`:332 :421`（图谱页右栏的 `select`/`input`）→ 右栏与详情面板圆角变 | 改值可以（任务 1.3 的目标），但**必须为图谱页作用域重新钉回 `6px/6px/22px`**：`#layout[data-page="graph"] { --dsw-radius-sm:6px; --dsw-radius-md:6px; --dsw-radius-lg:22px; }` |
| **F-4** | 全局字体栈 `--dsw-font-family` 改值 | `workbench.css:11-13` | `body` 继承（`:63`）→ 图谱顶栏、`.seg button`、`.icon-btn`、`.legend`、`.chip`、`.hint`、`.solver-line` 全部文字字形/字宽变。**按 C-5 更正**：表单控件**也**继承 —— `:334`（`select`）、`:376`（`button`）、`:423`（`input:not([type])`，图谱搜索框命中）都写了 `font-family: inherit`，所以图谱搜索框与所有图谱按钮的字形**同样随全局字体栈变** | 图谱页作用域钉回原栈：`#layout[data-page="graph"] { --dsw-font-family: <原值>; }`。注意：图谱区段内那 5 处 Georgia 硬编码（`:1688/1712/1742/1748/1823`）**不随** `--dsw-font-family` 变，不需要额外处理 |
| **F-5** | 「全站衬线统一」把图谱的 Georgia 栈换成 `--font-reading` | `workbench.css:1688 :1712 :1742 :1748 :1823` | **按 C-6 更正理由**：字形与字宽全变 → `.label`（`:1711` `max-width: 168px`）内的换行行数可能变化 → 标签块高度变化 → 标签与邻点的重叠关系变化 → **像素变**。但**不会**让物理布局重排：`graph-physics-core.js:83-85` 的 `labelWidth(title)` = `Math.min(168, Math.max(62, Array.from(title).length * 12 + 18))` 是**按字符数**估算，不读字体度量；`:93-100` 的 `footprint()` 只用 `labelWidth` 与 `node.size` | 这 5 行**保持原样**。新阅读面字体只接到题面/知识点正文/解析（任务 3.3 的三处） |
| **F-6** | `#middle-page` 视图转场动画 | 新增（任务 17.1） | `#middle-page` 是**全站共用容器**（`pages.py:97`），图谱页的 `.page-header` / `.graph-content` 是它的子节点。实测 `grep -n 'middle-page' workbench.css` 只有 3 处（`:255` padding、`:1198` 窄屏 padding、`:1525` 图谱 flex），**今天没有任何 `#middle-page` 动画** → 任务 17.1 是**全新引入**，默认会命中图谱页。若实现为 `#middle-page > * { animation: lk-rise … }`（innerHTML 替换后新子节点重新触发），**图谱页每次进入都会播放上浮+淡入**；若含 `scale`，`graphCanvas.getBoundingClientRect()`（`workbench.js:1503`）会变形 → `graphTideResize()`（`:1501`）取到的 tide 画布尺寸与真实画布不符 → 环境色 canvas 与画布错位 | 转场作用域排除图谱页：`#layout:not([data-page="graph"]) #middle-page > *`。若坚持全站生效，则**必须**只动 `transform: translateY` / `opacity`（不含 `scale`），并在 §6.3 的截图协议里冻结动画 |
| **F-7** | `body` / `html` 的背景与 `font-family` | `workbench.css:60-71` | `body` 背景 = `var(--dsw-bg-base)` = `var(--lk-paper)`（`:16`、`:5`）→ 图谱页所有未被覆盖的底色；`font-family`（`:63`）→ 全部继承文字。**注意 `:60` 的 `html, body { height:100% }` —— `html` 上今天没有 `font-family`，新增 `html{font-family:…}` 对渲染是惰性的（`body` 已覆盖），但一旦有人删掉 `body` 的 `font-family` 就会暴露** | 改 `body` 背景**只能通过改 `--lk-paper`/`--dsw-bg-base` 的值**——因此 §4 F-1/F-3/F-4 的「作用域钉回」是唯一合规路径。`html` 不得新增 `background`（除非同时给图谱页钉回 `#fffdf7`） |
| **F-8** | `--lk-paper` 系列（`--lk-paper` / `--lk-paper-shade`）改值 | `workbench.css:5-6` | `--lk-paper` → 页面底 + 右栏（`agent-ui.css` 8 处）；`--lk-paper-shade` → 左栏底（`:168`）+ `--dsw-bg-layer-2`（`:18`）+ `agent-ui.css:142` | 图谱页作用域钉回 `#fffdf7` / `#f3f1ea`；或**不动这两个变量**，把新基色放在新族名（`--surface-base`）上，让 `--lk-paper` 退化为别名但**图谱页作用域保留原值** |
| **F-9** | 全局 `transition` / `animation` 基线 | `workbench.css:1126-1131`（reduced-motion 全局降级） | 删掉或改窄这条全局 `!important` 规则 → 图谱的 `.node-face`（`:1680`）、`.label`（`:1714`）、`.meta`（`:1718`）、`.toast`（`:1810`）恢复过渡；`.graph-tide` 的 `opacity:.62` 降级（`:1864`）失效。**这条规则同时是 §6.3 冻结方案的地基**：没有它，`prefers-reduced-motion: reduce` 下的截图仍会带过渡中间帧 | 保留该规则原样。新的 `--motion-*` token 只用于**新增**动效，不改这条兜底 |
| **F-10** | 新增/改写 `outline` 清理 | `workbench.css:338 :427 :833`（`outline:none`）、**`workbench.css:1572`（`outline: 0`）** | 任务 2.4 的 grep 是 `outline: *none`，命中 3 处；若被放宽到 `outline:\s*(none\|0)`，会命中 `1572`（`.graph-topbar .search input`）→ 图谱搜索框突然出现全局焦点环 | 焦点环清理只针对 `338/427/833` 三处；`1572` 属图谱区段，**排除**。可用 `sed -n '1497,1884p'` 过滤后再 grep |
| **F-11** | 硬编码 hex 收编（任务 2.1）批量替换 | `workbench.css` 全文 | 任务 2.1 列出 4 蓝 / 9 红 / 10 黄橙 / 6 绿共 29 个 hex。图谱区段内（`1497-1884`）实测有 **83 处**硬编码 hex（`sed -n '1497,1884p' \| grep -cE '#[0-9a-fA-F]{3,6}'` → `83`），远超 29 → 若被收编成 token，**图谱边色/节点色/控件色全变** | 收编范围**排除 `workbench.css:1497-1884`**。用 `sed -n '1,1496p;1885,$p'` 过滤后再批量替换 |
| **F-12** | 左栏导航改造（任务 11.3–11.5）与顶栏三段式（任务 12.1） | `pages.py:85`（`_left_column`）/ `pages.py:71-84`（topbar） | **DOM 结构改造，无法用 CSS 作用域排除**。左栏加图标、顶栏重排 → 图谱页的左栏与顶栏像素**必然改变** → G-5「整页截图像素级一致」必然 FAIL | **图谱页必须走旧版外壳分支**（`graph_mode=True` 时不注入新导航/新顶栏），或——见 §6.6——**把 G-5 的比对范围收窄到图谱画布区域**并由所有者裁决 |
| **F-13** | `.muted` 新规则（任务 2.3） | `workbench.css`（新增） | 图谱页右栏 `<p id='ai-session-empty' class='muted'>还没有对话。</p>`（`pages.py:732`）与详情面板 `<p class='muted'>`（`pages.py:476`）当前**与正文同色**。新增 `.muted` 规则 → 右栏与详情面板文字变色 | 新 `.muted` 规则**排除图谱页**：`#layout:not([data-page="graph"]) .muted { … }`；或接受详情面板变化但右栏必须排除 |
| **F-14** | `--lk-ink` 改值 / 三栏描边改描边策略 | `workbench.css:7`、`:103`、`:167`、`:237` | 新基线「不用描边，靠圆角+柔影分层」（`decisions.md:610`）。若 `#topbar`/`#left-column`/`#ai-column` 的边框被改成柔影或圆角块 → 图谱页三栏分界形态改变 | 图谱页作用域钉回 `border: 1px solid var(--lk-ink)` / `border-bottom: 2px solid var(--lk-ink)`；新分层策略只施加于中栏内容 |
| **F-15** | 夜纸值集 `[data-theme="night"]` | 新增（任务 10.1） | 见 M-4：`html[data-theme="night"]` 特异性 `(0,1,1)` **高于** `:root`，且若它重定义 `--paper` / `--ink` / `--hair` / `--blue` / `--shadow`，**图谱画布与节点色在夜纸下全变**。任务 10.4 又要求「图谱页在两主题下均与基线一致」 | 夜纸块**不重定义这 12 个裸名**；图谱页用 `data-theme` 之外的机制排除夜纸（如 `html:not([data-theme="night"])` 的选择器不作用于图谱页，或图谱页不写 `data-theme`）。详见 §7。**（A-8 之后：夜纸下的图谱适配已移出本变更，归 `graph-node-visual-language`；但 M-4 这条机制事实对图谱 change 照样成立 —— `html[data-theme="night"]` 会压过 `:root`。）** |
| **F-16** | `#middle-page > .page-header { padding-right: 128px }` 删除（任务 11.2） | `workbench.css:255` | 该规则**对图谱页生效**（图谱页 `.page-header` 在 `#middle-page` 内，`pages.py:415-416`）→ 删掉后图谱页标题右边的 128px 空档消失，标题整体左移 | 保留该规则，或改成 `#layout:not([data-page="graph"]) #middle-page > .page-header` |
| **F-17** | 视口 / 滚动 / 布局重排引发的图谱尺寸漂移 | `workbench.css:160`（三栏几何）、`:253`（`max-width:800px`） | 图谱画布宽度 = 中栏宽度 → 三栏几何一变，画布与所有节点坐标基准都变 | 三栏几何**值不变**（`280px / minmax(0,1fr) / 420px`），只改写法；`.graph-content{max-width:none}`（`:509`）与 `.graph-workspace` 网格不变 |
| **F-18** | 静态资源缓存策略（`app.py:214-232`） | `app.py` `_send_static` | 该函数**不发 `Cache-Control`/`ETag`/`Last-Modified`**；若本次顺手加长缓存，改造后的 CSS 可能被旧缓存遮蔽 → 截图比的是旧样式，结论无效 | 本次**不加**长缓存；若必须加，`.css` 必须 `no-cache`；截图流程一律硬刷新 |
| **F-19** | 动效 token 收编（任务 4.1）误伤图谱时长 | `workbench.css:1680 :1714 :1718 :1810 :1771-1772` | 图谱有 5 处自己的时长（`.18s` / `.16s` / `.16s` / `.18s` / `1s`）。若批量把 `transition: … .18s` 改成 `var(--motion-fast)`，而 `--motion-fast` ≠ `180ms`，图谱交互手感与截图时序变 | 收编范围排除 `1497-1884`；或新 token 取值**恰好等于**原值（`--motion-fast:180ms` / `--motion-base:160ms`） |
| **F-20** | 图谱脚本加载路径与顺序 | `pages.py:100-102`、`middle-navigation.js:34-36` | 三脚本有严格顺序（core → renderer → physics）；`middle-navigation.js` 的 SPA 路径也会动态补载（`:31-43`） | 保持不变 |
| **F-21** | **在图谱专用区段内新增任何 `var(--lk-*)` / `var(--dsw-*)` 引用** | `workbench.css:1497-1884` | C-8 实测：当前该区段对全局 token 的引用是 **0 次**，这是 L1 自足的**唯一保证**。任何一条新引用（例如「顺手把 `--paper` 换成 `var(--lk-paper)`」或「让画布跟着 `--surface-base` 走」）都会**立刻把 L1 变成 L2**，把整个全局 token 层的风险敞口扩大到图谱画布本身 | **该区段一行不改**（§5.1 断言 1）。若将来确需新引用，必须先把该 token 在 `#layout[data-page="graph"]` 作用域钉回原值，并在本文件登记 |
| **F-22** | **改变图谱画布的可用像素尺寸或 auto-fit 的输入面** | `workbench.css:160 :175 :509 :1529-1537`；`workbench.js:1203-1227`（`graphFit`）、`:1406-1411`（首次 auto-fit） | **放大机制**：`graphFit()` 用 `graphCanvas.clientWidth/clientHeight`（`:1222-1223`）与节点 footprint 的包围盒算缩放，`:1221` 取 `Math.min(1.05, …)`。收敛后 `workbench.js:1406-1411` **恰好一次**调用 `graphFit()`。因此：中栏宽度 / `#middle` padding / `.graph-content` 宽度的任何变化，会被 auto-fit **放大成整幅图谱的缩放变化**——不是「画布右边多出几像素」，而是**所有节点同时变大或变小**，整幅图谱重排一次 | 三栏几何与 `#middle` padding **值不变**（可改写法）；`.graph-content{max-width:none}`（`:509`）与 `.graph-workspace` 网格不变。截图前必须等 auto-fit 发生（§6.4 的静止签名包含 `graphStage.style.transform`） |

### 4.9 移交清单 D：六项硬边界（带传导链的展开）

> 本节把上面 22 条里**最容易被「顺手改掉」的六项**单独展开。每项给出：
> **为什么危险**（可验证的传导链）+ **替代做法**（不改图谱的合规路径）+ **可执行验证**。
> 这六项合起来，覆盖了任务书里所有会碰到全局基线的改造点。
>
> **A-8 之后**：这六项是图谱 change 动手前必须先读完的传导链；
> **本变更不执行其中任何一项改造**（本变更对图谱只做「不误伤」的静态核对）。

---

#### B-1 全局圆角变量（`--dsw-radius-sm` / `-md` / `-lg`）

**当前值**：`workbench.css:43-45` → `6px` / `6px` / `22px`。

**为什么危险 —— 三条传导链：**

1. **图谱区段外**：`:544` `.graph-dashboard-metrics` 的 `border-radius: var(--dsw-radius-sm)`、
   `:576` `.graph-relation-row` 的 `border-radius: var(--dsw-radius-sm)`。
   这两处在**详情面板内**，只有选中一个节点后才可见（S-G2 状态）。
   「圆角统一 12px」（`decisions.md:609`）→ 指标格与关系行的圆角从 6px 变 12px
   → **详情面板截图必然 FAIL**。
2. **右栏**：右栏由 `agent-ui.css` 覆盖，装载在 `workbench.css` **之后**（`pages.py:1101-1102`）。
   `agent-ui.css:141` 用 `--dsw-radius-sm`、`:207 :241` 用 `--dsw-radius-md`
   → 图谱页右栏的输入类与卡片圆角变。
3. **图谱页右栏里的原生表单**：`:332`（`select`）与 `:421`（`input`）也用 `--dsw-radius-sm`
   → 图谱页若出现 `select`（详情面板 `:595` 有 `#graph-detail-panel select`），圆角变。

**替代做法**：改值可以（这正是任务 1.3 的目标），但**必须为图谱页作用域钉回原值**：

```css
/* 图谱页作用域：圆角基线钉回改造前的值（G-5 要求） */
#layout[data-page="graph"] {
  --dsw-radius-sm: 6px;
  --dsw-radius-md: 6px;
  --dsw-radius-lg: 22px;
}
```

> **作用域选择的理由**：`#layout[data-page="graph"]` 的特异性是 `(1,1,1)`，
> **高于**任何 `:root`（`(0,1,0)`）与 `html[data-theme=…]`（`(0,1,1)`，但同特异性时
> 后写者赢 → 只要图谱页作用域块写在文件更后即可胜出）。
> 用 `#layout[data-page="graph"]` 而不是 `html[data-page="graph"]`，是因为
> `data-page` 属性在 `#layout` 上（`pages.py:94-95`），不在 `<html>` 上。

**可执行验证**：

```bash
grep -n 'dsw-radius' workbench/server/static/workbench.css
# 图谱页作用域钉回块必须存在，且位于图谱区段之外（1497-1884 之前或 1884 之后）
```

浏览器侧：`getComputedStyle(document.getElementById('layout')).getPropertyValue('--dsw-radius-sm')` === `'6px'`（§5.2 R-7）。

---

#### B-2 全局字体栈（`body` / `html` 的 `font-family`）

**当前值**：`workbench.css:11-13` 的 `--dsw-font-family`；
`workbench.css:63` `body { font-family: var(--dsw-font-family); }`。
**`html` 上今天没有 `font-family`**（`:60` 只有 `html, body { height:100% }`）。

**为什么危险 —— 传导链：**

1. `body` 的 `font-family` 是**图谱页所有非 Georgia 文字**的唯一来源：
   顶栏标题（`:106-114` 继承）、`.seg button`（`:1581`）、`.icon-btn`（`:1589`）、
   `.chip`（`:1751`）、`.legend-item`（`:1786`）、`.hint`（`:1763`）、
   `.solver-line`（`:1767`）、`.distance-scale`（`:1759`）、`.control-note`（`:1737`）。
   **换栈 → 字形变 → 字宽变 → 这些控件的内部排版变 → 像素变。**
2. **表单控件也继承（按 C-5 更正）**：`:334`（`select`）、`:376`（`button`）、
   `:423`（`textarea, input[type="text"], input[type="number"], input:not([type])`）
   三处都写了 `font-family: inherit`。图谱搜索框 `pages.py:420` 的
   `<input id='graph-search'>` **没有 `type` 属性** → 命中 `input:not([type])`
   → **继承 `--dsw-font-family`**。
   `.seg button` / `.icon-btn` 都是 `<button>` → 也继承。
   → **改全局字体栈会改掉图谱页的搜索框与所有图谱按钮的字形。**
3. `html` 上新增 `font-family` 本身是**惰性的**（`body` 已覆盖），但它是给未来埋的雷：
   一旦有人「清理冗余」删掉 `body` 的 `font-family`，`html` 的新值立刻显形。

**替代做法**：

```css
#layout[data-page="graph"] {
  --dsw-font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
    "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue",
    Helvetica, Arial, sans-serif;
}
```

**不要**把 `html { font-family: … }` 加进新层 —— `html` 上的 `font-family` 会被
`body` 覆盖，看起来"无害"，但它是 F-4 的隐患来源；且 `html` 也是自定义属性的
**唯一宿主**（M-3/M-6），在它上面动任何东西都要重新评估 M-4/M-5。

**可执行验证**：

```bash
grep -n 'font-family' workbench/server/static/workbench.css | grep -vE ':(1688|1712|1742|1748|1823):'
# 期望：全局只有 :11-13（声明）与 :63（body 消费）；:334/:376/:423 是 inherit，不动
```

浏览器侧：`getComputedStyle(document.querySelector('.graph-topbar .search input')).fontFamily`
必须等于 `getComputedStyle(document.body).fontFamily`（证明继承链成立），
且等于改造前的记录值。

---

#### B-3 `--lk-paper` 系列

**当前值**：`workbench.css:5` `--lk-paper: #fffdf7`；`:6` `--lk-paper-shade: #f3f1ea`。
派生：`:16` `--dsw-bg-base: var(--lk-paper)`；`:18` `--dsw-bg-layer-2: var(--lk-paper-shade)`；
`:19` `--dsw-sidebar-fill: var(--lk-paper-shade)`。

**为什么危险 —— 传导链：**

| 落点 | 位置 | 图谱页上的可见性 |
|---|---|---|
| `body` 背景 | `:67` `background: var(--dsw-bg-base)` | **全页**（顶栏以外的所有底色） |
| `#left-column` 背景 | `:168` `background: var(--dsw-sidebar-fill)` | 图谱页左栏 |
| `code` / `pre` 底 | `:1035-1036` | 图谱页内代码块（右栏若有） |
| `.detail-block` 底 | `:490` | 图谱页详情面板 |
| 右栏 8 处 | `agent-ui.css:17 :39 :152 :165 :231 :368 :400 :424` | 图谱页右栏 |

**而且这是「视觉基线切换」的必然踩点**：新 token 层的亮色底色定为**浅奶油 `#fdf8ef`**
（`decisions.md:606`），与今天的 `#fffdf7` **不是同一个值**（RGB 253,248,239 vs 255,253,247）。
一旦 `--lk-paper` 被重定向到新基色，图谱页底色立刻变 → 整页像素 FAIL。
（**A-8 之后**：这个「新基色」是本变更 token 层的事实，而图谱换不换值归图谱 change；
本变更遵守的是「不误伤」——`tasks.md` 1.2 的口径：**图谱页中栏底色继续由既有
`--lk-paper` 链供给，不接到会随主题变的新族名上**。）

**替代做法**（二选一）：

- **方案 A（推荐）**：**不动** `--lk-paper` / `--lk-paper-shade` 这两个变量的全局取值；
  把新基色放在**新族名**上（`--surface-ground` / `--wb-surface-ground`），
  让 `--lk-paper` 退化为「旧外壳别名」，**仅供未改造区域使用**；
  图谱页作用域显式钉回 `#fffdf7` / `#f3f1ea`。
- **方案 B**：改 `--lk-paper` 的全局取值，但在 `#layout[data-page="graph"]` 作用域内
  显式重钉 `--lk-paper: #fffdf7; --lk-paper-shade: #f3f1ea;`。
  注意这条依赖 B-1/B-2 的作用域块**写在文件更后**（同特异性时后写者赢）。

> ⚠️ **注意与 §7 的关系**：原 `night-paper-tokens.md` §1.2 的钉回表把 `--surface-base`
> 钉成 `#fdf8ef`。那是**新层的浅色值**，不是今天的值——直接照抄会让图谱页底色变化。
> （该表已随 A-8 撤下，结论保留在 §7.2 的对照表里。）
> 详见 §7 的结论。

**可执行验证**：

```bash
sed -n '5,6p;16,19p' workbench/server/static/workbench.css
# 期望：--lk-paper: #fffdf7 / --lk-paper-shade: #f3f1ea
```

浏览器侧：`getComputedStyle(document.body).backgroundColor === 'rgb(255, 253, 247)'`
且 `getComputedStyle(document.getElementById('left-column')).backgroundColor === 'rgb(243, 241, 234)'`。

---

#### B-4 `#middle-page` 的转场动画

**当前值**：**无**。实测 `grep -n 'middle-page' workbench/server/static/workbench.css`
只有 3 处命中：`:255`（`padding-right: 128px`）、`:1198`（窄屏 padding）、
`:1525`（图谱页 flex 布局）。**今天 `#middle-page` 上没有任何 `animation` 或 `transition`。**

**为什么危险 —— 传导链：**

1. `#middle-page` 是**全站共用容器**（`pages.py:97`）。任务 17.1「换页 = 容器动画 + 骨架屏」
   （`decisions.md:669`）明确要求「必须是 `#middle-page` 容器动画，不能靠 JS 加一次性类名
   （innerHTML 会被替换）」。
   → **这条设计路线默认命中图谱页**：SPA 换页时 `middle-navigation.js:87`
   `middlePage.innerHTML = nextPage.innerHTML;` 替换子节点 → CSS 动画在**新子节点**上重新触发。
2. 图谱页的子节点是 `.page-header`（`:415-416`）与 `.graph-content`（`:417`）。
   若动画含 `transform: scale(...)`：
   - `graphCanvas.getBoundingClientRect()`（`workbench.js:1503`）会随缩放变形
   - `graphTideResize()`（`:1501-1513`）据此设置 tide 画布的 backing store
     （`:1507-1508` `graphTide.width = round(w*dpr)`）
   - → **环境色 canvas 与真实画布尺寸错位**，且错位量随动画相位变化 → **每帧不同**
3. 若动画含 `opacity`：`.graph-shell` 的背景（`:1599-1602`）在动画期间半透明
   → 透出 `body` 的底色 → 截图时序敏感。
4. 若骨架屏在 `#middle-page` 内：**图谱页会短暂显示灰色骨架块** —— 这不是"观感不变"，
   而且 S-G1 默认状态截图会抓到骨架。

**替代做法**（按优先级）：

1. **首选**：转场作用域排除图谱页
   ```css
   #layout:not([data-page="graph"]) #middle-page > * { animation: lk-rise … }
   ```
2. **次选**：保留全站生效，但**只动 `transform: translateY` 与 `opacity`**，
   **禁止 `scale`**；并把动画时长压到 `≤240ms`（`decisions.md:666`「场景 240–520ms」的上界），
   同时在 §6.3 的截图协议里用 `animations: 'disabled'` 定格到终态。
3. **兜底**：图谱页在 `middle-navigation.js:73-78` 的图谱分支里**跳过**转场类。

**可执行验证**：

```bash
grep -n 'middle-page' workbench/server/static/workbench.css
# 期望：新增的转场规则里必须带 :not([data-page="graph"]) 限定，或确认不含 scale
```

浏览器侧：`getComputedStyle(document.getElementById('middle-page')).animationName === 'none'`
（§5.2 R-6）；以及 `#middle-page` 的**后代**的 `animationName` 全为 `'none'`。

---

#### B-5 全局 `transition`

**当前值**：`workbench.css:1126-1131`

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    transition: none !important;
    animation: none !important;
  }
}
```

**为什么危险 —— 传导链：**

1. **它不是「装饰性兜底」，而是 G-5 的技术地基。**
   §6.3 的冻结方案靠 `prefers-reduced-motion: reduce` 把图谱的三类动画源全部按住
   （环境色 canvas、求解脉冲、CSS 过渡）。这条 `!important` 规则是其中 CSS 那一环。
   删掉它 → `.node-face`（`:1680` `transition: transform .18s, border-color .18s, box-shadow .18s`）、
   `.label`（`:1714` `transition: opacity .16s`）、`.meta`（`:1718`）、`.toast`（`:1810`）
   恢复过渡 → **截图时序敏感** → 两次截图可能拍到过渡中间帧 → 差异像素非 0。
2. **它与 A-2 的裁决直接耦合**：`decisions.md:707-711`（A-2 派生铁律）要求
   「动效的静态样式必须等于终态，起始态只能写在 `@keyframes` 内部」。
   若有人为了满足这条铁律而**改写** `:1126-1131`（例如把 `transition: none` 改成
   `transition-duration: 0.01ms` 以便保留 `!important` 的语义），**图谱页的过渡会回来**。
3. 图谱自己的 reduced-motion 区段（`:1861-1867`）只是**补充**（把 tide 透明度降到 `.62`、
   把图谱自己的过渡关掉），它**依赖**全局这条兜底兜住其余元素。

**替代做法**：**保留 `:1126-1131` 原样，一字不改**。
新动效按 A-2 铁律自检（静态样式 = 终态），新的 `--motion-*` / `--dur-*` token
只用于**新增**动效，不改这条兜底。

**可执行验证**：

```bash
sed -n '1126,1131p' workbench/server/static/workbench.css
# 期望：与上文逐字相同
```

浏览器侧：在 `prefers-reduced-motion: reduce` 下，
`getComputedStyle(document.querySelector('.node-face')).transitionDuration === '0s'`
且 `getComputedStyle(document.querySelector('.label')).transitionDuration === '0s'`。

---

#### B-6 `body` 背景

**当前值**：`workbench.css:61-67`

```css
body {
  margin: 0;
  font-family: var(--dsw-font-family);
  font-size: 14px;
  line-height: 22px;
  color: var(--dsw-label-primary);
  background: var(--dsw-bg-base);
  …
}
```

**为什么危险 —— 传导链：**

1. `body` 背景 = `var(--dsw-bg-base)` = `var(--lk-paper)`（`:16` → `:5`）= `#fffdf7`。
   它是**图谱页所有未被任何局部规则覆盖的底色** —— 包括：
   - `#middle` 内的留白（`:510 :1522-1523` 的 `#middle` **没有**自己的 background）
   - 顶栏与三栏之间的任何缝隙（当前 `#layout` 是 `grid-template-columns` 且 `gap` 为 0，
     但**窄屏抽屉态**（`:1186-1192`）会让 `#middle` 露出 `body` 底色）
   - 图谱页的滚动条溢出区
2. **它是 B-3 的下游**：改 `body` 背景**只可能**通过改 `--lk-paper` / `--dsw-bg-base`
   的取值实现（`body` 规则本身不需要动）。因此 **B-6 的合规路径 = B-3 的合规路径**
   —— 不存在「只改 body 背景不改 `--lk-paper`」这种独立选项。
3. **夜纸会绕过作用域钉回**：`html[data-theme="night"]` 特异性 `(0,1,1)` > `:root` `(0,1,0)`
   （M-4）。若夜纸块直接重定义 `--dsw-bg-base` 或 `--lk-paper`，
   **无论** `#layout[data-page="graph"]` 的钉回块写得多靠后，**它都赢不了**
   （因为 `#layout[data-page="graph"]` 是 `(1,1,1)` —— 等等，它赢得了；但如果夜纸块
   写成 `html[data-theme="night"]`，而图谱页的钉回写的是 `#layout[data-page="graph"]`，
   后者特异性 `(1,1,1)` > `(0,1,1)` → **图谱页钉回胜出**）。
   → **结论：图谱页的钉回必须挂在 `#layout[data-page="graph"]` 上，
   不能挂在 `:root` 上**（`:root` 与 `html[data-theme]` 同为 `(0,1,0)` vs `(0,1,1)`，会输）。

**替代做法**：

```css
/* 图谱页作用域：底色钉回改造前的值 */
#layout[data-page="graph"] {
  --lk-paper: #fffdf7;
  --lk-paper-shade: #f3f1ea;
  --dsw-bg-base: #fffdf7;   /* 若新层把它拆成独立变量 */
}
```

**可执行验证**：

```bash
sed -n '16p;67p' workbench/server/static/workbench.css
# 期望：--dsw-bg-base: var(--lk-paper) / background: var(--dsw-bg-base);
```

浏览器侧：`getComputedStyle(document.body).backgroundColor === 'rgb(255, 253, 247)'`。

---

### 4.10 移交清单汇总（22 条硬事实）

| 编号 | 禁止改动项 | 对应任务书风险点 |
|---|---|---|
| F-1 | 裸名 `--ink` | 任务 1.2 |
| F-2 | 裸名 `--paper` / `--shadow` / `--blue` / `--red` / `--yellow` / `--hair` / `--*Soft` / `--green` / `--graphite` | 任务 1.2 |
| F-3 | 全局圆角变量 | 任务 1.3 |
| F-4 | 全局字体栈 | 任务 3.2 |
| F-5 | 图谱自带 Georgia 栈被统一 | 任务 3.2 / 3.3 |
| F-6 | `#middle-page` 转场动画 | 任务 17.1 |
| F-7 | `body` / `html` 的背景与 `font-family` | 任务 1.x / 3.x |
| F-8 | `--lk-paper` 系列 | 任务 1.x |
| F-9 | 全局 `transition` / `animation` 基线 | 任务 4.1 |
| F-10 | `outline` 清理误伤 `:1572` | 任务 2.4 |
| F-11 | 硬编码 hex 收编误伤 `:1497-1884` | 任务 2.1 |
| F-12 | 左栏 / 顶栏 DOM 改造 | 任务 11.3–11.5、12.1 |
| F-13 | `.muted` 新规则 | 任务 2.3 |
| F-14 | `--lk-ink` / 三栏描边策略 | 任务 11.x |
| F-15 | 夜纸值集重定义图谱裸名 | 任务 10.1 / 10.4 |
| F-16 | 删除 `#middle-page > .page-header` 的 128px 预留 | 任务 11.2 |
| F-17 | 布局重排引发尺寸漂移 | 任务 11.1 |
| F-18 | 静态资源缓存策略 | 基础设施 |
| F-19 | 动效 token 收编误伤图谱时长 | 任务 4.1 |
| F-20 | 图谱脚本加载路径与顺序 | 基础设施 |
| F-21 | **图谱区段内新增全局 token 引用**（C-8 新增） | 任务 1.x / 2.x |
| F-22 | **画布像素尺寸 / auto-fit 输入面**（新增） | 任务 11.1 / 11.2 |
| **B-1** | 全局圆角变量（收尾专章） | = F-3 |
| **B-2** | 全局字体栈（收尾专章） | = F-4 + F-5 |
| **B-3** | `--lk-paper` 系列（收尾专章） | = F-8 + F-2 |
| **B-4** | `#middle-page` 转场动画（收尾专章） | = F-6 |
| **B-5** | 全局 `transition`（收尾专章） | = F-9 + F-19 |
| **B-6** | `body` 背景（收尾专章） | = F-7 + F-8 |

> **计数口径**：**22 条 F 项**（F-1…F-22，其中 F-21 / F-22 为本轮新增）
> + **6 条收尾硬边界**（B-1…B-6，与 F 项同源，是 F 项的展开而非新增条目）
> = **22 条独立禁止改动项**，其中 **6 项**被单独展开成专章。
>
> **A-8 之后**：这 22 条的**执行主体**是 `graph-node-visual-language`；
> 本变更只守 F-1 / F-2（零同名）这一条底线，用来证明「新 token 层没有误伤图谱」。

---

## 5. 移交清单 E：图谱 change 的自检清单（执行与验收归 `graph-node-visual-language`）

> **A-8 之后的读法**：这 15 条静态断言 + 12 条运行时断言 + 6 条视觉断言
> （外加 §5.5 的单命令自检脚本）原本是「本变更改完 token 后逐条跑」的验收闸门。
> A-8 之后本变更不碰图谱，它们变成**图谱 change 自己的自检清单** ——
> **执行与验收归 `graph-node-visual-language`**。
>
> **本变更实际只跑其中的最小子集**（用于证明「不误伤」）：
> §5.2 断言 11（区段零全局依赖 = 0）、断言 13 / 15（关键值未动）、
> §5.2 断言 12（14 个落点仍是同样这 8 个名字），
> 以及 `acceptance.md` **G-5** 的改造前后像素比对（差异 = 0）。

### 5.1 静态断言（不启动服务，秒级）

```bash
cd "D:/Projects/Academic Workflow/lesson-kit"
CSS=workbench/server/static/workbench.css

# 1) 图谱专用区段一行未改：任何 hunk 不得覆盖 1497-1884
git diff -U0 -- "$CSS" | grep -E '^@@' \
  | grep -E '\+149[7-9]|\+1[5-8][0-9][0-9]|\+188[0-4]' && echo "FAIL: 图谱区段被改" || echo "OK"

# 2) 图谱 12 个裸名各只声明一次，且全部落在 1506-1517
grep -nE '^\s*--(paper|ink|hair|blue|blueSoft|yellow|yellowSoft|red|redSoft|green|graphite|shadow)\s*:' "$CSS"
# 期望：恰好 12 行，行号 ∈ [1506,1517]

# 3) 文件里 :root 只有 2 处，且第 2 处在图谱区段内、其后无新 :root
grep -n ':root' "$CSS"
# 期望：1505 之后不再出现 :root（夜纸值集必须用 html[data-theme=...] 或作用域限定）

# 4) 夜纸块不得重定义图谱 12 个裸名
grep -nE 'data-theme[^{]*\{[^}]*--(paper|ink|hair|blue|blueSoft|yellow|yellowSoft|red|redSoft|green|graphite|shadow)\s*:' \
  "$CSS" && echo "FAIL" || echo "OK"

# 5) 图谱自带 Georgia 栈仍是原来 5 处、行号不变
grep -n 'Georgia' "$CSS"
# 期望：1688 / 1712 / 1742 / 1748 / 1823

# 6) 图谱 JS 一行未改
#    注意：git 对「无改动」的文件**不输出任何行**，不能直接看 numstat 的行数。
#    必须逐文件取「有改动则为增删和，无改动则为 0」。
jsd() { local v; v=$(git diff --numstat -- "$1" 2>/dev/null | awk '{print $1+$2}' | head -1); echo "${v:-0}"; }
for f in graph-physics-core.js graph-physics.js graph-physics-worker.js graph-renderer.js; do
  printf '%s -> %s\n' "$f" "$(jsd "workbench/server/static/$f")"
done
# 期望：四个都 -> 0

# 7) 图谱区段外的图谱规则（509-513 / 536-595 / 1167-1171）未被收编/改写
git diff -U0 -- "$CSS" | grep -E '^\+.*graph' && echo "REVIEW" || echo "OK"

# 8) 图谱区段外的硬编码 hex 收编没有误伤图谱
git diff -U0 -- "$CSS" \
  | grep -E '^\+' | grep -E '#(456fc9|aaa399|c3a128|c75a52|bbb4a9|d9d3c8|eeeae1|fffdf8|d8d2c6|e0dbd0|22201d|d3a914)' \
  && echo "FAIL: 图谱硬编码色被收编" || echo "OK"

# 9) outline 清理没有碰 1572
git diff -U0 -- "$CSS" | grep -E '^\-.*outline: *0' && echo "FAIL" || echo "OK"

# 10) 128px 死预留仍在（任务 11.2 删它会动图谱页标题）
grep -n 'padding-right: 128px' "$CSS"
# 期望：255 行仍在，或已加 :not([data-page="graph"]) 限定
```

### 5.2 追加静态断言（C-8 新增，锁死「零全局依赖」）

```bash
CSS=workbench/server/static/workbench.css

# 11) 【C-8】图谱专用区段内对全局 token 的引用必须仍为 0
awk 'NR>=1497 && NR<=1884' "$CSS" | grep -cE 'var\(--(lk|dsw)-'
# 期望：0

# 12) 图谱区段外那 25 行图谱规则里，全局 token 落点必须仍是同样这 8 个名字
for r in "509,513" "536,595" "1167,1171"; do
  sed -n "${r}p" "$CSS"
done | grep -oE 'var\(--(lk|dsw)-[a-z0-9-]+' | sort -u
# 期望（14 处 / 8 个名字）：
#   var(--dsw-bg-layer-1)      var(--dsw-border-l1)   var(--dsw-brand-accent)
#   var(--dsw-label-secondary) var(--dsw-label-tertiary)
#   var(--dsw-radius-sm)       var(--lk-blue)         var(--lk-red)
#   （--dsw-bg-layer-1 / --dsw-border-l1 / --dsw-label-secondary 各出现多次）

# 13) 六项硬边界的锚点行仍在原位
sed -n '43,45p;11,13p;5,6p;255p;161p;1126,1131p' "$CSS"
# 期望：圆角 43-45、字体 11-13、paper 5-6、128px 在 255、200ms 在 161、
#       reduced-motion 兜底整块在 1126-1131

# 14) #middle-page 仍然没有任何动画规则（除非已加图谱排除）
grep -nE 'middle-page[^{]*\{[^}]*(animation|transition)' "$CSS"
# 期望：要么无命中，要么命中行里含 :not([data-page="graph"])

# 15) 全局圆角/字体/底色的**值**未被改动（与本文件记录比对）
sed -n '5,6p;11,13p;16,19p;43,45p' "$CSS"
# 期望：#fffdf7 / #f3f1ea / 原字体栈 / #fffefa / #f3f1ea / 6px / 6px / 22px
```

### 5.3 运行时断言（浏览器控制台，图谱页上执行）

```js
// R-1 图谱 12 个 token 在 <html> 上的取值
const cs = getComputedStyle(document.documentElement);
const expect = {
  '--paper':'#fffdf7','--ink':'#191816','--hair':'#ddd8cd','--blue':'#2457c5',
  '--blueSoft':'#edf2ff','--yellow':'#f2c94c','--yellowSoft':'#fff7cf',
  '--red':'#d6453d','--redSoft':'#fff0ed','--green':'#4f9870','--graphite':'#2a2926'
};
for (const [k,v] of Object.entries(expect))
  console.assert(cs.getPropertyValue(k).trim() === v, k, cs.getPropertyValue(k), v);
console.assert(cs.getPropertyValue('--shadow').trim().startsWith('0 7px 18px'), '--shadow');

// R-2 画布底色
console.assert(getComputedStyle(document.querySelector('.graph-shell'))
  .backgroundColor === 'rgb(255, 253, 247)', 'graph-shell bg');

// R-3 图谱自带衬线栈仍在
console.assert(getComputedStyle(document.querySelector('.node-value'))
  .fontFamily.includes('Georgia'), 'node-value font');
console.assert(getComputedStyle(document.querySelector('.label'))
  .fontFamily.includes('Georgia'), 'label font');

// R-4 图谱搜索框的 outline: 0 未被改
console.assert(getComputedStyle(document.querySelector('.graph-topbar .search input'))
  .outlineStyle === 'none', 'graph search outline');

// R-5 图谱控件的硬编码圆角未被 token 化
console.assert(getComputedStyle(document.querySelector('.graph-topbar .icon-btn'))
  .borderTopLeftRadius === '4px', 'graph icon-btn radius');

// R-6 #middle-page 转场动画不得作用在图谱页
console.assert(getComputedStyle(document.getElementById('middle-page')).animationName === 'none',
  'middle-page animation on graph page');
[...document.getElementById('middle-page').children].forEach(el =>
  console.assert(getComputedStyle(el).animationName === 'none',
    'middle-page child animation: ' + el.className));

// R-7 外壳 token 在图谱页作用域被钉回
const g = getComputedStyle(document.getElementById('layout'));
console.assert(g.getPropertyValue('--lk-paper').trim() === '#fffdf7', 'pinned --lk-paper');
console.assert(g.getPropertyValue('--dsw-radius-sm').trim() === '6px', 'pinned --dsw-radius-sm');

// R-8 画布尺寸随中栏而变（确认几何未被改）
console.assert(document.querySelector('#graph-canvas').clientWidth > 0, 'canvas width');

// R-9【C-5 更正】图谱搜索框与图谱按钮确实继承全局字体栈
console.assert(getComputedStyle(document.querySelector('.graph-topbar .search input'))
  .fontFamily === getComputedStyle(document.body).fontFamily, 'search input inherits body font');
console.assert(getComputedStyle(document.querySelector('.graph-topbar .seg button'))
  .fontFamily === getComputedStyle(document.body).fontFamily, 'seg button inherits body font');

// R-10【B-6】body 与 #left-column 的底色未被改
console.assert(getComputedStyle(document.body).backgroundColor === 'rgb(255, 253, 247)', 'body bg');
console.assert(getComputedStyle(document.getElementById('left-column')).backgroundColor
  === 'rgb(243, 241, 234)', 'left column bg');

// R-11【B-5】reduced-motion 生效时图谱的 CSS 过渡被兜底关掉
console.assert(getComputedStyle(document.querySelector('.node-face')).transitionDuration === '0s',
  'node-face transition under reduced motion');
console.assert(getComputedStyle(document.querySelector('.label')).transitionDuration === '0s',
  'label transition under reduced motion');

// R-12【C-8】图谱区段零全局依赖在运行时也成立（抽样 5 个图谱自有元素）
['.graph-shell','.graph-topbar','.node-value','.legend','.floating'].forEach(sel => {
  const el = document.querySelector(sel);
  if (!el) return;
  const v = getComputedStyle(el).backgroundColor;
  console.assert(!/var\(/.test(v), sel + ' inline global var leak');
});
```

### 5.4 视觉断言（§6 的截图协议跑完后）

- [ ] **G-5-A**：图谱页**整页**截图，改造前 vs 改造后，`pixelmatch` 差异像素数 **= 0**（文字抗锯齿区可按 G-5 允许项标注掩膜）。
- [ ] **G-5-B**：图谱**画布区域**（`.graph-workspace` 的裁剪矩形）截图，差异像素数 **= 0**。
- [ ] **G-5-C**：图谱页在夜纸下与亮色下**同一份**图谱画布截图，差异像素数 **= 0**。⚠️ **A-8 之后这条只在「本变更不动图谱」的意义上成立**（本变更不碰图谱 ⇒ 夜纸与亮色下的图谱本来就没差别）；图谱 change 让图谱**跟随夜纸**之后，这条断言**退役**，届时由「夜纸下图谱可读且对比度达标」取代。
- [ ] **G-5-D**：三个状态（默认 / 选中节点 / 控制卡展开）各出一组，差异像素数均为 **= 0**。
- [ ] **G-5-E**（新增）：**左右列宽拖拽把手 hover 态**（`workbench.css:551`）截图，差异像素数 = 0。
- [ ] **G-5-F**（新增）：**详情面板展开态**（选中节点后出现的指标格 + 关系行，即区段外的 `:536-595`）差异像素数 = 0。

### 5.5 单命令自检脚本

把 §5.1 + §5.2 的 15 条断言合成一个可重复执行的脚本：

```bash
#!/usr/bin/env bash
# graph-isolation 静态自检（只读，不改任何文件）
set -u
cd "D:/Projects/Academic Workflow/lesson-kit" || exit 1
CSS=workbench/server/static/workbench.css
FAIL=0
chk() { # chk <描述> <期望> <实际>
  if [ "$2" = "$3" ]; then printf "  OK   %s\n" "$1"
  else printf "  FAIL %s  (期望 %s / 实际 %s)\n" "$1" "$2" "$3"; FAIL=1; fi
}

echo "== 图谱隔离静态自检 =="

# A1 区段零全局依赖
chk "图谱区段零全局依赖" "0" \
  "$(awk 'NR>=1497 && NR<=1884' "$CSS" | grep -cE 'var\(--(lk|dsw)-')"

# A2 图谱 12 个裸名各声明一次
chk "图谱 12 裸名声明数" "12" \
  "$(grep -cE '^\s*--(paper|ink|hair|blue|blueSoft|yellow|yellowSoft|red|redSoft|green|graphite|shadow)\s*:' "$CSS")"

# A3 裸名声明行号全在 1506-1517
chk "图谱裸名行号范围" "OK" \
  "$(grep -nE '^\s*--(paper|ink|hair|blue|blueSoft|yellow|yellowSoft|red|redSoft|green|graphite|shadow)\s*:' "$CSS" \
     | cut -d: -f1 | awk '$1<1506||$1>1517{print "BAD";exit}END{print "OK"}')"

# A4 :root 只有 2 处
chk ":root 出现次数" "2" "$(grep -c ':root' "$CSS")"

# A5 Georgia 仍是 5 处且行号不变
chk "Georgia 行号" "1688 1712 1742 1748 1823" \
  "$(grep -n 'Georgia' "$CSS" | cut -d: -f1 | tr '\n' ' ' | sed 's/ $//')"

# A6 关键值未被改
chk "--lk-paper" "#fffdf7" "$(sed -n '5p' "$CSS" | sed 's/.*: *//;s/;.*//')"
chk "--lk-paper-shade" "#f3f1ea" "$(sed -n '6p' "$CSS" | sed 's/.*: *//;s/;.*//')"
chk "--dsw-radius-sm" "6px" "$(sed -n '43p' "$CSS" | sed 's/.*: *//;s/;.*//')"
chk "--dsw-radius-md" "6px" "$(sed -n '44p' "$CSS" | sed 's/.*: *//;s/;.*//')"
chk "--dsw-radius-lg" "22px" "$(sed -n '45p' "$CSS" | sed 's/.*: *//;s/;.*//')"

# A7 128px 预留仍在
chk "128px 预留" "1" "$(grep -c 'padding-right: 128px' "$CSS")"

# A8 reduced-motion 兜底整块仍在
chk "reduced-motion 兜底" "OK" \
  "$(sed -n '1126,1131p' "$CSS" | grep -q 'transition: none !important' && \
     sed -n '1126,1131p' "$CSS" | grep -q 'animation: none !important' && echo OK || echo BAD)"

# A9 #middle-page 无动画
chk "#middle-page 动画" "0" \
  "$(grep -cE 'middle-page[^{]*\{[^}]*(animation|transition)' "$CSS")"

# A10 图谱 JS 未改
#     git 对「无改动」文件不输出任何行 → 逐文件取「有改动则为增删和，无改动则为 0」
jsd() { local v; v=$(git diff --numstat -- "$1" 2>/dev/null | awk '{print $1+$2}' | head -1); echo "${v:-0}"; }
chk "图谱 JS numstat" "0 0 0 0" "$(jsd workbench/server/static/graph-physics-core.js) $(jsd workbench/server/static/graph-physics.js) $(jsd workbench/server/static/graph-physics-worker.js) $(jsd workbench/server/static/graph-renderer.js)"

echo "== 结果 =="
[ "$FAIL" = "0" ] && echo "全部通过" || echo "存在 FAIL"
exit $FAIL
```

> 用法：改造分支上跑一次，再在基线分支上跑一次，**两次输出必须逐行相同**。
> 只要有一项不同，说明改造动了图谱的锚点。

---

## 6. 移交清单 F：像素级比对方案（供图谱 change 执行）

> **A-8 之后的读法**：本节原本是「本变更改完 token 后如何证明图谱没变」的方案。
> A-8 之后本变更不碰图谱，**本变更只借用它的一条否定式断言**
> （改造前后图谱页截图差异 = 0，见 `acceptance.md` G-5）；
> 而**完整的比对协议（含 R-1 / R-2 / R-3 三种口径的裁决、S-G1…S-G7 状态矩阵、
> 三类动画源的冻结手段）归 `graph-node-visual-language` 执行与验收**。

### 6.1 目标与难点

`acceptance.md` §0 **G-5**：「改造前后同一图谱页截图并排比 → 差异像素数 = 0」。
（**A-8 之后**：G-5 在本变更里是**否定式**断言 —— 本变更不碰图谱，
所以「无差异」是必然结果，用来证明新 token 层没有误伤图谱。）

图谱页有**三处**天然不可比源，必须逐一冻结，否则「像素不一致」无法归因：

| # | 不可比源 | 证据 | 冻结手段 |
|---|---|---|---|
| N-1 | **环境色 canvas 是时间驱动的无限动画** | `workbench.js:1634` `graphTideDraw(graphTideState.reduced ? 0 : now/1000)`；`:1635` 非 reduced 无限 `requestAnimationFrame` | **开 `prefers-reduced-motion: reduce`** → `:1639` `reduced=true` → `:1634` 固定 `t=0`、`:1635` 不再排帧、`:1659` 只画一次 → 一次性确定性绘制 |
| N-2 | **物理布局由 Worker 迭代收敛** | `graph-physics-worker.js:88` 单条消息最多 `8` 步；`graph-physics-core.js:1246` alpha 衰减、`:1255` 连续 15 帧稳定 → `:1260` `settled = true` | 等到 `#graph-solver-state` **不再带 `.solving` 类**（`workbench.js:719`）**且** DOM 静止签名连续 N 次不变（§6.4） |
| N-3 | **布局被 `localStorage` 缓存，二次访问走另一条渲染路径** | `graph-physics.js:69-86` `writeLayoutSeed()`；`:344-369` 二次访问「采纳缓存、不再重解」 | **两次截图都用全新浏览器上下文**（清 `lk_graph_layout_v1_<workspace>`），强制两次都走「从零求解」同一条路径 |

> N-3 容易被忽略：`graph-physics.js:358` 判定「所有节点都有座位」时走**采纳缓存**分支，
> 该分支不跑求解器，最终坐标与「从零求解」的收敛点**可能相差 0.1px**（`:75` 存储时四舍五入到 0.1）。
> 混用两条路径 → 节点位置差 0.1px → 整图非零差异，但与 CSS 无关。

### 6.2 环境固定

| 项 | 取值 | 理由 |
|---|---|---|
| 浏览器 | 同一台机器、同一浏览器**同一版本**、同一份 profile 策略 | G-5 允许「除浏览器字体渲染差异」；跨机器字体渲染必然不同 |
| **视口** | **1440 × 900**（与 `acceptance.md` §1 的 1440 档一致） | 1440 是 `acceptance.md` 全部 S-1…S-12 条目的统一宽度；图谱页在 1440 下三栏 `280 / 1fr / 420` 全部展开，无抽屉 |
| **`deviceScaleFactor`** | **= 1** | `graph-renderer.js:189` dpr 夹在 1..2；`workbench.js:1506` tide dpr `min(2, dpr)` → dpr 必须两次一致，否则 WebGL backing store（`:191-193`）与 tide canvas（`:1507-1508`）分辨率不同 → 边缘渲染不同 |
| 浏览器缩放 | 100%，不叠加操作系统缩放 | 同上；Windows 显示缩放会影响 `devicePixelRatio` |
| WebGL | headless Chromium 用固定 flag：`--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`（或两次都用同一块真 GPU） | `graph-renderer.js:169-175` 强制 WebGL2，无 WebGL2 直接抛错（`:175`）；软件光栅化是确定性的，但与真 GPU 结果不同 → **两次必须同一种** |
| **动效** | `prefers-reduced-motion: reduce`（Playwright `reducedMotion: 'reduce'`） | N-1；**同时是 N-2 确定性的前提**（见 §6.3 A-2）与 WebGL 同步绘制的前提（§6.3 A-3） |
| 字体 | 不装新字体；截图前等 `document.fonts.ready` | 新阅读面字体（任务 3.1）若被图谱继承，fallback 与 swap 会产生两种渲染 → 必须等 `document.fonts.ready` |
| 数据 | **池数据库副本** + 隔离注册表 + 独立端口；两次用**同一份**副本快照 | `acceptance.md` §5 |
| 工作区 | 同一工作区名（影响 `localStorage` key `lk_graph_layout_v1_<workspace>` 与 `identity`） | `graph-physics.js:43-48` |
| 缓存 | 每次导航前 `context.clearCookies()` + 关缓存；或 URL 加 `?v=<timestamp>` 查询串 | `app.py:214-232` 不发 `Cache-Control`/`ETag` → 浏览器启发式缓存可能遮蔽新 CSS（F-18） |
| 滚动位置 | **强制 `window.scrollTo(0, 0)`**，且截图前断言 `window.scrollX === 0 && window.scrollY === 0` | `#middle` 在图谱页 `overflow: hidden`（`:510 :1523`），中栏不滚动；但文档本身仍可能滚动 |

### 6.3 如何冻结图谱动画（三类源，逐个冻结）

> 图谱页的动画**不只一处**。只关掉 CSS 动画是不够的 —— 环境色 canvas 是 canvas 2D 绘制，
> WebGL 边是 rAF 调度，物理布局是 Worker 异步迭代。**三者都要各自冻结。**

#### A-1 环境色 canvas（`#graph-tide`）

| 项 | 内容 |
|---|---|
| 机制 | `workbench.js:1628-1636` `graphTideFrame(now)` → `:1634` `graphTideDraw(reduced ? 0 : now/1000)` → `:1635` 非 reduced 无限排 rAF |
| 不冻结的后果 | 每次截图的环境色相位不同 → 画布底纹整片不同 → **AE 差异可达数万像素** |
| **冻结手段** | `prefers-reduced-motion: reduce` → `:1639` `reduced = true` → `:1659` `graphTideFrame(0)` **只画一次**，`t` 恒为 0 → 每次加载的底纹完全一致 |
| 配套 | 全局兜底 `workbench.css:1126-1131`（B-5）保证没有 CSS 动画残留；图谱自己的降级区段 `:1861-1867` 把 tide 透明度定在 `.62` |
| 断言 | 截图后检查 `getComputedStyle(document.getElementById('graph-tide')).opacity === '0.62'`（reduced 下） |

#### A-2 物理布局（Worker 迭代 + 帧内缓动）—— **最难冻结的一处**

| 项 | 内容 |
|---|---|
| 机制 | Worker 每条消息最多 8 步（`graph-physics-worker.js:88`）；主循环 `workbench.js:1388-1395` 每帧 `sim.tick()`；alpha 衰减到收敛（`graph-physics-core.js:1246-1260`） |
| **关键发现 1** | **收敛后有一次「自动适配」**：`workbench.js:1406-1411` 在 `sim.graph.settled && autoFitAfterSettle && !graphView.userMoved` 时调 `graphFit()`（`:1203-1227`）**恰好一次**。`graphFit` 用 `graphCanvas.clientWidth/clientHeight`（`:1222-1223`）算缩放 → **画布尺寸变了，整幅图谱的缩放就变了**（F-22）。→ 截图前**必须等 auto-fit 发生** |
| **关键发现 2** | **节点尺寸与透明度是逐帧缓动的**：`workbench.js:1302-1305` `node.size += (targetSize - size) * .14`、`node.opacity += … * .18`。缓动是**渐近**的，永远不精确到目标值 → **最终像素取决于「缓动了多少帧」** |
| **关键发现 3** | `workbench.js:1444` `paintNow = !overBudget && !(graphTideState.reduced && solving)` → **reduced 模式下，求解期间完全不绘制**；只有收敛后的那一帧才画一次 → **缓动次数恒为 1** → 结果确定 |
| **反例** | 若**不**开 reduced motion：`overBudget`（`:1443`，帧耗时 > 20ms）会让某些帧跳过绘制 → **缓动次数随机器负载变化** → 同一份代码在不同机器上截出不同像素 → **G-5 在非 reduced 模式下根本不可复现** |
| **结论** | **`prefers-reduced-motion: reduce` 不是"方便"，是 G-5 可复现的必要条件。** |
| 冻结手段 | ① reduced motion；② 等 `#graph-solver-state` 不带 `.solving`（`workbench.js:719`）；③ 等 DOM 静止签名连续 N 次不变（§6.4） |
| 附带约束 | 两次截图必须**同一浏览器上下文策略**（同一 `localStorage` 空态）→ 否则走 N-3 的缓存分支 |

#### A-3 WebGL2 边渲染

| 项 | 内容 |
|---|---|
| 机制 | `graph-renderer.js:307-314` `render()`：`:309` `if (reducedMotion) { draw(); }` **同步绘制**；`:311-313` 否则 `requestAnimationFrame(draw)` **延后一帧** |
| 不冻结的后果 | 非 reduced 模式下，截图可能落在「DOM 已更新、WebGL 还没画」的帧 → **边整片缺失或滞后** |
| 冻结手段 | reduced motion → `draw()` 同步执行 → 每次 `render()` 调用都立刻反映到画布 |
| 附带 | WebGL 的实际着色由 `graph-renderer.js:345-346` 的内联 GLSL 决定（`u_size` 归一化），**不读 CSS 变量** → 边色来自 JS 传入的 `runtime.edgeStyle()`，不是 token → 改 token 不改边色 |
| 断言 | `document.querySelector('#graph-canvas').classList.contains('graph-renderer-active')` 必须为 `true`（WebGL 已接管，`:352`）；若为 `false`，说明回退到 SVG，截图不可比 |

#### A-4 CSS 过渡与关键帧（图谱自身 + 全局兜底）

| 图谱自己的动效 | 位置 | reduced 下 |
|---|---|---|
| `.node-face` 过渡 | `:1680` `transform/border-color/box-shadow .18s` | 全局 `:1126-1131` 兜底关掉 |
| `.label` 过渡 | `:1714` `opacity .16s` | 同上 |
| `.meta` 过渡 | `:1718` `opacity .16s` | 同上 |
| `.toast` 过渡 | `:1810` | 同上 |
| `graph-pulse` 关键帧 | `:1771-1772` `1s ease-in-out infinite` | 图谱降级区段 `:1866` `animation: none` |

**冻结手段**：reduced motion（浏览器级）+ Playwright `animations: 'disabled'`（把 CSS 动画/过渡定格到**终态**）。
两者叠加，覆盖 F-6（`#middle-page` 转场）与 F-9（全局 transition）。

#### A-5 布局过渡

`workbench.css:161` `#layout { transition: grid-template-columns 200ms ease; }`
→ 截图前必须等列宽过渡结束（三栏宽度稳定）。
判据：`getComputedStyle(document.getElementById('layout')).gridTemplateColumns`
连续两次采样相同（§6.4 的静止签名里不含它，但可单独断言）。

#### A-6 视图变换（缩放 / 平移）

`workbench.js:703` `graphView = { scale: .7, panX: 52, panY: -18, userMoved: false }`
→ **必须用默认视图**：不滚轮、不拖拽、不点节点、不用搜索框。
停在 `pages.py:415-429` 的默认状态：
视图 = structure（`pages.py:424` 的 `class=active`）、筛选 = 全部（`pages.py:441`）、
重力 = 85（`pages.py:446` 的 `value=85`）、看板收起（`pages.py:430`）、控制卡收起（`pages.py:432`）。
`graphView.userMoved` 必须保持 `false` —— 否则 auto-fit 被跳过（`:1406`），视图停在 `.7` 而非适配值。

### 6.4 等待谓词（**按 C-7 更正后的正确写法**）

> **原谓词无效**：`#graph-solver-text` 的 `textContent === '已收敛'` 在**页面刚载入时即成立**
> （`pages.py:454` 服务端渲染的初始文本就是 `已收敛`）。用它等待会**立刻返回**，
> 从而在物理布局还在求解时就截图 → 必然 FAIL 且无法归因。

**正确谓词 = 两个条件同时成立：**

1. **求解态指示器复位**：`#graph-solver-state` 不带 `.solving` 类。
   （`workbench.js:719` `classList.toggle("solving", !!solving)`；`:1412-1413` 在
   `wasSolving !== (sim.graph.alpha > 0)` 的跳变点调用 `graphSolver()`。）
2. **DOM 静止签名连续 N 次不变**：把图谱的**渲染结果**序列化成一个字符串，
   要求它在 ≥ 3 次采样（间隔 ≥ 100ms）内逐字相同。

**静止签名覆盖**：所有节点的 `data-kp-id` / `left` / `top` / `--size` / `opacity` /
`.label` 的 `opacity` / `.meta` 的 `opacity`，以及 `#graph-stage` 的 `style.transform`
（**包含 auto-fit 后的最终缩放与平移**）。

```js
// 在页面控制台粘贴执行；返回 Promise<静止签名>
function graphQuiescentSignature() {
  const stage = document.getElementById('graph-stage');
  const parts = [];
  stage.querySelectorAll('.node-wrap').forEach(w => {
    const label = w.querySelector('.label');
    const meta  = w.querySelector('.meta');
    parts.push([
      w.dataset.kpId,
      w.style.left, w.style.top,
      w.style.getPropertyValue('--size'),
      w.style.opacity,
      label ? label.style.opacity : '',
      meta  ? meta.style.opacity  : '',
    ].join('|'));
  });
  parts.push('stage:' + stage.style.transform);
  return parts.join(';');
}

// 轮询直到静止
async function waitForGraphQuiescence({ samples = 3, intervalMs = 120, timeoutMs = 30000 } = {}) {
  const deadline = Date.now() + timeoutMs;
  let last = null, stable = 0;
  while (Date.now() < deadline) {
    const st = document.querySelector('#graph-solver-state');
    const sig = graphQuiescentSignature();
    if (st && !st.classList.contains('solving') && sig === last) {
      stable += 1;
      if (stable >= samples) return sig;
    } else {
      stable = 0;
    }
    last = sig;
    await new Promise(r => setTimeout(r, intervalMs));
  }
  throw new Error('graph did not quiesce within ' + timeoutMs + 'ms');
}
```

**为什么签名必须包含 `#graph-stage` 的 `transform`**：
`graphFit()` 在收敛后把 `graphStage.style.transform` 写成
`translate(panX, panY) scale(scale)`（`workbench.js:1106`）。
它是在**收敛之后**才发生的，若签名不含它，截图可能拍在 auto-fit 之前
→ 视图缩放是 `.7` 而不是适配值 → 整幅图谱缩放不同。

**为什么签名必须包含 `--size` 与 `opacity`**：
`workbench.js:1302-1308` 用缓动写 `style.setProperty("--size", …)` 与 `style.opacity`。
缓动次数不同 → 数值不同 → 节点直径与透明度不同。

**为什么签名必须包含 `.label` / `.meta` 的 opacity**：
`workbench.js:1324-1325` 按 `graphView.scale >= labelScaleThreshold(node)` 决定标签显隐
→ 缩放变了，标签显隐集合就变 → 画布上的文字像素变。

### 6.5 截图时刻的固定流程（每次截图都必须走完这 9 步）

```
1. 全新 browser context（localStorage / cookie 皆空 → N-3 走「从零求解」分支）
2. goto /w/<workspace>/graph
3. context.emulateMedia({ reducedMotion: 'reduce' })   ← 必须在 goto 之前设
4. await page.evaluate(() => document.fonts.ready)
5. await page.evaluate(() => window.scrollTo(0, 0))
6. await waitForGraphQuiescence()                        ← §6.4；已包含 auto-fit 等待
7. 断言静止：window.scrollX===0 && window.scrollY===0
            && #graph-solver-state 不带 .solving
            && #graph-canvas 带 .graph-renderer-active
            && getComputedStyle(#graph-tide).opacity === '0.62'
8. await page.screenshot({ animations: 'disabled', caret: 'hide', scale: 'css' })
9. 记录签名（静止签名 + viewport + dpr + 浏览器版本 + 数据快照哈希），供复现
```

**补充与坑：**

- `animations: 'disabled'` 会把 CSS 动画与过渡**定格在终态**，正好覆盖 A-4 与 F-6。
- `caret: 'hide'` 隐藏的是**文本插入光标**（聚焦输入框里的闪烁竖线），
  **不是鼠标指针**。
  → **鼠标指针处理**：Playwright 的 `page.screenshot()` 是**合成截图**，
  **不包含**操作系统鼠标指针 → 天然没有指针问题。
  但若改用**操作系统级截屏**（Windows 桌面截图 / 录屏 / 人工截屏），
  **必须先把指针移出视口**（如移到屏幕另一块显示器或 `(0,0)` 角落），
  否则指针会被烧进像素，且两次的位置几乎不可能一致 → 必然 FAIL。
  → **本方案统一用 Playwright `page.screenshot()`**，避免指针问题。
- **不要**在截图前 hover 任何元素：`graph-renderer.js:223-240` 的 `applyLod()` 会按
  视口裁剪节点；`workbench.js:1016-1018` 的 `mouseenter` 会设置 `sim.graph.hover`
  → 节点标签显隐集合改变（`:1321`）→ 像素变。
  → **鼠标必须停在视口之外**（Playwright 默认无鼠标位置，等价于不 hover）。
- `#middle` 在图谱页是 `overflow: hidden`（`workbench.css:510`、`:1523`），中栏不滚动；
  **但文档本身仍可能滚动** → 第 5 步不可省。
- 截图**必须是视口截图**（`fullPage: false`）：`fullPage: true` 会改变视口高度
  → 三栏 `1fr` 中栏高度变 → 画布高度变 → auto-fit 缩放变。
- 两次截图**必须用同一份数据快照**：图谱内容来自
  `GET /api/w/{name}/graph/model`（`app.py:85`），节点数与关系数变 → 布局变。

### 6.6 比对

```bash
# 改造前 / 改造后 同名同尺寸
npx pixelmatch before.png after.png diff.png          # 或用 ImageMagick
magick compare -metric AE before.png after.png null:   # 绝对错误像素数
magick compare -metric RMSE before.png after.png null: # 均方根误差

# 画布区域裁剪比对（R-2 口径）
magick compare -metric AE -crop <W>x<H>+<X>+<Y> before.png after.png null:
```

判定：

| 指标 | 通过标准 |
|---|---|
| AE（差异像素数） | **0**（整页，G-5-A）；若仅文字抗锯齿处有差，按 G-5「浏览器字体渲染差异」允许项标注掩膜后仍应为 0 |
| 画布区域 AE（G-5-B） | **0**，且**不接受任何掩膜**——画布内无浏览器字体渲染差异的辩解空间（节点数字用 Georgia，但同机同版浏览器下渲染确定） |
| 尺寸 | 两图 width/height 完全相同 |
| 静止签名 | 两次的 §6.4 静止签名字符串**逐字相同**（这是最强的辅助证据：签名不同 → 像素必然不同，且能立刻指出差异源） |

> **静止签名是本方案的关键增量**：它把「像素不一致」从"需要人眼找差异"
> 变成"签名不一致 → 直接定位到哪一项变了"。
> 例如：签名里只有 `stage:translate(...)` 不同 → 是画布尺寸/auto-fit 变了；
> 只有 `--size` 不同 → 是缓动帧数不同（多半没开 reduced motion）；
> 只有 `.label` 的 opacity 不同 → 是缩放变了（多半是三栏几何变了）。

### 6.7 比对范围的三种口径（**需所有者裁决**）

`acceptance.md` §0 **G-5** 写的是「图谱页截图并排比」，未指定裁剪范围。三种口径的结论会不同：

| 口径 | 比对区域 | 能否达成 | 说明 |
|---|---|---|---|
| **R-1 整页** | 1440×900 整屏 | **当前无法达成** | 任务 11.3–11.5（左栏导航加图标、选中态改圆角色块）与 12.1（顶栏三段式）**改的是 DOM 结构**，无法用 CSS 作用域排除 → 图谱页左栏与顶栏必然变（F-12） |
| **R-2 画布区域** | `.graph-workspace` 的裁剪矩形 | **可以达成** | 图谱自身 + 中栏容器。这是 F-1…F-11、F-13…F-22 全部守住后的必然结果 |
| **R-3 画布 + 顶栏/左栏/右栏背景色采样** | 画布矩形 + 三栏各取 1 个纯色像素 | **可以达成** | 在 R-2 之上额外证明外壳底色/描边未变（F-3/F-7/F-8/F-14） |

> **建议（供裁决）**：G-5 判为 **R-2 + R-3**；R-1 整页比对改为「**除左栏与顶栏外**像素级一致」，
> 并把「左栏/顶栏在图谱页上是否跟随全站改造」作为**独立议题**登记到契约文件——
> **A-8 之后**：三份工件对「图谱是否在范围内」的表述**已经一致** ——
> `proposal.md`「Explicitly out of scope」= 完全不在范围内；
> `tasks.md` 1.2 = 只做「不误伤」；`acceptance.md` G-5 = 否定式断言。
> 但**比对范围**（整页 / 画布区域 / 采样）这一层**仍未定**，
> 且它现在**只影响图谱 change**（本变更只需要「差异 = 0」这一条否定式断言，
> 不需要 R-1 / R-2 / R-3 的裁决）。
> 按 `AGENTS.md`「契约冲突处理」，此处**保持冲突显式**并提请裁决，不在本文件内自行选边。

### 6.8 状态矩阵（每个状态各一组前后对照）

| 状态 | 触发 | 覆盖到的 CSS | 特别注意 |
|---|---|---|---|
| **S-G1 默认** | 直接进入 `/w/<ws>/graph`，不交互 | `:1520-1884` 全部；`pages.py:430` 看板收起、`:432` 控制卡收起 | 基准状态；必须包含在每一次比对里 |
| **S-G2 选中节点** | 点击一个节点（`pages.py:470` 的 `.node` 按钮） | 详情面板 `:1815-1859` + **区段外** `:536-595` + 节点选中态 `:1702-1708` | **这是唯一暴露区段外 14 个全局 token 落点的状态** → 必须做（否则 §3.2 的落点全部没被验证） |
| **S-G3 控制卡展开** | 点击 `#graph-controls-toggle` | `:1721-1776`（chip / 滑杆 / 求解行 / 距离刻度） | 展开后卡片宽度 230px（`:1728`），露出下方画布 → 画布区域也被覆盖 |
| **S-G4 图例切换** | 点击某个 `.legend-item` | `:1778-1799` + `workbench.js` 的边可见性逻辑 | 边消失 → WebGL 顶点缓冲变化 → WebGL 路径也必须被验证 |
| **S-G5 夜纸** | 主题切到夜纸（若图谱页参与主题） | `html[data-theme="night"]` 对图谱的影响（F-15） | 与 Q-2 绑定，见 §7 |
| **S-G6 右栏有会话**（新增） | 右栏 Agent 有会话记录 | `agent-ui.css` 全部 | 覆盖 Q-5 的第二种右栏状态 |
| **S-G7 拖拽把手 hover**（新增） | 鼠标悬停 `#left-resizer` | `workbench.css:551` `--dsw-brand-accent` | 覆盖 §3.5.2 最后一行的落点 |

> S-G5 若采用 R-2 口径，夜纸是否作用于图谱页**已由 A-8 关闭**（夜纸下**图谱跟随夜纸**，
> 但**在 `graph-node-visual-language` 里做**）—— 本变更不碰图谱，
> 所以本变更的走查里 S-G5 只作为「本变更没有误伤图谱」的负向证据存在。
>
> **S-G2 是最容易被漏掉、也最关键的一个**：它把「区段外那 25 行图谱规则」和
> 「详情面板的全局 token 落点」全部拉进比对范围。若只做 S-G1，
> §3.2 表里的 `--dsw-radius-sm` / `--dsw-bg-layer-1` / `--dsw-border-l1` /
> `--dsw-label-secondary` / `--dsw-label-tertiary` / `--lk-blue` / `--lk-red`
> **一个都没被验证**。

---

## 7. 与 `night-paper-tokens.md` §1.2 的一致性核对

> **本节的目的**：确保本文件与 `design-notes/night-paper-tokens.md` §1.2
> 「知识图谱页：**不在本变更范围内**」**不互相矛盾**。
>
> **A-8 之后的读法**：两份文件现在讲的是同一件事的两面 ——
> `night-paper-tokens.md` §1.2 声明**范围**（本变更不碰图谱），
> 本文件提供**事实与后果**（图谱由什么构成、被牵连会怎样、接手时要守什么）。
> §7.2 / §7.3 的两处出入**仍然存在**，但它们的**裁决主体已变成图谱 change**。
> 按任务要求：**若有出入，以「图谱页观感必须与现在完全一致」为准，并在此注明。**

### 7.1 逐条核对

| # | `night-paper-tokens.md` §1.2 的结论 | 本文件的结论 | 是否一致 |
|---|---|---|---|
| 1 | 图谱自有的裸名 token 在 `workbench.css:1505-1518`（12 个） | 同（§3.1） | ✅ 一致 |
| 2 | **新 token 层与图谱零同名**（`--surface-* / --ink-* / --role-*` 命名）—— 仍是本变更对图谱的**唯一硬约束** | 同（F-1、F-2、M-4、M-5） | ✅ 一致 |
| 3 | 因此图谱画布本身在两主题下**逐像素不变** | 同（§3.4 C-8：图谱区段对全局 token 引用 = 0） | ✅ 一致（且本文件给出了更强的实测依据） |
| 4 | 图谱页跑在同一个外壳里（`pages.py:410-481` → `shell(..., graph_mode=True)` → `pages.py:68-110`） | 同（§2.1） | ✅ 一致 |
| 5 | **本变更不触碰图谱**（A-8）；夜纸下的图谱适配与节点重设计归 `graph-node-visual-language` | §4 / §5 / §6 全部降级为**移交清单**：内容保留，执行与验收归图谱 change | ✅ 一致（A-8 之后本文件不再是「隔离工程」） |
| 6 | 原「图谱路由下把下面这组 token 钉回浅色值」的清单 —— **已随 A-8 撤下**（§1.2 现在只作范围声明，不再给施工图） | §7.2 仍**原样保留**那张表，并主张钉回**图谱今天的值** | ⚠️ **出入仍在（Q-7），裁决主体 = 图谱 change** |
| 7 | 「夜纸下保持浅色 vs 跟随夜纸」二选一 —— **已由 A-8 关闭** | §8 Q-2 已关闭 | ✅ 一致（结论：跟随夜纸，但**在图谱 change 里做**） |

### 7.2 出入一：钉回清单的**数量**与**取值**

**原** `night-paper-tokens.md` §1.2（2026-10-22 按 A-8 改写**前**）的钉回表
—— 该表已随 A-8 一并撤下（§1.2 现在只作范围声明，不再给施工图）。
此处**原样保留**作为历史记录，供图谱 change 复用其取值结论：

| 需钉回的 token | 浅色值 | 为什么 |
|---|---|---|
| `--surface-base` | `#fdf8ef` | 图谱画布周边底色 |
| `--surface-card` | `#fffdf7` | 图谱页的卡片面 |
| `--surface-raised` | `#ffffff` | 浮层 |
| `--surface-ink` | `#221f1a` | 墨块 |
| `--ink-strong` / `--ink-body` / `--ink-muted` / `--ink-faint` | `#221f1a` / `#3b3630` / `#6b6459` / `#8d8578` | 图谱内的字 |
| `--rule-hair` / `--rule-structure` | `#e6dcc4` / `#221f1a` | 图谱内的线 |
| `--role-blue` / `--role-yellow` / `--role-red` | `#2b62e8` / `#f5c518` / `#d1392b` | 图谱节点色 |

**计数出入**：任务书说「11 个 token」，但实测这张表是
**7 行 / 13 个 token 名**（`--surface-base`、`--surface-card`、`--surface-raised`、
`--surface-ink`、`--ink-strong`、`--ink-body`、`--ink-muted`、`--ink-faint`、
`--rule-hair`、`--rule-structure`、`--role-blue`、`--role-yellow`、`--role-red`）。
→ **以表为准：13 个**。本文件按 13 个记录。

**A-8 之后的读法**：这张表不再是「本变更要钉回什么」的施工图，
而是**图谱 change 钉回时的取值对照** —— 结论不变：**钉回值必须是「图谱今天的值」**，
不是「新层的浅色值」（见下表）。

**取值出入（关键）**：

| token | §1.2 给的浅色值 | 图谱页**今天**的实际值 | 结论 |
|---|---|---|---|
| `--surface-card` | `#fffdf7` | 图谱区段 `--paper: #fffdf7`（`:1506`） | ✅ 一致 |
| `--surface-base` | **`#fdf8ef`** | **`--lk-paper: #fffdf7`（`:5`）→ `body` 背景（`:67`）** | ❌ **不一致** |
| `--surface-raised` | `#ffffff` | 图谱区段无对应；`--dsw-bg-layer-1: #fffefa`（`:17`）是顶栏/右栏面 | ⚠️ 值不同（`#ffffff` vs `#fffefa`） |
| `--surface-ink` | `#221f1a` | 图谱区段 `--ink: #191816`（`:1507`） | ❌ **不一致** |
| `--ink-*` 四件套 | `#221f1a / #3b3630 / #6b6459 / #8d8578` | 图谱区段 `--ink: #191816`（`:1507`） | ❌ **不一致** |
| `--rule-hair` / `--rule-structure` | `#e6dcc4` / `#221f1a` | 图谱区段 `--hair: #ddd8cd`（`:1508`） | ❌ **不一致** |
| `--role-blue` / `--role-yellow` / `--role-red` | `#2b62e8 / #f5c518 / #d1392b` | 图谱区段 `--blue: #2457c5` / `--yellow: #f2c94c` / `--red: #d6453d`（`:1509 :1511 :1513`） | ❌ **不一致** |

**为什么这是实质冲突（不是措辞差异）**：

`night-paper-tokens.md` §1.2 的钉回表列的是**新 token 层的浅色主题值**，
而 G-5 要求的是**「图谱页与改造前逐像素一致」**。
两者的目标值**不同**：

- 新层的浅色底色是**浅奶油 `#fdf8ef`**（`decisions.md:606`）；
- 图谱页今天的底色是**`#fffdf7`**（`workbench.css:5`）。
- RGB(253, 248, 239) ≠ RGB(255, 253, 247) → **整页底色像素变** → G-5 FAIL。

同理，新层的角色色（`#2b62e8` 等）比图谱自己的（`#2457c5` 等）更饱和更亮，
新层的墨色（`#221f1a`）比图谱自己的（`#191816`）更暖 → 节点面、边、标签全变。

**裁决（按任务要求「以『图谱页观感必须与现在完全一致』为准」）**：

> **图谱路由下钉回的值，必须是「图谱页今天的值」，而不是「新层的浅色值」。**
>
> 具体地，图谱页作用域需要钉回的是：
>
> | 新层 token | 图谱页应钉回的值 | 来源 |
> |---|---|---|
> | `--surface-base` | **`#fffdf7`**（不是 `#fdf8ef`） | `workbench.css:5` `--lk-paper` |
> | `--surface-card` | `#fffdf7` | `workbench.css:1506` `--paper` |
> | `--surface-raised` | **`#fffefa`**（不是 `#ffffff`） | `workbench.css:17` `--dsw-bg-layer-1` |
> | `--surface-ink` | **`#191816`**（不是 `#221f1a`） | `workbench.css:1507` `--ink` |
> | `--ink-strong` / `--ink-body` / `--ink-muted` / `--ink-faint` | **`#191816` / `#191816` / `#191816` / `#191816`**（或按图谱区段实际用到的取值逐项钉） | `workbench.css:1507` |
> | `--rule-hair` | **`#ddd8cd`**（不是 `#e6dcc4`） | `workbench.css:1508` `--hair` |
> | `--rule-structure` | 图谱区段无对应描边 token → **钉回 `#ddd8cd`** 或不适用 | `workbench.css:1508` |
> | `--role-blue` | **`#2457c5`**（不是 `#2b62e8`） | `workbench.css:1509` `--blue` |
> | `--role-yellow` | **`#f2c94c`**（不是 `#f5c518`） | `workbench.css:1511` `--yellow` |
> | `--role-red` | **`#d6453d`**（不是 `#d1392b`） | `workbench.css:1513` `--red` |
>
> **并且**：最稳妥的做法是**根本不引入这层映射** ——
> 图谱页的画布用图谱自己的 `--paper` / `--ink` / `--hair` / `--blue` / `--yellow` / `--red`
> （`workbench.css:1506-1517`），**不经过任何新 token**。
> §3.4 的 C-8 实测已经证明这是现状，只要**一行不改**（F-21）就天然成立。
> 新层只需要**不污染**这 12 个裸名（F-1、F-2、F-15），并把**外壳**（顶栏 / 左栏 / 右栏）
> 的 14 个落点钉回原值（B-1…B-3）。
>
> **A-8 之后**：本裁决的**执行主体**是 `graph-node-visual-language`；
> 本变更只遵守其中「不误伤」的部分（`tasks.md` 1.2、`acceptance.md` G-5）。

### 7.3 出入二：`--surface-sheet` vs `--surface-card` 的命名冲突

| 文件 | 用的名字 | 出处 |
|---|---|---|
| `design.md:131`、`:133`、`:1083`、`:1239` | **`--surface-sheet`** | 「新层里保留一个**只给图谱用**的 `--surface-sheet: #fffdf7`」+ `#layout[data-page="graph"] #middle { background: var(--surface-sheet); }` |
| `tasks.md` 1.2 | **`--surface-sheet`** | 原 1.2「建图谱兼容区：保留只给图谱用的 `--surface-sheet: #fffdf7`（值与今天完全一致），并新增 `#layout[data-page="graph"] #middle { background: var(--surface-sheet); }`」—— ⚠️ **A-8 之后该条已改写为「图谱不受影响（保护措施）」**，措辞不再主张建「图谱兼容区」，但**「图谱专用纸面 token 恒为 `#fffdf7`」这条硬事实不变** |
| `decisions.md:732` | **`--surface-sheet`** | 「图谱页的 9 处控件与 `--surface-sheet` 属于冻结项」 |
| `component-spec.md:19`、`:163`、`:1818` | **`--surface-sheet`** | 「（尤其 `--surface-sheet` 保持 `#fffdf7`）」 |
| `asset-spec.md:180` | **`--surface-sheet`** | 「不得引用图谱页专用的 `--surface-sheet`」 |
| `night-paper-tokens.md` §3.1（2026-10-22 改写后） | **`--surface-graph-sheet`** | 「`--surface-graph-sheet` \| `#fffdf7` \| `#fffdf7` \| 图谱页专用（**保护用**）」—— ⚠️ **第三个名字**：改写后 §1.2 的钉回表已撤下，图谱专用纸面 token 在该文件里的名字是 `--surface-graph-sheet`；同文件里的 `--surface-card` 是**全站卡面** token（有夜纸值 `#232019`），**不是**图谱专用 |
| `tmp/agent-briefs/SYNTH.md:31` | **`--surface-sheet`** | 「新 token 层不得改变图谱依赖的 token 值（尤其 `--surface-sheet` 保持 `#fffdf7`）」 |

**这是契约漂移（contract drift）**：同一个语义（"图谱专用的、值恒为 `#fffdf7` 的纸面 token"）
现在有**三个名字**——`--surface-sheet`（6 份文件）、`--surface-card`（原
`night-paper-tokens.md` §1.2，已撤下）、`--surface-graph-sheet`（现
`night-paper-tokens.md` §3.1）。

**按 `AGENTS.md`「契约冲突处理」**：

- 本文件**不选边**，但**记录一个可执行的判据**：
  `--surface-card` 在 `night-paper-tokens.md` 的完整值表（§3.1）里**有夜纸值 `#232019`**，
  而 `--surface-sheet` 在 `design.md` / `tasks.md` 里是**图谱专用、无夜纸值、恒为 `#fffdf7`**。
  → 两者**不是同一个 token**：`--surface-card` 是全站卡面 token（会随主题变），
  `--surface-sheet` / `--surface-graph-sheet` 是图谱专用冻结 token（永不随主题变）。
- → **正确做法**：图谱页必须使用**图谱专用且不随主题变**的 token
  （`--surface-sheet` 或 `--surface-graph-sheet`），
  **不能**用 `--surface-card`。若实现时把图谱页接到 `--surface-card` 上，
  夜纸下卡面会变 `#232019` → 图谱页在夜纸下**大面积变色** → 图谱观感被误伤。
- → **登记为待核项**（§8 Q-6），需所有者裁决最终命名，并同步
  `night-paper-tokens.md`、`design.md`、`tasks.md`、`decisions.md`、`component-spec.md`、
  `asset-spec.md` 六份文件（**不是本文件的责任范围**）。
- → **A-8 之后**：这条漂移的**裁决主体是图谱 change**（`graph-node-visual-language`）——
  它要同时定下「图谱专用纸面 token 的名字」与「夜纸下图谱用什么值」；
  本变更只要保证自己**不误伤**（不用 `--surface-card` 顶替图谱纸面）即可。

### 7.4 一致性小结

| 维度 | 结论 |
|---|---|
| 「新 token 层与图谱 12 个裸名零同名」 | **两文件完全一致**（F-1/F-2/F-15）—— 且这是本变更对图谱的**唯一硬约束** |
| 「图谱画布本身两主题逐像素不变」 | **两文件完全一致**，本文件补了 C-8 实测（区段零全局依赖） |
| 「本变更不触碰图谱」 | **两文件完全一致**（A-8）；本文件随之从「隔离工程」变为「移交说明」 |
| 「图谱路由需把外壳 token 钉回浅色值」 | **方向一致，数值有出入**：§1.2 原表用的是新层的浅色值，**本文件要求用图谱今天的值**（§7.2）—— 出入的裁决主体 = 图谱 change |
| 钉回清单的条数 | **13 个**（原 §1.2 的表是 7 行 13 名；任务书说的「11 个」与表不符） |
| token 命名 | **存在漂移**：`--surface-sheet` / `--surface-card` / `--surface-graph-sheet` 三个名字（§7.3），登记为 Q-6 |
| 夜纸是否波及图谱页 | **已由 A-8 关闭**：夜纸下**图谱跟随夜纸**，但**在 `graph-node-visual-language` 里做**（Q-2） |

---

## 8. 待核事项（不臆断，按「待核」登记）

> **A-8 之后的读法**：Q-1 / Q-2 / Q-6 / Q-7 / Q-8 的**裁决主体已变为
> `graph-node-visual-language`**（图谱 change）；Q-3 / Q-4 / Q-5 仍是
> 本变更可以直接实测的项。Q-9 / Q-10 是本轮新登记的**移交事实**。

| # | 事项 | 查证方式 | 状态 |
|---|---|---|---|
| Q-1 | G-5 的比对范围是整页还是画布区域 | 所有者裁决（§6.7）。影响图谱 change 的任务 11/12 是否需要为图谱页留旧外壳分支 | **待裁决 —— 归 `graph-node-visual-language`**（本变更只需 G-5 的否定式断言：差异 = 0） |
| Q-2 | 图谱页是否参与夜纸主题 | **已关闭**：`decisions.md` **A-8** —— 夜纸下**图谱跟随夜纸**，但**在 `graph-node-visual-language` 里做**；本变更不碰图谱 | **已关闭**（A-8） |
| Q-3 | 任务 11.2 删除 `#middle-page > .page-header { padding-right: 128px }`（`workbench.css:255`）后，图谱页标题的左移量 | 在改造分支上实测 `.page-header` 的 `getBoundingClientRect()` 差值；非零即 FAIL（F-16） | 待实测（**本变更可实测**） |
| Q-4 | 任务 2.1 的 29 个 hex 里，有多少落在 `workbench.css:1497-1884` 内 | **已实测**：`sed -n '1497,1884p' workbench.css \| grep -cE '#[0-9a-fA-F]{3,6}'` → **83**。图谱区段内的硬编码 hex 命中数远多于任务 2.1 的收编清单 → F-11（收编必须排除 `1497-1884`） | **已解决** |
| Q-5 | `agent-ui.css` 在图谱页右栏的可见元素中，有多少实际渲染（空态 / 有会话） | 两个状态各截一张：S-G1（空对话列表）与 S-G6（有对话列表） | 待实测（**本变更可实测**） |
| **Q-6** | 图谱专用纸面 token 的最终命名：`--surface-sheet`（`design.md` / `tasks.md` / `decisions.md` / `component-spec.md` / `asset-spec.md` / `SYNTH.md`）· `--surface-card`（原 `night-paper-tokens.md` §1.2，已撤下）· `--surface-graph-sheet`（现 `night-paper-tokens.md` §3.1） | 所有者裁决 + 六份文件同步。三者语义应统一（前者恒定、后两者是全站卡面 token）→ §7.3 | **待裁决 —— 归 `graph-node-visual-language`**（契约漂移） |
| **Q-7** | 图谱路由钉回的**具体取值**：用「新层浅色值」（原 `night-paper-tokens.md` §1.2 钉回表）还是「图谱今天的值」（本文件 §7.2） | 所有者裁决。图谱页要求后者；§7.2 已给出逐项对照表 | **待裁决 —— 归 `graph-node-visual-language`** |
| **Q-8** | 任务 11.3–11.5 与 12.1（左栏 / 顶栏 DOM 改造）是否给图谱页留旧外壳分支 | 所有者裁决。若不留，则 G-5 的 R-1 整页口径**在结构上不可能达成**，必须走 R-2 + R-3 | **待裁决 —— 归 `graph-node-visual-language`**（与 Q-1 绑定） |
| **Q-9**（新增） | **图例色与 WebGL 实际线色不一致**：图例「相关」色 `#aaa399`（`workbench.css:1796`）与 SVG 边 `.graph-edge.related`（`:1636`）同值，但 WebGL 接管后 SVG 边被隐藏（`graph-renderer.js:148`），实际画出来的是 `EDGE_COLORS.related = [117/255, 112/255, 104/255]` = **`rgb(117,112,104)` = `#757068`** | 已实测（`graph-renderer.js:15-19`） | **移交 `graph-node-visual-language`**（图谱 change 顺手校正图例色键；本变更不动图谱） |
| **Q-10**（新增） | **死规则清单**（声明了但永不生效，可安全清理）：① `--green` / `--graphite` 全仓**无 CSS 引用**（仅声明，§3.2）；② `.node-wrap.in-scope .status-ring`（`workbench.css:1708`）永不命中，因为 `graphSyncScope()`（`workbench.js:1077`）是**空函数**（`:1052` 处调用） | 已实测（§3.2 + `grep -n 'graphSyncScope' workbench.js`） | **移交 `graph-node-visual-language`**（图谱 change 可删或接线；本变更不动图谱） |

---

## 9. 结论

> **A-8 之后**：本文件不再是「本变更怎么隔离图谱」的施工图，而是
> **「图谱 change 接手时必须知道什么」的移交说明**。
> 下面 8 条**全部保留**（都是实测结论），只是**归属**变了：
> 前 4 条是图谱页的客观构成，第 5 条是移交清单本体，第 6 条是比对方法论，
> 第 7 条是待裁决项，第 8 条是与 `night-paper-tokens.md` §1.2 的一致性结论。

1. 图谱页**不是**一块自足的样式：它由 `pages.py:410-481` 的 HTML、`workbench.css:1497-1884`
   的 388 行专用样式、**外加区段外的 25 行图谱规则**（`:509-513`、`:536-595`、`:1167-1171`）、
   6 个 JS 模块、4 个 API 端点共同构成；图谱区段内另有 **83 处**硬编码 hex
   （`sed -n '1497,1884p' | grep -cE '#[0-9a-fA-F]{3,6}'` 实测），远超任务 2.1 的收编清单。
2. **最重要的实测（C-8）**：图谱专用区段（`:1497-1884`）对全局 token
   `--lk-*` / `--dsw-*` 的引用**恰好是 0 次**（14 种 `var()` 全部是图谱自有的 12 个裸名
   或 4 个本地变量）。→ **L1 天然自足**，只要不动 `:1505-1518` 这 12 个裸名，
   图谱自身就绝不会因全局 token 变化而变。危险的全部集中在 **L2 外壳**与
   **区段外那 14 个全局 token 落点**（§3.2）。
3. 图谱专用 `:root`（`:1505-1518`）的 12 个变量与全局层**命名空间不相交**，
   今天**并不存在「覆盖」**；它之所以安全，靠的是「同特异性 + 后写者赢」这条**顺序**。
   真正的风险是**新层反向定义同名裸名**（`--ink` 已在任务 1.2 中出现），
   以及**夜纸用 `html[data-theme=…]` 以更高特异性压过 `:root`**。
4. 图谱**自身**对全局 token 的依赖很浅；图谱**外壳**（顶栏 / 左栏 / 右栏 / 页面底色 /
   字体栈 / 圆角）与**详情面板**却深度依赖全局层——
   **图谱页的像素一致，本质上要求外壳为图谱页重新钉回原值。**
   而且这层依赖会被 **auto-fit 放大**：`graphFit()`（`workbench.js:1203-1227`）用画布像素尺寸
   算缩放，**中栏宽度一变 → 整幅图谱的缩放就变**（F-22）。
5. 本文件给出 **22 条硬事实（F-1…F-22）**，其中 **6 条**（B-1…B-6：圆角 / 字体栈 /
   `--lk-paper` 系列 / `#middle-page` 转场 / 全局 `transition` / `body` 背景）
   展开成带传导链与可执行验证的专章；另有 **15 条静态断言 + 12 条运行时断言 +
   6 条视觉断言**，以及一套**单命令自检脚本**（§5.5）。
   **执行与验收归 `graph-node-visual-language`**；本变更只借用 F-1 / F-2
   （零同名）作为「没有误伤」的证据。
6. 像素级比对方案的关键不是"截两张图比"，而是**先把三类动画源各自冻结**：
   环境色 canvas（reduced motion → `t=0` 单帧）、物理布局（等 `.solving` 消失 **且**
   DOM 静止签名连续 3 次不变，**签名必须含 `#graph-stage` 的 transform** 以覆盖 auto-fit）、
   WebGL2 边（reduced motion → 同步 `draw()`）。
   **并且**：不开 reduced motion 时，节点尺寸/透明度的缓动帧数随机器负载变化
   （`workbench.js:1443-1444` 的 `overBudget` 会跳过绘制），
   → **像素比对在非 reduced 模式下根本不可复现**。reduced motion 是必要条件，不是便利。
7. 存在 **8 项待核（Q-1…Q-8）+ 2 项新登记的移交事实（Q-9 / Q-10）**，
   其中 Q-1（G-5 比对范围）、Q-6（`--surface-sheet` / `--surface-card` /
   `--surface-graph-sheet` 命名漂移）、Q-7（钉回值取「新层浅色值」还是「图谱今天的值」）
   是**契约冲突**，按 `AGENTS.md` 要求保持显式，**裁决主体是图谱 change**；
   Q-2（夜纸是否波及图谱页）已由 A-8 关闭。
8. 与 `night-paper-tokens.md` §1.2 的核对结论（§7）：**「新 token 层与图谱 12 个裸名
   零同名」与「图谱画布两主题逐像素不变」两条完全一致**；
   **出入只在「钉回的具体取值」与「token 命名」两处**，
   本文件主张钉回**图谱今天的值**（§7.2 对照表），并把命名漂移登记为 Q-6。
   而 §1.2 现在的**范围结论**（「本变更不触碰图谱」）与本文件的新定位**完全一致**。
