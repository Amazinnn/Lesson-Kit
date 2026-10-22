# Tasks — graph-node-visual-language

> **范围依据**：`proposal.md`（范围与冻结）、`design.md` **D-1…D-14**（十四条决策，任务逐条对应）。
> **视觉语言依据**：`../workbench-visual-language-v2/decisions.md` 的
> **A-24**（图谱节点改 Obsidian 式）、**A-26**（图谱算法冻结）、
> **A-28**（用 Obsidian 源码实测值修正 A-24 的参数）、
> **A-34**（量值投影的半径读法：改写 A-33 第 ① 条）、**A-7 / A-8**（夜纸归本变更）、
> **A-10**（归档顺序）、**A-12**（自带门禁）、**A-14**（比对范围与可复现前提）、
> **A-15**（标签字号 12px）、**A-16**（图谱纸面 token 名）。
> **参数的第一来源**：`tmp/frontend-audit/OBSIDIAN-GRAPH.md`
> （结论来自本机 Obsidian 安装包 `app.js` 源码的逐条核实）。
> **现状证据**：`tmp/frontend-audit/GRAPH-NODE-PIPELINE.md`（1114 行 / 180+ 处 `文件:行号`）。
> **行为契约依据**：`specs/graph-visual-language/spec.md`（新能力，9 需求 / 39 场景）、
> `specs/workbench-ui/spec.md`（delta，6 条 MODIFIED）。
> **验收口径依据**：`acceptance.md`（§0 底线守卫 G-1…G-5、§0.2 结构不变量 **SI-0…SI-5**、
> §0.3 允许变化区 **AV-1…AV-4**、§1 对照截图 S-L1…S-L8 / S-N1…S-N6、
> §2 关键帧 M-1…M-6、§3 交互清单、§4 通过标准、§5 走查协议、§6 状态矩阵）。
>
> **实施口径**：
> - **先修缩放补偿，再落视觉语言**（D-1 明确、G-24 派生、A-28.2 派生）——第 1 组是所有
>   视觉任务的前置，不得与其它组并行或提前；否则新配色会画在 3px 的圆上看不出来。
> - **不新增任何学习事实、不新增任何持久字段、不改 API 请求序列与载荷**；`pool/` `pipeline/`
>   `workbench/data/` 一行不动。
> - **只改绘制层**（A-26）：节点的形状 / 颜色 / 绘制尺寸（**与物理半径解耦**）、
>   标签的绘制与位置、边的绘制（线宽 / 透明度 / 箭头 / 端点落点）、缩放补偿；
>   **物理半径、布局算法、边集合、投影语义、筛选语义一律不动**（D-13 的 14 条冻结项，
>   第 13 组逐条复核）。
> - **无框架、无构建步骤、无 npm、无 CDN、无外部图标字体**；纯 CSS + 原生 JS + 内联 SVG。
> - **不碰** `openspec/changes/workbench-visual-language-v2/` 下的任何文件（第 12 组只做
>   「合入后 re-base」的动作，不提前改动 v2）。
>
> **四处已知的上游裁决覆盖**（以 v2 `decisions.md` 的 A-15 / A-16 与 **A-28 / A-34** 为准）：
> ① **标签字号 12 屏幕 px**（A-15 裁决，A-28 确认不变）；
> ② **节点半径 5–13 屏幕 px、标签偏移 r+5、标签对数淡出、边宽屏幕恒定 1.25px、
>    非邻接 alpha 0.2、选中态加 1px 描边环**（A-28 用 Obsidian 源码实测值定案，
>    **取代 A-24 的 8–23px / r+18 / 无描边环**）——
>    `frontend/editable-graph` 是**本地参照实现，但它自己不是 faithful 的 Obsidian 克隆**
>    （halo+core 双层 + 1.4px 描边 + `drop-shadow`）⇒ **它的参数不作为依据**；
> ③ **图谱纸面 token 的夜纸取值**（本变更 D-12.1 取 `#1c1a16`）与 v2 A-16 的
>   「图谱纸面恒为 `#fffdf7`、不参与夜纸换值」**存在张力** —— A-16 那条是 v2 不碰图谱
>   （A-8）语境下的性质，夜纸适配已整体划归本变更；**该冲突按 AGENTS.md 的
>   contract drift 显式登记**，落地时在第 10 组任务里定稿并同步登记。
> ④ **量值投影的半径读法**（**A-34** 改写 A-33 第 ① 条 / A-28 的字面取值）：
>   **半径下限 6.5px（直径 13px）+ 随量映射**（`6.5 + 6.5·√score`），**不是**恒 13px
>   —— 恒定会同时杀死量值投影的「值越大点越大」编码 ⇒ 两份 delta 已按此改写
>   （见第 12 组 12.7 与 `design.md` D-3.4）。
>
> **每组末尾的「阶段验收」任务统一要求跑 AGENTS.md 的四条验证命令**：
> `python -m pytest tests -q`、`python -m compileall -q lessonkit.py workbench pipeline pool tests`、
> `openspec validate --specs --strict`、`python lessonkit.py guard extract-problems --course dmath --chapter ch06`；
> 并按 `acceptance.md` 指向对应小节。截图走查一律在**池数据库副本 + 隔离注册表 +
> 独立端口**上点检，**永不写真实池**（`acceptance.md` §5）。
>
> **design.md 的 Open Questions**（7 条：底噪预渲染倍率、标签让位权重、量值分档阈值、
> 夜纸底噪透明度、关系线 alpha 分级、**量值投影的半径读法（已由 A-34 裁决）**、
> 标签淡出常数）：除第 6 条外全部是**实现参数**，按 `design.md`「Open Questions」的
> 自我声明就地定稿即可，**不需要先问所有者**；**第 6 条已关闭** ——
> **A-34 裁决：量值投影半径 = `clamp(6.5 + 6.5·√score, 6.5, 13)`**
> （下限 6.5px = 直径 13px，**随量映射**，**不是**恒 13px），四个投影的半径**都随量映射**
> ⇒ 实现按 1.2 / 2.7 的公式落地；`workbench-ui` delta 里 `Metric projection morphology`
> 的旧口径一句**已按 A-34 改写**（见第 12 组 12.7）。

---

## 1. 屏幕空间缩放补偿（最高优先级，D-1 / G-24 / A-28.2）

