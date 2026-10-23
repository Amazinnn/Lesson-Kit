# IMPL-W2j 交工报告 —— CSS 收口第三波（夜纸巡检 6 处 + 负荷柱错峰 + 状态点几何）

> 执行体：CSS 收口执行体（第 3.2 波）· 任务书：`briefs/IMPL-W2j.md`
> 交付日期：2026-10-22 / 2026-10-23（夜）· 分支：`feat/workbench-visual-language-v2`
>
> **文件所有权**：`workbench/server/static/workbench.css` · `workbench/server/static/agent-ui.css`
> —— **只动了这两个文件**（`git diff 7828e053..HEAD --name-only` 里除这两个 CSS 之外的
> openspec 文档改动**全部来自并发 agent**，不是我落的）。

---

## 0. 已落盘路径 + commit 清单（9 个，一个主题一个）

| # | hash | 主题 | 落盘内容 |
|---|---|---|---|
| 1 | `f06c2032` | P0 图谱冻结块补钉 | `body:has(#layout[data-page="graph"])` 补钉 `--surface-raised` / `--elev-2` / `--elev-3` / `--ink-body` / `--ink-on-role` / `--ink-on-warm`（24 行新增，既有 20 来条新名 pin 一条未动） |
| 2 | `36b27845` | CD-175 删死规则 | 删 `.status-dot` / `.ok` / `.warn` / `.err` 四条规则 + `--dsw-state-success: #22c55e` 定义；文件头注释同步 |
| 3 | `28dfa60f` | CD-174 负荷柱错峰 | `.bar-fill` 加 `lk-bar-grow`（只动 `transform`，`scaleY 0→1`，底边为锚，320ms / `out`）+ 静态样式 = 终态 |
| 4 | `6bcb32bf` | A-96 热力日历 | `.level-0..4` 的混色底由 `white` 改 `var(--surface-card)`（主题表面 token） |
| 5 | `ac15095e` | 三处颜色取值 | ① `.calendar-cell.today .calendar-day` 文字 → `--ink-on-warm` ② `.lk-dot--ink --dot-fill` → `--ink-faint` ③ `.lk-dot--yellow --dot-fill` → `--role-yellow-deep` ④ `.lk-combo-banner__count` → `--role-yellow-deep` |
| 6 | `cd12f12c` | INC-05 题号格几何 | 六态补几何（叉 / 横杠 / 勾 / 实心点 / 实心盘 / 空心环），角标挪到盘的右上角 |
| 7 | `df86e9d0` | agent-ui 硬编码 | `.agent-approval-card` 底色 `#fff9df` → `var(--role-yellow-soft)`；同时给图谱冻结块补钉 `--role-yellow-soft` |
| 8 | `8deca26f` | A-103 会话列表 | `#ai-session-list` 加 `overflow-y:auto` + `flex:1` + `align-content:start`；`#ai-session-list-view` 定高 |
| 9 | `890339e8` | A-97 三处红色误用 | `.ai-plan-summary` 红 → `--ink-muted`；`.flash-card-answer` 红边 → 墨环；`.bar-heavy-flag` 红点 → `--role-blue` |

**并发 agent 在同一分支上的 commit（不是我落的，未被我扫进任何 commit）**：`73ddd4d8`
（弱动效档闸门补顶栏，同样改了 `workbench.css`）、`961d7d84` / `77393544` / `2a019439` /
`88d261ae`（A-115 文档）。

---

## 1. 逐条「改前 → 改后 + 实测值」

### 一、P0 —— 图谱页章节透镜面板在夜纸下变了（**本波主目标**）

**根因**：图谱冻结块（`body:has(#layout[data-page="graph"])`）钉回了 20 来条 token，
**漏钉** `--surface-raised` / `--elev-2` / `--elev-3` / `--ink-body` ⇒ 夜纸下顶栏浮层随主题翻成深色。

**改前 → 改后**（实测取自真实浏览器 `getComputedStyle`）：

| 项 | 改前（夜纸） | 改后（夜纸） | 改后（亮色） |
|---|---|---|---|
| 面板底色 | `rgb(43,38,32)`（`--surface-raised` 夜 `#2b2620`） | **`rgb(255,255,255)`** | `rgb(255,255,255)` |
| 面板阴影 | `rgba(0,0,0,.52) 0 20px 48px, rgba(255,236,200,.06) 0 0 32px, inset…` | **`rgba(61,52,37,.1) 0 4px 12px, rgba(61,52,37,.12) 0 20px 48px`** | 同左（**逐字节相同**） |
| `--ink-body`（面板选项文字） | `#e7dfd0`（浅墨） | **`#3b3630`** | `#3b3630` |
| 面板矩形 | `(215.45, 42) 176×48` | 同 | 同 |

