# 知识图谱页隔离清单（graph-isolation）

> **性质**：知识图谱页是本次前端改造的**明确不可触碰区**（`proposal.md`「Explicitly out of
> scope」）。本文件的全部目的是**证明它不会被改动**，并给出**可执行的验证方法**。
> **本文件不提出任何图谱页的改动建议。**
>
> **依据**：`openspec/changes/workbench-visual-language-v2/proposal.md`（范围与冻结）、
> `decisions.md`「# 收口：最终基线」（视觉基线）、`acceptance.md` §0 **G-5**
> （图谱页观感不变 → 像素级一致）、`tasks.md:9-11`（图谱区段一行不改的硬约束）。
>
> **所有行号均为实测**（`grep -n` / `sed -n` 于 2026-10-21 的工作区状态），
> 文件路径相对仓库根 `D:\Projects\Academic Workflow\lesson-kit`。
>
> **本文件不改动任何产品代码。**

---

## 0. 一句话契约

> **图谱页不是一个独立页面，它是一条从服务端模板到 WebGL 画布的纵切链路；
> 这条链路上任何一环被全局 token 牵动，整页截图就不再像素一致。**
>
> 本次改造可以换掉整张设计语言，但**不能换掉这条链路上的任何一个取值**——
> 除非该取值在图谱作用域内被**重新钉回原值**。

隔离分两层，两层都必须成立：

| 层 | 范围 | 隔离方式 |
|---|---|---|
| **L1 图谱自身** | 画布、节点、边、图例、控制卡、缩放、toast、详情面板 | 图谱专用 `:root`（`workbench.css:1505-1518`）+ 图谱专用区段（`:1497-1884`）——**一行不改** |
| **L2 外围外壳** | 顶栏 / 左栏 / 右栏 / 页面底色 / 字体栈 / 三栏几何 | 与全站共享 token——**必须为图谱页重新钉回当前取值**，否则 G-5 整页比对必 FAIL |

---

## 1. 图谱页完整影响面清单

### 1.1 服务端渲染（HTML 结构）

**`workbench/server/pages.py`**

| 位置 | 内容 |
|---|---|
| `pages.py:410-481` | `graph_page()` 全体 |
| `pages.py:415-416` | `_page_header(...)` → 标题「知识图谱」，副标题「约束布局 · 纸质图谱 · 蒙德里安」 |
| `pages.py:417` | `.page-content.graph-content` 容器 |
| `pages.py:418` | `header.graph-topbar` |
| `pages.py:419-420` | `#graph-search`（搜索框，内含 `.visually-hidden` label） |
| `pages.py:421-426` | `.seg#graph-views` — 4 个视图按钮（structure / problem_count / importance / state），默认 `.active` 在 structure |
| `pages.py:427` | `#graph-focus` 聚焦按钮 |
| `pages.py:428` | `#graph-fit` 适应画布按钮 |
| `pages.py:430` | `.graph-workspace#graph-workspace[data-dashboard='collapsed']` — **看板默认收起是像素基线的组成部分** |
| `pages.py:431` | `section.graph-shell#graph-canvas[tabindex=0]` |
| `pages.py:432` | `.floating.controls#graph-controls[data-collapsed='true']` — **控制卡默认收起** |
| `pages.py:433-435` | `#graph-controls-toggle` / 「图谱控制」 |
| `pages.py:438-443` | `.filter-row#graph-filters` + 5 个 `.chip`（全部 / 重点练习 / 可以复习 / 已掌握 / 未标记） |
| `pages.py:444-451` | `#graph-gravity`（range，默认 85）/ `#graph-gravity-value` / `.distance-scale` 三格 |
| `pages.py:452-458` | `#graph-solver-state`+`.solver-dot` / `#graph-solver-text` / `#graph-readability-state` / `#graph-edge-budget` |
| `pages.py:460` | `canvas.graph-tide#graph-tide` — **持续动画的环境色 canvas**（见 §6） |
| `pages.py:461` | `.graph-stage#graph-stage > svg.graph-edges#graph-edges` — SVG 边（被 WebGL 接管后隐藏，见 `graph-renderer.js:148`） |
| `pages.py:462-467` | `.legend#graph-legend` + 5 个 `.legend-item`（先修 / 相关 / 应用 / 对比 / 隐含） |
| `pages.py:468-471` | `.zoom` + `#graph-zoom-out` / `#graph-zoom-in` / `#graph-reset` |
| `pages.py:472` | `.toast#graph-toast` |
| `pages.py:474-477` | `aside#graph-detail-panel.graph-dashboard` — 学习看板（收起时 `display:none`，见 `workbench.css:1544`） |
| `pages.py:478-481` | 调 `shell(..., "graph", graph_mode=True, page_type="graph", ...)` |
| `pages.py:68-109` | `shell()` 全体——图谱页与其它页共用外壳 |
| `pages.py:91` | `_ai_column(workspace["name"], graph_mode, page_type)` — 图谱页右栏 |
| `pages.py:94-95` | `#layout[data-page='graph']` — **图谱页的唯一 CSS 作用域开关** |
| `pages.py:97` | `<main id='middle'> … <div id='middle-page'>` — 三栏骨架与视图转场容器 |
| `pages.py:100-102` | **仅图谱页注入**三个脚本：`graph-physics-core.js` → `graph-renderer.js` → `graph-physics.js` |

**`workbench/server/app.py`**

| 位置 | 内容 |
|---|---|
| `app.py:236` | 路由形态注释 `/w/{name}/{practice\|kps\|kp/{id}\|graph\|session-end}` |
| `app.py:260-263` | `page == "graph"` → `pages.graph_page(...)` |
| `app.py:85-87` | `GET /api/w/{name}/graph/model`、`POST /api/w/{name}/graph/state`、`POST /api/w/{name}/graph/kp` |
| `app.py:103` | `GET /api/w/{name}/graph`（raw artifact） |
| `app.py:145-146`, `app.py:341-352` | `_send_graph_artifact()` |

### 1.2 CSS

**A. 图谱专用区段：`workbench/server/static/workbench.css:1497-1884`（388 行，一行不改）**

| 区段 | 行 | 内容 |
|---|---|---|
| 图谱专用 `:root` | `1505-1518` | 12 个图谱 token（清单见 §2） |
| 页面胶水 | `1520-1560` | `#layout[data-page="graph"] #middle` / `#middle-page` / `.graph-content` / `.graph-workspace` / `.graph-dashboard` |
| 顶栏 | `1562-1593` | `.graph-topbar` 及其 `.search` / `.seg` / `.icon-btn` |
| 画布外壳 | `1595-1639` | `.graph-shell`（含 `::before` 网格纹理、`::after` 点阵）+ `.graph-tide` + `.graph-stage` + `.graph-edges` + 5 条边色 |
| 节点 | `1641-1719` | `.node-wrap` / `.metric-track` / `.status-ring` / `.node-face` / `.node-value` / `.node-satellite` / `.label` / `.meta` |
| 浮动控制卡 | `1721-1776` | `.floating` / `.controls` / `.control-toggle` / `.chip` / `.slider-block` / `.solver-line` / `.distance-scale` |
| 图例 / 缩放 / toast | `1778-1813` | `.legend` / `.zoom` / `.toast` + `@keyframes graph-pulse`（`1772`） |
| 详情面板 | `1815-1859` | `#graph-detail-panel` 全部子规则 |
| 降级 | `1861-1867` | `@media (prefers-reduced-motion: reduce)` — `.graph-tide{opacity:.62}` 等 |
| 窄屏 | `1869-1884` | `@media (max-width:900px)` / `@media (max-width:640px)` |

