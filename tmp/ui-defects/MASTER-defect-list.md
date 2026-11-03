# UI 缺陷主清单（合并去重 · 按严重度排序）

**总计：去重后 78 条** —— 高 13 / 中 50 / 低 15。（原 60 条 + 浮层/遮罩批次净新增 18 条，见下方「浮层/遮罩专项」节。）另附「分支已修但主检出仍在」5 条（不计入待修）+「非 UI 设计缺陷」1 条脚注。

**方法说明**：由 5 份审计报告合并而成（A 组件形态/视觉 · B 文案/冗余 · C 交互/可达性 · D 版式/信息架构/响应式 · MAIN 主会话量化/交互流程）。A/B/C/D 为 agent 纯静态读代码审计；MAIN 为主会话 Playwright 浏览器实测（DOM `getBoundingClientRect` 量化 + 截图 + 实点）。跨报告重复簇（命中区 / 禁用术语 / 焦点环 / 仅颜色状态 / 空态加载态）已合并为单条主条目并保留全部原 ID 便于溯源。F 报告未落盘，本清单不含 F 类。

---

## 严重度：高（11）

| 原 ID | 严重度 | 标题 | 文件:行号 | 类别 |
|---|---|---|---|---|
| A-01 | 高 | agent-ui.css 末尾 `#agent-artifact-body` 规则未闭合，吞掉整个移动端 `@media` 块（花括号 99/98 实测差 1） | workbench/server/static/agent-ui.css:435-446 | 组件形态/语法 |
| A-05 | 高 | exam-prep 块用未定义 token（`--radius-md`/`--ink-line`/`--surface`/`--text`）回落硬编码浅色，夜纸不翻转 | workbench/server/static/workbench.css:5254,5261 | 主题/视觉基线 |
| A-03 | 高 | Agent 审批动作禁用态用 `opacity` 压暗，spec 明令禁用此写法 | workbench/server/static/agent-ui.css:372 | 组件形态 |
| D-01 | 高 | 图谱右栏看板选中态渲染 8 个区块 + 禁止的图谱参数，而非「名称+提醒+一个链接」 | workbench/server/static/workbench.js:2484-2503 | 信息架构 |
| D-02 + D-13 | 高 | 图谱看板空态自贴「掌握状态·关联题数·关系强度」承诺，与权威「仅名称+提醒+链接」矛盾 | workbench/server/pages.py:843-845 | 信息架构/空态 |
| E-01 | 高 | 单页三套并列练习入口（今日题单/演示卷/题号格），两个 primary 抢主次，用户不知走哪条 | workbench/server/pages.py（practice 页） | 交互流程 |
| B-07 | 高 | 完成页 kicker 用英文全大写口号「A LITTLE FURTHER, TOGETHER.」 | workbench/server/pages.py:522 | 文案 |
| A-04 + A-12 + C-10 + C-11 + C-19 | 高 | 状态只靠颜色/缺几何第二通道（选中态·工具卡·计划步·里程碑）：合并簇 | workbench.css:5263,2648-2654 · agent-ui.css:175-186,284-295 · agent-ui.js:122-133 | 状态冗余通道 |
| B-01 + B-02 + B-06 + B-15 + D-03 | 高 | 禁用/不一致术语暴露给学生：掌握度·能力分·正确率·theta·kp_id·薄弱点 vs 弱项：合并簇 | records.py:732,740,742-746,789,791,798 | 文案/术语契约 |
| M-01 + A-02 + A-06 + A-16 + A-21 + A-23 + C-01~C-06 + C-18 + C-20 + E-02 | 高 | 命中区系统性 <44px：合并簇（MAIN 实测 84 可点元素中 30 个 <44px，硬约束 §3.1） | 见下方点位清单 | 可达性/命中区 |
| C-06 | 高 | 图谱图例项约 17px 高且关闭态只靠 opacity（无几何/`aria-pressed` 第二通道） | workbench/server/static/workbench.css:5025-5033 | 命中区/状态通道 |

### 命中区 <44px 合并簇 · 点位清单

