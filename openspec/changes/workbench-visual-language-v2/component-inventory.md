# 组件清单对齐表（spec 类名 ↔ 产品真实类名）

> **产物性质**：实测对齐表，**不是**设计权威。
> `design-notes/component-spec.md` §4 仍然是组件形态的**唯一设计权威**；
> 本文件只回答一个问题：**spec 里那 28 个组件，产品里现在到底叫什么、长什么样、有没有**。
>
> **对应任务**：`briefs/IMPL-F1b.md` 第一件（清单对齐）。
> **实测日期**：2026-10-22
> **实测口径**：工作区当前状态（`workbench/` 正在被并行 agent 修改，
> 本表所有计数与行号都是**当场 grep 出来的**，会随并行改动漂移 —— 复核命令见 §7）。

---

## 0. 方法与判定口径

### 0.1 实测命令

```bash
# CSS 规则（真实类名的来源）
grep -n "<类名>" workbench/server/static/workbench.css
grep -n "<类名>" workbench/server/static/agent-ui.css

# 服务端渲染的类名
grep -o "class=['\"][^'\"]*['\"]" workbench/server/pages.py | sort -u
grep -o "class=['\"][^'\"]*['\"]" workbench/server/records.py | sort -u

# JS 里动态拼出来的类名
grep -rn "className = \"<类名>\|class='<类名>\|class=\"<类名>" workbench/server/static/*.js
```

### 0.2 三种状态

| 标记 | 含义 | 判定依据 |
|---|---|---|
| ✅ | **有独立形态** | 产品里存在一个**专属的类名 + 专属的 CSS 规则**，视觉上自成一体 |
| ⚠️ | **存在但没有专属样式** | 组件**界面存在**，但**没有自己的 CSS 规则**：要么用**原生控件**（浏览器默认外观），要么**借用别的组件的样式**（裸类名 / 元素选择器），要么**只有 markup、样式零命中**（渲染不出来） |
| ❌ | **产品里根本没有这个界面** | 全仓 grep 不到任何承载该角色的界面 |

> ⚠️ 三类里最容易被忽略的是第三种细分：
> **「markup 已在、CSS 零命中」** —— 组件在 HTML 里存在，但**渲染出来是空的**。
> 本表把它们一律记为 ⚠️，并在「备注」列里**显式写明「样式零命中」**。

---

## 1. 总览

| 状态 | 条数 | 组件 |
|---|---|---|
| ✅ 有独立形态 | **13** | §4.1 主按钮、§4.2 次按钮、§4.3 文字按钮、§4.12 标签、§4.13 徽标、§4.14 状态圆点、§4.15 进度条、§4.17 题号格、§4.18 卡片、§4.21 空态、§4.22 骨架屏、§4.26 时间线节点、§4.28 Tab |
| ⚠️ 存在但没有专属样式 | **12** | §4.4 图标按钮、§4.5 输入框、§4.6 文本域、§4.7 自绘下拉、§4.8 复选框、§4.9 单选、§4.10 开关、§4.11 分段控件、§4.19 纸面层级、§4.20 沉底块、§4.23 吐司、§4.27 折叠段 |
| ❌ 产品里根本没有 | **3** | §4.16 分段进度条、§4.24 对话框、§4.25 工具调用卡 |
| **合计** | **28** | 与 spec §4.1–§4.28 一一对应，无遗漏、无多余 |

**一句话结论**：spec 的 `lk-` 前缀命名体系**基本没有落地**。
28 个组件里只有 **6 个**真的用 `lk-` 前缀且有 CSS：
`.lk-dot` / `.lk-progress__fill` / `.lk-card` / `.lk-empty` / `.lk-skeleton` / `.lk-streak`。
其余 22 个在产品里的名字**与 spec 完全不同**（`primary` / `outline` / `ghost` / `paper-dot` / `count-badge` / `agent-milestone` / `record-tab` …），
**或者压根没有**。

---

## 2. 逐组件对照表（28 行）

> 「产品里的真实类名」列写的是**实测到的、真正在给这个组件定型的那个类名**；
> 若产品里同时存在多套（同名不同形），全部列出并标 ⚠️ 多套并存。