> ⚠️ **`--ink-body` 必须与 `--surface-raised` 一起钉**：只钉底色不钉文字 ⇒ 夜纸下
> 选项文字是浅墨 `#e7dfd0` 落在白底上 ⇒ 文字几乎不可见（比原问题更糟）。这一点已在
> CSS 注释里写死。
>
> ⚠️ **钉回值取「亮色主题当前取值」而不是旧名值**：面板是 15.4（`064111b1`）**新增**的组件，
> 改造前**根本没有**这块浮层 ⇒「改造前的值」对它不存在；参照系是**今天亮色下的样子**。
> 后果：**亮色主题零变化**、夜纸下与亮色逐字节相同。
> （`design-notes/graph-isolation.md` §7.2 那张历史表曾把 `--surface-raised` 记成 `#fffefa`
>（旧 `--dsw-bg-layer-1`）—— 本波**没有**采用：那会让**亮色**主题下的面板底色从
> `#ffffff` 变成 `#fffefa`（多 1–2/255 的像素变化），与「亮色零变化」相悖。）

**整页 AE = 0 的证据**（亮 / 夜各 3 次采集，9 组配对；脚本 `tmp/w2j/measure_graph.py` +
`tmp/w2j/ae_scopes.py`，产物 `tmp/w2j/graph-lens-ae.json` / `graph-ae-scopes.json`）：

| 口径 | 改前（模拟补钉前的夜纸值） | 改后（亮 × 夜） |
|---|---|---|
| **R-1（整页，排除左栏 x<280 与顶栏 y<52，A-48 口径）** | **36,554 – 36,566 px**（绝对误差和 2,960,698） | **0 px / 绝对误差 0**（9/9 组配对全为 0） |
| **R-2（`.graph-workspace` 画布矩形 `320,272 660×608`）** | — | **0 px / 绝对误差 0**（9/9 组） |
| 整页（不排除左栏） | 36,554 – 36,566 px | 0 或 **12 px**（见下） |

> ⚠️ **诚实说明那 12 px**：它落在**左栏「知识图谱」导航图标的 SVG 抗锯齿**上
> （bbox 恒为 `(21,307)-(38,311)`），**不是主题差异** —— 实测**同主题**两次采集
> （night1 vs night2）也出现**同样的 12 px**，即它是栅格化非确定性；
> 9 组亮/夜配对里有 3 组是整页 0 px，其余 6 组是这 12 px。
> 按 A-48 的口径（左栏与顶栏不在像素比对范围内），**R-1 / R-2 全为 0**。
>
> 「改前」不是口头断言：脚本用**行内样式**把补钉前的夜纸值
> （`--surface-raised:#2b2620` / `--elev-3` 夜档 / `--ink-body:#e7dfd0`）写回 `<body>`
> —— 行内样式压过冻结块规则 ⇒ **精确复原了改造前的产品状态**，再采一次图。

**证据图**：`IMPL-W2j-shots/graph-lens-expanded-night.png`（夜纸下展开透镜面板）。

---

### 二、CD-175 —— 删掉死规则，全站旧名归零

**改前**：`workbench.css` 有 `.status-dot` / `.status-dot.ok` / `.status-dot.warn` /
`.status-dot.err` 四条规则 + `--dsw-state-success: #22c55e`（全站唯一的旧名残留）。
**改后**：四条规则与该定义**全部删除**；文件头注释改为「全站旧名归零」。

**实测**：

```
$ grep -rn "status-dot" --include=*.py --include=*.js --include=*.html --include=*.css .
（产品代码 0 命中；仅 openspec/docs 文档提及）
$ grep -c "var(--dsw-\|var(--lk-" workbench/server/static/workbench.css
0
$ grep -n "var(--dsw-\|var(--lk-" workbench/server/static/agent-ui.css
（0 命中）
```

⇒ **全站 `var(--dsw-*)` / `var(--lk-*)` 引用归零**（CSS 注释里保留的「旧 X 值」是
钉回值的**出处注记**，不是引用点）。

---

### 三、CD-174 —— 负荷柱逐柱 24ms 错峰（补实现）

**改前**：服务端确实逐柱写了行内 `animation-delay:{index * 24}ms`
（`workbench/server/records.py:470`），但 CSS 的 `.bar-fill` **没有任何 `animation` 属性**
⇒ 那条延迟挂在一个**不存在的动画**上 ⇒ **逐柱错峰整条从未生效**。
**改后**：`.bar-fill` 加 `lk-bar-grow`（`scaleY 0→1`，`transform-origin: bottom center`，
320ms / `--ease-out`，`both`），静态样式 `transform: scaleY(1)` = 终态。
**高度编码（行内 `height:Npx`）一行未动。**

**录帧证据**（把每条动画 `pause()` 后逐帧设 `currentTime`，量每根柱的**渲染高度**；
脚本 `tmp/w2j/bar_frames.py`，产物 `tmp/w2j/bar-frames.json`）：