- **M-01（主会话浏览器实测，30 个 <44px）**：顶栏品牌 `a.brand` 22px · `select#workspace-select` 34px · `input#chapter-lens-switch` 13px · `button#topbar-search` 40px · `button#mobile-ai-toggle` 40px · 左栏 5 导航项 32px · `a#setting-view-toggle` 22px · 优先回看条目×3 22px · `button#start-today` 40px · `button#paper-start` 40px · `a.outline.button-link` 19px · `summary`×2 22px · `input#exam-date-input` 20px · `input#goal-start-date`/`#goal-deadline` 20px · `select#goal-kind` 34px · `button#goal-submit.primary.sm` 28px · `button#goal-assist-send.outline.sm` 28px · `button#ai-new-session.outline.sm` 28px。
- **C 组静态点位**：C-01 `.ai-pending-handle` 24×24（agent-ui.css:76-82）· C-02 `.part-details` ~22px（workbench.css:5253 · part-practice.js:83）· C-03 `.ai-pending-actions button` ~27px（agent-ui.css:101）· C-04 Agent 活动/收起按钮 28×36（agent-ui.css:259-260 · pages.py:365-366,377-378）· C-05 图谱图标 34 / 缩放 36 / chip ~23 / 分段 ~25（workbench.css:4820-4831,4990-4993,5040-5044 · pages.py:796-797,809）· C-18 `.sm` 档 28px 且主动关掉命中区伪元素、中心距未逐点证明（workbench.css:1231,1241-1242 · practice-flow.js:1636-1637,2055）· C-20 图谱图例/分段/chip 字号 9-10px 过小连带（workbench.css:4822,4992,5023）。
- **A 组静态点位**：A-02 队列操作按钮 11px + 4/7px 内距（agent-ui.css:101）· A-06 `button.ghost` 36px 无命中补偿（workbench.css:1245-1262）· A-16 `button.rate` 24px 无补偿（workbench.css:1263-1272）· A-21 `#ai-model-switch` 被 ID 规则压到 30px（agent-ui.css:22-28 · pages.py:1219）· A-23 `.ai-paper-approval-order` 10px 字号低于 micro 下限（agent-ui.css:358-364）· E-02 题号格旁独立「详情」按钮（分支已删，见文末节）。

### 禁用/不一致术语合并簇 · 明细

- B-01「掌握度估计（能力分）」栏目标题（records.py:789）· B-02「每日正确率」（records.py:798）· B-06 暴露原始 IRT `theta` + 机器 `kp_id`（records.py:744）· B-15「薄弱点」vs GLOSSARY 权威「弱项」，同视图两种叫法（records.py:732,740,791）· D-03 能力估计行以 `kp_id` 为主文本 + 裸 `theta`、可读名缺位（records.py:742-746）。

### 状态只靠颜色合并簇 · 明细

- A-04 备考评分档 `--picked` 选中只改边框/文字色（workbench.css:5263）· A-12 工具卡/计划步进行中-完成-失败只靠左边框色，且「完成=黄」与权威映射冲突、属 B 类未裁先实现（agent-ui.css:175-186）· C-10 计划步 running/done/failed 几何均为实心圆、仅颜色区分（workbench.css:2648-2654 · agent-ui.css:284-295）· C-11 工具调用卡状态只靠 3px 左边条颜色（agent-ui.css:183-186）· C-19 Agent 里程碑 marker 无 `aria-label`、状态靠 JS 符号字符（agent-ui.js:122-133，存疑）。

---

## 严重度：中（36）

