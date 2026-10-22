# Tasks — graph-node-visual-language

> **范围依据**：`proposal.md`（范围与冻结）、`design.md` **D-1…D-14**（十四条决策，任务逐条对应）。
> **视觉语言依据**：`../workbench-visual-language-v2/decisions.md` 的「图谱节点重设计」
> 第 1–5 组（**G-1…G-24**）、**A-7 / A-8**（夜纸归本变更）、**A-10**（半径收窄 + 归档顺序）、
> **A-12**（自带门禁）、**A-14**（比对范围与可复现前提）、**A-15**（标签字号 12px）、
> **A-16**（图谱纸面 token 名）。
> **现状证据**：`tmp/frontend-audit/GRAPH-NODE-PIPELINE.md`（1114 行 / 180+ 处 `文件:行号`）。
> **行为契约依据**：`specs/graph-visual-language/spec.md`（新能力，7 需求 / 24 场景）、
> `specs/workbench-ui/spec.md`（delta，6 条 MODIFIED）。
> **验收口径依据**：`acceptance.md`（§0 底线守卫 G-1…G-5、§0.2 结构不变量 **SI-1…SI-5**、
> §0.3 允许变化区 **AV-1…AV-4**、§1 对照截图 S-L1…S-L8 / S-N1…S-N6、
> §2 关键帧 M-1…M-6、§3 交互清单、§4 通过标准、§5 走查协议、§6 状态矩阵）。
>
> **实施口径**：
> - **先修缩放补偿，再落视觉语言**（D-3 明确、G-24 派生）——第 1 组是所有视觉任务的前置，
>   不得与其它组并行或提前；否则新配色会画在 3px 的圆上看不出来。
> - **不新增任何学习事实、不新增任何持久字段、不改 API 请求序列与载荷**；`pool/` `pipeline/`
>   `workbench/data/` 一行不动。
> - **只改节点外观**（形态 / 尺寸 / 配色 / 标签）；布局物理、关系线的线型/粗细/亮色取值、
>   交互、投影语义一律不动（D-13 逐项复核见第 13 组）。
> - **无框架、无构建步骤、无 npm、无 CDN、无外部图标字体**；纯 CSS + 原生 JS + 内联 SVG。
> - **不碰** `openspec/changes/workbench-visual-language-v2/` 下的任何文件（第 12 组只做
>   「合入后 re-base」的动作，不提前改动 v2）。
>
> **两处已知的上游裁决覆盖**（以 v2 `decisions.md` 的 A-15 / A-16 为准，本文件已按其取值）：
> ① **标签字号 12 屏幕 px**（A-15 裁决，`design.md` D-1/D-6 的 11px 作废）——
>   依据 proposal.md:68 与 A-15「以 proposal 为准」；
> ② **图谱纸面 token 的夜纸取值**（本变更 D-12.1 取 `#1c1a16`）与 v2 A-16 的
>   「图谱纸面恒为 `#fffdf7`、不参与夜纸换值」**存在张力** —— A-16 那条是 v2 不碰图谱
>   （A-8）语境下的性质，夜纸适配已整体划归本变更；**该冲突按 AGENTS.md 的
>   contract drift 显式登记**，落地时在第 10 组任务里定稿并同步登记。
>
> **每组末尾的「阶段验收」任务统一要求跑 AGENTS.md 的四条验证命令**：
> `python -m pytest tests -q`、`python -m compileall -q lessonkit.py workbench pipeline pool tests`、
> `openspec validate --specs --strict`、`python lessonkit.py guard extract-problems --course dmath --chapter ch06`；
> 并按 `acceptance.md` 指向对应小节。截图走查一律在**池数据库副本 + 隔离注册表 +
> 独立端口**上点检，**永不写真实池**（`acceptance.md` §5）。
>
> **design.md 的 Open Questions**（4 条：底噪预渲染倍率、标签让位权重、量值分档阈值、
> 夜纸底噪透明度）全部是**实现参数**，不改变规格 / 方案 / 任务拆分，按 `design.md`
> 「Open Questions」的自我声明就地定稿即可，**不需要先问所有者**。

---

## 1. 屏幕空间缩放补偿（最高优先级，D-1 / G-24）

- [ ] 1.1 在 `workbench/server/static/workbench.js` 的 `graphApplyView()`（`:1104-1107`）里，把当前相机缩放**在写 `transform` 的同一次调用中**写到 `.graph-stage` 上：`--stage-scale`（= `graphView.scale`）与 `--inv-scale`（= `1 / scale`）。**一次相机变化 = 一次变量写入**；不引入任何新状态对象、不做逐节点的 JS 计算。验证：`graphApplyView()` 只多出两条 `style.setProperty`；`--inv-scale` 在 CSS 中**只有一处定义**（其余全是消费点）。
- [ ] 1.2 在 `workbench/server/static/graph-physics.js` 的 runtime 门面（`runtime = {...}`，`:254-300`）新增 `nodeScreenRadius(node)`：返回**屏幕像素**的绘制半径 = `14 + 16·√score`，`score` 取自 `runtime.scoreFor(node)`（实现在 `graph-physics-core.js:1463-1470`）。这是**全仓唯一的半径公式来源**（画节点与修 WebGL 端点共用，见第 5 组 5.3）。验证：`grep -n "14 + 16" workbench/server/static/*.js` 命中 1 处；`nodeScreenRadius()` 对同一 `node` 在同一投影下返回值稳定（相等量值 ⇒ 相等半径）。
- [ ] 1.3 在 `workbench/server/static/workbench.js` 的 `graphPaintNodes()`（`:1296-1325`）里，每帧为每个节点往 `elements.wrap`（`.node-wrap`）写两个 CSS 变量：`--node-d`（**屏幕 px** 的绘制直径，形如 `44px`）与 `--node-box`（舞台 px 的盒子尺寸 = `calc(var(--node-d) * var(--inv-scale))`，写成字符串交给 CSS 求值）。**不写数值缩放**（不在 JS 里算除法），避免两处漂移。验证：`getComputedStyle(wrap).getPropertyValue('--node-d')` 返回带 `px` 的屏幕直径；860×460 画布 Fit 后该值落在 28–60px。
- [ ] 1.4 在 `workbench/server/static/workbench.css` 的 `.node`（`:1659-1663`）把 `width/height: var(--size)` 改为 `var(--node-box)`，保留 `background: transparent` / `border: 0` / `padding: 0` / `overflow: visible` / `cursor: grab`。**命中区 = 绘制直径**（视觉与手感一致）。验证：`elementFromPoint` 在圆盘可见外缘 ±2px 处命中该节点；`--size` 在图谱节点样式里 0 引用。
- [ ] 1.5 在 `workbench/server/static/workbench.css` 新增 `.node-core` 与 `.node-ring` 两层的**几何骨架**（配色在第 3 组落实）：两层均 `position: absolute; inset: 0; border-radius: 50%; box-sizing: border-box`；`.node-ring` 用 `border-width: var(--ring-w)`；`.node-core` 用 `inset: var(--ring-w)`（内核半径 = 盒子半径 − 环宽）。两层的盒尺寸随 `.node` 走，**不再有独立的世界像素尺寸**。验证：`.node-core` 的 computed `width` = `.node` 盒宽 − 2×环宽；`.node-ring` 的外缘 = `.node` 盒外缘。
- [ ] 1.6 在 `workbench/server/static/workbench.css` 把排版单位屏幕化：`.label`（`:1710-1715`）的 `font-size: 12px` → `calc(12px * var(--inv-scale))`、`max-width: 168px` → `calc(168px * var(--inv-scale))`（A-15：12 屏幕 px）；`.node-value`（`:1686-1691`）的 `clamp(11px, calc(var(--size) * .28), 18px)` → `calc(clamp(12px, calc(var(--node-d) * .34), 18px) * var(--inv-scale))`。验证：取 `getComputedStyle(label).fontSize` **× 当前 scale** ≈ **12 屏幕 px**、`.node-value` 的**视觉**字号落在 12–18 屏幕 px；860×460 画布 Fit 后圆心数字不小于 12px。
- [ ] 1.7 节点与标签的间距屏幕化：`.node-wrap`（`workbench.css:1643-1647`）的 `gap: 8px` → `calc(8px * var(--inv-scale))`。验证：视觉间距 = 8 屏幕 px（computed gap × scale ≈ 8px）。
- [ ] 1.8 登记 `Screen-space sizing` 的「small-dot diameter 按屏幕像素」一条为**空实现**：`graph-visual-language` 的该条在本实现下**无对象**（节点上不再有任何点状标记，见第 8 组 8.4）；在 `specs/graph-visual-language/spec.md` 或 `design.md` 的 D-1 段**显式登记**，不得把它当成「已补偿」上报。验证：第 8 组完成后 `grep -c "node-satellite" workbench.css workbench.js` = 0，且 delta 里有一条明示。
- [ ] 1.9 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §1 **S-L2**（缩放补偿前后对照）与 §3.5（可读性与对比度）走查 —— 860×460 画布下**节点直径落在 28–60px、标签视觉字号 12px、可见标签 0–1/31 的现状被彻底消除**；对照 `tmp/frontend-audit/GRAPH-NODE-PIPELINE.md` §7.3 的现状表逐行核对。

