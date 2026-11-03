# A 组 · 组件形态·视觉基线缺陷审计（只读 · 静态）

- 审计员：A 组（组件形态·视觉基线）
- 权威依据：`openspec/changes/workbench-visual-language-v2/design-notes/component-spec.md` §4.30 裁定表（唯一形态权威）+ §3 通用规则 + `night-paper-tokens.md`
- 实现落点：`workbench/server/static/workbench.css`（5279 行）、`workbench/server/static/agent-ui.css`（446 行）、`workbench/server/pages.py`、`workbench.js`
- 方法：**纯静态读代码**（Read / Grep）。**无浏览器工具**（无 `mcp__node_repl__js` / Playwright 工具面），按协调方回退条款仅做静态审计；可视化核验归主会话。因此 E 类（交互流程）未真点过，见文末说明。

---

## A 类 · 组件形态 / 视觉基线

### A-01 · agent-ui.css 末尾 `#agent-artifact-body` 规则未闭合，吞掉整个移动端 `@media` 块
- 严重度: 高
- 证据: `workbench/server/static/agent-ui.css:435-446` —— 第 435 行 `#agent-artifact-body {`，第 438 行 `border-top: 1px solid var(--rule-hair);` 之后**没有 `}`**，第 440 行直接是 `@media (max-width: 760px) {`。全文件花括号 `{` = 99、`}` = 98（实测 Python 计数），差 1。
- 违反: CSS 语法（未闭合声明块）；连带 §4.30.3 第 4 条时间线/移动端形态不可达
- 为什么是缺陷: 未闭合的 `#agent-artifact-body` 把 `@media (max-width: 760px) { .agent-activity-float { … } }` 嵌进了声明块内部 ⇒ 该 `@media` 与其内 `.agent-activity-float` 移动端宽度规则整块失效（浏览器会丢弃这条非法嵌套），窄屏下 artifact split / activity float 的移动端布局规则不生效。
- 建议方向: 在第 438 行后补 `}` 闭合 `#agent-artifact-body`，再让 `@media` 顶层独立。

### A-02 · Agent 待发队列操作按钮 11px 字 + 4/7px 内距，命中区远小于 44px
- 严重度: 高
- 证据: `workbench/server/static/agent-ui.css:101` —— `.ai-pending-actions button { margin: 0; padding: 4px 7px; font-size: 11px; }`
- 违反: §3.1 硬约束（命中区 ≥ 44×44 CSS px）；§2.3 `--fs-micro` 11px「不得承载学习语义/不可作按钮文字」
- 为什么是缺陷: 11px 文字 + 上下各 4px 内距 ⇒ 按钮视觉高约 26px，且无 `::before` 命中区补偿（对比 `button.primary::before` / `.lk-switch__track::before` 都补到 44px）⇒ 可点目标 <44×44，违反不可让步的无障碍硬约束。
- 建议方向: 给该按钮加 `min-height: 44px` 或 `::before { inset: … }` 命中补偿，字号升到 `--fs-label`(12px)。

### A-03 · Agent 审批动作禁用态用 `opacity` 压暗
- 严重度: 高
- 证据: `workbench/server/static/agent-ui.css:372` —— `.ai-paper-approval-actions button:disabled { opacity: .55; cursor: wait; }`
- 违反: §4.1 disabled 态明文「**不用 opacity 压暗**——opacity 会把蓝底一起压成灰蓝」；§4.2 disabled 应为「沉底/基础面 + 淡墨 + 无阴影」
- 为什么是缺陷: opacity 会把按钮**底色、边框、文字一起**半透明化，在蓝洗底/沉底面上读成「灰蓝幽灵」，且文字对比被一并削弱；spec 已明确禁用此写法。
- 建议方向: 改为 `background: var(--surface-base); color: var(--ink-disabled);` 去掉 opacity。