| 原 ID | 严重度 | 标题 | 文件:行号 | 类别 |
|---|---|---|---|---|
| A-07 | 中 | 按钮基类 `border-radius:18px` 既非 token 也不在圆角五档内（旧药丸残留） | workbench/server/static/workbench.css:1121 | 组件形态/圆角 |
| A-08 | 中 | `#ai-chat-head` / `.agent-skill-row` 用墨色 token 当结构线（近黑边框） | agent-ui.css:20 · workbench.css:5239 | 分层/描边 |
| A-09 | 中 | Agent 贴底输入区圆角 16px + 墨色描边，与 composer 特例（12px/沉底/无强描边）不符 | agent-ui.css:128-137 | 分层/描边 |
| A-13 | 中 | 闪卡用大偏移硬阴影（blur=0）+ 2px 近黑描边，违背「柔影分层/不描边」 | workbench.css:3131-3134,3148,3152 | 分层/描边 |
| A-14 | 中 | `!important` 覆盖 + 硬编码 9px/10px 圆角散落 agent-ui（不在五档内） | agent-ui.css:365,373-379,397-403 | 圆角/覆盖 |
| A-15 | 中 | `.part-card` 用 `currentColor` 描边 + 8px 圆角，卡片语言偏离裁定 | workbench.css:5244 | 卡片语言 |
| A-24 | 中 | `.paper-options label` 与 `fieldset.problem-options > label` 两套选项行几何并存（活的冲突源） | workbench.css:5227 vs 2009-2017 | 组件形态 |
| A-17 | 中 | `.exam-bar` 进度条 10px/6px 圆角，未并入 §4.15「8px 胶囊」统一语言 | workbench.css:5275（对照权威 :4403-4407） | 进度条 |
| A-10 | 中 | `#ai-input` 用 `:focus`（非 `:focus-visible`）、圆角 4px、且缺 §4.6 规定的「聚焦抬起 -2px + elev-2」 | agent-ui.css:149-153 | 焦点环/composer |
| A-11 + A-25 + C-07 + C-08 + C-09 + C-17 | 中 | 焦点环多套并存口径、非 `:focus-visible` 冒环、只染边框无环、硬编码黄 `#d3a914` 未接 `--focus-outer`：合并簇 | agent-ui.css:83-87,149-153 · workbench.css:1055,4980,5031,5262 | 焦点环 |
| A-19 | 中(存疑) | 原生 `<select>` 34px 高 + 6px 圆角，低于 44px 命中下限（B 类待替换过渡态） | workbench.css:1044-1049（对照输入框 :1323-1328） | 命中区/B类 |
| A-22 | 中(存疑) | `#ai-input-row` 同屏混用「卡片描边+浮起柔影+沉底子件」，纸面层级 L1/L2/L3 归属不清 | agent-ui.css:128-137,138-148 | 分层 |
| C-12 | 中 | 图谱过滤 chip 是开/关切换按钮，但无 `aria-pressed`、选中态无文字/形状冗余 | pages.py:809-812 · workbench.css:4994-4997 | 状态通道 |
| C-13 | 中 | Agent 队列/状态区（`#ai-queue-status`/`#ai-status`/`.ai-handoff-status`）均无 `aria-live` | agent-ui.css:61,158-163,40-46（对比 practice-flow.js:2068 已设） | 可达性 |
| C-14 | 中 | 评分卡校验失败后焦点不移动，错误只靠 aria-live 广播（无 role=alert/焦点管理） | practice-flow.js:2065-2078 | 可达性/焦点 |
| C-15 | 中 | `.part-preview` 浮层 hover/focus 出现但仅 Escape 可关，关闭通道三处三套 | part-practice.js:85,88 | 交互一致性 |
| B-09 | 中 | 完成页统计句同句内混用「判定正确」与裸「错误」，且用「正确/错误」而非契约「对/错」 | paper-practice.js:1508-1510 | 文案/术语 |
| B-10 | 中 | 小问状态机把批改管线内部状态（待批改/批改中/已批改/批改失败…）直出给学生，且未纳入 copy-table | part-practice.js:3,6-10 | 文案 |
| B-11 | 中 | 小问汇总行「批改/答案/过程」字段名前缀堆计数，且无标签时回落裸机器键 | part-practice.js:69 | 文案/注释型 |
| B-13 | 中 | 记录-备考视图 kicker「备考」与标题「备考倒排」同字冗余 | records.py:785-786 | 文案 |
| B-16 | 中(存疑) | 备考视图「回忆质量分布/每日投入」暴露 SM-2 调度内部概念与等级词 | records.py:754,794,796 | 术语/调度 |
| B-17 | 中 | 练习反馈「我的评价：★★★☆☆（3/5）」同一评分双通道重复呈现 | practice-flow.js:968-969 | 文案冗余 |
| D-11 + D-12 + D-19 + B-21 + B-14 | 中 | 空态/加载态/占位系统性不合规（裸文字空态、加载中文字闪现、占位直出 0、措辞漂移）：合并簇 | 见下方明细 | 空态/加载 |
| D-04 | 中 | 顶栏段一→段二分隔仍是字面 `/` 文字，未换成 1px 竖向结构线 | pages.py:299 · workbench.css:686 | 版式 |
| D-05 | 中 | 顶栏三色标记与产品名间距 44px（margin 34 + gap 10），spec 收到 10px 未落地 | workbench.css:669,671-681 | 版式 |
| D-06 | 中 | 章节透镜兜底 `<select>` 以「1px 深墨边框 + 4px 圆角」裸原生形态渲染 | workbench.css:712-720 · pages.py:255-257 | 组件形态 |
| D-07 | 中 | 顶栏段三桌面端常驻文本按钮「Agent 对话」，spec 要求图标控件且 A/B 档段三为空 | pages.py:317-318 | 导航/版式 |
| D-08 | 中(存疑) | workspace 切换器把原始内部代号当可见选项名（`c05-thin-tempval`/`graph-dmath`/`graph-c02`） | pages.py:277-285 | 信息架构 |
| D-09 | 中 | 双轨版式未接线：`--shell-measure-wide:1120px` 定义后零引用，数据密集页仍锁 880 阅读轨 | workbench.css:125,127,883-888 | 版式 |
| D-10 | 中 | 记录中心 Tab 是「nav>a」整页跳转，无 `role=tablist/tab`/`aria-selected`/焦点环 | records.py:618-626 | 语义/可达性 |
| D-14 | 中 | Agent 活动浮层用 1px 深墨描边，违反「靠圆角+柔影分层、不用描边」 | agent-ui.css:199-205 | 分层/描边 |
| D-15 | 中 | 窄屏顶栏 7 控件无收口规则，工作区名 `max-width:36ch` 在 375px 有横向溢出风险 | pages.py:295-323 · workbench.css:607-610,3440-3448 | 响应式 |
| M-02 | 中 | 开关控件 track 内容溢出容器（`.lk-switch__track` scrollWidth 38 > clientWidth 32） | workbench.css（`.lk-switch__track`） | 组件形态 |
| M-03 | 中 | 开关 input 被 `aria-hidden` track 拦截指针事件（Playwright 直点 `#topbar-theme` 超时 5s） | workbench.css/pages.py（`#topbar-theme`） | 可达性 |
| E-04 | 中 | 顶栏「对话视图」switch 与「Agent 对话」按钮语义重叠（同右栏两个入口、两种交互） | practice 页顶栏（switch + button） | 交互流程 |
| E-05 | 中 | 批改失败后主操作按钮全禁用，恢复路径依赖孤立「重试批改」，无指引易卡住 | part-practice.js（小问 1 失败态） | 交互流程 |

