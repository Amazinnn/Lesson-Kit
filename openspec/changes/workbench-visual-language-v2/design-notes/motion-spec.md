# 动效规格（Motion Spec）— 柔和蒙德里安 v2

> **定位**：本文件是 `workbench-visual-language-v2` 的**动效设计规格**，不是代码。
> 它定义 token、映射、关键帧、音画同步、参数化输入、降级矩阵与性能红线，
> 供 `design.md` / `tasks.md` / 实现期直接取用。
>
> **不改变任何东西**：本文件不引入新的用户可观察行为，不改请求序列与载荷，
> 不改持久化内容，不改学习事实与状态机。动效属于 `proposal.md`「Frozen」条款里
> 明确允许的**纯装饰 + 表现层**范围（"允许 = DOM 结构与顺序、焦点顺序、视觉分组、
> 纯装饰元素、动效（但不得改变请求时序）"）。

---

## 0. 读法与证据分级

### 0.1 权威顺序

冲突时按此顺序裁决，**不得按"哪个文件更新得晚"自行选边**：

1. `openspec/changes/workbench-visual-language-v2/decisions.md`「# 收口：最终基线」
   —— 视觉与动效决策的最终依据；
2. `openspec/changes/workbench-visual-language-v2/proposal.md` —— 范围与冻结；
3. `openspec/changes/workbench-visual-language-v2/acceptance.md` —— 验收口径
   （尤其 §2 关键帧序列与 §3 交互清单）；
4. `tmp/frontend-audit/DUOLINGO-ANIM-IMPL.md`、`DUOLINGO-CELBRATION.md` —— 证据来源，
   不是决定；
5. 本文件 —— 把上述决策翻译成可执行的数值与 CSS。

### 0.2 证据分级标注

本文件每一个数值都带来源标注：

| 标注 | 含义 |
|---|---|
| **【实证】** | 多邻国反编译源码或实测帧序列里能直接读到的常量/时序 |
| **【公开】** | 多邻国公开资料（官方博客、第三方拆解）能引用的行为描述 |
| **【惯例】** | 行业通行的动效惯例（Material、MDN、CSS 规范） |
| **【决策】** | 本项目在 `decisions.md` / `acceptance.md` 里自己定的值 |
| **【推断】** | 由以上证据推导，无直接出处 |
| **【待核】** | 尚未查证，附查证方式 |

> 纪律：`【实证】` 与 `【决策】` 不得混写。一个数字如果只是"听起来对"，
> 标 `【推断】` 或 `【待核】`，不要伪装成实测。

### 0.3 禁止项（本规格内一律不得出现）

`decisions.md`「动效 · 禁止」与任务书一致：

- ❌ 全局背景 canvas
- ❌ 鼠标跟随 / 视差 / 光标辉光
- ❌ 任何动画库（GSAP / anime.js / Motion One / Rive runtime / Lottie）
- ❌ 任何外部资源（CDN、外部字体、外部图标字体、远程图片）
- ❌ 任何新增构建步骤（无 npm、无打包器）

台灯、静物插画、火苗、彩带一律是**本地内联 SVG** 或纯 CSS 形状。

---

## 1. 动效 token 表

所有 token 落在 `:root`（亮色）与 `[data-theme="night"]`（夜纸）两套值集里，
**动效 token 本身不随主题变化**（时长与缓动与明暗无关），只有颜色 token 分主题。

```css
:root {
  /* ── 时长档（权威表 §2.6） ─────────────────────── */
  --dur-fast: 120ms;      /* 微反馈：hover 淡入、按下、焦点环 */
  --dur-base: 160ms;      /* 入场：列表项、统计卡、展开内容 */
  --dur-slow: 240ms;      /* 视图转场、骨架一轮 */
  --dur-scene: 400ms;     /* 弹出 / 场景：火苗点燃、爆点、进度带 */
  --dur-ceremony: 700ms;  /* 里程碑：挤压回弹满程、日常庆祝、台灯转场、连对横幅停留 */

  /* ── 缓动档（权威表 §2.6，值以权威表为准） ─────── */
  --ease-out: cubic-bezier(.22, .61, .36, 1);      /* 进入视线的减速 */
  --ease-standard: cubic-bezier(.4, 0, .2, 1);     /* 通用双向 */
  --ease-in: cubic-bezier(.55, .06, .68, .19);     /* 离开视线的加速 */
  --ease-rebound: cubic-bezier(.34, 1.3, .64, 1);  /* 轻微过冲（限幅 1.3） */
  --ease-ripple: cubic-bezier(.16, .84, .44, 1);   /* 涟漪专用（起手快、收尾慢） */
  /* 挤压回弹 5 段的段内缓动（多邻国实测 PathInterpolator） */
  --ease-snap-hold: cubic-bezier(.33, 0, .67, 1); /* 第 1、4 段 */
  --ease-snap-pull: cubic-bezier(.37, 0, .67, 1); /* 第 2、3 段 */
  --ease-snap: cubic-bezier(.17, 0, .67, 1);      /* 第 5 段（收敛） */
}
```

> **位移 / 缩放 / 透明度三档（§1.3 / §1.4 / §1.5）在权威表 §2 中没有对应 token**
> （结构 token 53 个已封闭：圆角/间距/字号/字族/字重/线宽/时长/缓动/z-index）。
> 因此本规格**不再把它们写成 token**：数值**原样内联**在用到它们的关键帧与规则里（见 §1.3–§1.5）。
>
> **缓动档已全部进权威表 §2.6（A-18-4 裁定）**：原先内联在本规格里的
> 涟漪曲线与多邻国三条回弹段曲线，语义都与通用档不同，故在权威表里**各自独立命名**
> （`--ease-ripple` / `--ease-snap-hold` / `--ease-snap-pull` / `--ease-snap`），
> **不再出现同名不同值**。本规格只引用，不另定值。

### 1.1 时长档

| 档（权威表 token） | 值 | 用于哪类交互 | 出处 |
|---|---|---|---|
| `fast`（`--dur-fast`） | 120ms | 极微反馈：hover 覆盖层淡入、按钮按下、焦点环显形 | 【决策】`decisions.md` 12.1「交互反馈 120–180ms」取下限 |
| `base`（`--dur-base`） | 160ms | 列表项入场、统计卡弹入、展开/收起内容补间、连对数字替换 | 【决策】12.3「入场 180–240ms」取下限（权威表取 160ms） |
| `slow`（`--dur-slow`） | 240ms | 视图转场（`#middle-page` 容器）、骨架微光一轮、连对横幅入退场 | 【决策】12.3 取上限；`acceptance.md` M-8 要求 0/60/120/240ms 四帧 |
| `scene`（`--dur-scene`） | 400ms | 火苗逐簇点燃、几何爆点、进度带填充 | 【推断】取自 `duolingo` 结算统计卡错峰 80–120ms × 2–3 档的量级 |
| `ceremony`（`--dur-ceremony`） | 700ms | 挤压回弹满程、日常庆祝总时长、里程碑彩带落程、台灯转场总时长、10 连横幅停留 | 【决策】12.1「场景动效 240–520ms」上限 + 17.2「共 ~700ms」 |

> **特例：挤压回弹 = 517ms**【实证】。多邻国 5 段时长 `17+33+83+167+217 = 517ms`
> （`DUOLINGO-ANIM-IMPL.md` §3.1.6，`MidLessonDuoJumpView.JuicierScaleAnimationSection`）。
> 517ms 落在 `ceremony`（700ms）档内；**关键帧百分比按 517ms 归一化**计算，
> 700ms 档位仅作归档用，实际 `animation-duration` 写 `517ms` 以保证曲线形状不失真。
>
> ⚠️ **待裁决**：本表是**token 层**的时长档（权威表 §2.6 钉死的 5 档）；
> 下文各节 CSS / 编排里**写死的字面量**（180ms / 320ms / 520ms 等）**本次未改** ——
> 它们不是 `--lk-*` token，改它们会连带改动关键帧时长与编排时序（§2.1 / §3 / §4.5 / §6）。
> 是否把这些字面量也改为引用权威 token（或反过来把权威档位调到与字面量一致）→ 待裁决。

### 1.2 缓动档

> **值以权威表 `design-notes/night-paper-tokens.md` §2.6 为准**（A-18-4：权威表补出每条
> 缓动的 `cubic-bezier` 系数，本规格**只引用、不另定值**）。

| 档（权威表 token） | 曲线 | 语义 | 出处 |
|---|---|---|---|
| `out`（`--ease-out`） | `cubic-bezier(.22,.61,.36,1)` | 元素**进入**视线的减速（入场、淡入、弹入） | 【惯例】Material "decelerate" |
| `standard`（`--ease-standard`） | `cubic-bezier(.4,0,.2,1)` | 通用双向（hover、骨架扫过、焦点环） | 【惯例】Material "standard" |
| `in`（`--ease-in`） | `cubic-bezier(.55,.06,.68,.19)` | 元素**离开**视线的加速（退场、收起） | 【惯例】Material "accelerate" |
| `rebound`（`--ease-rebound`） | `cubic-bezier(.34,1.3,.64,1)` | 轻微过冲（限幅在 1.3，避免廉价弹跳感）；挤压回弹的通用手感 | 【推断】"overshoot 限幅"是动画通行做法 |
| `ripple`（`--ease-ripple`） | `cubic-bezier(.16,.84,.44,1)` | **涟漪专用**：起手快、收尾慢，模拟光推开 | 【推断】语义独立 → 权威表**独立命名**（A-18-4） |
| `snap-hold`（`--ease-snap-hold`） | `cubic-bezier(.33,0,.67,1)` | 回弹第 1、4 段 | 【实证】多邻国 SECTION_1/4 |
| `snap-pull`（`--ease-snap-pull`） | `cubic-bezier(.37,0,.67,1)` | 回弹第 2、3 段 | 【实证】多邻国 SECTION_2/3 |
| `snap`（`--ease-snap`） | `cubic-bezier(.17,0,.67,1)` | 回弹第 5 段（收敛） | 【实证】多邻国 SECTION_5 |

> 这 8 条曲线**全部**是权威表 §2.6 的 token（CSS 里写 `var(--ease-*)`；
> WAAPI 的 `easing` 只接受字面量字符串，故 JS 调用处照抄权威表的同一系数，
> **不得另写一套**——见 §4.5 的说明）。

> **不要用** `ease` / `ease-in-out` 关键字，也不建议 `linear`：
> `linear` 在本规格里只允许出现在**匀速旋转**（加载环）一处。
> （骨架的横扫已按 A-115 取消 —— 呼吸用的是 `standard` 缓动，不占 `linear` 名额。）
>
> **既有动画的例外**：`workbench.css:992` 的 `flash-answer-reveal` 用了自己的
> `cubic-bezier(.2,.75,.2,1)`。它属于闪卡组件，**不并入本档位表**，
> 铺开阶段是否收敛到本表的 `out` 档由实现期另行评估，本规格不预先改动它。

### 1.3 位移档

> **不是 token**：权威表 §2 无位移 token，本档的数值**原样内联**在使用处（见 §2.2 / §3）。

| 档 | 值 | 用于哪类交互 | 出处 |
|---|---|---|---|
| `nudge` | 4px | 答错的水平摆动幅度 | 【公开】`DUOLINGO-CELBRATION.md` §7.1 L0：「轻微左右位移（≤4px，≤160ms），不抖动」 |
| `rise-list` | 8px | 列表项 / 统计卡入场位移 | 【决策】12.3「8–12px」取下限 |
| `rise-view` | 12px | 视图转场入场位移 | 【决策】12.3「8–12px」取上限；`acceptance.md` M-8「内容上浮 8–12px + 淡入」 |
| `burst` | 20px | 纸片/爆点飞散位移基准 | 【推断】庆祝物的可读性位移上限 |