- [ ] 1.1 在 `workbench/server/static/workbench.js` 的 `graphApplyView()`（`:2199-2202`）里，把当前相机缩放**在写 `transform` 的同一次调用中**写到 `.graph-stage` 上：`--stage-scale`（= `graphView.scale`）与 `--inv-scale`（= `1 / scale`）。**一次相机变化 = 一次变量写入**；不引入任何新状态对象、不做逐节点的 JS 计算。验证：`graphApplyView()` 只多出两条 `style.setProperty`；`--inv-scale` 在 CSS 中**只有一处定义**（其余全是消费点）。
- [ ] 1.2 在 `workbench/server/static/graph-physics.js` 的 runtime 门面（`runtime = {...}`，`:254-300`）新增 `nodeScreenRadius(node)`：返回**屏幕像素**的绘制半径，按 D-3 的三条公式（结构投影用度数 `clamp(5 + 2.2·√degreeRaw, 5, 13)` —— **A-108：`degree` = `state.degreeRaw`**（与 `scoreFor` 同源的加权度数），**不是** `degreeCount`；状态投影用 `score` `clamp(5 + 8·√score, 5, 13)`；两个数值投影用 `clamp(6.5 + 6.5·√score, 6.5, 13)` —— **A-34：下限 6.5px（直径 13px，容得下 12px 的数字），随量映射，不是恒 13px**）。这是**全仓唯一的绘制半径公式来源**（画节点与修 WebGL 端点共用，见第 5 组 5.3）。验证：`grep -n "nodeScreenRadius" workbench/server/static/*.js` 命中 1 处定义；同一 `node` 在同一投影下返回值稳定（相等量值 ⇒ 相等半径）；**结构投影的半径与物理半径同序**（A-108）。
- [ ] 1.3 在 `workbench/server/static/workbench.js` 的 `graphPaintNodes()`（`:2391-2420`）里，每帧为每个节点往 `elements.wrap`（`.node-wrap`）写 CSS 变量：`--node-d`（**屏幕 px** 的绘制直径，形如 `26px`）与 `--node-box`（舞台 px 的盒子尺寸 = `calc(var(--node-d) * var(--inv-scale))`，写成字符串交给 CSS 求值）。**不写数值缩放**（不在 JS 里算除法），避免两处漂移。验证：`getComputedStyle(wrap).getPropertyValue('--node-d')` 返回带 `px` 的屏幕直径；860×460 画布 Fit 后该值落在 10–26px（两个数值投影 13–26px 随量映射，A-34）。
- [ ] 1.4 在 `workbench/server/static/workbench.css` 的 `.node`（`:3745-3749`）把 `width/height: var(--size)` 改为 `var(--node-box)`，保留 `background: transparent` / `border: 0` / `padding: 0` / `overflow: visible` / `cursor: grab`。**命中区 = max(绘制直径, 24 屏幕 px)**（D-3：小点也要点得中），命中区**完全不可见**。验证：`elementFromPoint` 在圆盘可见外缘 ±2px 处命中该节点；`--size` 在图谱节点样式里 0 引用。
- [ ] 1.5 在 `workbench/server/static/workbench.css` 新增 `.node-dot` 的**几何骨架**（配色在第 3 组落实）：`position: absolute; inset: 0; border-radius: 50%; background: var(--node-fill);` **无 border、无 box-shadow、无渐变、无 ::before 高光**（A-28.1：Obsidian 官方只有一次 `beginFill` + `drawCircle`）。盒尺寸随 `.node` 走，**没有独立的世界像素尺寸**。验证：computed `width` = `.node` 盒宽；`border-width` = 0；`box-shadow` = none。
- [ ] 1.6 在 `workbench/server/static/workbench.css` 把排版单位屏幕化：`.label`（`:3796-3801`）的 `font-size: 12px` → `calc(12px * var(--inv-scale))`（A-15 / A-28 不变）、`max-width: 168px` → `calc(168px * var(--inv-scale))`；`.node-value`（`:3772-3777`）的 `clamp(11px, calc(var(--size) * .28), 18px)` → `calc(12px * var(--inv-scale))`（**A-28：圆心数字固定 12px**）。验证：取 `getComputedStyle(label).fontSize` **× 当前 scale** ≈ **12 屏幕 px**、`.node-value` 的**视觉**字号 = 12 屏幕 px。
- [ ] 1.7 节点与标签的间距屏幕化：**5 屏幕 px**（A-28：圆底到字顶 5px；照 Obsidian 源码 `(size+5)·nodeScale`）。`.node-wrap`（`workbench.css:3729-3733`）的 `gap: 8px` → `calc(5px * var(--inv-scale))`。**作废**旧设计的 18px。验证：视觉间距 = 5 屏幕 px（computed gap × scale ≈ 5px）；点下缘与字顶之间没有重叠。
- [ ] 1.8 落实**标签的对数淡出**（A-28）：在 `graphApplyView()` 写 `--label-alpha` = `clamp(log2(s) + 2, 0, 1)`（s = 舞台缩放）；`.label` 的 `opacity` 乘上它（与去冲突 pass 的 `opacity: 0` 相乘）。**s ≥ 0.5 ⇒ alpha = 1；0.25 ≤ s < 0.5 ⇒ 按对数淡出；s ≤ 0.25 ⇒ 消失**。验证：默认 Fit（s ≈ 0.41–0.47）下标签 alpha ≈ 0.82–0.9（**仍然可见**）；s = 0.3 时明显变淡；s = 0.25 时不可见；**这条不是「按缩放阈值硬隐藏」**（旧规则 `LABEL_MIN_RADIUS_PX` 在第 4 组删除）。
- [ ] 1.9 登记 `Screen-space sizing` 的「small-dot diameter 按屏幕像素」一条为**空实现**：节点上不再有任何点状标记（见第 8 组 8.4）；在 `specs/graph-visual-language/spec.md` 或 `design.md` 的 D-1 段**显式登记**，不得把它当成「已补偿」上报。验证：第 8 组完成后 `grep -c "node-satellite" workbench.css workbench.js` = 0，且 delta 里有一条明示。
- [ ] 1.10 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §1 **S-L2**（缩放补偿前后对照）与 §3.5（可读性与对比度）走查 —— 860×460 画布下**节点直径落在 10–26px、标签视觉字号 12px、可见标签 0–1/31 的现状被彻底消除**；对照 `tmp/frontend-audit/GRAPH-NODE-PIPELINE.md` §7.3 的现状表逐行核对。

## 2. 节点形态与尺寸映射（D-2 / D-3 / A-28 / G-1 / G-13 / G-17）

- [ ] 2.1 **〔护栏，先做〕确认 `sizeFor()` 不动**：`workbench/server/static/graph-physics-core.js` 的 `sizeFor(score)`（`:60-61`）**一行不改**（世界直径仍是 20–80）。旧设计曾把它改成 28–60 —— **那已越过 A-26 的冻结线，本变更撤销该改动**。验证：`git diff workbench/server/static/graph-physics-core.js` 中 `sizeFor` **零改动**；节点的世界尺寸全部落在 20–80。
- [ ] 2.2 把**绘制半径**收敛成**单一来源**：`graph-physics.js` 的 `nodeScreenRadius()`（1.2）是唯一实现，`workbench.js` 与 `graph-renderer.js` 都调它，**不得各写一份公式**。验证：`grep -nE "5 \+ 2\.2|5 \+ 8|6\.5 \+ 6\.5" workbench/server/static/*.js` 的**定义点**只有 1 处（其余全是调用）。
- [ ] 2.3 在 `workbench/server/static/workbench.js` 的 `graphCreateNodes()`（`:2052-2148`）把节点子层从「五层叠一个圆」改为「**单层实心圆 + 可选数字 + 交互态描边环**」：新增 `.node-dot`（由 `:2074` 的 `.node-face` 改造而来）与 `.node-focus-ring`（新元素，**常态 `display: none`**，仅交互态出现），保留 `.node-value`（`:2076`），**删除** `.metric-track`（`:2070`）与 `.status-ring`（`:2072`）的 DOM 创建。对应 CSS 规则的删除归第 8 组。验证：`graphCreateNodes()` 产出的节点 DOM 只含 `.node-dot` / `.node-focus-ring` / `.node-value` 三件 + 外层 `.label`；`grep -c "metric-track\|status-ring" workbench.js` = 0。
- [ ] 2.4 在 `workbench/server/static/workbench.css` 落实「**单层实心圆、无描边、无投影、无内高光**」（A-28.1）：`.node-dot` 只有 `background` + `border-radius`；删 `.node-face` 的 `box-shadow`、`inset 0 0 0 1px rgba(255,255,255,.82)`、`border: 1px solid …` 与 `.node-face::before` 的径向高光。验证：常态截图里节点**读作一枚平涂的实心点**；computed `border-width` = 0、`box-shadow` = none、`background-image` = none。
- [ ] 2.5 落实「**命中区只作命中、不得有可见痕迹**」（A-28）：`.node` 盒透明（`background: transparent`、`border: 0`），命中区下限 24 屏幕 px（1.4），**不得**出现任何常驻 halo / 光晕。验证：节点周围没有可见的半透明圈；`grep -c "halo" workbench.css` 在图谱节点规则里 = 0。
- [ ] 2.6 在 `workbench/server/static/workbench.js` 的 `graphProjectionDisplay()`（`:2150-2156`）落实「**圆心数字按投影决定**」（A-24.4 / A-28）：
  - **关系结构**投影 → **无数字**（结构由边表达）；
  - **学习状态**投影 → **无数字**（状态由颜色表达），删除 `STATE_SHORT` 单字分支（`:1673`）；
  - **题目数量**投影 → 数字 = 该节点的**正式题数**（`node.problems`）；
  - **重要性**投影 → 数字 = `Math.round(node.importance * 100)`（**不含 `%`**：现状 `.node-unit{display:none}` 从未显示过 `%`，单位由图例承载）。
  验证：结构 / 状态投影下节点**没有数字**；两个数值投影下数字 = 该投影的量；`STATE_SHORT`（`:1673`）在图谱区段 0 引用。
- [ ] 2.7 落实「**量值投影的半径下限 6.5px、随量映射**」（**A-34**：A-28 的**目的**是给 12px 的字腾出**直径 13px** 的空间 ⇒ **半径下限 6.5px**；**不是**恒 13px —— 恒定会同时杀死量值投影的「值越大点越大」编码）：`nodeScreenRadius()` 在两个数值投影下用 `clamp(6.5 + 6.5·√score, 6.5, 13)`；结构投影用 `clamp(5 + 2.2·√degreeRaw, 5, 13)`（**A-108**：`degree` = `state.degreeRaw`，与 `scoreFor` 同源 ⇒ **结构投影与物理半径同序**；**不是** `degreeCount`）；状态投影用 `clamp(5 + 8·√score, 5, 13)`。**〔口径〕** 四个投影的半径**都随量映射**（相等量值 ⇒ 相等半径）；量值投影里量值由**数字 + 色阶 + 大小**三条通道共同承载。**A-33 第 ① 条的字面读（恒 13px）作废。**验证：两个数值投影下半径随 `score` **单调**、落在 **6.5–13px**（`score = 1` ⇒ 13.0px）；结构投影下随度数**单调**、落在 5–13px；`nodeScreenRadius()` 里**没有**对数值投影返回常数 13 的分支。
- [ ] 2.8 保证圆心数字**压在点之上**且不溢出：`.node-value` 的 `z-index` 高于 `.node-dot`；字号 12 屏幕 px；直径 26px 的圆里放 12px 的字留有边距。验证：在 1440×900 与 860×460 两个视口下，节点中心的数字完整可读、不被点边缘切断。
- [ ] 2.9 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.3 **AV-1** 判据①②③④⑤⑥逐条走查（节点数量与 id 不变、位置不变、圆心数字按投影决定且无状态文字、量值 → 尺寸映射单调且区间落在 5–13 屏幕 px、常态点无描边无投影）；并核对 §1 **S-L1** 的「单层实心圆 + 圆心数字按投影」。

## 3. 图谱暖色板与四投影色键（D-4 / D-5 / G-7 / G-8 / G-11…G-14 / G-16 / G-20…G-22）

