# G 组 · 浮层/遮罩/弹层呈现缺陷审计（只读·静态）

范围：`workbench/server/static/{workbench.css,agent-ui.css,workbench.js,agent-ui.js,practice-flow.js,paper-practice.js,part-practice.js}`、`workbench/server/pages.py`。
权威 z-index 表（`static/workbench.css:114-121`）：`--z-base 0 / --z-raised 10 / --z-dropdown 100 / --z-toast 200 / --z-overlay 250 / --z-modal 300 / --z-lamp 400`。
已避开主会话 M-03（lk-switch track）与 C 组 C-15（.part-preview 仅 Esc 关）。

### G-01 · 对话抽屉（#ai-column）C/D 档开启时无任何遮罩层，唯一关闭通道是顶栏开关
- 严重度: 高
- 类型: 遮罩挡下方 / 关闭通道
- 证据: `static/workbench.css:3386-3397` —— `#ai-column { position: fixed; z-index: 10; … transform: translateX(105%); }` + `#layout.ai-drawer-open #ai-column { transform: translateX(0); }`；`static/workbench.js:1683-1693` —— `toggleDrawer()` 只 `classList.toggle`，无 backdrop/scrim；`pages.py:317-319` —— 顶栏只有 `#mobile-ai-toggle` 一个开关，无遮罩元素。
- 为什么是缺陷: 抽屉滑入后**没有半透明蒙幕**，下方中栏内容仍可见且**仍可点击/可聚焦**（无 scrim 拦截），而关闭只有「再点一次顶栏 Agent 对话」这一条路；`grep` 全仓无 `ai-drawer-open` 相关 backdrop/veil/scrim。这与任务书「浮窗出现遮罩/被遮罩」的裁定项（浮层应带可点关闭的蒙幕）相悖。
- 建议方向: 抽屉开启时插入一层 `--z-overlay`(250) 蒙幕，点击蒙幕关闭 + Esc 关闭，并 `inert`/`aria-hidden` 下方内容。

### G-02 · 导航抽屉（#left-column）D 档同样无蒙幕，下方主内容不被遮罩仍可交互
- 严重度: 高
- 类型: 遮罩挡下方 / 关闭通道
- 证据: `static/workbench.css:3412-3426` —— `@media (max-width:1023px) #left-column { position: fixed; z-index: 10; … transform: translateX(-105%); }` + `#layout.left-drawer-open #left-column{transform:translateX(0);}`；开启逻辑同 `static/workbench.js:1683-1693`（仅切 class）。
- 为什么是缺陷: 左侧导航抽屉与对话抽屉共用 `toggleDrawer`，**同样没有蒙幕**；抽屉盖住左栏但它右侧的中栏内容仍处于可点/可 Tab 状态，且**无点击外部关闭**——用户必须精确点回 `#mobile-nav-toggle`。属于「挡住下方内容却没挡住交互」的双重缺陷。
- 建议方向: 与 G-01 同一蒙幕机制统一处理，点击外部/Esc 关闭，抽屉外内容 `inert`。

### G-03 · 抽屉 z-index 钉在 10，低于 dropdown(100)/toast(200)，开启抽屉后下拉与吐司反盖在抽屉之上
- 严重度: 中
- 类型: 浮层被遮(z-index)
- 证据: `static/workbench.css:3392`（`#ai-column … z-index: 10`）、`static/workbench.css:3413`（`#left-column … z-index: 10`）vs `static/workbench.css:116-118`（`--z-raised:10 / --z-dropdown:100 / --z-toast:200`）。
- 为什么是缺陷: 抽屉按「抬起次按钮」层级（10）建模，却是一个占满侧栏的浮层；`--z-dropdown`(100) 的自绘面板（如 `chapter-lens-panel`）和 `--z-toast`(200) 的吐司会**叠在已展开抽屉之上**，遮挡抽屉内的对话/导航控件。
- 建议方向: 抽屉层级提到 `--z-overlay`(250) 档（在其蒙幕之上、modal 之下），与蒙幕成对。

### G-04 · 抽屉开启/关闭不管理焦点：不移焦点入抽屉、不 trap、Esc 无效、关闭不还焦
- 严重度: 中
- 类型: 焦点
- 证据: `static/workbench.js:1683-1693` —— `toggleDrawer()` 全程只切 class + 写 `aria-expanded`，无 `focus()`、无焦点陷阱、无 Esc 分支（对照同文件 `chapter-lens` 面板 `workbench.js:154-182` 有完整 Esc/焦点归还）。
- 为什么是缺陷: 抽屉是个模态化的侧栏浮层，但打开后键盘焦点仍留在顶栏开关；Tab 会落到抽屉**之外**的下方内容（因无蒙幕/inert），Esc 也关不掉抽屉；关闭时不把焦点还给触发按钮。与任务书「焦点陷阱/焦点不回」切面直接对应。
- 建议方向: 开启时移焦入抽屉首个可聚焦元素 + 焦点环 trap；Esc 关闭；关闭归还焦点给 `#mobile-ai-toggle`/`#mobile-nav-toggle`。

