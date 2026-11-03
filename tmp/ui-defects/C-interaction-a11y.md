# C 组 · 交互·状态·可达性·焦点·命中区缺陷审计

只读静态审计（Read / Grep / Glob），未起浏览器、未跑服务、未改任何仓库文件。
权威依据：component-spec §3.1（命中区 ≥44×44）/ §3.2 焦点环 / §3.3 动效 / §3.6 冗余状态通道 / §4.30；live spec `openspec/specs/workbench-ui/spec.md`。
实现落点：`workbench/server/static/*.css|*.js`、`workbench/server/pages.py`。

> 审计口径说明：行号与内容均已 Read 确认；命中区为**静态盒模型推算**（含 base class 继承与同特异度源顺序），分不清的标「存疑」。`:where()` 特异度回归本轮**未复现**——`:where()` 仅出现在注释（`workbench.css:1220-1224`），形态高度写在 (0,1,1) 变体规则里，当前无零特异度命中区规则被 base 盖住，故不报。

---

### C-01 · 队列拖拽手柄仅 24×24，无命中区补偿
- 严重度: 高
- 证据: `workbench/server/static/agent-ui.css:76-82` —— `.ai-pending-handle { width: 24px; min-width: 24px; padding: 0; cursor: grab; touch-action: none; }`；markup `workbench/server/static/workbench.js:4231-4237`（`<button class="ai-pending-handle">↕</button>`，可拖拽 + 方向键重排）
- 违反: §3.1 命中区 ≥44×44 硬约束
- 为什么是缺陷: 这是一个可点、可拖、可键盘方向键操作的核心控件，命中区只有 24×24，且未用伪元素撑到 44×44，也无 §3.1「方法 2」的中心距补偿声明；手指/鼠标都极难点准。
- 建议方向: 视觉 24px 保留，加 `::before{content:"";position:absolute;inset:-10px}` 把命中区补到 44×44（该按钮无相邻命中目标争抢）。

### C-02 · `.part-details`（详情）按钮约 22px，且是 hover 才出现的次级控件
- 严重度: 高
- 证据: `workbench/server/static/workbench.css:5253` —— `.part-details { font-size: .75em; padding: 3px; }`；markup `workbench/server/static/part-practice.js:83`（`<button class="part-details">详情</button>`）
- 违反: §3.1 命中区 ≥44×44
- 为什么是缺陷: 「各小问做题情况」的唯一入口按钮，12px 字号 + 3px 内距 ⇒ 命中区约 22×22，远低于 44×44，且无伪元素补偿。属任务书提到的「题号格详情按钮」同族残留（落在 `part-practice.js` 而非题号格，仍存活）。
- 建议方向: 至少 `min-height:44px;min-width:44px`（或 `::before` inset 补偿）；字号提到 §4 控件档位。

### C-03 · `.ai-pending-actions button` 命中区约 27px
- 严重度: 高
- 证据: `workbench/server/static/agent-ui.css:101` —— `.ai-pending-actions button { margin: 0; padding: 4px 7px; font-size: 11px; }`（继承基类 `button{padding:0 15px;height:36px}` 被本块 4px 竖内距覆盖 ⇒ 高 ≈ 27px）
- 违反: §3.1 命中区 ≥44×44
- 为什么是缺陷: 队列候选消息的「编辑/删除/上移/下移」等操作按钮，命中区约 27×27；多条消息纵向堆叠时间距由 grid `gap:5px`（`agent-ui.css:71`）决定，不满足 §3.1 方法 2 的中心距 ≥44px。
- 建议方向: 提到 `.sm` 档（28px 视觉 + 容器间距）或直接 `min-height:44px`，并把 grid gap 提到 ≥16px。

### C-04 · Agent 活动浮层收起/展开按钮 28×28，无命中区补偿、焦点环缺内环
- 严重度: 高
- 证据: `workbench/server/static/agent-ui.css:259-260` —— `.agent-aux-collapse, .agent-activity-toggle { width: 28px; padding: 0; }`（基类 `height:36px` 未被覆盖 ⇒ 高 36，宽 28）；markup `workbench/server/pages.py:377-378`、`:365-366`
- 违反: §3.1 命中区 ≥44×44（无 40×40 + 伪元素补偿，区别于 §4.4 图标按钮）；§3.2 焦点环
- 为什么是缺陷: 两个纯符号（`−` / `+` / `×`）图标按钮命中区 28×36，未走 §4.4 的「40×40 + `::before` inset:-2px」口径；且未声明 `:focus-visible` 内环，弱化于 spec 的双环。
- 建议方向: 统一挂 `button.icon-only` 形态（40×40 + 命中区伪元素 + 全局单圈焦点环）。