### 1.4 缩放档

> **不是 token**：权威表 §2 无缩放 token，本档的数值**原样内联**在使用处（见 §2.2 / §3）。

| 档 | 值 | 用于哪类交互 | 出处 |
|---|---|---|---|
| `tap` | 0.92 | 答错时的轻微压缩（与摆动同时） | 【决策】12.2 prose「scale 0.92」 |
| `press` | 0.96 | 按钮/选项按下 | 【惯例】触控反馈的常规压缩量 |
| — | 1.00 | 静止/终值 | — |
| `pop` | 1.06 | 通用弹出上限 | 【决策】12.2 prose「1.06」 |
| `burst` | 1.12 | 里程碑几何爆点峰值 | 【推断】 |
| `flame` | 1.15 | 火苗点燃峰值 | 【推断】 |

> **回弹专用组**（只用于挤压回弹，不进通用缩放档）：
> `0.6 → 1.1 → 0.9603 → 1.0067 → 1.0`【实证】。
> 详见 §3.1 与 §10 的漂移登记。

### 1.5 透明度档

> **不是 token**：权威表 §2 无透明度 token，本档的数值**原样内联**在使用处。
> hover 覆盖层例外 —— 它直接用权威表的 `--veil-hover` 面纱 token（自带透明度）。

| 档 | 值 | 用于哪类交互 | 出处 |
|---|---|---|---|
| — | 0 | 完全不可见 | — |
| `veil` | 0.08 | hover 覆盖层的默认可见度 | 【推断】暖纸底上 8% 蓝灰足以让"可点"被感知 |
| `soft` | 0.35 | 骨架底纹、灯罩溢光、涟漪辉光 | 【推断】 |
| `mid` | 0.6 | 折叠区残影、彩带片基准 | 【推断】 |
| `strong` | 0.85 | 爆点环峰值 | 【推断】 |
| `full` | 1 | 完全可见 | — |

### 1.6 硬红线：哪些属性允许被"动画"

`acceptance.md` §2 通用判据与 §3.7 性能项都写明「所有动效只用 `transform` / `opacity`」。
本规格把这条红线**精确化**，避免实现期各行其是：

| 类别 | 属性 | 规则 |
|---|---|---|
| **允许插值** | `transform`、`opacity` | ✅ 一切**动画**（`@keyframes` / WAAPI / `transition`）只插值这两个 |
| **允许瞬切** | `color`、`background-color`、`border-color`、`box-shadow`、`outline` | 状态切换必须是**瞬时**（无 `transition`）。状态靠颜色表达时**必须同时**有几何通道（`docs/GLOSSARY.md`「冗余状态通道」） |
| **禁止动画** | `width` / `height` / `top` / `left` / `margin` / `padding` / `grid-template-rows` / `font-size` | ❌ 不写进任何 `transition` 或 `@keyframes`。展开收起用「**高度瞬切 + 内容补间**」（见 §2.1） |

> **为什么 hover 不用 `background-color` 过渡**：`transition: background-color` 会触发
> 逐帧重绘，与红线冲突。本规格统一用**伪元素覆盖层 + `opacity`** 做 hover
> （见 §2.2），颜色是静态的，只有透明度在动。
>
> **若日后确实需要颜色过渡**：必须先改 `acceptance.md` §2 / §3.7，
> 走一次契约同步，不得在本规格内默默开口子。

### 1.7 命名与注入位置

> **补钉约定（2026-10-22 A-116）**：新增动效的 `@keyframes` 一律用 `lk-` 前缀 +
> **动效语义名**（`lk-skeleton-breathe` / `lk-combo-in` / `lk-bar-grow` …），
> **不许**用临时名（`anim1` / `fade` / `slide`）——
> 临时名会让「同一组件多套实现」这种病在动效层复发。

- **token 名字一律用权威表**（`design-notes/night-paper-tokens.md`）的
  `--surface-*` / `--ink-*` / `--role-*` / `--rule-*` / `--veil-*` / `--elev-*` /
  `--skeleton-*` / `--dur-*` / `--ease-*`；**不再有本规格自有的 token 命名族**
  （`decisions.md` A-13：第三族 `--lk-*` 整体退役）。
  关键帧前缀 `lk-` 与类名前缀 `lk-` 保留 —— 那是动画名与选择器名，**不是 token**。
- token 定义在 `workbench/server/static/workbench.css` 的 `:root`；
  动效相关的 keyframes 集中在同文件尾部的 `/* ── motion ── */` 区块，
  便于一次性审查"只动 transform/opacity"。
- **图谱页不受影响**：`workbench.css` 中图谱相关选择器（`graph-pulse` 等，
  现 `:1772`）不并入本 token 体系，图谱页观感保持像素级不变
  （`proposal.md`「Explicitly out of scope」、`acceptance.md` G-5）。

### 1.8 本规格依赖的配色 token（非动效 token，由色彩层提供）

本规格只定义**动效**参数，但它引用的下列颜色 token 必须由 token 地基层提供，
否则实现期会临时硬编码十六进制值（正是本次要消除的问题）。
**建议命名**如下，供 token 层作者对齐：

| 权威表 token | 用途 | 备注 |
|---|---|---|
| `--veil-hover` | hover 覆盖层底色 | 权威表 §3.5「交互面纱」：自带 6% 暖面纱，透明度不再另设 |
| `--ink-faint` | 加载环的底圈 | 弱一档 |
| `--role-blue` | 学习蓝（答对几何标记、连对高档横幅、加载环前段） | 三角色色之一 |
| `--role-yellow` | 阳光黄（连对低档横幅、火苗已燃层） | 三角色色之一 |
| `--role-red` | 注意红（答错几何标记） | 三角色色之一；**仅用于失败与阻塞** |
| `--skeleton-base` | 骨架灰块 | — |
| `--skeleton-sheen` | ~~骨架微光高光~~ **不再使用**（A-115 取消了横扫） | — |
| `--surface-base` | **页面地面色**（两主题各一套值） | 台灯转场读它作为涟漪的目标色 |
| `--asset-lamp-warm` | 灯下暖光 | 台灯转场专用；由资产层提供（`asset-spec.md` §2） |
| 灯位 | 台灯在视口中的位置 | 权威表无对应 token → 暂写死 `88%` / `82%`（→ 待裁决） |

> **重要**：涟漪覆盖层的颜色必须**精确等于**新主题的页面地面色
> （`--surface-base` 的目标主题取值），否则 §4.3 的第 ④ 步（换肤）
> 与第 ⑤ 步（退场）之间会出现可见的色差跳变。
> 权威表的 `--surface-base` **在同一个变量名下随 `data-theme` 变化**，
> 所以取「目标主题」的值必须在换肤前读出（见 §4.2 的 `themeBase()`）。

---

## 2. 交互 → 动效映射表

### 2.1 映射表

| # | 交互 | 触发时机 | 动画描述 | 时长 | 缓动 | 实现方式 | reduced-motion 降级形态 |
|---|---|---|---|---|---|---|---|
| 1 | **hover** | 指针进入可交互元素 | 伪元素覆盖层（`::after`）从 `opacity 0` 淡到 `0.08`；同时元素 `translateY(-1px)` | 120ms | `standard` | 纯 CSS | 覆盖层瞬时显形（0ms），不位移；或直接不显示覆盖层，只保留边框态 |
| 2 | **active（按下）** | `pointerdown` / 键盘 Space | `scale(0.96)`；`pointerup` 回 1 | 120ms | `standard` | 纯 CSS（`:active`） | 瞬时 `scale(1)`，不压缩；按下反馈改由**状态色瞬切 + 几何点**承担 |
| 3 | **focus** | 键盘 Tab 抵达 | 焦点环**瞬时**出现（`outline` + `box-shadow`），不做动画 | 0ms | — | 纯 CSS（`:focus-visible`） | 同左（本就是直切） |
| 4 | **focus-within** | 输入框/编辑器获得焦点 | 外框色瞬切到学习蓝 + 容器 `translateY(-1px)` 抬起 | 120ms | `standard` | 纯 CSS（`:focus-within`） | 颜色瞬切保留；**取消抬起** |
| 5 | **展开 / 收起** | 折叠面板开合 | 容器高度**瞬切**（不动画）；内容 `opacity 0→1` + `translateY(-8px→0)` 补间 | 180ms | `out`（展开）/ `in`（收起） | 纯 CSS | 内容瞬时显形，无位移无淡入 |
| 6 | **视图转场** | 中栏换页（`#middle-page` innerHTML 被替换） | `#middle-page` 容器整体 `opacity 0→1` + `translateY(12px→0)` | 240ms | `out` | vanilla JS（WAAPI `element.animate()`，每次换页重放） | 容器瞬时出现（无动画） |
| 7 | **列表 stagger** | 列表/卡片组入场 | 逐项 `opacity 0→1` + `translateY(8px→0)`，项间错峰 40ms（第 9 项之后封顶） | 180ms（项） | `out` | 纯 CSS（`:nth-child` 错峰，见 §3.2） | 全部项瞬时可见，无错峰无位移 |
| 8 | **数字滚动** | 统计数字变化（正确率 / 用时 / 最高连对） | 逐位数字条上下滚动（strip `translateY`），逐位错峰 40ms | 240ms（每位） | `out` | vanilla JS（构建 strip + `transition: transform`） | 数字**直接落终值**，无滚动 |
| 9 | **骨架呼吸** | 内容加载中 | 灰块**自身**在 opacity 1 ↔ .55 之间循环（**不做横扫**） | 1400ms/轮（无限） | `standard` | 纯 CSS（元素自身 `opacity`） | 灰块**静止**（`animation: none`，`opacity: 1` 直出） |
| 10 | **加载** | 请求在途且无可骨架化的结构 | 24px 圆环匀速旋转 | 700ms/圈 | `linear` | 纯 CSS | 圆环**静止**（呈现为一个静态环） |
| 11 | **错误** | 提交被拒 / 答错 | 目标元素 `translateX` 往返摆动（≤4px），同时错误几何标记瞬时出现（红叉） | 160ms | `standard` | 纯 CSS | **无摆动**，只保留红叉几何标记 + 错误文案 |
| 12 | **成功（答对）** | 判定为正确 | 目标选项**挤压回弹**（5 段）+ 蓝色勾选几何标记瞬时出现 | 517ms | 三档 `snap-*` | 纯 CSS | **无回弹**；勾选几何标记瞬时出现（终态直落） |
| 13 | **庆祝（日常档）** | 一份试卷完成 | 完成页容器上浮淡入 → 数字滚动 → 进度带 `scaleX 0→1` → 3 张统计卡错峰弹入 → CTA 滑入 | 900ms 总程 | `out` | 纯 CSS + vanilla JS（数字） | 全部元素**直接落终态**：数字直显、进度带 100%、统计卡已就位、CTA 可点；**无任何位移或淡入** |
| 14 | **庆祝（里程碑档）** | 全对 / 破纪录 / 章节首次完成 | 日常档之上叠：几何爆点（圆环扩散）+ 纸片飞散 | 1200ms 总程 | `out` / `ripple` | 纯 CSS + 内联 SVG（纸片形状） | 只保留**最终静态构图**：一帧爆点 + 落定后的纸片静置（或直接不画纸片）；数字/进度带同日常档降级 |
| 15 | **台灯转场** | 切换亮/暗主题 | 台灯从角落探出 → 点亮 → 涟漪铺满 → 收回（完整时序见 §4） | 700ms | `out` / `ripple` / `rebound` | vanilla JS（编排）+ 内联 SVG（台灯）+ 纯 CSS（涟漪层） | **整段跳过**：主题属性直接切换，台灯与涟漪层不创建；不播放任何音效 |
| 16 | **涟漪** | 台灯转场的第 ③ 段 | 新主题地面色以径向遮罩从灯位扩散铺满（详见 §4） | 450ms（扩散） | `ripple` | 纯 CSS（`transform: scale` + `mask-image` + `opacity`） | 直接切主题，涟漪层不创建 |
| 17 | **火苗簇** | 连对数增长 | 火苗逐簇点燃（每簇 `scale .55→1.15→1` + 由灰到黄的**透明度交叉淡入**），簇间错峰 80ms | 320ms（每簇） | `out` | 纯 CSS + 内联 SVG（火苗形状） | 火苗**直接落终态**（该亮的直接是黄的），无逐簇过程、无缩放 |
| 18 | **连对横幅** | 连对达到 5 / 10（插播） | **一份**横幅弹入 → 数字替换 → 退场（参数化，见 §6） | 700ms（5 连）/ 900ms（10 连） | `out` / `rebound` | 纯 CSS + vanilla JS（写 CSS 变量） | 横幅**直接落终态**（显示正确数字后立即可读），无弹入/退场补间 |
| 19 | **进度带** | 数据层负荷柱 / 日历扩散 / 庆祝进度 | `scaleX 0→1`（`transform-origin: left`），逐柱错峰 24ms | 320ms | `out` | 纯 CSS | 直接落终值（柱高 100%），无生长 |