### A-04 · 备考评分档 `--picked` 选中态**只靠颜色**传达
- 严重度: 高
- 证据: `workbench/server/static/workbench.css:5263` —— `.rating-grade--picked { border-color: var(--role-blue); color: var(--role-blue); font-weight: 600; }`
- 违反: §3.6 冗余状态通道（状态**不得只靠颜色**，必须配几何编码 + 零文字）
- 为什么是缺陷: 选中态只改边框色与文字色为蓝，没有状态点/勾/环等第二几何通道 ⇒ 灰度打印与色觉障碍下无法与未选项区分；spec 要求「当前·交互层=蓝 ring」这类几何配对。
- 建议方向: 给选中档补一个 8px 蓝实心点或空心蓝环几何标记。

### A-05 · exam-prep 块使用**未定义 token**（`--radius-md`/`--ink-line`/`--surface`/`--text`），回落成硬编码浅色，夜纸下不翻转
- 严重度: 高
- 证据: `workbench/server/static/workbench.css:5261` —— `.rating-grade { border-radius: var(--radius-md, 10px); border: 1.5px solid var(--ink-line, #ccc); background: var(--surface, #fff); }`；同文件 `:5254` —— `.part-preview { color: var(--text, #222); background: var(--surface, #fff); border: 2px solid currentColor; box-shadow: 3px 5px 12px #0002; }`
- 违反: night-paper-tokens（值 token 契约）；§2.1 圆角统一 12px（`--r-md`）；§4.18 卡片不描边
- 为什么是缺陷: `--radius-md` / `--ink-line` / `--surface` / `--text` 在全仓 CSS/py **零定义**（已 grep 确认）⇒ 永远取回落值 `10px` / `#ccc` / `#fff` / `#222`。`#fff` 背景在夜纸（`--surface-card` 深色）下**仍是纯白亮块**，破坏夜纸；圆角 10px 也不是 12px 档。
- 建议方向: 换成真 token `--r-md` / `--rule-control` / `--surface-card` / `--ink-strong`，删除回落字面量。

### A-06 · 文字按钮 `button.ghost` 无 44px 命中区补偿（视觉 36px，点击目标 36px）
- 严重度: 高
- 证据: `workbench/server/static/workbench.css:1245-1262` —— `button.ghost { gap: var(--sp-2); color: var(--ink-muted); }` 只设 gap/color，**未设 height、未挂 `::before`**；基类 `button`（`:1129`）`height: 36px`。对照 `button.primary::before`(`:1185`) / `button.outline::before`(`:1205`) / `button.icon-only::before`(`:1302`) 都补到 44px，唯独 ghost 没有。
- 违反: §3.1 硬约束（命中区 ≥44px）；§4.3 文字按钮「高 44px（命中区）」
- 为什么是缺陷: 文字按钮是最常点的低强调动作（取消/展开/更多），36px 高且无命中补偿 ⇒ 点击目标 36×?，低于 44px 不可让步线；三个兄弟形态都补了，唯独它漏 ⇒ 同族不一致。
- 建议方向: 给 `button.ghost` 补 `min-height:44px` 或 `::before { inset:-4px 0 }` 命中区补偿。

### A-07 · 按钮基类 `border-radius: 18px` 既不是 token 也不是裁定档
- 严重度: 中
- 证据: `workbench/server/static/workbench.css:1121` —— 基类 `button { … border-radius: 18px; … }`
- 违反: §4.1「圆角 `--r-md`（12px）」；night-paper-tokens §2.1 圆角五档（6/12/16/50%/999）无 18px 档
- 为什么是缺陷: 18px 是旧药丸残留，不在圆角 token 五档内；`button.primary` / `button.outline` 已用 `--r-md`(12px) 覆盖，但**不带变体类的普通按钮**仍继承 18px ⇒ 圆角语言分叉。
- 建议方向: 基类改 `border-radius: var(--r-md)`。

