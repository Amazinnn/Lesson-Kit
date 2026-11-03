# UI-D · 页面信息架构·空态·加载·导航·响应式缺陷审计报告

> 审计员：D 组（信息架构与页面结构）。只读审计，未改动任何仓库文件。
> 权威依据：`openspec/changes/workbench-visual-language-v2/design-notes/layout-spec.md`、同目录 `component-spec.md` §4.19/§4.21/§4.22/§4.23/§4.28、live spec `openspec/specs/workbench-ui/spec.md`。
> 实现落点：`workbench/server/pages.py`、`workbench/server/records.py`、`workbench/server/static/workbench.js`、`workbench/server/static/workbench.css`。
> 审计方式：**纯静态读代码**（Read/Grep）。本环境无 Playwright 浏览器工具（`browser_use` 技能存在但无可调用的 `mcp__node_repl__js` 函数、`ZCODE_PLUGIN_ROOT` 未设），依协调者改指令「禁止起浏览器」，全部条目为静态审计，可视化核验由主会话负责。
> 范围外：图谱**节点画法**（graph-node-visual-language 另案、算法冻结）不报；**壳层右栏面板（graph-detail-panel）在范围内**，已报。

---

### D-01 · 图谱右栏看板（选中态）渲染 8 个区块 + 禁止的图谱参数，而非「名称 + 提醒 + 一个链接」
- 严重度: 高
- 证据: `workbench/server/static/workbench.js:2484-2503` —— `graphDetail.innerHTML = "<div class='eyebrow'>Knowledge Point</div>" + <h3 title> + "<div class='id'>" + node.id + "</div>" + <state-pill> + <section 学习概况 metric 关联题目/直接关系> + <section 直接关系 rel-list 强/中/弱> + <section 说明 布局…port 与 lane> + <a 打开知识点>`
- 违反: live spec「Graph detail is a learning dashboard」（spec.md:408）「Selecting a graph node SHALL show **only** its readable title, concise action reminder, and one link to the formal knowledge-point page. Full evidence … SHALL NOT be repeated as student-facing graph parameters.」；同 spec.md:413「the right panel shows its name, any applicable 重点练习/可以复习 reminder, and one 打开知识点 link」
- 为什么是缺陷: 现状把原始 node.id、掌握状态、关联题数、直接关系数、逐条关系**强度（强/中/弱）**、甚至一段布局实现说明全部铺给学生，正是该条明令禁止「作为学生可见图谱参数重复」的东西；信息架构上右栏从「简洁看板」变成「调试面板」，抢走学习锚点。
- 建议方向: 收敛到名称 + 适用时的 `重点练习/可以复习` 提醒 + 单个 `打开知识点` 链接；删除 eyebrow/raw id/状态药丸/指标行/关系强度列表/布局说明。

### D-02 · 图谱看板空态自贴「掌握状态·关联题数·关系强度」承诺，与「仅名称+提醒+链接」相矛盾
- 严重度: 高
- 证据: `workbench/server/pages.py:843-845` —— `<aside id='graph-detail-panel' …><p class='side-label'>学习看板</p><h2>选择一个节点</h2><p class='muted'>点击图中的知识点，查看掌握状态、关联题数与关系强度。</p>`
- 违反: live spec「Graph detail is a learning dashboard」（spec.md:408/413）；live spec「Graph does not duplicate content editing」（spec.md:435）
- 为什么是缺陷: 空态文案主动承诺展示「掌握状态/关联题数/关系强度」，而权威要求右栏只给名称+提醒+链接；空态在引导用户期待被禁止的参数，且未按 §4.21 用「插画 + 一句 + 主按钮」，而是堆了一行说明文字 + 自贴「学习看板」分区标签。
- 建议方向: 空态改为「选择一个节点查看它的名称与回看提醒」级别的单句，去掉对掌握状态/题数/关系强度的承诺；或按 §4.21 用静物插画 + 一句。