### C-05 · 图谱页图标按钮 34×34、缩放按钮 36×36、过滤 chip / 分段按钮 ~23–25px，集体低于 44×44
- 严重度: 高
- 证据: `workbench/server/static/workbench.css:4828-4831`（`.graph-topbar .icon-btn{height:34px;min-width:34px}`）、`:5040-5044`（`.zoom button{width:36px;height:36px}`）、`:4990-4993`（`.chip{padding:5px 8px;font-size:9px}` ⇒ 高 ≈23px）、`:4820-4823`（`.graph-topbar .seg button{padding:6px 9px;font-size:10px}` ⇒ 高 ≈25px）；markup `workbench/server/pages.py:796-797,809`
- 违反: §3.1 命中区 ≥44×44
- 为什么是缺陷: 聚焦/适应/缩放/过滤/分段都是图谱高频操作，命中区 23–36px 且**无伪元素、无中心距补偿声明**。其中缩放按钮 36×36 是裸值，连「题号格 36px+8px 间隙=44 步距」的补偿法都不满足（缩放两键 gap 仅 6px，中心距 42px）。
- 建议方向: 图谱页豁免视觉 token，但 §3.1 是「唯一不可让步」硬约束 ⇒ 用伪元素把命中区补到 44×44（不影响图谱视觉）。

### C-06 · 图谱图例项 `.legend-item` 约 17px 高，且关闭态只靠 opacity
- 严重度: 高
- 证据: `workbench/server/static/workbench.css:5025-5033` —— `.legend-item{padding:2px 4px;font:inherit}`（继承 9px 字号 ⇒ 高 ≈17px）；`.legend-item.off { opacity: .34; }`
- 违反: §3.1 命中区 ≥44×44；§3.6 冗余状态通道（live spec「Redundant state cues」）
- 为什么是缺陷: 图例项是可点开/关的过滤开关，命中区约 17px（全站最小）；「关闭」态只靠 `opacity:.34` + `i` 灰度滤镜，**颜色/透明度是唯一载体**，无几何形状、无 `aria-pressed`。
- 建议方向: 命中区补到 44×44；关闭态加几何通道（如划掉线 `::after`）+ `aria-pressed`。

### C-07 · 焦点环存在三套并存口径，违背 §3.2 统一 token
- 严重度: 中
- 证据: `workbench/server/static/workbench.css:4980`（`.control-toggle:focus-visible{outline:2px solid #d3a914;outline-offset:1px}`）、`:5031`（`.legend-item:focus-visible{outline:2px solid #d3a914;outline-offset:1px}`）、`:5262`（`.rating-grade:focus-visible{outline:2px solid var(--role-blue,#2668d8);outline-offset:2px}`）、`agent-ui.css:83-87`（`.ai-pending-handle:focus-visible,…{outline:2px solid var(--role-blue);outline-offset:1px}`）vs 全局基线 `workbench.css:3289-3292`（`:focus-visible{outline:var(--focus-width) solid var(--focus-outer);outline-offset:var(--focus-offset)}`，2px/2px）
- 违反: §3.2 焦点环（全局单圈 `--focus-outer` / 2px / 2px 偏移）；live spec「Focus visibility and contrast floors」
- 为什么是缺陷: 同一应用里并存三套焦点环——图谱黄 `#d3a914`/偏移 1px、备考蓝/偏移 2px、Agent 蓝/偏移 1px、全局 `--focus-outer`/偏移 2px。键盘用户在不同区段看到不一致的焦点表达，且 1px 偏移档未走 token、无对比度下限保证。
- 建议方向: 统一到 `:focus-visible{outline:2px solid var(--focus-outer);outline-offset:2px}` 单圈（spec 明确「图谱页 token 不碰」可保留图谱特例，但应登记裁决而非各写一套）。

