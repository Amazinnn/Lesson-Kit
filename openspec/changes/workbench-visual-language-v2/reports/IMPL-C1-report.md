# IMPL-C1 报告 —— 组件形态裁定 A 类 · **样式波**（workbench.css + agent-ui.css）

> **权威源**：`component-spec.md` **§4.30**（各组件的**唯一形态定义**）
> > 各节「形态裁定」框 > 各节正文；裁定原始记录 `design-notes/styleboard-picks.md`；
> 任务书 `briefs/IMPL-C1.md`；`decisions.md` **A-115**（28 条裁定 + 尺寸口径）
> 与 **A-117**（骨架屏「呼吸」判据口径定稿）。
> **本波范围**：A 类 **24 条**（§4.1–4.6 · §4.8–4.15 · §4.17–4.23 · §4.26–4.28）——
> **只改外观**，不改请求序列 / 载荷键 / DOM 身份 / 事件绑定 / 判定分支。
> **文件所有权**：本波只写 `workbench/server/static/workbench.css` ·
> `workbench/server/static/agent-ui.css` + 本报告。

---

## 0. 状态摘要

| 项 | 值 |
|---|---|
| **A 类 24 条** | **24 / 24 全部落盘**（逐条实测见 §3） |
| **其中「只落形态、markup 待用」的** | **5 类**（§4.12 `.lk-tag` · §4.13 `.lk-badge` 别名 · §4.14 `.lk-dot--ring`/`--half` · §4.19 `.lk-surface-0..3` · §4.23 `.lk-toast`）—— 已登记，见 §3 与 §9 |
| **仓库级验证** | **7 条命令全绿**（见 §7） |
| **图谱零差异** | **图谱区段逐字节不变** ✔ · **R-2 差异像素 0** ✔ · **夜纸下展开章节透镜整页 AE = 0**（口径内）✔ |
| **骨架屏（§4.22）** | **判据 `3.4-3` 由 FAIL 转 PASS** ✔（5/5 骨架块呼吸；降级档 5/5 有体积） |
| **命中区 ≥44px** | **逐条实测达标**（见 §6） |
| **本波复核中修掉的真问题** | **5 处**（见 §2）＋ **A-126 三条裁决的落地**（见 §10） |
| **未做 / 打折的地方** | **如实登记 7 项**（见 §11）；A-126 已裁的 3 条已落地（§10），**剩余 3 条留登记**（见 §9） |

---

## 1. 已落盘路径 + commit 清单

### 1.1 文件

| 文件 | 改动 | 说明 |
|---|---|---|
| `workbench/server/static/workbench.css` | 主体 | 21 条 A 类落点 + 骨架屏 + 吐司 + 时间线 + 折叠段 + Tab 合并 |
| `workbench/server/static/agent-ui.css` | 时间线 / Agent 输入区 | §4.26（`.agent-milestone` 与 `.ai-plan-step` 合一套）· §4.6 特例（`#ai-input`） |
| `openspec/changes/workbench-visual-language-v2/reports/IMPL-C1-report.md` | 本报告 | — |
| `openspec/changes/workbench-visual-language-v2/reports/IMPL-C1-shots/` | 12 张截图 | 暖纸 + 夜纸各 6 张 |

### 1.2 commit 清单（**9 个 CSS commit**，全部只含上面那两个 CSS 文件）

| # | hash | 主题 | 内容 | 改动量 |
|---|---|---|---|---|
| 1 | `c6a8b2f5` | §4.1–§4.6 按钮族与输入控件 | 主按钮无影平底 / 次按钮沉底 / 文字按钮带箭头 / 图标按钮 40×40 圆形 / 输入框 44px / 文本域 96px | workbench.css +175 / agent-ui.css +3 |
| 2 | `5739d421` | §4.10–§4.15 控件族 | 迷你开关 32×18 / 药丸分段 / 角色色标签 / 胶囊徽标 / 状态圆点 10px + 三档几何 / 胶囊进度 8px | workbench.css +216 / −56 |
| 3 | `62f6597f` | §4.17–§4.21 表面族 | 题号格 36px 方 / 卡片 24px 留白 / 纸面四层 / 竖线沉底 / 卡面空态 | workbench.css +200 / −52 |
| 4 | `87191d79` | §4.22 骨架屏改**呼吸式** | 删 `lk-skeleton-sweep` + `.lk-skeleton::after` 横扫覆盖层与渐变；改 `lk-skeleton-breathe`（只动 `opacity`） | workbench.css +24 / −25 |
| 5 | `5b5e0888` | §4.23 吐司 spec 形态 | `.lk-toast` 右上角浮起面 + 12px 圆角 + 13px 字 + 左侧 10px 状态点 + 浅底深字 | workbench.css +53 |
| 6 | `07d4799b` | §4.26–§4.28 | 时间线两套几何合一 / 折叠段手风琴 / Tab 与分段控件合并成同一个类 | workbench.css +192 / agent-ui.css ±40 |
| 7 | `680de9e6` | §4.8 / §4.9 样式底座 | 复选 / 单选整行选中的**样式底座**（markup 侧另有一波，**现已取消**，见 §5） | workbench.css +133 |
| 8 | **`7012dc32`** | **验收复核修正**（本轮新增） | §4.8/§4.9 改挂既有类名 + 删三处死规则 + 禁用选中态可辨性 + A-123 链接间距 | workbench.css +148 / −127 |

> **第 9 个 commit** = 本报告 + 12 张截图（`docs(v2): IMPL-C1 报告 …`）——
> 与前 8 个一样**只碰 `workbench/server/static/` 下的两个 CSS + 报告目录**。
> **第 10 个 commit** = A-126 的三条裁决落地（见 **§10**）——
> 同样**只碰 `workbench/server/static/workbench.css`**。

> ⚠️ **commit 7（`680de9e6`）的落点已被 commit 8 推翻**：它新起的
> `.lk-check__row` / `.lk-radio-row` / `.lk-check__box` / `.lk-radio__dot`
> 四族在 markup 里**零命中** ⇒ 已在 commit 8 里**整族删除**，改挂既有类名
> （详见 §5）。**该 commit 的「排除了 markup 侧」这一条也随之作废**。

---

## 2. 本轮复核发现并修掉的 **5 处真问题**

### 2.1 §4.8 / §4.9 —— 新起的类名在 markup 里零命中（**整族重挂**）

- **事实**：`grep -rn "lk-check\|lk-radio" pages.py static/*.js *.py` ⇒ **空**。
  而**行级容器早就存在**：试卷流 `paper-practice.js:688` 造
  `<label class="option-row">`，练习流 `practice-flow.js:907` 给 `<label>`
  挂 `option-selected`；两者都住在 `<fieldset class="problem-options">` 里。
- **处置**：四族死规则**整族删除**；样式改挂既有类名（详见 §5）。
- **连带**：**IMPL-C2 的 markup 改造取消**（前提「行容器需要 markup 改造」不成立）。

### 2.2 禁用 + 选中态的标记**看不见**（**真 bug，已修**）

- **实测**：答完 / 锁定后 `input[type=radio]` 是 `checked + disabled`。
  按 spec 的禁用档（沉底面 `--surface-base`）⇒ 白色标记 `--ink-on-role` 落在
  `#fdf8ef` 上 ⇒ **对比只有 1.04:1（暖）/ 1.06:1（夜）** ⇒ **白点肉眼不可见**。
- **处置**：改成「**几何不变**（仍是实心盘 + 白点）、色降到 `--ink-disabled`、
  标记取 `--surface-base`」⇒ **3.59:1（暖）/ 3.61:1（夜）**。
- **依据**：§4.14 的同款口径 ——「disabled ⇒ 点降到 `--ink-disabled` 且
  **不改变几何**（几何仍可辨）」。

### 2.3 `.problem-topic` 是**死选择器**（**已删**）

- **事实**：markup 里**零命中**；`tests/workbench/test_ui_routes.py:783` 还
  **明确断言** `"problem-topic" not in body` ⇒ 它是**已被淘汰的旧类名**。
- **处置**：原先给它写的整套 §4.27 手风琴规则**删除**（死规则）。
  ⚠️ **没有**为了让规则有用而把它加回 markup。

### 2.4 图谱补钉②是**死规则**（**已删**）

- **事实**：`grep -rn "detail-actions" *.js *.py` ⇒ 全仓只有
  `workbench.js:2377` 一处；那里渲染的是 `<a class='ghost'>打开知识点</a>`，
  **没有 `.primary`** ⇒ 补钉②永不命中。
- **处置**：删除该规则并改写注释。**补钉① 保留**（`#graph-search` 的
  `min-height: 32px` 是真的会被基类撑到 44px）。
- **附带**：图谱区段自己那条 `#graph-detail-panel .detail-actions .primary`
  是**历史遗留的硬编码样式**，在**冻结区段内** ⇒ **本波不碰**。

### 2.5 A-123 —— 记录中心提示块的标签与链接没有分隔（**已修**）

- **事实**：R-54 去掉了句号、R-55 判「查看全部记录」为「留」⇒ 渲染成
  「按单题过滤查看全部记录」。
- **处置**：`.record-filter-note a { margin-left: var(--sp-2); }`
  —— **零文字**，只加外边距（用现有 token，不硬编码像素）。

---

## 3. 逐条「改前 → 改后 + 实测值」（**24 条 A 类一条不落**）