### 焦点环合并簇 · 明细

- A-11 Agent 单圈蓝 outline 偏移 1px（agent-ui.css:83-87）· A-25 备考档单圈蓝 outline + 非 token 回落 `#2668d8`（workbench.css:5262）· C-07 三套并存口径：图谱黄 `#d3a914`/1px、备考蓝/2px、Agent 蓝/1px vs 全局 `--focus-outer`/2px（workbench.css:4980,5031,5262 · agent-ui.css:83-87）· C-08 `#ai-input` 用 `:focus` ⇒ 鼠标冒环（agent-ui.css:149-153）· C-09 `select:focus` 只染 1px 边框、键盘聚焦无环（workbench.css:1055）· C-17 图谱焦点环硬编码 `#d3a914`、控件裸 hex，未接 `--focus-outer`（workbench.css:4980,5031,4817,4991,5041）。

### 空态/加载态/占位合并簇 · 明细

- D-11 记录中心 6 处 + 左栏薄弱轨空态是 `<p class='muted'>` 裸文字，违反 §4.21「插画+一句+满宽主按钮」（records.py:126,195,449,553,595,752 · pages.py:1131-1132）· D-12 加载态只有练习页 1 处骨架，其余为永久「加载中…」文字占位、§4.22 形同孤例（pages.py:483-486,453,466）· D-19 作答明细一次性渲染最多 500 卡、无加载态/分页、边界提示仅恰好≥500 才出现（pages.py:969 · records.py:650-655,666-672）· B-21 复习负荷摘要占位直出「共 0 项」（pages.py:1656）· B-14 经验面板空态「暂无关联题目」与 copy-table E-15 定稿措辞漂移（kp-experience.js:93）。