### C-08 · `#ai-input` 用 `:focus` 而非 `:focus-visible` ⇒ 鼠标点击冒焦点环
- 严重度: 中
- 证据: `workbench/server/static/agent-ui.css:149-153` —— `#ai-input:focus { outline: 2px solid var(--role-blue); outline-offset: 2px; border-radius: 4px; }`
- 违反: §3.2（spec 反复强调「**鼠标点击不冒环**」「只改 `:focus-visible`」，见 `workbench.css:1345`、`:2926` 注释）；live spec「Focus visibility」
- 为什么是缺陷: Agent 贴底输入区是全站唯一在 `:focus`（而非 `:focus-visible`）上画环的输入控件，鼠标点进去会冒蓝环，与 `textarea/input/#answer-box`（均已改 `:focus-visible`，`workbench.css:1347`、`:2927`）不一致；且用 `--role-blue` 而非 `--focus-outer`。
- 建议方向: 改成 `#ai-input:focus-visible` 并换用 `--focus-outer` 单圈，与全局对齐。

### C-09 · `select:focus` 只改边框色，键盘聚焦无可见焦点环
- 严重度: 中
- 证据: `workbench/server/static/workbench.css:1055` —— `select:focus { border-color: var(--role-blue); }`（同段 `:1059` 才是 `select:focus-visible` 画环）
- 违反: §3.2 焦点环不可压死/不可缺失；WCAG 2.4.7 Focus Visible
- 为什么是缺陷: `select:focus`（含鼠标与程序化聚焦）只把 1px 边框染蓝，不画 `--focus-outer` 环；`select` 默认是替换元素，UA 默认焦点环常被 `border-color` 覆盖后不明显的场景下，键盘用户可能看不到聚焦位置。属「焦点表达仅靠 1px 边框色」的弱表达（存疑：`select:focus-visible` 在 :1059 有补环，键盘 Tab 应能拿到，故严重度中）。
- 建议方向: `select:focus-visible` 与 `:focus` 统一走 `--focus-outer` 单圈，去掉只染边框的弱表达。

### C-10 · 时间线/计划步骤状态点 running 与 done 共用「filled」几何，仅颜色区分
- 严重度: 中
- 证据: `workbench/server/static/workbench.css:2648-2654` —— `.ai-plan-step.is-running .ai-plan-marker{background:var(--role-blue);box-shadow:none;animation:ai-plan-pulse}`、`.is-done{background:var(--role-yellow);box-shadow:none}`、`.is-failed{background:var(--role-red);box-shadow:none}`；`agent-ui.css:284-295`（`.agent-milestone.is-running/.is-done/.is-failed .agent-milestone-marker` 同为实心圆）
- 违反: §3.6 冗余状态通道（状态 → 色+几何唯一映射；进行中=蓝+`half` 半填充，已完成=蓝+`filled` 实心）
- 为什么是缺陷: running / done / failed 三态的几何都是**实心圆**（filled），仅靠蓝/黄/红区分。§3.6 要求「进行中」用 `half`（半填充）、「已完成」用 `filled`，且「不得有两条状态共用同一组合」。灰度打印/色觉障碍下 running 与 done 无法区分（文字标签「进行中/已完成」在 `agent-ui.js:129-133` 有补，但几何第二通道缺失）。
- 建议方向: running 改 `half`（`box-shadow: inset -5px 0 0 0 currentColor` 造半圆），done 保持 filled，failed 保持 filled+红，几何与色同时区分。

### C-11 · 工具调用卡/计划步骤状态只靠**左边条颜色**，无几何第二通道
- 严重度: 中
- 证据: `workbench/server/static/agent-ui.css:183-186` —— `#ai-messages .ai-activity.is-done, .ai-plan-step.is-done { border-left-color: var(--role-yellow-deep); }`、`.is-failed { border-left-color: var(--role-red); }`（默认蓝 `:178`）
- 违反: §3.6 冗余状态通道；live spec「Color SHALL NOT be the only carrier of … interaction state」
- 为什么是缺陷: Tool Call Card 的 running/done/failed 完全由 3px 左边条的颜色承载，形状（边条）、粗细、位置都一样 ⇒ 状态无几何冗余。灰度下 done（黄）与默认（蓝）几乎同灰度，键盘/读屏用户若不读文字难以区分。存疑：卡内 `.ai-plan-state` 文字与 `is-failed .ai-plan-state` 红字（`workbench.css:2665`）提供了文字冗余，故严重度中而非高。
- 建议方向: 左边条改「色 + 几何」（如 done 用 `filled` 点、failed 用 `cross`），或按 §3.6 给每态一个形状标记。