### A-08 · `#ai-chat-head` / `.agent-skill-row` 用墨色 token 当结构线
- 严重度: 中
- 证据: `workbench/server/static/agent-ui.css:20` —— `#ai-chat-head { … border-bottom: 1px solid var(--ink-strong); }`；`workbench/server/static/workbench.css:5239` —— `.agent-skill-row { … border-top:1px solid var(--ink-strong); }`
- 违反: §3.4「分层铁律：相邻两级靠圆角 + 柔影拉开，**不靠描边**」；结构线应走 `--rule-structure`/`--rule-hair`，**墨色 token 语义是文字不是线**
- 为什么是缺陷: `--ink-strong` 是正文墨色（近黑），拿它画 1px 全宽分割线会产生一圈刺眼黑边（正是 `design.md` D-2/D-13 记录的「运行卡/统计卡全带黑边」要消除的东西）。
- 建议方向: 换成 `border-bottom: 1px solid var(--rule-structure)`（或 `--rule-hair`）。

### A-09 · Agent 贴底输入区圆角 16px + 墨色描边，与 §4.6 composer 特例（12px/沉底/无强描边）不符
- 严重度: 中
- 证据: `workbench/server/static/agent-ui.css:128-137` —— `#ai-input-row.ai-input-row { … border: 1px solid var(--ink-strong); border-radius: 16px; … box-shadow: var(--elev-1); }`
- 违反: §4.6 特例（`pages.py:773` `#ai-input`）——贴底输入区 `border-radius: var(--r-md)`（12px）；§4.5「聚焦=蓝边 + 3px 蓝洗底光晕」；「不用描边」例外只许 `--rule-control`
- 为什么是缺陷: 16px 既不是 12px（`--r-md`）也不是 16px 的浮层档用途（那是 `--r-lg` 给浮层/抽屉/模态）；且用 `--ink-strong` 描边，读成黑框而不是控件边界。
- 建议方向: 圆角改 `--r-md`(12px)，边框改 `--rule-control` 或内发丝线。

### A-10 · `#ai-input:focus` 用 `:focus`（非 `:focus-visible`）、圆角 4px、且缺 §4.6 规定的「聚焦抬起 -2px + elev-2」
- 严重度: 中
- 证据: `workbench/server/static/agent-ui.css:149-153` —— `#ai-input:focus { outline: 2px solid var(--role-blue); outline-offset: 2px; border-radius: 4px; }`
- 违反: §3.2 焦点环（双环：内圈纸色 + 外圈 `--focus-outer`，且**鼠标点击不冒环**应用 `:focus-visible`）；§4.6 composer「聚焦时变蓝并轻微抬起 `transform: translateY(-2px)` + `--elev-2`」；圆角 4px 与行容器 16px 不一致
- 为什么是缺陷: 用 `:focus` ⇒ 鼠标点进输入框也会冒蓝环（spec 要求只键盘冒环）；`border-radius: 4px` 与外层 `#ai-input-row` 的 16px 打架，聚焦瞬间盒子形状突变；且完全没有实现 composer 规定的抬起反馈。
- 建议方向: 改 `:focus-visible` + 双环 `--focus-outer`，圆角对齐外层，补 `translateY(-2px)` + `--elev-2`。

### A-11 · Agent 焦点环走「单圈蓝 outline」，不是 §3.2 的双环口径
- 严重度: 中
- 证据: `workbench/server/static/agent-ui.css:83-87` —— `.ai-pending-handle:focus-visible, .ai-pending-actions button:focus-visible { outline: 2px solid var(--role-blue); outline-offset: 1px; }`
- 违反: §3.2 焦点环（`box-shadow: 0 0 0 2px var(--surface-base), 0 0 0 4px var(--focus-outer)` 双环；外圈用 `--focus-outer` 而非角色蓝）；§6.1 全局硬规则
- 为什么是缺陷: 用角色蓝画单圈 ⇒ ① 焦点指示被读成「选中/角色色」（§3.5 蓝是「当前选中」槽位）；② 单圈偏移 1px 在沉底/卡面上对比不足，双环（内纸色环 + 外蓝环）才在任意底面上可辨。
- 建议方向: 统一到全局 `.lk-focusable:focus-visible` 双环口径。