**B. 图谱区段**之外**的图谱相关规则（最容易漏掉的一批 —— 不在 1497-1884 内，但同样属于图谱页）**

| 位置 | 选择器 | 依赖的全局 token |
|---|---|---|
| `workbench.css:509` | `.graph-content { max-width: none; }` | — |
| `workbench.css:510` | `#layout[data-page="graph"] #middle` | — |
| `workbench.css:511` | `#layout[data-page="graph"] .page-header` | — |
| `workbench.css:512` | `#layout[data-page="graph"] .page-summary` | — |
| `workbench.css:513` | `#layout[data-page="graph"] .graph-content` | — |
| `workbench.css:536-537` | `#graph-detail-panel` / `h2` | — |
| `workbench.css:538-547` | `#graph-detail-panel .graph-dashboard-metrics` | `--dsw-border-l1` / `--dsw-radius-sm` |
| `workbench.css:552-563` | `.graph-dashboard-metrics > div / span / strong` | `--dsw-bg-layer-1` / `--dsw-label-secondary` |
| `workbench.css:564-565` | `.graph-dashboard-note` / `.graph-dashboard-link` | — |
| `workbench.css:567-593` | `.graph-relations-panel` … `.graph-relation-row*` | `--dsw-border-l1` / `--dsw-radius-sm` / `--dsw-bg-layer-1` / `--dsw-label-tertiary` / `--dsw-label-secondary` / **`--lk-blue`** / **`--lk-red`** |
| `workbench.css:594-595` | `#graph-detail-panel label` / `select` | `--dsw-label-secondary` |
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
| `workbench.css:1688` | `.node-value { font-family: Georgia, "Songti SC", "STSong", "SimSun", serif; … }` |
| `workbench.css:1712` | `.label { font-family: Georgia, "Songti SC", "STSong", "SimSun", serif; … }` |
| `workbench.css:1742` | `.control-toggle strong { font-family: Georgia, "Songti SC", "SimSun", serif; … }` |
| `workbench.css:1748` | `.control-head strong { font-family: Georgia, "Songti SC", "SimSun", serif; … }` |
| `workbench.css:1823` | `#graph-detail-panel h2, h3 { font-family: Georgia, "Songti SC", "STSong", "SimSun", serif; … }` |

> 这 5 处是**硬编码字族栈**，不引用任何 token。任务 3.2 引入 `--font-reading` 时若「顺手统一
> 全站衬线栈」，就会改到这 5 行 → 节点数字与标签的字形与字宽全变 → 整幅图谱重排。

**E. 样式表装载顺序（`workbench/server/pages.py:1101-1103`）**

```
/static/workbench.css   →  /static/agent-ui.css   →  /static/katex/katex.min.css
```

`agent-ui.css` 在 `workbench.css` **之后**装载，因此 `agent-ui.css` 中的
`--lk-paper` / `--dsw-*` 用法（`:17 :39 :142 :152 :165 :231 :368 :400 :424`，
`--dsw-radius-sm` 在 `:141`，`--dsw-radius-md` 在 `:207 :241`）同样落在图谱页的
右栏上。

**F. 静态资源服务（`workbench/server/app.py:214-232`）**

`_send_static()` **不发送 `Cache-Control`、不发送 `ETag`、不发送 `Last-Modified`**。
→ 截图前必须显式绕过浏览器缓存（见 §6.4），否则「改造后」可能拿到「改造前」的 CSS。

### 1.3 JavaScript

| 文件 | 行数 | 角色 | 图谱页上的作用 |
|---|---|---|---|
| `workbench/server/static/graph-physics-core.js` | 1603 | DOM-free 的约束语义布局求解器；被 worker `importScripts` | 无 DOM 依赖 → 天然不受 CSS 影响 |
| `workbench/server/static/graph-physics-worker.js` | 100 | Worker 外壳 | `importScripts`（`:3`）、`onmessage`（`:60`）、`step` 步进（`:89-95`） |
| `workbench/server/static/graph-physics.js` | 398 | 公共模块 + Worker 宿主 | `layoutStorageKey()`（`:43-48`）、`storage()`（`:50-53`）、`readLayoutSeed()`（`:55-67`）、`writeLayoutSeed()`（`:69-86`）、`new Worker("/static/graph-physics-worker.js")`（`:302`）、调用 `readLayoutSeed`（`:344`） |
| `workbench/server/static/graph-renderer.js` | 379 | WebGL2 边渲染器 | `addStyle()`（`:142-152`）、`attach()`（`:154`）、`resizeCanvas()`（`:188-197`，dpr 夹到 1..2）、`applyLod()`（`:223-240`）、`draw()`（`:242`） |
| `workbench/server/static/workbench.js` | — | 图谱页的全部 DOM 侧逻辑 | `mountGraphPage()`（`:531-1941`，其中 `disposeGraphPage` 闭包 `:1927-1941`）；`mountMiddlePage()` 调 `graphPageDispose = mountGraphPage()`（`:4874`） |
| `workbench/server/static/middle-navigation.js` | — | 同工作区 SPA 换页 | `ensureGraphScripts()`（`:31-43`）、`installPage()`（`:68-80`，图谱分支 `:73-78`）、`installPageContent()`（`:82-93`，**`:87` `middlePage.innerHTML = nextPage.innerHTML;`**） |

**图谱页的关键运行时状态**（截图可比性的来源，见 §6）：

| 状态 | 位置 | 含义 |
|---|---|---|
| `graphTideState` | `workbench.js:1479` | 环境色 canvas 的动画状态；`reduced` 决定是否走 rAF 无限循环 |
| `graphTideState.reduced` | `workbench.js:1639` | `matchMedia("(prefers-reduced-motion: reduce)").matches` |
| `graphTideFrame()` | `workbench.js:1628-1636` | `:1634` `graphTideDraw(reduced ? 0 : now/1000)`；`:1635` 非 reduced 才重新排 rAF |
| `graphStartTide()` | `workbench.js:1638-1661` | `:1659` reduced 时只调 `graphTideFrame(0)` 一次 |
| `graphTideResize()` | `workbench.js:1501-1513` | 用 `graphCanvas.getBoundingClientRect()` 定 tide 画布尺寸，dpr = `Math.min(2, devicePixelRatio)` |
| 求解收敛判定 | `workbench.js:1440`（`solving = sim.graph.alpha > 0`）、`graph-physics-core.js:1246-1260`（`alpha` 衰减 → `settled = true`） | **无随机数**（`graph-physics-core.js` / `graph-physics.js` 全无 `Math.random`）→ 收敛终点确定 |
| 布局缓存 | `graph-physics.js:43-86` | 落盘到 `localStorage["lk_graph_layout_v1_<workspace>"]`；**二次访问直接采纳缓存、不再重解**（`:344-368`） |
| 画布 resize | `graph-renderer.js:188-197` | backing store = `stageWidth × dpr`（dpr 夹 1..2） |