> 「改前」取自 `c6a8b2f5~1`（C1 首波之前的 HEAD）的 `workbench.css`；
> 「实测」全部来自**当场**的真实浏览器 `getComputedStyle` / `getBoundingClientRect`
> / `document.elementFromPoint`（Chromium 1440×900，`device_scale_factor=1`）。
> 暖纸 = 亮色主题，夜纸 = `html[data-theme="night"]`。

### §4.1 主按钮 · **B 无影平底**（`btn-primary-flat`）

| | 值 |
|---|---|
| **改前** | `border: 1px solid var(--ink-strong)`（近黑描边）· `box-shadow: 2px 2px 0 var(--ink-strong)`（硬阴影）· 高度**未写**（继承基类 36px） |
| **改后** | `border: 0` · `box-shadow: none` · `height: 40px` · `border-radius: var(--r-md)`（12px）· hover 只抬 1px（`transform`，走基类 `transition: transform`）· 底色**瞬切**（不进 transition） |
| **实测** | `box-shadow: none` ✔ · `border: 0px none` ✔ · `h = 40` ✔ · `radius 12px` ✔ · 底色 `rgb(43,98,232)` = `--role-blue` ✔ · hover 位移 `translateY(-1px)` ✔ |
| **命中区** | 视觉 40px + `::before { inset: -2px 0 }` ⇒ **44px**（见 §6） |
| **`.sm` 档** | ⚠️ **A-126 裁决 2**：形态高度改走**零特异度**（`:where(button.primary, button.outline)`）⇒ `.sm` 真正生效（**28px**，不再是 40px）⇒ 命中区改走 **§3.1 方法 2（容器间距）**、`.sm` **不挂**伪元素外溢（见 §10.2） |

### §4.2 次按钮 · **C 沉底次按钮**（`btn-secondary-sunken`）

| | 值 |
|---|---|
| **改前** | `border: 1px solid var(--rule-control)`（描边）· `background: transparent`（透明）· 无高度 |
| **改后** | `background: var(--surface-sunken)`（沉底面）· `box-shadow: inset 0 0 0 1px var(--rule-hair)`（**内发丝线，不是描边**）· `border: 0` · `height: 40px` · hover 沉底→卡面（底色瞬切） |
| **实测** | `box-shadow: rgb(230,220,196) 0px 0px 0px 1px inset` ✔ · `border: 0px none` ✔ · `bg rgb(242,236,225)` = `--surface-sunken` ✔ · `h = 40` ✔ · `radius 12px` ✔ |

### §4.3 文字按钮 · **B 带箭头**（`btn-text-arrow`）

| | 值 |
|---|---|
| **改前** | `button.ghost` 只有 `hover { background: var(--veil-hover) }`；**无箭头**；`color` 走基类 |
| **改后** | `gap: var(--sp-2)`（8px）· `color: var(--ink-muted)` · hover `背景 --veil-hover` + `color --ink-strong` · `::after` 用 `border-top/right: 1.5px solid currentColor` + `rotate(45deg)` 画 **7×7 右箭头**（**不引 SVG 资产**）· `opacity: .72` ⇒ 箭头**随文字墨色**、不承载语义色 · **`.icon-only` 被排除**（图标按钮自己有一套形状） |
| **实测** | 练习页「不会 ›」可见箭头 ✔ · 箭头色随文字（`currentColor`）✔ · 图标按钮（`ghost sm icon-only`）**无箭头** ✔ · gap 8px ✔ |

### §4.4 图标按钮 · **C 圆形图标按钮**（`iconbtn-round`）

| | 值 |
|---|---|
| **改前** | `32 × 32` 方形 · `border-radius: var(--r-md)`（12px）· 透明底 · **无描边**（旧 W2g 口径） |
| **改后** | `40 × 40` **圆形**（`border-radius: var(--r-round)` → 50%）· `background: var(--surface-sunken)`（沉底面）· `box-shadow: inset 0 0 0 1px var(--rule-hair)` · `::before { inset: -2px }` 补命中区 |
| **实测** | `w = 40` · `h = 40` · `border-radius: 50%` ✔ · `bg rgb(242,236,225)` = `--surface-sunken` ✔ · `shadow rgb(230,220,196) 0 0 0 1px inset` ✔ · **命中区 44×44**（见 §6） |
| **落点** | 走**既有类名** `button.icon-only`（`class="ghost sm icon-only"`，`pages.py` + `workbench.js`）—— **未新起类名** |

### §4.5 输入框 · **A spec 输入框**（`input-spec`）

| | 值 |
|---|---|
| **改前** | `min-height: 32px` · `padding: 6px 10px` · `border-radius: 10px` · 聚焦只有**焦点环** |
| **改后** | `min-height: 44px` · `padding: 0 14px` · `border-radius: var(--r-md)`（12px）· 聚焦 = **蓝边 + 3px 蓝洗底光晕** + 底色提到 `--surface-raised`；**焦点环保留**（不写 `outline: none`） |
| **实测** | `#rating-input`：`min-height 44px` · `padding 0px 14px` · `radius 12px` ✔ · 聚焦 `box-shadow: 0 0 0 3px var(--role-blue-wash)` + `border-color: --role-blue` ✔ |

### §4.6 文本域 · **A spec 文本域**（`textarea-spec`）

| | 值 |
|---|---|
| **改前** | 走输入框那条（`min-height: 32px` · `padding: 6px 10px`）· **无 `resize`** |
| **改后** | `min-height: 96px` · `padding: 12px 14px` · `line-height: 1.6` · `resize: vertical` · 与 §4.5 共用聚焦口径 |
| **实测** | `#paper-answer`：`min-height 96px` · `padding 12px 14px` · `radius 12px` ✔ · `#feedback-note` 同 ✔ |
| **特例** | Agent 贴底输入区 `#ai-input`（`agent-ui.css`）：`min-height 40px` · `padding 6px 10px` · `resize: none` —— **贴底的一行**，不是多行录入面（§4.6 明写的唯一变体）✔ |

### §4.8 复选框 · **B 整行选中**（`check-row`）—— 见 **§5**

### §4.9 单选 · **B 整行卡选中**（`radio-row`）—— 见 **§5**

### §4.10 开关 · **B 迷你开关**（`switch-mini`）

| | 值 |
|---|---|
| **改前** | 轨道 `44 × 26` · 滑块 `20 × 20` · 位移 `translateX(18px)` |
| **改后** | 轨道 **`32 × 18`**（`--r-pill` 胶囊）· 滑块 `14 × 14` 正圆 · 位移 `translateX(14px)`（= 32 − 2×2 − 14）· 关态仍 `--ink-disabled`（**A-84 第 4 条不变**）· `::before { inset: -13px -6px }` 撑到 **44×44** |
| **实测** | 轨道 `31.99 × 18` ✔ · `radius 999px` ✔ · 滑块 `13.99 × 13.99` ✔ · 关态底 `rgb(138,130,117)` = `--ink-disabled` ✔ · 开态底 `rgb(43,98,232)` = `--role-blue` ✔ · `label` `min-height 44px` ✔ · **命中区 44×44，6 个探针点全部命中轨道本体**（见 §6） |

### §4.11 分段控件 · **C 药丸分段**（`seg-pill`）

| | 值 |
|---|---|
| **改前** | 容器 `--r-md`（12px）· 沉底面 · **选中项 = 角色蓝实心**（`--role-blue` + `--ink-on-role`） |
| **改后** | 容器 **`--r-pill`（胶囊槽）** · 沉底面 + 内发丝线 · 项 = **药丸**（`--r-pill`）· **选中项 = 白色药丸**（`--surface-raised` + `--elev-1` + 墨字 + 600）⇒ **不用角色蓝**（A-84 第 2 条）· `::before { inset: -4px 0 }` 把 36px 项补到 44px |
| **实测** | 容器 `132.96 × 43.99` · `radius 999px` · `bg rgb(242,236,225)` = `--surface-sunken` ✔ · 选中项 `bg rgb(255,255,255)` = **白色药丸** ✔ · `radius 999px` ✔ · 未选中项 `rgba(0,0,0,0)` ✔ |

### §4.12 标签 · **C 角色色标签**（`tag-role`）

| | 值 |
|---|---|
| **改前** | **产品里没有**标签 markup（`.chip` 是**图谱区段**的类名，A-78 命名口径不变 ⇒ 不许复用） |
| **改后** | 新增 `.lk-tag` / `.lk-tag__dot` / `.lk-tag--blue|--yellow|--red`：洗底 + 文字色 + **左侧 10px 状态点**（点各取角色色）· `min-height 24px` · `padding 0 10px` · `--r-md` · 12px 字；黄**不承载文字**（取 `--ink-on-warm`）· **不复用 `.chip`** |
| **实测** | **形态已落，markup 零命中**（`grep -rn "lk-tag" pages.py static/*.js` ⇒ 0）⇒ 属「形态先落、markup 待用」，已登记（§9）。<br>探针实测（真实 token 下的 computed）：`.lk-tag` `min-height 24px` · `radius 12px` · `padding 0 10px` · `font-size 12px` · 中性底 `--veil-hover`；`.lk-tag--blue` 底 `rgb(242,240,239)`（`--role-blue-wash`）/ 字 `rgb(43,98,232)`（`--role-blue`）；`.lk-tag--yellow` 底 `rgb(252,240,205)`（`--role-yellow-soft`）/ 字 `rgb(34,31,26)` 暖（`--ink-on-warm`）⇒ **黄不承载文字** ✔；`.lk-tag--red` 底 `rgb(249,233,223)` / 字 `rgb(184,51,31)`（`--role-red-ink`）|