### A-12 · 工具调用卡/计划步的「进行中/完成/失败」只靠左边框颜色（无几何第二通道），且属 B 类未裁先实现
- 严重度: 中
- 证据: `workbench/server/static/agent-ui.css:175-186` —— `#ai-messages .ai-activity, #ai-messages .ai-plan { border-left: 3px solid var(--role-blue); background: var(--surface-sunken); }` / `.is-done { border-left-color: var(--role-yellow-deep); }` / `.is-failed { border-left-color: var(--role-red); }`
- 违反: §3.6 冗余状态通道（不得只靠颜色，须配几何：进行中=half、完成=filled、失败=cross/filled）；§4.30 工具调用卡 `tool-line` = **B 类**（须先改 OpenSpec 才实现）；§3.6 映射「已完成=蓝 filled」，此处完成用黄，与权威映射冲突
- 为什么是缺陷: 状态只有左边框颜色一个通道（蓝/黄/红），没有状态圆点几何，灰度/色觉下不可分；且「完成=黄」与 §3.6「已完成=蓝 filled」「当前·内容层才用黄」相悖；工具调用卡整块是 B 类形态，按纪律不该先实现。
- 建议方向: 状态改由 `.lk-dot`（几何 + 色）承载；工具调用卡形态等 `workbench-component-forms` change 裁定。

### A-13 · 闪卡用大偏移硬阴影 + 2px 近黑描边，违背「柔影分层 / 不描边」
- 严重度: 中
- 证据: `workbench/server/static/workbench.css:3131-3134` —— `.flash-card-face { border: 2px solid var(--ink-strong); … box-shadow: 5px 7px 0 rgb(17 19 24 / 14%); }`；`:3148`/`:3152` 翻开后两张卡 `box-shadow: 4px 9px 0 …` / `7px 10px 0 …`
- 违反: §3.4「分层铁律：靠圆角 + **柔影**拉开，不靠描边」；§4.18 卡片不描边、用 `--elev-1` 柔影；硬偏移 `0` 模糊阴影 = 装饰性硬阴影（decorative shadow）
- 为什么是缺陷: `5px 7px 0`（blur=0）是 neo-brutalism 式**硬投影**，不是 token 化的柔影（`--elev-*`）；再叠 2px 近黑描边，卡片读成贴纸/漫画框，与全站纸面分层语言脱节。
- 建议方向: 描边改内发丝线，阴影改 `var(--elev-1/2)` 柔影；如确需「两张牌错落」语义，位移用 transform、阴影仍走 elev token。

### A-14 · `!important` 覆盖 + 硬编码圆角（9px/10px）散落 agent-ui
- 严重度: 中
- 证据: `workbench/server/static/agent-ui.css:365`（`.ai-paper-approval-impact { color: var(--ink-strong) !important; }`）、`:373-379`（`.ai-paper-proposal-history { … border-radius: 9px !important; … }`）、`:397-403`（`.agent-artifact-card { … border-radius: 10px !important; border-left: 4px solid var(--role-blue) !important; … }`）
- 违反: §2.1 圆角统一 12px（无 9px/10px 档）；§4.30 形态裁定应由类承载而非 `!important` 强压
- 为什么是缺陷: 9px/10px 圆角不在五档 token 内（应 `--r-md` 12px）；用 `!important` 顶掉基类形态 ⇒ 将来改卡片语言时这几处不会跟随，正是 §4.30.3 第 5 条要消灭的「同一组件两套实现/改不动」。
- 建议方向: 去掉 `!important`，圆角归 `--r-md`，让特异性/源顺序自然生效。