| # | spec 组件 | spec 给的类名 | **产品里的真实类名** | 状态 | 备注 |
|---|---|---|---|---|---|
| §4.1 | 按钮 · 主按钮 | `.lk-btn` / `.lk-btn--primary` | **`button.primary`**（`workbench.css:939-945`）<br>+ `button.primary:disabled`（`:933-937`）<br>+ `button.sm` 尺寸档（`:938`）<br>+ `<a>` 变体 `.primary.button-link`（`pages.py:80`） | ✅ | spec 命名 **0 命中**；产品用**语义单词** `primary`。现状形态 = 蓝底 + `1px` **近黑描边** + `2px 2px 0` **硬阴影** + `18px` **胶囊圆角** + 高 `36px` —— 与 spec §4.1（无描边 / 柔影 / `--r-md` 12px / 44px 高）**四种都不同**。建议收敛：`button.primary` 保留类名，形态按 spec 重画；`.lk-btn--primary` 作为**第二类名**挂上去而不是重命名（避免一次性改 17 处 markup）。 |
| §4.2 | 按钮 · 次按钮 | `.lk-btn--secondary` | **`button.outline`**（`workbench.css:947-948`） | ✅ | spec 命名 0 命中。现状 = **透明底** + `1px var(--rule-control)` 边 + `18px` 胶囊圆角 + **无阴影**；spec §4.2 要的是 `--surface-card` 底 + `--elev-1` 柔影 + `--r-md` 12px。差在**底色**与**阴影**两处。 |
| §4.3 | 按钮 · 文字按钮 | `.lk-btn--text` | **`button.ghost`**（`workbench.css:946`，只有 `:hover` 一条规则） | ✅ | spec 命名 0 命中。现状 **只有一条 hover 规则**，其余全靠 `button` 基类（`:915-931`）—— 字体色/圆角/内距都是基类给的。spec §4.3 的 `--ink-muted` / `--r-md` / `font-weight:500` 都没写。 |
| §4.4 | 按钮 · 图标按钮 | `.lk-iconbtn` | **`button.icon-only`**（`pages.py:213,215,254,267,1035`，共 5 处）<br>· **CSS 零命中**（`workbench/server/static/*.css` 里 grep 不到 `.icon-only`）<br>· 另有 `button.icon-btn`（`pages.py:651-652`），**仅图谱页**，规则在 `workbench.css:3352-3357` | ⚠️ | 5 处产品用法**完全借用 `button` 基类**（36px 高、15px 内距、18px 胶囊圆角）—— 图标按钮和文字按钮现在**长得一模一样**，只有内容不同。`.icon-btn` 那 2 处是**图谱页冻结项**（spec §5.6），不要一起改。 |
| §4.5 | 输入框 | `.lk-input` | **元素选择器** `textarea, input[type="text"], input[type="number"], input:not([type])`（`workbench.css:962-975`）<br>+ `input:focus`（`:973`） | ⚠️ | spec 命名 0 命中；产品**没有类名**，靠**标签选择器**统一定型。现状 = 高 `32px`（spec 要 44px）、圆角 `10px`（spec 要 `--r-md` 12px）、`padding: 6px 10px`（spec 要 `0 14px`）。⚠️ `input:focus { outline: none }` 与 spec §6.1 A-1「不得出现 `outline: none`」**直接冲突**（spec 自检 S-11 说「§4 无一处」，但 CSS 里有 3 处，是产品侧的债）。 |
| §4.6 | 文本域 | `.lk-textarea` / `.lk-textarea--composer` | **元素选择器**（同 §4.5，`workbench.css:962`）<br>+ `#ai-input` 的 id 级覆写（Agent 贴底输入区） | ⚠️ | spec 命名 0 命中。现状文本域与输入框**共用一条规则**（两者没有分开定型），只有 `#ai-input` 一处单独覆写。spec §4.6 的「最小高 96px / `line-height: 1.6` / `resize: vertical`」都没落地。 |
| §4.7 | 自绘下拉（Select / Combobox） | `.lk-select` / `.lk-select__trigger` / `.lk-select__panel` / `.lk-select__option` | **原生 `<select>`**（`workbench.css:874-885`）<br>8 处：`.chapter-lens select`（`:627`）、`.knowledge-sort-bar select`（`:1099`）、`#graph-detail-panel select`（`:1325`）、`#ai-session-controls select`（`:1364`）、`.practice-count-label select`（`:1710`） | ❌→⚠️ | **自绘 combobox 在产品里完全不存在**。spec §5.2 计划的「8 处全部替换」**尚未开始**。<br>现状 = 原生 `<select>` + 元素规则（高 34px、圆角 `--r-xs`、`border-color` 转蓝 + `outline: none`）。<br>⚠️ 归为 ⚠️ 而非 ❌：**下拉这个界面是有的**（只是没自绘）。 |
| §4.8 | 复选框 | `.lk-check` / `.lk-check__box` | **原生 `<input type="checkbox">`**<br>· `practice-flow.js:968`（选项作答，多选分支）、`practice-flow.js:1652`（筛选维度）、`paper-practice.js:797`（试卷选项）、`kp-experience.js:99`（关联题目多选）<br>· 唯一一处调色：`.chapter-lens-toggle input { accent-color: var(--role-blue) }`（`workbench.css:626`） | ⚠️ | **完全用原生控件**，浏览器默认外观（系统蓝方框），**没有任何专属 CSS**。spec §4.8 要求的 20px 方框 / 6px 圆角 / 蓝底白勾 / 44px 命中区**一条都没有**。 |
| §4.9 | 单选 | `.lk-radio` / `.lk-radio__dot` / `.lk-choicegroup` | **原生 `<input type="radio">`**<br>· `practice-flow.js:968`（单选分支）、`paper-practice.js:797` | ⚠️ | 同 §4.8：纯原生，**零专属样式**。另外 spec §4.9 要求的 `fieldset` + `legend` 分组结构，产品里**也没有** —— 用的是裸 `<input>` 平铺。 |
| §4.10 | 开关 | `.lk-switch` / `.lk-switch__track` / `.lk-switch__thumb` | **`.lk-switch`（markup 在，CSS 零命中）**<br>· `pages.py:862-865, 880-891`（3 处设置项：主题 / 动效 / 声音）<br>· 实际在用形态：**`.chapter-lens-toggle`**（`pages.py:60` + `workbench.css:619-626`）—— 原生 checkbox + `accent-color` | ⚠️ | ⚠️ **典型「markup 在、样式没接上」**：`.lk-switch` / `.lk-switch__track` / `.lk-switch__thumb` 在 `pages.py` 里有 9 处命中，**在 `workbench.css` 里 grep 命中数为 0** ⇒ 三个开关**渲染出来是一条裸文字 + 空的 span**（轨道和滑块都没有样式）。<br>产品里**真正生效**的开关是 `.chapter-lens-toggle`（原生 checkbox 染色）。<br>⇒ 这条是**最该优先接上样式**的一条：它已经在页面上，只是没穿衣服。 |
| §4.11 | 分段控件 | `.lk-seg` / `.lk-seg__item` / `.lk-seg--semantic` / `.lk-seg--scroll` | **`.lk-seg`（markup 在，CSS 零命中）**<br>· `pages.py:870-876`（设置页「阅读字面」二选一）<br>· 另有 **`.seg`**（`pages.py:645`，`role="tablist"`，**图谱页**）→ 规则在 `workbench.css:3340-3350`，**图谱冻结项**<br>· 另有 **`button.rate`**（`workbench.css:949-959`）—— 1–5 自评胶囊组 | ⚠️ | `.lk-seg` / `.lk-seg__item` 在 `pages.py` 有 3 处，**CSS 零命中** ⇒ 设置页那组「衬线 / 无衬线」**渲染成两个没有样式的 label**（没有任何胶囊槽、没有选中态）。<br>⇒ 与 §4.10 同病：**markup 已落地、样式没接上**。 |
| §4.12 | 标签（Tag / Chip） | `.lk-tag` / `.lk-tag--blue` / `--yellow` / `--red` / `.lk-tag__dot` | **三套并存**：<br>① **`.agent-context-chip`**（`agent-ui.css:35-44`）—— Agent 上下文标签，`999px` 胶囊 + `1px hairline` 边 + 11px 字<br>② **`.chip`**（`workbench.css:3514-3522`）—— **图谱页**筛选 chip（`pages.py:664`），**硬编码 hex**（`#d7d1c6` / `#fffdf7`）+ 3px 圆角 + 9px 字 ⇒ 仿古遗留，**图谱冻结项**<br>③ **`.record-verdict`**（`workbench.css:2448-2500`）—— 记录页判定胶囊，`999px` + 内发丝线 + 几何符号 | ✅ | spec 命名 0 命中。产品里**同一个角色有三个不同的实现**，圆角（胶囊 / 3px / 胶囊）、字号（11 / 9 / 12）、边界（描边 / 内发丝线）**全不一致**。⚠️ ② 是硬编码 hex 的仿古件，**本轮不要动**（图谱冻结），但**不要把它当参照物**。 |
| §4.13 | 徽标（Badge） | `.lk-badge` / `.lk-badge--alert` | **`.count-badge`**（`workbench.css:831-841`）<br>· `pages.py` 侧栏小节标题的计数徽标 | ✅ | spec 命名 0 命中。现状 = `min-width: 18px` + `999px` 胶囊 + `--surface-card` 底 + `--ink-muted` + **11px** 字。spec §4.13 要 20px 最小宽 + `--r-round` 圆 + `--surface-sunken` 底 + `--ink-strong` + 12px/700 + `tabular-nums`。**产品里没有「红底阻塞计数」这一档**（`.lk-badge--alert` 无对应物）。 |
| §4.14 | 状态圆点 | `.lk-dot` + `--filled` / `--half` / `--dash` / `--cross` / `--check` / `--blue` / `--yellow` / `--red` / `--ink` / `--muted` / `--sm` / `--lg` / `--on-paper` / `--on-ink` | **`.lk-dot`**（`workbench.css:1112-1165`）<br>· 已实现：`--red` / `--yellow` / `--ink`（颜色，实心）+ `--cross` / `--dash` / `--check`（几何，挖空画线）<br>· `pages.py:17-19` 三态映射、`:102` 单点 | ✅ | **spec 命名**唯一**落地且对齐**的一条（但只落地了 6 个变体）。<br>⚠️ **缺 8 个变体**：`--filled`、`--half`、`--blue`、`--muted`、`--sm`、`--lg`、`--on-paper`、`--on-ink`。<br>· `pages.py:102` 写的是 `lk-dot lk-dot--red lk-dot--filled`，而 **`.lk-dot--filled` 在 CSS 里没有规则** ⇒ 它**碰巧**渲染成实心红点（因为 `--red` 已经把 `--dot-fill` 设成 `--role-red`），但**「实心」这件事是由颜色变体顺带实现的，不是由 `--filled` 实现的** —— 一旦哪天真按 spec 加上 `--filled`（= 空心环语义），这处就会翻车。<br>· 圆角用 `--r-round`（50%），spec §4.14 明写「圆点用 `--r-pill`，**不用** `--r-round`」—— 12×12 正方形上两者视觉相同，但**取值与 spec 不一致**。 |
| §4.15 | 进度条 | `.lk-progress` / `.lk-progress__fill` | **真正在用的三套**：<br>① **`.record-run-progress`**（`workbench.css:2424-2428`）—— 8px 轨道 + 蓝填充<br>② **`.record-rating-track`**（`:2390-2394`）—— 8px 轨道 + 黄填充<br>③ **`.record-verdict-dist-track`**（`:2407-2411`）—— 8px 轨道 + 三态填充<br>④ **`.lk-progress`**（`pages.py:388`）—— **只有 `__fill` 子规则**（`workbench.css:2923-2929`），**轨道本身没有规则** | ⚠️ | spec 的 `.lk-progress` 轨道**在 CSS 里没有定义**（`grep -n "lk-progress"` 只有 `@keyframes` + `__fill` + `.is-filled`）⇒ 完成页那条「进度带」**渲染不出来**（div 无高度、无底色）。<br>真正在跑的是 `.record-run-progress` 一族：**8px 直角条**（无圆角）、轨道底 `--surface-sunken`、填充纯色。spec §4.15 要的是 `--r-pill` 胶囊 + `--veil-active` 轨道 + `width` 过渡。 |
| §4.16 | 分段进度条（Segmented progress） | `.lk-steps` / `.lk-steps__seg` | **无** | ❌ | 全仓 grep `.lk-steps` **零命中**（CSS / pages.py / JS 全无）。<br>产品里最接近的是 **`.lk-flames`**（`workbench.css:2823-2842`，连对火苗，12×16px `clip-path` 火苗剪影 + `--role-yellow` 点亮）+ **`.lk-streak`**（`:2870-2913`，沉底面 + 左竖条强调），但那是**火苗图标串**，不是**分段条**。<br>⇒ 该组件是**全新能力**，spec §4.16 的规则要直接当设计用。 |
| §4.17 | 题号格 | `.lk-qcell` / `.lk-qgrid` / `.lk-qgrid__legend` | **`.paper-dot`**（`workbench.css:3652-3674`）<br>· 容器 `.paper-dots`（`:3651`）<br>· 状态类：`.state-filled`（黄）/ `.state-locked`（蓝洗底）/ `.state-correct`（墨环 + 勾）/ `.state-wrong` / `.state-stuck`（红洗底）/ `.is-current`（蓝 `outline`）<br>· markup：`pages.py:357`（`<nav id='paper-dots'>`）+ `paper-practice.js:611` 动态拼类名 | ✅ | spec 命名 0 命中；**spec §4.17 自己就写了「现状 `.paper-dot`」**，两边对得上。<br>⚠️ 形态差得远：现状 **34px 圆**（spec 要 **36px 方 + `--r-md` 12px**）、描边 `1px var(--ink-muted)`（spec 要 `inset 0 0 0 2px`）、当前题用 `outline: 3px`（spec 要黄实心 + `scale(1.06)`）。 |
| §4.18 | 卡片 | `.lk-card` | **`.card`（基类，`workbench.css:1019-1026`）+ `.lk-card`（`workbench.css:1034-1040`，同规格复述）**<br>· 另有 `.goal-card` / `.workspace-card` / `.practice-set-card` / `.agent-artifact-card` / `.record-row` 等**各自带覆写** | ✅ | **唯一「spec 类名真的落地」的组件**，但 `.lk-card` 的 CSS 注释自己写着「**与 `.card` 基类同规格**」⇒ **两个类名一份规则**，等于没有收敛。<br>⚠️ 更麻烦的是**覆写散落**：`.practice-set-card` 加了 5px 黄顶条（`:1713`）、`.practice-question-card` 加了 4px 蓝左边条、`.agent-artifact-card` 加了 4px 蓝左边条（`agent-ui.css:421-427`）—— **卡片语言已经分叉成好几种**。 |
| §4.19 | 纸面层级（Paper level） | `.lk-surface-0` / `-1` / `-2` / `-3` | **无类名** —— 直接用 token：<br>`--surface-base` / `--surface-card` / `--surface-raised` / `--surface-sunken`（`workbench.css:133-138` 暖纸、`:281-286` 夜纸）<br>`--surface-sunken` 全文件 **31 处**引用（含 4 处 token 定义 / 别名）＋ 大量 `--surface-card` 引用 | ⚠️ | spec 的 `.lk-surface-0..3` **零命中**。产品的做法是**直接用 token**，**没有层级类** ⇒ 「哪一层」这件事**没有单一出口**：同一个 L1 在不同文件里被写成 `--surface-card`、被写成 `.card`、被写成 `--surface-raised`，全凭各处自觉。<br>⇒ 这是 spec 落地时**最需要补的一层**（不是新画一套，而是给四个面各一个类名 + 一处权威规则）。 |
| §4.20 | 沉底块（Sunken block） | `.lk-sunkenblock` | **无同名类** —— 用「`--surface-sunken` 底 + `inset 0 0 0 1px var(--rule-hair)`」这一组合，共 4 处：<br>① **`.msg.user`**（`workbench.css:1003-1012`）—— 用户消息<br>② **`.lk-empty`**（`:1234-1244`）—— 空态面板<br>③ **`.record-filter-note`**（`:2230-2234`）—— 记录页提示块<br>④ **`.lk-streak`**（`:2870-2890`）—— 连对计数器底 | ⚠️ | spec 命名零命中。**规则已经存在，但被复制了 4 遍**（每处各写一遍 `background` + `border-radius` + `box-shadow: inset`）⇒ 改一次圆角要改 4 个地方。<br>⇒ 建议：**抽一个 `.lk-sunkenblock` 基类**，4 处改为挂它 + 各自的变体（这正是 spec §4.20 想要的东西）。 |
| §4.21 | 空态 | `.lk-empty` / `.lk-empty__art` / `.lk-empty__text` / `.lk-empty__action` | **`.empty-state`（`workbench.css:1222`）+ `.lk-empty`（`:1234-1255`）**<br>· `pages.py:84-88` 输出 `<div class='empty-state lk-empty'>` | ✅ | **spec 类名真的落地**（`.lk-empty` 三个子元素也落地）。<br>⚠️ 现状与 spec 有两处差：插画 **180px**（spec 要 144px）、**面是沉底块**（spec §4.21 原文没规定面，spec 的示例 CSS 也没给面 —— 这里的「沉底」是实现侧的选择，**算实现先行，需主会话裁决是否保留**）。 |
| §4.22 | 骨架屏 | `.lk-skeleton` / `.lk-skeleton--text` / `--block` / `--avatar` | **`.lk-skeleton`**（`workbench.css:2773-2787`）+ `.lk-skeleton--text`（`pages.py:345`，**CSS 零命中**） | ✅ | spec 类名落地了，但**只有基类**：`--text` / `--block` / `--avatar` 三个尺寸变体**都没写** ⇒ `pages.py:345` 那个 `<span class='lk-skeleton lk-skeleton--text'>` **没有高度，渲染不出来**。<br>⚠️ **与 spec 直接冲突**：现状微光用 `linear-gradient`（`:2776-2780`），spec §4.22 明写「**不用渐变**（全局禁用界面渐变）」，spec 的写法是 32% 宽**实色块平移**。 |
| §4.23 | 吐司（Toast） | `.lk-toast` / `.lk-toast__action` | **`.toast`**（`workbench.css:3570-3576`）<br>· **只有图谱页在用**：`pages.py:696`（`#graph-toast`）+ `workbench.js:1482`<br>· 规则写在**图谱仿古段**里：近黑底 `#26231f` + `3px` 圆角 + **10px** 字 + 底部居中 | ⚠️ | **工作台主体（记录 / 练习 / 试卷 / 设置 / Agent）里没有吐司**。唯一那一个是**图谱页仿古件**（硬编码 hex、底部居中、10px 字），且图谱是冻结项。<br>⇒ 现状列对吐司来说**基本等于「没有」**，只能当反例看。spec §4.23 要的是右上角、`--surface-raised` 浮起面、13px 字。 |
| §4.24 | 对话框（Dialog） | `.lk-dialog` / `.lk-dialog-backdrop` / `.lk-dialog__title` / `.lk-dialog__body` / `.lk-dialog__actions` | **无** | ❌ | 全仓 grep `.lk-dialog` / `dialog` / `modal` **零命中**（CSS 无、pages.py 无、JS 无）。<br>产品里的「打断式确认」是两种**都不是模态**：<br>① **原生 `window.confirm()`** —— `workbench.js:2979, 3019, 3099, 4843, 5360`（删试卷 / 重开练习 / 删目标 / 整批回滚 / 删会话）<br>② **Agent 的内联「需要确认」卡** —— `.agent-approval-card`（`agent-ui.css:341-347`，**替换输入区**，不弹层）<br>⇒ spec §4.24 是**全新能力**。 |
| §4.25 | 工具调用卡（Tool-call card） | `.lk-tool` / `.lk-tool__head` / `.lk-tool__name` / `.lk-tool__cost` / `.lk-tool__body` / `.lk-tool__payload` | **无** | ❌ | grep `tool_name` / `toolName` / `tool-call` / `toolCall` **全仓零命中** —— 产品**不渲染工具调用**。<br>最接近的三个件：<br>① **`.ai-activity`**（`workbench.css:1453-1462`）—— 4px 左边条的状态块<br>② **`.ai-plan-step`**（`:1394-1426`）—— 计划的一步（12px 方 marker + 三态）<br>③ **`.ai-plan-output`**（`:1436-1451`）—— 步骤里的 `<details>` 折叠输出<br>⇒ spec §4.25 是**全新能力**，但可以复用 ②③ 的现成结构。 |
| §4.26 | 时间线节点 | `.lk-timeline` / `.lk-timeline__item` / `.lk-timeline__dot` | **两套并存**：<br>① **`.agent-milestone`**（`agent-ui.css:292-336`）—— 20px 列 + **18px 圆环** marker（带序号数字）+ 发丝线上边线<br>② **`.ai-plan-step`**（`workbench.css:1394-1426`）—— 12px 列 + **9px 方** marker（`--role-blue` 空心 / 实心脉冲 / 黄 / 红）+ `border-top` 分隔 | ✅ | spec 命名零命中。**同一个「步骤序列」角色，两处用了两套几何**（圆环带数字 vs 空心方块）—— 视觉上像两个产品。<br>⇒ 这是**最值得让所有者挑的一个**：两套都在页面上同时出现（Agent 里程碑 vs 计划步骤），必须二选一或合并。 |
| §4.27 | 折叠段（Disclosure） | `.lk-disclosure__head` / `.lk-disclosure__body` | **原生 `<details>` / `<summary>`，四处各写各的**：<br>① `.ai-plan-output summary`（`workbench.css:1437`）—— 11px 灰字<br>② `.practice-set-item-body > summary`（`:1733-1740`）—— `▸`/`▾` 字符 + 3 列 grid<br>③ `.attempt-history summary`（`:2524`）—— 13px 灰字<br>④ `.problem-topic summary`（`:1208`）<br>另：`.agent-aux-collapse`（`agent-ui.css:289-290`，28×28 图标按钮）、`.control-toggle`（`workbench.css:3497-3505`，**图谱冻结项**） | ⚠️ | spec 命名零命中，**没有共享组件**，四处 `<summary>` 的箭头、字号、间距**各不相同**（④ 甚至连 `cursor: pointer` 都没写）。<br>⚠️ 注意 spec §4.27 写的「现状用 `<details>`」是对的，但**产品里是 4 种不同的 details**，不是 1 种。 |
| §4.28 | Tab（标签页） | `.lk-tablist` / `.lk-tab` | **`.record-tabs`（容器）+ `.record-tab`（项）**（`workbench.css:2217-2229`）<br>· markup：`records.py:611-614`（`<a class='record-tab'>` + `.active`）<br>另：图谱页 `.seg` + `role="tablist"`（`pages.py:645`，**冻结项**） | ✅ | spec 命名零命中。现状 = `<a>` 标签 + `8px 11px` 内距 + 底部 `3px` 蓝指示条（`.active`）+ 容器底部 `1px` hairline 分隔线；spec §4.28 要 48px 高 + `0 16px` 内距 + `--r-md` 圆角 hover 底 + 指示条 `left/right: 12px`。⚠️ 现状是**链接式 Tab**（`<a>`，可右键新开），spec 的示例是 `<button>` —— 换实现要留意 `aria-selected` 语义。 |

