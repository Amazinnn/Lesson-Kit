# H 组 · z-index 层叠与浮层「被遮」专项审计

> 只读静态审计 · 仅用 Read/Grep · 未跑浏览器。范围：`workbench/server/static/*.css|*.js`、`server/pages.py`。
> 本组专查「**被遮**」：z-index 冲突 / stacking context 打断 / overflow 裁切 / 定位基准错位。遮罩挡下方内容、关闭通道、焦点环归 G 组（M-03 lk-switch 已记，未重复）。

---

### H-01 · 章节透镜下拉面板 z-index:100 被 #topbar 的 stacking context 压平，被 #middle 盖住
- 严重度: 高
- 类型: stacking context 打断
- 证据: `workbench/server/static/workbench.css:731` `.chapter-lens-panel { z-index: var(--z-dropdown) }`(=100) 与 `workbench.css:574-575` `#topbar { position:relative; z-index:1 }`
- 为什么是缺陷: 面板虽写 z-index:100，但它的 stacking 父 `#topbar` 自建 stacking context 且只有 z-index:1，面板的 100 只在顶栏内部生效；面板 `top:calc(100%+6px)` 向下溢出顶栏，进入 `#middle`（`workbench.css:851-857` `position:relative; z-index:1`）区域。顶栏(1)与 #middle(1) 同值，而 `#middle` 在 DOM 中更靠后（`server/pages.py:334` topbar 先、`pages.py:338` #middle 后）⇒ 后者赢，**下拉面板被中栏内容盖住**。
- 建议方向: 让 `#topbar` 在面板展开时提升到高于三栏（如 z-index 高于 1），或把面板改为 `position:fixed` 脱离顶栏 stacking context。

### H-02 · --z-overlay/--z-modal/--z-raised/--veil-modal 全部定义但从未使用 ⇒ 遮罩/模态层不存在
- 严重度: 高
- 类型: scrim 缺失（层缺失）
- 证据: `workbench.css:116 --z-raised:10`、`:119 --z-overlay:250`、`:120 --z-modal:300`、`:181/:286 --veil-modal`（明暗两套）—— grep `var(--z-modal)|var(--z-overlay)|var(--z-raised)` 在 *.css **零命中**
- 为什么是缺陷: 权威层序表 §2.7 声称 modal(300)>overlay(250)>toast(200)，但没有任何元素实际引用这些 token，也没有 `.modal/.overlay/.scrim` 类 ⇒ 抽屉、浮窗全都没有蒙幕层夹在它们与底层内容之间，"模态"层在实现里根本不存在（关闭通道/焦点归 G，此处只记层缺失导致被遮/无隔离）。
- 建议方向: 抽屉/模态真正消费 `--z-overlay`+`--veil-modal` 建一层 scrim，或删掉死 token 避免误导。

### H-03 · runtime 更新提示内联 z-index:9999，魔法值≈顶层 token 的 25 倍
- 严重度: 高
- 类型: z-index 冲突（异常大值）
- 证据: `workbench/server/static/runtime.js:21` `node.style.cssText='position:fixed;...;z-index:9999;...'`
- 为什么是缺陷: 全仓最高 token 仅 `--z-lamp:400`（`workbench.css:121`），9999 是无来源魔法值；该 fixed 提示条会压过抽屉(10/20)、下拉(100)、toast(200) 等一切浮层，出现即遮挡其它浮层的可见/可点区域。
- 建议方向: 改用 token（如 `--z-toast` 或新增 `--z-system`），移除 9999。

### H-04 · 来源筛选浮窗 .filter-popup z-index:40 是离群魔法值，低于 dropdown/toast/modal
- 严重度: 中
- 类型: z-index 冲突
- 证据: `workbench.css:4042` `.filter-popup { position:absolute; z-index:40; ... }`
- 为什么是缺陷: 40 不在 token 表（`--z-raised`10 / `--z-dropdown`100 / `--z-toast`200）内；任何同时打开的下拉(100)、toast(200) 都会盖在筛选浮窗之上，多浮层并存时筛选窗"被遮"。
- 建议方向: 统一改用 `var(--z-dropdown)`，移除裸 40。

### H-05 · .part-preview z-index:30 与 .filter-popup:40、dropdown:100 三套互不兼容
- 严重度: 中
- 类型: z-index 冲突
- 证据: `workbench.css:5254` `.part-preview { position:absolute; top:100%; z-index:30; ... }`
- 为什么是缺陷: 两个并列浮层 30(小问预览) vs 40(来源筛选) 是任意手写值，谁在上全凭数值巧合；预览 z-index 低于 dropdown(100) ⇒ 预览展开时被下拉面板盖住。
- 建议方向: 收敛到同一浮层 token，按"谁后开谁在上"用 JS 管理，而非散写数值。