### A-15 · `.part-card` 用 `currentColor` 描边 + 8px 圆角，卡片语言偏离裁定
- 严重度: 中
- 证据: `workbench/server/static/workbench.css:5244` —— `.part-card { padding: 18px; border: 1px solid currentColor; border-radius: 8px; min-width: 0; }`
- 违反: §4.18 卡片不描边（D-2）、圆角 `--r-md` 12px、`--elev-1` 柔影；`currentColor` 让边框色随文字色变化（不可控）
- 为什么是缺陷: `border: 1px solid currentColor` 的边框色取决于继承的文字色（可能是蓝/黄/红），卡片边界语义被内容色劫持；8px 圆角非 token 档；对比同页 `.card` 基类（12px + elev-1 + 无描边）⇒ 同一产品两种卡片语言。
- 建议方向: 去描边、改 12px、加 `--elev-1`，与 `.lk-card` 基类对齐。

### A-16 · `button.rate` 高 24px 且无命中补偿，点击目标 <44px
- 严重度: 高
- 证据: `workbench/server/static/workbench.css:1263-1272` —— `button.rate { height: 24px; min-width: 32px; padding: 0 8px; border-radius: 12px; … border: 1px solid var(--rule-control); }`（无 `::before`）
- 违反: §3.1 硬约束（命中区 ≥44×44）；§4.1 命中区下限
- 为什么是缺陷: 24px 视觉高、32px 最小宽，且没有伪元素把命中区撑到 44px（对比同文件 `button.primary::before`/`icon-only::before` 都补了）⇒ 评分档这类小按钮点击目标严重低于无障碍下限，且与同族不一致。
- 建议方向: 补 `::before { inset: -10px -6px }` 或容器间距补偿到 44px 中心距。

### A-17 · `.exam-bar` 进度条 10px/6px 圆角，未并入 §4.15「8px 胶囊」统一语言
- 严重度: 中
- 证据: `workbench/server/static/workbench.css:5275` —— `.exam-bar { display: block; height: 10px; border-radius: 6px; background: var(--surface-sunken, #0001); overflow: hidden; }`；对照权威实现 `:4403-4407` `.lk-progress { height: 8px; border-radius: var(--r-pill); background: var(--veil-active); }`
- 违反: §4.15 进度条 `progress-pill` 裁定 = **8px 胶囊**（`--r-pill`）；同文件 `:4401-4402` 自己写明「四条轨道一次改齐，**不留一族 8px、一族 10px、一族 12px 的中间态**」
- 为什么是缺陷: `.exam-bar` 正是那句要消灭的「10px + 6px 圆角」一族 ⇒ 进度条高度/圆角/底槽（`--surface-sunken` vs `--veil-active`）三处与权威 `.lk-progress` 都不同，进度语言分叉。
- 建议方向: 改成 `.lk-progress` 同款（8px + `--r-pill` + `--veil-active` 底槽），或直接复用该类。

### A-18 · `.solution-block` 局部圆角 `0 6px 6px 0`，未用 12px 档
- 严重度: 低
- 证据: `workbench/server/static/workbench.css:1423-1429` —— `.solution-block { border-left: 2px solid var(--rule-structure); padding: 4px 10px; … border-radius: 0 6px 6px 0; }`
- 违反: §2.1 圆角统一 12px（`--r-md`）；沉底/强调块圆角应与卡面同档
- 为什么是缺陷: 6px 属 `--r-xs`（微型标签底）档，被用在解析块这类内容容器上 ⇒ 圆角档位误用；且左直角右 6px 的非对称圆角在 12px 纸面语言里显得突兀。
- 建议方向: 改 `border-radius: var(--r-md)`（或明确登记为「左侧竖线 + 直角」的有意设计）。