### D-03 · 记录中心能力估计把原始 kp_id 当主文本、并暴露原始能力分 theta
- 严重度: 高
- 证据: `workbench/server/records.py:742-746` —— `f"<li><span class='exam-kp'>{html.escape(row['kp_id'])}</span><span class='exam-theta'>{row['theta']:.0f}</span>…"`；容器标题 `records.py:789`「掌握度估计（能力分）」
- 违反: live spec「Knowledge point list page」（spec.md:109）「use each knowledge point's **readable name as primary text** and show raw identifiers only as secondary context」；live spec「Knowledge point display page」（spec.md:75）「Raw signal and scheduler parameters SHALL not be shown.」
- 为什么是缺陷: 能力估计行把 `kp_id`（如 `kp-0042`）放在首位、可读名缺位，学生要解码 id 才知道是哪个点；同时把原始能力分 `theta` 直接示人，属「raw signal」外露。
- 建议方向: 主文本换 `knowledge_item` 可读名（`row` 里补 name，或用 `kp_titles` 映射），raw id 降为次要/`data-*`；能力分若要保留，用分档词而非裸 theta。

### D-04 · 顶栏段一→段二分隔仍是字面 `/` 文字，未换成 1px 竖向结构线
- 严重度: 中
- 证据: `workbench/server/pages.py:299` —— `<span class='topbar-separator'>/</span>`；`workbench/server/static/workbench.css:686` —— `.topbar-separator { color: var(--graph-page-caption, var(--ink-faint)); }`
- 违反: layout-spec §2.2 段一「补 **1px 竖向结构线** 取代字面 `/`」
- 为什么是缺陷: 分隔符用字面 `/` 字符 + 灰色文字，是文本语气而非结构线；layout-spec 已裁定改为 1px 竖线（与三栏 1px `--rule-hair` 同族），现状仍是斜杠字符。
- 建议方向: 用 1px×18px 的 `--rule-hair` 竖线元素替换 `/` 文字（对应 layout-spec §2.1 线框「竖向结构线 1px×18px」）。

### D-05 · 顶栏三色标记与产品名间距 44px（margin 34 + gap 10），spec 收到 10px 未落地
- 严重度: 中
- 证据: `workbench/server/static/workbench.css:671-681` —— `#topbar .brand::before { … margin-right: 34px; }`；`workbench.css:669` —— `#topbar .brand { … gap: 10px; }`
- 违反: layout-spec §2.2 段一「三色标记与文字的间距从现状 `margin-right:34px` + `gap:10px`（合计 44px）收到 **10px**」
- 为什么是缺陷: 顶栏最左的品牌标记与 `lesson-kit` 文字之间留 44px 空白，品牌段被无谓拉宽、挤压段二/段三；layout-spec 已明确收到 10px。
- 建议方向: `#topbar .brand::before { margin-right: 0 }`（靠 `.brand` 的 `gap:10px` 即 10px 总距）。

### D-06 · 章节透镜兜底 `<select>` 以「1px 深墨边框 + 4px 圆角」裸原生形态渲染
- 严重度: 中
- 证据: `workbench/server/static/workbench.css:712-720` —— `.chapter-lens select { max-width:130px; … border: 1px solid var(--ink-strong); border-radius: 4px; }`；对应 DOM `pages.py:255-257`（`chapter-lens-select`）
- 违反: layout-spec §2.3「现状是**裸原生 `<select>`**（`appearance:auto`、1px 黑框、`max-width:130px`），与基线『章节透镜 = 自绘下拉面板（圆角、阴影、分隔、每项带章节名）』不符」；§4.19/§2.3 自绘面板用圆角+柔影、**不用描边**
- 为什么是缺陷: layout-spec 把这个裸 select 列为要被自绘面板取代的现状缺陷；当前 CSS 仍保留 1px 深墨描边 + 4px 直角形态。虽有 `@media (max-width:1023px)` 把 `max-width` 收到 92/84px（workbench.css:3407/3447），但**边框/圆角/`appearance` 从未被改**，且该 select 始终在 DOM 里（无 JS 或 `.js` 未加时直接可见）。
- 建议方向: 兜底 select 去描边、用 `--r-md`/卡面+柔影对齐自绘面板形态；确认 `.js .chapter-lens-select-fallback{display:none}`（workbench.css:725）在启用 JS 时确实接管。