### 1.4 影响面小结（数量）

| 类别 | 数量 |
|---|---|
| 服务端 HTML 行（图谱） | 68 行（`pages.py:410-481`）+ 3 行脚本注入（`pages.py:100-102`） |
| CSS 图谱专用区段 | 388 行（`workbench.css:1497-1884`） |
| CSS 图谱区段外的图谱规则 | **25 行**（`workbench.css:509-513`、`:536-547`、`:552-565`、`:567-595`、`:1167-1171`）。实测 `grep -nE 'graph' workbench.css` 在区段外命中 **26 行**，多出的 `:1047` 是含 "choreography" 字样的无关注释，非图谱规则 |
| CSS 运行时注入 | 2 行（`graph-renderer.js:147-148`） |
| CSS 图谱自带衬线栈 | 5 处（`workbench.css:1688/1712/1742/1748/1823`） |
| JS 模块 | 6 个文件 |
| API 端点 | 4 个（`app.py:85-87`、`:103`） |

---

## 2. 图谱专用 `:root` 与「覆盖」机制

### 2.1 图谱专用 `:root` 定义了什么（`workbench.css:1505-1518`）

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

### 2.2 引用点实测（全部落在 `1558-1850`，即 L1 之内）

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

### 2.3 「为什么能覆盖全局值」—— 机制澄清（**这里与常见误解不同，必须照抄执行**）

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
> 是本次最容易踩的坑（见 §4 D-1 与 §5 F-1）。

---

## 3. 图谱继承的全局 token 清单

判定口径：**「改它会不会让图谱页的像素发生变化？」会 → 必须保持不变。**

### 3.1 背景与纸面

| 全局 token | 定义 | 图谱页上的落点 | 判定 | 理由 |
|---|---|---|---|---|
| `--lk-paper` `#fffdf7` | `workbench.css:5` | `--dsw-bg-base`（`:16`）→ `body` 背景（`:67`）；`agent-ui.css:17/39/152/165/231/368/400/424` → 右栏 | **必须保持不变** | 改值 → 整页底色变 → 整页像素变 |
| `--lk-paper-shade` `#f3f1ea` | `:6` | `--dsw-sidebar-fill`（`:19`）→ `#left-column` 背景（`:168`） | **必须保持不变** | 改值 → 图谱页左栏底色变 |
| `--dsw-bg-layer-1` `#fffefa` | `:17` | `#topbar` 背景（`:102`）；`agent-ui.css:4` `#ai-column.agent-rail` 背景；`workbench.css:557` 指标格底 | **必须保持不变** | 改值 → 顶栏 + 右栏 + 详情面板变 |
| `--dsw-bg-layer-2` `#f3f1ea` | `:18` | `code`/`pre` 底（`:1031-1032`） | **必须保持不变** | 改值 → 图谱页内代码块变（右侧栏可能含代码） |
| `--dsw-bg-base` | `:16`（别名 `var(--lk-paper)`） | `body` 背景（`:67`） | **必须保持不变（值）** | 同 `--lk-paper` |

> 现状备注：`--dsw-bg-layer-1` 与 `--lk-paper` 的差是 `rgb(0,-1,-3)`（`proposal.md:8-9` 已实测），
> 肉眼几乎不可分。**但像素比对会判 FAIL**——所以「肉眼没变」不是放行理由。

### 3.2 墨色与文字

| 全局 token | 定义 | 图谱页上的落点 | 判定 |
|---|---|---|---|
| `--lk-ink` `#171717` | `:7` | `#topbar` 下边框（`:103`，2px）；`#left-column` 右边框（`:167`）；`#ai-column` 左边框（`:237`） | **必须保持不变** |
| `--dsw-label-primary` | `:20`（别名 `var(--lk-ink)`） | `body` 文字色（`:66`）→ 图谱顶栏/图例/控制卡全部继承文字 | **必须保持不变** |
| `--dsw-label-secondary` `#61666b` | `:21` | `.graph-relations-panel`（`workbench.css:584`）、详情面板 label（`:594`）、`agent-ui.css` 多处 | **必须保持不变** |
| `--dsw-label-tertiary` `#81858c` | `:22` | `.graph-relation-type`（`:580`）、`.side-label`（`:274-279`） | **必须保持不变** |
| `--dsw-label-caption` `#adb2b8` | `:24` | `.topbar-separator`（`:127`） | **必须保持不变** |
| `--dsw-border-l1` `rgb(0 0 0 / 4%)` | `:31` | `.graph-dashboard-metrics` 描边（`:543`）、`.graph-relation-row` 描边（`:575`） | **必须保持不变** |
| `--dsw-border-l2` `rgb(0 0 0 / 10%)` | `:32` | `agent-ui.css` 描边（`:19 :29 :52 :55`） | **必须保持不变** |

### 3.3 描边 / 分隔线

| 全局 token | 定义 | 判定 | 理由 |
|---|---|---|---|
| `--lk-ink`（作边框） | `:7` | **必须保持不变** | 三栏分隔线是图谱页构图的一部分；新基线「不用描边」的策略一旦落到 `#left-column`/`#ai-column`/`#topbar`，图谱页三栏边界形态改变 |
| `--dsw-border-l3` | `:33` | **本次允许改** | 图谱页无引用（实测 `grep var(--dsw-border-l3)` 命中 0 次在图谱相关规则内） |

### 3.4 圆角

| 全局 token | 定义 | 图谱页上的落点 | 判定 |
|---|---|---|---|
| `--dsw-radius-sm` `6px` | `:43` | `agent-ui.css:141`（右栏输入类）；`workbench.css:546`（`.graph-dashboard-metrics`，**在图谱区段外**）、`:575`（`.graph-relation-row`） | **必须保持不变** |
| `--dsw-radius-md` `6px` | `:44` | `agent-ui.css:207 :241`（右栏）；`workbench.css:202`（`.scope-tray-panel`） | **必须保持不变** |
| `--dsw-radius-lg` `22px` | `:45` | `workbench.css:442`（`.detail-block`） | **本次允许改**（图谱页无引用；但右栏若复用 `.detail-block` 则受影响 → 按「必须保持不变」执行更安全） |

> **图谱自身的圆角全部硬编码**（`border-radius: 4px / 5px / 3px / 2px / 999px / 50%`，
> 见 `workbench.css:1571 1578 1582 1590 1598 … 1838 1844 1855`），
> **不引用 `--dsw-radius-*`**。因此「圆角统一 12px」（任务 1.3）**不会**直接改动图谱控件的圆角——
> 但会改动**图谱页外壳**（右栏 `agent-ui.css:141/207/241`、详情面板 `:546/:575`）的圆角。