```
t(ms) | 13 根柱的渲染高度（px）
    0 | 0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0
   36 | 11.0 0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0
   60 | 32.0 2.7  0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0
   96 | 58.3 10.2 10.9 0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0
  144 | 81.2 17.5 29.1 51.9 16.2 0.0  0.0  0.0  0.0  0.0  0.0  0.0  0.0
  216 | 98.3 23.1 44.3 101.1 53.1 14.3 20.8 21.8 0.0  0.0  0.0  0.0  0.0
  312 | 105.6 25.7 51.7 126.2 73.3 23.1 44.3 81.2 17.5 43.4 20.8 5.3 0.0
  640 | 106.0 26.0 53.0 132.0 79.0 26.0 53.0 106.0 26.0 79.0 53.0 26.0 53.0
delays(ms) = 24,48,72,96,120,144,168,192,216,240,264,288,312   动画名 = lk-bar-grow（13 条）
```

* **逐柱错峰**：每根柱的「首个非零帧」= 它的 delay 之后的第一个采样点
  （第 1 柱 delay 24 → 首个非零 36；第 2 柱 48 → 60；第 3 柱 72 → 96；…；第 13 柱 312 → 336）
  ⇒ **第 N 柱比第 N-1 柱晚 24ms 起** ✅
* **终态一致**：t=640 时各柱渲染高度 = `offsetHeight`（132/106/79/53/26…）**逐项相等** ✅
* **降级档**（`prefers-reduced-motion: reduce`）：**运行中的动画 0 条**，
  `animation-name: none`，`transform: matrix(1,0,0,1,0,0)`（= `scaleY(1)`），
  渲染高度 132 = 布局高度 ⇒ **直接满格** ✅（静态样式 = 终态成立）

**证据图**：`IMPL-W2j-shots/bars-t0.png` / `bars-t96.png` / `bars-t200.png` / `bars-t640.png`
（t=96 那张只有前三根柱在长，峰值柱还没起 ⇒ 错峰肉眼可见）。

> ⚠️ **口径出入（如实登记）**：`design-notes/motion-spec.md` §2.1 第 19 条把
> 「负荷柱 / 日历扩散 / 庆祝进度」写在一起并给了 `scaleX 0→1` + `transform-origin: left`。
> 负荷柱的编码轴是**高度** ⇒ 本波按**任务书**与 N2 报告的写法取 `scaleY` + `bottom`。
> 该条 motion-spec 的措辞是否要拆分，**登记为待裁决**（motion-spec 不在本波文件所有权内，没动）。

---

### 四、N1 的三处 P1

#### 4.1 热力日历五档（A-96 —— spec 已由主会话改好，本波只实现）

**改前**：`.level-0..4` 用 `color-mix(in srgb, var(--role-blue) N%, white)`，
**混色底写死 `white`** ⇒ 夜纸下五档仍是**亮块**（83 个元素三通道均 ≥ 200），
**「0 次」档（level-0）成了整块面板里最亮的一项** ⇒ 热力编码在夜纸下**倒转**。
**改后**：混色底改**主题表面 token** `var(--surface-card)`（日历所在的 `.card` 面）。

**实测（`getComputedStyle` 取值 + `tools/verify_tokens.py` 的 `ratio()` 实算）**：

| 档 | 改前（夜纸） | 改后（夜纸） | 改后（亮色） | 改后对卡面对比（夜 / 亮） |
|---|---|---|---|---|
| level-0（0 次） | `#f2f5fc`（**14.89:1** 对卡面，最显眼 ❌） | **`#2a2a2b`** | `#eceff6` | **1.13:1 / 1.13:1**（最弱 ✅） |
| level-1 | `#e5ebf9` | `#31343c` | `#d9e1f4` | 1.31:1 / 1.29:1 |
| level-2 | `#cfd9f3` | `#3e465c` | `#b7c8f2` | 1.73:1 / 1.64:1 |
| level-3 | `#b1c2ec` | `#4e5e85` | `#8aa8ef` | 2.53:1 / 2.31:1 |
| level-4（≥8） | `#91a9e5` | `#6178b3` | `#5a84eb` | 3.75:1 / 3.48:1 |

⇒ **五档取值随主题翻转**（不再是写死 `white`）✅；
**「0 次」档不再是最显眼项**（夜纸下 1.13:1，是五档里最弱的）✅；
「越多越深」在两主题下都成立 ✅。

> 顺带核过：夜纸 `--heat-4` = `#6178b3` **正好**等于「夜蓝 78% 混夜纸卡面」的结果
> ⇒ 新公式与权威表 §3.10「同一色阶逻辑，只换混色底」口径一致。

**证据图**：`IMPL-W2j-shots/records-calendar-night.png` / `records-legend-night.png`
（图例五档：0 最暗、≥8 最亮）。

#### 4.2 练习页「今天」圆点

