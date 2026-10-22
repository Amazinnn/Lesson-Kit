# 夜纸（暗色）主题全站巡检报告 — IMPL-N1

> **本文件是巡检产物，不是规范。** 行为契约以 `openspec/changes/workbench-visual-language-v2/specs/*/spec.md`
> 为准，视觉基线以 `design-notes/night-paper-tokens.md`（53 个值 token）为唯一依据。
> **本任务只出报告，不改产品代码** —— `workbench/` / `pool/` / `pipeline/` 一行未动。
>
> 截图产物：本目录下的 `night-sweep-shots/`（22 张 PNG + `index.json`，合计 **2.38 MB**）。

---

## 0. 结论速览

| 项 | 结果 |
|---|---|
| 巡检页态 | **17 个页态 × 2 主题**（亮/夜），逐元素枚举 **12 – 943** 个元素/页 |
| **P0** | **1 项** —— 图谱页在夜纸下**并非完全相同**：章节透镜下拉面板取了夜纸值（§3.1） |
| **P1** | **3 项** —— 记录中心热力日历亮块残留 + 编码倒转（§3.2）／练习页「今天」圆点数字不可见（§3.3）／知识点列表 `lk-dot--ink` 亮白点（§3.4） |
| **P2** | **3 项** —— 主按钮墨色描边在夜纸下读作发光（需人工看图）／Agent 审批卡硬编码 `#fff9df`（需人工看图）／两条**亮色主题**既有缺陷登记备查 |
| 零缺陷页态 | 工作台、知识点详情、记录中心（练习/试卷 · 作答明细 · 错题）、练习集、设置视图 —— **共 8 个页态 0 条 finding** |
| 图谱页默认态 | **夜纸与亮色逐字节相同**（同一 sha256）⇒ 冻结块在默认态成立（§2） |
| 图谱页章节透镜展开态 | **变了**（整页 AE = 109,912 px）⇒ **P0**（§3.1） |
| 真实池 `pool/dmath.db` | **未变**：sha256 `44fd434e…` / size `868352` / mtime_ns `1792479648444559700`（巡检前后一致） |

---

## 1. 巡检环境与方法

### 1.1 隔离走查服务

```bash
python tools/walkthrough/launch.py \
    --scratch tmp/night-sweep-scratch --port 3391 --side after
```

| 隔离项 | 值 |
|---|---|
| 仓库根 cwd | `D:/Projects/Academic Workflow/lesson-kit`（launch.py 强制 `os.chdir`） |
| 端口 | `3391`（**不是** `3081`；`launch.check_port` 会拒绝 `3081`） |
| `LESSONKIT_WB_HOME` | `tmp/night-sweep-scratch/registry`（隔离注册表，不指向 `~/.lessonkit-workbench`） |
| 池副本 | `tmp/night-sweep-scratch/ws-walk/pool/dmath.db`（**按字节复制**，inode 与源不同） |
| A1/A2/A3 隔离硬断言 | `launch.assert_isolated` 在 init 后立即跑，**任何一条不成立即抛异常终止** |

### 1.2 服务字节数 = 磁盘字节数（硬门槛）

| 文件 | 服务返回 | 磁盘 | 相等 |
|---|---|---|---|
| `workbench.css` | 177,728 | 177,728 | ✅（sha256 亦相同） |
| `agent-ui.css` | 12,767 | 12,767 | ✅ |
| `workbench.js` | 257,770 | 257,770 | ✅ |

⇒ 服务跑的是**仓库里这份**代码，不是 pip editable 安装指向的旧快照。

### 1.3 采集一致性要素（照 `tools/walkthrough/shots.py` §5.2 钉死）

| 变量 | 取值 |
|---|---|
| 视口 / DPR | 1440×900 / `device_scale_factor=1` |
| `color_scheme` | **恒为 `light`**（避免 UA 层随系统变；主题由产品自己的 `wb_settings_walk` 键驱动 ⇒ 两态可比） |
| 主题切换 | `localStorage['wb_settings_walk'] = {"theme":"night"\|"day"}`（产品自己的存储键，首屏内联脚本消费） |
| `reduced_motion` | `reduce`（图谱页必需：否则布局不可复现） |
| locale / timezone | `zh-CN` / `Asia/Shanghai` |
| 浏览器参数 | `--force-color-profile=srgb --disable-lcd-text` |
| 动画 | 截图前轮询 `document.getAnimations()`，无有限时长动画在跑 |