### 3.5 字体

| 全局 token | 定义 | 图谱页上的落点 | 判定 |
|---|---|---|---|
| `--dsw-font-family` | `:11-13` | `body { font-family: var(--dsw-font-family) }`（`:63`）→ 图谱顶栏、`.seg button`（`:1583`）、`.icon-btn`（`:1591`）、`.legend`（`:1784`）、`.chip`（`:1753`）、`.hint`（`:1763`）、`.solver-line`（`:1767`）等**全部非 Georgia 文字** | **必须保持不变** |
| `--dsw-font-code` | `:14-15` | `code`/`pre`（`:1031-1032`） | **本次允许改**（图谱画布不渲染代码；右栏若含代码块则受影响） |
| 图谱自带 Georgia 栈 | `:1688 :1712 :1742 :1748 :1823` | 节点数字、节点标签、控制卡标题、详情面板标题 | **必须保持不变**（硬编码，不改这 5 行） |
| 新 `--font-reading`（任务 3.2） | 待建 | 若实现「全站衬线统一」会改到上面 5 行 | **禁止施加于图谱区段** |

### 3.6 阴影

| 全局 token | 定义 | 图谱页上的落点 | 判定 |
|---|---|---|---|
| `--dsw-shadow-lv1` | `:36` | `workbench.css:189`（`.scope-tray-trigger`，图谱页已无此元素） | **本次允许改**（图谱页无可见落点） |
| `--dsw-shadow-lv2` | `:37` | 图谱页无引用 | **本次允许改** |
| `--dsw-shadow-lv3` | `:38-39` | `workbench.css:1189`（窄屏抽屉）；`agent-ui.css` 右栏浮层 | **必须保持不变**（右栏在图谱页可见） |
| 图谱 `--shadow` | `:1517` | `.floating` 控制卡（`:1726`） | **必须保持不变** |

### 3.7 动效 / 时长 / 缓动

| 全局 token / 规则 | 定义 | 图谱页上的落点 | 判定 |
|---|---|---|---|
| `@media (prefers-reduced-motion: reduce)` 全局降级 | `workbench.css:1126-1131` | `transition: none !important; animation: none !important` 作用于**全部元素** | **必须保持不变** | 删掉它 → 图谱页 `.node-face` 的 `transition: transform .18s…`（`:1680`）、`.label` 的 `transition: opacity .16s`（`:1714`）恢复 → 截图时序敏感、像素不可比 |
| `graph-pulse` 关键帧 | `workbench.css:1771-1772` | 求解中圆点脉冲 | **必须保持不变** |
| 图谱 reduced-motion 区段 | `workbench.css:1863-1867` | `.graph-tide{opacity:.62}` / `.node-wrap,.node-face,.label,.meta,.toast{transition:none}` / `.solver-state.solving .solver-dot{animation:none}` | **必须保持不变** | 它是 §6 冻结方案的技术基础 |
| `#layout { transition: grid-template-columns 200ms ease }` | `workbench.css:161` | 三栏宽度过渡 | **必须保持不变（值）** | 任务 4.1 要求把它收编到 `--motion-*` token；**值必须仍是 200ms**，否则截图时若列宽在动，图谱画布尺寸会漂 |
| `#left-column/#ai-column { transition: transform 160ms ease }` | `workbench.css:1190` | 窄屏抽屉 | **必须保持不变（值）** |

### 3.8 布局 / 结构 token

| 项 | 定义 | 图谱页上的落点 | 判定 |
|---|---|---|---|
| `#layout` 三栏几何 `280px / 1fr / 420px` | `workbench.css:160` | 图谱页中栏宽度 → 画布宽度 | **必须保持不变**（值）；任务 11.1「改为 CSS 变量驱动」**可以改写法，但值不能变** |
| `.page-header, .page-content { max-width: 800px }` | `workbench.css:253` | 被 `.graph-content{max-width:none}`（`:509`）覆盖 | **必须保持不变** |
| `#middle-page > .page-header { padding-right: 128px }` | `workbench.css:255` | 图谱页 `.page-header` 在 `#middle-page` 内 → **生效** | **必须保持不变**（任务 11.2 要删它 → 会让图谱页标题右移 → 像素变。**必须为图谱页保留**） |
| `#middle { padding: 34px 40px 48px }` | `workbench.css:175` | 图谱页中栏内边距 | **必须保持不变** |
| `.graph-workspace { gap: 12px; padding-top: 12px }` | `workbench.css:1529-1537` | 图谱区段内 | **必须保持不变** |

### 3.9 判定汇总

| 类别 | 必须保持不变 | 本次允许改 |
|---|---|---|
| 背景 / 纸面 | 5 | 0 |
| 墨色 / 文字 / 描边 | 7 | 1 |
| 圆角 | 2 | 1（但图谱页右栏可见 → 建议按不变处理） |
| 字体 | 2（+ 图谱自带 5 行硬编码） | 1 |
| 阴影 | 2 | 2 |
| 动效 / 时长 | 6 | 0 |
| 布局 / 结构 | 5 | 0（可改写法不可改值） |
| **合计** | **29 项** | **5 项** |

---

## 4. 禁止改动清单（可执行）

> 每行的「替代做法」都是**不改图谱**的合规路径。表中的「位置」是**必须核对的锚点**。