---

## 严重度：低（13）

| 原 ID | 严重度 | 标题 | 文件:行号 | 类别 |
|---|---|---|---|---|
| A-18 | 低 | `.solution-block` 局部圆角 `0 6px 6px 0`，未用 12px 档（6px 属 `--r-xs` 误用于内容容器） | workbench.css:1423-1429 | 圆角 |
| A-20 | 低(存疑) | 复选/单选「禁用且选中」把标记与底色降为墨/纸色，蓝→灰语义跳变（已有 3.59:1 对比取舍注释） | workbench.css:2115-2124 | 状态通道 |
| C-16 | 低(存疑) | `.flash-answer-reveal` 620ms 关键帧超 §3.3 时长档（非 240/517/700ms 任一档） | workbench.css:3153,3155-3159 | 动效 |
| B-18 | 低(存疑) | 备考倒排区 kicker「备考倒排」与同节 `aria-label` 重复（可见层再复述一次） | pages.py:463-465 | 文案 |
| B-19 | 低 | 备考倒排空值句重复「倒排」且要求跨页设置，语焉不详 | records.py:735 | 文案 |
| B-20 | 低 | runtime 更新守卫「更新等待中：正在等待当前任务完成」同义重复 | runtime.js:68 | 文案 |
| D-16 | 低 | 顶栏「搜索」跳转到图谱页搜索框，搜个知识点要跨页+借道，属绕远路径 | workbench.js:1721-1727,1701-1703 | 交互流程 |
| D-17 | 低 | 章节透镜把「章」字标签与 checkbox + 原生 select 三件套并存，未收敛到「章身份只有一个家」 | pages.py:246-261 | 信息架构 |
| D-18 | 低(存疑) | 图谱页把已废止的「3px 深墨标题带底线 + 76×8 装饰黄块」钉回，形成全站唯一例外 | workbench.css:468-480（对照基线 :889-893） | 版式 |
| E-03 | 低 | 今日题单「用时预估 48 / 45 分钟」预估超预算却照常展示无提示 | practice 页（今日题单卡） | 交互流程 |
| E-06 | 低 | 右栏每个会话常驻 ✎/× 两个小图标按钮，低频操作占视觉且 × 紧邻标题易误删 | 右栏历史对话列表 | 交互流程 |
| E-07 | 低(存疑) | 「你的作答」标签游离在小问作答区与「上一题/下一题」之间，无紧邻可读内容 | part-practice.js | 交互流程 |
| M-04 | 低(存疑) | 响应式窄屏不确定：resize 375 但 clientWidth 实测 562，左右 rail 移出视口（疑似抽屉设计） | pages.py/workbench.css（mobile-nav-toggle/mobile-ai-toggle） | 响应式 |

---

## 浮层/遮罩专项（本轮 checkpoint · 净新增 18 条）

> 所有者 checkpoint：「浮窗出现遮罩/被遮罩的情况」——浮层出现时挡住下方内容、或浮层被别的层遮住/裁切导致操作不便。来源：G（静态遮罩/关闭通道/焦点，13 条）+ H（静态 z-index/层叠/裁切，15 条）+ MAIN（运行时 elementFromPoint 实锤，N 5 条），去重合并为 18 条净新增。其中 N-01（运行时）与 H-01（源码）互为印证。