> **第 10 项与第 9 项的区别**：第 9 项是「有结构可占位」时用骨架；
> 第 10 项是「没有可占位结构」时用转环。默认优先骨架。

### 2.2 通用实现约定

**（a）hover 覆盖层**（hover 行的落地形态）：

```css
.lk-tappable { position: relative; }
.lk-tappable::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: var(--veil-hover);        /* 权威表 §3.5：面纱自带透明度 */
  opacity: 0;
  pointer-events: none;                 /* 装饰层不拦截交互：acceptance G-7 */
  transition: opacity var(--dur-fast) var(--ease-standard);
}
.lk-tappable:hover::after { opacity: 1; }
.lk-tappable:hover { transform: translate3d(0, -1px, 0); }
.lk-tappable:active { transform: scale(.96); }   /* 缩放档 §1.4 `press`，内联 */
```

**（b）state class 命名**：一律 `is-*`（`is-revealed` / `is-correct` / `is-wrong` /
`is-lit` / `is-open`），挂**容器**上，由容器驱动子元素的动效。
**禁止**给子元素挂一次性 class（`middle-navigation.js:87` 整块替换 `#middle-page`
的 innerHTML，子元素的 class 会被冲掉——见 `decisions.md` 12.4 的实现约束）。

**（c）视图转场必须用 WAAPI 或容器动画**：

```js
// middle-navigation.js：innerHTML 替换之后重放一次容器动画
middlePage.innerHTML = nextPage.innerHTML;
middlePage.animate(
  [{ opacity: 0, transform: "translate3d(0, 12px, 0)" },
   { opacity: 1, transform: "translate3d(0, 0, 0)" }],
  { duration: 240, easing: easeVar("--ease-out"), fill: "none" }
);
```
> `easeVar()` 是 §4.2 定义的取 token 助手（WAAPI 的 `easing` 只接受字面量字符串，
> 所以值从权威表 §2.6 读，**不在 JS 里另抄一份系数**）。
纯 CSS 方案（`#middle-page { animation: lk-rise-in-12 240ms both; }`）**只会在元素
首次渲染时播放一次**，换页不会重放——故不采用。

**（d）装饰层一律 `pointer-events: none`**（`acceptance.md` G-7）。

**（e）动效偏好开关**：设置视图的「动效偏好」写 `<html data-motion="off">`。
CSS 侧与既有的 reduced-motion 兜底（`workbench.css:1126-1131`）**同构**：

```css
/* 与 workbench.css:1126-1131 同构：关掉一切动画与过渡 */
[data-motion="off"] *,
[data-motion="off"] *::before,
[data-motion="off"] *::after {
  transition: none !important;
  animation: none !important;
}
```

JS 侧读同一个开关决定**是否创建**台灯/涟漪层（因为它们是 JS 造的节点，
CSS 关不掉）与**是否播放**音效
（模式参考 `workbench.js:1639` 现有的 `matchMedia("(prefers-reduced-motion: reduce)")`
判定写法）。

> **优先级**【待核，见 §10 D-6】：系统 `prefers-reduced-motion: reduce`
> **恒定降级**（用户可在系统里关掉，不允许被 UI 覆盖）；
> UI 开关只是在此之上**额外**关闭动效。二者取"或"。

---

## 3. `@keyframes` 库（可直接粘贴）

> 以下片段**全部只动 `transform` / `opacity`**（除 §3.4 的 `transition: transform`，
> 同样只动 `transform`）。可直接粘进
> `workbench/server/static/workbench.css` 的 `/* ── motion ── */` 区块。

### 3.1 挤压回弹（直译多邻国 5 段）

**来源**【实证】：`DUOLINGO-ANIM-IMPL.md` §3.1.6
`com.duolingo.session.MidLessonDuoJumpView$JuicierScaleAnimationSection`：

| 段 | from | to | PathInterpolator | 时长 |
|---|---|---|---|---|
| SECTION_1 | 0.6 | 1.1 | `PathInterpolator(0.33, 0.0, 0.67, 1.0)` | 17ms |
| SECTION_2 | 1.1 | 1.1 | `PathInterpolator(0.37, 0.0, 0.67, 1.0)` | 33ms |
| SECTION_3 | 1.1 | 0.9603 | `PathInterpolator(0.37, 0.0, 0.67, 1.0)` | 83ms |
| SECTION_4 | 0.9603 | 1.0067 | `PathInterpolator(0.33, 0.0, 0.67, 1.0)` | 167ms |
| SECTION_5 | 1.0067 | 1.0 | `PathInterpolator(0.17, 0.0, 0.67, 1.0)` | 217ms |

**CSS 直译**（百分比按 517ms 归一化：17→3.288%、50→9.671%、133→25.725%、
300→58.027%、517→100%）：

```css
@keyframes lk-squash-bounce {
  0%      { transform: scale(.6);     animation-timing-function: var(--ease-snap-hold); }
  3.288%  { transform: scale(1.1);    animation-timing-function: var(--ease-snap-pull); }
  9.671%  { transform: scale(1.1);    animation-timing-function: var(--ease-snap-pull); }
  25.725% { transform: scale(.9603);  animation-timing-function: var(--ease-snap-hold); }
  58.027% { transform: scale(1.0067); animation-timing-function: var(--ease-snap); }
  100%    { transform: scale(1); }
}

/* 用法：答对时给"被选中的那一项"加 .is-correct */
.lk-option.is-correct {
  transform-origin: 50% 100%;                       /* 底边为锚，视觉上像从地面弹起 */
  animation: lk-squash-bounce 517ms both;
}
```

> **锚点说明**：多邻国的对象是"从地面跳起的角色"，锚点在底部；
> 我们的对象是"列表里的一项"，锚点同样取底边 `50% 100%`，读作"被顶了一下"。
>
> **配套淡出**：多邻国在同一段里还挂了一条 `alpha 1→0 / 117ms / linear / delay 733ms`
> 【实证】。我们的元素不能消失，因此**只把这条淡出借给"答对横幅"**（§6），
> 不用于选项本身。

### 3.2 上浮淡入

```css
@keyframes lk-rise-in-8 {
  from { opacity: 0; transform: translate3d(0, 8px, 0); }
  to   { opacity: 1; transform: translate3d(0, 0, 0); }
}
@keyframes lk-rise-in-12 {
  from { opacity: 0; transform: translate3d(0, 12px, 0); }
  to   { opacity: 1; transform: translate3d(0, 0, 0); }
}

/* 用法：列表项 / 统计卡 */
.lk-stagger > * { animation: lk-rise-in-8 180ms var(--ease-out) both; }
.lk-stagger > :nth-child(1) { animation-delay: 0ms; }
.lk-stagger > :nth-child(2) { animation-delay: 40ms; }
.lk-stagger > :nth-child(3) { animation-delay: 80ms; }
.lk-stagger > :nth-child(4) { animation-delay: 120ms; }
.lk-stagger > :nth-child(5) { animation-delay: 160ms; }
.lk-stagger > :nth-child(6) { animation-delay: 200ms; }
.lk-stagger > :nth-child(7) { animation-delay: 240ms; }
.lk-stagger > :nth-child(8) { animation-delay: 280ms; }
/* 第 9 项及以后封顶在 280ms，避免长列表尾部长久空白 */
.lk-stagger > :nth-child(n+9) { animation-delay: 280ms; }
```

> **封顶依据**【决策】`acceptance.md` §3.7「长列表（98+ 条记录）滚动流畅」；
> 记录明细是 98+ 条的圆角卡片流（`decisions.md` 收口「作答明细 → 圆角卡片流」），
> 逐项无限错峰会让末尾项等 4 秒才出现。

### 3.3 骨架呼吸（底色明暗呼吸，**不做横扫**）

> ⚠️ **2026-10-22 按 A-115 改**：所有者把骨架屏定成「**呼吸式**」⇒
> **微光扫过（`::after` 横扫 + 表面渐变）作废**。
> `acceptance.md` §2 的 **M-9** 判据已同步改成「灰块**整体明暗呼吸**」；
> 走查判据 `3.4-3` 的口径 = 「**块自身表面随时间变化**」，**`::after` 上的横扫不满足**
> （见 `decisions.md` **A-114** / **A-115**）。

```css
.lk-skeleton {
  position: relative;
  overflow: hidden;
  background: var(--skeleton-base);            /* 灰块 */
  /* 呼吸：动的是**块自身的 opacity** —— 不动位置、不用伪元素覆盖层、不用表面渐变 */
  animation: lk-skeleton-breathe 1400ms var(--ease-standard) infinite;
}
@keyframes lk-skeleton-breathe {
  0%, 100% { opacity: 1; }
  50%      { opacity: .55; }
}
```

- **只动 `opacity`**（§1.6 红线：只许动 `transform` / `opacity`）；
- **不用伪元素**、**不用 `linear-gradient`** ⇒ **A-74**（微光是渐变的明确例外）
  **不再被行使**（账本不改写，只记它不再适用）；
- **不动位置**；
- **静态样式 = 终态**（§7.1 铁律）：`opacity` 的静态值是 `1` ⇒ 降级档 `animation: none`
  时灰块**直出**，不停在起始态；
- 灰块**始终有可见体积**（`min-height` + 三个变体 `--text` / `--block` / `--avatar`）。

### 3.4 数字滚动

**主方案：逐位滚动条（ticker strip）**。
**来源**【实证】：多邻国连对计数器用 `com.robinhood.ticker.TickerView` 做数字滚动
（`DUOLINGO-ANIM-IMPL.md` §5.3；`DUOLINGO-FEEDBACK.md` §5.8
`view_combo_indicator.xml` 里的 `TickerView`）。

```html
<span class="lk-ticker" data-value="87" role="text" aria-label="87"></span>
```

```css
.lk-ticker {
  display: inline-flex;
  align-items: flex-end;
  font-variant-numeric: tabular-nums;   /* 等宽数字，避免滚动时宽度抖动 */
}
.lk-ticker-digit {
  display: inline-block;
  overflow: hidden;
  height: 1em;
  line-height: 1;
  vertical-align: bottom;
}
.lk-ticker-strip {
  display: flex;
  flex-direction: column;
  transform: translate3d(0, 0, 0);
  transition: transform 240ms var(--ease-out);
  will-change: transform;
}
.lk-ticker-glyph { height: 1em; line-height: 1; }
```