### 1.4 判定口径（**不许手抄**）

- 对比度公式与判定线**直接取自 `tools/verify_tokens.py`**（WCAG 2.x 相对亮度，`ratio()`），
  本报告每个数字都是脚本实算值。
- 判定线（权威表 §4.1）：**正文/次要文字 ≥ 4.5:1**；**三级文字**（`--ink-faint` / `--ink-disabled`）
  **≥ 3:1**；**大字号**（≥24px，或 ≥18.66px 且字重 ≥700）**≥ 3:1**；**非文本边界 ≥ 3:1**。
- **有效背景**：沿祖先链把半透明背景逐层合成到第一个不透明背景（画布底取 `body` 底色），不做近似。
- **「亮色块」**：元素自身底色（含 alpha 合成后）三通道**均 ≥ 200**（对应任务书里的 `rgb(2xx,2xx,2xx)`）。
- **「不可见元素」**：文字色与有效背景对比 **< 1.2:1**。
- **「未跟随主题」**：同一元素（按 DOM 路径配对）在亮/夜两态的 computed 值（color / background-color /
  border-top-color / border-top-width / background-image）**逐项完全相同**。
- **硬编码亮色残留**：夜纸下仍出现亮色块，且其取值不随主题改变 —— 用 `getComputedStyle` 枚举，不靠看图。

### 1.5 巡检页态清单（17）

| # | 页态 | URL |
|---|---|---|
| 1 | 工作台 | `/` |
| 2 | 练习页 · 建卷态 | `/w/walk/practice` |
| 3 | 练习页 · **题面** | `/w/walk/practice?paper=<id>`（E1 起手后） |
| 4 | 练习页 · **解析**（参考答案 + 判定依据 + 解析） | 同上，作答后 |
| 5 | 练习页 · **作答区** | 同上，文本题 |
| 6 | 练习页 · **完成页** | 同上，交卷后 `#paper-completion` |
| 7 | 练习页 · 时间安排日历（「今天」圆点） | 同上，展开「目标与时间安排」 |
| 8 | 知识点列表 | `/w/walk/kps` |
| 9 | 知识点详情 | `/w/walk/kp/<id>`（从列表页取第一条链接） |
| 10 | 记录中心 · 概览 | `/w/walk/records?view=overview` |
| 11 | 记录中心 · 练习/试卷 | `/w/walk/records?view=runs` |
| 12 | 记录中心 · 作答明细 | `/w/walk/records?view=attempts` |
| 13 | 记录中心 · 错题 | `/w/walk/records?view=wrong` |
| 14 | 练习集 | `/w/walk/practice-sets` |
| 15 | 设置视图 | `/w/walk/settings` |
| 16 | 图谱页 · 默认态 | `/w/walk/graph` |
| 17 | 图谱页 · 控制卡展开 / 章节透镜展开 | 同上（S-G3 / 章节透镜面板） |

---

## 2. 图谱页：夜纸与亮色是否完全相同（**R-3 口径**）

> 口径出处：`design-notes/graph-isolation.md` §6.7（A-48 / A-65）。
> **R-1** = 整页（排除左栏 `x<280` 与顶栏 `y<52`）· **R-2** = `.graph-workspace` 裁剪矩形
> · **R-3** = 画布矩形 + 三栏各一个纯色采样点。**G-5 判为 R-2 + R-3。**

### 2.1 默认态（S-G1）：**逐字节相同** ✅

| 指标 | 亮色 | 夜纸 | 判定 |
|---|---|---|---|
| `html[data-theme]` | `""` | `"night"` | 主题属性**确实**翻成了夜纸 |
| `body` 背景 | `rgb(255,253,247)` | `rgb(255,253,247)` | 相同（图谱冻结块生效） |
| **R-1 差异像素** | — | **0** | ✅ |
| **R-2 差异像素**（画布区 `320,272 660×608`） | — | **0** | ✅ |
| **R-3 差异像素**（画布矩形 `320,284 660×596`） | — | **0** | ✅ |
| R-3 采样点 · 左栏纸面 `(6,58)` | `[243,241,234]` | `[243,241,234]` | 同色 ✅ |
| R-3 采样点 · 右栏纸面 `(1043,86)` | `[255,254,250]` | `[255,254,250]` | 同色 ✅ |
| R-3 采样点 · 画布 `(326,290)` | `[252,250,246]` | `[252,250,246]` | 同色 ✅ |
| 静止签名（节点位置/尺寸/透明度，1932 字符） | — | **逐字相同** | ✅ |
| **整页截图 sha256** | `7b24423a5b52…` | `7b24423a5b52…` | **逐字节相同** ✅ |