**改前**：`color: var(--ink-strong)` 落在 `--role-yellow` 底上 ⇒ 夜纸 **1.51:1**（数字几乎不可见）。
**改后**：`color: var(--ink-on-warm)`。

| 主题 | 改前文字 / 底 | 改后文字 / 底 | 对比 |
|---|---|---|---|
| 亮色 | `#221f1a` / `#f5c518` | `#221f1a` / `#f5c518` | 10.07:1 → **10.07:1（零变化）** |
| 夜纸 | `#f4ede0` / `#e0c151` | **`#14120f`** / `#e0c151` | 1.51:1 → **10.61:1** ✅ |

**实测**（`/w/walk/practice` 展开「目标与时间安排」后读 computed）：
`day: color rgb(34,31,26) / bg rgb(245,197,24)`；`night: color rgb(20,18,15) / bg rgb(224,193,81)`。
**证据图**：`IMPL-W2j-shots/practice-calendar-night.png`（黄底上的「23」清楚可读）。

#### 4.3 `lk-dot--ink`

**改前**：`--dot-fill: var(--ink-strong)` ⇒ 夜纸下是一枚 `#f4ede0` 的**亮白点**（卡面上 13.96:1），
反而成了红（5.00:1）/黄（9.86:1）/墨三点里**最亮**的 ⇒ 语义与视觉相反。
**改后**：`--dot-fill: var(--ink-faint)`。

| 主题 | 改前 | 改后 | 对卡面对比 |
|---|---|---|---|
| 亮色 | `#221f1a` | `#8d8578` | 16.14:1 → **3.59:1**（仍 ≥ 3:1，且弱于红/黄两点） |
| 夜纸 | `#f4ede0` | **`#978d7c`** | 13.96:1 → **4.97:1** |

**实测**（`/w/walk/kps`）：`night: ink fill rgb(151,141,124) / red rgb(212,115,107) / yellow rgb(240,217,138)`。
⚠️ **按建议落地、语义待裁**（见 §5 人工裁决项）。

---

### 五、N1 的两处亮色主题既有缺陷

| 元素 | 改前（亮色） | 改后（亮色） | 改后（夜纸） |
|---|---|---|---|
| `.lk-combo-banner__count` | `var(--role-yellow)` = `#f5c518`，**1.54:1** ❌ | **`var(--role-yellow-deep)`** = `#8a6a00`，**4.98:1** ✅ | `#f0d98a`，**11.61:1** ✅ |
| `.lk-dot--yellow --dot-fill` | `var(--role-yellow)` = `#f5c518`，**1.60:1** ❌ | **`var(--role-yellow-deep)`** = `#8a6a00`，**4.98:1** ✅ | `#f0d98a`，**11.61:1** ✅ |

`.lk-dot--yellow` 的挖空符号仍用 `--ink-on-warm`（亮色 **3.24:1** / 夜纸 **13.35:1**，都 ≥ 3:1）。
依据：权威表 §3.4「黄色只承载面积，承载文字一律 `--role-yellow-deep`」+ §4.4-10「黄色状态圆点改用标记档」。

---

### 六、INC-05 —— Paper 状态点补几何（灰度下可分）

**改前**：`paper-practice.js` 出 6 态，CSS 里**只有 `correct` 有几何**；
`wrong` / `stuck` **同一行规则**（红洗底 + 红字）⇒ **灰度下完全不可分**；
`filled`（黄实心）/ `unanswered`（纸面 + 细环）**只差颜色**。

**改后**（复用 `.lk-dot--cross` / `--dash` / `--check` 的**同一支笔**：2px 线宽、1px 圆角、纯 CSS 伪元素）：

| 状态 | 改前 | 改后（颜色 + 几何） |
|---|---|---|
| `unanswered` | 纸面 + 1px 细环（无几何） | 纸面 + 细环 = **空心环** |
| `filled` | 黄底（无几何） | 黄底 = **实心盘** |
| `stuck` | 红洗底 + 红字（与 wrong 同款） | 红洗底 + **右上角横杠（dash）** |
| `correct` | 卡面 + 2px 墨环 + **中下位置的勾（压着题号）** | 卡面 + 2px 墨环 + **右上角勾（挪开了）** |
| `wrong` | 红洗底 + 红字 | 红洗底 + **右上角叉（cross）** |
| `locked` | 蓝洗底 + 蓝字（与 unanswered 只差颜色） | 蓝洗底 + **右上角实心小点**（`.lk-dot--filled` 的缩小版） |

**实测**（真实试卷页 `?paper=ps-001`，驱动出 wrong / stuck 两态后读 computed）：

```
wrong : ::before / ::after = 7px × 2px 两条，left 24px top 6.5px，rotate ±45°（叉）
        颜色 rgb(184,51,31)（亮）/ rgb(224,136,120)（夜）= --role-red-ink
stuck : ::before = 8px × 2px 一条，left 20px top 6.5px（横杠），颜色同上
unanswered: ::before / ::after = none（空心）
```