## 2. 同心圆结构与尺寸映射（D-2 / D-3 / G-1 / G-13 / G-17 / A-10.1）

- [ ] 2.1 在 `workbench/server/static/graph-physics-core.js` 的 `sizeFor(score)`（`:60-61`）把世界直径从 `20 + 60·√score`（20–80）改为 `28 + 32·√score`（**28–60**，= 2 × 屏幕半径 14–30）。**只改量程**：`√` 映射保持不变（`:48-59` 的注释解释了保留开方的原因），力模型、吸引强度、footprint、碰撞、端口间隙、Worker 求解流程**全部照旧**。验证：dmath/ch06 的节点尺寸全部落在 28–60；**同一 score 序列的相对大小顺序与改造前完全一致**（只缩放不改排序）。
- [ ] 2.2 把尺寸映射收敛成**单一来源**：`graph-physics-core.js` 的 `sizeFor()` 与 `graph-physics.js` 的 `nodeScreenRadius()`（1.2）引用**同一个量程常量**（下限 14、跨度 16 世界 px），不得各写一份魔数。验证：`grep -nE "14 \+ 16|28 \+ 32" workbench/server/static/*.js` 的**定义点**只有 1 处。
- [ ] 2.3 在 `workbench/server/static/workbench.js` 的 `graphCreateNodes()`（`:957-1053`）把节点子层从「五层叠一个圆」改为「内核 + 外环 + 一个数字」：新增 `.node-core`（`:979` 的 `.node-face` 改造而来）与 `.node-ring`（新元素，`border-radius:50%` + `border`），保留 `.node-value`（`:981`），**删除** `.metric-track`（`:975`）与 `.status-ring`（`:977`）的 DOM 创建。绘制层级：内核 → 数字 → 外环（外环最后画，保证边界线不被内核压住）。对应 CSS 规则的删除归第 8 组。验证：`graphCreateNodes()` 产出的节点 DOM 只含 `.node-core` / `.node-ring` / `.node-value` 三件 + 外层 `.label`；`grep -c "metric-track\|status-ring" workbench.js` = 0。
- [ ] 2.4 在 `workbench/server/static/workbench.js` 的 `graphProjectionDisplay()`（`:1055-1061`）把圆心数字改为**恒为该节点的正式题数**（`node.problems`）：删掉 `structure` 的度数分支、`importance` 的 `Math.round(node.importance*100)` 分支与 `"%"` 单位、`state` 的 `STATE_SHORT` 单字分支。**四个投影返回同一个数**。依据 G-9 与 `review-workbench` 的 `Semantic graph attraction`（`node.problems` 已是正式题数）。验证：四个投影下同一节点的圆心数字**逐字相同**；值等于 `node.problems`；`STATE_SHORT`（`:578`）在图谱区段 0 引用。
- [ ] 2.5 在 `workbench/server/static/workbench.js` 的 `graphUpdateNodeAppearance()`（`:1063-1075`）写外环粗细 `--ring-w` = `calc((1.5 + 2.5·score) * 1px * var(--inv-scale))`（**1.5–4 屏幕 px**，与半径**同源**同一个 `scoreFor()`），并**删除** `--metric-angle` 写入（`:1067`）。验证：`grep -c "metric-angle" workbench.js` = 0；同一投影下环宽随 score **单调**；`design.md` D-3 的「一条量值三条通道（半径 / 环宽 / 颜色）」成立。
- [ ] 2.6 在 `workbench/server/static/workbench.css` 落实「内核淡、外环深」（G-13）：`.node-core` = 同色相**淡**填充（色相混纸 20%，色值见第 3 组），`.node-ring` = 同色相**实**色描边。**外环半径 = 盒子外缘**（`inset: 0` + `box-sizing: border-box`），**内核半径 = 盒子半径 − 环宽**。验证：节点读作「一枚带边的圆片」；内核与纸面对比 ≥1.3:1（D-4 的填充门槛，实测 1.42 / 1.45）；外环对纸面 ≥3:1。
- [ ] 2.7 保证圆心数字**压在所有圆盘之上**且不溢出外环内缘：`.node-value` 的 `z-index` 高于 `.node-ring`；字号按 `clamp(12px, .34·D, 18px)` 屏幕 px ⇒ 直径 28px 时数字 ≤ 9.5px、留出环宽余量。验证：在 1440×900 与 860×460 两个视口下，节点中心的数字完整可读、不被环切断。
- [ ] 2.8 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.3 **AV-1** 判据①②③④⑤逐条走查（节点数量与 id 不变、位置不变、圆心数字 = 正式题数且四投影相同、节点上无任何状态文字、量值→尺寸映射单调且区间落在 14–30 屏幕 px）；并核对 §1 **S-L1** 的「内核 + 外环两同心圆、圆心一个题数」。

## 3. 图谱暖色板与四投影色键（D-4 / D-5 / G-7 / G-8 / G-11…G-14 / G-16 / G-20…G-22）