> 证据：`night-sweep-shots/graph-day.png` 与 `night-sweep-shots/graph-night.png`
> —— **两个文件 sha256 完全相同**，肉眼与字节都无法区分。

### 2.2 控制卡展开态（S-G3）：**逐字节相同** ✅

| 指标 | 亮色 | 夜纸 | 判定 |
|---|---|---|---|
| `#graph-controls` 的 `data-collapsed` | `false`（已展开） | `false`（已展开） | 状态对齐 |
| R-1 / R-2 / R-3 差异像素 | — | **0 / 0 / 0** | ✅ |
| 整页截图 sha256 | `013883bfb763…` | `013883bfb763…` | **逐字节相同** ✅ |

> 证据：`night-sweep-shots/graph-S-G3-day.png` / `graph-S-G3-night.png`。

### 2.3 逐元素 computed 值双态对比（默认态）

> 比对对象：图谱页**全部 688 个元素**（`getComputedStyle` 全量枚举，含隐藏节点）；
> 另在巡检探针里按「可见且有盒子」过滤后为 400 个元素，两组口径结论一致。

| 结果 | 数量 | 说明 |
|---|---|---|
| 亮/夜两态 **完全相同** | **397 / 400**（可见口径） | 图谱冻结块生效 |
| 亮/夜两态 **不同** | **3** | `html`、`input#chapter-lens-switch`、`input#setting-show-rating` —— 三者的 `color` / `border-top-color` 由 `rgb(0,0,0)` 变成 `rgb(255,255,255)`，来源是 `color-scheme: dark` 让 UA 默认文字色变白。**这三个都不是可见文字载体**（一个是根元素、两个是视觉隐藏的 checkbox），**像素影响 = 0**（R-1/R-2/R-3 全 0 已证）。 |

### 2.4 非图谱页的反向证据：主题跟随是完整的

| 页 | 五项取值（`color` / `background-color` / `border-top-color` / `border-top-width` / `background-image`）在亮/夜两态**完全相同**的元素数 |
|---|---|
| 工作台 / 知识点详情 / 知识点列表 / 练习集 / 设置 / 记录中心 4 视图 / 练习页 5 态 | **全部 = 0** |

⇒ 非图谱页**没有任何一个元素**的 computed 取值在亮/夜两态完全相同；
图谱页则**几乎每一个元素**都不变。冻结与跟随两条边界都落在该落的位置。

---

## 3. 逐页问题清单

### 3.1 【P0】图谱页 · 章节透镜下拉面板在夜纸下变了（图谱冻结块漏钉 token）

| 项 | 值 |
|---|---|
| **页面** | `/w/walk/graph`（图谱页）· 顶栏「章」章节透镜展开态 |
| **元素** | `#chapter-lens-panel` / `.chapter-lens-panel`（`workbench.css:589-603`） |
| **实测（亮）** | 底色 `rgb(255,255,255)`（`--surface-raised` 浅 `#ffffff`）；阴影 `rgba(61,52,37,.1) 0 4px 12px, rgba(61,52,37,.12) 0 20px 48px`（`--elev-3` 浅） |
| **实测（夜）** | 底色 `rgb(43,38,32)`（`--surface-raised` 夜 `#2b2620`）；阴影 `rgba(0,0,0,.52) 0 20px 48px, rgba(255,236,200,.06) 0 0 32px, inset …`（`--elev-3` 夜） |
| **像素后果** | 面板展开后**整页 AE = 109,912 px**；面板矩形 `(215,48)-(391,96)` 内 **AE = 7,800 px**；差异带 `x∈[158,448] · y∈[11,172]` |
| **文字后果** | 面板内章节项文字用的是**未钉**的 `--ink-body`（夜纸 `#e7dfd0`）落在夜纸深底 `#2b2620` 上 = **11.32:1** ⇒ **文字本身可读**；问题在「**面板颜色**」，不在「文字」 |
| **视觉后果** | 图谱页整体被冻结成亮色（`body` 底两态同为 `#fffdf7`），唯独这个顶栏浮层在夜纸下变深 ⇒ 夜纸下点开「章」透镜，会看到一块**深色浮层压在亮色图谱上** |
| **证据** | `night-sweep-shots/graph-lens-day.png` vs `night-sweep-shots/graph-lens-night.png` |