**证据图**：`IMPL-W2j-shots/paper-dots-real-day.png` / `paper-dots-real-night.png`
（真实产品题号格）、`paper-dots-6states-after.png`（六态并排：1 空心 / 2 实心 / 3 横杠 / 4 勾 / 5 叉 / 6 点）。

> ⚠️ **核验方式（如实说明）**：`unanswered` / `wrong` / `stuck` 三态是**驱动真实产品**
> （答题 → 判错；点「不会」→ 卡住）得到的；`correct` / `filled` / `locked` 三态在
> 隔离工作区里**拿不到**（走查工作区没有可开始的第二份卷子），因此用**产品自己的类名**
> （`paper-practice.js:611` 产出的 `paper-dot state-<status>`）在**同一个真实页面**里
> 注入六个元素后截图与读 computed —— 走的是同一张产品样式表，class 契约一字未改。
> **markup 侧没有加任何类**；如果产品后续要更细的角标形态，需要 markup 侧加类的话，
> 本波**不需要**（现状已满足「形状 + 颜色」双通道）。
>
> ⚠️ 角标位置：为了让角标不压住题号，勾从原来的**中下**（x 20…33 / y 17…27，压着数字）
> 挪到盘的**右上角**（墨迹 x 20…28 / y 3…9；实测 1 位数字字身 x 13…21、2 位 x 9…25，
> y 10…24 ⇒ 基本不重叠）。这是**本波对既有 `correct` 形态的一处可见改动**。

---

### 七、`agent-ui.css` 一处硬编码

**改前**：`.agent-approval-card { background: #fff9df; }` ⇒ 夜纸下是一块约 **15:1** 的浅黄亮块。
**改后**：`background: var(--role-yellow-soft)`（浅 `#fcf0cd` / 夜 `#3d3721`）⇒ 两主题都随主题翻转。

**全文件再扫一遍**（`grep -nE "#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\("`）：

```
agent-ui.css 里只剩两处字面色：
  :263  box-shadow: -8px 0 28px rgb(0 0 0 / 6%);   ← 方向性阴影（非浅色底，见 §6 待裁决）
  :346  background: #fff9df;                        ← 本波已改
其余全部是 var(--role-*) / var(--ink-*) / var(--surface-*) / var(--rule-*) 等 token。
```

⚠️ `--role-yellow-soft` 是**随主题翻**的 token ⇒ 图谱页冻结块**一并补钉**浅色档
（否则夜纸下图谱页右栏一旦出现审批卡，就是一块深色卡压在亮色图谱上）。

---

### 八之三、A-103 —— 会话列表补滚动容器

**改前**：`#ai-column { overflow: hidden }` + `#ai-session-list` **无 `overflow-y`**
⇒ 整条链上**没有任何滚动容器** ⇒ 120 条会话只有前 ~20 条够得着 ⇒ **静默裁切**。
**改后**：`#ai-session-list` 加 `overflow-y:auto` + `flex:1` + `min-height:0` + `align-content:start`；
`#ai-session-list-view` 定高（`flex:1`；`min-height:0`；flex 列）。
`#ai-column` 的 `overflow: hidden` **保留**（那是让装饰层不吃点击用的，不是滚动容器）。

**实测（120 条会话）**：

```
items: 120          overflow-y: auto      display: grid
scrollHeight: 7438  clientHeight: 748    scrollable: true
#ai-session-list-view: display flex / flex 1 1 0% / min-height 0px / 高 788px
#ai-column overflow: hidden（保留）
--- 滚到底之后 ---
scrollTop: 6690 = maxScrollTop(6690)
末条 rect (1037,808,387,60) 完全落在列表 rect (1037,120,387,748) 之内 → lastInsideList: true
elementFromPoint(末条中心) → "ai-session-entry"，且命中末条（elementFromPointIsLast: true）
```

⇒ **最后一条能滚到可视区** ✅（`IMPL-W2j-shots/ai-column-bottom.png`）。

---

### 八之二、A-97 —— 另外三处「红色用在非失败语义」

| 位置 | 改前 | 改后 | 依据 |
|---|---|---|---|
| `.ai-plan-summary`（Agent 计划摘要行，装的是「查看输出」这类中性文案） | **无条件** `var(--role-red-ink)` | **`var(--ink-muted)`** | A-97 ②。失败通道另有其人：`.ai-plan-step.is-failed .ai-plan-marker`（红点）+ `.ai-plan-step.is-failed .ai-plan-state`（红字）⇒ 改中性**不丢失败信号** |
| `.flash-card-answer`（闪卡「另一面」的边框，**分类色**） | `border-color: var(--role-red)` | **`var(--ink-strong)`**（中性墨环；正面仍是 `--role-blue`） | A-97 ③。灰度也分得开：墨 ≈ 灰度 22 / 蓝 ≈ 灰度 82 |
| `.bar-heavy-flag`（「重日」标记点，**量级高 ≠ 失败**） | `background: var(--role-red)` | **`var(--role-blue)`** | A-97 ④。标记点落在柱顶**之上**（`bottom` = 柱高 − 3）⇒ 不与蓝柱面糊在一起（见 `bars-t640.png`：峰值柱是黄的，重日点是蓝的） |