### D-07 · 顶栏段三在桌面端常驻一个文本按钮「Agent 对话」，且非图标控件
- 严重度: 中
- 证据: `workbench/server/pages.py:317-318` —— `<button id='mobile-ai-toggle' class='outline topbar-action-text' … aria-label='打开对话'>Agent 对话</button>`；`workbench.css` 全文无 `mobile-ai-toggle` 的 `display` 规则（仅 `#mobile-nav-toggle` 在 C 档 `display:none`、D 档 `display:block`，见 workbench.css:3378/3406）；行为分支 `workbench.js:1747-1761`
- 违反: layout-spec §2.2 段三「桌面端**完全为空**」→ 填入「① Agent 对话开关 ② 主题切换」两个**图标按钮**（§2.1 线框段三 = `◐`/`☀` 图标按钮 34×34）；live spec「Three-column shell with navigation」（spec.md:12）「the left and right columns SHALL become dismissible drawers opened by **two compact icon controls** in the top bar」
- 为什么是缺陷: 「Agent 对话」是带中文文本的 `outline` 文本按钮，在 A/B 档（≥1280，右栏本就常驻可折叠）也一直占段三位置；layout-spec 期望桌面段三是**图标**控件、且语义为「收起/展开右栏」。文本按钮 + 全档常驻，是段三从「紧凑图标动作区」退化成「文字按钮排」的表现。
- 建议方向: 段三改图标按钮（34×34/12px 圆角），A/B 档图标语义=折叠右栏；文本标签仅在窄档必要时出现。

### D-08 · workspace 切换器把原始内部代号当可见选项名（`c05-thin-tempval`/`graph-dmath`/`graph-c02`）
- 严重度: 中
- 证据: `workbench/server/pages.py:277-285` —— `_workspace_switcher` 直接 `ws['name']` 作 `<option>` 文本；实际渲染（service `GET /w/lesson-kit/practice`）选项含 `c05-thin-tempval`、`w5-replica`、`graph-preview`、`graph-dmath`、`graph-c02`
- 违反: live spec「The top bar shows the name, not the identifier」（spec.md:34-37）；「Knowledge point list page」spec.md:109「raw identifiers only as secondary context」
- 为什么是缺陷: 顶栏身份段的下拉把明显的机器/内部代号（`c05-thin-tempval`、`graph-c02`）作为人类可读名展示；虽 live spec 允许「name is the folder name」，但这些是内部测试/预览工作区代号，作为可见文本属信息架构噪音，与「机器代号不进可见文本」的精神冲突。**存疑**：这些是否属合法注册名（来自 `workspaces.json`）——若合法则降级为「测试工作区未隐藏」的数据卫生问题。
- 建议方向: 工作区注册名与内部代号分离，或在切换器过滤非学习型/测试工作区。

### D-09 · 双轨版式未接线：`--shell-measure-wide:1120px` 定义后零引用，数据密集页仍锁 880 阅读轨
- 严重度: 中
- 证据: `workbench/server/static/workbench.css:125` —— `--shell-measure-wide: 1120px; /* 数据轨宽 */`；`workbench.css:127` —— `--shell-track: var(--shell-measure);`（指向 880 阅读轨）；全仓 `grep shell-measure-wide` 仅此 1 处定义、**无任何使用**；`.page-header,.page-content { max-width: var(--shell-measure); }`（workbench.css:883-888）
- 违反: layout-spec §4.2 / DRIFT-3（layout-spec.md:148-167）——页面级双轨「阅读轨 880px（疏朗面）/ 数据轨 1120px（紧凑面），页面二选一」
- 为什么是缺陷: 记录中心（12 周日历 + 14 天负荷柱 + 判定/评价分布双卡 + 概览卡）是典型「数据轨」页面，却被 `--shell-measure`（880px）锁在阅读轨里；1120 数据轨 token 定义了却没接任何选择器，双轨机制形同未实现，宽屏下右侧留大片空白、数据卡挤在 880 内。
- 建议方向: 给记录中心/图谱元数据等数据页接 `--shell-track: var(--shell-measure-wide)`（或 `.records-center` 用 wide 轨），兑现 §4.2 双轨。