**根因**：图谱冻结块（`workbench.css:336-433`，`body:has(#layout[data-page="graph"])`）钉回了
`--surface-base/card/sunken/sheet`、`--ink-strong/muted/faint`、`--role-blue/yellow/red`、`--rule-*`、
`--r-*`、`--veil-hover`、`--asset-*`、`--shell-measure` 等，**但没有钉**
`--surface-raised`、`--elev-2/3`、`--ink-body`、`--ink-on-role`、`--ink-on-warm`、
`--role-blue-soft`、`--role-red-wash`、`--role-red-soft`、`--veil-active`、`--veil-modal`、
`--focus-*`、`--skeleton-*`、`--art-*`、`--heat-*`。
面板与控制卡阴影用的正是 `--surface-raised` + `--elev-3` ⇒ 漏钉即刻显形。

**建议修法**（二选一，**本任务不改代码**）：
1. 在图谱冻结块里补钉：`--surface-raised: #ffffff; --elev-2: <旧值>; --elev-3: <旧值>;`（以及图谱页
   实际读到的其余未钉 token），使图谱页「任何态」都与亮色逐字节相同；
2. 或把章节透镜面板**移出**图谱作用域（它属顶栏，而顶栏按 A-48 本就不在像素比对口径内 —— 见 §5 待裁决项）。

---

### 3.2 【P1】记录中心 · 概览 —— 热力日历与图例色块在夜纸下仍是亮色块，且编码语义倒转

| 项 | 值 |
|---|---|
| **页面** | `/w/walk/records?view=overview` |
| **元素** | `.record-activity-day.level-0..4`（本轮 **81 个日历格子**：79 个 level-0 + 1 个 level-1 + 1 个 level-3）· `.lk-legend__swatch.level-0..4`（**5 个图例色块**） |
| **根因** | `workbench.css:2568-2576`：`--level-bg: color-mix(in srgb, var(--role-blue) N%, white)` —— **混色底写死 `white`**，不随主题 |
| **实测（夜纸）** | level-0 = `color(srgb 0.950235 0.961176 0.988353)` = **#f2f5fc**；level-1 = **#e5ebf9**；level-2 = **#cfd9f3**；level-3 = **#b1c2ec**；level-4 = **#91a9e5** |
| **实测对比（夜纸，落在卡面 `#232019`）** | level-0 **14.89:1** · level-1 **13.61:1** · level-2 **11.51:1** · level-3 **9.13:1** · level-4 **6.97:1** |
| **实测对比（亮色，落在卡面 `#fffdf7`）** | level-0 **1.11:1** · level-1 **1.26:1** · level-2 **1.61:1** · level-3 **2.28:1** · level-4 **3.43:1** |
| **「亮色块」判定** | level-0/1/2 三通道 **均 ≥ 200**（#f2f5fc / #e5ebf9 / #cfd9f3）⇒ **83 个元素**（79 个 level-0 格子 + 1 个 level-1 格子 + 3 个 level-0/1/2 图例色块）命中「夜纸下仍出现 `rgb(2xx,2xx,2xx)` 亮色块」；level-3/4（#b1c2ec / #91a9e5）虽是浅色但三通道未全 ≥200，未计入 |
| **后果** | 「**0 次**」这一档（绝大多数格子）成为整块面板里**最亮**的东西 ⇒ 热力编码在夜纸下被**倒转**（最少 = 最亮）；且这 83 块亮色是夜纸下唯一的浅色残留 |
| **证据** | `night-sweep-shots/records-overview-night.png`（日历区 y≈540–730、图例 y≈770）· 对照 `records-overview-day.png` |

**建议修法**：把混色底从 `white` 换成主题底（`var(--surface-card)`），或直接改读权威表 §3.10 已有的
夜纸热力 token `--heat-1..4` = `#31343c / #414b64 / #51628b / #6178b3`（权威表 §3.10 的夜纸热力是
「蓝 18%→78% **混夜纸卡面**」，与浅色的「混白」同配方、只换混色底）。
5 档 ↔ 4 token 的映射建议：`level-0` 用 `--surface-sunken`（零负荷有独立档，不回落底色，
`records.py::_calendar_level` 口径），`level-1..4` 用 `--heat-1..4`。
⚠️ 该修法会同时改动亮色主题的取值 —— 属「用户可感知行为」，**须先改 OpenSpec 再动代码**。