---

## 3. 命名分歧汇总（给主会话的收敛建议）

| spec 家族 | spec 类名 | 产品里的等价物 | 建议 |
|---|---|---|---|
| 按钮族 | `.lk-btn--primary/--secondary/--text` | `button.primary` / `button.outline` / `button.ghost` | **保留产品类名**（17+21+14 处 markup），把 spec 的形态**挂**上去：`.primary` 改画 + 可选加 `.lk-btn--primary` 之类的第二类名做语义锚点 |
| 卡片 | `.lk-card` | `.card` + `.lk-card`（同规格复述） | 保留 `.card` 基类，把 `.lk-card` 变成**真正的子类**（只覆写差异），并把 `.practice-set-card` / `.agent-artifact-card` 的**左边条/顶条**收敛成「卡片变体」而不是各写各的 |
| 纸面层级 | `.lk-surface-0..3` | 无（直接用 token） | **补 4 个类名**作为层级的单一出口（`--surface-*` 保持不变，只加类名） |
| 沉底块 | `.lk-sunkenblock` | 4 处各写一遍 `--surface-sunken` + 内发丝线 | **抽基类**，4 处挂载 |
| 状态点 | `.lk-dot` | `.lk-dot` | 类名已对齐；**补齐缺的 8 个变体**（尤其 `--filled`，`pages.py:102` 已经用了但没样式） |
| 分段控件 | `.lk-seg` | `.lk-seg`（样式零命中）/ `.seg`（图谱）/ `button.rate` | **先把 `.lk-seg` 的样式接上**（markup 已就位），再决定 `button.rate` 是否并进来 |
| 开关 | `.lk-switch` | `.lk-switch`（样式零命中）/ `.chapter-lens-toggle`（原生） | **先把 `.lk-switch` 的样式接上** |
| 骨架屏 | `.lk-skeleton` | `.lk-skeleton` | 补 `--text` / `--block` / `--avatar` 三个尺寸变体；**渐变 → 实色块平移**（spec 明禁渐变） |