### §4.13 徽标 · **B 胶囊计数**（`badge-pill`）

| | 值 |
|---|---|
| **改前** | `.count-badge`：`background: var(--surface-card)` · `color: var(--ink-muted)` · 11px 字 · `line-height 16px` · **无发丝线** |
| **改后** | `.count-badge, .lk-badge` 合并：`background: var(--surface-sunken)`（**沉底实心**，不用近黑墨块 —— A-23）· `box-shadow: inset 0 0 0 1px var(--rule-hair)`（胶囊轮廓 + 内发丝线，**不用 border**）· `color: var(--ink-strong)` · **11px 字** · `font-weight 700` · `tabular-nums` · `line-height 18px` |
| **实测** | `.count-badge`：`w 18.33` · `h 18` · `bg rgb(242,236,225)` = `--surface-sunken` ✔ · `shadow rgb(230,220,196) 0 0 0 1px inset` ✔ · `font-size 11px` ✔ · 胶囊 `radius 999px` ✔ |
| **说明** | `.lk-badge` **零 markup 命中**（别名，先落形态）；`.count-badge` 是既有类名，**未新起类名** |

### §4.14 状态圆点 · **A spec 全几何集**（`dot-spec`）

| | 值 |
|---|---|
| **改前** | `12 × 12` · 几何只有 `cross` / `dash` / `check` / `filled`（**缺 ring / half**） |
| **改后** | 尺寸收到 **`10 × 10`**（`--r-pill` 胶囊档）· **补 `ring`**（`inset 0 0 0 2px var(--dot-line)`）与 **`half`**（`inset -5px 0 0 0`，10px 的一半 = 5px）· 新增 `--dot-line` 变量承载**线型**几何的颜色（黄走 `--role-yellow-deep`，≥3:1）· 叉/勾的线宽由 7px 收到 6px |
| **实测** | 探针实测（真实 token 下）：`.lk-dot` **10 × 10** ✔ · `radius 999px` ✔；`--ring` = `inset 0 0 0 2px`（暖 `rgb(138,130,117)` = `--ink-disabled` / 夜 `rgb(122,113,98)`）✔；`--half` = `inset -5px 0 0 0`（左半填充）✔；`--filled` = 盘面填充 `--dot-fill`（**颜色由 `--red`/`--yellow`/`--ink` 变体给**，单用 `--filled` 时 `--dot-fill` 仍是透明 —— 与改造前的写法一致）；`--cross` / `--check` 的线宽 7px → **6px**（`::after` 实测 `6px × 2px`）✔ |
| **说明** | `--ring` / `--half` **零 markup 命中** ⇒ 几何集**已补齐**（§4.14 的要求是「补齐现状缺的三档」），但**当前无组件用它们** ⇒ 已登记（§9） |

### §4.15 进度条 · **A 胶囊进度**（`progress-pill`）

| | 值 |
|---|---|
| **改前** | 四条轨道**三种高度**：`.lk-progress` 10px · `.record-rating-track` 12px · `.record-verdict-dist-track` 12px · `.record-run-progress` 10px；底色 `--surface-sunken`；`.record-run-progress` 还带 1px 内发丝线 |
| **改后** | 四条**一次改齐**：`height: 8px` · `border-radius: var(--r-pill)` · 轨道 `background: var(--veil-active)` · 填充角色蓝（语义变体用黄）· **去掉发丝线**（轨道底色换了之后它与轨道同色系 ⇒ 「更少的一层」） |
| **实测** | 全部 9 条可见轨道 `h = 7.99` ≈ 8px ✔ · `radius 999px` ✔ · `bg rgba(61,52,37,0.11)` = `--veil-active` ✔ · `.lk-progress` 填充 `rgb(43,98,232)` = `--role-blue` ✔ · 自评分布填充 `rgb(245,197,24)` = `--role-yellow`（语义变体）✔ |

### §4.17 题号格 · **A spec 形态**（`qcell-spec`）

| | 值 |
|---|---|
| **改前** | `34 × 34` **圆形** · `border: 1px solid var(--ink-muted)` · `background: var(--surface-sheet)` · 六态里 **5 个硬编码色**（`#f2c94c` / `#dce7ff` / `#d9ebdd` / `#f6d8d5` / `#245d32` 契约外绿）· 「当前」= `outline: 3px solid var(--role-blue)` · 「卡住」与「判定错误」**同一行规则** ⇒ 灰度下不可分 |
| **改后** | **`36 × 36` 方 · `--r-md`（12px）** · 未答 = 纸面 + 2px 淡墨空心环（`inset` 阴影，不用 border）· 已答 = **角色蓝实心** · **当前 = 角色黄实心 + `scale(1.06)`** · 判定正确 = 纸面 + **中性墨环 + 角标勾形**（**不用绿、不用蓝** —— A-20-3）· 判定错误 = **红实心 + 角标叉形** · 卡住 = 纸面 + 红环 + 角标叉形 · 角标坐标按 36px 重算 |
| **实测** | `.paper-dot` `w = 36` · `h = 36` ✔ · `radius 12px` ✔ · `state-wrong` `bg rgb(209,57,43)` = `--role-red`（红实心）✔ · `is-current` `bg rgb(245,197,24)` = `--role-yellow`（黄实心）· 尺寸 `38.16`（`scale(1.06)`）✔ · **步距 = 44.0px**（36 + 8 gap；实测左边缘步距 42.91 + 缩放偏移 1.08 = 43.99）✔ |

### §4.18 卡片 · **A spec 留白**（`card-spec`）

| | 值 |
|---|---|
| **改前** | `.card` / `.lk-card` 留白 **18px** |
| **改后** | 留白 **`var(--sp-5)` = 24px**（`.card` 与 `.lk-card` 一起改 ⇒ 不长出第二种卡片）· 12px 圆角 + `--elev-1` 柔影 + **无描边**（不变） |
| **实测** | 探针实测：`.card` 与 `.lk-card` **两者都是 `padding: 24px`**（暖 / 夜同值）· `radius 12px` · 底 `--surface-card` · 柔影 `--elev-1` ✔<br>⚠️ 例外登记：`.time-view` 面板（`workbench.css:2792`）有自己的 `padding: 22px` ⇒ **实测 22px** —— 那是**改造前就有的**更靠后规则（`.time-view` 在 `.card` 之后），**不是本波引入**，且它是「时间视图」这一个面板的专属密度，不属「卡片族」。**未动** |

### §4.19 纸面层级 · **A spec 四层**（`surface-spec`）

| | 值 |
|---|---|
| **改前** | 四层**散落在各组件里**各写一遍 `background` + `box-shadow` |
| **改后** | 显式命名四层：`.lk-surface-0`（底 `--surface-base`）· `.lk-surface-1`（卡 `--surface-card` + `--elev-1`）· `.lk-surface-2`（浮起 `--surface-raised` + `--elev-3`）· `.lk-surface-3`（沉底 `--surface-sunken` + **1px 内发丝线**、**不抬升**、墨字）；夜纸下 `.lk-surface-2` 补一圈发丝线避免与 L1 糊在一起 · **不用描边 / 不用图案 / 不用渐变** |
| **实测** | 探针实测（暖）：`--surface-0` 底 `rgb(253,248,239)` · `--surface-1` 底 `rgb(255,253,247)` + `--elev-1` · `--surface-2` 底 `rgb(255,255,255)` + `--elev-3` · `--surface-3` 底 `rgb(242,236,225)` + **1px 内发丝线** `rgb(230,220,196)` ✔；夜纸下 `--surface-2` 的发丝线垫圈 `rgb(51,45,37)` 在位 ✔ |
| **说明** | **零 markup 命中** ⇒ 属「形态先落、markup 待用」，已登记（§9） |

### §4.20 沉底块 · **C 竖线沉底**（`sunken-rail`）

| | 值 |
|---|---|
| **改前** | 三个落点只有沉底面 + 1px 内发丝线：`.msg.user`（用户消息）· `.detail-block`（强调块）· `.paper-answer-block`（作答区） |
| **改后** | 三处**就地**加 **左侧 4px 黄竖线**（`inset 4px 0 0 0 var(--role-yellow)`）+ 原 1px 内发丝线 —— 黄**只承载面积、不承载文字**（权威表 §3.4）· **不用 border**、不改盒模型 |
| **实测** | `.paper-answer-block`：`box-shadow: rgb(245,197,24) 4px 0px 0px 0px inset, rgb(230,220,196) 0px 0px 0px 1px inset` ✔（黄竖线 + 发丝线，两段都是 inset） |
| **未套** | `.lk-streak`（连对计数器底）**不套**：它左侧那根 4px 条是**档位色条**（灰→黄→黄蓝），本身就是状态通道，再叠一根黄竖线会让两套语义打架 |

### §4.21 空态 · **B 卡面空态**（`empty-card`）

| | 值 |
|---|---|
| **改前** | `background: var(--surface-sunken)` + `box-shadow: inset 0 0 0 1px var(--rule-hair)`（**沉底面**） |
| **改后** | `background: var(--surface-card)` + `box-shadow: var(--elev-1)`（**卡面 + 柔影**）· 旧的沉底形态作废（空态是「一块内容卡」，不是「一块空地」） |
| **实测** | 探针实测：底 = `--surface-card`（暖 `rgb(255,253,247)` / 夜 `rgb(35,32,25)`）· 阴影 = `--elev-1`（**卡面 + 柔影**，不再是沉底面 + 内发丝线）✔ · `radius 12px` · `padding 48px 0` ✔；3.4-5 的「满宽」仍成立（面板 ≤240px、按钮与面板同宽）✔ |