### G-05 · 来源筛选浮窗 .filter-popup z-index 硬编码 40，低于 --z-dropdown(100) 层级令，会被自绘下拉盖住
- 严重度: 中
- 类型: 浮层被遮(z-index)
- 证据: `static/workbench.css:4042` —— `.filter-popup { position: absolute; z-index: 40; width: min(420px,90vw); max-height: 70vh; overflow:auto; }`；层级令见 `static/workbench.css:117`（`--z-dropdown:100`）。
- 为什么是缺陷: 筛选浮窗是一个独立弹层，却用了 40 这个**既不等于 --z-raised(10) 也不等于 --z-dropdown(100)** 的中间值；与 `.chapter-lens-panel`(z 100)、`.part-preview`(z 30) 等其它弹层不在同一套层级谱上，同屏出现时叠序靠数值偶合而非令牌，浮窗可被下拉面板压住。
- 建议方向: 统一改用 `var(--z-dropdown)`（或新增 `--z-popover`）令牌，去掉裸 40。

### G-06 · .filter-popup 只能靠内部「关闭」按钮或再次点启动器关闭，无 Esc、无点击外部关闭
- 严重度: 中
- 类型: 关闭通道
- 证据: `static/practice-flow.js:1656-1670` —— 仅 `#filter-close` 按钮 `classList.add("hidden")` 与 `filterLaunch` click `classList.toggle("hidden")` 两条路径；文件内无该浮窗的 `Escape`/outside-click 处理（对照 `workbench.js:156` chapter-lens 有 Esc）。
- 为什么是缺陷: 弹层开着时点击页面其它区域**不会关**，也没有 Esc 通道；用户必须把鼠标移回浮窗底部的「关闭」按钮或重新点启动器。属于任务书「关闭通道不一致/缺失」的典型（且与 C-15 那个浮层是不同组件）。
- 建议方向: 补 outside-click 关闭 + Esc 关闭，并把 `aria-expanded` 同步逻辑抽成一个 `setFilterOpen(bool)`。

### G-07 · .filter-popup 用 position:absolute 挂在滚动流内，易被 overflow 祖先裁切/被内容顶出视口（存疑）
- 严重度: 低
- 类型: 被裁溢出
- 证据: `static/workbench.css:4042` —— `position: absolute; max-height: 70vh; overflow: auto;`（无 `position: fixed`，无锚定方向约束）。
- 为什么是缺陷: 浮窗是 absolute 定位，其包含块取决于最近的 positioned 祖先；若该祖先是带 `overflow` 的滚动容器，弹层会被裁，窄屏下也可能溢出视口右侧/底部。**存疑**：未在浏览器实测定位上下文，标记为待验证。
- 建议方向: 确认锚点后改 `position: fixed` + 视口内 clamp，或显式指定包含块与翻转方向。

### G-08 · .part-preview 无蒙幕、pinned 后持续盖住下方作答内容，除 Esc/详情按钮外无可见关闭
- 严重度: 中
- 类型: 遮罩挡下方 / 关闭通道
- 证据: `static/workbench.css:5254` —— `.part-preview { position:absolute; top:100%; left:0; z-index:30; width:min(360px,80vw); … box-shadow:… }`；`static/part-practice.js:85` —— `details` 点击 `pinned=!pinned`，卡持续显示，仅 hover 出 / mouseleave 且非 pinned 时隐藏 / Esc 或 `details` 再点收起。
- 为什么是缺陷: 浮层 z 30 直接浮在题目与作答区之上，**无任何蒙幕**且 pinned 态下不移开鼠标不会消失；除 Esc / 再点「详情」外无关闭按钮，也**不点击外部关闭**。与 C-15（同为 part-preview 只能 Esc 关）相邻但聚焦不同切面：此处是「无蒙幕 + 盖住下方内容 + 无显式关闭控件」。
- 建议方向: pinned 态提供明确的 ✕ 关闭按钮并支持点击外部收起，避免长期遮挡作答区。

### G-09 · .part-preview 固定 left:0/top:100% 且宽 360px，靠右的触发器处会向右溢出/被裁（存疑）
- 严重度: 低
- 类型: 被裁溢出
- 证据: `static/workbench.css:5252-5254` —— `.part-preview-wrap{position:relative}` + `.part-preview{position:absolute; top:100%; left:0; width:min(360px,80vw);}`；`.part-preview-wrap{display:inline-flex}` 内联于文本流。
- 为什么是缺陷: 弹层始终向右下展开、左边缘对齐触发器，当「详情」按钮位于行尾/靠右时，360px 宽会越过容器右缘；若祖先有 `overflow:hidden` 即被裁，最坏情况部分内容点不到。**存疑**：未实测祖先 overflow 与实际定位，标注待验证。
- 建议方向: 按触发器到视口右边距动态翻转（left/right 对齐），或窄屏沿用 5257 行的居中 fixed 方案。