**未动**（A-97 ①⑤ 豁免）：顶栏品牌三色点的红（装饰）、图谱「矛盾关系」红竖条（图谱按 A-8 冻结）。

---

## 2. 图谱区段逐字节未变

```
$ git show 7828e053:workbench/server/static/workbench.css > tmp/w2j/css-before.css
$ git show HEAD:workbench/server/static/workbench.css     > tmp/w2j/css-after.css
图谱区段（从 "/* Knowledge graph V2" 到 ".paper-toolbar, .paper-navigation" 之前）：
  改前 18711 字节 / 改后 18711 字节 → byte-identical: True
12 个裸名的 :root 块（--paper/--ink/--hair/--blue/--blueSoft/--yellow/--yellowSoft/
                    --red/--redSoft/--green/--graphite/--shadow）：
  byte-identical: True
```

**「逐字节」的判定口径说明**：区段的**边界**取「`/* Knowledge graph V2` 标记 → 图谱规则结束
（`.paper-toolbar, .paper-navigation` 之前）」这一段连续区段；若粗暴地取「标记 → 文件末尾」，
则会把图谱区段**之后**的共享规则（题号格等）也算进去 —— 那些不是图谱区段，
且本波确实改了其中的一部分（题号格几何，见 §六）。

**R-2 像素差 = 0**（画布矩形 `320,272 660×608`，9/9 组亮/夜配对全为 0，见 §1）。

**图谱区段之外的改动清单**（`git diff 7828e053..HEAD --unified=0` 的 hunk 位置）：
`@7`（文件头注释）· `@239`（删 `--dsw-state-success`）· `@358`（冻结块**补钉**，在图谱区段之前）·
`@1229/@1231`（lk-dot 颜色）· `@1674/@1676/@1688`（会话列表滚动）· `@1820`（`.ai-plan-summary`）·
`@2140`（`.status-dot` 删除）· `@2460`（今天圆点）· `@2531`（`.bar-fill` 动画）· `@2540`（重日点）·
`@2639…@2653`（热力日历五档）· `@3388`（连对横幅数字）· `@3548`（弱动效档闸门 —— **并发 agent 的**）·
`@4063…`（题号格几何，在图谱区段**之后**）—— **没有一条落在图谱区段内** ✅。

---

## 3. 六条验证命令（原样结果）

### 3.1 `python -m pytest tests -q`

```
FAILED tests/workbench/test_ui_routes.py::UiRouteTests::test_session_end_page_mentions_cards
E       AssertionError: '题目与闪卡' not found in '<!doctype html>...'
tests\workbench\test_ui_routes.py:418: AssertionError
=========================== short test summary info ===========================
FAILED tests/workbench/test_ui_routes.py::UiRouteTests::test_session_end_page_mentions_cards
1 failed, 1180 passed in 247.12s (0:04:07)
```

**⚠️ 这条失败不是本波造成的 —— 是并发 agent 的在途改动**：

* 断言要找的字符串 `题目与闪卡`，来自 `workbench/server/pages.py` 的一句
  「只补充尚未评分的**题目与闪卡**；已写入的记录不会重复出现。」
* 该句在**并发 agent 未提交的** `pages.py` 改动里被删掉了：
  ```
  $ git diff workbench/server/pages.py | grep -n "闪卡"
  190:-            "只补充尚未评分的题目与闪卡；已写入的记录不会重复出现。",
  $ git show HEAD:workbench/server/pages.py | grep -c "题目与闪卡"   → 1
  $ grep -c "题目与闪卡" workbench/server/pages.py                   → 0
  ```
* **隔离验证**（在 HEAD 的独立 worktree 里跑同一条测试，**没有碰主工作区**）：
  ```
  $ cd tmp/w2j/wt-head && python -m pytest tests/workbench/test_ui_routes.py::UiRouteTests::test_session_end_page_mentions_cards -q
  .                                                                        [100%]
  1 passed in 1.25s
  ```
  ⇒ 在**含本波全部 CSS 改动**、**不含并发 agent 的 pages.py 改动**的树上，这条测试**通过**。
* 本波**没有**碰 `pages.py`（`git diff 7828e053..HEAD --name-only` 里没有它）。

### 3.2 `python -m compileall -q lessonkit.py workbench pipeline pool tests`

```
（无输出）COMPILEALL OK (exit 0)
```

### 3.3 `openspec validate --specs --strict`