### D-10 · 记录中心 Tab 是「nav>a」整页跳转，无 `role=tablist/tab`/`aria-selected`/焦点环
- 严重度: 中
- 证据: `workbench/server/records.py:618-626` —— `<nav class='record-tabs' aria-label='记录视图'>` + `f"<a class='record-tab{…active…}' href='{base}?view={key}'>{label}</a>"`（无 `role`/`aria-selected`/`aria-controls`，靠 `href` 整页刷新切换）
- 违反: component-spec §4.28 Tab（component-spec.md:1918-1966）——语义要求 `role="tablist"`/`role="tab"` + `aria-selected` + `aria-controls`、面板 `role="tabpanel"`、键盘 `←/→` roving tabindex（注：§4.28 权威**形态**=分段控件/白药丸，`.record-tab.active` 的白药丸选中态本身**符合**，问题只在语义与切换方式）
- 为什么是缺陷: 记录中心的概览/练习·试卷/作答明细/错题四视图是同层内容切换，却用 `<a href>` 整页导航实现：无 tablist/tab 语义、无 `aria-selected`、无方向键导航、切换即整页重载（丢失滚动位、触发全页进场动画）；另 `.record-tab` 无 `:focus-visible` 焦点环规则（`:has(input:focus-visible)` 那条只覆盖 `.lk-seg__item`，workbench.css:1975）。
- 建议方向: 改为 `role=tablist` + `role=tab` + `aria-selected` + 客户端切换（或至少补 tablist/tab/aria-selected 语义与 `:focus-visible` 焦点环）。

### D-11 · 记录中心与左栏薄弱轨的空态是裸文字，违反 §4.21「插画 + 一句 + 满宽主按钮」
- 严重度: 中
- 证据: `workbench/server/records.py:126` —— `return "".join(rows) or "<p class='muted'>暂无记录</p>"`；`records.py:195` —— `… or "<p class='muted'>暂无练习轮次</p>"`；`records.py:449`「最近 14 天暂无作答」、`553`「最近 12 周暂无作答」、`595`「暂无带评价的作答」、`752`「暂无弱项信号。」；`pages.py:1131-1132` —— 左栏薄弱轨 `empty = "暂无明确薄弱证据" if not actionable else "暂无提醒"` → `<p class="score">`
- 违反: component-spec §4.21 空态（component-spec.md:1569-1615）——形态固定为「静物插画 144×144 + 一句 ≤18 字 + 满宽主按钮」，禁止堆解释文字
- 为什么是缺陷: 全站空态规范早已落地（`_empty_state` 在 `pages.py:121-151`，知识点列表/试卷列表都用了插画+按钮），但记录中心 6 处与左栏薄弱轨的空态仍是 `<p class='muted'>` 裸文字：无插画、无动作按钮，空态退化为「堆说明文字」，与 §4.21 及本仓已有实现都不一致。
- 建议方向: 这些空态改走 `_empty_state`（插画 + 一句 + 满宽主按钮，按钮指向「去练习/去组卷」等真实动作）。

### D-12 · 加载态只有练习页试卷计数一处骨架，其余为永久「加载中…」文字占位，§4.22 未落地
- 严重度: 中
- 证据: `workbench/server/pages.py:483-486`（唯一骨架：`paper-count` 的 `lk-skeleton lk-skeleton--text` + `aria-busy='true'`）；对比 `pages.py:453`「今日题单」`<p id='today-meta' class='muted'>加载中…</p>`、`pages.py:466` 备考倒排 `<div id='exam-summary' class='muted'>加载中…</div>`；`grep lk-skeleton pages.py records.py` 仅 485 一处
- 违反: component-spec §4.22 骨架屏（component-spec.md:1617-1666）「**加载中**的面…始终有可见体积」；layout-spec §1.6/§4.22 —— 加载用骨架、不闪文字；§4.21「loading → 显示骨架而非空态」
- 为什么是缺陷: 练习页的「今日题单」「备考倒排」两个由 JS 异步填充的面板，初始是「加载中…」文字而非骨架块：无可见体积、加载完成时文字→内容会跳（CLS），与同页 `paper-count` 的骨架做法割裂；全站仅 1 处骨架，§4.22 形同孤例。
- 建议方向: 「加载中…」文字占位统一换成 `lk-skeleton--text/--block`（同高，避免 CLS），并补 `aria-busy`。