---

### 3.3 【P1】练习页 ·「今天」日历圆点的日期数字在夜纸下几乎不可见

| 项 | 值 |
|---|---|
| **页面** | `/w/walk/practice`（中栏「目标与时间安排 → 本月安排」日历） |
| **元素** | `.calendar-cell.today .calendar-day`（`workbench.css:2381-2384`） |
| **根因** | `color: var(--ink-strong); background: var(--role-yellow);` —— 黄面上的文字用了 `--ink-strong`，而不是黄面专用的 `--ink-on-warm` |
| **实测（夜纸）** | 文字 `rgb(244,237,224)`（`--ink-strong` 夜 `#f4ede0`）落在底色 `rgb(224,193,81)`（`--role-yellow` 夜 `#e0c151`）上 ⇒ **1.51:1** |
| **实测（亮色）** | 文字 `rgb(34,31,26)`（`--ink-strong` 浅 `#221f1a`）落在 `rgb(245,197,24)`（`--role-yellow` 浅 `#f5c518`）上 ⇒ **10.07:1 ✅** |
| **判定** | 夜纸下 1.51:1 < 1.2:1 的「不可见」只差 0.3，远低于正文判定线 4.5:1 ⇒ 「今天是哪天」在夜纸下读不出来 |
| **影响面** | 练习页 **5 个页态**（题面 / 解析 / 作答区 / 完成页 / 时间安排）**都带这段日历** ⇒ 四态全部命中同一条 finding |
| **证据** | `night-sweep-shots/practice-calendar-night.png`（黄底上的「22」几乎看不见）· 对照 `practice-calendar-day.png`（黑底黄点上的「22」清清楚楚） |

**建议修法**：`color: var(--ink-on-warm)` —— 权威表 §3.4 / §5 明确「黄面上的文字一律用 `--ink-on-warm`」
（夜纸 `#14120f` ⇒ 落在 `#e0c151` 上 **10.61:1 ✅**；浅色 `#221f1a` ⇒ **10.07:1**，**亮色主题零变化**）。
这是**一处 token 换名**、两主题观感都不坏的最省事修法。

---

### 3.4 【P1】知识点列表 · `lk-dot--ink` 状态圆点在夜纸下变成一枚亮白点

| 项 | 值 |
|---|---|
| **页面** | `/w/walk/kps`（知识点列表行末的状态圆点） |
| **元素** | `.knowledge-state-dot.lk-dot--ink`（`workbench.css:1197`：`--dot-fill: var(--ink-strong); --dot-mark: var(--ink-on-role);`） |
| **实测（夜纸）** | 自身底色 `rgb(244,237,224)` = `#f4ede0`（`--ink-strong` 夜），落在卡面 `#232019` 上 ⇒ **13.96:1** |
| **对比** | 同排的红点 `--role-red` 夜 `#d4736b` = **5.00:1**、黄点 `--role-yellow` 夜 `#e0c151` = **9.86:1** ⇒ **「中性点」反而是三点里最亮的** |
| **判定** | 非文本对比**达线**（13.96:1 ≥ 3:1），**不是 WCAG 缺陷**；但「中性 / 无状态」的圆点用 `--ink-strong` ⇒ 夜纸下变成整页最亮的小件，**语义与视觉相反**（亮色主题下 `--ink-strong` 是深墨，恰好是「弱」，所以这是夜纸才暴露的语义漂移） |
| **证据** | `night-sweep-shots/kps-night.png`（行末三枚圆点：红 / 黄 / 白） |

**建议修法**：`--dot-fill` 改用 `--ink-faint`（夜纸 `#978d7c` ⇒ 卡面 **4.97:1**；浅色 `#8d8578` ⇒ 卡面 **3.59:1**
—— 亮色主题也在 3:1 之上，且比状态点弱）。或者把 `lk-dot--ink` 单独钉一个「中性点」token，
但**先要确认它的语义**（是「已掌握」还是「未标记」）——见 §5 待裁决项。

---

### 3.5 【P2】主按钮的墨色描边 + 硬阴影在夜纸下读作「发光」