- [ ] 3.1 在 `workbench/server/static/workbench.css` 的图谱 token 块新增**状态四色**（G-21 / D-4）：`--graph-state-new: #8a8377`（对比 3.69）/ `--graph-state-review: #b08a12`（3.18）/ `--graph-state-mastered: #d4702f`（3.35）/ `--graph-state-work: #b03a2a`（5.92）。全暖色相，**不占用蓝**（G-16）。验证：四个值与 `design.md` D-4 的表逐字相同；图谱区段内 `#2457c5`（旧 `--blue`）0 引用。
- [ ] 3.2 同处新增**量值橙阶**（G-20 / D-12）：`--graph-scale-1: #b25d24`（4.60）/ `--graph-scale-2: #a15421`（5.43）/ `--graph-scale-3: #8a4519`（7.01）/ `--graph-scale-4: #7d2f12`（9.03）。方向规则只有一条：**值越大，与纸面的对比越强**。〔口径〕第 1、2 档由旧设计的 `#d4702f` / `#c0601f` 加深 —— A-28 让**圆心数字直接坐在填充色上**，旧值上纸色数字只有 3.35 / 4.18，达不到 4.5:1 的文本门槛；**色相、档序、语义、档数全部不变**。验证：与 D-4 表逐字相同；四个值构成同一色相的明度阶；**每一档上放 12px 的纸色数字都 ≥ 4.5:1**。
- [ ] 3.3 同处新增**墨阶三档**（G-22）：`--graph-ink-1: #2f2b24`（对纸 13.84）/ `--graph-ink-2: #6f6759`（5.49）/ `--graph-ink-3: #9c9184`（3.04）。〔口径〕在**实心点**形态下，三档是**点填充色的三个档位**（旧设计里它们是同心圆的三个零件），因此**每一档都必须过 3:1 的边界门槛** ⇒ 第三档由 `#ded6c6`（1.42）改为 `#9c9184`。验证：与 D-4 表逐字相同；三档全部 ≥3:1。
- [ ] 3.4 同处新增**文字色**：`--graph-label: #5c5549`（对纸 7.24，≥4.5:1）/ `--graph-value-ink: #fffdf7`（对橙阶 4.60–9.03）；夜纸侧 `--graph-value-ink: #1c1a16`（对夜纸橙阶 4.78–8.62）。验证：与 D-4 表逐字相同；两处对比度均达标。
- [ ] 3.5 **关系线在亮色主题下逐字节不变**（D-12.2）：`workbench/server/static/graph-renderer.js` 的 `EDGE_COLORS`（`:15-21`）**一行不动**（先修 `#456fc9` / 应用 `#c3a128` / 对比 `#c75a52` / 相关 `#757068` / 隐含 `#bbb4a9`）；`graph-physics-core.js` 的 `edgeStyle()`（`:1326-1329`）**只有线宽与透明度两处改动**（见第 5 组 5.2），**边的类型与权重不动**。验证：`git diff` 显示 `EDGE_COLORS` **零改动**（图例的错另在第 8 组 8.2 修，图例不是线）。
- [ ] 3.6 在 `workbench/server/static/workbench.js` 的 `graphUpdateNodeAppearance()`（`:2158-2170`）按当前投影给节点写色键（**一个变量，实心点填充色**）：`structure` → 墨阶三档（按 `score` 分 3 档）；`problem_count` → 橙阶 4 档（按 `score`）；`importance` → 橙阶**按数据实际给两档**（**A-107**：`importance` 只有 `core` / `supplementary` 两类 ⇒ `0.55` / `1` ⇒ 落在橙阶的第 3、第 4 档；**不许发明数据**）；`state` → 状态四色（按 `node.state`）。**不写学习记录、不改状态、不改成员**。验证：四个投影各截一张，节点填充色与 `design.md` D-4 的表逐项对应；切换投影**不发任何请求**。
- [ ] 3.7 校验量值分档阈值（D-5 的〔待核〕）：用 `tmp/frontend-audit/GRAPH-NODE-PIPELINE.md` §12 的复算方法，在 dmath/ch06 的**真实 score 分布**上确认 `.25 / .5 / .75` 四档**不空置**；若某档空置，改用分位数分档（**不改「单色阶」这一规格**）。〔**A-107 修正**〕本条**只适用于 `problem_count`**：`importance` 在真实数据里只有 `core` / `supplementary` **两类**（映射为 `0.55` / `1`）⇒ **按数据实际给两档**，四档里的另两档**必然为空** —— 这是数据事实、不是缺陷。⚠️ **不许发明数据**（不许为了凑四档而给内容侧造第三、四档的重要性分级）—— 要四档是**内容侧**给知识点补重要性分级的**另一个决定**，不是图谱渲染能解决的。验证：复算表里 `problem_count` 的四档各有节点数；`importance` 的两档（core / supplementary）各有节点数；分档边界写成常量而非散落的字面量。
- [ ] 3.8 把图例改为**两块**（G-14 / D-5）：在 `workbench/server/pages.py` 的 `graph_page()`（`:661-732`）把现有 `.legend`（`:713-718`，5 个关系类型）改为「上半 = 关系线型（**保留现状**的可点按显示/隐藏行为与 `data-edge-type` / `aria-pressed`）+ 下半 = 节点颜色键」的两块结构；下半块的 4 套内容（`structure` / `problem_count` / `importance` / `state`）**一次渲染全**，每套带 `data-legend-for="…"`。**颜色值只在 CSS 里定义一处**，模板只给结构 ⇒ 不会两处漂移。验证：图例 DOM 存在 4 套 `data-legend-for`；关系线型的 5 项与改造前逐字一致。
- [ ] 3.9 在 `workbench/server/static/workbench.js` 的 `graphApplyView()`（`:2199-2202`）按当前投影切换图例下半块的可见套（与顶栏 Tab 的 `data-view` 同源）；`structure` 投影显示**节点形态键**（一枚样例实心点 + 「标签在点下方」的示意），**不是**色阶列表（G-22：颜色不承载语义）。**图例只解释颜色，不引入任何学习状态 / 指标 / 筛选控件**。验证：切四个投影，图例下半块随之切换；`grep -c "graph-legend" workbench.js` 的切换逻辑只改 `hidden` / `display`，不写学习数据。
- [ ] 3.10 在上半块给**有向的两项（先修 / 应用）补箭头符号**，把 D-7.3 的箭头语义钉在图例上（对比 / 相关 / 隐含不画箭头）。验证：图例上半的箭头符号与画布上实际画出的箭头一一对应。
- [ ] 3.11 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.3 **AV-3** 判据①②③④走查（两块都在、下半与当前投影严格对应、上半关系线型保留现状且带箭头符号、图例「相关」色与 WebGL 实况一致 —— ④ 由第 8 组 8.2 收口）与 §3.3（投影切换）逐条走查；并核对 §1 **S-L5**（四投影各一张）与 §1 **S-N4**（夜纸四投影各一张）。

## 4. 标签系统与重叠让位（D-6 / G-5 / G-6 / G-23 / A-10.3 / A-28）