| 原 ID | 严重度 | 标题 | 文件:行号 | 类别 |
|---|---|---|---|---|
| H-01 + N-01 | 高 | 章节透镜下拉面板被遮：`.chapter-lens` position:relative/z-index:auto 未建 stacking context，ch06 选项按钮中心点被 `main` 盖住（运行时 elementFromPoint 实锤 + 源码根因一致） | pages.py:246-261 · workbench.css（chapter-lens） | 浮层被遮 |
| H-02 + G-01 + G-02 | 高 | 遮罩层 token（`--z-overlay`/`--z-modal`/`--z-raised`/`--veil-modal`）**定义了却从未使用** ⇒ 抽屉开启无蒙幕：对话抽屉 C/D 档、导航抽屉 D 档开启时下方主内容仍可交互，唯一关闭通道是顶栏开关 | workbench.css（token 定义）· agent-ui.css / workbench.js（抽屉） | 遮罩缺失/操作不便 |
| G-04 | 中 | 抽屉开启后焦点不进抽屉、关闭不还焦点，键盘用户被困/丢失位置 | agent-ui.js / workbench.js（抽屉） | 焦点 |
| G-03 + H-06 + H-07 + G-10 | 中 | 抽屉 z-index 同值冲突：`#ai-column` 与 `#left-column` 同为 10（窄屏同时打开顺序不定）；图谱 `.toast:20` 与图谱抽屉 `:20` 同值冲突，抽屉盖住 toast | agent-ui.css / workbench.css:4820 区 · pages.py | z-index 冲突 |
| G-11 + H-10 + H-11 | 中 | 图谱选中被盖：`.graph-kp-selection` 自带 transform 建 stacking context 困住 z-index:5；`.controls`/`.zoom` 同为 8、`.legend:7`、选中标签:5 抢层 | workbench.css 图谱区 | 层叠/被遮 |
| H-03 + H-04 + H-05 + H-12 + H-13 + H-14 + G-05 + G-13 + N-04 | 中 | **z-index 无统一口径**（合并簇）：全站散落 0/1/5/9/10/30/40/50/51/100/9999（运行时统计 10 种值）；`--z-overlay/--z-modal` token 定义未用；`9999` inline magic（runtime 更新提示）；`.filter-popup:40`、`.part-preview:30`、combo:100、纸屑:50 互不兼容；无 modal(300) 层时 `--z-toast(200)` 成实际顶层盖住 combo/part-preview | workbench.css · agent-ui.css · runtime.js:68 · 图谱 css | z-index 无口径 |
| G-08 | 中 | Agent 工件预览浮层遮挡下方对话内容，无遮罩直接压在消息流上 | agent-ui.js / agent-ui.css（artifact 预览） | 遮挡交互 |
| H-08 + N-05 | 中 | 浮层普遍 `position:relative + z-index:auto` 未建层叠上下文；抽屉用 `transform:translateX` 开合（transform 建 stacking context + containing block）困住子层 z-index | agent-ui.css / workbench.css（抽屉·浮层基类） | 层叠上下文根因 |
| G-06 | 中 | 来源筛选浮窗 `.filter-popup` 关闭通道不全（无点击外部关闭/关闭按钮不明显） | workbench.js / workbench.css（filter-popup） | 关闭通道 |
| G-12 | 低(中) | Agent 活动浮层常驻占用视觉、与主内容抢注意力 | agent-ui.css（activity-float） | 遮挡交互 |
| N-02 + G-07 + G-09 + H-15 | 中 | **浮层被裁**：`.part-preview` 位于 `overflow:auto` 的 `.paper-dots` 容器内（运行时实锤），filter-popup/part-preview 为 absolute 依赖祖先无 overflow，多小问/窄屏下预览卡被裁切显示不全 | workbench.css:5253-5254 · part-practice.js · workbench.js | 浮层被裁 |
| C-15 + N-03 | 中 | part-preview 浮层**只能 Esc 关闭**（运行时确证无关闭按钮、无点击外部关闭），触屏/鼠标用户无 Esc 概念 | workbench.css:5253-5254 · part-practice.js:84-85 | 关闭通道 |
| G-05 | 中 | tooltip/浮层提示被父 overflow 裁切或遮挡 | workbench.css（tooltip） | 浮层被裁 |
| M-03（印证） | 中 | 顶栏夜纸/对话视图开关 input 被 `aria-hidden` 的 `.lk-switch__track` 拦截指针，直点 input 无效（Playwright 超时实证）；章透镜 checkbox 仅 13×13 | workbench.css（lk-switch）· pages.py | 遮挡交互 |

> 运行时确证（主会话 elementFromPoint/computedStyle 实测）：N-01（ch06 按钮被 main 遮）、N-02（part-preview 在 overflow:auto 容器内）、N-03（part-preview escOnly 无关闭钮）、N-04（全页 z-index 10 种值含 9999）、N-05（浮层 relative+auto 未建上下文）。源码侧由 G/H 全量清点互证。

---

## 分支已修但主检出仍在（不计入待修）