### A-19 · 原生 `<select>` 34px 高 + 6px 圆角，与输入框 44px/12px 基线不一致（B 类待替换项，存疑）
- 严重度: 中（存疑）
- 证据: `workbench/server/static/workbench.css:1044-1049` —— `select { … height: 34px; … border-radius: var(--r-xs); … }`；对照输入框 `:1323-1328` `min-height: 44px; border-radius: var(--r-md)`
- 违反: §3.1 命中区 ≥44px（34px 低于下限）；§4.7 自绘下拉触发器「高 44px / 圆角 `--r-md`」（但 §4.30 标注 `select-spec` 为 **B 类**，8–9 处原生 `<select>` 尚未替换）
- 为什么是缺陷 / 存疑: 同屏输入框 44px、下拉 34px、圆角 12 vs 6 ⇒ 控件基线不一致，且 34px 低于 44px 硬约束。**但** §4.30 已把自绘下拉定为 B 类「先改 OpenSpec 再实现」，原生 select 的临时样式是已知过渡态，故标 **存疑**：究竟是「过渡期可接受」还是「当下就该补命中区」由所有者定。
- 建议方向: 过渡期先给 `select` 补 `min-height:44px` 命中补偿；根治仍走 `workbench-component-forms` 的自绘下拉替换。

### A-20 · 复选/单选「禁用且选中」把标记与底色都降为墨/纸色，蓝→灰语义跳变（存疑，已登记对比权衡）
- 严重度: 低（存疑）
- 证据: `workbench/server/static/workbench.css:2115-2124` —— `:disabled:checked { background: var(--ink-disabled); border-color: var(--ink-disabled); }`，标记改 `--surface-base`；注释自述对比 **3.59:1（暖）/3.61:1（夜）**，并说明原「沉底面 + ink-on-role」方案对比仅 **1.04:1** 会看不见白点
- 违反: §4.8/§4.9 checked = 蓝实心（选中语义走蓝 R1）；§3.6 几何不变但此处色通道从「蓝选中」跳到「中性墨禁用」
- 为什么是缺陷 / 存疑: 禁用+选中把「蓝实心选中盘」改成「灰实心盘」，选中语义在视觉上从蓝降为中性灰，与「选中=蓝」的整体语言不一致。**但** 注释已给出实测对比权衡（保持蓝白标记在沉底面上 1.04:1 不可辨），这是一处**有意识的取舍**而非疏漏，故标 **存疑**：建议所有者在「保蓝 vs 保标记可辨」间裁决，或改用「沉底面 + 蓝实心 + 深色勾」第三方案兼顾。
- 建议方向: 探索「保留蓝底 + 用深墨勾/白点」的第三方案，既保选中蓝语义又保标记 ≥3:1。

### A-21 · 模型切换下拉 `#ai-model-switch` 被 ID 规则压到 30px，命中区 <44px
- 严重度: 高
- 证据: `workbench/server/static/agent-ui.css:22-28` —— `#ai-model-switch { min-width: 0; height: 30px; … font-size: 12px; }`（元素为 `<select>`，`pages.py:1219`）
- 违反: §3.1 硬约束（命中区 ≥44×44）；§4.7 触发器「高 44px」；ID 特异度 (1,0,0) 压过 `select` 基类 34px
- 为什么是缺陷: ID 选择器把模型切换下拉强行压到 30px（比基类 34px 还矮），是全站最矮的可点控件之一，且低于 44px 不可让步线；同时它同屏紧邻 44px 的输入区 ⇒ 控件高度基线在同一视野内分叉。
- 建议方向: 去掉 `height:30px`（至少 `min-height:44px` 或补命中伪元素），与输入区高度对齐。