- [ ] 3.1 在 `workbench/server/static/workbench.css` 的图谱 token 块新增**状态四色**（G-21 / D-4）：`--graph-state-new: #8a8377`（对比 3.69）/ `--graph-state-review: #b08a12`（3.18）/ `--graph-state-mastered: #d4702f`（3.35）/ `--graph-state-work: #b03a2a`（5.92）。全暖色相，**不占用蓝**（G-16）。验证：四个值与 `design.md` D-4 的表逐字相同；图谱区段内 `#2457c5`（旧 `--blue`）0 引用。
- [ ] 3.2 同处新增**量值橙阶**（G-20 / D-12）：`--graph-scale-1: #d4702f`（3.35）/ `--graph-scale-2: #c0601f`（4.18）/ `--graph-scale-3: #a3461f`（5.98）/ `--graph-scale-4: #7d2f12`（9.03）。方向规则只有一条：**值越大，与纸面的对比越强**。验证：与 D-4 表逐字相同；四个值构成同一色相的明度阶（可被判定为「单色阶」）。
- [ ] 3.3 同处新增**墨阶三档**（G-22）：`--graph-ink-ring: #2f2b24`（对纸 13.84）/ `--graph-ink-value: #6f6759`（5.49）/ `--graph-ink-core: #ded6c6`（1.42，非边界，≥1.3:1 即可）。验证：与 D-4 表逐字相同；关系结构投影下节点色**不承载语义**。
- [ ] 3.4 同处新增**文字与内核色**：`--graph-label: #5c5549`（对纸 7.24，≥4.5:1）/ `--graph-value-ink: #2f2b24`（对内核 9.75–11.28，≥4.5:1）。验证：与 D-4 表逐字相同；两处对比度均达标。
- [ ] 3.5 **关系线在亮色主题下逐字节不变**（D-12.2）：`workbench/server/static/graph-renderer.js` 的 `EDGE_COLORS`（`:15-21`）**一行不动**（先修 `#456fc9` / 应用 `#c3a128` / 对比 `#c75a52` / 相关 `#757068` / 隐含 `#bbb4a9`）；`graph-physics-core.js` 的 `edgeStyle()`（`:1326-1329`）的线宽与透明度**一行不动**。验证：`git diff` 显示这两处**零改动**（图例的错另在第 8 组 8.2 修，图例不是线）。
- [ ] 3.6 在 `workbench/server/static/workbench.js` 的 `graphUpdateNodeAppearance()`（`:1063-1075`）按当前投影给节点写色键（**一个变量，两个同心圆共用同一色相**）：`structure` → 墨阶外环色；`problem_count` / `importance` → 橙阶 4 档（按 `score`）；`state` → 状态四色（按 `node.state`）。**不写学习记录、不改状态、不改成员**。验证：四个投影各截一张，节点外环颜色与 `design.md` D-5 的表逐项对应；切换投影**不发任何请求**。
- [ ] 3.7 校验量值分档阈值（D-5 的〔待核〕）：用 `tmp/frontend-audit/GRAPH-NODE-PIPELINE.md` §12 的复算方法，在 dmath/ch06 的**真实 score 分布**上确认 `.25 / .5 / .75` 四档**不空置**；若某档空置，改用分位数分档（**不改「单色阶」这一规格**）。验证：复算表里四档各有节点数；分档边界写成常量而非散落的字面量。
- [ ] 3.8 落实「内核淡、外环深」的实际取色：`.node-core` 的 `background: color-mix(in srgb, var(--node-ring-color) 20%, var(--graph-paper))`、`.node-ring` 的 `border-color: var(--node-ring-color)`；两个同心圆**同色相两档**（G-8 / G-13）。验证：computed `background` 与手工 `color-mix` 结果逐字相同；节点读作「一枚带边的圆片」而不是两个色。
- [ ] 3.9 把图例改为**两块**（G-14 / D-5）：在 `workbench/server/pages.py` 的 `graph_page()`（`:410-481`）把现有 `.legend`（`:462-467`，5 个关系类型）改为「上半 = 关系线型（**保留现状**的可点按显示/隐藏行为与 `data-edge-type` / `aria-pressed`）+ 下半 = 节点颜色键」的两块结构；下半块的 4 套内容（`structure` / `problem_count` / `importance` / `state`）**一次渲染全**，每套带 `data-legend-for="…"`。**颜色值只在 CSS 里定义一处**，模板只给结构 ⇒ 不会两处漂移。验证：图例 DOM 存在 4 套 `data-legend-for`；关系线型的 5 项与改造前逐字一致。
- [ ] 3.10 在 `workbench/server/static/workbench.js` 的 `graphApplyView()`（`:1104-1107`）按当前投影切换图例下半块的可见套（与顶栏 Tab 的 `data-view` 同源）；`structure` 投影显示**节点结构键**（一枚样例节点 + 外环 / 内核 / 数字三件的说明），**不是**色阶列表（G-22：颜色不承载语义）。**图例只解释颜色，不引入任何学习状态 / 指标 / 筛选控件**。验证：切四个投影，图例下半块随之切换；`grep -c "graph-legend" workbench.js` 的切换逻辑只改 `hidden` / `display`，不写学习数据。
- [ ] 3.11 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.3 **AV-3** 判据①②③④走查（两块都在、下半与当前投影严格对应、上半关系线型保留现状、图例「相关」色与 WebGL 实况一致 —— ④ 由第 8 组 8.2 收口）与 §3.3（投影切换）逐条走查；并核对 §1 **S-L5**（四投影各一张）与 §1 **S-N4**（夜纸四投影各一张）。

## 4. 标签系统与重叠让位（D-6 / G-5 / G-6 / G-23 / A-10.3）