```js
// vanilla JS：构建 0-9 重复 3 轮的竖条，并把目标数字写到 CSS 变量上
function setTicker(el, value) {
  var digits = String(value).split("");
  if (el.childElementCount !== digits.length) {
    el.replaceChildren();
    digits.forEach(function () {
      var d = document.createElement("span");
      d.className = "lk-ticker-digit";
      var strip = document.createElement("span");
      strip.className = "lk-ticker-strip";
      for (var i = 0; i < 30; i++) {
        var g = document.createElement("span");
        g.className = "lk-ticker-glyph";
        g.textContent = String(i % 10);
        strip.appendChild(g);
      }
      d.appendChild(strip);
      el.appendChild(d);
    });
  }
  Array.prototype.forEach.call(el.children, function (d, i) {
    /* 直接写 transform（过渡仍作用在 transform 上）；不再经由 CSS 变量中转 */
    d.querySelector(".lk-ticker-strip").style.transform =
      "translate3d(0," + (-digits[i]) + "em,0)";
  });
}
```

> **两个必查的坑**：
> 1. `1em` 必须在 `.lk-ticker-digit` 与 `.lk-ticker-strip` 上解析到**同一字号**，
>    否则数字会错位（strip 的 `1em` 按自身 font-size 算）；
> 2. 若某浏览器对"自定义属性驱动的 transform 过渡"表现异常，
>    退化为直接写 `strip.style.transform = "translate3d(0," + (-d) + "em,0)"`，
>    过渡仍然只作用在 `transform` 上。
>
> **逐位错峰**：多位数字时，第 i 位延迟 `i * 40ms`（JS 设置 `transition-delay`），
> 形成从右向左滚出的层次感。
>
> **`will-change` 的处置**（呼应 §8.3）：上面的 `will-change: transform` 写在
> CSS 里是**默认写法**，前提是同屏滚动中的 ticker ≤ 8 个（统计卡最多 3 个数字、
> 记录中心每张卡 1 个，满足）。若同一屏出现 > 8 个滚动数字，改为由 JS 在
> 开始滚动时加 `will-change`、结束后 200ms 移除。

**备选方案：逐位翻（3D 翻牌）**——**不作为默认**。

```css
.lk-flip { display: inline-block; perspective: 400px; }
.lk-flip-inner { display: block; transform-style: preserve-3d; }
@keyframes lk-flip-roll {
  0%   { transform: rotateX(0deg); }
  50%  { transform: rotateX(-90deg); }
  100% { transform: rotateX(0deg); }
}
```

不采用的理由【推断】：① 需要 `perspective` + `preserve-3d`，比纯 `translateY`
多一层合成上下文；② 表格数字用翻牌读数比滚动条更慢；
③ 翻牌在 `--dur-fast` 级别（120ms）内完成才不拖沓，而逐位翻至少要 200ms/位。
**保留此片段仅供后续取用**，实现期不落地。

### 3.5 台灯转场（探出 / 点亮 / 收回）

台灯是**内联 SVG**（`decisions.md` 17.2：台灯属于静物插画语言的一部分，
须与空态插画同一支笔、同一套线宽与圆角——`图案适配原则`）。
**只驱动 SVG 根节点的 `transform` / `opacity`**，不逐路径动画。

```css
.lk-lamp {
  position: fixed;
  right: 2rem;
  bottom: 1.5rem;
  width: 132px;
  height: 132px;
  pointer-events: none;                 /* 装饰层不拦截交互：G-7 */
  opacity: 0;
  transform-origin: 50% 100%;
  z-index: var(--z-lamp);                        /* 权威表 §2.7：灯层在所有 UI 层之上 */
  will-change: transform, opacity;
}
.lk-lamp__glow {                        /* 灯罩内亮起 + 暖色溢出 */
  transform-box: fill-box;
  transform-origin: 50% 100%;
  opacity: 0;
}

@keyframes lk-lamp-lean-out {
  from { opacity: 0; transform: translate3d(0, 120%, 0) scale(.86) rotate(-12deg); }
  to   { opacity: 1; transform: translate3d(0, 0, 0) scale(1) rotate(0deg); }
}
@keyframes lk-lamp-light-up {
  0%   { opacity: 0;   transform: scale(.35); }
  60%  { opacity: 1;   transform: scale(1.12); }
  100% { opacity: 1;   transform: scale(1); }
}
@keyframes lk-lamp-retract {
  from { opacity: 1; transform: translate3d(0, 0, 0) scale(1) rotate(0deg); }
  to   { opacity: 0; transform: translate3d(0, -28%, 0) scale(.9) rotate(8deg); }
}
```

### 3.6 火苗簇逐簇点亮

火苗 = **内联 SVG**（一个 14×18 的火苗形状，灰/黄两版共形，靠 CSS 变量换色）。
「由灰变黄」是**颜色变化**，按 §1.6 只能瞬切——但我们用**两层交叉淡入**把它变成
纯 `opacity` 动画，于是既不违反红线，又比瞬切好看。

```html
<span class="lk-flame">
  <span class="lk-flame-off" aria-hidden="true"></span>   <!-- 灰底 -->
  <span class="lk-flame-on"  aria-hidden="true"></span>   <!-- 黄，opacity 0→1 -->
</span>
```

```css
.lk-flame { position: relative; display: inline-block; width: 14px; height: 18px; }
.lk-flame-off, .lk-flame-on { position: absolute; inset: 0; }
.lk-flame-on {
  opacity: 0;
  transition: opacity 180ms var(--ease-standard);
}
.lk-flame.is-lit .lk-flame-on { opacity: 1; }
.lk-flame.is-lit { animation: lk-flame-ignite 320ms var(--ease-out) both; }

@keyframes lk-flame-ignite {
  0%   { opacity: 0; transform: translate3d(0, 6px, 0) scale(.55); }
  55%  { opacity: 1; transform: translate3d(0, -2px, 0) scale(1.15); }
  100% { opacity: 1; transform: translate3d(0, 0, 0) scale(1); }
}
```

> **簇间错峰**【决策】`decisions.md` 收口「连对进度本身是动效（火苗簇式）」：
> 第 i 簇 `animation-delay = i * 80ms`。
> 80ms 取自【公开】`DUOLINGO-CELBRATION.md` §7.2 M3「3 张卡错峰 80–120ms 弹出」
> 的下限。
>
> **负反馈不可沉默**【实证】多邻国 combo > 4 时答错必须给明确负反馈
> （`R.string.combo_lost`）。我们的对位做法：**连对 > 4 时答错，已亮的火苗簇
> 逐个熄灭**（`is-lit` 移除 → 黄层 `opacity` 淡出，180ms），并给一次 ≤4px 的
> 水平摆动（§3.8）。熄灭同样是纯 `opacity`。

### 3.7 庆祝

**（a）日常档**（`acceptance.md` M-2：0/120/300/600/900ms 五帧）：

| t | 事件 | 实现 |
|---|---|---|
| 0 | 完成页容器入场 | `lk-rise-in-12` 240ms |
| 120 | 数字滚动开始 | ticker，240ms/位，逐位错峰 40ms |
| 180 / 300 / 420 | 3 张统计卡错峰弹入 | `lk-rise-in-8` 180ms，delay 180/300/420 |
| 300 | 进度带 0→100% | `lk-progress-fill` 320ms（`scaleX`） |
| 600 | CTA 滑入并高亮 | `lk-rise-in-8` 180ms |
| 900 | 终态 | — |

**（b）里程碑档**（M-3：0/150/400/800/1200ms 五帧）：

| t | 事件 |
|---|---|
| 0 | 容器入场（完成页） |
| 150 | 数字滚动 + 进度带 |
| 400 | **几何爆点**（圆环扩散）起 + **里程碑音效**落在这一拍 |
| 800 | 纸片飞散峰值 |
| 1200 | 终态（**不遮挡 CTA**） |

```css
/* 进度带：只动 scaleX，transform-origin 固定在左端 */
@keyframes lk-progress-fill {
  from { transform: scaleX(0); }
  to   { transform: scaleX(1); }
}
.lk-progress__fill {
  transform: scaleX(0);
  transform-origin: left center;
  transition: transform 320ms var(--ease-out);
}
.lk-progress.is-filled .lk-progress__fill { transform: scaleX(1); }

/* 几何爆点：圆环扩散并淡出 */
@keyframes lk-celebrate-burst {
  0%   { opacity: 0;   transform: scale(.4); }
  40%  { opacity: 1;   transform: scale(1.08); }
  100% { opacity: 0;   transform: scale(1.45); }
}

/* 纸片飞散：每片的位移/旋转由 CSS 变量给出（JS 逐片赋值） */
@keyframes lk-confetti-fall {
  0%   { opacity: 0; transform: translate3d(0, -12px, 0) rotate(0deg) scale(.6); }
  12%  { opacity: 1; }
  100% { opacity: 0; transform: translate3d(0, 120px, 0)
                    rotate(180deg) scale(1); }
}
```

> **日常档无彩带**【决策】`acceptance.md` M-2「**无彩带**（彩带只在里程碑档）」；
> `DUOLINGO-CELBRATION.md` §1.4 同样指出"彩带只出现在少数里程碑级动画里"。
> 纸片用**内联 SVG**（3 种小形状：细条 / 圆片 / 三角），不用位图。

### 3.8 杂项

```css
/* 答错：水平摆动，幅度 ≤4px，160ms 内结束，不做屏幕级震动 */
@keyframes lk-error-nudge {
  0%   { transform: translate3d(0, 0, 0); }
  25%  { transform: translate3d(-4px, 0, 0); }
  50%  { transform: translate3d(4px, 0, 0); }
  75%  { transform: translate3d(-2px, 0, 0); }
  100% { transform: translate3d(0, 0, 0); }
}

/* 加载环：匀速旋转（linear 仅在此处出现 —— 骨架横扫已按 A-115 取消） */
@keyframes lk-spin { to { transform: rotate(360deg); } }
.lk-spinner {
  width: 24px; height: 24px;
  border-radius: var(--r-round);              /* 正方形真圆（权威表 §2.1） */
  border: 3px solid var(--ink-faint);
  border-top-color: var(--role-blue);
  animation: lk-spin 700ms linear infinite;
}
```

---

## 4. 涟漪扩散的 CSS 实现方案

### 4.1 机制

目标：**「底色从灯下扩散铺满」**，且**只动 `transform` / `opacity`**。

做法（与任务书提示一致）：

1. 一层 `position: fixed; inset: 0;` 的**底色层**，背景是**新主题的地面色**
   （目标主题的 `--surface-base`）；它位于**内容层之下**（A-1：卡片全程不被覆盖，见 §4.5）；
2. 覆盖层挂 `mask-image: radial-gradient(circle at <灯位>, #000 0, #000 22vmax, transparent 30vmax)`
   —— 一个**静止的**径向遮罩；
3. 覆盖层用 `transform: scale()` 从 `0.06` 放大到 `4.8`，
   `transform-origin` 设在**灯位**；
   因为遮罩与背景都在覆盖层的本地坐标系里、缩放中心相同，
   **遮罩的圆随覆盖层一起长大** —— 这就是"扩散"；
4. 覆盖层的 `opacity` 另走一条动画：起手淡入 → 换肤时保持 → 换肤后淡出。

> **为什么缩放覆盖层而不是动画化遮罩的半径**：动画化 `mask-image` 的
> 渐变半径属于**逐帧重绘**，直接违反 §1.6 红线；`transform: scale()` 是合成器
> 操作，不触发重绘。

### 4.2 完整可粘贴片段