| # | 改动点 | 位置 | 为什么危险 | 替代做法 |
|---|---|---|---|---|
| **F-1** | 新 token 层定义裸名 `--ink` | 新 `:root`（`workbench.css:4-46` 内） | **与图谱 `--ink:#191816`（`:1507`）同名**。同特异性后写者赢；图谱 `:root` 在 `:1505` 更靠后，今天侥幸赢；一旦有人在 `:1518` 之后追加 `:root`（M-5），或写 `html[data-theme="night"] { --ink: … }`（M-4，特异性更高，**无视顺序**），图谱详情面板文字与搜索框文字色立刻变 | 给新墨色取带前缀的族名（`--role-ink` / `--color-ink` / `--lk-ink-v2`），**不要用 `--ink`**。若已用 `--ink`，则在夜纸块里显式重钉 `--ink:#191816` |
| **F-2** | 新 token 层定义裸名 `--paper` / `--shadow` / `--blue` / `--red` / `--yellow` / `--hair` / `--*Soft` | 同上 | 12 个图谱 token 全部裸名（`workbench.css:1506-1517`），撞一个改一个。其中 `--paper` → 画布底色（`:1602`）、`--shadow` → 控制卡阴影（`:1726`）、`--blue` → 先修边与核心节点色（`:1635` 用的是硬编码 `#456fc9`，但 `:1651/1656/1708/1756/1762/1771/1848` 用 `var(--blue)`） | 新层一律用带前缀族名（`--surface-*` / `--role-*` / `--shadow-*` / `--hair-*`）。落地前用 §5.1 的 grep 断言 12 个名字各只声明一次 |
| **F-3** | 全局圆角变量 `--dsw-radius-sm/md/lg` 改值 | `workbench.css:43-45`（任务 1.3 要改） | 图谱页**外壳**用它：`agent-ui.css:141`（`--dsw-radius-sm`）、`:207 :241`（`--dsw-radius-md`）、`workbench.css:546 :575`（图谱区段**外**的详情面板/关系行）→ 右栏与详情面板圆角变 | 改值可以（任务 1.3 的目标），但**必须为图谱页作用域重新钉回 `6px/6px/22px`**：`#layout[data-page="graph"] { --dsw-radius-sm:6px; --dsw-radius-md:6px; --dsw-radius-lg:22px; }` |
| **F-4** | 全局字体栈 `--dsw-font-family` 改值 | `workbench.css:11-13` | `body` 继承（`:63`）→ 图谱顶栏、`.seg button`、`.icon-btn`、`.legend`、`.chip`、`.hint`、`.solver-line` 全部文字字形/字宽变；节点标签布局不重排，但画布整体观感变 | 图谱页作用域钉回原栈：`#layout[data-page="graph"] { --dsw-font-family: <原值>; }`。注意：表单控件（`input`/`button`）在 Chrome UA 样式里**不继承** `font-family`——`.graph-topbar .search input`（`workbench.css:1570-1573`）未显式设 `font-family`，其字体由 UA 决定，与 `--dsw-font-family` 无关 |
| **F-5** | 「全站衬线统一」把图谱的 Georgia 栈换成 `--font-reading` | `workbench.css:1688 :1712 :1742 :1748 :1823` | 节点数字（`.node-value`）与节点标签（`.label`）的字形与字宽全变 → 标签换行、节点间距观感变 → 整幅图谱重排 | 这 5 行**保持原样**。新阅读面字体只接到题面/知识点正文/解析（任务 3.3 的三处） |
| **F-6** | `#middle-page` 视图转场动画 | 新增（任务 17.1） | `#middle-page` 是**全站共用容器**（`pages.py:97`），图谱页的 `.page-header` / `.graph-content` 是它的子节点。若转场实现为 `#middle-page > * { animation: lk-rise … }`（innerHTML 替换后新子节点重新触发），**图谱页每次进入都会播放上浮+淡入**；若含 `scale`，`graphCanvas.getBoundingClientRect()`（`workbench.js:1503/1666/1763`）会变形 → `graphTideResize()`（`:1501`）取到的 tide 画布尺寸与真实画布不符 → 环境色 canvas 与画布错位 | 转场作用域排除图谱页：`#layout:not([data-page="graph"]) #middle-page > *`。若坚持全站生效，则**必须**只动 `transform: translateY` / `opacity`（不含 `scale`），并在 §6 的截图协议里冻结动画 |
| **F-7** | `body` / `html` 的背景与 `font-family` | `workbench.css:60-71` | `body` 背景 = `var(--dsw-bg-base)` = `var(--lk-paper)`（`:16`、`:5`）→ 图谱页所有未被覆盖的底色；`font-family` → 全部继承文字 | 改 `body` 背景**只能通过改 `--lk-paper`/`--dsw-bg-base` 的值**——因此 §4 F-1/F-3/F-4 的「作用域钉回」是唯一合规路径 |
| **F-8** | `--lk-paper` 系列（`--lk-paper` / `--lk-paper-shade`）改值 | `workbench.css:5-6` | `--lk-paper` → 页面底 + 右栏（`agent-ui.css` 9 处）；`--lk-paper-shade` → 左栏底（`:168`）+ `--dsw-bg-layer-2` | 图谱页作用域钉回 `#fffdf7` / `#f3f1ea`；或**不动这两个变量**，把新基色放在新族名（`--surface-base`）上，让 `--lk-paper` 退化为别名但**图谱页作用域保留原值** |
| **F-9** | 全局 `transition` / `animation` 基线 | `workbench.css:1126-1131`（reduced-motion 全局降级） | 删掉或改窄这条全局 `!important` 规则 → 图谱的 `.node-face`（`:1680`）、`.label`（`:1714`）、`.meta`（`:1718`）、`.toast`（`:1810`）恢复过渡；`.graph-tide` 的 `opacity:.62` 降级（`:1864`）失效 | 保留该规则原样。新的 `--motion-*` token 只用于**新增**动效，不改这条兜底 |
| **F-10** | 新增/改写 `outline` 清理 | `workbench.css:338 :427 :833`（`outline:none`）、**`workbench.css:1572`（`outline: 0`）** | 任务 2.4 的 grep 是 `outline: *none`，命中 3 处；若被放宽到 `outline:\s*(none\|0)`，会命中 `1572`（`.graph-topbar .search input`）→ 图谱搜索框突然出现全局焦点环 | 焦点环清理只针对 `338/427/833` 三处；`1572` 属图谱区段，**排除**。可用 `sed -n '1497,1884p'` 过滤后再 grep |
| **F-11** | 硬编码 hex 收编（任务 2.1）批量替换 | `workbench.css` 全文 | 任务 2.1 列出 4 蓝 / 9 红 / 10 黄橙 / 6 绿共 29 个 hex。其中**图谱区段内**的硬编码 hex（`#456fc9 #aaa399 #c3a128 #c75a52 #bbb4a9 #d9d3c8 #eeeae1 #fffdf8 #9cb2e5 #f2eee5 #d8d2c6 #f4f5f7 #e0dbd0 #9499a2 #8c6b00 #555c66 #22201d #d3a914 #d8d2c6 #9a9388 #8d929a #535a65 #a0a5ad #59616d #a1a6ae #7e848d #4d4a44 #f3efe7 #f4f5f7 #2b2925 …`）若被收编成 token，**图谱边色/节点色/控件色全变** | 收编范围**排除 `workbench.css:1497-1884`**。用 `sed -n '1,1496p;1885,$p'` 过滤后再批量替换 |
| **F-12** | 左栏导航改造（任务 11.3–11.5）与顶栏三段式（任务 12.1） | `pages.py:_left_column` / `pages.py:71-85` | **DOM 结构改造，无法用 CSS 作用域排除**。左栏加图标、顶栏重排 → 图谱页的左栏与顶栏像素**必然改变** → G-5「整页截图像素级一致」必然 FAIL | **图谱页必须走旧版外壳分支**（`graph_mode=True` 时不注入新导航/新顶栏），或——见 §6.5——**把 G-5 的比对范围收窄到图谱画布区域**并由所有者裁决 |
| **F-13** | `.muted` 新规则（任务 2.3） | `workbench.css`（新增） | 图谱页右栏 `<p id='ai-session-empty' class='muted'>还没有对话。</p>`（`pages.py:732`）与详情面板 `<p class='muted'>`（`pages.py:476`）当前**与正文同色**。新增 `.muted` 规则 → 右栏与详情面板文字变色 | 新 `.muted` 规则**排除图谱页**：`#layout:not([data-page="graph"]) .muted { … }`；或接受详情面板变化但右栏必须排除 |
| **F-14** | `--lk-ink` 改值 / 三栏描边改描边策略 | `workbench.css:7`、`:103`、`:167`、`:237` | 新基线「不用描边，靠圆角+柔影分层」（`decisions.md:610`）。若 `#topbar`/`#left-column`/`#ai-column` 的边框被改成柔影或圆角块 → 图谱页三栏分界形态改变 | 图谱页作用域钉回 `border: 1px solid var(--lk-ink)` / `border-bottom: 2px solid var(--lk-ink)`；新分层策略只施加于中栏内容 |
| **F-15** | 夜纸值集 `[data-theme="night"]` | 新增（任务 10.1） | 见 M-4：`html[data-theme="night"]` 特异性 `(0,1,1)` **高于** `:root`，且若它重定义 `--paper` / `--ink` / `--hair` / `--blue` / `--shadow`，**图谱画布与节点色在夜纸下全变**。任务 10.4 又要求「图谱页在两主题下均与基线一致」 | 夜纸块**不重定义这 12 个裸名**；图谱页用 `data-theme` 之外的机制排除夜纸（如 `html:not([data-theme="night"])` 的选择器不作用于图谱页，或图谱页不写 `data-theme`） |
| **F-16** | `#middle-page > .page-header { padding-right: 128px }` 删除（任务 11.2） | `workbench.css:255` | 该规则**对图谱页生效**（图谱页 `.page-header` 在 `#middle-page` 内，`pages.py:415-416`）→ 删掉后图谱页标题右边的 128px 空档消失，标题整体左移 | 保留该规则，或改成 `#layout:not([data-page="graph"]) #middle-page > .page-header` |
| **F-17** | 视口 / 滚动 / 布局重排引发的图谱尺寸漂移 | `workbench.css:160`（三栏几何）、`:253`（`max-width:800px`） | 图谱画布宽度 = 中栏宽度 → 三栏几何一变，画布与所有节点坐标基准都变 | 三栏几何**值不变**（`280px / 1fr / 420px`），只改写法；`.graph-content{max-width:none}`（`:509`）与 `.graph-workspace` 网格不变 |
| **F-18** | 静态资源缓存策略（`app.py:214-232`） | `app.py` `_send_static` | 该函数**不发 `Cache-Control`/`ETag`/`Last-Modified`**；若本次顺手加长缓存，改造后的 CSS 可能被旧缓存遮蔽 → 截图比的是旧样式，结论无效 | 本次**不加**长缓存；若必须加，`.css` 必须 `no-cache`；截图流程一律硬刷新 |
| **F-19** | 动效 token 收编（任务 4.1）误伤图谱时长 | `workbench.css:1680 :1714 :1718 :1810 :1771-1772` | 图谱有 5 处自己的时长（`.18s` / `.16s` / `.16s` / `.18s` / `1s`）。若批量把 `transition: … .18s` 改成 `var(--motion-fast)`，而 `--motion-fast` ≠ `180ms`，图谱交互手感与截图时序变 | 收编范围排除 `1497-1884`；或新 token 取值**恰好等于**原值（`--motion-fast:180ms` / `--motion-base:160ms`） |
| **F-20** | 图谱脚本加载路径与顺序 | `pages.py:100-102`、`middle-navigation.js:34-36` | 三脚本有严格顺序（core → renderer → physics）；`middle-navigation.js` 的 SPA 路径也会动态补载 | 保持不变 |