### D-13 · 图谱看板空态文案承诺「掌握状态/关联题数/关系强度」，与权威「仅名称+提醒+链接」冲突
- 严重度: 中
- 证据: `workbench/server/pages.py:845` —— `点击图中的知识点，查看掌握状态、关联题数与关系强度。`（对 `pages.py:843` 的 `#graph-detail-panel`）；选中态实现 `workbench.js:2484-2503`
- 违反: live spec spec.md:408/413（节点选中只给 name + 重点练习/可以复习 reminder + 打开知识点 link）
- 为什么是缺陷: 空态显式列出「掌握状态、关联题数、关系强度」三项，与 D-01 的选中态一起构成「面板自称是参数看板」；即便选中态收敛后，这句空态仍会引导学生期待被禁止的参数。
- 建议方向: 空态单句改为「选择一个节点，查看它的名称与回看提醒」，去掉对题数/关系强度的承诺。

### D-14 · Agent 活动浮层用 1px 深墨描边（`border:1px solid var(--ink-strong)`），违反「靠圆角+柔影分层、不用描边」
- 严重度: 中
- 证据: `workbench/server/static/agent-ui.css:199-205` —— `.agent-activity-float, .agent-artifact-split { z-index:9; border: 1px solid var(--ink-strong); background: var(--surface-card); box-shadow: var(--elev-3); }`
- 违反: component-spec §4.19 纸面层级（component-spec.md:1463-1464）「相邻两级靠**圆角 + 柔影**拉开，**不用描边**、不用背景图案、不用渐变」；live spec「Learning content is the visual anchor」
- 为什么是缺陷: 活动浮层是 `position:sticky; float:right; z-index:9`（agent-ui.css:206-214）浮在**中栏学习内容之上**的 L1 卡面，却用了 1px 近黑硬描边 —— 正是 §4.19 明令排除的分层手段；深墨硬边压在学习正文上，削弱「学习内容是视觉锚点」。
- 建议方向: 去掉 `border`，改 `box-shadow: var(--elev-3)` + 必要时夜纸补 `0 0 0 1px var(--rule-hair)`（对齐 §4.19 夜纸浮起层）。

### D-15 · 窄屏顶栏 7 控件无收口规则，工作区名 `max-width:36ch` 在 375px 有横向溢出风险
- 严重度: 中
- 证据: `workbench/server/pages.py:295-323`（顶栏 = 品牌 + `/` + workspace-select + chapter-lens + 搜索 + 对话视图 + 夜纸 + Agent 对话 + mobile-nav）；`workbench.css:607-610` —— `#topbar .topbar-workspace { max-width:36ch; … }`；E 档 `@media (max-width:767px)`（workbench.css:3440-3448）**只**收了 `.brand{font-size:0;width:47px}` 与 `.chapter-lens select{max-width:84px}`，未收 `.topbar-workspace`/`.topbar-identity`
- 违反: layout-spec §7.8 断点守卫（workbench.css:584 自述「顶栏内容超宽是横向滚动来源之一」）；layout-spec §1.4 E 档 <768 单栏、顶栏应保持紧凑
- 为什么是缺陷: 375px 视口下顶栏要同时容纳：47px 品牌 + 16px gap + 工作区名（最长 `毛泽东思想和中国特色社会主义理论体系概论` 36ch≈远超屏宽）+ 透镜 + 搜索 + 两个开关（各带中文标签 `white-space:nowrap`）+ Agent 对话 + ☰。E 档只压了品牌字号与透镜宽度，**工作区名与四个动作控件无任何收口**，`#topbar{flex:none}`（workbench.css:563）不允许换行 ⇒ 内容必然溢出或把 `topbar-identity` 压到不可读。**存疑**：`topbar-identity` 是 `flex:0 1 auto` + `min-width:0`（workbench.css:586/583）可收缩、select 有 `text-overflow:ellipsis`，实际是否溢出需可视化确认；但「E 档未对工作区名/动作区设收口」这一缺口静态可证。
- 建议方向: E/D 档把 `.topbar-workspace` 收到 `max-width:~10ch`、动作区只留 ☰ + Agent 图标（隐藏搜索/开关文字标签），或让顶栏允许在窄屏折两行。