| 项 | 值 |
|---|---|
| **页面** | 练习页（`提交试卷`）、完成页（`查看本次答卷`）、练习集空态（`去组卷`）等所有 `.primary` 按钮 |
| **元素** | `button.primary`（`workbench.css:898-903`）：`border: 1px solid var(--ink-strong); box-shadow: 2px 2px 0 var(--ink-strong);` |
| **实测（夜纸）** | 描边 `#f4ede0`（`--ink-strong` 夜）；按钮填色 `--role-blue` 夜 `#7291de`；按钮文字 `--ink-on-role` 夜 `#14120f` ⇒ **6.07:1 ✅**（文字达标）；描边与**自身填色**对比 **2.64:1** |
| **判定** | 文字对比度**达标**，描边 2.64:1 是「描边 vs 自身填色」而非「控件边界 vs 周围面」，**不构成 WCAG 1.4.11 缺陷**。但夜纸下 `--ink-strong` 变成近白色 ⇒ 蓝按钮外围一圈近白描边 + 近白硬投影，在深底上读作「发光描边」，与基线「不用描边」（权威表 §6.3 的**四条**窄例外不含按钮墨边）不一致 |
| **结论** | **需人工看图** —— 这不是可自动判定的对比度问题 |
| **证据** | `night-sweep-shots/practice-completion-night.png`（「查看本次答卷」按钮）、`practice-stem-night.png`（「提交试卷」按钮） |

### 3.6 【P2】Agent 右栏审批卡：硬编码亮色 `#fff9df`

| 项 | 值 |
|---|---|
| **页面** | 任何工作区页的右栏（Agent 对话 → 试卷审批卡） |
| **元素** | `.agent-approval-card`（`workbench/server/static/agent-ui.css:346`）：`background: #fff9df;` —— **写死的浅黄**，不走 token |
| **判定** | 夜纸下会是一块约 **15:1** 的浅黄亮块落在夜纸卡面上 ⇒ 硬编码亮色残留 |
| **为什么没截图** | 本轮无 AI 会话、**触达不到该态**（Agent 右栏空态）⇒ **需人工看图**（本报告不附该图） |
| **建议修法** | 改用 `--role-yellow-soft`（浅 `#fcf0cd` / 夜 `#3d3721`）或 `--art-wash-yellow`（浅 `#fdf3cf` / 夜 `#3d3721`） |

### 3.7 【P2·登记备查】两条**亮色主题**的既有缺陷（不是夜纸问题）

| 元素 | 亮色实测 | 夜纸实测 | 说明 |
|---|---|---|---|
| `.lk-combo-banner__count { color: var(--role-yellow) }`（`workbench.css:3280-3285`） | **1.54:1** ❌ < 3:1 | **9.86:1 ✅** | 庆祝大数字用「面积档」黄当字色。**夜纸反而达标** —— 这是亮色主题的缺陷 |
| `.lk-dot--yellow { --dot-fill: var(--role-yellow) }`（`workbench.css:1196`） | **1.60:1** ❌ < 3:1 | **9.86:1 ✅** | 权威表 §4.4-10 已明令「黄色状态圆点改用**标记档** `--role-yellow-deep`」，CSS 未落地 |

⇒ 两条都违反权威表 §4.4-10 的裁定，但**只在亮色主题下暴露**。本任务只报不改，
登记给「亮色主题对比度」那一摊（可并入 IMPL-N2 / N3 的范围，请所有者裁决）。

---

## 4. 已核通过（0 条 finding）的页态

| 页态 | 元素数（夜纸） | 结论 |
|---|---|---|
| 工作台 `/` | 12 | 全部随主题翻转，无低对比、无亮块残留 |
| 知识点详情 `/w/walk/kp/<id>` | 943 | 同上 |
| 知识点列表 `/w/walk/kps` | 276 | 仅 §3.4 的 `lk-dot--ink` 一条 |
| 记录中心 · 练习/试卷 `?view=runs` | 159 | 0 条 |
| 记录中心 · 作答明细 `?view=attempts` | 215 | 0 条 |
| 记录中心 · 错题 `?view=wrong` | 205 | 0 条 |
| 练习集 `/w/walk/practice-sets` | 238 | 0 条 |
| 设置视图 `/w/walk/settings` | 150 | 0 条 |
| 记录中心 · 概览 `?view=overview` | 458 | 仅 §3.2 的热力档 83 条 |
| 练习页 · 题面 / 解析 / 作答区 / 完成页 | 347 / 362 / 333 / 328 | 各 1 条 —— **全是 §3.3 的同一个 `.calendar-day`** |