**类名冲突提醒**：`.seg`（图谱页）与 spec 的 `.lk-seg`（分段控件）**语义不同**（前者是 tablist，后者是 radiogroup）；
`.chip`（图谱筛选）也不是 spec §4.12 的静态标签（它可点）。⇒ **图谱页的 `.seg` / `.chip` 不要与新组件混用**。

---

## 4. 产品里缺失的形态（⚠️ + ❌ 汇总，共 15 条）

### 4.1 ❌ 完全没有（3 条）

| # | 组件 | 产品现状 | 说明 |
|---|---|---|---|
| §4.16 | **分段进度条** | 无 | spec §4.16 的「段 + 几何双编码」是**全新能力**；产品里只有 `.lk-flames` 火苗串可以借鉴 |
| §4.24 | **对话框** | 无 | 只有 `window.confirm()`（浏览器弹窗）与 Agent 内联确认卡；spec §4.24 的遮罩 / 焦点陷阱 / 焦点归还**全部要新建** |
| §4.25 | **工具调用卡** | 无 | 产品不渲染工具调用；可复用 `.ai-plan-step` + `.ai-plan-output` 的结构 |

### 4.2 ⚠️ 有界面、没有专属样式（12 条）

| # | 组件 | 现状载体 | 缺什么 |
|---|---|---|---|
| §4.4 | 图标按钮 | `button.icon-only`（5 处，CSS 零命中） | 40×40 / 12px 圆角 / 44px 命中区 / `aria-label` 强制 |
| §4.5 | 输入框 | 元素选择器 | 44px 高 / `--r-md` / 聚焦蓝环 / **清掉 `outline: none`** |
| §4.6 | 文本域 | 元素选择器（与输入框同规则） | 与输入框**分开**定型；行高 1.6；composer 变体 |
| §4.7 | 自绘下拉 | 原生 `<select>`（8 处） | 整块 combobox（触发器 / 面板 / 选项 / 键盘 / ARIA）+ hidden input 承载载荷 |
| §4.8 | 复选框 | 原生 `<input type=checkbox>` | 20px 方框 + 6px 圆角 + 蓝底白勾 + 整行命中区 |
| §4.9 | 单选 | 原生 `<input type=radio>` | 20px 圆 + 白内核点 + `fieldset`/`legend` 分组 |
| §4.10 | 开关 | `.lk-switch`（markup 在，CSS 零命中） | 44×26 胶囊轨道 + 20px 滑块 + 开态蓝 |
| §4.11 | 分段控件 | `.lk-seg`（markup 在，CSS 零命中） | 沉底槽 + 选中卡 + roving tabindex |
| §4.19 | 纸面层级 | 散用 `--surface-*` token | 四个面各一个类名 + 单一权威规则 |
| §4.20 | 沉底块 | 4 处各写一遍 | 抽基类，去掉复制 |
| §4.23 | 吐司 | `.toast`（**仅图谱页**，仿古硬编码） | 工作台主体右上角吐司 + 状态点 + 层级（modal > toast） |
| §4.27 | 折叠段 | 原生 `<details>`，**四种写法** | 共享的 disclosure 头 / 体 / 箭头 / 展开动画 |