### C-12 · 图谱过滤 chip 是开/关切换按钮，但无 `aria-pressed`、无可见选中态文字冗余
- 严重度: 中
- 证据: `workbench/server/pages.py:809-812` —— `<button type='button' class='chip{ active}'>…`（无 `aria-pressed`）；选中态 `workbench.css:4994-4997` —— `.chip.active{background:var(--blueSoft);…;box-shadow:inset 0 -2px 0 var(--blue)}`
- 违反: §3.6 冗余状态通道；live spec「Active navigation … SHALL retain text, outline, position, or another geometric cue」；WCAG 4.1.2
- 为什么是缺陷: 过滤 chip 是标准的开关（toggle）语义，但既没有 `aria-pressed`，选中态也只靠蓝底 + 2px 蓝下边线（无文字/形状冗余、无位置指示）。读屏用户完全无法得知某个过滤是否已启用。
- 建议方向: 加 `aria-pressed`，选中态在颜色之外加几何通道（如下边线已有 ⇒ 再补 `aria-pressed` + 文字权重变化即可达标）。

### C-13 · Agent 队列/状态区无 `aria-live`，排队与发送状态变化读屏无感
- 严重度: 中
- 证据: `workbench/server/static/agent-ui.css:61`（`#ai-queue-status`）、`:158-163`（`#ai-status`）、`:40-46`（`.ai-handoff-status`）—— 三个状态区**均未设 `aria-live`**；全文 grep `aria-live` 在 `agent-ui.js` 命中 0（对比 `practice-flow.js:2068`、`part-practice.js:49,54` 均已设）
- 违反: live spec「Explicit collapse / Agent sending is single-flight」配套的状态可见性；WCAG 4.1.3 Status Messages
- 为什么是缺陷: `#ai-queue-status` 会写入「队列已暂停；继续后会按顺序发送。」（`workbench.js:4198-4202`）、`#ai-status` 承载发送/失败等状态，但都不是 live region ⇒ 状态只对看得见的人可见，读屏用户得不到任何通知。
- 建议方向: 给 `#ai-queue-status` / `#ai-status` / `.ai-handoff-status` 加 `aria-live="polite"`（`role="status"`）。

### C-14 · 评分卡校验失败后焦点不移动，错误只靠 aria-live 广播
- 严重度: 中
- 证据: `workbench/server/static/practice-flow.js:2069-2078` —— `showCardError` 只 `error.textContent=…; error.classList.remove("hidden")`，无 `focus()`；`error` 在 `:2065-2068` 建为 `aria-live="polite"` 但从未成为聚焦目标
- 违反: WCAG 3.3.1 Error Identification / 2.4.3 Focus Order；live spec「Dynamic practice controls are accessible」
- 为什么是缺陷: 点「保存评价」若未选质量，错误段落被 aria-live 读出但焦点仍停在按钮上，键盘用户必须反向 Tab 才能定位错误文本；无 `role="alert"` 也无焦点管理。
- 建议方向: 校验失败时把焦点移到错误段落（`tabindex="-1"` + `focus()`）或回焦到缺失的评分控件。

### C-15 · `.part-preview` 浮层 hover/focus 出现，但仅 Escape 可关，无点击外部关闭，关闭通道不一致
- 严重度: 中
- 证据: `workbench/server/static/part-practice.js:85` —— `wrap.addEventListener('mouseenter',show); …('focusin',show); wrap.addEventListener('keydown',…Escape…); details.addEventListener('click',…pinned…)`；全局 `:88` —— `document.addEventListener('keydown',…Escape…querySelectorAll('.part-preview').forEach(hide))`
- 违反: 交互一致性（Escape/键盘行为不一致）；live spec「Saved paper cards fold」配套的可控性
- 为什么是缺陷: 浮层出现通道是 hover + focusin，但消失通道**只有** Escape（全局或 wrap 内）或再点「详情」——没有点击浮层外部关闭、没有 mouseleave 之外的兜底。同一应用里 Agent 工件预览靠「关闭 ×」按钮、图谱浮层另有通道 ⇒ 关闭交互三处三套。鼠标用户误触后不易关掉。
- 建议方向: 统一「点击外部关闭 + Escape + 显式关闭钮」三通道，或至少给浮层补 click-outside。