### §4.22 骨架屏 · **B 呼吸式**（`skeleton-breathe`）—— **重点复核，见 §6.2**

| | 值 |
|---|---|
| **改前** | `@keyframes lk-skeleton-sweep`（横扫）+ `.lk-skeleton::after` 覆盖层（`linear-gradient` 微光）⇒ 判据 `3.4-3` **FAIL** |
| **改后** | **横扫与覆盖层整族删除**（`grep -n "lk-skeleton-sweep\|\.lk-skeleton::after" workbench.css` ⇒ **只剩注释里那一句说明**，无任何规则）· 新增 `@keyframes lk-skeleton-breathe`：**只动 `opacity`**（`1 → .45 → 1`，1600ms）· **无渐变** · **不动位置** · `overflow: hidden` 一并去掉（不再需要裁切覆盖层）· 静态样式 = 终态（`opacity: 1`）· 降级档直接是静止灰块 |
| **实测** | **判据 `3.4-3` = PASS**（详见 §6.2） |

### §4.23 吐司 · **A spec 吐司**（`toast-spec`）

| | 值 |
|---|---|
| **改前** | 产品里**没有**非图谱的吐司 markup；图谱那条仿古硬编码 `.toast` 归 `graph-node-visual-language` change（**图谱冻结**）⇒ 本波不碰 |
| **改后** | 新增 `.lk-toast`：右上角 `fixed top/right 16px` · `z-index: var(--z-toast)`（**在模态之下** —— 权威表 §2.7）· 浮起面 `--surface-raised` + `--elev-3` · 12px 圆角 · **13px 字** · `padding 12px 16px` · **浅底深字**（A-23 之后不再是墨块）· 左侧 **10px 状态点**（`.lk-toast__dot`，成功蓝 / 错误红）· 容器 `pointer-events: none`、内部动作 `auto`（**不抢焦点**）· 夜纸下补一圈发丝线 |
| **实测** | 探针实测：宽 240 / `min-width 240` · `padding 12px 16px` · `radius 12px` · `font-size 13px` · 底 `--surface-raised`（暖 `rgb(255,255,255)` / 夜 `rgb(43,38,32)`）+ `--elev-3`（夜纸另补 `rgb(51,45,37)` 1px 垫圈）· `.lk-toast--error` 只改状态点为红、底色不变（浅底深字）✔；图谱那条 `.toast` **零改动** ✔（在冻结区段内） |
| **说明** | **零 markup 命中** ⇒ 属「形态先落、markup 待用」，已登记（§9） |

### §4.26 时间线节点 · **B 分隔线时间线**（`timeline-flat`）

| | 值 |
|---|---|
| **改前** | **两套几何**：`.ai-plan-step`（9px **方块** + 2px 蓝环，`gap 8px`，分隔 `rgb(0 0 0 / 9%)`）· `.agent-milestone`（18px **圆环** + 数字，`gap 7px`，`border-top: 1px solid var(--rule-hair)`）· 两者都**不画竖线**，但**节点形状不同** |
| **改后** | **两套合成一套**：都是 **12px 圆点**（`--r-pill` 胶囊）· `grid-template-columns: 12px minmax(0,1fr)` + `gap: var(--sp-3)`（12px）· `padding: 10px 0` · 分隔走 **`var(--rule-hair)` 发丝线** · 状态色统一成同一支笔（默认 = 蓝环 / running = 蓝实心 / done = 黄实心 / failed = 红实心）· **不画竖线** |
| **实测** | 两个类的几何值逐条一致（12px / 胶囊 / gap 12px / 发丝线）✔ · 类名**仍未收敛**（两族并存）⇒ 已登记（§9） |

### §4.27 折叠段 · **C 手风琴折叠段**（`disc-accordion`）—— **实际覆盖见 §4（专节）+ §10.3（A-126 裁决 3 补齐）**

### §4.28 Tab · **B 分段式标签页**（`tab-seg`）

| | 值 |
|---|---|
| **改前** | `.record-tabs`：`display: flex` + `gap 6px` + **`border-bottom: 1px solid var(--rule-hair)`**（容器底发丝线）· `.record-tab`：`padding 8px 11px` + **`border-bottom: 3px solid transparent`** · `.record-tab.active`：`color --ink-strong` + `font-weight 700` + **`border-color: var(--role-blue)`**（3px 蓝下边框） |
| **改后** | **与 §4.11 分段控件合并成同一个类**（同一组规则：胶囊槽 + 药丸 + **白色药丸**）· 容器 `flex-wrap: wrap` + `margin: 0 0 2px`（**`border-bottom` 作废**）· 项 `padding 0 14px` + `min-height 36px` + `--r-pill` · 选中 = `--surface-raised` + `--elev-1` + 墨字 + 600（**旧的 3px 蓝下边框与蓝字作废**）· `.record-tab` 是 `<a>` ⇒ 选中态用 `.active` 类表达（不依赖 radio） |
| **实测** | 容器 `880 × 43.99` · `radius 999px` · `bg rgb(242,236,225)` = `--surface-sunken` ✔ · `padding 4px` ✔ · 项 `53.99 × 36` · `radius 999px` ✔ · 选中项 `bg rgb(255,255,255)` = **白色药丸** ✔ · `shadow rgba(61,52,37,.06) 0 1px 2px, rgba(61,52,37,.04) 0 4px 12px` = `--elev-1` ✔ · **未选中项 `border-bottom: 0px none`** ✔（旧 3px 蓝边框已作废） |

---

## 4. §4.27 折叠段的**实际覆盖**（主会话复核发现后的处理）

### 4.1 站点清单（**当场 grep 的输出**）

| class | markup 命中 | CSS 规则块 | 处理 |
|---|---|---|---|
| `.ai-plan-output` | 2 | 7 | ✅ **已统一**（卡面 + 48px 头 + 内容同卡） |
| `.practice-set-item-body` | 1 | 7 | ✅ **已统一**（头行是三列网格 ⇒ 保留 grid，只统一高度与排版） |
| `.attempt-history` | 1 | 7 | ✅ **已统一** |
| `.practice-planning` | 2 | 1 | ⚠️ **不是折叠段**（是普通区块容器）—— 不属本条范围 |
| `.goal-editor` | 4 | 3 | ⚠️ **不是折叠段**（是目标编辑表单）—— 不属本条范围 |
| `.practice-set-card-body` | 2 | 1 | ❌ **未统一** —— 它**是**原生 `<details>`（`pages.py:794`）；那 1 条 CSS 只管三角翻转（`.practice-set-card-body[open] > .practice-set-card-head::before { content: "▾" }`），**没有手风琴形态** |
| `.practice-reference` | 1 | 0 → **已统一** | ✅ **A-126 裁决 3 落地**（§10.3）：它**自己就是卡面**（卡面 + 48px 头 + 内容同卡） |
| `.practice-set-continuation-details` | 1 | 0 → **已统一** | ✅ 同上，但**宿主已是卡**（在 `.practice-set-card` 内）⇒ 只取**头行**那一套，**不套第二层卡面** |
| `.practice-set-unavailable-items` | 1 | 0 → **已统一** | ✅ 同上 |
| `.active-practice-continuation-details` | 3 | 0 → **已统一** | ✅ 同上（宿主 `.active-practice-resume.card`） |
| `.practice-set-card-body` | 2 | 1 → **已统一** | ✅ **头行**并入同一套（卡面是**外层**的 `.practice-set-card`） |
| `.problem-topic` | **0** | 5（**死**） | 🔴 **死选择器 ⇒ 整族删除**（§2.3） |

> grep：`grep -rno "<class>" workbench/server/pages.py workbench/server/experience_page.py
> workbench/server/records.py workbench/server/static/*.js | wc -l`（逐个 class 跑）；
> CSS 侧：`grep -c "\.<class>" workbench/server/static/workbench.css`。

### 4.2 处理结论

1. **`.problem-topic` 那一份已删**（死规则）。
   判定依据：`.ai-plan-output` / `.practice-set-item-body` / `.attempt-history`
   **三处实测取值完全一致**（卡面 `--surface-card` + `--r-md` + `--elev-1` +
   `overflow: hidden`；头行 `min-height 48px` + `padding 0 var(--sp-4)` +
   `--font-ui` / `--fs-body` / 500 / `--ink-strong`）⇒ 不需要「改成一致」，
   只需删掉那一份**落在空处**的副本。
   ⚠️ **没有**为了让规则有用而把 `.problem-topic` 加回 markup。
2. **§4.27「四处统一」的口径**：spec 里的「四处」是**旧计数**；实际有
   **10 个站点**，其中 **3 个已统一**（`.ai-plan-output` · `.practice-set-item-body`
   · `.attempt-history`）、**5 个未统一**（4 个零规则 + `.practice-set-card-body`
   只有 1 条三角翻转规则）、**2 个不是折叠段**（`.practice-planning` 是普通区块
   容器 · `.goal-editor` 是目标编辑表单）、**1 个是死类**（`.problem-topic`）。
   ⇒ **A-126 裁决 3 已把这 5 处收进本波并落地**（§10.3）⇒ 现在是
   **8 个已统一 · 2 个不是折叠段 · 1 个死类（已删）**，**零个「未统一」**。