---

## 5. 需要主会话裁决的点（本表只登记，不自行拍板）

| # | 冲突 | 说明 |
|---|---|---|
| Q-1 | **spec §4.21 空态的「面」** | spec §4.21 原文没规定空态用什么面，实现侧先用了**沉底块**（`.lk-empty` = `--surface-sunken` + 内发丝线）。这是**实现先行**，需确认是否写回 spec |
| Q-2 | **spec §4.22 骨架屏「不用渐变」** | 现状 `.lk-skeleton::after` 用了 `linear-gradient`（`workbench.css:2776`），与 spec 明文冲突 ⇒ 以 spec 为准则要改产品；或改 spec。二选一 |
| Q-3 | **spec §6.1 A-1「不得 `outline: none`」** | 产品侧有 3 处（`workbench.css:885, 973` 等）⇒ spec 自检 S-11 只核了 §4 片段，没核产品。**债在产品侧**，需登记 |
| Q-4 | **`.seg`（图谱）vs `.lk-seg`（分段）语义冲突** | 建议保留图谱 `.seg` 不动，新组件一律 `lk-` 前缀；spec §5.6 已把图谱列入冻结项，本表一致 |
| Q-5 | **`.chip`（图谱筛选）不是「静态标签」** | spec §4.12 明确「标签不可点击」，而图谱 `.chip` 是可点的筛选按钮 ⇒ 新标签组件不能复用 `.chip` 这个名字，否则语义打架 |
| Q-6 | **Tab 的元素类型** | 产品用 `<a>`（可右键新开），spec 示例用 `<button>`。换实现要保住 `role="tablist"`/`aria-selected` 语义 |
| Q-7 | **`.lk-progress` 轨道无规则** | 完成页那条进度带**当前渲染不出来**；是「补轨道规则」还是「改用 `.record-run-progress`」，需定 |
| Q-8 | **`.lk-dot--filled` 是一条空规则** | `pages.py:102` 写了 `.lk-dot--filled`，但 CSS 里**没有这条规则**；它现在能渲染成实心红点**只是因为 `.lk-dot--red` 顺手把 `--dot-fill` 设成了 `--role-red`**。若后续按 spec 补 `--filled`（spec §4.14 里 `filled` 是几何集的一档），这处行为会改变 ⇒ 补规则前要先定 `--filled` 的语义 |
| Q-9 | **`.lk-dot` 圆角取值与 spec 不一致** | 现状 `--r-round`（`workbench.css:1119`），spec §4.14 明写「圆点用 `--r-pill`（胶囊档），**不用** `--r-round`」。12×12 正方形上视觉相同，但**取值口径要统一**（权威表 §2.1 把 `--r-pill` 明确留给「状态圆点」） |