### D-16 · E 类流程（由 D 组顺带发现，静态判定）：顶栏「搜索」跳转到图谱页搜索框，属绕远路径
- 严重度: 低
- 证据: `workbench/server/static/workbench.js:1721-1727` —— `topbar-search` click → 若不在图谱页则 `window.location.href = "/w/"+WS+"/graph"`；`workbench.js:1701-1703` 自述「跳到知识图谱页的既有搜索框——产品里唯一真的会查东西的检索控件」
- 违反: 通用交互流程合理性（船与木桩）；E 类「同类操作流程一致、返回路径不绕」
- 为什么是缺陷: 学习者在任意页点顶栏「搜索」，被整页跳到知识图谱页才能输入关键词，再要从图谱返回原页 ——「搜个知识点」要跨越页面 + 借道图谱页搜索框；而知识点列表页本就有 `knowledge-sort`/列表（pages.py:764），顶栏搜索却不能直达。**说明**：这是静态读代码判定的流程绕远，未在浏览器实点（本组无浏览器工具），主责在 C 组。
- 建议方向: 顶栏搜索给一个真正的全局检索入口（下拉/面板，回车直达知识点详情），或至少保留来源页返回路径。

### D-17 · 章节透镜把「章」字标签与 checkbox+原生 select 三件套并存，与「章身份只有一个家（透镜）」的收敛形态不符
- 严重度: 低
- 证据: `workbench/server/pages.py:246-261` —— `<label class='chapter-lens-toggle'><input type='checkbox' id='chapter-lens-switch'><span>章</span></label>` + `<select id='chapter-lens-select' class='chapter-lens-select-fallback'>` + `<div class='chapter-lens-panel' role='listbox' hidden>`
- 违反: layout-spec §2.2 硬约束 2「顶栏**不再有独立的章 chip、也不再有「章」文字标签**（现状是 `checkbox` + 「章」span + `<select>` 三件套，`pages.py:56-65`）」；§2.3 自绘面板
- 为什么是缺陷: layout-spec 明确点名「checkbox + 『章』span + select 三件套」是要被「工作区名 + 透镜」两项取代的现状缺陷；当前 `pages.py` 仍渲染 `<span>章</span>` 文字标签 + checkbox + select（+ 自绘面板），章身份在顶栏出现「章」字 + 透镜 + 兜底 select 三处视觉，段二信息架构未收敛到两项。
- 建议方向: 去掉「章」文字标签与常驻 checkbox，章身份只由自绘透镜触发器（含当前章名）承担；原生 select 仅作无 JS 兜底。