- [ ] 4.1 在 `workbench/server/static/workbench.js` 删掉**缩放阈值**隐藏规则：`LABEL_MIN_RADIUS_PX`（`:2385`）与 `labelScaleThreshold()`（`:2387-2389`）整体删除；`graphPaintNodes()`（`:2415-2417`）的 `labelVisible` 判定改为「**默认可见**（除被屏幕空间去冲突 pass 隐藏）」。〔实证〕该规则在 Fit 后（s = 0.17–0.49）让 30/31 个节点没有标签。**〔口径〕** 新的「缩放 < 0.5 对数淡出」（1.8）是**连续的透明度曲线**，与这条**硬阈值**不是一回事。验证：`grep -c "LABEL_MIN_RADIUS_PX\|labelScaleThreshold" workbench.js` = 0。
- [ ] 4.2 在 `workbench/server/static/workbench.css` 落实标签「常态可见但不抢眼」（G-5）：`.label`（`:3796-3801`）的颜色从 `#2b2925`（≈15:1）降到 `var(--graph-label)`（7.24:1）；纸色描边光晕从 `0 0 6px` **减薄**到 `0 0 3px`（〔依据〕`OBSIDIAN-GRAPH.md` §6.1：官方没有光晕，但我们的纸底更杂乱，光晕有存在理由，只是 4.4px 太粗）；字重与行高不变。验证：实测对比度 ≥4.5:1（夜纸下同样达标）**且低于**节点自身填充的对比度（不抢节点）。
- [ ] 4.3 落实「**不截断**」（A-10.3 取 G-5 的这一支）：`.label` **不加** `text-overflow: ellipsis`、**不加** `-webkit-line-clamp`、**不设**行数上限；`max-width` 保持 `calc(168px * var(--inv-scale))`，文字**换行显示全文**。验证：一条含标点的长标题在 DOM 里完整换行显示；图谱区段 `grep -c "line-clamp\|text-overflow" workbench.css` = 0。
- [ ] 4.4 新增**屏幕空间去冲突 pass**（G-23 / D-6）：在 `workbench/server/static/workbench.js` 实现 `graphResolveLabelCollisions()`，触发时机为**相机变化（缩放/平移）、布局收敛、投影切换、选中变化**——**不是每帧**；**一次批量读**全部标签的 `getBoundingClientRect()`（一次读全部，禁止逐个读触发强制回流），按「**半径降序 → 重要度降序 → 节点 id 升序**」排序，标签矩形相交时**排位靠后者隐藏**（`opacity: 0` + `aria-hidden="true"`）。验证：触发时机只有那 4 类；排序键可在代码里逐条指认；隐藏项同时带 `aria-hidden`。
- [ ] 4.5 落实**可见标签预算**（D-6）：预算 = `floor(画布面积 / 9000)`（一个标签块 ≈ 66×30 屏幕 px，留一倍呼吸空间；860×460 ⇒ **43**）。**即使不重叠**，同时绘制的标签也有上限；超预算时按同一排序保留前 N 个。验证：dmath/ch06 的 31 个节点不触顶；构造 120 节点场景时标签数被预算截住。
- [ ] 4.6 落实**永不隐藏**清单（与既有契约 `workbench-ui:248`「selected, hovered, and high-focus labels SHALL remain visible」一致）：选中节点、悬停节点、其 **1 跳邻居**的标签永不隐藏；**被隐藏的标签在悬停 / 选中该节点时立刻恢复**（`opacity` 回到 1）。验证：选中一个标签被隐藏的节点，标签立即出现。
- [ ] 4.7 落实「**标签让位于节点**」与「**超出画布也算一次冲突**」（D-6 的代价段〔推断〕+ D-11.2 的代价）：去冲突 pass 同时判定「标签矩形 ∩ 邻点圆盘」——命中且该邻点未被隐藏时**先藏标签**；标签矩形超出画布边界时**先藏**。验证：截图里没有标签压在别人的点上；Fit 后贴边的标签被正确让位，画布不出现半截标签。
- [ ] 4.8 保证**完整标题**仍可达（G-5 / A-10.3）：`label.title = node.title`（`workbench.js:2091`）与 `button.title = node.title`（`:2092`）**保留**；被隐藏标签的完整标题由**悬浮**与**键盘聚焦**取到（键盘聚焦时该节点标签恢复显示）。验证：Tab 到一个标签被隐藏的节点，标签恢复且完整标题可见于 `title` 属性。
- [ ] 4.9 落实「**节点上不出现任何状态文字**」（G-6 / A-24.5）：`graphProjectionDisplay()`（`:2150-2156`）不再返回状态单字（见 2.6）；`workbench.js:2155` 的状态投影写入路径整体删除；状态名**只**保留在**学习看板**（`pages.py:725-728`）、`button.title` / `label.title`（悬浮）与**无障碍名**（`aria-label`，`workbench.js:2068`）里，**不渲染成可见文字**。验证：节点上肉眼看不到「新 / 练 / 复 / 熟」任何一个字；看板与无障碍名里状态名仍在。
- [ ] 4.10 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.3 **AV-2** 判据①—⑥走查（默认可见、判据改为重叠让位 / 预算、不截断、屏幕像素字号、对比度低于节点填充但可读、隐藏的必须是**次要**标签、**缩放 < 0.5 时按对数淡出**）+ §3.1 / §3.2（键盘可达、悬浮）+ §1 **S-L7**（标签重叠）逐条核对。

## 5. 关系线：屏幕恒定 1.25px + 方向箭头 + 端点落在点缘（D-7 / A-24.3 / A-28）

- [ ] 5.1 在 `workbench/server/static/graph-physics-core.js` 标注并处理 `NODE_FACE_INSET = .07`（`:1343`）与 `endpointRadius(node)`（`:1345-1347`）：该常量与已删除的 `.node-face` 的 `inset: 7%` **是一对 coupled 的**（注释明说「If the face's inset ever changes, this constant has to change with it」）⇒ **不得**继续用它算新形态的端点。**端点计算不在物理核心做**（Worker 不知道缩放；把缩放推进核心会让缩放 reheat 求解器，违反 `workbench.js:2202-2203` 的「Camera movement never reheats the solver」）。验证：`grep -n "NODE_FACE_INSET" workbench/server/static/*.js` 只剩注释或已删除。
- [ ] 5.2 落实「**屏幕恒定 1.25px / 基础 alpha 0.3**」（A-24.3 + A-28）：`edgeStyle(edge)`（`graph-physics-core.js:1326-1329`）的 `width` 从 `1.05 + score·2.35` 改为**常数 1.25**、`baseOpacity` 从 `.15 + score·.43` 改为**常数 .30**。〔口径〕`edgeStyle()` 是**绘制辅助函数**（唯一消费点是 `graph-renderer.js:274`），**不是物理参数** ⇒ 改它落在 A-26 的「允许改（纯绘制）」之内；**边的类型与权重（`NEIGHBOR_WEIGHT` `:32`、`baseGapForStrength()` `:68-70`）一律不动**。线宽本就是屏幕像素（`graph-renderer.js:276` 的 `style.width / scale`）⇒ 1.25 与现状同口径。验证：`git diff` 中 `edgeStyle` **只改这两行**；`NEIGHBOR_WEIGHT` / `baseGapForStrength` **零改动**。
- [ ] 5.3 在 `workbench/server/static/graph-renderer.js` 的 `draw()`（`:242-300`，采样点循环 `:283-300`）实现端点回退：按**采样点**从两端向节点中心回退，直到与节点中心的距离 ≥ **新的端点半径**（= 绘制点的边缘 = 屏幕半径 / 舞台缩放；`stageScale(stage)` 已在 `:267` 拿到 `scale`），再从那里开始 / 结束画。验证：线上不再出现「够不着节点」的缺口。
- [ ] 5.4 两端**共用一个函数**（D-7 的硬要求，防止公式漂移）：`graph-renderer.js` 与 `workbench.js` 都调用第 1.2 条的 `nodeScreenRadius()`（经 `graph-physics.js` 门面），不得各写一份。验证：`grep -n "nodeScreenRadius" workbench/server/static/*.js` 命中 ≥3 处（定义 + 两个消费点），且无第二份半径公式；放大 4 倍截图检查线头与点**零缝隙**。
- [ ] 5.5 钉死**五种关系的箭头语义**（A-24.3 + A-28）：**先修 `prereq`**（箭头指向后学项）、**应用 `apply`**（箭头指向被应用方）**有向**、画箭头；**对比 `contrast`**、**相关 `related`**、**隐含 `legacy`** **对称或无方向语义，不画箭头**；`direction === "symmetric"` 的先修 / 应用**不画**箭头（现状 `graph-renderer.js:299` 的规则保留）。箭头的**屏幕尺寸恒定**（约 2× 线宽），落在**目标点的绘制边缘**。验证：四种类型的边各截一张，箭头出现 / 不出现与上表逐项对应；边的 `direction` 字段与拓扑**零改动**。
- [ ] 5.6 落实「**非邻接元素降到 alpha 0.2**」（A-28：现状节点 0.18 / 边 0.07 太狠）：`workbench.css:3734` 的 `.node-wrap.dim` 的 `opacity: .18` → **.2**；`graph-renderer.js:277-282` 的 `edgeFocus` 的「其余」系数 **0.07 → 0.2**；二跳邻域的 0.38 → **0.4**（〔口径〕`workbench-ui` 的「two-hop neighbors remain secondary」是既有契约，不能与非邻接同档）。**哪些元素被强调不变**（冻结的交互语义），改的只是**淡出的强度**。验证：选中一个节点后，非邻接的点与边**仍可见但退后**（alpha ≈ 0.2），关联边保持全亮。
- [ ] 5.7 确认**关系线的拓扑与权重零改动**（A-26）：线型、虚实节奏（`contrast` 与 `legacy` 虚线）、`EDGE_COLORS` 的亮色取值、边的 `type` / `strength` / `direction` 字段**一律不动**。〔实证〕Obsidian 官方「连线粗细与两端节点度数/权重**无关**」（`OBSIDIAN-GRAPH.md` §3）⇒ 本设计与之一致。验证：`git diff` 这几处**零改动**；改前后的边**几何拓扑**相同（同一对端点、同一控制点族），仅可见长度被截短一小段。
- [ ] 5.8 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.2 **SI-2**（关系边集合不变：source/target/type/direction 四元组全集差集为空）+ §1 **S-L3**（选中态截图里线头与点相接）走查。

## 6. 选中 / 悬停 / 聚焦（D-8 / A-24.7 + A-28）