```
✓ spec/calendar-workload
✓ spec/daily-learning-plan
✓ spec/flash-card
✓ spec/knowledge-figures
✓ spec/mastery-evaluation
✓ spec/micro-quiz-content
✓ spec/practice-experience
✓ spec/practice-review
✓ spec/practice-set-export
✓ spec/problem-difficulty
✓ spec/retrieval-evaluation
✓ spec/review-workbench
✓ spec/workbench-content-governance
✓ spec/workbench-ui
Totals: 19 passed, 0 failed (19 items)
EXIT=0
```

### 3.4 `python lessonkit.py guard extract-problems --course dmath --chapter ch06`

```
Gate: extract-problems
Course: dmath
Chapter: ch06
Result: PASS

All required artifacts exist and check files contain no blocking markers.
EXIT=0
```

### 3.5 `node --test tests/workbench/*.test.js`

```
ℹ tests 264
ℹ suites 0
ℹ pass 264
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1026.7369
EXIT=0
```

### 3.6 `node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json`

```
  current ids     : 96
  only in baseline: (none)
  only in current : (none)

[converged coordinates — SI-0 target]
  differences     : 0

[initial coordinates (seed) — the 'same initial condition' half]
  differences     : 0

[summary]
  compared nodes  : 96
  coordinate diffs: 0
  seed diffs      : 0
  id set diffs    : 0
  total differences: 0

RESULT: PASS — converged coordinate diff = 0 (SI-0 green)
EXIT=0
```

---

## 4. 走查环境（隔离口径）

| 项 | 值 |
|---|---|
| 仓库根 cwd | `D:/Projects/Academic Workflow/lesson-kit`（`launch.py` 强制 `os.chdir`） |
| 端口 | **3523**（避开 3081/3092/3099/3177/3178/3184/3200/3201/3281/3282/3288/3411/3460/3461/3462/3477/3481/3482） |
| 启动 | `python tools/walkthrough/launch.py --scratch tmp/w2j/scratch --port 3523 --side after --seed-records 120 --seed-sessions 120` |
| `LESSONKIT_WB_HOME` | `tmp/w2j/scratch/registry`（隔离注册表） |
| 池副本 | `tmp/w2j/scratch/ws-walk/pool/dmath.db`（**按字节复制**） |
| 真实池 | `pool/dmath.db` sha256 `44fd434e5fb695c339597ca8a7ea2cfa45d8aaf5676a7b7db73f49dd97bc6daf` —— 播种前后**一致**（脚本自校验 `realPoolUnchanged: true`） |
| **服务字节数 == 磁盘字节数** | **终版复核**（全部 commit 落盘后重新起服务）：`workbench.css` served **196,861** = disk **196,861** ✅；`agent-ui.css` served **13,110** = disk **13,110** ✅（波中首次测得 190,979 / 12,767，亦相等 —— 两个数都指向同一件事：**服务跑的是仓库里这份代码**，不是 pip 安装快照） |
| 代理 | 全部请求带 `env -u http_proxy -u https_proxy -u all_proxy` |
| 采集一致性 | 视口 1440×900 / DPR 1 / `color_scheme=light`（主题由产品自己的 `localStorage['wb_settings_walk']` 驱动）/ `--force-color-profile=srgb --disable-lcd-text` / `prefers-reduced-motion: reduce`（除负荷柱录帧那一轮用 `no-preference`） |

---

## 5. 两处**要人工裁决的**（我只列出来，没有擅自改）

1. **`.primary` 按钮的墨色描边 + 硬阴影在夜纸下读作发光**
   （描边 vs 蓝面 2.64:1；文字 6.07:1 ✅）。**需要人工看图**：
   `openspec/changes/workbench-visual-language-v2/night-sweep-shots/practice-completion-night.png`
   与 `practice-stem-night.png`。可能要给权威表 §6.3 补一条窄例外。
   ⇒ **本波一个字未动**（`button.primary` 的 `border` / `box-shadow` 原样）。
2. **`.lk-dot--ink` 的语义**（已掌握 vs 未标记）⇒ **按建议落地**（N1 的 `--ink-faint`），
   **语义待裁**。改动的可见后果：夜纸下这枚点从「亮白点」变成「弱墨点」
   （卡面对比 13.96:1 → 4.97:1）。若裁定为「已掌握」，可能需要一个**独立的中性点 token**
   （而不是 `--ink-faint`），那就得改 token 层 ⇒ 属主会话的账。

---

## 6. 待裁决项（本波**没有**顺手改的）