- [ ] 4.1 在 `workbench/server/static/workbench.js` 删掉**缩放阈值**隐藏规则：`LABEL_MIN_RADIUS_PX`（`:1290`）与 `labelScaleThreshold()`（`:1292-1294`）整体删除；`graphPaintNodes()`（`:1319-1321`）的 `labelVisible` 判定改为「**默认可见**（除被屏幕空间去冲突 pass 隐藏）」。〔实证〕该规则在 Fit 后（s = 0.17–0.49）让 30/31 个节点没有标签。验证：`grep -c "LABEL_MIN_RADIUS_PX\|labelScaleThreshold" workbench.js` = 0。
- [ ] 4.2 在 `workbench/server/static/workbench.css` 落实标签「常态可见但不抢眼」（G-5）：`.label`（`:1710-1715`）的颜色从 `#2b2925`（≈15:1）降到 `var(--graph-label)`（7.24:1）；纸色描边光晕从 `0 0 6px` 降到 `0 0 3px`（缩到 4px 时不再糊成一团）；字重与行高不变。验证：实测对比度 ≥4.5:1（夜纸下同样达标）**且低于**节点自身填充的对比度（不抢节点）。
- [ ] 4.3 落实「**不截断**」（A-10.3 取 G-5 的这一支）：`.label` **不加** `text-overflow: ellipsis`、**不加** `-webkit-line-clamp`、**不设**行数上限；`max-width` 保持 `calc(168px * var(--inv-scale))`，文字**换行显示全文**。验证：一条含标点的长标题在 DOM 里完整换行显示；图谱区段 `grep -c "line-clamp\|text-overflow" workbench.css` = 0。
- [ ] 4.4 新增**屏幕空间去冲突 pass**（G-23 / D-6）：在 `workbench/server/static/workbench.js` 实现 `graphResolveLabelCollisions()`，触发时机为**相机变化（缩放/平移）、布局收敛、投影切换、选中变化**——**不是每帧**；**一次批量读**全部标签的 `getBoundingClientRect()`（一次读全部，禁止逐个读触发强制回流），按「**半径降序 → 重要度降序 → 节点 id 升序**」排序，标签矩形相交时**排位靠后者隐藏**（`opacity: 0` + `aria-hidden="true"`）。验证：触发时机只有那 4 类；排序键可在代码里逐条指认；隐藏项同时带 `aria-hidden`。
- [ ] 4.5 落实**可见标签预算**（D-6）：预算 = `floor(画布面积 / 9000)`（一个标签块 ≈ 66×30 屏幕 px，留一倍呼吸空间；860×460 ⇒ **43**）。**即使不重叠**，同时绘制的标签也有上限；超预算时按同一排序保留前 N 个。验证：dmath/ch06 的 31 个节点不触顶；构造 120 节点场景时标签数被预算截住。
- [ ] 4.6 落实**永不隐藏**清单（与既有契约 `workbench-ui:248`「selected, hovered, and high-focus labels SHALL remain visible」一致）：选中节点、悬停节点、其 **1 跳邻居**的标签永不隐藏；**被隐藏的标签在悬停 / 选中该节点时立刻恢复**（`opacity` 回到 1）。验证：选中一个标签被隐藏的节点，标签立即出现。
- [ ] 4.7 落实「**标签让位于节点**」与「**超出画布也算一次冲突**」（D-6 的代价段〔推断〕+ D-11.2 的代价）：去冲突 pass 同时判定「标签矩形 ∩ 邻点圆盘」——命中且该邻点未被隐藏时**先藏标签**；标签矩形超出画布边界时**先藏**。验证：截图里没有标签压在别人的圆盘上；Fit 后贴边的标签被正确让位，画布不出现半截标签。
- [ ] 4.8 保证**完整标题**仍可达（G-5 / A-10.3）：`label.title = node.title`（`workbench.js:996`）与 `button.title = node.title`（`:997`）**保留**；被隐藏标签的完整标题由**悬浮**与**键盘聚焦**取到（键盘聚焦时该节点标签恢复显示）。验证：Tab 到一个标签被隐藏的节点，标签恢复且完整标题可见于 `title` 属性。
- [ ] 4.9 落实「**节点上不出现任何状态文字**」（G-6）：`graphProjectionDisplay()`（`:1055-1061`）不再返回状态单字（见 2.4）；`workbench.js:1060` 的状态投影写入路径整体删除；状态名**只**保留在**学习看板**（`pages.py:474-477`）、`button.title` / `label.title`（悬浮）与**无障碍名**（`aria-label`，`workbench.js:973`）里，**不渲染成可见文字**。验证：节点上肉眼看不到「新 / 练 / 复 / 熟」任何一个字；看板与无障碍名里状态名仍在。
- [ ] 4.10 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.3 **AV-2** 判据①—⑤走查（默认可见、判据改为重叠让位 / 预算、不截断、屏幕像素字号、对比度低于节点填充但可读、隐藏的必须是**次要**标签）+ §3.1 / §3.2（键盘可达、悬浮）+ §1 **S-L7**（标签重叠）逐条核对。

## 5. 关系线端点接外环（D-7 / G-18）

- [ ] 5.1 在 `workbench/server/static/graph-physics-core.js` 标注并处理 `NODE_FACE_INSET = .07`（`:1343`）与 `endpointRadius(node)`（`:1345-1347`）：该常量与已删除的 `.node-face` 的 `inset: 7%` **是一对 coupled 的**（注释明说「If the face's inset ever changes, this constant has to change with it」）⇒ **不得**继续用它算新形态的端点。**端点计算不在物理核心做**（Worker 不知道缩放；把缩放推进核心会让缩放 reheat 求解器，违反 `workbench.js:1107-1108` 的「Camera movement never reheats the solver」）。验证：`grep -n "NODE_FACE_INSET" workbench/server/static/*.js` 只剩注释或已删除。
- [ ] 5.2 在 `workbench/server/static/graph-renderer.js` 的 `draw()`（`:242-300`，采样点循环 `:283-300`）实现端点回退：按**采样点**从两端向节点中心回退，直到与节点中心的距离 ≥ **新的端点半径**（= 外环外缘的世界半径 = 屏幕半径 / 舞台缩放；`stageScale(stage)` 已在 `:267` 拿到 `scale`），再从那里开始 / 结束画。验证：线上不再出现「够不着节点」的缺口。
- [ ] 5.3 两端**共用一个函数**（D-7 的硬要求，防止公式漂移）：`graph-renderer.js` 与 `workbench.js` 都调用第 1.2 条的 `nodeScreenRadius()`（经 `graph-physics.js` 门面），不得各写一份。验证：`grep -n "nodeScreenRadius" workbench/server/static/*.js` 命中 ≥3 处（定义 + 两个消费点），且无第二份 `14 + 16·√` 公式；放大 4 倍截图检查线头与环**零缝隙**。
- [ ] 5.4 确认**关系线本身零改动**（G-18 的后半句）：线型、粗细、透明度、箭头方向、绘制顺序**一律不改**（`graph-renderer.js:15-21` 的 `EDGE_COLORS`、`:242-300` 的排序与虚实节奏、`graph-physics-core.js:1326-1329` 的 `edgeStyle`）。验证：`git diff` 这几处**零改动**；改前后的边**几何拓扑**相同（同一对端点、同一控制点族），仅可见长度被截短一小段。
- [ ] 5.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.2 **SI-2**（关系边集合不变：source/target/type/direction 四元组全集差集为空）+ §1 **S-L3**（选中态截图里线头与环相接）走查。

## 6. 选中 / 悬停 / 聚焦（D-8 / G-15）

- [ ] 6.1 在 `workbench/server/static/workbench.css` 落实**常态基线**：`.node-ring` 的 `border-width: var(--ring-w)`（1.5–4 屏幕 px）+ 当前投影色；节点 `transform: scale(1)`；**无阴影**。验证：常态截图里节点无 `box-shadow`。
- [ ] 6.2 落实**悬停**：外环在量值基线之上 **+1px**、颜色走**更实的一档**、节点 `scale(1.04)`；**不改变选中态**。验证：悬浮一个未选中的节点，选中态不变（`aria-selected` / `.selected` 类不变）。
- [ ] 6.3 落实**选中**：外环基线 **+1.5px**、颜色走**最实的一档**、节点 `scale(1.07)`；**标签永不隐藏**（D-6）。验证：选中态截图里外环明显加粗且变实；选中节点的标签始终可见。
- [ ] 6.4 落实**聚焦（1 跳 / 2 跳）沿用现状**：`workbench.js` 的 `graphApplyVisibility()`（`:1080-1105`）的 opacity / 权重机制**一行不改**。验证：`git diff` 该函数**零改动**。
- [ ] 6.5 **删除阴影与光晕**（G-15）：`workbench.css:1678`（`.node-face` 的 `box-shadow`）、`:1696`（`.node-satellite` 的 `box-shadow`）、`:1707`（选中时的卫星点光晕）、`:1699`（悬停时的 `translateY(-1px)` 抬升）全部去掉；`transition` 只保留 `transform` / `border-width` / `border-color` / `opacity`（`acceptance.md` §2 的通用判据）。验证：节点上无阴影、无光晕、无卫星点；`grep -c "box-shadow" ` 在图谱节点规则里只剩非节点用途。
- [ ] 6.6 **保留** `.node-wrap.dragging { z-index: 6 }`（`workbench.css:1650`）与拖拽行为不变。验证：拖拽中的节点仍在最上层，拖拽交互结果与改造前一致。
- [ ] 6.7 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §2 **M-1**（节点选中 0/60/120/200ms 四帧）与 **M-2**（悬浮进入与离开 0/60/120ms 三帧）出分镜条 + 降级对照帧（状态直切），并核对 §1 **S-L3 / S-L4**、§3.2（悬浮）。