### H-06 · 图谱页 .toast z-index:20 与图谱抽屉 z-index:20 同值冲突，抽屉盖住 toast
- 严重度: 中
- 类型: z-index 冲突（同值）
- 证据: `workbench.css:5049` `.toast { ... z-index:20 }` vs `workbench.css:447` `body:has(#layout[data-page="graph"]) #ai-column { z-index:20 }`、`:450 #left-column{z-index:20}`
- 为什么是缺陷: 图谱页 #middle 被钉回 `z-index:auto`（`workbench.css:436`），`.graph-shell` 是 `position:relative` 无 z-index ⇒ 不构成 stacking context，`.toast` 的 20 直接在根层与抽屉的 20 打平；`#ai-column` 在 DOM 中更靠后（`pages.py:339` vs `:338` #middle）⇒ 抽屉打开时盖住图谱 toast。
- 建议方向: 图谱 toast 提到高于抽屉档（如 `--z-toast`200），或抽屉避开 20。

### H-07 · 两个抽屉 #ai-column 与 #left-column 同为 z-index:10，窄屏同时打开顺序不定
- 严重度: 中
- 类型: z-index 冲突（同值）
- 证据: `workbench.css:3382` `#ai-column { position:fixed; z-index:10 }`(C档 ≤1279) 与 `workbench.css:3413` `#left-column { position:fixed; z-index:10 }`(D档 ≤1023)
- 为什么是缺陷: 在 ≤1023px 两档媒体查询同时命中，左右抽屉都是 fixed + z-index:10，同值 ⇒ 谁在上由 DOM 顺序（`pages.py:337` 左栏先、`:339` 右栏后）决定，右栏恒压左栏，属于未定义的层叠，易出现"导航抽屉被对话抽屉遮住点不到"。
- 建议方向: 后开者提到更高 z-index（JS 控制），或两抽屉取不同档位值。

### H-08 · 抽屉用 transform:translateX 开合，transform 建 stacking context + containing block
- 严重度: 中
- 类型: stacking context 打断 / 定位错位
- 证据: `workbench.css:3393/3397` `#ai-column { transform:translateX(105%) }` → `translateX(0)`；`workbench.css:3423/3425` `#left-column` 同法
- 为什么是缺陷: 抽屉即便"开到位"（translateX(0) 仍是 transform≠none）也持续自建 stacking context 与 containing block ⇒ 抽屉内任何 `position:fixed` 子元素改为相对抽屉定位、其 z-index 被困在抽屉层级内无法浮到全页之上；这也正是图谱页"抽屉被画布盖住"那次修复（`workbench.css:437-451`）的根因所在，属未根除的脆弱点。
- 建议方向: 开合改用 `translate` 之外的 `inset/transform: none` 切换或 `visibility`，避免常驻 stacking context。

### H-09 · .agent-activity-float z-index:9 低于抽屉 10 ⇒ 一开抽屉就被盖
- 严重度: 中
- 类型: z-index 冲突
- 证据: `workbench/server/static/agent-ui.css:201` `.agent-activity-float, .agent-artifact-split { z-index:9 }` vs 抽屉 `workbench.css:3382/3413 z-index:10`
- 为什么是缺陷: 该 sticky 悬浮卡（`agent-ui.css:206 position:sticky`）挂在 #middle 内，z-index 9 恰好比抽屉 10 低 1 级；AI 抽屉一展开（fixed, 10）就压住这块 agent 活动浮窗，视觉被遮。
- 建议方向: 悬浮卡与抽屉层位对齐到 token，抽屉态下让位或明确谁在上。

### H-10 · 图谱浮动控件 .controls 与 .zoom 同为 z-index:8，与 .legend:7、选中标签:5 抢层
- 严重度: 中
- 类型: z-index 冲突（同值）
- 证据: `workbench.css:4963` `.floating/.controls { z-index:8 }`、`:5039 .zoom { z-index:8 }`、`:5020 .legend { z-index:7 }`、`:3335 .graph-kp-selection { z-index:5 }`
- 为什么是缺陷: 左上控制卡(8) 与右下缩放条(8) 同值，靠 DOM 顺序定先后；而知识点选中标签 `.graph-kp-selection`(5) 低于控制卡(8)/图例(7)，当控制卡展开（width:230 覆盖左上区域）压到某节点选中标签时，**标签被控制卡遮住**。
- 建议方向: 选中标签提到控件之上，或控件层收敛到同一 token 并错开数值。