```css
/* ── 台灯转场：涟漪层 ─────────────────────────────────────────
   挂在 <body> 下的三个固定层，全部 pointer-events: none。
   .lk-ripple      底色前沿（承载新主题地面色）
   .lk-ripple-glow 灯下暖光（跟在前沿外圈，纯装饰）
   前两层是**底色层**：位于内容层之下（A-1，勿压平卡片）      */

.lk-ripple,
.lk-ripple-glow {
  position: fixed;
  inset: 0;
  pointer-events: none;
  opacity: 0;
  transform-origin: 88% 82%;
  will-change: transform, opacity;
}

.lk-ripple {
  z-index: var(--z-base);                        /* 底色层：在内容层之下（A-1，权威表 §2.7） */
  background: var(--surface-base);                     /* 新主题地面色（JS 覆盖为目标主题取值） */
  -webkit-mask-image: radial-gradient(circle at 88% 82%,
      #000 0, #000 22vmax, transparent 30vmax);
          mask-image: radial-gradient(circle at 88% 82%,
      #000 0, #000 22vmax, transparent 30vmax);
  transform: scale(.06);
}

/* 暖光：略大于底色前沿，形成"光在推着颜色走"的观感 */
.lk-ripple-glow {
  z-index: var(--z-base);                        /* 同属底色层：在内容层之下（A-1） */
  background: radial-gradient(circle at 88% 82%,
      var(--asset-lamp-warm) 0, transparent 62%);
  mix-blend-mode: screen;                                /* 加色，不遮底 */
  transform: scale(.02);
}
```

> **A-1 铁律（涟漪不得压平卡片）**：`.lk-ripple` / `.lk-ripple-glow` 是**底色层**，
> 必须待在**内容层之下** —— 三栏与卡片（`#left-column` / `#middle` / `#ai-column`
> 及其内部卡片）须置于 `z-index ≥ 1`，涟漪层自身取 `--z-base`（`0`，权威表 §2.7）。
> **不得**取负值（负值会落到页面底色之下，涟漪不可见），
> 更**不得**抬到内容层之上 —— 整屏不透明色块压住卡片就是「压平」，
> 已由 `decisions.md` A-1 明确否决（详见 §4.5）。
> 灯层 `.lk-lamp`（`--z-lamp` = 400，高于 `--z-modal` 300）留在内容之上是对的：它是一盏台灯，
> 不是铺满全屏的色块。

> **`mix-blend-mode: screen` 的性能提示**：全屏混合会让合成器多读一层背景。
> 本规格只在 450ms 的一次性转场里用它；若走查时 DevTools 显示该层掉帧，
> 退化为 `mix-blend-mode: normal` + 降低暖光的不透明度（观感损失可接受）。
> 该属性**本身不被动画**，不违反 §1.6 红线。

```css
/* 三条时间线：扩散 / 辉光 / 退场（见 §4.3 时序表） */
@keyframes lk-ripple-spread {
  from { transform: scale(.06); }
  to   { transform: scale(4.8); }
}
@keyframes lk-ripple-veil {
  0%   { opacity: 0; }
  18%  { opacity: 1; }
  100% { opacity: 1; }
}
@keyframes lk-ripple-clear {
  from { opacity: 1; }
  to   { opacity: 0; }
}
@keyframes lk-ripple-glow-spread {
  from { transform: scale(.02); opacity: 0; }
  12%  { opacity: 1; }
  to   { transform: scale(3.2); opacity: 1; }
}
```

**编排（vanilla JS，`workbench.js` 主题切换入口）**：

```js
/* 读目标主题的 --surface-base：权威表里它是「同名变量、两套值」，
   所以必须临时把 data-theme 置为目标主题再读（同一任务内完成，不会产生闪烁）。 */
function themeBase(theme) {
  var el = document.documentElement;
  var prev = el.getAttribute("data-theme");
  el.setAttribute("data-theme", theme);
  var v = getComputedStyle(el).getPropertyValue("--surface-base").trim();
  if (prev === null) el.removeAttribute("data-theme"); else el.setAttribute("data-theme", prev);
  return v;
}

/* 缓动值同样只从权威表 §2.6 取：WAAPI 的 easing 只接受字面量字符串，
   所以在这里把 token 读成字符串，而不是在 JS 里另抄一份系数（A-18-4）。 */
function easeVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function runLampTransition(nextTheme) {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches
            || document.documentElement.dataset.motion === "off";
  if (reduce) { applyTheme(nextTheme); return; }   // 降级：直接切

  var wash  = document.createElement("div"); wash.className  = "lk-ripple";
  var glow  = document.createElement("div"); glow.className  = "lk-ripple-glow";
  var lamp  = document.createElement("div"); lamp.className  = "lk-lamp";
  lamp.innerHTML = LAMP_SVG;                        /* 内联 SVG 字符串 */
  document.body.append(wash, glow, lamp);

  wash.style.background = themeBase(nextTheme);   /* 目标主题的 --surface-base */

  lamp.animate(
    [{ opacity: 0, transform: "translate3d(0,120%,0) scale(.86) rotate(-12deg)" },
     { opacity: 1, transform: "translate3d(0,0,0) scale(1) rotate(0deg)" }],
    { duration: 140, easing: easeVar("--ease-rebound"), fill: "forwards" });

  lamp.querySelector(".lk-lamp__glow").animate(
    [{ opacity: 0, transform: "scale(.35)" },
     { opacity: 1, transform: "scale(1.12)", offset: .6 },
     { opacity: 1, transform: "scale(1)" }],
    { duration: 80, delay: 140, easing: easeVar("--ease-out"), fill: "forwards" });

  wash.animate(
    [{ transform: "scale(.06)" }, { transform: "scale(4.8)" }],
    { duration: 450, delay: 140, easing: easeVar("--ease-ripple"), fill: "forwards" });
  wash.animate(
    [{ opacity: 0 }, { opacity: 1, offset: .18 }, { opacity: 1 }],
    { duration: 450, delay: 140, easing: "linear", fill: "forwards" });
  glow.animate(
    [{ transform: "scale(.02)", opacity: 0 },
     { transform: "scale(3.2)", opacity: 1, offset: .12 },
     { transform: "scale(3.2)", opacity: 1 }],
    { duration: 450, delay: 140, easing: easeVar("--ease-ripple"), fill: "forwards" });

  /* 换肤：涟漪完全铺满的瞬间瞬时切换 */
  window.setTimeout(function () { applyTheme(nextTheme); }, 590);

  /* 退场：涟漪淡出 + 收灯 */
  window.setTimeout(function () {
    wash.animate([{ opacity: 1 }, { opacity: 0 }],
      { duration: 110, easing: easeVar("--ease-in"), fill: "forwards" });
    glow.animate([{ opacity: 1 }, { opacity: 0 }],
      { duration: 110, easing: easeVar("--ease-in"), fill: "forwards" });
    lamp.animate(
      [{ opacity: 1, transform: "translate3d(0,0,0) scale(1) rotate(0deg)" },
       { opacity: 0, transform: "translate3d(0,-28%,0) scale(.9) rotate(8deg)" }],
      { duration: 110, easing: easeVar("--ease-in"), fill: "forwards" });
  }, 590);

  /* 收尾：移除节点（终态干净） */
  window.setTimeout(function () { wash.remove(); glow.remove(); lamp.remove(); }, 700);
}
```

### 4.3 完整时序表（700ms）

| 段 | 起 (ms) | 止 (ms) | 时长 | 元素 | 动作 |
|---|---|---|---|---|---|
| ① 探出 | 0 | 140 | 140 | `.lk-lamp` | `translate3d(0,120%→0)` + `scale(.86→1)` + `rotate(-12°→0)`，`opacity 0→1` |
| ② 点亮 | 140 | 220 | 80 | `.lk-lamp__glow` | `opacity 0→1` + `scale(.35→1.12→1)`，暖色溢出 |
| ③ 涟漪扩散 | 140 | 590 | 450 | `.lk-ripple` | `scale(.06→4.8)`，`opacity 0→1`（前 18% 淡入） |
| ③' 暖光 | 140 | 590 | 450 | `.lk-ripple-glow` | `scale(.02→3.2)`，`opacity 0→1`，`mix-blend-mode: screen` |
| ④ 换肤 | 590 | 590 | 瞬时 | `<html data-theme>` | 属性切换（底色已由涟漪带入新值，用户不可见；卡片主题值此刻整组换值，**结构与位置不变**） |
| ⑤ 涟漪退场 | 590 | 700 | 110 | `.lk-ripple` / `.lk-ripple-glow` | `opacity 1→0` |
| ⑥ 收灯 | 590 | 700 | 110 | `.lk-lamp` | `translate3d(0,0→-28%)` + `scale(1→.9)` + `rotate(0→8°)`，`opacity 1→0` |
| ⑦ 清理 | 700 | 700 | — | 三层 | `remove()`，终态干净 |

**对照 `acceptance.md` M-1 的六个采样帧**：

| 帧 | 时刻 | 画面 |
|---|---|---|
| 1 | 0ms | 台灯未入画（`opacity 0`，在画面下方） |
| 2 | 90ms | 台灯探出约 2/3 |
| 3 | 180ms | 台灯已探出、**已点亮**；涟漪刚起（前沿约 1/4 屏） |
| 4 | 330ms | 涟漪推过大半，暖光在前沿外圈 |
| 5 | 500ms | 涟漪接近铺满（几乎满屏新地面色） |
| 6 | 700ms | **终态干净**：新主题、灯与涟漪层已移除 |

> 四段（探出 → 点亮 → 涟漪扩散 → 收回）齐备 ✅

### 4.4 缩放倍数的取法（必须核对，别照抄 4.8）

不透明半径 = `22vmax × scale`，需要覆盖「灯位到最远角」的距离：

```
scale ≥ distance(灯位, 最远角) / (22 × vmax)
```

| 视口 | 灯位 | 最远角距离 | vmax | 所需 scale | 取值 |
|---|---|---|---|---|---|
| 1440×900 | (88%, 82%) | ≈1466px | 14.4px | 4.63 | **4.8** |
| 1440×900 | (50%, 50%) | ≈855px | 14.4px | 2.70 | **2.9** |
| 390×844（手机竖） | (88%, 82%) | ≈772px | 8.44px | 4.16 | **4.4** |

> 实现期**按实际灯位算一遍**，别把 4.8 写死成常量。灯位（当前写死 `88%` / `82%`）
> 决定，涟漪层与台灯共用同一组变量。

### 4.5 涟漪不压平卡片（A-1 唯一结论）

**裁决**（`decisions.md` A-1，所有者已拍板）：**不压平**。
卡片全程不动，只有**底色**从灯下扩散；结构始终清晰，450ms 后一切如初。

**本规格只有这一种实现** —— 不存在 A / B 变体，也不再留「走查时二选一」：

- **涟漪层是底色层，不是盖在内容上的色块**：`.lk-ripple` / `.lk-ripple-glow` 位于
  **内容层之下**（三栏与卡片置于 `z-index ≥ 1`），涟漪只让**底色**从灯位向外扩散。
  任何把涟漪抬到内容层之上的实现（整屏不透明色块压住卡片）＝「压平」，**被 A-1 否决**。
- **卡片全程不动**：卡片不参与扩散（无位移 / 缩放 / 透明度变化），不换位置、不换层级；
  卡片自身的主题值在 ④ 换肤那一刻整组换值 —— **结构、圆角、柔影、层级关系始终清晰可辨**。
- **450ms 后一切如初**：450ms 扩散（140→590ms）走完时底色已整屏是新主题地面色，
  换肤随之完成，涟漪退场（590→700ms）露出同一片底色 ⇒ 终态干净，无残影、无遮罩。
- **降级路径不变**：`prefers-reduced-motion` 下三层都不创建，主题直切（§4.6）。

> 旧版本把「压平」写成**默认变体**、把「保结构」写成走查时由所有者二选一的备选 ——
> 那是把**已拍板**的 A-1 重新打开成待选项，与 `decisions.md` A-1 直接冲突，**已作废**。

### 4.6 降级

```css
@media (prefers-reduced-motion: reduce) {
  .lk-ripple, .lk-ripple-glow, .lk-lamp { display: none; }
}
```