| # | 事项 | 依据 / 现象 | 建议归属 |
|---|---|---|---|
| 1 | `motion-spec.md` §2.1 第 19 条把「负荷柱 / 日历扩散 / 庆祝进度」写在一起并给 `scaleX` + `transform-origin: left`；负荷柱的编码轴是**高度** ⇒ 本波按任务书取 `scaleY` + `bottom` | `design-notes/motion-spec.md:267` | 主会话（措辞是否拆分） |
| 2 | `agent-ui.css:263` 的 `box-shadow: -8px 0 28px rgb(0 0 0 / 6%)`（工件预览面板的**方向性**阴影）：不是浅色底，但**不随主题的抬升阶梯**走（夜纸的 `--elev-*` 是 30–52% 黑），夜纸下几乎不可见 | `agent-ui.css:263` | 主会话（要改得新增一个方向性阴影 token ⇒ 属 token 层） |
| 3 | 图谱冻结块补钉的取值口径：历史表 `graph-isolation.md` §7.2 把 `--surface-raised` 记为 `#fffefa`（旧 `--dsw-bg-layer-1`），本波取**亮色主题当前值** `#ffffff`（理由：面板是 15.4 新增、改造前无此物 ⇒ 参照系是今天亮色的样子，且亮色主题零变化） | `graph-isolation.md` §7.2 | 主会话（口径确认） |
| 4 | 题号格 `correct` 态的勾从「中下（压着题号）」挪到「右上角」—— 本波对既有形态的**可见改动**（题号可读性优先） | `workbench.css` 题号格块 | 主会话（形态确认） |
| 5 | `.lk-dot--yellow` 改标记档后，挖空符号（`--ink-on-warm`）在亮色主题下对标记档只有 **3.24:1**（≥3:1 但偏弱）。改成 `--ink-on-role` 可到 5.12:1，但会拉伸该 token 的语义（它原本是「蓝/红角色面上的文字」） | 实测 | 主会话（是否新增一个「深黄面上的文字」token） |
| 6 | `paper-dot` 的 `unanswered` 仍是 1px 细环（权威表 §4.17 的 `.lk-qcell` 写的是 2px 内环 + `--ink-disabled`）。本波只做「补几何」，**没做**形态整体对齐（那属 `.lk-qcell` 组件波） | `component-spec.md` §4.17 | IMPL-C1/C2 组件波 |
| 7 | 走查工作区没有第二份可开始的卷子 ⇒ `correct` / `filled` / `locked` 三态的题号格只能**用产品自己的类名在真实页面里注入**来核验（不是驱动出来的） | 见 §六 | 主会话（若要端到端取证，需在走查种子里多播一份卷子） |

---

## 7. 诚实回报（哪些没做到 / 打折 / 绕过了）

1. **`pytest` 有 1 条 FAIL**（`test_session_end_page_mentions_cards`）——**不是本波造成的**
   （并发 agent 未提交的 `pages.py` 文案删除），已用 HEAD 独立 worktree 隔离验证。
   本波**没有**去改那条测试或那条文案（不碰 `tests/` 与 `pages.py`）。
2. **「整页 AE = 0」的口径要打折说**：按 A-48 的 R-1 口径（排除左栏与顶栏）**9/9 组配对全为 0**；
   不排除左栏时，有 6/9 组是 **12 px**，那 12 px 在**左栏图谱导航图标的 SVG 抗锯齿**上，
   **同主题两次自比也会出现同样的 12 px** ⇒ 是栅格化非确定性，不是主题差异。
3. **`correct` / `filled` / `locked` 三态的题号格不是驱动出来的**，是用产品自己的类名在真实
   页面里注入后核验的（§六 已写明原因与做法）。
4. **题号格的 `correct` 勾被挪了位置**（中下 → 右上角）—— 这是一处**既有形态的可见改动**，
   虽在「补几何」的名义下，但**不是纯增量**。
5. **热力日历的混色底选了 `--surface-card`**（日历所在的 `.card` 面），而不是任务书举例的
   `--asset-paper`。两者在非图谱页同值（`--asset-paper: var(--surface-card)`），
   差别只在图谱作用域（那里被钉成 `#fffdf7`）—— 但记录中心不在图谱页，故**无实际差别**。
6. **并发 agent 在同一分支上改了同一个文件**（`workbench.css` 的弱动效档闸门，
   commit `73ddd4d8`）。本波的 9 个 commit **每一个都只含本波的改动**
   （逐个 `--stat` 已核），未把对方的在途改动扫进任何 commit；反过来也**没有**把对方的
   commit 覆盖掉。工作区当前仍有对方的在途改动（`pages.py` / `practice-flow.js` /
   `workbench.js` / `tools/walkthrough/probe.py`），本波**一行未碰**。
7. **负荷柱的 320ms 时长**取自 `motion-spec.md` §2.1 第 19 条（该文件不在本波所有权内，
   未改）；CSS 里因此出现一处**非 token 的字面时长**（与 `flash-answer-reveal 620ms` 同款写法）。
8. `tmp/w2j/` 下有本波的实测脚本与产物（gitignored，未提交）；报告引用的截图已复制到
   `reports/IMPL-W2j-shots/`（436 KB）。