## 7. 底噪光斑：保留观感，改绘制方式（D-9 / G-4）

- [ ] 7.1 在 `workbench/server/static/workbench.js` 实现**预渲染**：把 5 条色带（`:1482-1488`）+ 尘埃点（`:1587-1604`）+ 短线段（`:1606-1622`）在**半分辨率**离屏画布上渲染一次，尺寸随 `graphTideResize()`（`:1501-1513`）。〔实证〕底噪是极低 alpha（0.018–0.13）的纹理，半分辨率放大后肉眼无差。验证：离屏画布只创建一次、只在 resize 时重画。
- [ ] 7.2 把 `graphTideDraw(t)`（`:1538-1626`）的每帧路径改为**一次 `drawImage`**（带缓慢的亚像素漂移，保留「活纸纹」的手感）。验证：每帧的绘制调用里**没有**逐点循环。
- [ ] 7.3 把**节点挖洞**改写：`graphTideNodeMask()`（`:1515-1530`）从「每色斑点 × 每节点的距离计算」（860×460 下约 600 × 31 = **18,600 次/帧**）改为「每**可见节点**一次径向渐变 + `destination-out`」（≤31 次）。验证：每帧的节点遮罩开销与节点数成正比、与色斑数无关。
- [ ] 7.4 把 `graphTideSurge(amount)`（`:1497-1499`）改为对 blit 的**整体** alpha / 缩放施加，而不是重算 600 个点。验证：求解时底噪更密更亮的观感保留（对照 `acceptance.md` §2 **M-6**）。
- [ ] 7.5 **保持** `prefers-reduced-motion` 下只画一帧（`:1634`、`:1639`）与 CSS 的 `opacity: .62` 兜底（`workbench.css:1864`）不变。验证：reduced-motion 下只画一帧的断言仍在。
- [ ] 7.6 底噪**不承载任何数据语义**（AV-4 判据④）：它与图谱数据完全无关，只在节点周围挖洞；除节点遮罩外**不读取任何图谱状态**。验证：除 `graphTideNodeMask` 外，tide 代码不引用 `sim` 的节点 / 边 / 投影状态。
- [ ] 7.7 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.3 **AV-4** 判据①—④走查（底噪仍在、观感仍读作极淡纸纹、不再每帧重绘 600 个色斑、不承载数据语义）+ §3.6（性能）+ §2 **M-6**（首帧即有底噪、1000ms 后不再每帧重绘）核对；tide 画布在像素比对协议里被列为**已知差异区**（D-12.3 / R-5）。

## 8. 死规则清理（D-10：只删能证明永不生效的代码）

- [ ] 8.1 删 `.node-wrap.in-scope .status-ring`（`workbench.css:1708`）**与**空函数 `graphSyncScope()`（`workbench.js:1077`）——两者一起删（`in-scope` 全仓无 `classList.add("in-scope")`）。验证：`grep -c "in-scope" workbench.css workbench.js` = 0；`grep -c "graphSyncScope" workbench.js` = 0。
- [ ] 8.2 修**图例「相关」色**：`workbench.css:1796` 的 `.legend i.rel { background: #aaa399 }` 改成 WebGL 实况值 `#757068`（`graph-renderer.js:15-21` 的 `related: [117/255, 112/255, 104/255]`）。**改的是图例的错，不是线的错**。验证：图例色块与画布实况逐字相同（截图取色比对）。
- [ ] 8.3 删 `.metric-track`（`workbench.css:1664-1670`）的 CSS 规则与 `--metric-angle` 变量引用（DOM 与写入已在第 2 组 2.3 / 2.5 删）。验证：`grep -c "metric-track" workbench.css` = 0。
- [ ] 8.4 删 `.node-satellite`（`workbench.css:1693-1697`）的 CSS 规则（DOM 已在第 2 组 2.3 删）——G-6 不许状态文字 / 状态点、G-15 去掉卫星点光晕。验证：`grep -c "node-satellite" workbench.css workbench.js` = 0。
- [ ] 8.5 删 `.node-unit { display: none }`（`workbench.css:1692`）与对应写入（`workbench.js:1070`）——写入了 `%` 但 CSS 永远隐藏 ⇒ 重要性投影的百分号**从未显示**；圆心恒为正式题数（G-9），不再有单位位。验证：`grep -c "node-unit" workbench.css workbench.js` = 0。
- [ ] 8.6 删 `.node-wrap.warning { --kind-color: var(--red) }`（`workbench.css:1653`）——没有任何 JS 会加 `warning` 类。验证：`grep -c "warning" workbench.css` 在图谱节点区段 = 0；`grep -rn "node-wrap.warning\|\"warning\"" workbench/server/static/*.js` 无 JS 加类路径。
- [ ] 8.7 删 `--green` / `--graphite` 两个裸名 token（`workbench.css:1515-1516`）——全仓**无 CSS 引用**。验证：`grep -c -- "--green\|--graphite" workbench.css` = 0；全仓无引用这两个变量的地方。
- [ ] 8.8 删 `.meta`（`workbench.css:1716-1719`）的 CSS 规则 + DOM 元素（`workbench.js:998-1001`）+ 写入（`:1072-1073`）+ 可见性判定（`:1322`）——G-6 节点上不许状态文字。同步在 `specs/workbench-ui/spec.md` 的 delta 里去掉 `label/meta LOD` 的 `meta` 措辞。验证：`grep -c "\.meta\b" workbench.css` 的图谱命中 = 0；`grep -c "elements.meta\|STATE_LABEL" workbench.js` = 0。
- [ ] 8.9 交付前的**死规则断言**：`grep -cE "\.metric-track|node-satellite|node-unit|\.meta\b|status-ring|in-scope|\.warning" workbench.css` 的图谱区段命中 **0 次**；`workbench.js` 中同名命中 **0 次**。任何一条不为 0 ⇒ 回到本组对应任务。
- [ ] 8.10 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.2 **SI-1 / SI-2 / SI-4**（清理不改变节点集合 / 边集合 / 投影语义）+ §0.3 **AV-3** 判据④（图例「相关」色与实况一致）走查。

## 9. 相机与 auto-fit（D-11）