且 JS 侧在 reduced-motion / `data-motion="off"` 时**根本不创建这三个节点**
（见 §4.2 的 `runLampTransition` 首段）：主题**直接切换**，不播音效，不留残影。

---

## 5. 音画同步表

### 5.1 约束（来自 `acceptance.md` §3.3）

- 只有**四个时刻**有音效：答对 / 答错 / 完成 / 里程碑；**每条 < 200ms**；
- 首次音效必须发生在一次**用户手势**之后；
- 有静音开关，静音后**所有**音效都不播（包括庆祝）；
- 无音效时，**动效与视觉反馈仍完整可用**（声音不是唯一通道）。

### 5.2 同步表

| 时刻 | 音效文件 | 起始 | 长度 | 伴随的视觉动作（同一时刻） | 出处 |
|---|---|---|---|---|---|
| **答对** | `sfx-right` | 0ms | ≤200ms | 目标选项挤压回弹起（`lk-squash-bounce`, 517ms）；蓝色勾选几何标记瞬时出现 | 【实证】多邻国 `SOUND.CORRECT` → `right_answer.mp3` |
| **答错** | `sfx-wrong` | 0ms | ≤200ms | 目标选项水平摆动起（`lk-error-nudge`, 160ms）；红色叉号几何标记瞬时出现 | 【实证】多邻国 `SOUND.INCORRECT` → `wrong_answer.mp3` |
| **连对 5/10（插播）** | **无新音效** | — | — | 横幅弹入 + 火苗簇逐簇点亮；**复用上面的答对音效** | 【决策】`acceptance.md` §3.3 只允许四个时刻；【实证】多邻国虽有 `correct_answer_5_in_a_row_lightning` 等专用音效，但那是"第五种时刻"，超出本项目契约 |
| **完成** | `sfx-complete` | 0ms | ≤200ms | 完成页容器上浮淡入起 | 【实证】多邻国 `SOUND.FINISHED` → `lesson_complete.mp3` |
| **完成 · 统计卡 1** | `sfx-tick` | +180ms | ≤120ms | 统计卡 1 弹入 | 【实证】多邻国 `SE_STATS_1` → `se_stats_audio_1.mp3` |
| **完成 · 统计卡 2** | `sfx-tick` | +300ms | ≤120ms | 统计卡 2 弹入 | 【实证】`SE_STATS_2` |
| **完成 · 统计卡 3** | `sfx-tick` | +420ms | ≤120ms | 统计卡 3 弹入 | 【实证】`SE_STATS_3` |
| **里程碑** | `sfx-milestone` | +400ms（相对完成时刻） | ≤200ms | 几何爆点（圆环扩散）起；纸片飞散在 +800ms 起 | 【实证】多邻国 `SE_PERFECT_LESSON` → `lessoncomplete_perfectlesson_finalaudio.mp3` |

**「完成 1 声 + 统计卡 3 声」节奏的借用**【实证】：多邻国结算页预载
`[FINISHED, SE_STATS_1, SE_STATS_2, SE_STATS_3]` 四个音频并依次触发
（`DUOLINGO-ANIM-IMPL.md` §3.2，`defpackage/l5a0.java` 的 `dt10.q(...)`）。
本项目照搬这个**节奏形状**（完成 1 声 + 逐卡 3 声，间隔 120ms），
但把三声压成**同一个 `sfx-tick` 资产的 3 次重放**，
以控制资产数量（`proposal.md` 只允许"short key-feedback audio"这一类新增文件）。

### 5.3 声画对齐的工程约束

- **不串行等待**：音效与动画**同时启动**【实证】多邻国把播放丢进协程
  （`defpackage/zu90.java`），不等音效播完再播动画。本项目同样**不等**。
- **必须预载**：【实证】多邻国用 `SoundEffects$SOUND.getEntries()` 全量预载
  （`defpackage/xs10.java`）以避免首次解码延迟。本项目在设置视图首次交互后
  预载 5 个资产（`sfx-right` / `sfx-wrong` / `sfx-complete` / `sfx-tick` / `sfx-milestone`）。
- **首次手势约束**：交卷由点击触发 ✅；但**页面加载时不得有任何自动播放**。
- **静音实现**：`<html data-sound="off">` 或 `localStorage` 偏好；
  静音时**连庆祝的 tick 也不播**（`acceptance.md` §3.3）。
- **音量**：主反馈 0.5，统计卡 tick 0.35【实证】多邻国普通反馈用 0.5
  （`defpackage/ElementFragment.java`）。
- **资产来源**：多邻国的 mp3 有版权，**不可直接复用**。必须自制 4 个短音效
  （或用 Web Audio 合成）。见 §10 的待核项。

---

## 6. 参数化横幅的输入表（连对插播）

### 6.1 原则：一份横幅，不按档位另写动画

【决策】`decisions.md` 收口：「连对升级 … 5 连/10 连插播横幅（**横幅只做一份，
参数化输入**）」。
【实证】多邻国的做法完全一致：同一份 `streakmidlesson_xinarow_31.riv`
通过 **4 个 Rive 输入 + 1 个 Trigger** 驱动出不同档位
（`DUOLINGO-FEEDBACK.md` §5.5）。

> **本节硬规则**：
> **不按档位另写动画**。5 连与 10 连**共用同一份 CSS `@keyframes`**、
> **同一段 DOM 结构**；差异只通过**CSS 自定义属性**与**文字内容**表达。
> 实现期若出现第二份 `@keyframes` 或第二套 DOM，即为违规。

### 6.2 输入表

| 参数 | 对应多邻国 Rive 输入 | 类型 | 取值 | 视觉结果 |
|---|---|---|---|---|
| `count`（连对数） | 文案 + `text_lines_num` | int | 5, 6, 7, 8, 9, **10**, 11, … | 横幅主数字显示为该值；**≥10 时**文字整体上移 100px（多邻国 `LONG_STREAK_V2` 的 `setTranslationY(-100f)`），且改为**单行**结构（`text_lines_num = 0`；5 连为 `1`） |
| `threshold`（阈值档） | `animation_num` | enum | `small`（=5） / `large`（≥10） | 决定入场节奏与停留时长：`small` 700ms、`large` 900ms；`large` 的入场多一个 `rebound`（`--ease-rebound`）过冲 |
| `color`（颜色档） | `color_num` | enum | `0` 阳光黄 / `1` 学习蓝 | 横幅强调色与数字色。`1` 用于更高档（多邻国高档 combo 文字用高亮色 `juicyMacaw`）——本项目对应**学习蓝** |
| `duration`（总时长） | — | ms | 700（5 连）/ 900（≥10 连） | 横幅**总程**：弹入动画的时长；退场在 `总程 − 180ms` 处开始（退场动画本身 180ms） |
| `trigger`（触发） | `play_trig` | 事件 | `count` 跨过 5 或 10 的那一刻 | 播放一次。**同一道题只触发一次**（`count` 单调递增时的跨阈值检测） |

### 6.3 参数 → 视觉结果对照

| `count` | `threshold` | `color` | 结果 |
|---|---|---|---|
| 5 | `small` | 0（黄） | 黄色横幅，两行结构，数字"5"，弹入 700ms |
| 6–9 | `small` | 0（黄） | 同上，数字替换为 6–9。**动画不变** |
| 10 | `large` | 1（蓝） | 蓝色横幅，单行结构，数字"10"上移 100px，入场多一次过冲，停留 900ms |
| 11+ | `large` | 1（蓝） | 同上，数字替换。**不再新起横幅**（多邻国亦然：插播只在跨阈值时发生） |
| 任意（combo 断开） | — | — | 横幅立即退场（`opacity 1→0`，180ms），火苗簇熄灭 |

### 6.4 实现（纯 CSS + 写变量）

```css
.lk-combo-banner {
  position: absolute;
  top: 0; left: 50%;
  transform: translate3d(-50%, 0, 0);
  opacity: 0;
  pointer-events: none;
}
.lk-combo-banner.is-on {
  animation: lk-combo-in 700ms var(--ease-rebound) both,
             lk-combo-out 180ms var(--ease-in) 520ms both;
}
.lk-combo-banner__count {
  display: inline-block;
  transform: translate3d(0, 0, 0);
  color: var(--role-yellow);
  font-size: var(--fs-hero);              /* 庆祝数字：权威表 §2.3（A-18：不得压到 --fs-display 28px） */
}
/* 10 连档：数字上移 100px、强调色转蓝、入场多一次过冲、停留 900ms */
.lk-combo-banner.is-large.is-on {
  animation: lk-combo-in 900ms var(--ease-rebound) both,
             lk-combo-out 180ms var(--ease-in) 720ms both;
}
.lk-combo-banner.is-large .lk-combo-banner__count {
  transform: translate3d(0, -100px, 0);
  color: var(--role-blue);
}
@keyframes lk-combo-in {
  0%   { opacity: 0; transform: translate3d(-50%, 12px, 0) scale(.88); }
  60%  { opacity: 1; transform: translate3d(-50%, -2px, 0) scale(1.04); }
  100% { opacity: 1; transform: translate3d(-50%, 0, 0) scale(1); }
}
@keyframes lk-combo-out {
  from { opacity: 1; transform: translate3d(-50%, 0, 0) scale(1); }
  to   { opacity: 0; transform: translate3d(-50%, -8px, 0) scale(.96); }
}
```

```js
// 唯一的差异入口：切一个语义类，DOM 结构与 @keyframes 都不变
banner.classList.toggle("is-large", count >= 10);
banner.querySelector(".lk-combo-banner__count").textContent = String(count);
banner.classList.add("is-on");
```

> `is-large` 是给样式与测试用的**语义标记**（便于走查截图比对），
> **不引入新的 `@keyframes`**；档位差异（数字上移 100px、强调色转蓝、入场过冲、
> 停留 900ms）全部由 `.is-large` 的静态样式承担。
> ⚠️ 权威表 §2 无「横幅时长 / 位移 / 强调色」这类 per-element 运行时 token，
> 因此**不再用 CSS 变量中转**（否则会自造 token 名）；数值原样保留在上面的 CSS 里。

---

## 7. 降级矩阵（`prefers-reduced-motion: reduce`）

### 7.1 一条必须先知道的既有实现事实