3. **5 个零规则的站点**：C1 交工时判「不在本波授权范围（归 `IMPL-C2` 的
   markup 类名收敛）」⇒ **A-126 裁决 3 已改判**：**它们需要的是 CSS，不是
   markup** ⇒ 收进本波并就地统一（§10.3）⇒ **没有给它们编新类名**。

---

## 5. §4.8 / §4.9 的落点（**改挂既有类名，未引入新类名**）

### 5.1 既有类名是什么

| 流程 | 文件 | markup |
|---|---|---|
| **试卷流** | `workbench/server/static/paper-practice.js:681-701` | `fieldset.className = "problem-options"` → 每个选项一个 `<label class="option-row">`，内含 `input[type=radio|checkbox]`（带 `name` / `value` / `data-paper-choice`）+ `span` |
| **练习流** | `workbench/server/static/practice-flow.js:902-914` | `<fieldset class='problem-options'>` → `<label [class='option-selected' 'option-correct']>`，内含 `input[data-choice-option]` + `span.wb-reading` |

⇒ **行级容器就是 `<label>` 本尊**，两套流程的**行容器都住在
`<fieldset class="problem-options">` 里** ⇒ 一律挂既有类名。

### 5.2 新增规则挂在哪

```css
/* 行：整行可点 + 命中区 ≥44px */
fieldset.problem-options > label {
  display: flex; align-items: center; gap: var(--sp-2);
  min-height: 44px; padding: var(--sp-2) var(--sp-3);
  border-radius: var(--r-md); cursor: pointer;
}
fieldset.problem-options > label:hover { background: var(--veil-hover); }
/* 选中 = 整行蓝洗底（用 :has(input:checked) 取状态，不依赖 JS 加的类） */
fieldset.problem-options > label:has(input:checked) { background: var(--role-blue-wash); }
/* .option-selected（练习流 JS 驱动的选中态）与上面同义：两条指向同一个底色 */
.problem-options label.option-selected { background: var(--role-blue-wash); }
```

> **为什么用 `fieldset.problem-options > label`（特异度 0,1,2）而不是
> `.problem-options label`（0,1,1）**：
> ① 它精确命中两套流程的**选项行直系子元素**；
> ② 它**高于** `.paper-options label`（0,1,1）—— 那条带
> `align-items: baseline`，自绘的 20×20 框挂在 baseline 上会歪；
> ③ 顺序无关（不依赖「谁写在后面」）。
> **代价（已登记）**：`.paper-options label` 的 `padding: 12px` /
> `gap: 12px` / `border-radius: 8px` 被本条接管 ⇒ 试卷流的选项行留白
> 由 `12px` 收成 `8px 12px`、间隙 12px → 8px、圆角 8px → 12px。
> 这是**两套流程行几何统一**的代价，也是 §4.8/§4.9「整行读成卡片」的必要条件。

### 5.3 `appearance: none` 的自绘怎么做

```css
.problem-options input[type="checkbox"],
.problem-options input[type="radio"] {
  appearance: none; -webkit-appearance: none;
  position: relative; flex: none; width: 20px; height: 20px; margin: 0;
  border: 1.5px solid var(--ink-disabled);
  background: var(--surface-card); cursor: pointer;
}
.problem-options input[type="checkbox"] { border-radius: var(--r-xs); }  /* 6px 方 */
.problem-options input[type="radio"]   { border-radius: var(--r-round); }/* 真圆 */
.problem-options input[type="checkbox"]::before,
.problem-options input[type="radio"]::before {          /* 命中区 20→44 */
  content: ""; position: absolute; left: 50%; top: 50%;
  width: 44px; height: 44px; transform: translate(-50%, -50%);
}
/* 选中：蓝实心 */
.problem-options input[type="checkbox"]:checked,
.problem-options input[type="radio"]:checked { background: var(--role-blue); border-color: var(--role-blue); }
/* 勾（复选框）：两条旋转的线画的白勾（不引 SVG 资产） */
.problem-options input[type="checkbox"]:checked::after {
  content: ""; position: absolute; left: 4px; top: 1px; width: 9px; height: 14px;
  border-right: 2px solid var(--ink-on-role); border-bottom: 2px solid var(--ink-on-role);
  transform: rotate(42deg);
}
/* 白点（单选钮）：中心 6px */
.problem-options input[type="radio"]:checked::after {
  content: ""; position: absolute; left: 50%; top: 50%; width: 6px; height: 6px;
  border-radius: var(--r-pill); background: var(--ink-on-role);
  transform: translate(-50%, -50%);
}
```

### 5.4 为什么取消 IMPL-C2 的 markup 改造

**一句话**：**行容器已存在**，新增 `.lk-*` 类名只为给**已经存在的行容器**套样式，
正是 A-115 要消灭的「**同一个组件两套实现**」（这次发生在类名层）；
而且 `.option-row`（试卷流）与 `.option-selected`（练习流）是两个流程各自的既有类，
再叠一层 `.lk-*` 会让「哪个是权威」更难判。
⇒ **C2 的 markup 改造取消**；C2 的其余职责（折叠段类名收敛等）不受影响。

### 5.5 实测（**warm + night 两态**）

| 项 | 暖纸 | 夜纸 | 判定 |
|---|---|---|---|
| `appearance`（computed） | `none` | `none` | ✅ 自绘 |
| 框尺寸 | `20 × 20` | `20 × 20` | ✅ |
| 框圆角（radio） | `50%` | `50%` | ✅ 真圆（与方框区分） |
| 框 `::before` | `44 × 44` | `44 × 44` | ✅ 命中区 |
| **命中区探针**（中心 ±21px 六点 + 中心点） | **7/7 全部命中 `INPUT` 本体** | 同 | ✅ |
| 选中行整行底色 | `rgb(242,240,239)` = `--role-blue-wash` | `rgb(41,41,41)` = `--role-blue-wash` | ✅ **整行**（`getBoundingClientRect().width` = 628 / 849 = 行全宽，非只染框） |
| 未选中行底色 | `rgba(0,0,0,0)` | 同 | ✅ |
| 行高 | `68px` | `68px` | ✅ ≥44 |
| 禁用+选中：标记/底对比 | **3.59:1** | **3.61:1** | ✅ 可辨（§2.2） |
| **键盘可达性** | 原生 `input` 仍在 DOM、`name`/`value`/`data-paper-choice` 不变、Tab 可达 | 同 | ✅ **未变** |

> ⚠️ **只改 CSS**：没有碰任何 `input` 的属性 / 事件 / DOM 结构
> （成绩判定、`data-paper-choice`、A-102 的音效 arm 都挂在选项上）。
> **实测**：`input.type` / `name` / `value` / `data-paper-choice` /
> `checked` / `disabled` 在改动前后**逐字相同**。

---

## 6. 三项重点复核

### 6.1 图谱零差异（**硬底线**）

#### (a) 图谱区段**逐字节不变** ✔

```
$ grep -n "Knowledge graph V2" workbench/server/static/workbench.css
4363:/* Knowledge graph V2 — constrained semantic layout, paper Mondrian skin. */
```

区段 = 标记行起 **388 行**（`graph-isolation.md` §5.1 的「388 行，一行不改」）：

| | 行号 | sha256（整段文本） |
|---|---|---|
| C1 之前（`c6a8b2f5~1`） | 3778–4165 | `57c93f7bc3e60628d7388be2c7380e09feb9268a13b71bae4fa85f68b421d2d8` |
| **现在**（A-126 落地后） | 4461–4848 | `57c93f7bc3e60628d7388be2c7380e09feb9268a13b71bae4fa85f68b421d2d8` |

⇒ **逐字节相同**（`og == ng` ⇒ `True`）。

#### (b) 图谱页**冻结块**（`body:has(#layout[data-page="graph"]) { … }`）**取值一条未改** ✔

| | 行号 | 行数 | diff |
|---|---|---|---|
| C1 之前 | 331–422 | 92 | — |
| **现在** | 331–422 | 92 | **`difflib.unified_diff` ⇒ 0 行** |

⇒ 冻结块**逐字节不变**。
（块外另有 **1 条补钉**：`body:has(#layout[data-page="graph"]) .graph-topbar .search input { min-height: 32px; }`
—— 任务书明写「图谱页冻结块**只许补钉**」；它把图谱 38px 搜索框的
`min-height` 钉回改造前的 32px，否则会被基类的 44px 撑开。**实测图谱搜索框
仍为 `h = 38px` / `min-height 32px` / `padding 0px 13px` / `radius 4px`
（后三项本就该由图谱区段自己压过基类）** ✔）

#### (c) R-2 差异像素 = 0 ✔ ＆ 夜纸下展开章节透镜面板的整页 AE = 0 ✔

**协议**（照抄 IMPL-W2j 的 `tmp/w2j/measure_graph.py` + `ae_scopes.py`，
以便与上一波的数字直接可比）：
viewport 1440×900 · `device_scale_factor=1` · `color_scheme=light` ·
locale `zh-CN` · 时区 `Asia/Shanghai` · chromium `--force-color-profile=srgb
--disable-lcd-text` · `emulate_media(reduced_motion="reduce")` +
`screenshot(animations="disabled")`（图谱有无限环境动画，不冻结则像素差全是噪声）·
主题经 `localStorage wb_settings_walk` 注入 · 章节透镜面板 `hidden = false`。
口径：**R-1** = 整页排除左栏（x<280）与顶栏（y<52）；**R-2** = `.graph-workspace`
裁剪矩形 `(320,272) 660×608`；**整页** = 不排除任何东西。
每种态采 **3 次**，3 组配对。