- [ ] 9.1 落实 **D-11.1 初始相机按 Fit 口径算**：在 `workbench/server/static/workbench.js` 的节点创建完成之后（`graphCreateNodes()`，`:957-1053` 之后）立即调一次 `graphFit()`（`:1203-1229`）计算初始相机，替掉硬编码的 `{ scale: .7, panX: 52, panY: -18 }`（`:703`）。〔实证〕现状下 **31 个节点里 23 个落在画布外**，露出的 8 个挤在右下角（基线截图正是这一帧），且要持续到求解收敛。验证：首帧截图里 **31/31 节点全部在画布内**；收敛后现有的那一次 auto-fit（`:1406-1410`）照旧发生并微调相机。
- [ ] 9.2 落实 **D-11.2 Fit 改用「节点圆盘包围盒」**：`graphFit()`（`:1208-1214`）把 `GraphPhysics.footprint(node)`（`graph-physics-core.js:93-101`，含标签留白 `half = max(size/2+13, labelWidth/2)`）换成**节点圆盘**投影（`node.size` / 2）+ 固定屏幕边距，**不再包含标签留白**。**不改** `labelWidth()`（`:82-85`）与 `footprint()`（改了就是改布局物理，违 G-10）。〔实证〕现状包围盒 1142×1147 世界 px，而节点圆心只占 890×919。验证：860×460 画布下 scale 从约 0.37 升到 **0.41–0.47**，节点间距整体放大约 20–35%。
- [ ] 9.3 确认 **Fit 只改相机**：核对 `graphFit()` 不写回 `node.x` / `node.y`、不 reheat 求解器（`workbench.js:1107-1108` 的「Camera movement never reheats the solver」保持原样），与既有契约 `workbench-ui:155-158`「Fit without rewriting layout」一致。验证：点 Fit 前后取节点坐标集，**逐节点相同**（`acceptance.md` §0.2 **SI-3** 的一部分）。
- [ ] 9.4 落实 **D-11.3「中栏宽度变则整图缩放变」不修**：`graphFit()` 用 `graphCanvas.clientWidth/clientHeight`（`:1223-1224`）算缩放是 fit-to-viewport 的**固有性质**，不是缺陷；在代码注释里**登记该口径**，避免后续被当 bug 改掉。真正被解开的只有「缩放被标签文字长度牵着走」（9.2 已解）。
- [ ] 9.5 落实 **D-11.4 缩放条语义变更**：**量纲与上限不动**（`+` 每次 +0.09、上限 1.6，`workbench.js:1885`；滚轮下限 0.38、步长 ×0.92/×1.08，`:1762`），只把缩放条的 `title` 文案改成反映新语义（「拉开间距 / 看整体」），并同步 `docs/PRODUCT-MANUAL.md`。〔语义〕放大不再让节点变大（节点尺寸是屏幕 px），「看清细节」改由悬停与看板承担。验证：缩放档位与上限逐字不变；`title` 文案已更新。
- [ ] 9.6 **本地布局种子零改动**：`graph-physics.js:43-48` 的 `lk_graph_layout_v1_<workspace>` 格式**不动**（种子存的是节点 id 集合与坐标；本变更不改节点数、不改坐标语义）⇒ 旧种子继续有效，**不需要清缓存**。验证：种子读写的键名与序列化格式逐字不变；用改造前的旧种子加载成功。
- [ ] 9.7 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.2 **SI-3**（布局收敛性与确定性：等 `#graph-solver-state` 去掉 `.solving` 且 DOM 静止签名连续 N 次不变；清 `lk_graph_layout_v1_<workspace>` 后重跑两次从零求解，逐节点坐标相同、允许 ≤0.1px）+ §1 **S-L8**（控制卡展开、画布被覆盖时仍满足 §0.3 判据）走查。

## 10. 夜纸适配（D-12）

- [ ] 10.1 落实 **D-12.1 token 改名**：`workbench/server/static/workbench.css:1505-1518` 的 12 个裸名 `--paper / --ink / --hair / --blue / --blueSoft / --yellow / --yellowSoft / --red / --redSoft / --green / --graphite / --shadow` 改为 `--graph-paper / --graph-ink / --graph-hair / --graph-blue / --graph-blue-soft / --graph-yellow / --graph-yellow-soft / --graph-red / --graph-red-soft / --graph-green / --graph-graphite / --graph-shadow`（同区段内替换；`--green` / `--graphite` 因无引用在第 8 组 8.7 已删）。〔动机〕裸名 `--ink / --paper / --shadow` 与任何新 token 层同名 ⇒ 静默取到图谱的值。验证：`awk 'NR<1497||NR>1884' workbench.css | grep -cE 'var\(--(paper|ink|hair|blue|blueSoft|yellow|yellowSoft|red|redSoft|green|graphite|shadow)\b'` = 0；改名后图谱区段外的引用仍为 0。
- [ ] 10.2 落实**夜纸值集**：在 `workbench/server/static/workbench.css` 新增 `html[data-theme="night"]` 块，重新声明图谱 token —— 纸面 `#1c1a16`、墨 `#efe8db`、状态四色 `#9a938a / #d9a441 / #e58a4f / #d4695a`（5.72 / 7.72 / 6.68 / 4.94）、橙阶 `#a55f30 / #cf7c40 / #e59a5c / #f0b985`（3.54 / 5.47 / 7.54 / 9.91）、墨阶 `#efe8db / #9b9384 / #3a362e`、标签 `#c9c2b5`（9.82）、关系线夜纸值 `#7d9ad8 / #cbb463 / #d08a83 / #9b958a / #4e4941`。〔依据〕`html[data-theme="night"]` 特异性 (0,1,1) **高于** `:root` (0,1,0)，会压过图谱的 `:root`（F-15）。验证：夜纸下 `getComputedStyle` 取到的每个图谱 token 与 `design.md` D-4 的夜纸列逐字相同。
- [ ] 10.3 **显式登记并定稿 A-16 与 D-12.1 的张力**（contract drift）：v2 A-16 写「图谱纸面 token 恒为 `#fffdf7`、不参与夜纸换值」，而本变更 D-12.1 取夜纸纸面 `#1c1a16`。该冲突**显式登记**在 `design.md` D-12 与本 change 的 `docs/PENDING-DEFINITIONS.md` 之外的显式条目里（按 AGENTS.md 的 contract drift 纪律：不得靠时间戳或代码现状静默选边），定稿口径为「**v2 不碰图谱（A-8）⇒ 夜纸适配整体归本变更 ⇒ 图谱纸面在夜纸下取 `#1c1a16`**」，并同步 `workbench-ui` 的 delta。验证：`design.md` 里能指认这条登记；`openspec validate --specs --strict` 通过。
- [ ] 10.4 夜纸的**图例颜色键跟随**（AV-3 判据② + S-N6）：图例下半块的 4 套键在夜纸下取夜纸值（`--graph-*` 夜纸块覆盖即可，**不另写第二套图例 DOM**）。验证：夜纸截图里图例色块与节点实况一致（`acceptance.md` §1 **S-N6**）。
- [ ] 10.5 落实 **D-12.2「G-18 的『颜色不改』限定在亮色主题」**：亮色主题下 5 条关系线的颜色值**逐字节不变**（见 3.5）；夜纸主题下 5 条关系线取**同色相**的夜纸值（图例同步跟随）。〔理由〕`legacy` 在亮纸下对纸 2.02:1、在夜纸下照搬只有 1.95:1 ⇒ 几乎不可见；夜纸值集属**主题适配**（A-7 / A-8），不是「顺手重画关系线」。在 `workbench-ui` 的 delta 里写明「关系线的亮色取值不变、夜纸取值是主题适配」。验证：亮色下 `EDGE_COLORS` 的字面值逐字未变；夜纸下 `legacy` 可辨（仍是全图最淡的一档，与亮纸 2.02:1 对称）。
- [ ] 10.6 夜纸的 `.graph-tide` 透明度**单独给值**：夜纸下底噪需要压暗，**不能**沿用亮纸的 `opacity: .92` + `multiply` 结果；在夜纸 token 块里显式给出该值（`design.md` Open Question 第 4 条的实施定稿）。验证：夜纸截图里底噪仍读作极淡纸纹、不是一片灰雾。
- [ ] 10.7 **图谱区段零全局依赖**（C-8 的 L1 自足性，必须继续成立）：图谱 CSS 区段**零**引用 `var(--lk-*)` / `var(--dsw-*)`；新增的夜纸块限定在图谱作用域内，**不外泄**到其它页面。验证：`awk 'NR>=1497 && NR<=1884' workbench.css | grep -cE 'var\(--(lk|dsw)-'` = 0；夜纸块里的变量名全部带 `--graph-` 前缀。
- [ ] 10.8 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.3 **AV-1** 判据⑥、**AV-3** 判据②、§1 **S-N1…S-N6**（夜纸六张对照截图）、§3.5（夜纸下填充 / 外环 / 关系线 / 标签均可读）、§3.7（零全局依赖）逐条走查；核对「夜纸保持同一色相、只是提亮降饱和」（G-19）。