**已核通过的具体项（抽样实测，均取自夜纸）**：

| 元素 | 实测 |
|---|---|
| 按钮/表单文字 `--ink-body` `#e7dfd0` 落在卡面 `#232019` | **12.28:1 ✅** |
| 次要文字 `--ink-muted` `#c2b8a5` 落在卡面 | **8.28:1 ✅** |
| 三级文字 `--ink-faint` `#978d7c` 落在卡面 | **4.97:1 ✅** |
| 主按钮文字 `--ink-on-role` `#14120f` 落在蓝面 `#7291de` | **6.07:1 ✅** |
| 链接蓝 `--role-blue` `#7291de` 落在卡面 | **5.28:1 ✅** |
| 红字 `--role-red-ink` `#e08878` 落在沉底 `#272319` | **5.94:1 ✅**（红洗底 `#352821` 上 5.39:1） |
| 题号格 `.paper-dot.state-unanswered` `#f4ede0` 落在 `#1c1a16` | **14.92:1 ✅** |
| 题号格 `.paper-dot.state-wrong` `#e08878` 落在 `#352821` | **5.39:1 ✅** |
| 判定条 `.record-verdict-dist-fill--bad` `#e08878` 落在 `#272319` | ✅ |
| 自评圆点 `.record-rating-dot` `#f0d98a`（`--role-yellow-deep`）落在卡面 | **11.61:1 ✅** |
| 沉底内容块（作答区 / 解析纸）文字 `--ink-body` 落在 `#272319` | **11.83:1 ✅** |

---

## 5. 待裁决项

| # | 事项 | 说明 | 建议归属 |
|---|---|---|---|
| **Q-1** | **章节透镜面板在图谱页要不要跟夜纸？** | 面板属**顶栏浮层**。A-48 已把「左栏与顶栏」排除出像素比对口径（`R-1` 改为「除左栏与顶栏外像素级一致」，`G-5` 判为 `R-2` + `R-3`）⇒ **按既定口径，它不判 FAIL**；但「图谱页在夜纸下取值必须与亮色完全相同」这句承诺字面上不成立。两种解法（补钉冻结块 / 把面板移出图谱作用域）**后果不同** | `graph-node-visual-language`（图谱 change）+ 本 change 的冻结块 |
| **Q-2** | **热力日历混色底改主题底会不会动到亮色主题的观感？** | §3.2 的修法必然同时改亮色取值（`mix(#2b62e8 N%, white)` → `mix(#2b62e8 N%, var(--surface-card))`）。浅色下 `--surface-card` = `#fffdf7` ≈ `white`，**Δ 极小**，但仍是「用户可感知行为」 ⇒ 按 AGENTS.md 纪律 1 须先改 OpenSpec | 本 change（值层） |
| **Q-3** | **`lk-dot--ink` 的语义是什么？** | 「已掌握」还是「未标记」？语义不同 ⇒ 修法不同（换成 `--ink-faint` 还是新钉一个中性点 token）。另：权威表 §4.4-10 明确「黄色状态圆点改用标记档 `--role-yellow-deep`」，而 CSS 用了面积档 `--role-yellow`（两主题都违反，只是夜纸恰好达标） | 本 change |
| **Q-4** | **`.primary` 按钮的墨色描边在夜纸下留不留？** | 留 ⇒ 夜纸下蓝按钮外围一圈近白发光描边；不留 ⇒ 要给按钮补一条 §6.3 的窄例外。**这不是可自动判定的缺陷**，需要一次视觉裁决 | 本 change（值层 + §6.3 例外表） |
| **Q-5** | **`.agent-approval-card` 的硬编码 `#fff9df` 归谁？** | 它在 `agent-ui.css` 里，是「Agent 右栏」的地盘；本轮触达不到该态、无截图。改法建议 `--role-yellow-soft` 或 `--art-wash-yellow` | 本 change（或 Agent UI 专项） |
| **Q-6** | **本轮巡检的数据覆盖度** | 池里只有 3 条 `problem_attempts`、1 个章节（ch06）、无 AI 会话 ⇒ 空态（练习集空态已覆盖）、错题仅 1 条、审批卡/骨架屏/里程碑庆祝等态**未触达**。这些态按纪律记「需人工看图」，**不记通过** | 下一轮补种子 |

---

## 6. 复跑方法