---

## 6. 现状里已知的「仿古 / 硬编码」残留（**不要当参照物**）

| 位置 | 现象 |
|---|---|
| `workbench.css:3484-3585` | **图谱仿古段**（`.floating` / `.controls` / `.control-toggle` / `.chip` / `.toast` / `.zoom` / `.legend`）—— 大量硬编码 hex（`#d7d1c6` / `#fffdf7` / `#26231f` / `#9a9388`…）、9px 小字、`backdrop-filter: blur(5px)`（spec 全局禁玻璃拟态） |
| `workbench.css:3175-3200` 附近 | `.graph-*` 一族（spec §5.6 冻结项） |
| `workbench.css:3514-3522` | `.chip`：3px 圆角 + 9px 字 + 硬编码 hex |
| `workbench.css:3570-3576` | `.toast`：近黑底 + 3px 圆角 + 10px 字 |

⇒ 这些是**图谱页冻结项**，spec §5.6 已列明「不改」。本表的「现状」列对它们只做**记录**，不做参照。

---

## 7. 复核命令（可重跑）

```bash
cd "D:/Projects/Academic Workflow/lesson-kit"

# 1) spec 命名到底落地了几个
grep -c "lk-btn\|lk-input\|lk-textarea\|lk-select\|lk-check\|lk-radio\|lk-tag\|lk-badge\|lk-steps\|lk-qcell\|lk-surface-\|lk-sunkenblock\|lk-dialog\|lk-tool\|lk-timeline\|lk-disclosure\|lk-tablist" workbench/server/static/workbench.css

# 2) 每个 spec 家族在产品里的真实类名
grep -n "^\.paper-dot\|^\.count-badge\|^\.agent-milestone\|^\.record-tab\|^\.lk-dot\|^\.lk-empty\|^\.lk-skeleton\|^\.card {\|^\.lk-card {\|^\.toast {\|^\.ai-plan-step\|^\.ai-activity\|^\.msg\.user\|^\.record-run-progress" workbench/server/static/workbench.css
grep -n "^\.agent-milestone\|^\.agent-context-chip\|^\.agent-artifact-card\|^\.agent-aux-collapse" workbench/server/static/agent-ui.css

# 3) 「markup 在、样式零命中」的三条
grep -c "\.lk-switch" workbench/server/static/workbench.css   # 0
grep -c "\.lk-seg"   workbench/server/static/workbench.css   # 0
grep -c "\.icon-only" workbench/server/static/workbench.css  # 0

# 4) 缺失的三条（应全为 0）
grep -c "lk-steps\|lk-dialog\|lk-tool" workbench/server/static/workbench.css   # 0

# 5) 原生控件统计
grep -c "<select"   workbench/server/pages.py   # 8
grep -c "<input"    workbench/server/pages.py   # 14
grep -c "<textarea" workbench/server/pages.py   # 6
grep -ro "<button"  workbench/ | wc -l          # 68
```

> ⚠️ `workbench/` 正被并行 agent 修改，**计数会漂**；
> 复核时请以**类名是否存在**为准（类名比计数稳），计数只作参考。