- [ ] 6.1 在 `workbench/server/static/workbench.css` 落实**常态基线**：`.node-dot` 只有填充色，**无描边**、**无阴影**；`.node-focus-ring` **常态 `display: none`**。验证：常态截图里节点是**一枚平涂实心点**，无环无影。
- [ ] 6.2 落实**交互态的 1px 描边环**（A-28，照 Obsidian 官方的高亮环：点在圈外 1px 处、线宽屏幕恒定 1px）：`.node-focus-ring` = `position: absolute; inset: calc(-1px * var(--inv-scale)); border: calc(1px * var(--inv-scale)) solid var(--graph-focus); border-radius: 50%;`，悬停 / 选中时 `display: block`。**不是**本地参照实现那种「8px 宽、22% 透明的 halo」。验证：截图里选中点外面是**一圈细环**，不是光晕；环宽在任何缩放下都是 1 屏幕 px。
- [ ] 6.3 落实**换色**：悬停走**更实的一档**、选中走**最实的一档**（分类投影 = 同色相更饱和/更深；量值投影 = 橙阶上对比更强的一档；结构投影 = 墨阶最深一档）。验证：四个投影各截一张选中态，颜色与 `design.md` D-4 的档位一致。
- [ ] 6.4 落实**点放大**：悬停 `R_screen × 1.06`、选中 `× 1.12` —— **只改绘制半径，物理半径不动**（A-26 / A-28.4）⇒ 布局不因选中 / 悬停而变。验证：选中前后节点的**世界坐标完全相同**。
- [ ] 6.5 落实**标签提亮**：`.label` 的 `font-weight` 650 → **700**（悬停 / 选中）；**不改标签颜色**（颜色是投影色键的载体）。验证：选中态截图里该节点的标签明显更粗；标签颜色与常态一致。
- [ ] 6.6 落实**聚焦（1 跳 / 2 跳）沿用现状**：`workbench.js` 的 `graphApplyVisibility()`（`:2174-2198`）的 opacity / 权重机制**一行不改**（只有 5.6 的**淡化系数**是绘制层参数）。验证：`git diff` 该函数的**判定逻辑**零改动。
- [ ] 6.7 **删除阴影与光晕**（A-24.1 / G-15）：`workbench.css:3764`（`.node-face` 的 `box-shadow`）、`:3782`（`.node-satellite` 的 `box-shadow`）、`:3793`（选中时的卫星点光晕）、`:3795`（`box-shadow: … 0 0 0 2px var(--paper)` 的纸色光晕）、`:3785`（悬停时的 `translateY(-1px)` 抬升）全部去掉；`transition` 只保留 `transform` / `opacity` / `color`（`acceptance.md` §2 的通用判据）。验证：节点上无阴影、无光晕、无卫星点；`grep -c "box-shadow"` 在图谱节点规则里只剩非节点用途。
- [ ] 6.8 **保留** `.node-wrap.dragging { z-index: 6 }`（`workbench.css:3736`）与拖拽行为不变。验证：拖拽中的节点仍在最上层，拖拽交互结果与改造前一致。
- [ ] 6.9 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §2 **M-1**（节点选中 0/60/120/200ms 四帧）与 **M-2**（悬浮进入与离开 0/60/120ms 三帧）出分镜条 + 降级对照帧（状态直切），并核对 §1 **S-L3 / S-L4**、§3.2（悬浮）。

## 7. 底噪光斑：保留观感，改绘制方式（D-9 / G-4）

- [ ] 7.1 在 `workbench/server/static/workbench.js` 实现**预渲染**：把 5 条色带（`:2577-2583`）+ 尘埃点（`:2682-2699`）+ 短线段（`:2701-2717`）在**半分辨率**离屏画布上渲染一次，尺寸随 `graphTideResize()`（`:2596-2608`）。〔实证〕底噪是极低 alpha（0.018–0.13）的纹理，半分辨率放大后肉眼无差。验证：离屏画布只创建一次、只在 resize 时重画。
- [ ] 7.2 把 `graphTideDraw(t)`（`:2633-2721`）的每帧路径改为**一次 `drawImage`**（带缓慢的亚像素漂移，保留「活纸纹」的手感）。验证：每帧的绘制调用里**没有**逐点循环。
- [ ] 7.3 把**节点挖洞**改写：`graphTideNodeMask()`（`:2610-2625`）从「每色斑点 × 每节点的距离计算」（860×460 下约 600 × 31 = **18,600 次/帧**）改为「每**可见节点**一次径向渐变 + `destination-out`」（≤31 次）。验证：每帧的节点遮罩开销与节点数成正比、与色斑数无关。
- [ ] 7.4 把 `graphTideSurge(amount)`（`:2592-2594`）改为对 blit 的**整体** alpha / 缩放施加，而不是重算 600 个点。验证：求解时底噪更密更亮的观感保留（对照 `acceptance.md` §2 **M-6**）。
- [ ] 7.5 **保持** `prefers-reduced-motion` 下只画一帧（`:2729`、`:2734`）与 CSS 的 `opacity: .62` 兜底（`workbench.css:3950`）不变。验证：reduced-motion 下只画一帧的断言仍在。
- [ ] 7.6 底噪**不承载任何数据语义**（AV-4 判据④）：它与图谱数据完全无关，只在节点周围挖洞；除节点遮罩外**不读取任何图谱状态**。验证：除 `graphTideNodeMask` 外，tide 代码不引用 `sim` 的节点 / 边 / 投影状态。
- [ ] 7.7 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.3 **AV-4** 判据①—④走查（底噪仍在、观感仍读作极淡纸纹、不再每帧重绘 600 个色斑、不承载数据语义）+ §3.6（性能）+ §2 **M-6**（首帧即有底噪、1000ms 后不再每帧重绘）核对；tide 画布在像素比对协议里被列为**已知差异区**（D-12.3 / R-6）。

## 8. 死规则清理（D-10：只删能证明永不生效或被 A-24 / A-28 取代的代码）

- [ ] 8.1 删 `.node-wrap.in-scope .status-ring`（`workbench.css:3794`）**与**空函数 `graphSyncScope()`（`workbench.js:2172`）——两者一起删（`in-scope` 全仓无 `classList.add("in-scope")`）。验证：`grep -c "in-scope" workbench.css workbench.js` = 0；`grep -c "graphSyncScope" workbench.js` = 0。
- [ ] 8.2 修**图例「相关」色**：`workbench.css:3882` 的 `.legend i.rel { background: #aaa399 }` 改成 WebGL 实况值 `#757068`（`graph-renderer.js:15-21` 的 `related: [117/255, 112/255, 104/255]`）。**改的是图例的错，不是线的错**。验证：图例色块与画布实况逐字相同（截图取色比对）。
- [ ] 8.3 删 `.metric-track`（`workbench.css:3750-3756`）的 CSS 规则与 `--metric-angle` 变量引用（DOM 与写入已在第 2 组 2.3 / 2.6 删）。验证：`grep -c "metric-track" workbench.css` = 0。
- [ ] 8.4 删 `.node-satellite`（`workbench.css:3779-3783`）的 CSS 规则（DOM 已在第 2 组 2.3 删）——G-6 / A-24.5 不许状态文字 / 状态点、A-24.1 不要光晕。验证：`grep -c "node-satellite" workbench.css workbench.js` = 0。
- [ ] 8.5 删 `.node-unit { display: none }`（`workbench.css:3778`）与对应写入（`workbench.js:2165`）——写入了 `%` 但 CSS 永远隐藏 ⇒ 重要性投影的百分号**从未显示**；圆心数字**不含单位**，单位由图例承载。验证：`grep -c "node-unit" workbench.css workbench.js` = 0。
- [ ] 8.6 删 `.node-wrap.warning { --kind-color: var(--red) }`（`workbench.css:3739`）——没有任何 JS 会加 `warning` 类。验证：`grep -c "warning" workbench.css` 在图谱节点区段 = 0；`grep -rn "node-wrap.warning\|\"warning\"" workbench/server/static/*.js` 无 JS 加类路径。
- [ ] 8.7 删 `--green` / `--graphite` 两个裸名 token（`workbench.css:3601-3602`）——全仓**无 CSS 引用**。验证：`grep -c -- "--green\|--graphite" workbench.css` = 0；全仓无引用这两个变量的地方。
- [ ] 8.8 删 `.meta`（`workbench.css:3802-3805`）的 CSS 规则 + DOM 元素（`workbench.js:2093-2096`）+ 写入（`:2167-2168`）+ 可见性判定（`:2417`）——G-6 / A-24.5 节点上不许状态文字。同步在 `specs/workbench-ui/spec.md` 的 delta 里去掉 `label/meta LOD` 的 `meta` 措辞。验证：`grep -c "\.meta\b" workbench.css` 的图谱命中 = 0；`grep -c "elements.meta\|STATE_LABEL" workbench.js` = 0。
- [ ] 8.9 删 `.status-ring`（`workbench.css:3757-3759`）与 `.node-face` 的一整套规则（`:3760-3771`：`box-shadow` / `inset` 内高光 / 1px 描边 / `::before` 径向高光）——A-28.1：新形态是**单层实心圆**，旧的面层与环层**整体不存在**。验证：图谱区段 `grep -cE "\.node-face|\.status-ring" workbench.css` = 0；`workbench.js` 同名命中 = 0。
- [ ] 8.10 交付前的**死规则断言**：`grep -cE "\.metric-track|node-satellite|node-unit|\.meta\b|status-ring|in-scope|\.warning|\.node-face" workbench.css` 的图谱区段命中 **0 次**；`workbench.js` 中同名命中 **0 次**。任何一条不为 0 ⇒ 回到本组对应任务。
- [ ] 8.11 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.2 **SI-1 / SI-2 / SI-4**（清理不改变节点集合 / 边集合 / 投影语义）+ §0.3 **AV-3** 判据④（图例「相关」色与实况一致）走查。

## 9. 相机与 auto-fit（D-11）