## 11. 验收（对照 `acceptance.md` 逐条核）

- [ ] 11.1 走 **§0.1 底线守卫 G-1…G-5**（最高优先级）：在**池副本 + 隔离注册表 + 独立端口**上脚本化走一遍图谱页（进页 → 切投影 → 搜索 → 筛选 → 选中节点 → 拖拽 → 缩放 → Fit），记录服务端收到的**请求方法 + 路径 + 载荷键集合**，改造前后各跑一次并 diff；再比对 `problem_attempts` / `feedback_events` / `practice_runs` 的行数与关键列、以及受影响知识点 / 题目的当前状态与调度行。验证：G-1 序列与载荷**逐条相同**、G-2 行数与关键列**逐行相同**、G-3 学习投影**完全相同**、G-4 复习建议集合与弱项排序**完全相同**、G-5 池 schema **零变更**。
- [ ] 11.2 走 **§0.2 SI-1 节点集合不变**：取图谱页渲染完成后的节点 id 全集（DOM `.node-wrap` 的 `data-kp-id` / 后端返回的节点清单），改造前后各取一次并求差集。验证：节点 id 集合**完全相同**（数量、内容皆同）。
- [ ] 11.3 走 **§0.2 SI-2 关系边集合不变**：取 WebGL 关系线的拓扑（source / target / type / direction 四元组全集），改造前后各取一次求差集。验证：边四元组集合**完全相同**（未新增、删除、改类型、改方向）。
- [ ] 11.4 走 **§0.2 SI-3 布局收敛性与确定性**：① 等 `#graph-solver-state` 不再带 `.solving`（`workbench.js:719`）且 DOM 静止签名连续 N 次不变后，取每个节点的归一化坐标；② 清空 `lk_graph_layout_v1_<workspace>`（`graph-physics.js:43-48`）后**重跑两次从零求解**，取同一批坐标。验证：布局**必须收敛**；两次从零求解的坐标**逐节点相同**（允许 ≤0.1px 存储取整误差）；改造前后的坐标集**相同**。
- [ ] 11.5 走 **§0.2 SI-4 投影语义不变**：取 `graph-physics-core.js:1463-1470` `scoreFor()` 对同一批节点算出的值，与 `workbench.js:1055-1061` `graphProjectionDisplay()` 的显示映射。验证：① 四个投影**都还在**、**含义不互换**（关系结构投影仍不承载量值语义）；② 同一节点在同一投影下的量值**相同**；③ 量值 → 视觉（半径 / 环宽 / 颜色）的映射**单调**，改动只落在**取值区间**（14→30 屏幕 px）与**色键**，不落在**排序**上。
- [ ] 11.6 走 **§0.2 SI-5 交互行为不变**：逐项对照 `workbench-ui:121-248` 与 `pages.py:410-481` 的搜索、筛选、缩放、平移、Fit、拖拽、聚焦、聚拢滑杆、详情看板。验证：每个交互的**结果与改造前一致**；**未新增**任何由本变更引入的交互态；筛选**只改成员、不改外观**（存活节点保持同心圆形态与当前投影配色，离场节点淡出而**不变色**）。
- [ ] 11.7 走 **§0.3 AV-1…AV-4 判据逐条成立** + 差异像素 ⊆ 四个允许变化区：比对截图的差异像素集合必须 ⊆（节点区 ∪ 标签区 ∪ 图例区 ∪ 底噪画布区）的**包围盒并集**；遮罩由 DOM 的 `getBoundingClientRect` 在截图时导出，作为比对脚本的输入。验证：**落在遮罩之外的任何一个差异像素 ⇒ FAIL**。
- [ ] 11.8 走 **§1 对照截图清单**：产出**改造前 / 改造后**并排图，**亮色** S-L1…S-L8（8 张）、**夜纸** S-N1…S-N6（6 张），同一视口 **1440×900**、同一数据状态、同一滚动位置。验证：每张的必看点逐条成立；文字内容（节点名、图例文字）除本变更显式改动（G-6 删状态文字、AV-3 图例「相关」色修好）外**逐字一致**。
- [ ] 11.9 走 **§1.3 比对的前置固定**：`deviceScaleFactor = 1`、浏览器缩放 100%、WebGL 固定 flag（`--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`，两次必须同一种）、`prefers-reduced-motion: reduce`、等 `document.fonts.ready`、两次都用**全新浏览器上下文**（清 `lk_graph_layout_v1_<workspace>`）、`window.scrollTo(0, 0)` 并断言、导航前清缓存。**先自证基线可复现**（连跑**两次改造前**基线截图并互比）；若基线自身不可复现，按 **A-14** 的顺序把它登记为**待裁决项**，**不**默默放宽标准。验证：比对脚本可重跑、结果入库可复现。
- [ ] 11.10 走 **§2 关键帧序列 M-1…M-6**：节点选中 / 悬浮进入与离开 / 投影切换 / 状态筛选 / 标签让位 / 底噪首帧，各采一组帧拼成分镜条；**每条另出一张 `prefers-reduced-motion` 降级对照帧**（状态直切）。验证：M-1 无阴影、无光晕、无卫星点、选中标签永不隐藏；M-3 节点配色与图例颜色键**同步**换、量值→尺寸映射在整段过渡里**单调**、圆心数字**不变**；M-4 离场节点**淡出不变色**；M-5 只隐藏**次要**标签。
- [ ] 11.11 走 **§3 交互清单逐条勾选**：§3.1 键盘可达（可见焦点环、节点可聚焦、聚焦态与悬浮态**同一种**强调且不改选中态、被隐藏标签的完整标题可由键盘聚焦取到、DOM 仍是可访问性载体）、§3.2 悬浮、§3.3 投影切换、§3.4 状态筛选、§3.5 可读性与对比度、§3.6 性能、§3.7 零全局依赖。验证：清单**全部勾选**，或未勾选项**逐条列出**并说明为何可接受。
- [ ] 11.12 走 **§4 通过标准逐条判定**：§0.1 G-1…G-5 全绿、§0.2 SI-1…SI-5 全绿、§0.3 AV-1…AV-4 判据成立且遮罩之外零差异、§1 截图无越界变化、§2 分镜条达标、§3 清单全勾。验证：任一项不通过 ⇒ **回到 `design.md` 对应决策返工**，不得带着未过的底线项或结构不变量进入铺开阶段。
- [ ] 11.13 **离线复算**：按 `tmp/frontend-audit/GRAPH-NODE-PIPELINE.md` §12 的复算方法，在实现后重跑一次（照抄 `workbench.js:806-852` 的标题截断、`:854-901` 的 `graphBuild`、`:1203-1229` 的 `graphFit` 逻辑，喂真实 `graph_model` 数据），产出新的「屏幕占用 / 标签可见数 / 直径」表，与 `design.md` D-1 的表**比对**（偏差 >10% 需回看设计，见 R-4），并把结果写进 `docs/audits/`。验证：新表与 D-1 表的偏差 ≤10% 或已回看设计。
- [ ] 11.14 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；**全量**复核 `acceptance.md` §0 + §1 + §2 + §3 + §4，并按 `acceptance.md` §5 把截图脚本与请求序列脚本**可重跑**地入库、每阶段的验收产出（对照截图组 + 分镜条 + 勾选后的交互清单 + 未过项清单）齐备。