```bash
cd "D:/Projects/Academic Workflow/lesson-kit"

# 1) 起隔离走查服务（仓库根 cwd、独立端口、池副本 + 隔离注册表）
python tools/walkthrough/launch.py \
    --scratch tmp/night-sweep-scratch --port 3391 --side after

# 2) 字节数门槛：服务返回必须等于磁盘字节数
python - <<'PY'
import urllib.request
for f in ("workbench.css","agent-ui.css","workbench.js"):
    s=len(urllib.request.urlopen("http://127.0.0.1:3391/static/"+f).read())
    d=len(open("workbench/server/static/"+f,"rb").read())
    print(f, s, d, "EQUAL", s==d)
PY

# 3) 对比度公式与判定线的唯一来源（值集核对 + 43 组配对复测）
python tools/verify_tokens.py
```

本轮探针脚本（枚举 computed style、双态对比、图谱 R-3 取证、截图采集）放在
`tmp/night-sweep-scratch/`（**`tmp/` 被 `.gitignore` 忽略，不入库**）：

| 脚本 | 职责 |
|---|---|
| `sweep.py` | 逐页逐态采集 ＋ 逐元素 finding 判定（不可见 / 低对比 / 亮块 / 未跟随主题） |
| `dual.py` | 亮/夜双态逐元素 computed 值对比 |
| `graph_r3.py` | 图谱页 R-1 / R-2 / R-3 三口径 + 采样点 + 静止签名 + 逐元素双态对比 |
| `graph_states.py` | 图谱页 S-G1 / S-G3 两态的夜/亮像素比对 |
| `graph_lens.py` | 图谱页章节透镜面板展开态的夜/亮像素比对（P0 取证） |

> ⚠️ `tools/walkthrough/README.md` §9.8 已记：**走查期间 `workbench/` 仍在被别的分支改动**，
> 同一份代码在不同轮次跑出的结论可能不同。**本报告对应的是 2026-10-22 的工作区状态**，
> `workbench.css` sha256 前缀 `b5a8f3e0…`（服务字节数 177,728）。
> 复跑时若 `workbench.css` 变了，本报告的实测值需重跑。

---

## 7. 硬约束遵守情况

| 约束 | 状态 |
|---|---|
| 只新建 `night-sweep-report.md` 与 `night-sweep-shots/` | ✅ 未新建其它仓库路径（探针脚本全在 gitignore 的 `tmp/`） |
| **不改产品代码**（`workbench/` / `pool/` / `pipeline/`） | ✅ 一行未动（`git status` 干净，除本任务新增的两个路径） |
| 不改 `docs/` / `openspec/` 下其它文件 | ✅ 未改 |
| **不写真实池** | ✅ `pool/dmath.db` 的 sha256 `44fd434e5fb695c339597ca8a7ea2cfa45d8aaf5676a7b7db73f49dd97bc6daf` / size `868352` / mtime_ns `1792479648444559700` **巡检前后完全一致**；所有写入落在 `tmp/night-sweep-scratch/ws-walk/pool/dmath.db`（副本） |
| 不放宽阈值 | ✅ 判定线全部取自 `tools/verify_tokens.py` 与权威表 §4.1；判不出来的一律写「需人工看图」并给截图路径（§3.5 / §3.6） |
| 截图入库 | ✅ 落在 `night-sweep-shots/`（**不在 `tmp/`**），22 张 PNG + `index.json`，合计 **2.38 MB** |

---

## 8. 引用

| 文件 | 用途 |
|---|---|
| `design-notes/night-paper-tokens.md` §3 / §4.1 / §4.4 / §5 | 值表、判定线、WCAG 公式、11 条已修不达标项、黄面文字档位 |
| `design-notes/graph-isolation.md` §6.3–§6.8 | 九步冻结协议、三口径（R-1 / R-2 / R-3）、状态矩阵 S-G1…S-G7 |
| `tools/verify_tokens.py` | **对比度公式的唯一来源**（`ratio()` / `lum()`），本报告所有数值均由它实算 |
| `tools/walkthrough/launch.py` / `README.md` | 隔离环境（A1–A4）、字节数门槛、一致性要素 |
| `tools/walkthrough/g5.py` | 图谱页冻结采集与三口径比对（本轮沿用其 `GRAPH_JS` 与静止签名） |
| `openspec/changes/workbench-visual-language-v2/contrast-measurements.md` | token 层 43 组配对复测（**全部达标**）—— 本报告是**页面层**的补充，两层不冲突 |