- [ ] 9.1 落实 **D-11.1 初始相机按 Fit 口径算**：在 `workbench/server/static/workbench.js` 的节点创建完成之后（`graphCreateNodes()`，`:2052-2148` 之后）立即调一次 `graphFit()`（`:2298-2324`）计算初始相机，替掉硬编码的 `{ scale: .7, panX: 52, panY: -18 }`（`:1798`）。〔实证〕现状下 **31 个节点里 23 个落在画布外**，露出的 8 个挤在右下角（基线截图正是这一帧），且要持续到求解收敛。〔A-26 口径〕本条只改**相机**，**不写任何节点坐标**。验证：首帧截图里 **31/31 节点全部在画布内**；收敛后现有的那一次 auto-fit（`:2501-2505`）照旧发生并微调相机。
- [ ] 9.2 落实 **D-11.2 Fit 改用「节点圆盘包围盒」**：`graphFit()`（`:2303-2309`）把 `GraphPhysics.footprint(node)`（`graph-physics-core.js:93-101`，含标签留白 `half = max(size/2+13, labelWidth/2)`）换成**节点圆盘**投影（`node.size` / 2）+ 固定屏幕边距，**不再包含标签留白**。**不改** `labelWidth()`（`:82-85`）与 `footprint()`（改了就是改布局物理，违 A-26）。〔实证〕现状包围盒 1142×1147 世界 px，而节点圆心只占 890×919。验证：860×460 画布下 scale 从约 0.37 升到 **0.41–0.47**，节点间距整体放大约 20–35%；**`footprint()` / `labelWidth()` 零改动**。
- [ ] 9.3 确认 **Fit 只改相机**：核对 `graphFit()` 不写回 `node.x` / `node.y`、不 reheat 求解器（`workbench.js:2202-2203` 的「Camera movement never reheats the solver」保持原样），与既有契约 `workbench-ui:155-158`「Fit without rewriting layout」一致。验证：点 Fit 前后取节点坐标集，**逐节点相同**（`acceptance.md` §0.2 **SI-3** 的一部分）。
- [ ] 9.4 落实 **D-11.3「中栏宽度变则整图缩放变」不修**：`graphFit()` 用 `graphCanvas.clientWidth/clientHeight`（`:2318-2319`）算缩放是 fit-to-viewport 的**固有性质**，不是缺陷；在代码注释里**登记该口径**，避免后续被当 bug 改掉。真正被解开的只有「缩放被标签文字长度牵着走」（9.2 已解）。
- [ ] 9.5 落实 **D-11.4 缩放条语义变更**：**量纲与上限不动**（`+` 每次 +0.09、上限 1.6，`workbench.js:2980`；滚轮下限 0.38、步长 ×0.92/×1.08，`:2857`），只把缩放条的 `title` 文案改成反映新语义（「拉开间距 / 看整体」），并同步 `docs/PRODUCT-MANUAL.md`。〔语义〕**放大不再让节点变大**（节点尺寸是屏幕 px，A-28.2），「看清细节」改由悬停与看板承担。验证：缩放档位与上限逐字不变；`title` 文案已更新。
- [ ] 9.6 **本地布局种子零改动**：`graph-physics.js:43-48` 的 `lk_graph_layout_v1_<workspace>` 格式**不动**（种子存的是节点 id 集合与坐标；本变更不改节点数、不改坐标语义）⇒ 旧种子继续有效，**不需要清缓存**。验证：种子读写的键名与序列化格式逐字不变；用改造前的旧种子加载成功。
- [ ] 9.7 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.2 **SI-3**（布局收敛性与确定性）与 **SI-0**（算法冻结 diff = 0）走查；并核对 §1 **S-L8**（控制卡展开、画布被覆盖时仍满足 §0.3 判据）。

## 10. 夜纸适配（D-12）

- [ ] 10.1 落实 **D-12.1 token 改名**：`workbench/server/static/workbench.css:3591-3604` 的 12 个裸名 `--paper / --ink / --hair / --blue / --blueSoft / --yellow / --yellowSoft / --red / --redSoft / --green / --graphite / --shadow` 改为 `--graph-paper / --graph-ink / --graph-hair / --graph-blue / --graph-blue-soft / --graph-yellow / --graph-yellow-soft / --graph-red / --graph-red-soft / --graph-green / --graph-graphite / --graph-shadow`（同区段内替换；`--green` / `--graphite` 因无引用在第 8 组 8.7 已删）。〔动机〕裸名 `--ink / --paper / --shadow` 与任何新 token 层同名 ⇒ 静默取到图谱的值。验证：`awk 'NR<3583||NR>3970' workbench.css | grep -cE 'var\(--(paper|ink|hair|blue|blueSoft|yellow|yellowSoft|red|redSoft|green|graphite|shadow)\)'` = 0；改名后图谱区段外的引用仍为 0。
  ⚠️ 原命令的行号与正则已过时，修正版见此（原版实测输出 **170**：行号 `1497/1884` 已过时，且正则的 `\b` 过宽，误匹配主线的 `--ink-strong` / `--ink-muted` / `--ink-faint` 等；修正版实测 = **0**）。
- [ ] 10.2 落实**夜纸值集**：在 `workbench/server/static/workbench.css` 新增 `html[data-theme="night"]` 块，重新声明图谱 token —— 纸面 `#1c1a16`、墨 `#efe8db`、状态四色 `#9a938a / #d9a441 / #e58a4f / #d4695a`（5.72 / 7.72 / 6.68 / 4.94）、橙阶 `#be752d / #cd8a45 / #dca067 / #eba87a`（4.78 / 6.05 / 7.67 / 8.62）、墨阶 `#efe8db / #9b9384 / #78705f`（14.26 / 5.71 / 3.54）、标签 `#c9c2b5`（9.82）、**圆心数字用墨色 `#1c1a16`**、关系线夜纸值 `#7d9ad8 / #cbb463 / #d08a83 / #9b958a / #4e4941`。〔依据〕`html[data-theme="night"]` 特异性 (0,1,1) **高于** `:root` (0,1,0)，会压过图谱的 `:root`（F-15）。验证：夜纸下 `getComputedStyle` 取到的每个图谱 token 与 `design.md` D-4 的夜纸列逐字相同。
- [ ] 10.3 **显式登记并定稿 A-16 与 D-12.1 的张力**（contract drift）：v2 A-16 写「图谱纸面 token 恒为 `#fffdf7`、不参与夜纸换值」，而本变更 D-12.1 取夜纸纸面 `#1c1a16`。该冲突**显式登记**在 `design.md` D-12 与本 change 的显式条目里（按 AGENTS.md 的 contract drift 纪律：不得靠时间戳或代码现状静默选边），定稿口径为「**v2 不碰图谱（A-8）⇒ 夜纸适配整体归本变更 ⇒ 图谱纸面在夜纸下取 `#1c1a16`**」，并同步 `workbench-ui` 的 delta。验证：`design.md` 里能指认这条登记；`openspec validate --specs --strict` 通过。
- [ ] 10.4 夜纸的**图例颜色键跟随**（AV-3 判据② + S-N6）：图例下半块的 4 套键在夜纸下取夜纸值（`--graph-*` 夜纸块覆盖即可，**不另写第二套图例 DOM**）。验证：夜纸截图里图例色块与节点实况一致（`acceptance.md` §1 **S-N6**）。
- [ ] 10.5 落实 **D-12.2「关系线亮色取值不变、夜纸取值是主题适配」**：亮色主题下 5 条关系线的颜色值**逐字节不变**（见 3.5）；夜纸主题下 5 条关系线取**同色相**的夜纸值（图例同步跟随）。〔理由〕`legacy` 在亮纸下对纸 2.02:1、在夜纸下照搬只有 1.95:1 ⇒ 几乎不可见；夜纸值集属**主题适配**（A-7 / A-8），不是「顺手重画关系线」。在 `workbench-ui` 的 delta 里写明这条。验证：亮色下 `EDGE_COLORS` 的字面值逐字未变；夜纸下 `legacy` 可辨（仍是全图最淡的一档）。
- [ ] 10.6 夜纸的 `.graph-tide` 透明度**单独给值**：夜纸下底噪需要压暗，**不能**沿用亮纸的 `opacity: .92` + `multiply` 结果；在夜纸 token 块里显式给出该值（`design.md` Open Question 第 4 条的实施定稿）。验证：夜纸截图里底噪仍读作极淡纸纹、不是一片灰雾。
- [ ] 10.7 **图谱区段零全局依赖**（C-8 的 L1 自足性，必须继续成立）：图谱 CSS 区段**零**引用 `var(--lk-*)` / `var(--dsw-*)`；新增的夜纸块限定在图谱作用域内，**不外泄**到其它页面。验证：`awk 'NR>=3583 && NR<=3970' workbench.css | grep -cE 'var\(--(lk|dsw)-'` = 0；夜纸块里的变量名全部带 `--graph-` 前缀。
- [ ] 10.8 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.3 **AV-1** 判据⑥、**AV-3** 判据②、§1 **S-N1…S-N6**（夜纸六张对照截图）、§3.5（夜纸下填充 / 数字 / 关系线 / 标签均可读）、§3.7（零全局依赖）逐条走查；核对「夜纸保持同一色相、只是提亮降饱和」（G-19）。

## 11. 验收（对照 `acceptance.md` 逐条核）