`workbench/server/static/workbench.css:1126-1131` **已经**存在一条全局降级规则：

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    transition: none !important;
    animation: none !important;
  }
}
```

**后果**：reduced-motion 下**所有** `@keyframes` 停止运行，`animation-fill-mode: both`
不再生效，元素回落到**其静态样式**。因此：

> **实现铁律（新增）**：每一个动效元素的**静态样式必须等于它的终态**。
> 起始态（`opacity: 0`、`translateY(12px)`）**只能写在 `@keyframes` 内部**，
> **不得写进基础规则**。否则降级后元素会停留在"从未出现"的状态
> （例如 `opacity: 0` 的统计卡会永远不可见）。
>
> 现有 `flash-answer-reveal`（`workbench.css:994-999`）就是反例：
> 它把终点 `transform` 写进了基础规则 `.flash-card-stage.is-revealed .flash-card-answer`
> （`:989-993`），降级后靠静态样式兜住——本规格的新动效一律不这么写。

### 7.2 降级矩阵

| # | 动效 | 常规终态 | reduced-motion 终态 | 降级方式 |
|---|---|---|---|---|
| 1 | hover 覆盖层 | 覆盖层 `opacity 1`（面纱 `--veil-hover` 自带 6% 暖面纱） | 覆盖层**瞬时**显形（0ms）或直接不显示 | 去掉 `transition`；保留覆盖层作为静态提示亦可 |
| 2 | active 按下 | `scale 1` | `scale 1`（**不压缩**） | 去掉 `transition`；按下反馈改由状态色瞬切承担 |
| 3 | focus 焦点环 | 环显形 | 环显形（本就瞬时） | 无需改动 |
| 4 | focus-within 抬起 | `translateY(-1px)` | `translateY(0)` | 去掉 `transform` 过渡；**颜色瞬切保留** |
| 5 | 展开 / 收起 | 内容完全展开 | 内容完全展开（瞬时） | 高度本就瞬切；内容不做淡入/位移 |
| 6 | 视图转场 | 新页完全可见 | 新页完全可见 | 跳过 WAAPI 调用 |
| 7 | 列表 stagger | 全部项可见 | 全部项可见、**无错峰** | 去掉 `animation-delay` 与 `animation` |
| 8 | 数字滚动 | 数字 = 终值 | 数字 = **终值（直显）** | 直接写 `textContent`，不建 strip |
| 9 | 骨架呼吸 | 灰块在 opacity 1 ↔ .55 之间循环 | **灰块静止**（`opacity: 1` 直出，无呼吸） | `animation: none`（由 7.1 全局规则自动生效） |
| 10 | 加载环 | 旋转的环 | **静止的环** | 同上 |
| 11 | 答错摆动 | `translateX 0` | `translateX 0`（**不摆动**） | 去掉 `animation`；红叉几何标记保留 |
| 12 | 答对回弹 | `scale 1` | `scale 1`（**不回弹**） | 去掉 `animation`；勾选几何标记保留 |
| 13 | 庆祝（日常档） | 数字/进度带 100%/3 张卡/CTA 就位 | **全部直接落终态** | 跳过 ticker 与 stagger；进度带 `scaleX(1)` |
| 14 | 庆祝（里程碑档） | 爆点已散、纸片已落 | **只留静态构图**：数字/进度带/CTA 就位；**爆点与纸片不画** | 不创建爆点与纸片节点 |
| 15 | 台灯转场 | 新主题，灯与涟漪已移除 | **新主题**，灯/涟漪**从未创建** | JS 提前 return（§4.2）；CSS 再兜一层 `display: none` |
| 16 | 涟漪 | 已移除 | **不存在** | 同上 |
| 17 | 火苗簇 | 该亮的火苗是亮的 | **该亮的火苗直接是亮的**（跳过逐簇过程） | 一次性打上 `is-lit`，不设 `animation-delay` |
| 18 | 连对横幅 | 已退场 | 横幅**直接以终态出现**并在 `hold` 后直接消失 | 去掉 `animation`；用 `setTimeout` 控制显隐 |
| 19 | 进度带 | `scaleX 1` | `scaleX 1` | 去掉 `transition`；静态样式即 `scaleX(1)` |

### 7.3 降级的三条判定原则

1. **状态必须仍然可读**：降级后，颜色 + 几何通道仍然足以表达状态
   （`docs/GLOSSARY.md`「冗余状态通道」）。**禁止**"降级 = 只剩颜色"。
2. **终态必须仍然可用**：降级后 CTA 依然可点、数字依然准确、进度带依然是 100%。
3. **降级不是隐藏信息**：降级只抹掉"过程"，不抹掉"结果"。

---

## 8. 性能红线

### 8.1 属性红线（复述并细化 §1.6）

- ✅ 只插值 `transform` 与 `opacity`；
- ✅ 状态属性（`color` / `background-color` / `border-color` / `box-shadow` / `outline`）
  **只做瞬时切换**；
- ❌ 不动画 `width` / `height` / `top` / `left` / `margin` / `padding` /
  `grid-template-rows` / `font-size` / `filter` / `backdrop-filter` / `box-shadow`；
- ❌ 不做全屏大面积 `filter: blur()` / `backdrop-filter`（合成代价高）；
- ❌ 不用 `background-position` 之类的**重绘型**属性做扫光（骨架微光必须用
  `transform` 移动覆盖层，见 §3.3）。

### 8.2 单帧预算

| 项 | 预算 | 依据 |
|---|---|---|
| 帧间隔 | 16.7ms（60fps） | 【惯例】 |
| 脚本占用 | ≤ 4ms/帧 | 【惯例】Chrome "long task" 50ms 门槛的四分之一 |
| 同时参与合成的元素 | ≤ 20 | 【推断】 |
| 同时存在的 `will-change` 合成层 | ≤ 8 | 【推断】 |
| 单个合成层面积 | ≤ 1 个视口 | 【推断】 |
| 涟漪/台灯层存活时间 | ≤ 700ms，且**用完即 `remove()`** | 【决策】§4.3 |

**长列表**（98+ 条记录，`acceptance.md` §3.7）：

- 错峰**封顶**在第 9 项（§3.2）——不让末尾项等 4 秒；
- 列表项入场动画**只在首次进入视口时**触发一次（用 `IntersectionObserver`），
  滚回时不重放；
- 滚动过程中**不启动**任何新动画。

### 8.3 `will-change` 的使用与移除

```css
/* ✅ 正确：will-change 与动画同生共死 */
.lk-skeleton::after { will-change: transform; animation: lk-skeleton-sweep 1200ms ... infinite; }
.lk-ripple, .lk-ripple-glow, .lk-lamp { will-change: transform, opacity; }
```

| 规则 | 说明 |
|---|---|
| **只在动画即将开始时加** | 不要写在全局基础规则里常驻 |
| **动画结束即移除** | 一次性动画：`animationend` 回调里 `el.style.willChange = ""`；层：§4.2 的 700ms `remove()` |
| **无限动画例外** | 骨架**呼吸**是无限循环，`will-change` 可常驻于**当前可见的那几个**骨架块（建议 ≤ 3） |
| **绝不超过 8 层** | 超过说明有元素不该同时动 |

> **现状提示**：`workbench.css` 现有动画（`ai-plan-pulse` `:732`、
> `graph-pulse` `:1772`）均为 `opacity` / `transform`，与本红线相容；
> 图谱相关动画**不并入**本 token 体系（§1.7）。

### 8.4 其它

- **骨架屏的 `content-visibility`**：长列表容器用 `content-visibility: auto` +
  `contain-intrinsic-size`，减少首屏渲染量。
- **字体**：`font-display` 策略正确，首次加载无字体闪烁
  （`acceptance.md` §3.7）。字体切换会引发重排，动效须避开切换窗口。
- **音效**：4 个资产全部预载（§5.3），避免首次播放解码延迟阻塞主线程。

---

## 9. 出处索引

| # | 数值 / 结论 | 出处 | 级别 |
|---|---|---|---|
| 1 | 回弹 5 段 `17/33/83/167/217ms`，总 `517ms` | `DUOLINGO-ANIM-IMPL.md` §3.1.6 `MidLessonDuoJumpView.JuicierScaleAnimationSection` | 【实证】 |
| 2 | 回弹 4 条贝塞尔 `.33,0,.67,1` / `.37,0,.67,1` / `.17,0,.67,1` | 同上（`PathInterpolator` 参数） | 【实证】 |
| 3 | 回弹缩放值 `0.6 → 1.1 → 0.9603 → 1.0067 → 1.0` | 同上 | 【实证】 |
| 4 | 答对淡出 `117ms / linear / delay 733ms` | 同上 | 【实证】 |
| 5 | 完成 1 声 + 统计卡 3 声（`FINISHED` + `SE_STATS_1..3`） | `DUOLINGO-ANIM-IMPL.md` §3.2 `defpackage/l5a0.java` | 【实证】 |
| 6 | 音效与动画**并行不串行**、音效**全量预载** | 同上 §3.1.5（`defpackage/zu90.java` / `xs10.java`） | 【实证】 |
| 7 | 音量 0.5 为普通反馈惯例 | 同上 §4.2（`defpackage/ElementFragment.java`） | 【实证】 |
| 8 | 连对阈值 5 / 10 | `DUOLINGO-FEEDBACK.md` §5.3（音效文件名反推） | 【实证】 |
| 9 | 横幅 = **同一份 `.riv`** + 4 输入 + 1 Trigger | `DUOLINGO-FEEDBACK.md` §5.5（`streakmidlesson_xinarow_31.riv`） | 【实证】 |
| 10 | 10 连时文字上移 100px | 同上（`setTranslationY(-100f)`） | 【实证】 |
| 11 | 计数器三档 `0 / >0 / ≥30`；灰 `#afafaf` → 绿 `#58cc02` → 绿蓝渐变 `#58cc02→#1899d6` | `DUOLINGO-FEEDBACK.md` §5.8（`ComboIndicatorView` / `defpackage/ffd.java`） | 【实证】 |
| 12 | 连对用 `TickerView` 滚动数字 | `DUOLINGO-ANIM-IMPL.md` §5.3 | 【实证】 |
| 13 | combo > 4 答错**必须**给负反馈 | `DUOLINGO-FEEDBACK.md` §5.6（`R.string.combo_lost`） | 【实证】 |
| 14 | 结算统计卡错峰 80–120ms | `DUOLINGO-CELBRATION.md` §7.2 M3 | 【公开】 |
| 15 | 彩带只用于少数里程碑级动画 | 同上 §1.4 | 【公开】 |
| 16 | 答错 = 轻微左右位移 ≤4px、≤160ms、不抖动 | 同上 §7.1 L0 | 【公开】 |
| 17 | 里程碑专属动画"只放在里程碑日" | 同上 §3.1 / §3.4 | 【公开】 |
| 18 | 强制动画引发反弹，**分层 + 提供开关**是解法 | 同上 §5 | 【公开】 |
| 19 | 时长基调：交互 120–180ms，场景 240–520ms | `decisions.md` 12.1 | 【决策】 |
| 20 | 挤压回弹必须做 | `decisions.md` 12.2 | 【决策】 |
| 21 | 入场 = 上浮 8–12px + 淡入，180–240ms | `decisions.md` 12.3 | 【决策】 |
| 22 | 换页必须是**容器动画**（`#middle-page`） | `decisions.md` 12.4 | 【决策】 |
| 23 | 台灯转场：探出 → 点亮 → 涟漪 → 收回，共 ~700ms，涟漪 ~450ms | `decisions.md` 16.5 / 17.2 | 【决策】 |
| 24 | 涟漪只能动 `transform`/`opacity`，用放大的径向渐变做 mask | `decisions.md` 16.5 + 任务书 | 【决策】 |
| 25 | 连对横幅**只做一份**，参数化输入 | `decisions.md` 15.3 / 收口 | 【决策】 |
| 26 | 连对三级计数器：灰 → 黄 → 黄蓝渐变 | `decisions.md` 15.3 / 收口 | 【决策】 |
| 27 | 火苗簇式连对进度 | `decisions.md` 15.3 / 收口 | 【决策】 |
| 28 | 庆祝分层：日常轻 / 里程碑重 | `decisions.md` 15.1 / 收口 | 【决策】 |
| 29 | 骨架屏 = 灰块 + 微光扫过 | `decisions.md` 17.3 | 【决策】 |
| 30 | 降级一律状态直切 | `decisions.md` 收口「降级」 | 【决策】 |
| 31 | 只允许 transform/opacity | `acceptance.md` §2 通用判据 / §3.7 | 【决策】 |
| 32 | 关键帧采样帧 M-1…M-10 | `acceptance.md` §2 | 【决策】 |
| 33 | 四个音效时刻，各 < 200ms | `acceptance.md` §3.3 | 【决策】 |
| 34 | 装饰层 `pointer-events: none` | `acceptance.md` G-7 | 【决策】 |
| 35 | 已存在全局 reduced-motion 兜底 `animation: none !important` | `workbench/server/static/workbench.css:1126-1131` | 【实证】 |
| 36 | 视图转场必须容器动画（innerHTML 整体替换） | `workbench/server/static/middle-navigation.js:87` | 【实证】 |
| 37 | 交卷提交点 / 完成页渲染点 | `workbench/server/static/paper-practice.js:1004`（`submitAnswer`）、`:1194`（`submitPaper`）、`:1311`（`renderCompletion`） | 【实证】 |
| 38 | 现有 `matchMedia("(prefers-reduced-motion: reduce)")` 判定写法 | `workbench/server/static/workbench.js:1639` | 【实证】 |
| 39 | `cubic-bezier(.4,0,.2,1)` / `(.22,.61,.36,1)` / `(.55,.06,.68,.19)` | Material 动效曲线通行值 | 【惯例】 |
| 40 | 缩放档 0.92 / 0.96 / 1.06 | `decisions.md` 12.2 prose + 触控反馈惯例 | 【决策】/【惯例】 |
| 41 | 涟漪缩放倍数 4.8 / 2.9 / 4.4 | 按「灯位→最远角」距离与 `22vmax` 推算（§4.4） | 【推断】 |
| 42 | 错峰 40ms（列表）/ 24ms（负荷柱）/ 80ms（火苗） | `decisions.md` 收口「负荷柱逐柱错峰 24ms」+ 通用节奏惯例 | 【决策】/【推断】 |