## 12. 契约协调（D-14 / A-10.2）

- [ ] 12.1 落实 **D-14 第 1 条落地顺序**：`workbench-visual-language-v2` **先**合入，本变更**后**。理由：本变更的夜纸值集以 v2 的夜纸基色 `#1c1a16` 为准；v2 的 `workbench-ui` delta 改写了 `Soft Mondrian visual foundation`，本变更要在其之上追加「图谱例外」段落。验证：合并顺序在提交历史里可查；本变更的 diff 基于 v2 之后的基线。
- [ ] 12.2 落实 **A-10.2 的 re-base**：本变更 `specs/workbench-ui/spec.md` 的 `Redundant state cues`（`:283-306`）与 `Soft Mondrian visual foundation`（`:308-337`）两块，在 v2 合入后**逐字复核**并 re-base 到 v2 的版本（MODIFIED 必须复制既有需求的**整块**），**一并删掉块内 `:285` / `:310` 的 A-10.2 标注行**。验证：两块正文 = 「**v2 的版本 + 本变更的图谱例外段落**」的合流结果，**不是**本变更的旧基线文本。
- [ ] 12.3 **退役** v2 里的场景「The knowledge graph page is unchanged」（v2 `specs/workbench-ui/spec.md:367-371`）—— 它在本变更落地后**不再成立**；该动作在 **v2 归档之后**做。验证：最终 `openspec/specs/workbench-ui/spec.md` 里该场景已消失，且「图谱例外」段落已进 `Soft Mondrian visual foundation`。
- [ ] 12.4 同步 `docs/PRODUCT-MANUAL.md` 的**知识图谱页章节**：图谱的配色（暖色板与四投影色键）、图例两块结构与随投影切换、标签规则（常态可见 / 不截断 / 重叠让位 / 无状态文字）、夜纸表现、缩放语义（放大 = 拉开间距）。验证：产品手册能逐条对上本变更的用户可观察行为。
- [ ] 12.5 `docs/GLOSSARY.md` **不引入新的正式设计名词**（D-14 第 4 条）：「同心圆 / 内核 / 外环 / 色键 / 下限」是几何与实现描述词，**不是**契约名词；若实现中确需新词（如同心圆的正式命名），**先**在 `docs/GLOSSARY.md` 建条目，否则只能进 `docs/PENDING-DEFINITIONS.md`，**不得**以挂名状态混进正式文档。验证：`docs/PENDING-DEFINITIONS.md` 里没有本变更遗留的未定义名词；正式文档里的每个名词都能在 GLOSSARY 解析。
- [ ] 12.6 同步 `docs/ACTION-GRAPH.md`：本变更**不新增、不退役、不改级**任何动作 —— **复核**后写明「无变更」。验证：ACTION-GRAPH 有对应记录（哪怕是「无变更」的显式记录）。
- [ ] 12.7 **登记既有契约漂移**（本变更触及、但不改变其行为）：① `.meta` 行的存在与 `workbench-ui:245-248` 的「label/meta LOD」措辞 ⇒ delta 里去掉 `meta`；②「Node labels SHALL always display their complete text」与实现的简称截断（`workbench.js:806-817` `graphTitleCut`）⇒ delta 里改写成与实现一致的表述（标签**显示时**呈现自己的完整文本、无省略号、无字符上限、换行而不截断；节点的完整标题由悬浮与键盘聚焦承载）。验证：两条漂移在 delta 里有对应改写，且 §2 的 `Complete primary learning text` 不被破坏。
- [ ] 12.8 落实 **A-10.2 的硬性归档顺序**（不可颠倒）：归档时**两个动作缺一不可** —— ① **先归档 `workbench-visual-language-v2`**，再归档本变更；② 归档本变更前**逐字复核**这两条需求的最终文本（`Redundant state cues` / `Soft Mondrian visual foundation`），确认是合流结果而非旧基线。验证：归档顺序在提交历史里可查；复核记录留痕。
- [ ] 12.9 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.1 **G-5**（无新增学习事实）复核职责文件的同步情况：`docs/PRODUCT-MANUAL.md` / `docs/GLOSSARY.md` / `docs/ACTION-GRAPH.md` / `openspec/specs/review-workbench/spec.md`（不动）；并确认 `openspec/specs/workbench-ui/spec.md` 的最终文本与 v2 合流一致。

## 13. 边界护栏（D-13 逐项复核：明确不动的东西）

- [ ] 13.1 复核 **D-13 第 1–3 条**：布局物理（力模型、吸引强度、端口与车道、24px 逻辑间距、Worker 求解流程）、关系线的线型 / 粗细 / 透明度 / 箭头方向 / 绘制顺序（亮色主题下逐值不变）、交互（搜索、筛选、缩放、平移、Fit、拖拽、聚焦、聚拢滑杆、详情看板）**全部未动**。验证：`git diff --stat` 显示 `graph-physics-worker.js` **零改动**；`graph-physics-core.js` 的改动**只有** `sizeFor()` 的量程（第 2 组 2.1）与端点相关注释（第 5 组 5.1）；`workbench.js` 的交互函数（`:1080-1105` 可见性、`:1203-1229` Fit 的相机部分、`:1885` 缩放档位）除本 change 明确列出的项外未改。
- [ ] 13.2 复核 **D-13 第 4–6 条**：投影语义（四个投影各代表什么、值的来源字段）、后端 / 持久化 / API（`pool/` `pipeline/` `workbench/data/`）、`localStorage` 布局种子的格式**全部未动**。验证：`git diff --stat` 显示 `pool/` `pipeline/` `workbench/data/` **零改动**；`graph-physics-core.js:1463-1470` 的 `scoreFor()` **零改动**；`graph-physics.js:43-48` 的种子读写**零改动**。
- [ ] 13.3 复核 **D-13 第 7–9 条**：可访问性契约（DOM 节点仍是外观、标签、选择、拖拽与无障碍的载体；`aria-label` 仍在）、图谱以外的任何页面、全站 token 层（`--lk-*` / `--dsw-*`）**全部未动**。验证：`workbench.css:4-46` 的全站 token 块**零改动**；`aria-label` 仍在 `workbench.js:973`；图谱区段外的页面无任何 diff。
- [ ] 13.4 复核**唯一被授权的越界**只有两项：节点**尺寸映射的取值区间**（D-3 / G-17）与**端点半径**（D-7 / G-18）。验证：把 `git diff` 的每一处改动归到「节点外观」或这两项授权之内；**归不进去的任何一处**都要么回退、要么先补 OpenSpec。
- [ ] 13.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.2 **SI-1…SI-5** 复核结构不变量（节点集合 / 边集合 / 布局收敛性与确定性 / 投影语义 / 交互行为）**全部成立**，并按 §0.1 **G-1…G-5** 复核底线守卫全绿；确认 `git diff` 里**没有**任何一行落在 D-13 的禁止清单上。