---

## 5. 隔离自检清单（实现者改完 token 后逐条跑）

### 5.1 静态断言（不启动服务，秒级）

```bash
cd "D:/Projects/Academic Workflow/lesson-kit"

# 1) 图谱专用区段一行未改：任何 hunk 不得覆盖 1497-1884
git diff -U0 -- workbench/server/static/workbench.css \
  | grep -E '^@@' \
  | grep -E '\+149[7-9]|\+1[5-8][0-9][0-9]|\+188[0-4]' && echo "FAIL: 图谱区段被改" || echo "OK"

# 2) 图谱 12 个裸名各只声明一次，且全部落在 1506-1517
grep -nE '^\s*--(paper|ink|hair|blue|blueSoft|yellow|yellowSoft|red|redSoft|green|graphite|shadow)\s*:' \
  workbench/server/static/workbench.css
# 期望：恰好 12 行，行号 ∈ [1506,1517]

# 3) 文件里 :root 只有 2 处，且第 2 处在图谱区段内、其后无新 :root
grep -n ':root' workbench/server/static/workbench.css
# 期望：1505 之后不再出现 :root（夜纸值集必须用 html[data-theme=...] 或作用域限定）

# 4) 夜纸块不得重定义图谱 12 个裸名
grep -nE 'data-theme[^{]*\{[^}]*--(paper|ink|hair|blue|blueSoft|yellow|yellowSoft|red|redSoft|green|graphite|shadow)\s*:' \
  workbench/server/static/workbench.css && echo "FAIL" || echo "OK"

# 5) 图谱自带 Georgia 栈仍是原来 5 处、行号不变
grep -n 'Georgia' workbench/server/static/workbench.css
# 期望：1688 / 1712 / 1742 / 1748 / 1823

# 6) 图谱 JS 一行未改
git diff --numstat -- \
  workbench/server/static/graph-physics-core.js \
  workbench/server/static/graph-physics.js \
  workbench/server/static/graph-physics-worker.js \
  workbench/server/static/graph-renderer.js
# 期望：0  0  （四行，全为 0）

# 7) 图谱区段外的图谱规则（509-513 / 536-595 / 1167-1171）未被收编/改写
git diff -U0 -- workbench/server/static/workbench.css | grep -E '^\+.*graph' && echo "REVIEW" || echo "OK"

# 8) 图谱区段外的硬编码 hex 收编没有误伤图谱
git diff -U0 -- workbench/server/static/workbench.css \
  | grep -E '^\+' | grep -E '#(456fc9|aaa399|c3a128|c75a52|bbb4a9|d9d3c8|eeeae1|fffdf8|d8d2c6|e0dbd0|22201d|d3a914)' \
  && echo "FAIL: 图谱硬编码色被收编" || echo "OK"

# 9) outline 清理没有碰 1572
git diff -U0 -- workbench/server/static/workbench.css | grep -E '^\-.*outline: *0' && echo "FAIL" || echo "OK"

# 10) 128px 死预留仍在（任务 11.2 删它会动图谱页标题）
grep -n 'padding-right: 128px' workbench/server/static/workbench.css
# 期望：255 行仍在，或已加 :not([data-page="graph"]) 限定
```

### 5.2 运行时断言（浏览器控制台，图谱页上执行）

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

// R-4 图谱搜索框的 outline: 0 未被改
console.assert(getComputedStyle(document.querySelector('.graph-topbar .search input'))
  .outlineStyle === 'none', 'graph search outline');

// R-5 图谱控件的硬编码圆角未被 token 化
console.assert(getComputedStyle(document.querySelector('.graph-topbar .icon-btn'))
  .borderTopLeftRadius === '4px', 'graph icon-btn radius');

// R-6 #middle-page 转场动画不得作用在图谱页
console.assert(getComputedStyle(document.getElementById('middle-page')).animationName === 'none',
  'middle-page animation on graph page');