### C-16 · `.flash-answer-reveal` 620ms 关键帧动画超过 §3.3 上限
- 严重度: 低
- 证据: `workbench/server/static/workbench.css:3153` —— `animation: flash-answer-reveal 620ms cubic-bezier(.2,.75,.2,1) both;`（关键帧 `:3155-3159`）；§3.3 时长表上限为里程碑 700ms、其余 ≤240ms/517ms
- 违反: §3.3 动效（翻转属「视图转场」应 240ms，620ms 无对应裁定档）
- 为什么是缺陷: 闪卡答案揭示动画 620ms 既不是 240ms 视图转场，也不在 517ms 回弹/700ms 里程碑档内，属超时长档；且它是**几何位移+旋转**，弱动效档下被 `animation-name:none` 直接砍成终态（`workbench.css:4613`）⇒ 有动效偏好者与无偏好者看到的状态切换差异较大。存疑：可能是刻意的「庆祝/仪式」感，但未登记到 §3.3 时长表。
- 建议方向: 归到 240ms 视图转场档，或登记为 ceremony 档并写明理由。

### C-17 · 图谱区焦点环用硬编码 `#d3a914`、控件用裸 hex，未接 `--focus-outer`
- 严重度: 低
- 证据: `workbench/server/static/workbench.css:4980`、`:5031`（`outline:2px solid #d3a914`）；同区控件裸 hex 边框 `:4817`（`#d9d3c8`）、`:4991`（`#d7d1c6`）、`:5041`（`#d8d2c6`）
- 违反: §3.2 焦点环 token（`--focus-outer`/`--focus-inner`）；live spec「Focus visibility and contrast floors」
- 为什么是缺陷: 焦点环颜色写死 `#d3a914`（黄），未走 `--focus-outer`，在图谱浅底上对比度未被任何下限约束（spec 明确「图谱页 token 不碰」是**视觉 token** 豁免，但 §3.1/§3.2 是「唯一不可让步」）。偏移 1px 也与全局 2px 不一致。
- 建议方向: 焦点环至少换 `--focus-outer` 或登记图谱特例并做对比度校验；偏移统一 2px。

### C-18 · `.sm` 档按钮命中区仅 28px，调用点未逐点保证 §3.1 方法 2 的 44px 中心距
- 严重度: 中
- 证据: `workbench/server/static/workbench.css:1231`（`button.sm{height:28px;…}`）、`:1241-1242`（`button.primary.sm::before, button.outline.sm::before{content:none}` ⇒ 命中区伪元素被整体关掉）；调用点如 `workbench/server/static/practice-flow.js:2055`（`<button class="primary sm">保存评价</button>`）、`:1636-1637`（`<button id="filter-clear" class="ghost sm">` / `<button id="filter-close" class="outline sm">`）
- 违反: §3.1 命中区 ≥44×44（方法 2：相邻命中区中心距 ≥44px）
- 为什么是缺陷: `.sm` 档视觉 28px 且**主动删除了命中区伪元素**，把达标责任完全交给「容器间距」。代码注释声称「每个 `.sm` 调用点的中心距都已实测（报告 §6.3）」，但 `filter-clear`/`filter-close` 这类并排文字按钮（`gap` 由父容器决定）与评分卡 `primary sm` 的实际中心距**无法从代码静态证明 ≥44px**。凡中心距不足的调用点即为硬约束违规。
- 建议方向: 对每个 `.sm` 调用点显式声明/校验中心距；给不出 44px 的改用默认 40px 形态（注释已写明该规则，需落实到 `ghost sm` / `primary sm` 全部调用点）。存疑：部分调用点可能确已满足，需实测才能逐点定性。

### C-19 · Agent 里程碑状态文本依赖 JS 注入，初始/无 JS 下状态无几何冗余
- 严重度: 低
- 存疑: 缺陷 vs 有意设计
- 证据: `workbench/server/static/agent-ui.js:122-133` —— `.agent-milestone-marker` 形状（`✓`/`!`/`·`）与 `.agent-milestone-state` 文字（已完成/失败/进行中）**均由 JS `textContent` 写入**；marker 元素本身无静态文本、无 `aria-label`
- 违反: §3.6 冗余状态通道（几何 + 宿主 `aria-label`，零可见状态文字）
- 为什么是缺陷: 里程碑已是「几何(✓/!/·) + 文字」双通道，符合 §3.6 零文字要求的精神；但状态完全依赖 JS 渲染，`marker` 未设 `aria-label`（任务书提到「里程碑已改几何+aria-label」，此处实测 marker 只有 `textContent`，**没有** `setAttribute("aria-label", …)`）⇒ 读屏拿到的是符号字符而非语义状态。
- 建议方向: 给 `.agent-milestone-marker` 补 `aria-label`（如「已完成」）或 `role="img"`；若确已在他处登记为已修，则本条按「残留未改到 marker 元素」报。