### H-11 · .graph-kp-selection 自带 transform 建 stacking context，z-index:5 被困
- 严重度: 中
- 类型: stacking context 打断
- 证据: `workbench.css:3333-3337` `.graph-kp-selection { position:absolute; z-index:5; transform:translate(-50%,-50%) }`
- 为什么是缺陷: `transform` 让它自建 stacking context，其 z-index:5 只在 `.graph-stage`/`.graph-shell` 内部生效；一旦祖先 `#middle` 在图谱页被钉回 `z-index:auto`（`workbench.css:436`），它的 5 与拖拽节点 `.node-wrap.dragging`(6, `workbench.css:4889`)、控件(8) 直接在根层比较 ⇒ 选中标签被拖拽节点/控件盖住。
- 建议方向: 选中态标签用更高且独立的层，或去掉常驻 transform 改用 left/top 定位。

### H-12 · .lk-approved-combo-wrap z-index:100 与 dropdown token 同值，且高于抽屉 10
- 严重度: 低
- 类型: z-index 冲突（同值/跨层）
- 证据: `workbench/server/static/practice-combo.css:2` `.lk-approved-combo-wrap { position:fixed; z-index:100 }` vs `workbench.css:731 var(--z-dropdown)`(=100)
- 为什么是缺陷: 连击庆祝层借用 100，与"下拉面板"层完全同值，语义混用；且它 fixed 于根层 z-index:100 > 抽屉 10 ⇒ 庆祝动画会画在抽屉之上（虽 `pointer-events:none` 不挡点击，但视觉叠在抽屉上）。
- 建议方向: 给庆祝层独立 token（介于 overlay/modal 之间），避免与 dropdown 撞值。

### H-13 · 做题完成层 50/51 与五彩纸屑 50 是离群值，夹在 raised(10) 与 dropdown(100) 之间
- 严重度: 低
- 类型: z-index 冲突（离群值）
- 证据: `workbench/server/static/practice-motion.css:13` `.paper-pixel-confetti { position:fixed; z-index:50 }`、`:16 #paper-completion { position:relative; z-index:51 }`
- 为什么是缺陷: 50/51 为手写离群值，不属任何 token；`#paper-completion`(51) 是完成面板却低于 dropdown(100)/toast(200) ⇒ 完成结算界面可被同屏的下拉/toast 盖住；纸屑(50) fixed 全屏也压在抽屉(10/20) 之上，层级与设计层序脱节。
- 建议方向: 完成结算层用 `--z-modal` 档，纸屑用独立庆祝 token，收敛离群值。

### H-14 · 无 modal(300) 层时 --z-toast(200) 成实际顶层，盖住 combo(100)/part-preview(30)/纸屑(50)
- 严重度: 中
- 类型: z-index 层序倒置
- 证据: `workbench.css:1748` `.toast { z-index: var(--z-toast) }`(=200) + 注释 `workbench.css:1737`「--z-toast 在模态之下」；但 modal/overlay token 从未被使用（见 H-02）
- 为什么是缺陷: 设计假设"toast 在 modal 之下"，可实现里根本没有 modal(300)/overlay(250) 层 ⇒ toast(200) 实际就是最高交互层，会盖住连击庆祝(100)、小问预览(30)、完成面板(51) 等本应更"重"的浮层，层序与注释自相矛盾。
- 建议方向: 补齐 modal/overlay 真实消费，或下调 toast 到庆祝/结算层之下。

### H-15 ·（存疑）filter-popup/part-preview 为 position:absolute，依赖祖先无 overflow，易被裁切
- 严重度: 低（存疑）
- 类型: overflow 裁切
- 证据: `workbench.css:4042` `.filter-popup { position:absolute; ... max-height:70vh }`、`workbench.css:5254` `.part-preview { position:absolute; top:100%; max-height:45vh }`；宿主 `#middle { overflow-y:auto }`(`workbench.css:853`)
- 为什么是缺陷: 两者都是 `position:absolute`（非 fixed），定位基准是最近的 positioned 祖先；`.part-preview` 从 `top:100%` 向下伸 45vh，若锚点靠 #middle 滚动区底部，超出部分被 `#middle` 的 `overflow-y:auto` 裁掉/需滚动才见。`.filter-popup` 的挂载点在本仓 CSS/JS/py 中均未找到（仅 `practice-flow.js:1576` getElementById）⇒ 无法确认其祖先 overflow，**标存疑**。
- 建议方向: 浮层改 `position:fixed` 或用 floating-ui 计算翻转，避免被滚动容器裁切；确认 filter-popup 实际挂载位置后再定性。

---

## z-index 值分布清点（全仓，按值大小排列）

**Token 定义（`workbench.css:115-121`）**：`--z-base:0` / `--z-raised:10` / `--z-dropdown:100` / `--z-toast:200` / `--z-overlay:250` / `--z-modal:300` / `--z-lamp:400`。
⚠️ 其中 `--z-raised`(10)、`--z-overlay`(250)、`--z-modal`(300) **定义后零使用**（H-02）。