// R-7 外壳 token 在图谱页作用域被钉回
const g = getComputedStyle(document.getElementById('layout'));
console.assert(g.getPropertyValue('--lk-paper').trim() === '#fffdf7', 'pinned --lk-paper');
console.assert(g.getPropertyValue('--dsw-radius-sm').trim() === '6px', 'pinned --dsw-radius-sm');

// R-8 画布尺寸随中栏而变（确认几何未被改）
console.assert(document.querySelector('#graph-canvas').clientWidth > 0, 'canvas width');
```

### 5.3 视觉断言（§6 的截图协议跑完后）

- [ ] G-5-A：图谱页**整页**截图，改造前 vs 改造后，`pixelmatch` 差异像素数 **= 0**（文字抗锯齿区可按 G-5 允许项标注掩膜）。
- [ ] G-5-B：图谱**画布区域**（`.graph-workspace` 的裁剪矩形）截图，差异像素数 **= 0**。
- [ ] G-5-C：图谱页在夜纸下与亮色下**同一份**图谱画布截图，差异像素数 **= 0**（任务 10.4）。
- [ ] G-5-D：三个状态（默认 / 选中节点 / 控制卡展开）各出一组，差异像素数均为 **= 0**。

---

## 6. 像素级比对方案

### 6.1 目标与难点

`acceptance.md:22` 的 G-5：「改造前后同一图谱页截图并排比 → 像素级一致（除浏览器字体渲染差异）」。

图谱页有**三处**天然不可比源，必须逐一冻结，否则「像素不一致」无法归因：

| # | 不可比源 | 证据 | 冻结手段 |
|---|---|---|---|
| N-1 | **环境色 canvas 是时间驱动的无限动画** | `workbench.js:1634` `graphTideDraw(graphTideState.reduced ? 0 : now/1000)`；`:1635` 非 reduced 无限 `requestAnimationFrame` | **开 `prefers-reduced-motion: reduce`** → `:1639` `reduced=true` → `:1634` 固定 `t=0`、`:1635` 不再排帧、`:1624` boost 不衰减 → 一次性确定性绘制 |
| N-2 | **物理布局由 Worker 迭代收敛** | `graph-physics-worker.js:89-95` 每条消息最多 `8` 步；`graph-physics-core.js:1246-1260` alpha 衰减到 0 才 `settled` | 等到 `sim.graph.settled === true`（`workbench.js:1440` `solving = sim.graph.alpha > 0` 变 false）**且** `#graph-solver-state` 不再带 `.solving` 类（`workbench.css:1771`） |
| N-3 | **布局被 `localStorage` 缓存，二次访问走另一条渲染路径** | `graph-physics.js:69-86` `writeLayoutSeed()`；`:344-368` 二次访问「采纳缓存、不再重解」 | **两次截图都用全新浏览器上下文**（清 `lk_graph_layout_v1_<workspace>`），强制两次都走「从零求解」同一条路径 |

> N-3 容易被忽略：`graph-physics.js:358` 判定「所有节点都有座位」时走**采纳缓存**分支，
> 该分支不跑求解器，最终坐标与「从零求解」的收敛点**可能相差 0.1px**（`:75` 存储时四舍五入到 0.1）。
> 混用两条路径 → 节点位置差 0.1px → 整图非零差异，但与 CSS 无关。

### 6.2 环境固定

| 项 | 取值 | 理由 |
|---|---|---|
| 浏览器 | 同一台机器、同一浏览器**同一版本**、同一份 profile 策略 | G-5 允许「除浏览器字体渲染差异」；跨机器字体渲染必然不同 |
| 视口 | **1440 × 900**（与 `acceptance.md` §1 的 1440 档一致），`deviceScaleFactor = 1` | `graph-renderer.js:189` dpr 夹在 1..2；`workbench.js:1504` tide dpr `min(2, dpr)` → dpr 必须两次一致，否则 WebGL backing store 与 tide canvas 分辨率不同 |
| 浏览器缩放 | 100%，不叠加操作系统缩放 | 同上 |
| WebGL | headless Chromium 用固定 flag：`--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`（或两次都用同一块真 GPU） | `graph-renderer.js:169-175` 强制 WebGL2，无 WebGL2 直接抛错；软件光栅化是确定性的，但与真 GPU 结果不同 → **两次必须同一种** |
| 动画 | `prefers-reduced-motion: reduce`（Playwright `contextOptions.reducedMotion: 'reduce'`） | N-1；同时触发 `workbench.css:1126-1131` 全局降级与 `:1863-1867` 图谱降级 |
| 字体 | 不装新字体；`font-display: swap` 的字体在截图前等 `document.fonts.ready` | 新阅读面字体（任务 3.1）若被图谱继承，fallback 与 swap 会产生两种渲染 → 必须等 `document.fonts.ready` |
| 数据 | **池数据库副本** + 隔离注册表 + 独立端口；两次用**同一份**副本快照 | `acceptance.md:150-152` |
| 工作区 | 同一工作区名（影响 `localStorage` key 与 `identity`） | `graph-physics.js:47` |
| 缓存 | 每次导航前 `context.clearCookies()` + 关缓存；或 URL 加 `?v=<timestamp>` 查询串 | `app.py:214-232` 不发 `Cache-Control`/`ETag` → 浏览器启发式缓存可能遮蔽新 CSS（F-18） |

### 6.3 截图时刻的固定流程（每次截图都必须走完这 6 步）

```
1. goto /w/<workspace>/graph  （全新 context）
2. await document.fonts.ready
3. await page.waitForFunction(() => {
     const s = document.querySelector('#graph-solver-state');
     return s && !s.classList.contains('solving')
        && document.querySelector('#graph-solver-text').textContent.trim() === '已收敛';
   })                                  // N-2：物理收敛
4. await page.evaluate(() => window.scrollTo(0, 0))   // 滚动归零
5. await page.screenshot({ animations: 'disabled', caret: 'hide' })
                                       // 冻结 CSS 动画/过渡到终态；隐藏光标
6. 记录截图时的 sim.graph.settled / alpha，供复现
```

补充：

- `animations: 'disabled'` 会把 CSS 动画与过渡**定格在终态**，正好覆盖 F-6（`#middle-page` 转场）与 F-9（全局 transition）。
- 若用桌面级截屏（而非页面级 API），**必须先移开鼠标指针**，否则光标会被烧进像素。
- `#middle` 在图谱页是 `overflow: hidden`（`workbench.css:510`、`:1523`），中栏不滚动；**但文档本身仍可能滚动** → 第 4 步不可省。
- 画布本身有 `transform` 缩放/平移（`workbench.js` 的 `graphApplyView` / `graphView.panX/panY/scale`）。**必须用默认视图**：不滚轮、不拖拽、不点节点，停在 `pages.py:415-429` 的默认状态（视图 = structure，筛选 = 全部，重力 = 85，看板收起，控制卡收起）。

### 6.4 比对