| 配对 | 整页（差异像素 / 绝对误差） | **R-1 口径**（差异像素 / 绝对误差） | **R-2 画布**（差异像素 / 绝对误差） |
|---|---|---|---|
| **夜纸 vs 暖纸（当前 CSS）** | 0 / 0 · 12 / 407 · 0 / 0 | **0 / 0** ×3 | **0 / 0** ×3 |
| 当前 CSS vs C1 之前（暖纸） | 52,322–52,334 / 8.27M | 52,055 / 8.26M | **0 / 0** ×3 |
| 当前 CSS vs C1 之前（夜纸） | 52,322–52,334 / 8.27M | 52,055 / 8.26M | **0 / 0** ×3 |
| **同主题噪声底**（暖 1 vs 暖 2） | 0 / 0 | 0 / 0 | 0 / 0 |
| **同主题噪声底**（夜 1 vs 夜 2） | 12 / 407 | 0 / 0 | 0 / 0 |

- **R-2 差异像素 = 0** ✔（当前 CSS vs C1 之前，暖/夜各 3 组配对全为 0）
- **夜纸下展开章节透镜面板的整页 AE = 0** ✔
  （口径内：R-1 = 0/0；整页只有 **0 或 12 px / 绝对误差 ≤407**，且**同主题**两次采集
  也出现**同样的 12 px** ⇒ 它是**左栏「知识图谱」导航图标的 SVG 抗锯齿栅格化
  非确定性**，不是主题差异 —— 与 IMPL-W2j 的结论一致）
- **透镜面板本身的取值（夜纸）**：`panelBg rgb(255,255,255)`（= 亮色档的
  `--surface-raised`，被冻结块钉住）· `panelShadow rgba(61,52,37,.1) 0 4px 12px,
  rgba(61,52,37,.12) 0 20px 48px`（= 亮色档 `--elev-3`）· 选项文字
  `rgb(23,23,23)` · 面板矩形 `(215.45, 42) 176×48`
  ⇒ **夜纸与亮色逐字节相同**（CD-176 / IMPL-W2j 的补钉仍有效）。

#### (d) ⚠️ **诚实登记**：C1 确实改了图谱页的**外壳**，但**不在 R-1/R-2 口径里**

「当前 CSS vs C1 之前」在 **R-1 口径**下有 **58,748 px** 差异。逐像素定位：

| 区域 | 差异像素 | 来源 |
|---|---|---|
| **x ≥ 980**（**画布矩形之外**）：其中 **x ≳ 1075** 是 **Agent 右栏**（80 个 `ghost sm icon-only` + 时间线），**x ∈ [980, 1075)** 是中栏右缘 | **52,055**（= 旧 R-1 口径的**全部**差异） | **§4.4 图标按钮 32×32 方 → 40×40 圆**（右栏 80 个）＋ **§4.26 时间线** |
| **x ∈ [240, 280)**（左栏，**旧 R-1 口径外**） | 267 | **§4.13 徽标**（卡面 → 沉底 + 内发丝线） |
| **图谱画布（R-2 矩形 320–980）** | **0** | — ⇒ 差异像素**一个都不在画布里** |

> ✅ **A-126 裁决 1（`decisions.md`）已落账**：**R-1 的范围重新界定为「图谱专属区」**
> （画布 + 图谱自己的工具条 / 图例 / 控件）；**共享外壳（左栏 / 右栏 / 顶栏）不在
> 图谱冻结范围**，随全站组件形态走。
> ⇒ 上表的 **52,055 px 是共享外壳的有意改版（A-115）**，**不算 G-5 失败**；
> **R-2（画布）= 0 仍是硬门禁** ✔（上表实测 0）。
> ⇒ **走查台账按新口径记录**：「R-1（图谱专属区）= 0；共享外壳变化 52,055 px
> 系 A-115 的有意改版」。（台账本身在 `decisions.md` / `IMPLEMENTATION-LOG.md`，
> **不属本波文件所有权** ⇒ 由主会话记账。）

⇒ **图谱本体（画布）零差异** ✔；变的是**共享外壳**（Agent 右栏的按钮与
左栏的徽标）—— 它们是**全站组件**，在**每一个页面**上都一样。
⚠️ **但按 A-48 的 R-1 口径（「除左栏与顶栏外像素级一致」）右栏**在**口径内**
⇒ 这是一个**口径与全站组件形态变更之间的张力**，已登记为**待裁决**（§9 第 1 条）。

### 6.2 骨架屏是否真的改成呼吸（§4.22）

**判据口径**（`decisions.md` A-117 定稿）：**有体积**（`w>0` 且 `h>0`）**且**
**块自身表面**随时间变化 —— ① 三次采样（t0 / +400ms / +800ms）里块的
`background-color` 或 `opacity` **真的变了**，或 ② 块**自身**（不是伪元素）有
一个 keyframes 改了 `opacity` 或 `background-color` 的动画；
**`::after` 上的横扫不算**；**降级档只判「有体积」**。

**（1）横扫必须已删 —— grep 零命中** ✔

```
$ grep -n "lk-skeleton-sweep\|\.lk-skeleton::after\|lk-sheen\|skeleton-sheen" \
      workbench/server/static/workbench.css workbench/server/static/agent-ui.css
workbench.css:195:  --skeleton-sheen: #fdf8ef;          ← token 定义（见下）
workbench.css:299:  --skeleton-sheen: #3c3529;          ← token 定义（见下）
workbench.css:3619:  ⚠️ **不做横扫**（旧的 `lk-skeleton-sweep` + `.lk-skeleton::after` 覆盖层
```

⇒ **没有任何 `lk-skeleton-sweep` 关键帧、没有 `.lk-skeleton::after` 规则**
（剩下的三处命中：两条是 **token 定义**、一条是**注释里对删除动作的说明**）。

> ⚠️ `--skeleton-sheen` token **保留未删**：它已被
> `design-notes/motion-spec.md:236` 标为「~~骨架微光高光~~ **不再使用**
> （A-115 取消了横扫）」⇒ 留着 token、停用引用，是**已登记的契约状态**，
> 不是漏删。删它会牵动 `night-paper-tokens.md` 的 token 清单。

**（2）重跑走查执行器 —— 判据由 FAIL 转 PASS** ✔

```
$ env -u http_proxy -u https_proxy -u all_proxy \
    python tools/walkthrough/run.py --skip-before --only 3.4-3 \
    --port-after 35562 --out tmp/wt-c1-final
```

`tmp/wt-c1-final/evidence/after/probe/3.4-3.json`：

```
verdict: PASS | 骨架屏有体积，且加载期有呼吸动效
  sweep    304x26   anim=lk-skeleton-breathe    after=none   surfaceChanged=True
  sweep    660x128  anim=lk-skeleton-breathe    after=none   surfaceChanged=True
  sweep    607x16   anim=lk-skeleton-breathe    after=none   surfaceChanged=True
  sweep    502x16   anim=lk-skeleton-breathe    after=none   surfaceChanged=True
  sweep    568x16   anim=lk-skeleton-breathe    after=none   surfaceChanged=True
降级档（reduced-motion）: tier=weak  sized=5  breathing=0
```

- **5/5 骨架块**：块**自身**的 `animation-name = lk-skeleton-breathe`、
  变的属性是 **`opacity`**、**`::after` 的 `animation-name = none`**（无横扫）、
  `surfaceChanged = True`（三次采样 opacity 真变了：`1 → 0.5598 → 0.45`）。
- **降级档**：`animation-name = none`（静止灰块）**且 5/5 有体积**
  （304×26 / 660×128 / 607×15 / 502×15 / 568×15）⇒ 只判「有体积」✔。
- **改前对照**（`decisions.md` A-117 第 3 节的实测）：改前是
  `afterAnimation = lk-skeleton-sweep` / `ownAnimations = []` / 三次采样完全不变
  ⇒ 判 **FAIL**。**本波 = PASS** ✔。
- ⚠️ **没有为了让判据变绿去改产品迎合，也没有改探针 / 改判据** ——
  产品改的是 `workbench.css`（`87191d79`），判据 / 探针**一行未动**
  （`tools/walkthrough/probe.py` 不在本波的文件所有权内，也没被碰过）。

### 6.3 命中区 ≥ 44px（**A-115 唯一不让步的两条之一**）

**测法**：视觉尺寸用 `getBoundingClientRect()`；命中区用
`document.elementFromPoint()` 在**视觉盒外扩 2px** 的六点（±21px 四角与四边）
+ 中心点**实测**命中谁 —— 不靠「算了 insets 当真」；
**`.sm` 档**（28px 视觉，不挂伪元素）用**相邻可点目标的中心距**实测（§3.1 方法 2）。