- [ ] 11.1 走 **§0.1 底线守卫 G-1…G-5**（最高优先级）：在**池副本 + 隔离注册表 + 独立端口**上脚本化走一遍图谱页（进页 → 切投影 → 搜索 → 筛选 → 选中节点 → 拖拽 → 缩放 → Fit），记录服务端收到的**请求方法 + 路径 + 载荷键集合**，改造前后各跑一次并 diff；再比对 `problem_attempts` / `feedback_events` / `practice_runs` 的行数与关键列、以及受影响知识点 / 题目的当前状态与调度行。验证：G-1 序列与载荷**逐条相同**、G-2 行数与关键列**逐行相同**、G-3 学习投影**完全相同**、G-4 复习建议集合与弱项排序**完全相同**、G-5 池 schema **零变更**。
- [ ] 11.2 走 **§0.2 SI-0 算法冻结（核心门禁）**：按第 14 组的对比脚本，改造后跑一次并与改造前的存档比对。验证：**收敛后的节点坐标集合逐项一致（diff = 0）**；节点 id 集合差集为空。
- [ ] 11.3 走 **§0.2 SI-1 节点集合不变**：取图谱页渲染完成后的节点 id 全集（DOM `.node-wrap` 的 `data-kp-id` / 后端返回的节点清单），改造前后各取一次并求差集。验证：节点 id 集合**完全相同**（数量、内容皆同）。
- [ ] 11.4 走 **§0.2 SI-2 关系边集合不变**：取 WebGL 关系线的拓扑（source / target / type / direction 四元组全集），改造前后各取一次求差集。验证：边四元组集合**完全相同**（未新增、删除、改类型、改方向）。
- [ ] 11.5 走 **§0.2 SI-3 布局收敛性与确定性**：① 收敛：等 `#graph-solver-state` 不再带 `.solving`（`workbench.js:1814`）且 DOM 静止签名连续 N 次不变后，取每个节点的归一化坐标；② 确定性：**清空 `lk_graph_layout_v1_<workspace>`**（`graph-physics.js:43-48`）后**重跑两次从零求解**，取同一批坐标。验证：布局**必须收敛**；两次从零求解的坐标**逐节点相同**（允许 ≤0.1px 存储取整误差）。
- [ ] 11.6 走 **§0.2 SI-4 投影语义不变**：取 `graph-physics-core.js:1463-1470` `scoreFor()` 对同一批节点算出的值，与 `workbench.js:2150-2156` `graphProjectionDisplay()` 的显示映射。验证：① 四个投影**都还在**、**含义不互换**；② 同一节点在同一投影下的量值**相同**；③ 量值 → 视觉的映射是**单调**的，改动只落在**取值区间**（5–13 屏幕 px）与**色键**上，不落在**排序**上；④ **圆心数字按投影决定**（结构 / 状态无数字，题量 / 重要性有数字）。
- [ ] 11.7 走 **§0.2 SI-5 交互行为不变**：逐项对照 `workbench-ui:121-248` 与 `pages.py:661-732` 的搜索、筛选、缩放、平移、Fit、拖拽、聚焦、聚拢滑杆、详情看板。验证：每个交互的**结果与改造前一致**；**未新增**任何由本变更引入的交互态；筛选**只改成员、不改外观**（存活节点保持实心小圆点形态与当前投影配色，离场节点淡出而**不变色**）。
- [ ] 11.8 走 **§0.3 AV-1…AV-4 判据逐条成立** + 差异像素 ⊆ 四个允许变化区：比对截图的差异像素集合必须 ⊆（节点区 ∪ 标签区 ∪ 图例区 ∪ 底噪画布区）的**包围盒并集**；遮罩由 DOM 的 `getBoundingClientRect` 在截图时导出，作为比对脚本的输入。验证：**落在遮罩之外的任何一个差异像素 ⇒ FAIL**。
- [ ] 11.9 走 **§1 对照截图清单**：产出**改造前 / 改造后**并排图，**亮色** S-L1…S-L8（8 张）、**夜纸** S-N1…S-N6（6 张），同一视口 **1440×900**、同一数据状态、同一滚动位置。验证：每张的必看点逐条成立；文字内容（节点名、图例文字）除本变更显式改动（G-6 删状态文字、AV-3 图例「相关」色修好）外**逐字一致**。
- [ ] 11.10 走 **§1.3 比对的前置固定**：`deviceScaleFactor = 1`、浏览器缩放 100%、WebGL 固定 flag（`--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`，两次必须同一种）、`prefers-reduced-motion: reduce`、等 `document.fonts.ready`、两次都用**全新浏览器上下文**（清 `lk_graph_layout_v1_<workspace>`）、`window.scrollTo(0, 0)` 并断言、导航前清缓存。**先自证基线可复现**（连跑**两次改造前**基线截图并互比）；若基线自身不可复现，按 **A-14** 的顺序把它登记为**待裁决项**，**不**默默放宽标准。验证：比对脚本可重跑、结果入库可复现。
- [ ] 11.11 走 **§2 关键帧序列 M-1…M-6**：节点选中 / 悬浮进入与离开 / 投影切换 / 状态筛选 / 标签让位 / 底噪首帧，各采一组帧拼成分镜条；**每条另出一张 `prefers-reduced-motion` 降级对照帧**（状态直切）。验证：M-1 无阴影、无光晕、无卫星点、**选中态 = 换色 + 1px 环 + 放大 + 标签提亮**、选中标签永不隐藏；M-3 节点配色与图例颜色键**同步**换、圆心数字**按投影决定**（结构 / 状态无数字）；M-4 离场节点**淡出不变色**；M-5 只隐藏**次要**标签。
- [ ] 11.12 走 **§3 交互清单逐条勾选**：§3.1 键盘可达、§3.2 悬浮、§3.3 投影切换、§3.4 状态筛选、§3.5 可读性与对比度、§3.6 性能、§3.7 零全局依赖。验证：清单**全部勾选**，或未勾选项**逐条列出**并说明为何可接受。
- [ ] 11.13 走 **§4 通过标准逐条判定**：§0.1 G-1…G-5 全绿、§0.2 **SI-0…SI-5** 全绿、§0.3 AV-1…AV-4 判据成立且遮罩之外零差异、§1 截图无越界变化、§2 分镜条达标、§3 清单全勾。验证：任一项不通过 ⇒ **回到 `design.md` 对应决策返工**，不得带着未过的底线项或结构不变量进入铺开阶段。
- [ ] 11.14 **离线复算**：按 `tmp/frontend-audit/GRAPH-NODE-PIPELINE.md` §12 的复算方法，在实现后重跑一次（照抄 `workbench.js:1901-1947` 的标题截断、`:1949-1996` 的 `graphBuild`、`:2298-2324` 的 `graphFit` 逻辑，喂真实 `graph_model` 数据），产出新的「屏幕占用 / 标签可见数 / 直径」表，与 `design.md` D-1 的表**比对**（偏差 >10% 需回看设计，见 R-5），并把结果写进 `docs/audits/`。验证：新表与 D-1 表的偏差 ≤10% 或已回看设计。
- [ ] 11.15 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；**全量**复核 `acceptance.md` §0 + §1 + §2 + §3 + §4，并按 `acceptance.md` §5 把截图脚本与请求序列脚本**可重跑**地入库、每阶段的验收产出（对照截图组 + 分镜条 + 勾选后的交互清单 + 未过项清单）齐备。

## 12. 契约协调（D-14 / A-10.2）

- [ ] 12.1 落实 **D-14 第 1 条落地顺序**：`workbench-visual-language-v2` **先**合入，本变更**后**。理由：本变更的夜纸值集以 v2 的夜纸基色 `#1c1a16` 为准；v2 的 `workbench-ui` delta 改写了 `Soft Mondrian visual foundation`，本变更要在其之上追加「图谱例外」段落。验证：合并顺序在提交历史里可查；本变更的 diff 基于 v2 之后的基线。
- [ ] 12.2 落实 **A-10.2 的 re-base**：本变更 `specs/workbench-ui/spec.md` 的 `Redundant state cues` 与 `Soft Mondrian visual foundation` 两块，在 v2 合入后**逐字复核**并 re-base 到 v2 的版本（MODIFIED 必须复制既有需求的**整块**），**一并删掉块内的 A-10.2 标注行**。验证：两块正文 = 「**v2 的版本 + 本变更的图谱例外段落**」的合流结果，**不是**本变更的旧基线文本。
- [ ] 12.3 **退役** v2 里的场景「This foundation leaves the knowledge graph page unchanged」（v2 `specs/workbench-ui/spec.md` 的**需求正文 `:686-691`** + **场景标题 `:720`**）—— 它在本变更落地后**不再成立**；该动作在 **v2 归档之后**做。验证：最终 `openspec/specs/workbench-ui/spec.md` 里该场景已消失，且「图谱例外」段落已进 `Soft Mondrian visual foundation`。
  ⚠️ 原引用指向无关条款，已修正（原写 `:367-371`，那里是「The transition survives the content being replaced」这条**无关的转场场景**；真正的场景标题在 `:720`、需求正文在 `:686-691` ⇒ **两处一起处理**，只删标题会留下正文里那句矛盾的断言）。