```bash
# 改造前 / 改造后 同名同尺寸
npx pixelmatch before.png after.png diff.png          # 或用 ImageMagick
magick compare -metric AE before.png after.png null:   # 绝对错误像素数
magick compare -metric RMSE before.png after.png null: # 均方根误差
```

判定：

| 指标 | 通过标准 |
|---|---|
| AE（差异像素数） | **0**（整页，G-5-A）；若仅文字抗锯齿处有差，按 G-5「浏览器字体渲染差异」允许项标注掩膜后仍应为 0 |
| 画布区域 AE（G-5-B） | **0**，且**不接受任何掩膜**——画布内无浏览器字体渲染差异的辩解空间（节点数字用 Georgia，但同机同版浏览器下渲染确定） |
| 尺寸 | 两图 width/height 完全相同 |

### 6.5 比对范围的三种口径（**需所有者裁决**）

`acceptance.md:22` 的 G-5 写的是「图谱页截图并排比」，未指定裁剪范围。三种口径的结论会不同：

| 口径 | 比对区域 | 能否达成 | 说明 |
|---|---|---|---|
| **R-1 整页** | 1440×900 整屏 | **当前无法达成** | 任务 11.3–11.5（左栏导航加图标、选中态改圆角色块）与 12.1（顶栏三段式）**改的是 DOM 结构**，无法用 CSS 作用域排除 → 图谱页左栏与顶栏必然变（F-12） |
| **R-2 画布区域** | `.graph-workspace` 的裁剪矩形 | **可以达成** | 图谱自身 + 中栏容器。这是 F-1…F-11、F-13…F-20 全部守住后的必然结果 |
| **R-3 画布 + 顶栏/左栏/右栏背景色采样** | 画布矩形 + 三栏各取 1 个纯色像素 | **可以达成** | 在 R-2 之上额外证明外壳底色/描边未变（F-3/F-7/F-8/F-14） |

> **建议（供裁决）**：G-5 判为 **R-2 + R-3**；R-1 整页比对改为「**除左栏与顶栏外**像素级一致」，
> 并把「左栏/顶栏在图谱页上是否跟随全站改造」作为**独立议题**登记到契约文件——
> 目前 `proposal.md`、`tasks.md`、`acceptance.md` 三者对这一点的表述互相冲突
> （`proposal.md:103-105` 说图谱「appearance stay exactly as they are」，
> `tasks.md:11` 说「图谱样式未动」，
> `tasks.md:97` 说「图谱页在两主题下均与基线一致」，
> 而 `tasks.md:103-104` 又要求左栏/顶栏全站改造）。
> 按 `AGENTS.md`「契约冲突处理」，此处**保持冲突显式**并提请裁决，不在本文件内自行选边。

### 6.6 状态矩阵（每个状态各一组前后对照）

| 状态 | 触发 | 覆盖到的 CSS |
|---|---|---|
| **S-G1 默认** | 直接进入 `/w/<ws>/graph`，不交互 | `:1520-1884` 全部；`pages.py:430` 看板收起、`:432` 控制卡收起 |
| **S-G2 选中节点** | 点击一个节点 | 详情面板 `:1815-1859` + `:536-595` + 节点选中态 `:1702-1708` |
| **S-G3 控制卡展开** | 点击 `#graph-controls-toggle` | `:1721-1776`（chip / 滑杆 / 求解行 / 距离刻度） |
| **S-G4 图例切换** | 点击某个 `.legend-item` | `:1778-1799` + `workbench.js` 的边可见性逻辑 |
| **S-G5 夜纸** | 主题切到夜纸（若图谱页参与主题） | `html[data-theme="night"]` 对图谱的影响（F-15） |

> S-G5 若采用 R-2 口径，需先确认夜纸是否作用于图谱页；任务 10.4 写的是「不随主题变化」，
> 与任务 10.1 的全局夜纸值集存在张力（F-15）。

---

## 7. 待核事项（不臆断，按「待核」登记）

| # | 事项 | 查证方式 |
|---|---|---|
| Q-1 | G-5 的比对范围是整页还是画布区域 | 所有者裁决（§6.5）。影响任务 11/12 是否需要为图谱页留旧外壳分支 |
| Q-2 | 图谱页是否参与夜纸主题 | 所有者裁决。影响 F-15 与 S-G5 是否成立 |
| Q-3 | 任务 11.2 删除 `#middle-page > .page-header { padding-right: 128px }`（`workbench.css:255`）后，图谱页标题的左移量 | 在改造分支上实测 `.page-header` 的 `getBoundingClientRect()` 差值；非零即 FAIL（F-16） |
| Q-4 | 任务 2.1 的 29 个 hex 里，有多少落在 `workbench.css:1497-1884` 内 | **已实测**：`sed -n '1497,1884p' workbench.css \| grep -cE '#[0-9a-fA-F]{3,6}'` → **83**。图谱区段内的硬编码 hex 命中数远多于任务 2.1 列出的 29 个，收编时必然误伤 → F-11（收编必须排除 `1497-1884`） |
| Q-5 | `agent-ui.css` 在图谱页右栏的可见元素中，有多少实际渲染（空态 / 有会话） | 两个状态各截一张：G-5 需覆盖「空对话列表」与「有对话列表」两种右栏状态 |

---

## 8. 结论

1. 图谱页**不是**一块自足的样式：它由 `pages.py:410-481` 的 HTML、`workbench.css:1497-1884`
   的 388 行专用样式、**外加区段外的 25 行图谱规则**（`:509-513`、`:536-595`、`:1167-1171`）、
   4 个 JS 模块、4 个 API 端点共同构成；图谱区段内另有 **83 处**硬编码 hex
   （`sed -n '1497,1884p' \| grep -cE '#[0-9a-fA-F]{3,6}'` 实测），远超任务 2.1 的收编清单。
2. 图谱专用 `:root`（`:1505-1518`）的 12 个变量与全局层**命名空间不相交**，
   今天**并不存在「覆盖」**；它之所以安全，靠的是「同特异性 + 后写者赢」这条**顺序**。
   真正的风险是**新层反向定义同名裸名**（`--ink` 已在任务 1.2 中出现），
   以及**夜纸用 `html[data-theme=…]` 以更高特异性压过 `:root`**。
3. 图谱**自身**对全局 token 的依赖很浅（几乎只用自己那 12 个变量）；
   图谱**外壳**（顶栏 / 左栏 / 右栏 / 页面底色 / 字体栈 / 圆角）却深度依赖全局层——
   **G-5 的整页像素一致，本质上要求外壳为图谱页重新钉回原值。**
4. 本文件给出 **20 条禁止改动项（F-1…F-20）**、**10 条静态断言 + 8 条运行时断言 +
   4 条视觉断言**、以及一套**含 5 个状态、3 种比对口径**的像素级比对方案。
5. 存在 **5 项待核（Q-1…Q-5）**，其中 Q-1（G-5 比对范围）与 Q-2（夜纸是否波及图谱页）
   是**契约冲突**，按 `AGENTS.md` 要求保持显式，需所有者裁决后再推进任务 11 / 12 / 10。