| z-index 值 | 用途 / 选择器 | 文件:行号 |
|---|---|---|
| **9999** | runtime 更新提示（inline，魔法值） | `runtime.js:21` |
| **400** | `.lk-lamp`（台灯层，`--z-lamp`） | `workbench.css:4504` |
| **300** | `--z-modal` 定义，**未使用** | `workbench.css:120` |
| **250** | `--z-overlay` 定义，**未使用** | `workbench.css:119` |
| **200** | `.toast`（`--z-toast`）；live-editor 内联 zIndex:200(vendor) | `workbench.css:1748`；`live-editor.js:9` |
| **100** | `.chapter-lens-panel`(`--z-dropdown`)；`.lk-approved-combo-wrap`；live-editor zIndex:100区(vendor) | `workbench.css:731`；`practice-combo.css:2`；`live-editor.js:9` |
| **51** | `#paper-completion`（离群） | `practice-motion.css:16` |
| **50** | `.paper-pixel-confetti`（离群） | `practice-motion.css:13` |
| **40** | `.filter-popup`（离群） | `workbench.css:4042` |
| **30** | `.part-preview`（离群） | `workbench.css:5254` |
| **20** | 图谱页抽屉 `#ai-column`/`#left-column`；图谱 `.toast`（**与抽屉同值**） | `workbench.css:447`、`:450`、`:5049` |
| **10** | `#ai-column` 抽屉(C档)、`#left-column` 抽屉(D档)（**彼此同值**）；`.graph-topbar`；列分割拖拽条 `column-resizer`；`--z-raised` 定义(未用) | `workbench.css:3382`、`:3413`、`:4806`、`:2467`、`:116` |
| **9** | `.agent-activity-float`/`.agent-artifact-split` | `agent-ui.css:201` |
| **8** | `.floating`/`.controls`、`.zoom`（**彼此同值**） | `workbench.css:4963`、`:5039` |
| **7** | `.legend` | `workbench.css:5020` |
| **6** | `.node-wrap.dragging` | `workbench.css:4889` |
| **5** | `.graph-kp-selection`；`.combo-scene`；`.after-stroke` | `workbench.css:3335`；`practice-combo.css:6`、`:28` |
| **3** | 图谱节点徽标 | `workbench.css:4935` |
| **2** | `.node-wrap`、节点体、`.flash-card-prompt`、网格底纹层 | `workbench.css:4885`、`:4926`、`:3144`、`:2724`、`:4866` |
| **1** | `#topbar`、`#left-column`、`#middle`、`#ai-column`（**四方同值=1**）、`.graph-tide`、`.graph-renderer-layer`、`.flash-card-answer`、若干底纹 | `workbench.css:575`、`:849`、`:856`、`:867`；`graph-renderer.js:147`；`workbench.css:4861`、`:3143`、`:2716`、`:3557`、`:4871` |
| **0** | `.lk-ripple`/`.lk-ripple-glow`(`--z-base`)、`.graph-shell::before/::after`、live-editor zIndex:0(vendor) | `workbench.css:4476`、`:4483`、`:4844`、`:4851`；`live-editor.js:9` |
| **auto** | 图谱页三栏钉回 | `workbench.css:436` |

分布要点：
- 值域极散：从 `0/1/2` 到 `9999`，跨 4 个数量级；**离群值**有 `9999`(runtime)、`51/50`(motion)、`40`(filter)、`30`(part-preview) 四处不属任何 token。
- **同值冲突群**：`20`(图谱抽屉 vs 图谱 toast)、`10`(两抽屉)、`8`(controls vs zoom)、`1`(#topbar vs 三栏，含 H-01)。
- 顶栏 `#topbar` 与三栏同为 `1` 且 `#middle/#ai-column` 在 DOM 后出现（`pages.py:338-339`），是 H-01「下拉被盖」的直接来源。
- vendor：`live-editor.js`(CodeMirror 压缩) 内 zIndex 0/200/300 不参与工作台浮层层序。

## 统计

- **共 15 条**：高 3（H-01/H-02/H-03）· 中 8（H-04/H-05/H-06/H-07/H-08/H-09/H-10/H-11/H-14）· 低 3（H-12/H-13/H-15）· 存疑 1（H-15）。
- 类型分布：z-index 冲突 8 · stacking context 打断 2 · scrim/层缺失 1 · 层序倒置 1 · overflow 裁切 1（存疑）· 定位错位 1（与 stacking 合并计）。
- 交叉引用：M-03（lk-switch track 拦截指针）属主会话已记，未重复；遮罩挡下方内容/关闭通道/焦点环归 G 组，本组未展开。