- [ ] 12.4 同步 `docs/PRODUCT-MANUAL.md` 的**知识图谱页章节**：节点形态（单层实心圆点、半径 5–13 屏幕 px、无描边无投影）、标签规则（点下方 5px、12px 恒定、不截断、重叠让位、缩放 < 0.5 对数淡出、无状态文字）、关系线（屏幕恒定 1.25px、箭头语义、非邻接 alpha 0.2）、选中态（换色 + 1px 环 + 放大 + 标签提亮）、图例两块结构与随投影切换、夜纸表现、缩放语义（放大 = 拉开间距）。验证：产品手册能逐条对上本变更的用户可观察行为。
- [ ] 12.5 `docs/GLOSSARY.md` **不引入新的正式设计名词**（D-14 第 5 条）：「实心小圆点 / 绘制半径 / 物理半径 / 色键」是几何与实现描述词，**不是**契约名词；若实现中确需新词，**先**在 `docs/GLOSSARY.md` 建条目，否则只能进 `docs/PENDING-DEFINITIONS.md`，**不得**以挂名状态混进正式文档。验证：`docs/PENDING-DEFINITIONS.md` 里没有本变更遗留的未定义名词；正式文档里的每个名词都能在 GLOSSARY 解析。
- [ ] 12.6 同步 `docs/ACTION-GRAPH.md`：本变更**不新增、不退役、不改级**任何动作 —— **复核**后写明「无变更」。验证：ACTION-GRAPH 有对应记录（哪怕是「无变更」的显式记录）。
- [ ] 12.7 **登记既有契约漂移**（本变更触及、但不改变其行为）：① `.meta` 行的存在与 `workbench-ui:245-248` 的「label/meta LOD」措辞 ⇒ delta 里去掉 `meta`；②「Node labels SHALL always display their complete text」与实现的简称截断（`workbench.js:1901-1912` `graphTitleCut`）⇒ delta 里改写成与实现一致的表述；③ **量值投影的半径读法**（**A-34 已裁决**：A-28 的**目的**是给 12px 的字腾出**直径 13px** ⇒ 半径**下限 6.5px**，且**随量映射**，**不是**恒 13px）：`graph-visual-language` delta 的 `Screen-space sizing` 已按 A-34 改写（见第 1 组 1.2 与本组 2.7）；`workbench-ui` delta 的 `Metric projection morphology` 里原「the node radius SHALL be held at the value that fits the centre number」一句（A-33 的旧口径）**已按 A-34 改写**为「半径随量映射且不小于 6.5 屏幕 px」⇒ **量值投影的「值越大点越大」重新成立**，量值由**数字 + 色阶 + 大小**共同承载。**〔收口〕该句已改**（原先按 `design.md` R-4b 与 Open Questions 第 6 条登记为漂移；现两份 delta 口径一致，漂移关闭）。验证：三条漂移在 delta 里有对应改写，且 §2 的 `Complete primary learning text` 不被破坏。
- [ ] 12.8 落实 **A-10.2 的硬性归档顺序**（不可颠倒）：归档时**两个动作缺一不可** —— ① **先归档 `workbench-visual-language-v2`**，再归档本变更；② 归档本变更前**逐字复核**这两条需求的最终文本，确认是合流结果而非旧基线。验证：归档顺序在提交历史里可查；复核记录留痕。
- [ ] 12.9 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.1 **G-5**（无新增学习事实）复核职责文件的同步情况：`docs/PRODUCT-MANUAL.md` / `docs/GLOSSARY.md` / `docs/ACTION-GRAPH.md` / `openspec/specs/review-workbench/spec.md`（不动）；并确认 `openspec/specs/workbench-ui/spec.md` 的最终文本与 v2 合流一致。

## 13. 边界护栏（D-13 逐项复核：明确不动的东西）

- [ ] 13.1 复核 **D-13.1 第 1–7 条（物理与布局）**：力模型、迭代次数与收敛判据、阻尼、引力 / 斥力参数、碰撞与分离逻辑（含 `sizeFor()` / `footprint()` / `labelWidth()`）、布局种子读写、auto-fit 之外的相机与布局逻辑**全部未动**。验证：`git diff --stat` 显示 `graph-physics-worker.js` **零改动**；`graph-physics-core.js` 的改动**只有** `edgeStyle()` 的线宽 / 透明度两行（第 5 组 5.2）与端点相关注释（第 5 组 5.1）；`sizeFor()`（`:60-61`）**零改动**。
- [ ] 13.2 复核 **D-13.1 第 8–12 条（图谱数据与语义）**：邻接与边集合、边的类型与权重、筛选语义、投影语义与分档、指标计算（`scoreFor()` / `stateAttention()` / `strength01()`）**全部未动**。验证：`git diff` 中 `NEIGHBOR_WEIGHT`（`:32`）、`baseGapForStrength()`（`:68-70`）、`scoreFor()`（`:1463-1470`）、`stateAttention()` **零改动**；`workbench.js:2150-2156` 的投影显示映射只改了**圆心数字的显示**（2.6），**投影取值来源未动**。
- [ ] 13.3 复核 **D-13.1 第 13–14 条（DOM 与交互）**：DOM 节点的身份与顺序（`data-kp-id`、创建顺序）、拖拽与聚焦的行为语义**全部未动**。验证：`graphCreateNodes()` 只换**子层**（2.3），节点 id 与顺序不变；`graphApplyVisibility()`（`workbench.js:2174-2198`）的判定逻辑零改动；`aria-label` 仍在 `workbench.js:2068`。
- [ ] 13.4 复核 **D-13.2 的六条「允许改」**：节点的绘制形状 / 颜色 / 绘制尺寸（与物理半径解耦）、标签的绘制与位置、边的绘制（线宽 / 透明度 / 箭头 / 端点落点）、缩放补偿 —— **每一处改动都能归进这六条之一**。验证：把 `git diff` 的每一处改动归类；**归不进去的任何一处**都要么回退、要么先补 OpenSpec。
- [ ] 13.5 复核 **后端 / 数据层 / 图谱以外的页面**：`pool/`、`pipeline/`、`workbench/data/`、`workbench.css:43-245` 的全站 token 块**零改动**；图谱区段外的页面无任何 diff。验证：`git diff --stat` 四处**零改动**。
- [ ] 13.6 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0.2 **SI-0…SI-5** 复核结构不变量与算法冻结**全部成立**，并按 §0.1 **G-1…G-5** 复核底线守卫全绿；确认 `git diff` 里**没有**任何一行落在 D-13 的禁止清单上。

## 14. **算法冻结与 diff = 0 证据**（A-26 的可执行判据）

> 〔A-26 原文〕「改造前后，用**同一份输入**（同一章节、同一初始条件、同一迭代预算）
> 各跑一次力导向，**收敛后的节点坐标集合必须逐项一致**（diff = 0）。
> 写一个对比脚本放进 `graph-node-visual-language` 的 tasks，改造前后各跑一次并留证据。」
> —— 若坐标有任何差异，就说明改动越界到了算法，**必须回退**。
>
> **〔A-104 口径：两条判据都要，条款不删〕** 本组 14.1–14.3 的 **dmath/ch06 + 浏览器 +
> DOM 收敛**是**出结论时的验收判据**（真实数据 + 真实渲染）；
> 已落地的 `tools/graph-layout-diff.js`（**合成确定性图谱** `synthetic-deterministic-v1`，
> 96 节点 / 338 边，**不读池、不用浏览器**）是**每次改动都跑的可复现回归判据**
> （无池依赖、秒级出结果）。
> ⇒ **合成图谱判据是补充，不是替代**：它**证明不了真实数据上的行为**，
> **不许**用它替代 14.1–14.3 的真实课程判据；反之亦然，两条都要跑、都算数。

- [ ] 14.1 **写对比脚本**（只读、不写池）：新增一个可重跑的脚本（如 `tools/graph-layout-diff.js` 或 `tests/` 下的等价物），职责：
  ① 取指定章节（默认 dmath/ch06）的图谱模型；
  ② **清空** `lk_graph_layout_v1_<workspace>`，从零求解（同一初始条件、同一迭代预算）；
  ③ 等收敛（`#graph-solver-state` 不再带 `.solving` 且 DOM 静止签名连续 N 次不变）；
  ④ 导出每个节点的 `(id, x, y)` 到一个 JSON（`--out <path>`）。
  **脚本不得写池**（走 `acceptance.md` §5 的池副本协议），**不得改任何产品代码**。
  〔A-104〕本条是**验收判据**；每次改动都跑的**可复现回归**另用
  `node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json`（合成图谱），
  两者**并行不互相替代**。
  验证：脚本能单独跑通并产出一份 JSON；连跑两次的 JSON 逐字节相同。
- [ ] 14.2 **改造前跑一次并存档**：在**任何产品代码改动之前**跑 14.1 的脚本，产出 `baseline` JSON 并入库（路径写进 `acceptance.md` §5 的产出清单）。〔A-104〕**合成基线同样要在任何产品代码改动之前产出**（`tools/graph-baseline/baseline.json`，已入库）⇒ 两条基线各自独立存档，**不许**互相顶替。验证：baseline JSON 存在、含 31 个节点（dmath/ch06）、含每个节点的 `id / x / y`。
- [ ] 14.3 **改造后再跑一次并比对**：改动落地后跑同一脚本，产出 `after` JSON；逐节点比较 `id / x / y`，**坐标差必须为 0**（不是「≤0.1px」—— 那是 SI-3「同一实现重跑两次」的确定性口径；SI-0 是**跨实现**比较，必须**严格 0**）。验证：diff 报告为 0 条差异；节点 id 集合差集为空。
- [ ] 14.4 **留证据**：把 `baseline.json` / `after.json` / `diff.json` 与**复跑命令**一起入库（路径与命令写进 `acceptance.md` §5）。验证：任何人拿到仓库都能按同一条命令复现同一份 diff 报告。
- [ ] 14.5 **失败即回退**：若 diff ≠ 0，**立刻定位越界的那一处改动**（用 `git diff` 逐行归类到 D-13.2 的六条），**回退**它并重跑 14.3；**不得**用「差异很小」或「四舍五入」解释掉。验证：最终 diff = 0，且 `acceptance.md` §0.2 **SI-0** 判定为绿。
- [ ] 14.6 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；把 **SI-0** 判据写进 `acceptance.md` §0.2 与 §4 的通过标准；确认 `acceptance.md` §0.2 的 SI 表**把 SI-0 与 SI-1…SI-5 并列**为核心门禁。