### D-18 · 图谱页把已废止的「3px 深墨标题带底线 + 76×8 装饰黄块」钉回，形成全站唯一的例外
- 严重度: 低
- 证据: `workbench/server/static/workbench.css:468-480` —— `body:has(#layout[data-page="graph"]) .page-header { border-bottom: 3px solid var(--ink-strong); }` 与 `… .page-header::after { … width:76px; height:8px; background: var(--role-yellow); border:1px solid var(--ink-strong); }`；对照基线 `workbench.css:889-893` —— `.page-header { border-bottom: 2px solid var(--rule-structure); }`（无黄块）
- 违反: layout-spec §0.2/任务 14.3「标题带底边从 3px 纯黑换成 2px `--rule-structure`、并删掉那块 76×8 的装饰黄块；黄色是稀缺语义色…挂在每页标题带末端当装订线 = 把语义色降级成装饰」；live spec「Learning content is the visual anchor」
- 为什么是缺陷: 全站标题带已统一为 2px 结构线、无黄块，唯独图谱页用 `body:has()` 把旧版 3px 深墨底线 + 76×8 黄块钉回（注释称因 G-5 逐像素冻结）。结果是同一 Shell 下图谱页标题带与其它页**版式不一致**，且复活了被判定为「语义色降级成装饰」的黄块。**存疑**：这是为图谱冻结刻意保留的兼容钉，属「刻意不一致」还是应随新形态退役需所有者裁决。
- 建议方向: 若图谱页仍需与其它页同构，移除该 `body:has()` 钉、改用 2px `--rule-structure`；若必须冻结，则在报告中登记为「已知的刻意例外」。

### D-19 · 记录中心作答明细视图无加载态/分页提示，最多一次性渲染 500 张卡
- 严重度: 低
- 证据: `workbench/server/pages.py:969` —— `limit = 500 if view in {"attempts","wrong"} else 100`；`records.py:666-672` —— attempts 视图 `f"<p>{len(records)} 条</p>" + _attempt_rows(workspace_name, records)`；`records.py:650-655` 仅当 `len(records) >= limit` 时给一句「已载入最近 {limit} 条，更早的记录未显示。」
- 违反: layout-spec §1.6（`#middle` 是唯一滚动容器，长列表应有边界/分页）；component-spec §4.22（长列表加载应有骨架/渐进呈现）；通用数据呈现
- 为什么是缺陷: 作答明细/错题视图把至多 500 条记录一次性渲染成卡片流（`_attempt_rows` 每条含题面+摘录+判定+评价，`records.py:71-126`），无分页、无「加载更多」、无骨架：首屏 DOM 巨大、滚动卡顿，且 500 条边界提示仅在**恰好≥500**时出现，499 条时用户无从知道是否还有更多。
- 建议方向: 分页或「加载更多」+ 渲染前骨架；把上限提示改为不依赖恰好触顶（如显示「已显示 X / 共 Y」）。

---

## 服务渲染与分支不一致（非设计缺陷）
- 本组在 `feat/exam-prep-engine` 分支上工作，`git status` 显示 `workbench/server/pages.py` 无改动（干净、与 HEAD 一致）；service `http://127.0.0.1:3081` 实际渲染的左栏/顶栏与当前 `pages.py` 一致。
- 协调者提醒的「左栏『设置』套『设置』、优先回看计数徽标」：当前检出 `pages.py:1142-1145` 渲染的是**单个** `<a id='setting-view-toggle' …>设置</a>`（在 `side-label`「设置」分区内，`aria-expanded='false'`），非「设置」嵌套「设置」；`优先回看` 分区带 `count-badge`（pages.py:1148）。这些是**当前分支的真实结构**，本组未将其计为 D 组缺陷（按协调者「别当新缺陷」归类到本节）。

## 无浏览器工具说明
本环境**无 Playwright 浏览器工具**：`browser-use` 技能存在，但无可调用的 `mcp__node_repl__js` 函数，且 `ZCODE_PLUGIN_ROOT` / `CLAUDE_PLUGIN_ROOT` 均未设置，无法引导浏览器运行时。依协调者改指令「禁止起浏览器」，本报告**全部为静态审计**，未做可视化核验/多视口截图；D-15、D-16 的实际渲染表现建议由主会话可视化复核。

## 统计
共 **19** 条（高 3 / 中 11 / 低 5）。
- 高：D-01、D-02、D-03
- 中：D-04、D-05、D-06、D-07、D-08、D-09、D-10、D-11、D-12、D-13、D-14、D-15
- 低：D-16、D-17、D-18、D-19
- 另含 E 类顺带发现 1 条（D-16，静态判定，未实点）。