### C-20 · 图谱图例/分段/chip 控件字号 9–10px，可点目标文字过小（可读性 + 命中区连带）
- 严重度: 低
- 证据: `workbench/server/static/workbench.css:4992`（`.chip{font-size:9px}`）、`:4822`（`.graph-topbar .seg button{font-size:10px}`）、`:5023`（`.legend{font-size:9px}`，图例项 `font:inherit`）
- 违反: §3.1（命中区连带过小）；live spec「Controls and metadata SHALL remain visually secondary」的下限边界
- 为什么是缺陷: 过滤 chip、分段切换、图例项文字 9–10px，是全站最小的一批可点文字；文字盒过小直接压低命中区（与 C-05/C-06 叠加）。作为「次要控件」可以小于正文，但 9px 已低于常见可读下限，且未在 §4.30 形态表登记为允许档。
- 建议方向: 提到 ≥12px，或登记图谱页字号特例；同时按 C-05/C-06 把命中区补到 44×44。

---

## 统计

共 **20** 条（高 6 / 中 9 / 低 5）。

| 编号 | 严重度 | 一句话标题 |
|---|---|---|
| C-01 | 高 | 队列拖拽手柄仅 24×24，无命中区补偿 |
| C-02 | 高 | `.part-details`（详情）按钮约 22px |
| C-03 | 高 | `.ai-pending-actions button` 命中区约 27px |
| C-04 | 高 | Agent 活动收起/展开按钮 28×28，无补偿、焦点环缺内环 |
| C-05 | 高 | 图谱页图标/缩放/过滤/分段按钮集体低于 44×44 |
| C-06 | 高 | 图例项约 17px 高，关闭态只靠 opacity |
| C-07 | 中 | 焦点环三套并存，违背 §3.2 统一 token |
| C-08 | 中 | `#ai-input` 用 `:focus` 而非 `:focus-visible` ⇒ 鼠标冒环 |
| C-09 | 中 | `select:focus` 只染边框，键盘聚焦无焦点环 |
| C-10 | 中 | 计划步骤 running/done 共用 filled 几何，仅颜色区分 |
| C-11 | 中 | 工具调用卡状态只靠左边条颜色，无几何第二通道 |
| C-12 | 中 | 过滤 chip 无 `aria-pressed`、选中态无文字/形状冗余 |
| C-13 | 中 | Agent 队列/状态区无 `aria-live` |
| C-14 | 中 | 评分卡校验失败后焦点不移动 |
| C-15 | 中 | `.part-preview` 浮层仅 Escape 可关，关闭通道不一致 |
| C-16 | 低 | `.flash-answer-reveal` 620ms 超时长档 |
| C-17 | 低 | 图谱焦点环硬编码 `#d3a914`，未接 `--focus-outer` |
| C-18 | 中 | `.sm` 档命中区 28px，中心距 ≥44px 未逐点证明 |
| C-19 | 低 | Agent 里程碑 marker 无 `aria-label`，状态靠 JS 符号字符 |
| C-20 | 低 | 图例/分段/chip 字号 9–10px 过小 |

### 诚实汇报与边界
- **本轮未复现 `:where()` 特异度回归**：`:where()` 仅出现在 `workbench.css:1220-1224` 的注释里（spec 明确「实测已否、不许用」），形态高度写在 (0,1,1) 变体规则（`button.primary`/`button.outline` `height:40px`）、`.sm` 与 `.icon-only` 均排在正确源顺序位 ⇒ 当前**无零特异度命中区规则被 base class 盖住**的活跃缺陷，故不报假阳性。
- **已清理项确认未回归**：题号格（`.paper-dot`，`workbench.css:5134-5216`）六态均有「颜色+几何角标（勾/叉）」双通道，符合 §3.6；36px 格 + 8px gap = 44px 步距达标；详情按钮不在题号格里（同族残留见 C-02，落在 `part-practice.js`）。
- **命中区为静态盒模型推算**（含 base `button{height:36px;padding:0 15px}` 继承与同特异度源顺序覆盖）；`box-sizing` 全局值未逐条核对，个别 1–2px 误差可能存在，不影响「<44×44」的定性。
- **审计边界**：本组为纯静态审计，未起浏览器、未跑服务；`workbench.js`（6367 行）按关键词定向取证，非逐行全读；Agent 侧会话/发送/单飞等运行时流程不在本组范围。