| 组件 | 视觉尺寸 | 命中区补法 | **实测命中** | 判定 |
|---|---|---|---|---|
| **§4.4 图标按钮** `button.icon-only` | `40 × 40` 圆形 | `::before { inset: -2px }` | 7/7 探针点命中按钮本体；**容器间距** `.ai-session-actions` `gap 2px → 4px` ⇒ 中心距 **44px**（原 42px，命中区会重叠 2px） | ✅ **44×44** |
| **§4.1 主按钮** `button.primary` | `h = 40` | `::before { inset: -2px 0 }` | ±21px 命中按钮本体 | ✅ **44 高** |
| **§4.2 次按钮** `button.outline` | `h = 40` | `::before { inset: -2px 0 }` | 同上 | ✅ **44 高** |
| **§4.10 迷你开关** `.lk-switch__track` | `32 × 18` 胶囊 | `::before { inset: -13px -6px }` ⇒ `43.99 × 43.99` | **6/6 探针点全部命中轨道本体**（`SELF`） | ✅ **44×44** |
| **§4.10 开关整行** `.lk-switch` | `min-height: 44px` | 原生 `input` 以 `inset: 0` 盖住整行 | — | ✅ |
| **§4.11 分段项** `.lk-seg__item` | `h = 36` | `::before { inset: -4px 0 }` | 容器高 `43.99`（36 + 4 + 4）⇒ 命中区**落在容器内**、不溢出、不压相邻项 | ✅ |
| **§4.17 题号格** `.paper-dot` | `36 × 36` | **尺寸补偿法**：格 36 + 间隙 8 = **44px 步距** | 实测布局步距 **43.99px** | ✅ |
| **§4.14 状态圆点** `.lk-dot` | `10 × 10` | **不补**（装饰性状态点，不是可点目标 —— §4.14 明写） | — | ✅ 合规 |
| **§4.8 / §4.9 选项框** | `20 × 20` | `::before { 44 × 44 }` 居中 | **7/7 探针点命中 `INPUT` 本体** | ✅ **44×44** |
| **§4.8 / §4.9 选项行** | `h = 68`（实测） | `min-height: 44px` | 整行可点 | ✅ |
| **`.sm` 档** `button.primary.sm` / `button.outline.sm` | **28px**（A-126 裁决 2 后真正生效） | **不挂伪元素外溢**（`inset: -8px` 会抢相邻点击）⇒ 走 **§3.1 方法 2（容器间距 / 中心距 ≥44px）** | 实测最近相邻目标中心距：**158.56 / 158.56 / 53.04** | ✅ |
| **§4.5 输入框 / §4.6 文本域** | `44px` / `96px` | 天然达标 | — | ✅ |
| **§4.11 分段容器** | `43.99`（44） | 天然达标 | — | ✅ |
| **§4.28 Tab 项** | `36`（容器 `43.99`） | 与 §4.11 同一套 | — | ✅ |
| **§4.27 折叠段头** | `48px` | 天然达标 | — | ✅ |

**焦点环**（A-115 另一条不让步的）：全局 `:focus-visible` 单圈
（`--focus-outer` / 2px / 2px 偏移）**全程保留**，本波**没有新增任何
`outline: none`**：

```
$ grep -n "outline: *none\|outline: *0" workbench/server/static/workbench.css \
      workbench/server/static/agent-ui.css
workbench.css:1089:     **不得** `outline: none`。                              ← 注释
workbench.css:1146:/* 焦点环（A-75 · IMPL-W2g 第 2 条）：此前这里写着 `outline: none`，  ← 注释
workbench.css:2538:   outline: none; }` 让它聚焦时**既没有边框也没有焦点环** …      ← 注释
```

⇒ **3 处命中全是注释**（讲「为什么当初删了 `outline: none`」），
**没有任何一条生效的 `outline: none` 规则**；`agent-ui.css` **零命中**。
图谱区段内的 `outline: 0` 属冻结区段，本波**不碰**。

---

## 7. 验证命令结果（**7 条全绿**）

| # | 命令 | 结果 |
|---|---|---|
| 1 | `python -m pytest tests -q` | **1181 passed** in 245.20s ✔ |
| 2 | `python -m compileall -q lessonkit.py workbench pipeline pool tests` | **exit 0**，无输出 ✔ |
| 3 | `openspec validate --specs --strict` | **19 passed, 0 failed** ✔ |
| 4 | `python lessonkit.py guard extract-problems --course dmath --chapter ch06` | **Result: PASS**（所有产物存在、检查文件无阻塞标记）✔ |
| 5 | `node --test tests/workbench/*.test.js` | **tests 264 · pass 264 · fail 0** ✔ |
| 6 | `node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json` | **differences 0**（compared 96 · coordinate diffs 0 · seed diffs 0 · id set diffs 0）→ **RESULT: PASS** ✔ |
| 7 | `python tools/verify_tokens.py` | **低于判定线的配对：0 项** → 全部适用配对达标 ✔ |

**额外**（A-39 与环境）：

- **A-39（服务字节数 == 磁盘字节数）**：走查执行器自己核对
  `{"served": 228671, "onDisk": 228671}` ✔；另手工核过
  `workbench.css` 与 `agent-ui.css` 两条（`identical=True`）✔。
- **代理**：`env -u http_proxy -u https_proxy -u all_proxy` 一律带上 ✔。
- **端口**：走查用 35560 / 35562，实测服务用 **35561**（避开全部禁列端口）✔。
- **池副本 + `LESSONKIT_WB_HOME`**：走查执行器与我的实测服务都用
  `tools/walkthrough/launch.py`（自带 A1/A2/A3 隔离断言）✔。
- **工作区产物验收**（`guard problem-set`）：**未跑** —— 按 AGENTS.md 纪律 6，
  它是「工作区产物验收」，只在对应输出已生成时运行，且干净 checkout 不跟踪
  `output/` ⇒ **不是仓库级 CI 前置条件**。

---

## 8. 截图路径（**暖纸 + 夜纸双主题**）

目录：`openspec/changes/workbench-visual-language-v2/reports/IMPL-C1-shots/`

| 文件 | 主题 | 看什么 |
|---|---|---|
| `practice-warm.png` | 暖纸 | §4.17 题号格（红实心 / 黄实心当前）/ §4.8·§4.9 自绘单选钮 / §4.1 主按钮（无影）/ §4.2 次按钮（沉底 + 内发丝线）/ §4.20 黄竖线 / §4.3 文字按钮箭头 |
| `practice-night.png` | 夜纸 | 同上（夜纸）—— 选中行整行蓝洗底 + 自绘钮可辨 |
| `records-warm.png` | 暖纸 | §4.28 Tab（胶囊槽 + 白色药丸）/ §4.15 胶囊进度 8px / §4.13 徽标 / §4.18 卡片 24px 留白 |
| `records-night.png` | 夜纸 | 同上（夜纸）—— 含 A-123 的「按单题过滤　查看全部记录」分隔 |
| `settings-warm.png` | 暖纸 | §4.10 迷你开关 32×18 / §4.11 药丸分段（白色药丸） |
| `settings-night.png` | 夜纸 | 同上（夜纸） |
| `agent-rail-warm.png` | 暖纸 | §4.4 图标按钮 40×40 圆形（80 个）/ §4.26 时间线 12px 圆点 + 发丝线 |
| `agent-rail-night.png` | 夜纸 | 同上（夜纸） |
| `graph-warm.png` / `graph-night.png` | 双主题 | 图谱页 —— **两张 sha256 完全相同**（`f777939c…`）⇒ 冻结生效 |
| `graph-canvas-warm.png` / `graph-canvas-night.png` | 双主题 | 图谱画布 —— **两张 sha256 完全相同**（`69f993f0…`）⇒ **R-2 逐像素零差异** |

> 同目录下还有上一棒留下的 `before/ after/ after2/ swap/ swap2/` 五组截图
> （本次未改动，保留原样）。

---

## 9. 待裁决项（**拿不准的登记，不自行拍板**）

| # | 项 | 事实 | 处置 |
|---|---|---|---|
| **1** | **§4.4 / §4.26 改了图谱页的 Agent 右栏**（右栏在 A-48 的旧 R-1 口径内） | 「当前 CSS vs C1 之前」在旧 R-1 口径下差 **52,055 px**（右栏 + 中栏右缘）+ 左栏徽标 267；**画布 R-2 = 0** | ✅ **A-126 裁决 1 已裁**：**R-1 的范围 = 图谱专属区**（画布 + 图谱自己的工具条 / 图例 / 控件）；**共享外壳（左栏 / 右栏 / 顶栏）不在图谱冻结范围**，随全站组件形态走 ⇒ 这 **52,055 px 不算 G-5 失败**（R-2 = 0 仍是硬门禁）。**本波按新口径记账**（§6.1(d)），台账由主会话记 |
| **2** | **`button.sm` 的尺寸档被形态规则盖掉** | `button.primary` / `button.outline` 的 `height: 40px` 写在 `button.sm { height: 28px }` **之后** ⇒ `class="primary sm"` / `class="outline sm"` 从 **28px 变成 40px** | ✅ **A-126 裁决 2 已裁并落地**：**这是级联 bug，不是设计选择** ⇒ `.sm` 真正生效（**28px**）· 形态高度改走**零特异度**（`:where(...)`）· 命中区走 **§3.1 方法 2（容器间距 / 中心距 ≥44px）**、**不挂** `inset: -8px` 外溢伪元素（实测它会抢相邻点击）。详见 §10.2 |
| **3** | **§4.27 的 5 个零规则站点** | `.practice-reference` · `.practice-set-card-body` · `.practice-set-continuation-details` · `.practice-set-unavailable-items` · `.active-practice-continuation-details` —— 各自都是原生 `<details>`，但**零 CSS 规则** | ✅ **A-126 裁决 3 已裁并落地**：**归属改为 CSS 波**（`IMPL-C2` 已取消 —— 它们需要的是 CSS，不是 markup）⇒ 本波**就地给既有类名同一套折叠段取值**（§10.3）。**没有给它们编新类名** |
| **4** | **时间线的两个类族仍在** | §4.26 已把 `.ai-plan-step`（workbench.css）与 `.agent-milestone`（agent-ui.css）**画成同一套几何**（12px 圆点 + 发丝线），但**类名未收敛** | 类名收敛归 `IMPL-C2`。本波只做到「视觉统一」 |
| **5** | **6 条「只落形态、markup 待用」** | §4.12 `.lk-tag` · §4.13 `.lk-badge` · §4.14 `.lk-dot--ring` / `--half` · §4.19 `.lk-surface-0..3` · §4.23 `.lk-toast` —— markup 命中均为 **0** | 这几条的**形态**是 A-115 明确要求补的（尤其 §4.14「补 ring/half/filled 三档」是「补齐几何集」），**先落样式**是任务书明写的做法（§4.7 / §4.16 / §4.24 / §4.25 那四条 B 类才是「不许实现」）。**markup 什么时候用、谁来用**登记待裁 |
| **6** | **`.practice-set-card-body` 的头行结构与前三处不同** | `pages.py:794` 输出 `<details class='practice-set-card-body'>`，头是 `.practice-set-card-head`（`content: "▸"` 三角 + 标题 + 三个动作按钮）⇒ **它也是原生 `<details>`**，只是头行结构不同 ⇒ ✅ 已并入裁决 3 的 CSS 波统一处理（§10.3），**只并几何（48px 头 + 纵向对齐）**、不接管它的字号（`<h2>` 标题有自己的 18px 刻度） |

---

## 10. A-126 的三条裁决落地（**C1 收尾追加**）

> `decisions.md` **A-126**（commit `bc488a40`）对 C1 报告 §9 的六条待裁决
> 裁了三条、留登记三条。**三条已在本波落地**，全部只碰
> `workbench/server/static/workbench.css`。

### 11.1 裁决 1（R-1 口径 = 图谱专属区）

见 **§6.1(d)**：新口径下 **R-1（图谱专属区）= 0**、**R-2（画布）= 0**；
共享外壳的 **52,055 px** 是 A-115 的有意改版，**不算 G-5 失败**。
台账由主会话记（本波只把数字与口径写进本报告）。

### 11.2 裁决 2（`.sm` 级联 bug → `.sm` 真正 28px）

**改前**：`button.primary` / `button.outline` 的 `height: 40px` 写在
`button.sm { height: 28px }` **之后** ⇒ 同特异度靠后者胜 ⇒
`class="primary sm"` / `class="outline sm"` 的 28px **被盖成 40px**。

**改后**（`workbench.css`）：

```css
/* 形态高度改成**零特异度** ⇒ `button.sm`（0,1,1）任何顺序都赢 */
:where(button.primary, button.outline) { height: 40px; }