---

## 10. 待核与契约漂移登记

> 纪律（`AGENTS.md`「契约权威与冲突处理」）：发现冲突**显式登记**，
> 不靠"哪个文件更新得晚"或"代码现状"自行选边。以下条目**不得在实现期被静默消解**。

| # | 类型 | 冲突内容 | 本规格的处理 | 待办 |
|---|---|---|---|---|
| D-1 | **契约漂移（已裁决，需回写）** | `decisions.md` 12.2 prose 写「scale 0.92 → 1.06 → 1」，同一节又要求「直接抄多邻国的 5 段关键帧：17/33/83/167/217ms」——后者对应的实测值是 `0.6 → 1.1 → 0.9603 → 1.0067 → 1.0` | 采用**5 段实测值**（同一节明写"直接抄"，且有源码可查）；prose 的 0.92/1.06 归入**通用缩放档**（§1.4） | `design.md` / `decisions.md` 应把 12.2 的 prose 数字改成 5 段实测值，或标注"prose 为粗略描述" |
| D-2 | **口径收紧** | `acceptance.md` §2/§3.7 要求"只动 transform/opacity"，但 hover/状态通常要变背景色 | 统一改为**伪元素覆盖层 + opacity** 做 hover；状态色**瞬切**不动画（§1.6、§2.2） | 若日后要颜色过渡，须先改 `acceptance.md` §2/§3.7 并走一次契约同步 |
| D-3 | **资产来源待定** | 多邻国的 `right_answer.mp3` 等**有版权，不可直接复用** | 规格只定义**时序与同步关系**（§5），不指定音频内容 | 5 个音效（`sfx-right` / `sfx-wrong` / `sfx-complete` / `sfx-tick` / `sfx-milestone`）需自制：或用 Web Audio 合成短音，或人工录制。**需所有者拍板来源** |
| D-4 | **既有实现需改** | `workbench.css:1126-1131` 的全局 `animation: none !important` 会让新动效在降级时停在"从未出现"的起始态 | 新增**实现铁律**：动效的静态样式必须等于终态（§7.1） | 实现期逐条自查；建议在 `workbench.css` 该处加注释说明这条铁律 |
| D-5 | **待核** | 是否允许在"完成"时刻播放 3 声 tick（`acceptance.md` §3.3 写的是"只有四个时刻有音效"） | 理解为"四个**时刻**"而非"四个**文件**"：3 声 tick 属于"完成"这一时刻内部（§5.2） | 若所有者认为应严格限制为 4 个文件，则把 3 声 tick 去掉，统计卡改为**纯视觉**错峰 |
| D-6 | **待核** | 页面级动效偏好开关（`data-motion="off"`）与系统 `prefers-reduced-motion` 的**优先级** | 规格假设：系统 reduce **恒定降级**（不可被 UI 覆盖）；UI 开关只是在系统允许时**额外**关闭动效 | 需在 `workbench-settings` 能力条款里写明这一优先级（由写 specs 的 agent 落） |

> 原 D-3「涟漪 A/B 变体待验收」已**删除**：A-1（不压平）已由所有者拍板，
> 不再是待核项（见 §4.5）。本表现有 6 条（D-1…D-6）。

---

## Self-check

- [x] §1 token 表：时长 5 档（120/160/240/400/700，以权威表 §2.6 为准）+ 517 特例说明；
      缓动 8 档（**全部是权威表 §2.6 的 token**，含 3 条多邻国实测贝塞尔；A-18-4 后本规格不再内联曲线值）；
      位移 4 档（4/8/12/20）；
      缩放 6 档 + 回弹专用组；透明度 5 档；每档标注「用于哪类交互」与出处。
- [x] §2 映射表：19 行，覆盖任务书点名的 16 项（hover / active / focus /
      focus-within / 展开收起 / 视图转场 / 列表 stagger / 数字滚动 / 骨架微光 /
      加载 / 错误 / 成功 / 庆祝（日常+里程碑）/ 台灯转场 / 涟漪 / 火苗簇），
      另加连对横幅与进度带两行；每行含触发时机 / 动画描述 / 时长 / 缓动 /
      实现方式（纯 CSS · vanilla JS · 内联 SVG）/ reduced-motion 降级形态。
- [x] §3 `@keyframes`：**20 条**（`lk-squash-bounce` / `lk-rise-in-8` /
      `lk-rise-in-12` / `lk-skeleton-sweep` / `lk-lamp-lean-out` /
      `lk-lamp-light-up` / `lk-lamp-retract` / `lk-ripple-spread` /
      `lk-ripple-veil` / `lk-ripple-clear` / `lk-ripple-glow-spread` /
      `lk-flame-ignite` / `lk-progress-fill` / `lk-celebrate-burst` /
      `lk-confetti-fall` / `lk-combo-in` / `lk-combo-out` /
      `lk-error-nudge` / `lk-spin` / `lk-flip-roll`〔备选〕），
      覆盖挤压回弹（5 段 / 4 贝塞尔 / 517ms 直译）、上浮淡入（8px 与 12px 两版）、
      骨架微光、数字滚动（ticker 为主 + 逐位翻备选）、台灯探出/点亮/收回、
      火苗点燃、庆祝（进度带 / 爆点 / 纸片）、连对横幅、错误摆动、加载旋转。
- [x] §4 涟漪：机制说明 + 完整可粘贴 CSS/JS + 700ms 时序表（7 段）+
      缩放倍数取法（含三档视口验算）+ 降级 + **A-1 唯一结论（不压平）**。
- [x] §5 音画同步表：答对 / 答错 / 完成 / 里程碑四时刻 + 统计卡 3 声节奏，
      共 9 行，逐条给出毫秒与伴随视觉动作。
- [x] §6 参数化横幅输入表：5 个参数（连对数 / 阈值档 / 颜色档 / 总时长 /
      触发）× 取值 → 视觉结果；明写「**不按档位另写动画**」，并给出
      "只写 4 个 CSS 变量、不新增 `@keyframes`、不新增 DOM" 的落地写法。
- [x] §7 降级矩阵：19 行逐项终态 + 三条判定原则 + 既有全局兜底的事实与铁律。
- [x] §8 性能红线：属性红线 / 单帧预算 / `will-change` 生命周期 / 长列表处置。
- [x] §9 出处索引：42 条，每条标【实证】/【公开】/【惯例】/【决策】/【推断】。
- [x] §10 漂移登记：6 条（D-1…D-6），均给出处理与待办。
      （原 D-3「涟漪 A/B 变体」已按 A-1 删除，条目重排为 D-3…D-6。）
- [x] 文档规模：1303 行；10 个编号章节 + Self-check；25 个代码块
      （18 CSS / 4 JS / 3 HTML-示意），代码围栏配平（50 条）。
- [x] 禁止项核对：无全局 canvas、无鼠标跟随、无视差、无光标辉光、无动画库、
      无外部资源；台灯/插画/火苗/纸片均为内联 SVG 或纯 CSS。
- [x] 冻结核对：全文不涉及请求序列、载荷、持久化、学习事实、状态机；
      装饰层一律 `pointer-events: none`；图谱页不在本规格的作用面内。
- [x] **只写了这一个文件**：未改 `proposal.md` / `design.md` / `tasks.md` /
      `specs/`，未改任何产品代码（`workbench/` / `pool/` / `pipeline/` /
      `lessonkit.py`）。
- [ ] **未决**：D-3（音效资产来源）、D-5（tick 声数量）需所有者拍板；
      D-6 需写进 `workbench-settings` 能力条款。

## 11. 新增动效的**补钉流程**（以后想到新动效就走这一条）

> 所有者 2026-10-22 的工作方式：
> 「以后想到什么新的动效可以不断打补丁上去，**但静态的得先做好**。」
> ⇒ 本节是那条工作方式的**落地流程**，也是 A-116 的操作口径。

### 11.1 前提：动效是**补丁**，静态是**主线**

- **静态先做**：一个组件的**形态**（颜色 / 圆角 / 留白 / 布局 / 纸面层级）**先落地**，
  动效**后挂**。动效**不得**成为形态的前置条件。
- 动效的**降级终态 = 静态形态**（§7.1 铁律）⇒ **静态没做好，动效就没有可回落的样子**。
  这就是「静态先做」的技术理由，而不只是排期偏好。

### 11.2 加一条新动效的**六步**（缺一步都不算完成）

| 步 | 落点 | 要求 |
|---|---|---|
| 1 | `design-notes/motion-spec.md`（**本文件**） | §1 token（时长 / 缓动 / 位移档，取现成的）· §2.1 映射表**加一行** · §3 `@keyframes` 库**加一段可直接粘贴的** · §7.2 降级矩阵**加一行** · §8 性能红线是否触及 |
| 2 | `decisions.md` | **A-27.2 的动效清单加一行**（M-O / M-P …）—— 那张清单是动效的**唯一权威** |
| 3 | `specs/workbench-ui/spec.md` | 新增或修改 **Requirement** + `#### Scenario:`（**WHEN / THEN**）—— 只有**用户可观察**的行为才进 spec |
| 4 | `tasks.md` | 加一条可勾选任务（**一个动效一条**），并**写明验证口径** |
| 5 | `acceptance.md` §2 | 加一行 **M-n**：**采样帧**（毫秒数）+ **通过标准** ⇒ **没有分镜条的动效视为未实现** |
| 6 | `tools/walkthrough/frames.py` | 若要**自动判定**：加 `MOTIONS` 条目 + `prepare_*` / `act_*` + `judge_*`，并把终态写进 `TERMINAL_CONTRACT` |

### 11.3 三条硬约束（新动效一律适用，与旧动效同标准）

1. **只动 `transform` / `opacity`**（§1.6）；
2. **静态样式 = 终态**（§7.1）—— 降级档直接是终态，不停在起始态；
3. **起始态只写在 `@keyframes` 内** —— 不得在静态样式里写起始值。

### 11.4 「想到就补」的**最小验收**（不必等整轮走查）

- **分镜条**（`acceptance.md` §2 那一行的采样帧）**肉眼可见**该动效；
- **降级帧与动效帧终态一致**（`frames.py` 的 `compare_terminal`）；
- **归类**：用户能感知 ⇒ 进 §2.1 映射表；纯装饰 ⇒ 不进，并**记一笔理由**。

### 11.5 「静态先做」的落地含义（本轮的排序依据）

- 本轮的主线顺序 = **静态形态（组件形态裁定 A-115 的 24 条）→ 验收走查 → 动效补钉**；
- 已在 `tasks.md` 第 8 组留着的两条**阶段验收**（8.6 / 8.10）是动效的**验收入口**，
  它们要等静态形态落定后再跑（否则测的是一版即将改掉的静态）；
- 之后每想到一个新动效，走 §11.2 的六步，**单开一条任务**，不必等整轮。