### A-22 · `#ai-input-row` 同屏混用「卡片描边 + 浮起柔影 + 沉底子件」，纸面层级 L1/L2/L3 乱用（存疑）
- 严重度: 中（存疑）
- 证据: `workbench/server/static/agent-ui.css:128-137` —— `#ai-input-row { border:1px solid var(--ink-strong); background: var(--surface-card); box-shadow: var(--elev-1); }`，而其内 `#ai-input`(`:138-148`) `background: transparent; border:0; box-shadow:none`，外层又 `border-radius:16px` / 内层 focus `border-radius:4px`
- 违反: §4.19 纸面四层 L0–L3 分工（L1 卡=输入框/列表项；L2 浮起=下拉/吐司/对话框）；§3.4「分层铁律靠圆角+柔影，不靠描边」
- 为什么是缺陷 / 存疑: 贴底输入区被做成「L1 卡 + 强描边 + L1 柔影」的混合体，圆角 16px(外)/4px(内聚焦) 两个非 12px 档并存 ⇒ 同一块上三层信号（描边/柔影/圆角跳变）打架。**存疑点**：贴底 composer 是 §4.6 特例，可能有意「抬升强调」，但当前实现既不是纯 L1 也不是纯 L2，形态归属不清。
- 建议方向: 明确 composer 归 L2 浮起（`--surface-raised` + `--elev-2` + 12px + 无强描边）或纯 L1，二选一，去掉强描边。

### A-23 · `.ai-paper-approval-order` 字号 10px，低于 11px micro 下限
- 严重度: 低
- 证据: `workbench/server/static/agent-ui.css:358-364` —— `.ai-paper-approval-order { … font-size: 10px; line-height: 15px; }`
- 违反: night-paper-tokens §2.3 字号阶（最小档 `--fs-micro` = **11px**；无 10px 档，且 micro「不得承载学习语义」）
- 为什么是缺陷: 10px 既不在字号阶内，也比 micro 下限还小一档；题号序这类**学习语义内容**用最小/超阶字号 ⇒ 可读性差且破坏字号阶。
- 建议方向: 升到 `--fs-micro`(11px) 或 `--fs-label`(12px)。

### A-24 · `.paper-options label` 与 `fieldset.problem-options > label` 两套选项行几何并存（A-115 要消灭的复发）
- 严重度: 中
- 证据: `workbench/server/static/workbench.css:5227` —— `.paper-options label { … align-items: baseline; border: 1px solid var(--rule-hair); border-radius: 8px; }`；对照 `:2009-2017` `fieldset.problem-options > label { … align-items:center; min-height:44px; border-radius: var(--r-md); }`（无 border）
- 违反: §4.30.3 第 5 条「同一组件两套实现」应合并；§4.8/§4.9 行级容器统一 12px + 44px 命中
- 为什么是缺陷: 同一产品里选项行有两套几何：一套 8px/描边/baseline（`.paper-options label`），一套 12px/无描边/center/44px（`fieldset.problem-options > label`，特异度 0,1,2 更高胜出）。后者覆盖前者，但前者仍是**活着的冲突源**——任何不在 `.problem-options` fieldset 内的 label 会掉回 8px/描边/baseline ⇒ 选中框挂在 baseline 上歪斜（`:2006-2007` 注释自述此风险）。
- 建议方向: 删除 `.paper-options label` 这套旧几何，或显式限定其作用域，避免两套并存。

### A-25 · 备考评分档焦点环又走「单圈蓝 outline」（A-11 同族，跨文件第二处）
- 严重度: 低
- 证据: `workbench/server/static/workbench.css:5262` —— `.rating-grade:focus-visible { outline: 2px solid var(--role-blue, #2668d8); outline-offset: 2px; }`
- 违反: §3.2 焦点环（双环 + `--focus-outer`，非角色蓝）；§6.1 全局硬规则；回落 `#2668d8` 非 token 值
- 为什么是缺陷: 与 `agent-ui.css:83-87`（A-11）同一毛病在另一文件复现：焦点用角色蓝单圈 ⇒ 焦点被误读为「选中」，且不走全局 `.lk-focusable` 双环口径；`#2668d8` 回落值不是任何 token（`--role-blue` 实为 `#2b62e8`）。
- 建议方向: 改用全局 `.lk-focusable:focus-visible` 双环；去掉非 token 回落值。