/* `.sm` 档不挂命中区伪元素：命中区走 §3.1「方法 2（容器间距）」 */
button.primary.sm::before,
button.outline.sm::before { content: none; }
```

> 选 `:where()` 而不是「把 `.sm` 排到最后」：`:where()` **与顺序无关**
> ⇒ 以后谁在后面加 `button.primary` 都不会再把 `.sm` 盖掉
> （这才是「修级联」而不是「挪一下顺序」）。

**实测**（改前 → 改后）：

| 调用点 | 改前 | 改后 | 最近相邻目标**中心距** | 判定 |
|---|---|---|---|---|
| `button.primary.sm` 「保存目标」 | 67.99 × **40** | 67.99 × **28** | 158.56 | ✅ |
| `button.outline.sm` 「让 Agent 代填」 | 94.51 × **40** | 94.52 × **28** | 158.56 | ✅ |
| `button.outline.sm` 「新建」 | 43.99 × **40** | 44 × **28** | 53.04 | ✅ |
| `button.ghost.sm.icon-only` ✎ / × | 40 × 40 | 40 × 40 | **44**（原 42，见下） | ✅ |

**「给不出 44px 中心距的调用点就不要用 `.sm`」**：
本次实测**每一个可见的 `.sm` 调用点的中心距都 ≥ 44px**
（158.56 / 158.56 / 53.04 / 44）⇒ **没有需要退掉 `.sm` 的调用点**，
**无需改 markup**。
⚠️ 未出现的调用点（试卷流里的 `选择试卷` / `保存` / `导出` / `改名` /
`删除` / `重试` / `编辑自评`）在当前工作区状态下**不可见**
⇒ 它们**尚未实测**，登记在 §9 之外，**由下一波页面波次补测**。

**顺带修的一处命中区缺陷**（实测发现的）：
Agent 右栏的两个 40×40 圆形图标按钮（✎ / ×）在
`.ai-session-actions { gap: 2px }` 里 ⇒ 中心距只有 **42px**（**不足 44px**，
两个 44×44 的命中区会重叠 2px）⇒ `gap` 改 **4px** ⇒ 中心距 **44px** ✔
（纯间距，**不是** `inset: -8px` 那种外溢伪元素）。

### 11.3 裁决 3（§4.27 的 5 处零规则折叠段 → CSS 波）

**归类原则**：**宿主已经是卡的** ⇒ **不再套第二层卡面**（那会变成「卡中卡」
—— A-125 说的「积木感 = 同一卡片重复 8–31 次」正是这么来的）⇒ 只取**头行**
那一套；**独立页块** ⇒ 它自己就是卡面。

| class | 宿主 | 落法 |
|---|---|---|
| `.practice-reference` | 与 `.practice-solution` 同级（**独立页块**） | **自己就是卡面**：`--surface-card` + `--elev-1` + `--r-md` + `overflow: hidden` + 48px 头 + `padding 0 16px` / 内容 `0 16px 16px` |
| `.practice-set-continuation-details` | `.practice-set-card`（`article.card`）**之内** | **只取头行**（48px 头 + `padding 0 8px` + 内容 `0 8px 8px`），**不套第二层卡面** |
| `.practice-set-unavailable-items` | 同上 | 同上 |
| `.active-practice-continuation-details` | `.active-practice-resume.card` **之内** | 同上 |
| `.practice-set-card-body` | `.practice-set-card` **之外**（它**就是**那张卡的可展开体） | 卡面 = **外层**的 `.practice-set-card` ⇒ 这里**不加卡面**，只把**头行**并入同一套（`min-height: 48px` + 纵向居中）；⚠️ **不接管它的字号**（`<h2>` 标题有自己的 18px 刻度） |

**实测**（暖 / 夜两态，真实 token 下的 computed）：

| class | 卡面底 | 卡面阴影 | 圆角 | 头高 | 头内距 | 头排版 | 内容内距 |
|---|---|---|---|---|---|---|---|
| `.practice-reference` | `rgb(255,253,247)` / `rgb(35,32,25)` | `--elev-1` | 12px | **48** | `0 16px` | 14px / 500 | `0 16px 16px` |
| `.practice-set-continuation-details` | 透明（**不套第二层卡面**） | none | — | **48** | `0 8px` | 14px / 500 | `0 8px 8px` |
| `.practice-set-unavailable-items` | 透明 | none | — | **48** | `0 8px` | 14px / 500 | `0 8px 8px` |
| `.active-practice-continuation-details` | 透明 | none | — | **48** | `0 8px` | 14px / 500 | `0 8px 8px` |
| `.practice-set-item-body`（**已统一的那一处**，对照组） | `rgb(255,253,247)` | `--elev-1` | 12px | **48** | `0 16px` | 14px / 500 | — |

⇒ §4.27 现在是 **8 处同一套**（3 处原统一 + 5 处本波补齐），
**零个「未统一」**，**没有新类名**。

---

## 11. 本波**没做 / 打折**的地方（诚实说明）

1. **B 类四条（§4.7 自绘下拉 / §4.16 分段进度条 / §4.24 对话框 / §4.25 工具调用卡）**
   —— **未实现**，符合裁定（产品里没有 ⇒ 必须先改 OpenSpec ⇒ 归
   `workbench-component-forms` change）。
2. **`--skeleton-sheen` token 未删** —— 它在 `motion-spec.md:236` 已登记为
   「不再使用」；删它会牵动 `night-paper-tokens.md` 的 token 清单（不在本波
   文件所有权内）。
3. **`.lk-check__row` / `.lk-radio-row` 两族曾在 commit 7 引入、commit 8 删除**
   —— 净效果是「这一波从没有过这两个类名」；但 commit 7 的历史仍在 git 里
   （`git log` 可查）。
4. **`guard problem-set` 未跑** —— 见 §7 的说明（工作区产物验收，非仓库级 CI）。
5. **夜纸下的**「夜纸巡检」全套（`night-sweep-report.md` 的 6 页逐页清单）
   **未重跑** —— 本波只针对 §4.22 要求的「图谱页 + 章节透镜展开态」做了
   夜/暖 AE 实测（§6.1），其余页面未逐页复扫。
6. **A-126 裁决 1 要求的「走查台账按新口径记录」** —— 台账在
   `decisions.md` / `IMPLEMENTATION-LOG.md`，**不属本波文件所有权**
   ⇒ 本波只把新口径与实测数字写进**本报告**（§6.1(d)），**由主会话记账**。
7. **`docs/**` / `openspec/`（报告目录外）/ `tasks.md` / `decisions.md` /
   `component-spec.md` / `motion-spec.md` / `acceptance.md` / `copy-table*.md`
   一律未动** —— 按任务书的文件所有权约束；主会话需要把「IMPL-C2 的 markup
   改造取消」「§4.8/§4.9 改挂既有类名」两条回写到共享台账。