> 以下在 `feat/workbench-display-redundancy-cleanup` 分支已删除/已修，但审计所针对的主检出 `feat/exam-prep-engine`（及 runtime 解析回 primary 的服务渲染）仍在，故静态审计仍可见。**不计入上方 60 条待修新缺陷。**

| 原 ID | 严重度 | 标题 | 文件:行号 | 分支状态 |
|---|---|---|---|---|
| B-03 | 高 | 小问解析区「你的答案（Agent 提炼）」括号暴露内部机制 | part-practice.js:33 | 分支已删 |
| B-04 | 高 | 小问解析区「参考来源 → Agent 独立推导」暴露 provenance 元信息 | part-practice.js:35 | 分支已删 |
| B-05 | 高 | 小问状态串硬拼「答案：」「过程：」字段名前缀 | part-practice.js:8-9 | 分支已删 |
| B-08 | 中(存疑) | 试卷判定「判定：正确 / 判定：错误」用「字段名: 值」硬前缀 | paper-practice.js:733-734 | 分支已删 |
| B-12 | 中 | 小问预览孤立「详情」按钮（题号格详情按钮残留） | part-practice.js:83 | 分支已删 |
| E-02 | 中 | 题号格旁独立「详情」按钮（悬停已有预览仍多一按钮） | part-practice.js:83 | 分支已删（A1：详情按钮已删、钉住迁到弹卡） |

> 同源提示：`part-practice.js` 整文件未纳入 copy-table 文案清单却承载大量学生可见文案，B-03/B-04/B-05/B-12 残留集中于此；`C-02`（`.part-details` 命中区）与 `E-02` 指向同一「详情」按钮，主检出修复命中区时应与分支的删除动作对齐，避免重复处置。

---

## 非 UI 设计缺陷（runtime）

> **M-05 · 服务渲染 pages 与分支不一致（非设计缺陷，不计入主清单）**
> 证据：`curl /w/lesson-kit/practice?paper=ps-001` 实测服务端渲染含 `count-badge=1`、`待回看=1`、`>设置</a>=1`（旧版条目），但 worktree `pages.py` grep `count-badge|count_badge|待回看` = 0（已删净，HEAD=4ca1d5a2）。静态 JS/CSS 服务的是分支，`pages.py` 服务端渲染却解析回主检出旧版（左栏「设置」套「设置」、优先回看计数徽标、题面「来源：」前缀）。
> 结论：**runtime 服务来源问题，不是 UI 设计缺陷**。禁止把「count-badge 存在 / 设置套设置 / 来源：前缀」当新缺陷报（分支已修 B2/B3/A5）。
> 建议：让 daemon worker 真正 import worktree 的 `pages.py`（核查 worker cwd / PYTHONPATH / runtime_source），或热重载不要回退到 primary。

---

## 复核口径

- 严重度沿用各原报告标注；跨报告簇取簇内最高严重度为主条目严重度，簇内其余原 ID 一并保留。
- 标「存疑」者（A-19 / A-20 / A-22 / B-16 / B-18 / D-08 / D-18 / C-16 / E-07 / M-04）为原报告已声明的两难/待验项，未硬凑为确定缺陷。
- 去重统计（第一轮）：原始 84 条（A 25 + B 21 + C 20 + D 19，MAIN M 5 + E 7 中 M-01 含 30 子项）→ 合并 5 个重复簇 + 折叠 D-13 入 D-02、C-06 归入命中区簇后，**主清单 60 条（高 11 / 中 36 / 低 13）**。
- 去重统计（第二轮 · 浮层/遮罩 checkpoint）：G 13 + H 15 + MAIN N 5 共 33 条浮层缺陷，与第一轮 60 条去重合并（N-01≈H-01、N-03≈C-15、N-04≈H-03/04、N-05≈H-08/11、H-02≈G-01/G-02 等重叠簇合并），**净新增 18 条 ⇒ 更新后主清单 78 条（高 13 / 中 50 / 低 15）**。F 报告两次未落盘，未纳入。
- 标「存疑」者（A-19 / A-20 / A-22 / B-16 / B-18 / D-08 / D-18 / C-16 / E-07 / M-04 / H-15）为原报告已声明的两难/待验项，未硬凑为确定缺陷。