### G-10 · 图谱页硬编码 .toast（z 20）位于底部居中，会盖住同区浮层控件
- 严重度: 低
- 类型: toast遮挡 / 浮层被遮(z-index)
- 证据: `static/workbench.css:5046-5053` —— `.toast{position:absolute; left:50%; bottom:22px; … z-index:20; pointer-events:none;}`；同区 `.floating/.controls` `static/workbench.css:4963`（z 8，左上）、`.zoom` `static/workbench.css:5039`（z 8，右下）、底部图例 `static/workbench.css:5020`（z 7，左下）。
- 为什么是缺陷: 图谱页这条 toast 用裸 `z-index:20`，既脱离 `--z-toast`(200) 令牌，又压在底部图例(z 7)/缩放(z 8)之上；toast 出现时短暂遮住底部浮层控件区域。`pointer-events:none` 减轻了点击拦截，但视觉遮挡与层级失序仍在。文件 `1738-1740` 也自承「图谱页这条 .toast 不归本波」⇒ 长期游离于令牌体系外。
- 建议方向: 收编进 `--z-toast` 令牌，并把落点移到不与底部浮层重叠的位置。

### G-11 · .graph-kp-selection 浮层 z-index 5，低于图谱页 .floating 控件(8) 与 toast(20)，会被盖住
- 严重度: 中
- 类型: 浮层被遮(z-index)
- 证据: `static/workbench.css:3335-3340` —— `.graph-kp-selection{position:absolute; z-index:5; transform:translate(-50%,-50%);}`；对照 `.floating` z 8（`workbench.css:4963`）、`.toast` z 20（`workbench.css:5051`）、拖拽节点 `.node-wrap.dragging` z 6（`workbench.css:4889`）。
- 为什么是缺陷: 这是一个居中于图谱的选中浮层，层级却低于左上角浮起控件卡(8) 与 toast(20)，甚至只比拖拽中的节点(6) 高 1；当浮层与这些元素重叠时被压在下面，内容显示不全/点不到。层级值同样未走令牌。
- 建议方向: 提到 `--z-dropdown` 档并纳入令牌；核对与 `.floating` 的叠序。

### G-12 · .agent-activity-float 以 sticky+float+负上边距(-22px)浮起，z 9 压在上方相邻内容上
- 严重度: 中
- 类型: 遮挡交互 / 遮罩挡下方
- 证据: `static/agent-ui.css:201-212` —— `.agent-activity-float{z-index:9; position:sticky; top:12px; float:right; width:min(320px,calc(100% - 24px)); margin:-22px 0 12px 16px;}`；markup 见 `pages.py:362`（`<section id='agent-activity-float' class='agent-activity-float hidden'>`）。
- 为什么是缺陷: 用 `margin-top:-22px` 把这块浮起面板上移，主动压到其上方的兄弟内容之上（z 9 + float right），属于「浮层靠负边距叠住下方/上方内容」；折叠态收成按钮尚可，展开时覆盖右上区域。文件 `197-199` 自述「these surfaces are inert until Agent runtime state asks for them」⇒ 但可见时确实盖内容。
- 建议方向: 负边距浮起改为明确的 popover 定位 + 蒙幕或让位布局；层级走令牌。

### G-13 · .agent-artifact-split 侧栏预览 z 9 低于 dropdown/toast，窄屏转 fixed 后可被上层浮层压住（存疑）
- 严重度: 低
- 类型: 浮层被遮(z-index)
- 证据: `static/agent-ui.css:200-236` —— `.agent-activity-float,.agent-artifact-split{z-index:9}`、`.agent-artifact-split{position:absolute; inset:0 0 0 auto; …}`；`static/agent-ui.css:383-392` —— `@media(max-width:1100px) .agent-artifact-split{position:fixed; inset:52px 12px 12px;}`。
- 为什么是缺陷: 该预览面板是占满右栏的浮层，层级却只有 9（raised 档），低于 `--z-dropdown`(100)/`--z-toast`(200)；与 chapter-lens 下拉、toast 同屏时被压住。**存疑**：实际叠序取决于各元素是否构成 stacking context，未浏览器实测，标注待验证。
- 建议方向: 侧栏浮层统一提到 overlay/dropdown 档令牌；核对窄屏 fixed 形态下的层级。

## 统计
共 13 条（高 2 / 中 7 / 低 4）

- 高: G-01（对话抽屉无蒙幕/单关闭通道）、G-02（导航抽屉无蒙幕）
- 中: G-03 抽屉 z10 被 dropdown/toast 反盖 · G-04 抽屉焦点不 trap/不还 · G-05 filter-popup z40 脱离令牌 · G-06 filter-popup 无 Esc/外部关闭 · G-08 part-preview 无蒙幕盖作答区 · G-11 graph-kp-selection z5 被盖 · G-12 agent-activity-float 负边距盖内容
- 低: G-07 filter-popup absolute 裁切(存疑) · G-09 part-preview 右溢出(存疑) · G-10 图谱 toast z20 盖底部控件 · G-13 artifact-split z9 被压(存疑)

重复规避：未采纳 M-03（lk-switch track 拦指针）与 C-15（.part-preview 仅 Esc 关）作为新条目；G-08 与 C-15 同组件但聚焦「无蒙幕/盖下方/无显式关闭」不同切面，已注明。