---

## 统计
共 **25** 条（高 8 / 中 13 / 低 4）。

- **高（8）**：A-01（未闭合花括号吞移动端媒体块）· A-02（11px 队列按钮命中区 <44px）· A-03（禁用态用 opacity）· A-04（评分档选中只靠颜色）· A-05（exam-prep 未定义 token 回落硬编码浅色，夜纸不翻转）· A-06（文字按钮无 44px 命中区）· A-16（`button.rate` 24px 无命中补偿）· A-21（模型下拉 30px <44px）
- **中（13）**：A-07（按钮基类 18px 圆角）· A-08（墨色 token 当结构线）· A-09（composer 16px + 墨描边）· A-10（`:focus` 冒环 + 4px 圆角 + 缺抬起）· A-11（单圈蓝焦点环）· A-12（工具卡状态只靠边框色 + B 类未裁先实现）· A-13（闪卡硬投影 + 近黑描边）· A-14（`!important` + 9/10px 圆角）· A-15（`.part-card` currentColor 描边 + 8px）· A-17（`.exam-bar` 10px/6px 未并入 8px 胶囊）· A-19（原生 select 34px/6px，存疑 B 类）· A-22（composer L1/L2/L3 混用，存疑）· A-24（选项行两套几何并存）
- **低（4）**：A-18（`.solution-block` 局部 6px 圆角）· A-20（禁用+选中蓝→灰语义跳变，存疑取舍）· A-23（10px 字号低于 micro 下限）· A-25（备考档单圈蓝焦点环）

> 严重度口径：**高** = 违反不可让步硬约束（§3.1 命中区 / §3.2 焦点环 / §3.6 冗余通道）或破坏主题/语法；**中** = 形态裁定偏离、圆角/描边/层级语言分叉、B 类未裁先实现；**低** = 局部档位误用、有意识取舍的存疑项。存疑项（A-19 / A-20 / A-22）已在条目内说明两难，未硬凑为确定缺陷。

---

## E 类 · 交互流程合理性（由 A 组顺带发现）
**本次未记录 E 类条目。** 原因：A 组**无浏览器工具**（无 `mcp__node_repl__js` / Playwright 工具面，且协调方明令禁止再尝试起浏览器），无法「真点过」任何操作路径；E 类硬约束是「必须真点过、禁止臆断」。为不污染 C agent 主责结论，此处只留说明、不臆造条目。建议由主会话或 C agent 在可视化环节覆盖。

---

## 服务渲染与分支不一致（非设计缺陷）
本次为**纯静态审计**（未起服务、未渲染页面），所有证据均直接来自源码文件行，故不存在「服务渲染了旧版 pages.py」导致的误判。若主会话在可视化时于左栏看到「设置套设置」「优先回看带计数徽标」「题面带『来源：』」等现象，按协调方指示应归入「服务解析回旧检出」而非本报告的设计缺陷，不在 A 组 25 条内。

---

## 复核说明（诚实汇报）
- 每条引用的 `文件:行号` 均已用 Read 当场确认当前行号与内容一致（A-01 的花括号计数用 Python 实测 99/98；A-05/A-21/A-25 的「未定义 token」用全仓 grep 确认 `--radius-md`/`--ink-line`/`--surface`/`--text` 零定义）。
- 图谱区段（`workbench.css` 冻结块，约 4700–5200 行）按 §5.6「不替换、不重绘」豁免，其中的硬编码色/圆角/`--green`（`:4754`）**未**计为缺陷。
- A-19 / A-20 / A-22 标注「存疑」，是因它们分别落在「B 类待替换过渡态」「已登记的对比取舍」「§4.6 特例形态归属」三处两难地带，按任务书不硬凑为确定缺陷。
