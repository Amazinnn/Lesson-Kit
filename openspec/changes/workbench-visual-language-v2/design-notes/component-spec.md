# 组件规格书 — 柔和蒙德里安 v2

> **性质**：全站组件规格书。这是**规格**，不是代码；下面的 CSS 片段可直接粘贴，
> 但本文件**不落地**到 `workbench/server/static/`，不改任何产品代码。
>
> **依据**（冲突时按此顺序）：
> 1. `decisions.md`「# 收口：最终基线」（视觉唯一权威）
> 2. `proposal.md`（范围、冻结清单、能力清单）
> 3. `acceptance.md`（验收口径：底线守卫 / 截图 / 分镜 / 交互清单）
> 4. `tmp/agent-briefs/SYNTH.md`（13 个新名词、方向转向）
> 5. `tmp/frontend-audit/F08.md` §6.5（原生控件统计）、`F03.md`/`F06.md`（页面上下文）
>
> **本文件不定义** SVG 资产规格（由资产规格书定义），只按名引用。
> 资产命名约定：`asset-icon-<name>.svg`（图标）、`asset-still-<name>.svg`（静物插画）、
> `asset-lamp.svg`（台灯转场）。
>
> **范围外**：知识图谱页（`graph-physics*.js` / `graph-renderer.js` / `.graph-shell`）。
> 图谱页观感必须与现在完全一致；新 token 层不得改动图谱依赖的 token 值
> （尤其 `--surface-sheet` 保持 `#fffdf7`）。本规格对图谱内的控件**不做替换要求**。

---

## 0. 名词与术语

严格使用 `SYNTH.md` 规定的 13 个新名词，不改写、不另造：

| 中文名 | English term | 在本文件中的用法 |
|---|---|---|
| 柔和蒙德里安 v2 | Soft Mondrian v2 | 本规格所描述的视觉语言总纲 |
| 纸面层级 | Paper level | §3.4 四层纸面（底 / 卡 / 浮起 / **沉底**） |
| 夜纸 | Night paper | 暗色主题值集（底 `#1c1a16`） |
| 冗余状态通道 | Redundant state channel | 状态点「颜色 + 几何」双编码（§3.6） |
| 主题偏好 | Theme preference | 亮 / 暗，按工作区存储 |
| 阅读字面 | Reading face | 衬线 / 无衬线偏好，映射到分段控件 |
| 动效偏好 | Motion preference | 动效开关，映射到开关控件 |
| 声音偏好 | Sound preference | 音效开关，映射到开关控件 |
| 工作台设置视图 | Workbench settings view | 设置视图内的四组偏好控件 |
| 静物插画 | Still-life illustration | 空态插画（§4.21） |
| 台灯转场 | Lamp transition | 主题切换转场（由动效规格定义，本文件只声明不冲突） |
| 少字原则 | Minimal-annotation principle | 状态表达优先形态与色彩；界面注释能删则删 |
| 图案适配原则 | Contextual-graphic principle | 图标 / 插画必须由背景视觉规则推导 |

本文件额外使用的**实现层术语**（非设计名词，不进 GLOSSARY）：
「纸面层级序号 L0–L3」、「角色色槽位」、「双环焦点环」、「状态点几何集」。

---

## 1. 全局设计基线（已定前提，本文件不再论证）

| 项 | 定案 |
|---|---|
| 底色（亮） | `#fdf8ef` |
| 底色（暗 / 夜纸） | `#1c1a16` |
| 墨色（亮） | `#221f1a`（暗色下反相为暖浅色 `#f2ede3`） |
| 圆角 | **12px 统一**（按钮 / 卡片 / 标签 / 输入框 / 下拉 / 面板） |
| 纸面层级 | 底 / 卡 / 浮起 / **沉底**（4 层），靠圆角 + 柔影分层，**不用描边**（沉底层例外：1px **内**发丝线，见 §4.19 / 权威表 §6.3 例外 4） |
| 阴影 | 暖调柔影（非纯黑） |
| 背景图案 | **不用**（纯色，无纹理无网点） |
| 描边 | **不用**；唯一例外是**控件边界**（输入框 / 下拉触发器 / 复选框 / 单选），用 1px 发丝线 |
| 渐变 | 只允许出现在图标与插画内部；界面**不使用**渐变（骨架屏微光用平移实色块，见 §4.22） |
| 界面字体 | 无衬线（系统栈） |
| 阅读字体 | 衬线（打包思源宋体，OFL） |
| 等宽 | 第三族，仅用于代码 / 编号 / 工具参数 |
| 正文 | 17px / 行高 1.75 / 行宽 38em |
| 角色色 | 三个，不加第五色：**学习蓝** / **阳光黄** / **注意红** |

### 1.1 三角色色语义与配额

| 角色 | 承担语义 | 允许出现的面 | 禁止出现在 |
|---|---|---|---|
| 学习蓝 `--role-blue` | 主按钮、链接、**交互层**当前选中 | 实心填充、淡彩底、文字（浅底用 `--role-blue`）、2–3px 指示条 | 正文段落、装饰性大色块 |
| 阳光黄 `--role-yellow` | **内容层**当前项、复习强调、连对进度 | 实心填充、淡彩底、图形 | **任何承载文字的面**（黄底文字一律用墨色） |
| 注意红 `--role-red` | 失败、阻塞 | 淡彩底、文字（浅底用 `--role-red-ink`）、计数徽标 | 边框、次要信息、装饰 |

> **黄不承载文字**是硬约束（`decisions.md` 色彩表「文字承载」行）。
> 黄色底上的文字一律取 `--ink-on-warm`；黄色本身只承载**面积与形状**。

**角色色槽位（quota）定义**：一个组件最多占用 N 个角色色槽位。
「槽位」= 一次渲染中该组件实例使用到的**不同角色色**数量。

| 级别 | 含义 | 允许者 |
|---|---|---|
| R0 | 不占任何角色色（中性纸面 + 墨色） | 次按钮、文字按钮、标签（中性）、进度条（通用蓝除外） |
| R1 | 最多 1 个角色色 | 主按钮（蓝）、图标按钮（选中时蓝）、开关（开时蓝）、状态点、徽标（红）、空态主按钮（蓝） |
| R2 | 最多 2 个角色色，且必须来自不同角色 | 卡片（选中蓝 + 状态点 1 色）、工具调用卡（状态点 + 徽标）、吐司（墨底 + 红点） |
| R3 | 允许三角色全用 | 状态点组、连对计数器三档、图标组 |

**页面级上限（软约束，用于走查）**：
同一屏内 **蓝 ≤ 3 处主强调面**、**黄 ≤ 1 处主强调面**、**红 ≤ 1 处主强调面**。
超出即视为「颜色失去解码力」，须降级为中性面 + 状态点。

---

## 2. Token 契约（本规格书作为**消费方**要求的 token 清单）

> **权责**：token 层的**值**由**唯一权威表** `design-notes/night-paper-tokens.md` 拍板
> （`decisions.md` A-9）；本文件登记**组件层需要的 token 名**与**必须满足的约束**
> （对比度下限、圆角统一、暖调阴影）。
> 名字必须一致，否则本文件的 CSS 无法粘贴即用——这是本文件的**硬要求**，
> 不是对 token 层的越权。
> **本文件不自造 token 值**：结构 token 的取值一律照抄权威表（`decisions.md` A-18-4/5）。

### 2.1 结构 token（主题无关）

```css
:root {
  /* 圆角（权威表 §2.1） */
  --r-md: 12px;         /* 默认：按钮 / 输入框 / 标签 / 卡片 / 面板 */
  --r-xs: 6px;          /* 内嵌小件：紧凑内件、徽标底、行内标签 */
  --r-round: 50%;       /* 真正的圆形（正方形元素）：图标圆底 / 圆形按钮 / 圆形徽标 */
  --r-pill: 999px;      /* 胶囊（非正方形元素）：状态圆点 / 开关轨道 / 进度条 */

  /* 间距（权威表 §2.2） */
  --sp-1: 4px;  --sp-2: 8px;  --sp-3: 12px;  --sp-4: 16px;
  --sp-5: 24px; --sp-6: 32px; --sp-7: 48px;

  /* 字族（权威表 §2.4） */
  --font-ui: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", system-ui, sans-serif;
  --font-read: "Source Han Serif SC", "Noto Serif CJK SC", "Songti SC",
    Georgia, serif;
  --font-mono: "SF Mono", "JetBrains Mono", Consolas, "Liberation Mono",
    Menlo, monospace;

  /* 字号（权威表 §2.3；行高与字号成对，随行高档见各 fs 的注释） */
  --fs-hero: 36px;      /* 英雄数字：空态大标题 / 庆祝数字 / 沉底块大数字；行高 44px */
  --fs-display: 28px;   /* 次级展示层（页面大标题）；行高 36px */
  --fs-stat: 24px;      /* 统计数字；行高 30px */
  --fs-question: 24px;  /* 题号大数字；行高 30px */
  --fs-title: 18px;     /* 区块标题；行高 26px */
  --fs-sub: 16px;       /* 小标题 / 卡片标题；行高 24px */
  --fs-reading: 17px;   /* 阅读面正文（衬线）；行高 30px（1.75） */
  --fs-body: 14px;      /* 界面正文；行高 22px */
  --fs-meta: 13px;      /* 元信息 / 计数；行高 20px */
  --fs-label: 12px;     /* 标签 / kicker；行高 18px */

  --measure: 38em;      /* 阅读面行宽 */

  /* 动效（权威表 §2.6） */
  --dur-fast: 120ms;      /* 交互反馈下界 */
  --dur-base: 160ms;      /* 交互反馈默认 */
  --dur-slow: 240ms;      /* 场景下界 / 入场 */
  --dur-scene: 400ms;     /* 场景转场 */
  --dur-ceremony: 700ms;  /* 里程碑 / 台灯转场 */
  /* 缓动：值全部取自权威表 §2.6（A-18：曲线系数由权威表钉死，本文件不再自造）。
     本文件旧值 --ease-out .2,.8,.3,1 / --ease-rebound .34,1.56,.64,1 /
     --ease-standard .2,0,0,1 已作废（A-18 同名不同值收敛）。 */
  --ease-out: cubic-bezier(.22, .61, .36, 1);
  --ease-standard: cubic-bezier(.4, 0, .2, 1);
  --ease-in: cubic-bezier(.55, .06, .68, .19);
  --ease-rebound: cubic-bezier(.34, 1.3, .64, 1);  /* 挤压回弹（限幅 1.3） */

  /* 层（权威表 §2.7；层序 modal > toast > dropdown > raised） */
  --z-base: 0;          /* 涟漪底色层（A-1）：在内容层之下 */
  --z-raised: 10;
  --z-dropdown: 100;
  --z-toast: 200;       /* 吐司在模态之下 */
  --z-overlay: 250;     /* 遮罩 */
  --z-modal: 300;       /* 模态盖过吐司 */
  --z-lamp: 400;
}
```

### 2.2 主题值（亮 / 夜纸）

```css
:root, [data-theme="light"] {
  /* 纸面层级（权威表 §3.1） */
  --surface-base: #fdf8ef;      /* 页面底 */
  --surface-card: #fffdf7;      /* 卡面 */
  --surface-raised: #ffffff;    /* 浮起面 */
  --surface-sunken: #f2ece1;    /* 沉底面（内容块：作答区 / 用户消息 / 强调块） */
  --surface-code: #221f1a;      /* 代码块反白面（仅代码块 / 等宽代码区） */

  /* 墨与文字（权威表 §3.2） */
  --ink-strong: #221f1a;        /* 标题 / 强调文字 */
  --ink-body: #3b3630;          /* 正文 */
  --ink-muted: #6b6459;         /* 次要文字（≥4.5:1） */
  --ink-faint: #8d8578;         /* 三级文字（≥3:1） */
  --ink-disabled: #8a8275;      /* 失活控件文字（≥3:1） */
  --ink-on-role: #fffdf7;       /* 蓝 / 红角色面上的文字 */
  --ink-on-warm: #221f1a;       /* 黄色暖面上的文字 */
  --ink-inverse: #fffdf7;       /* 代码块反白面上的文字（仅 --surface-code） */

  /* 规则线（权威表 §3.3） */
  --rule-hair: #e6dcc4;         /* 分隔线（装饰性） */
  --rule-control: #847552;      /* 控件边界（≥3:1） */
  --rule-structure: #221f1a;    /* 单侧结构线 2px */

  /* 角色色（权威表 §3.4） */
  --role-blue: #2b62e8;         /* 学习蓝：主按钮 / 链接 / 当前选中 */
  --role-blue-press: #1f4fc4;   /* 蓝的按下档 */
  --role-blue-wash: #f2f0ef;    /* 蓝洗底：承载文字 */
  --role-blue-soft: #e0e3ee;    /* 蓝软底：纯装饰 */
  --role-yellow: #f5c518;       /* 阳光黄：面积档 */
  --role-yellow-deep: #8a6a00;  /* 阳光黄：标记档（线 / 状态点） */
  --role-yellow-soft: #fcf0cd;  /* 黄软底（装饰） */
  --role-red: #d1392b;          /* 注意红：点 / 面档 */
  --role-red-ink: #b8331f;      /* 注意红：文字档 */
  --role-red-wash: #f9e9df;     /* 红洗底：承载文字 */
  --role-red-soft: #f6d9d0;     /* 红软底：装饰 */

  /* 交互面纱（权威表 §3.5） */
  --veil-hover: rgb(61 52 37 / 6%);
  --veil-active: rgb(61 52 37 / 11%);
  --veil-modal: rgb(33 31 26 / 42%);

  /* 抬升（权威表 §3.6） */
  --elev-1: 0 1px 2px rgb(61 52 37 / 6%), 0 4px 12px rgb(61 52 37 / 4%);
  --elev-2: 0 2px 6px rgb(61 52 37 / 8%), 0 12px 28px rgb(61 52 37 / 8%);
  --elev-3: 0 4px 12px rgb(61 52 37 / 10%), 0 20px 48px rgb(61 52 37 / 12%);

  /* 骨架屏（权威表 §3.8） */
  --skeleton-base: #ece3cf;
  --skeleton-sheen: #fdf8ef;
}

[data-theme="night"] {
  --surface-base: #1c1a16;
  --surface-card: #232019;
  --surface-raised: #2b2620;
  --surface-sunken: #272319;
  --surface-code: #14120f;

  --ink-strong: #f4ede0;
  --ink-body: #e7dfd0;
  --ink-muted: #c2b8a5;
  --ink-faint: #978d7c;
  --ink-disabled: #7a7162;
  --ink-on-role: #14120f;
  --ink-on-warm: #14120f;
  --ink-inverse: #f4ede0;

  --rule-hair: #332d25;
  --rule-control: #7d7361;
  --rule-structure: #ece3d3;

  --role-blue: #7291de;
  --role-blue-press: #8fa9e8;
  --role-blue-wash: #292929;
  --role-blue-soft: #31343c;
  --role-yellow: #e0c151;
  --role-yellow-deep: #f0d98a;
  --role-yellow-soft: #3d3721;
  --role-red: #d4736b;
  --role-red-ink: #e08878;
  --role-red-wash: #352821;
  --role-red-soft: #432f28;

  --veil-hover: rgb(255 244 224 / 6%);
  --veil-active: rgb(255 244 224 / 12%);
  --veil-modal: rgb(20 18 15 / 58%);

  --elev-1: 0 1px 2px rgb(0 0 0 / 30%), inset 0 1px 0 rgb(255 238 210 / 5%);
  --elev-2: 0 10px 28px rgb(0 0 0 / 38%), 0 0 24px rgb(255 236 200 / 5%), inset 0 1px 0 rgb(255 238 210 / 7%);
  --elev-3: 0 20px 48px rgb(0 0 0 / 52%), 0 0 32px rgb(255 236 200 / 6%), inset 0 1px 0 rgb(255 238 210 / 9%);

  --skeleton-base: #26221b;
  --skeleton-sheen: #3c3529;
}
```

**对比度**：本文件不再自带对比度结论 —— token 的**名字与取值**由
`design-notes/night-paper-tokens.md` 唯一裁决（`decisions.md` A-9），其 §4.2 / §4.3
已给出 76 行实算（38 个前景/背景配对 × 2 主题），§4.4 逐条修正了 11 项初始不达标项。
本文件只消费这些 token，**不得另立一套值或另算一套对比度**。

| 组合 | 出处 |
|---|---|
| `--ink-strong` on `--surface-base`（标题墨 / 页面底） | 权威表 §4.2 / §4.3 |
| `--ink-body` on `--surface-card`（正文墨 / 卡面） | 权威表 §4.2 / §4.3 |
| `--ink-muted` on `--surface-base`（次要文字） | 权威表 §4.2 / §4.3 |
| `--ink-faint` on `--surface-card`（三级文字） | 权威表 §4.2 / §4.3 |
| `--role-blue` on `--surface-base`（链接蓝） | 权威表 §4.2 / §4.3 |
| `--role-blue` on `--role-blue-wash`（蓝字落蓝洗底） | 权威表 §4.2 / §4.3 |
| `--role-red-ink` on `--role-red-wash`（红字落红洗底） | 权威表 §4.2 / §4.3 |
| `--ink-on-role` on `--role-blue`（主按钮文字） | 权威表 §4.2 / §4.3 |
| `--ink-on-warm` on `--role-yellow`（黄底文字） | 权威表 §4.2 / §4.3 |

> **黄色不承载文字**这条约束依然成立：黄底上的字取 `--ink-on-warm`，
> 而不是「黄色文字」。黄色若要当文字色（例如黄色进度条上的数字），用 `--ink-on-warm`。
> ⚠️ 待核：本表只做索引；权威表的实算若变更，改权威表即可，本表不另算。

### 2.3 焦点环 token

```css
:root {
  --focus-width: 2px;
  --focus-offset: 2px;
}
```

> 焦点环的**颜色**取权威表 §3.7 的 `--focus-outer` / `--focus-inner`
> （外圈 / 角色填充控件内圈），**本文件不在此重复定义**。

双环焦点环：内环用**当前纸面色**、外环用**蓝**，因此在蓝底、白底、纸上都可见。
- 落在页面底上的控件：内环 `var(--surface-base)`，外环 `var(--focus-outer)`；
- 落在卡面（`.lk-focusable--on-paper`）上的控件：内环 `var(--surface-card)`，外环 `var(--focus-outer)`；
- 角色填充控件（主按钮）：内环 `var(--focus-inner)`，外环 `var(--focus-outer)`（权威表 §8 规则 2）。

---

## 3. 通用规则

### 3.1 尺寸与最小点击区

- 所有可交互控件的**命中区 ≥ 44 × 44 CSS px**（权威表 §2 无「最小命中区」token → 直接写 44px → 待裁决）。
- 视觉尺寸可以小于 44px（如 34px 题号格、20px 复选框框），但必须：
  1. 用伪元素把命中区撑到 44px，或
  2. 用容器间距补偿，使**相邻命中区中心距 ≥ 44px**。
- 例外：连续密集的**题号格网格**用「2 号 (2) 尺寸补偿法」——格 36px + 间隙 8px = 44px 步距。

### 3.2 焦点环

```css
.lk-focusable:focus-visible {
  outline: 2px solid transparent;
  outline-offset: 2px;
  box-shadow: 0 0 0 2px var(--surface-base), 0 0 0 4px var(--focus-outer);
}
/* 位于卡片 / 浮起面上时，内环换成该面纸色 */
.lk-focusable--on-paper:focus-visible {
  box-shadow: 0 0 0 2px var(--surface-card), 0 0 0 4px var(--focus-outer);
}
@media (forced-colors: active) {
  .lk-focusable:focus-visible { outline: 2px solid Highlight; outline-offset: 2px; }
}
```

- 全局 `:focus-visible` 基础规则目前被三处 `outline: none` 压死
  （`workbench.css:338`、`:427`、`:833`）。本规格的所有控件**不得**再写 `outline: none`。
- 焦点环**不得**被 `overflow: hidden` 裁掉：需要时给容器留 2px 内缩或提升 `z-index`。

### 3.3 动效

| 场景 | 时长 | 缓动 |
|---|---|---|
| hover / active 反馈 | 120–180ms | `--ease-out` |
| 面板展开 / 折叠 | 160ms（`--dur-base`） | `--ease-out` |
| 视图转场（容器上浮淡入） | 240ms | `--ease-out` |
| 挤压回弹 | 517ms（17/33/83/167/217ms 关键帧） | `--ease-rebound` |
| 里程碑 | 700ms（`--dur-ceremony`） | `--ease-rebound` |

- 只动 `transform` / `opacity`（`acceptance.md` §3.7）；宽度类变化（进度条）例外允许
  `width`，但必须配 `transform` 无关的可接受帧率。
- `prefers-reduced-motion: reduce` 下**一律降级为状态直切**（已有全局闸门
  `workbench.css:1126-1131`，本规格不新增例外）。
- 骨架屏微光、骨架、装饰性入场不得阻止指针事件（`pointer-events: none`）。

### 3.4 纸面层级（Paper level）

| 级别 | 名称 | token | 用途 | 圆角 | 柔影 |
|---|---|---|---|---|---|
| L0 | 底 | `--surface-base` | 页面底、栏底 | — | 无 |
| L1 | 卡 | `--surface-card` | 卡片、输入框、列表项、内层面板 | 12px | `--elev-1` |
| L2 | 浮起 | `--surface-raised` | 下拉面板、吐司、对话框、悬浮工具条 | 12px | `--elev-3` |
| L3 | **沉底** | `--surface-sunken` | **内容块**：作答区、用户消息、强调块、题号大字块、连对计数器底 | 12px | 无（**凹层**） |

> **A-23（2026-10-22）**：L3 由「**墨块**」改为「**沉底**」。
> 原 L3 = 近黑深底（`--surface-ink` #221f1a / #14120f），**退出内容块**：
> 该 token **更名为 `--surface-code`**，语义收窄为「**仅代码块 / 等宽代码区的反白面**」
> （取值不变，代码块不因本裁决改动），**不再是一层纸面**。
> L3 沉底 = **浅色主题比卡面略深的暖灰米底 + 墨字**（#f2ece1），
> **夜纸反向 = 比卡面略亮 + 浅墨字**（#272319）。

**分层铁律**：相邻两级靠 **圆角 + 柔影** 拉开，不靠描边、不靠背景图案、不靠渐变。
**L3 沉底是唯一的例外**：它是**凹层**，不抬升（无柔影），
边界靠「**底色差 + 1px 内发丝线**」与 L1 卡面分开（权威表 §3.1【A-23-3】/ §6.3 例外 4）。

```css
.lk-paper-l0 { background: var(--surface-base); }
.lk-paper-l1 { background: var(--surface-card); border-radius: var(--r-md);
  box-shadow: var(--elev-1); }
.lk-paper-l2 { background: var(--surface-raised); border-radius: var(--r-md);
  box-shadow: var(--elev-3); }
/* L3 = 沉底：凹层，不抬升；1px 内发丝线用 inset 阴影（不引入 border，不改盒模型） */
.lk-paper-l3 { background: var(--surface-sunken); color: var(--ink-strong);
  border-radius: var(--r-md);
  box-shadow: inset 0 0 0 1px var(--rule-hair); }
```

### 3.5 角色色配额速查

| 组件 | 角色色 | 槽位 |
|---|---|---|
| 主按钮 | 蓝（实心） | R1 |
| 次按钮 | 无 | R0 |
| 文字按钮 | 无（选中态蓝） | R0 / R1 |
| 图标按钮 | 无（选中态蓝） | R0 / R1 |
| 输入框 / 文本域 | 无（错误态红） | R0 / R1 |
| 自绘下拉 | 无（选中项蓝） | R0 / R1 |
| 复选框 / 单选 | 无（选中蓝） | R0 / R1 |
| 开关 | 蓝（开） | R1 |
| 分段控件 | 无（选中蓝） | R0 / R1 |
| 标签 | 无（可有蓝 / 黄 / 红洗底变体，各 1） | R0 / R1 |
| 徽标 | 红（阻塞计数） | R1 |
| 状态圆点 | 蓝 / 黄 / 红 / 中性（每点 1） | R1 |
| 进度条 | 蓝（通用） | R1 |
| 分段进度条 | 黄（连对 / 复习）或蓝 | R1 |
| 题号格 | 蓝 / 黄 / 红 / 中性（每格 1） | R1 |
| 卡片 | 无（选中蓝 + 状态点） | R0 / R2 |
| 纸面 L0–L3 | 无 | R0 |
| 沉底块 | 无（可嵌 1 个角色色块） | R0 / R1 |
| 空态 | 蓝（主按钮） | R1 |
| 骨架屏 | 无 | R0 |
| 吐司 | 红点（错误时） | R0 / R1 |
| 对话框 | 无 | R0 |
| 工具调用卡 | 状态点（1 色）+ 可选红徽标 | R1 / R2 |
| 时间线节点 | 状态点（1 色） | R1 |
| 折叠段 | 无（可选状态点） | R0 / R1 |
| Tab | 蓝（当前指示） | R1 |

### 3.6 冗余状态通道（Redundant state channel）

状态**不得只靠颜色**（既有契约），必须配**几何**编码；**零文字**。

**状态点几何集**（10px 盒内绘制，全部用 CSS 绘制，不引图标字体）：

| 几何 | 形状 | 实现要点 |
|---|---|---|
| `filled` | 实心圆 | `background: currentColor` |
| `ring` | 空心环 | 2px 边框 + 透明底 |
| `half` | 左半填充 | `linear-gradient` 被禁 → 用 `box-shadow: inset -5px 0 0 0 currentColor` 造半圆 |
| `dash` | 45° 斜杠 | 2px 斜线（`transform: rotate(45deg)` 的细长方块） |
| `cross` | 叉 | 两条 2px 细长方块交叉 |
| `check` | 勾 | 两条 2px 细长方块组成勾形（左短 45° 下斜 + 右长 −45° 上斜，`transform-origin: 0 50%`）；**只用中性墨或红，不引入新色** |

**状态 → （色，几何）映射表**（唯一映射，不得有两条状态共用同一组合）：

| 语义 | 色 | 几何 | 说明 |
|---|---|---|---|
| 未开始 / 待办 | 中性墨 `--ink-disabled` | `ring` | 最弱 |
| 当前 · 交互层（导航 / Tab / 选中项） | 蓝 | `ring` | 空心蓝环 = 选中轮廓 |
| 进行中 | 蓝 | `half` | 半填充 |
| 已完成 / 通过（流程进度） | 蓝 | `filled` | 实心蓝 |
| 当前 · 内容层（当前题 / 复习强调 / 连对） | 黄 | `filled` | 实心黄 |
| 到期 / 需复习 | 黄 | `dash` | 黄斜杠 |
| 判定正确 / 答对 | 中性墨 `--ink-strong` | `check` | 墨色勾形（A-20-3：答对**不用绿、不用蓝**） |
| 失败 / 错误 | 红 | `filled` | 实心红 |
| 阻塞 / 卡住 | 红 | `cross` | 红叉 |

> **「当前」在蓝与黄之间如何分工**：`decisions.md` 里蓝 = 「当前选中」、黄 = 「当前」。
> 二者的边界是：**交互层**（用户正在操作的对象：导航项、Tab、选项、当前页）用**蓝**；
> **内容层**（内容本身的状态：当前题号、当前复习项、连对计数）用**黄**。
> 这是一条**规格级裁决**，若与 token 层或 spec delta 冲突，以本条为准并回改冲突处。

> **「答对」为什么是中性墨而不是绿 / 蓝**（`decisions.md` A-20 第 3 条）：
> 权威表 §3.4 的三角色配额里**没有绿**，而「当前选中」已经占住蓝 —— 让「答对」也用蓝，
> 「点我」和「我对了」就共用同一条通道。因此「答对」= **中性墨 `--ink-strong` + 勾形几何**，
> 「答错」= `--role-red`（既有语义不变）；**不引入第四种颜色**，也不新造绿 token。
> 现状里表示「答对」的绿（`#1a7f37` / `#e6f4ea` / `#d9ebdd` / `#245d32`）**本轮整体移除**，
> 现状兼容例外登记在 `contract-drift.md`（CD-071 / CD-072）。
> 几何仍是**第二通道**：墨色勾 vs 红色叉/红面，在灰度打印与色觉障碍下都能区分。

---

## 4. 组件规格

> 每条规格的格式：**定位 → 尺寸 → 状态表 → 角色色配额 → CSS → 深浅差异 → 可访问性**。
> 尺寸记号：`高 × 宽`，`padding` 记为 `padding: 上 右 下 左`。
>
> **两条覆盖本节的约定（2026-10-22 所有者裁定 · A-115）**：
> 1. **尺寸是默认建议值，不是硬约束** —— 本节各条里的尺寸数字（高 / 宽 / 内距 / 字号）
>    **可以按具体布局与视觉效果微调**，实现时以「看起来对」为准。
>    **唯一不可让步**的是 §3.1 的**命中区 ≥ 44×44 CSS px**（无障碍硬约束）与 §3.2 的**焦点环**。
>    （所有者原话：「按钮、卡片等的大小可以根据具体布局与视觉效果做微调，数字不是定死的。」）
> 2. **形态裁定优先** —— 每条下面的「**形态裁定**」框是所有者从样式板选定的**唯一形态**，
>    与本节正文冲突时**以形态裁定为准**；正文保留原文是为了记录推导过程（**不改写历史**）。
>    汇总见 **§4.30**。

### 4.1 按钮 · 主按钮（Primary）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **B 无影平底**（`btn-primary-flat`）。蓝底 **无描边、无阴影**；高度默认 40px
> （数字可按布局微调 —— 见 §4.30.2；命中区 ≥44px 仍是硬约束）。
> hover 只抬起 1px（`transform`），**底色瞬切**；active = 抬起 + 压缩。
> ⚠️ 旧稿的 `box-shadow: var(--elev-2)` 与近黑描边**作废**。

**定位**：页面上**唯一**的主要动作。一个视图内主按钮 ≤ 1 个；表单提交按钮与空态 CTA 都算主按钮。

- 尺寸：`高 44px`（L 48px / S 36px 视觉，命中区均 ≥ 44px）；`min-width: 96px`（S 免）
- 圆角：`--r-md`（12px）
- 字族字号：`--font-ui` / `--fs-body`（14px）/ `line-height: 1` / `font-weight: 600`
- 内外边距：`padding: 0 20px`（L `0 24px`，S `0 12px`）
- 最小点击区：`min-height: 44px`
- 图标（可选）：本地 SVG 18×18，`gap: 8px`，图标用 `--ink-on-role`

| 状态 | 表现 |
|---|---|
| 默认 | `background: var(--role-blue)`；`color: var(--ink-on-role)`；`box-shadow: var(--elev-2)` |
| hover | `background: var(--role-blue-press)`；`transform: translateY(-1px)`；阴影不变；`120ms` |
| active | `transform: translateY(1px)`；`box-shadow: none`；`80ms` |
| focus-visible | 双环焦点环（§3.2）；`transform` 保持 hover 位不叠加位移 |
| disabled | `background: var(--veil-active)`；`color: var(--ink-faint)`；`box-shadow: none`；`cursor: not-allowed`（**不用 opacity 压暗**——opacity 会把蓝底一起压成灰蓝） |
| loading | 原按钮内容替换为旋转指示器（12px 圆环，`--ink-on-role`）；`min-width` 锁定防跳动；`aria-busy="true"`；`pointer-events: none` |
| selected | 不适用（主按钮不是选择器） |
| error | 不适用。**按钮不承载 error 状态**；提交失败时按钮回到默认态，错误由「行内错误条 + 状态点」承担（§4.23 吐司 / 表单错误） |

- 角色色：**蓝**，R1。无第二种角色色。

```css
.lk-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: var(--sp-2);
  min-height: 44px; min-width: 96px;
  padding: 0 var(--sp-5);
  border: 0; border-radius: var(--r-md);
  background: var(--veil-active); color: var(--ink-strong);
  font-family: var(--font-ui); font-size: var(--fs-body);
  line-height: 1; font-weight: 600; text-decoration: none;
  cursor: pointer; position: relative;
  transition: background-color var(--dur-fast) var(--ease-out),
              transform var(--dur-fast) var(--ease-out),
              box-shadow var(--dur-fast) var(--ease-out);
}
.lk-btn:focus-visible {
  outline: 2px solid transparent; outline-offset: 2px;
  box-shadow: 0 0 0 2px var(--focus-inner), 0 0 0 4px var(--focus-outer);
}
.lk-btn--primary { background: var(--role-blue); color: var(--ink-on-role); box-shadow: var(--elev-2); }
.lk-btn--primary:hover:not(:disabled):not([aria-busy="true"]) { background: var(--role-blue-press); transform: translateY(-1px); }
.lk-btn--primary:active:not(:disabled) { transform: translateY(1px); box-shadow: none; }
.lk-btn:disabled { cursor: not-allowed; color: var(--ink-faint); background: var(--veil-active); box-shadow: none; }
.lk-btn--primary:disabled { background: var(--veil-active); color: var(--ink-faint); }
.lk-btn[aria-busy="true"] { cursor: progress; pointer-events: none; }
.lk-btn__spinner {
  width: 12px; height: 12px; border-radius: var(--r-round);
  border: 2px solid currentColor; border-top-color: transparent;
  animation: lk-spin 700ms linear infinite;
}
@keyframes lk-spin { to { transform: rotate(360deg); } }
```

### 4.2 按钮 · 次按钮（Secondary）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **C 沉底次按钮**（`btn-secondary-sunken`）。**沉底面 `--surface-sunken` + 内发丝线**
> （不是描边）⇒ 读成「压下去」而不是「浮起来」。不用角色色（蓝留给主按钮）。

**定位**：并列的次要动作（取消 / 返回 / 保存草稿）。与主按钮同屏并列时，**主在右、次在左**。

- 尺寸 / 圆角 / 字族字号 / 命中区：同 §4.1
- 内外边距：`padding: 0 16px`
- 边界：1px `--rule-control`（**控件边界是「不用描边」规则的唯一例外**）

| 状态 | 表现 |
|---|---|
| 默认 | `background: var(--surface-card)`；`color: var(--ink-strong)`；`border: 1px solid var(--rule-control)`；`box-shadow: var(--elev-1)` |
| hover | `background: var(--surface-raised)`；`border-color: var(--ink-disabled)`；`transform: translateY(-1px)` |
| active | `transform: translateY(1px)`；`box-shadow: none` |
| focus-visible | 双环焦点环，内环用 `--focus-inner`、外环用 `--focus-outer` |
| disabled | `background: var(--surface-base)`；`color: var(--ink-disabled)`；`border-color: var(--rule-control)`；无阴影 |
| loading | 同主按钮；加载圈用 `--ink-strong` |
| selected | 不适用 |
| error | 不适用（同 §4.1） |

- 角色色：**无**，R0。

```css
.lk-btn--secondary { background: var(--surface-card); color: var(--ink-strong);
  border: 1px solid var(--rule-control); box-shadow: var(--elev-1); }
.lk-btn--secondary:hover:not(:disabled) { background: var(--surface-raised);
  border-color: var(--ink-disabled); transform: translateY(-1px); }
.lk-btn--secondary:active:not(:disabled) { transform: translateY(1px); box-shadow: none; }
.lk-btn--secondary:disabled { background: var(--surface-base); color: var(--ink-disabled); box-shadow: none; }
```

### 4.3 按钮 · 文字按钮（Text / Ghost）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **B 带箭头**（`btn-text-arrow`）。透明底 + hover 洗底 + **一个 CSS 画的右箭头**
> （`::after`，用 border/transform 画，**不引 SVG 资产**）；箭头与文字 gap 8px，
> 随文字墨色、**不承载语义色**。

**定位**：低强调动作（取消、展开、更多）。**同一行最多一个文字按钮**。

- 尺寸：高 44px（命中区），`min-width: 0`
- 圆角：`--r-md`
- 内外边距：`padding: 0 12px`
- 字族字号：`--font-ui` / `--fs-body` / `font-weight: 500`
- 背景：默认透明

| 状态 | 表现 |
|---|---|
| 默认 | `background: transparent`；`color: var(--ink-muted)` |
| hover | `background: var(--veil-hover)`；`color: var(--ink-strong)` |
| active | `background: var(--veil-active)`；`color: var(--ink-strong)` |
| focus-visible | 双环焦点环 |
| disabled | `color: var(--ink-disabled)`；`background: transparent` |
| loading | 不适用（文字按钮不做异步动作；若必须，`aria-busy` + 文字不变） |
| selected | `background: var(--role-blue-wash)`；`color: var(--role-blue)`（用于「当前视图」切换，如记录中心 Tab 的文字形态） |
| error | 不适用 |

- 角色色：默认 R0；selected 态 R1（蓝）。

```css
.lk-btn--text { background: transparent; color: var(--ink-muted); padding: 0 var(--sp-3); min-width: 0; font-weight: 500; }
.lk-btn--text:hover:not(:disabled) { background: var(--veil-hover); color: var(--ink-strong); }
.lk-btn--text:active:not(:disabled) { background: var(--veil-active); color: var(--ink-strong); }
.lk-btn--text:disabled { color: var(--ink-disabled); background: transparent; }
.lk-btn--text[aria-selected="true"], .lk-btn--text[aria-pressed="true"] {
  background: var(--role-blue-wash); color: var(--role-blue); }
```

### 4.4 按钮 · 图标按钮（Icon）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **C 圆形图标按钮**（`iconbtn-round`）。**40×40 圆形**（`border-radius: 999px`）
> + **沉底面**；命中区 **≥44px** 用伪元素补（回答 **A-84 第 3 条**）。
> 图标保持字符（换 SVG 是资产问题，不在本波）。

**定位**：只有图形、没有文字的动作（抽屉开关、折叠、关闭、缩放）。**必须有可访问名**。

- 视觉尺寸：`40 × 40`（S 32×32）；命中区靠伪元素扩到 44px
- 圆角：`--r-md`
- 内外边距：`padding: 0`；图标 20×20（本地 SVG，`asset-icon-<name>.svg`）
- 字族字号：无文字；仅 `aria-label` / `title`

| 状态 | 表现 |
|---|---|
| 默认 | `background: transparent`；图标 `stroke: var(--ink-muted)` |
| hover | `background: var(--veil-hover)`；图标 `stroke: var(--ink-strong)` |
| active | `background: var(--veil-active)`；`transform: scale(.96)`；`80ms` |
| focus-visible | 双环焦点环（命中区而非图标本体） |
| disabled | 图标 `stroke: var(--ink-disabled)`；`background: transparent`；`cursor: not-allowed` |
| loading | 不适用；异步动作请改用带 label 的按钮 |
| selected | `background: var(--role-blue-wash)`；图标 `stroke: var(--role-blue)` |
| error | 不适用 |

- 角色色：默认 R0；selected R1（蓝）。

```css
.lk-iconbtn { position: relative; width: 40px; height: 40px; min-height: 44px;
  display: inline-flex; align-items: center; justify-content: center;
  padding: 0; border: 0; border-radius: var(--r-md);
  background: transparent; color: var(--ink-muted); cursor: pointer;
  transition: background-color var(--dur-fast) var(--ease-out),
              transform var(--dur-fast) var(--ease-out); }
.lk-iconbtn::before { content: ""; position: absolute; inset: -2px; min-width: 44px;
  min-height: 44px; }
.lk-iconbtn:hover:not(:disabled) { background: var(--veil-hover); color: var(--ink-strong); }
.lk-iconbtn:active:not(:disabled) { background: var(--veil-active); transform: scale(.96); }
.lk-iconbtn:disabled { color: var(--ink-disabled); cursor: not-allowed; }
.lk-iconbtn[aria-selected="true"], .lk-iconbtn[aria-pressed="true"] {
  background: var(--role-blue-wash); color: var(--role-blue); }
.lk-iconbtn svg { width: 20px; height: 20px; display: block; fill: none; stroke: currentColor;
  stroke-width: 1.75; stroke-linecap: round; stroke-linejoin: round; }
```

### 4.5 输入框（Input）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **A spec 输入框**（`input-spec`）。高 44px · 圆角 12px · `padding: 0 14px` ·
> 聚焦 = 蓝边 + **3px 蓝洗底光晕**。焦点环仍走 §3.2 的 `--focus-outer`
> （**不写 `outline: none`**）。

**定位**：单行文本录入。

- 高 44px（S 36px，命中区 ≥ 44px）；圆角 `--r-md`（12px）
- 字族字号：`--font-ui` / `--fs-body`（14px）
- 内外边距：`padding: 0 14px`
- 背景 `--surface-card`；边界 1px `--rule-control`（控件边界例外）

| 状态 | 表现 |
|---|---|
| 默认 | `background: var(--surface-card)`；`border-color: var(--rule-control)`；`color: var(--ink-strong)` |
| hover | `border-color: var(--ink-disabled)` |
| active | 同 hover（浏览器原生） |
| focus-visible | `border-color: var(--role-blue)`；`box-shadow: 0 0 0 3px var(--role-blue-wash)`；`background: var(--surface-raised)`。**禁止 `outline: none`** |
| disabled | `background: var(--surface-base)`；`color: var(--ink-disabled)`；`border-color: var(--rule-control)`；`cursor: not-allowed` |
| loading | 不适用（输入框不做加载态）；若字段正在校验，`aria-busy="true"` + 右侧 12px 指示器 |
| selected | 文本选中 `background: var(--role-blue-wash)`；`color: var(--ink-strong)` |
| error | `border-color: var(--role-red)`；`box-shadow: 0 0 0 3px var(--role-red-wash)`；下方 4px 处出现行内错误（红点 + 文字，§4.23）；`aria-invalid="true"` |
| readonly | `background: var(--surface-base)`；`color: var(--ink-muted)` |

- 角色色：默认 R0；error 态 R1（红）。聚焦环用蓝属于「焦点指示」，**不计角色色槽位**。

```css
.lk-input {
  width: 100%; min-height: 44px; padding: 0 14px;
  border: 1px solid var(--rule-control); border-radius: var(--r-md);
  background: var(--surface-card); color: var(--ink-strong);
  font-family: var(--font-ui); font-size: var(--fs-body); line-height: 1.4;
  transition: border-color var(--dur-fast) var(--ease-out),
              box-shadow var(--dur-fast) var(--ease-out),
              background-color var(--dur-fast) var(--ease-out);
}
.lk-input::placeholder { color: var(--ink-faint); }
.lk-input:hover:not(:disabled):not(:focus-visible) { border-color: var(--ink-disabled); }
.lk-input:focus-visible { outline: 2px solid transparent; outline-offset: 2px;
  border-color: var(--role-blue); background: var(--surface-raised);
  box-shadow: 0 0 0 3px var(--role-blue-soft); }
.lk-input:disabled { background: var(--surface-base); color: var(--ink-disabled); cursor: not-allowed; }
.lk-input[readonly] { background: var(--surface-base); color: var(--ink-muted); }
.lk-input[aria-invalid="true"] { border-color: var(--role-red); box-shadow: 0 0 0 3px var(--role-red-wash); }
.lk-input::selection, .lk-textarea::selection { background: var(--role-blue-wash); color: var(--ink-strong); }
```

### 4.6 文本域（Textarea）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **A spec 文本域**（`textarea-spec`）。最小高 96px · 行高 1.6 · 圆角 12px ·
> **竖向可拉**（`resize: vertical`）。与 §4.5 共用聚焦口径。

**定位**：多行录入。**行高 1.6、衬线不适用**（界面控件一律无衬线）；阅读面才是衬线。

- 最小高 96px（`rows=3` 时 88px）；圆角 `--r-md`
- 内外边距：`padding: 12px 14px`
- 字族字号：`--font-ui` / `--fs-body` / `line-height: 1.6`
- `resize: vertical`；`min-width: 100%`

| 状态 | 表现 |
|---|---|
| 默认 | 同输入框：`--surface-card` 底 + 1px `--rule-control` |
| hover | `border-color: var(--ink-disabled)` |
| active | 同 hover |
| focus-visible | `border-color: var(--role-blue)`；`box-shadow: 0 0 0 3px var(--role-blue-wash)`；`background: var(--surface-raised)` |
| disabled | `--surface-base` 底；`color: var(--ink-disabled)` |
| loading | 不适用 |
| selected | 文本选中 `--role-blue-wash` |
| error | `border-color: var(--role-red)`；`box-shadow: 0 0 0 3px var(--role-red-wash)`；`aria-invalid="true"` |

- **特例 · Agent 贴底输入区**（`pages.py:773` `#ai-input`）：
  贴底、`border-radius: var(--r-md)`、最小高 72px、聚焦时**变蓝**并**轻微抬起**
  （`transform: translateY(-2px)` + `--elev-2`），这是「Agent 输入区」的唯一变体。

- 角色色：默认 R0；error R1（红）。Agent 聚焦变蓝属焦点反馈，不计槽位。

```css
.lk-textarea {
  width: 100%; min-height: 96px; padding: 12px 14px;
  border: 1px solid var(--rule-control); border-radius: var(--r-md);
  background: var(--surface-card); color: var(--ink-strong); resize: vertical;
  font-family: var(--font-ui); font-size: var(--fs-body); line-height: 1.6;
  transition: border-color var(--dur-fast) var(--ease-out),
              box-shadow var(--dur-fast) var(--ease-out);
}
.lk-textarea::placeholder { color: var(--ink-faint); }
.lk-textarea:focus-visible { outline: 2px solid transparent; outline-offset: 2px;
  border-color: var(--role-blue); background: var(--surface-raised);
  box-shadow: 0 0 0 3px var(--role-blue-soft); }
.lk-textarea:disabled { background: var(--surface-base); color: var(--ink-disabled); cursor: not-allowed; }
.lk-textarea[aria-invalid="true"] { border-color: var(--role-red); box-shadow: 0 0 0 3px var(--role-red-wash); }
.lk-textarea--composer { min-height: 72px; border-radius: var(--r-md);
  transition: transform var(--dur-base) var(--ease-out),
              box-shadow var(--dur-base) var(--ease-out); }
.lk-textarea--composer:focus-visible { transform: translateY(-2px); box-shadow: var(--elev-2); }
```

### 4.7 自绘下拉（Select / Combobox）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **A spec 自绘下拉**（`select-spec`）。⚠️ **本条属 B 类** —— 产品里**没有**这个界面
> （原生 `<select>` 8 处）⇒ **先改 OpenSpec**（键盘与 ARIA + **保留 hidden input 承载载荷**，
> 请求序列与载荷不得变）再谈实现。形态：触发器 + 浮起面板 + 选中项蓝洗底 + 行尾蓝点。

**定位**：从一组**互斥**选项中选一个。**全站 8 处原生 `<select>` 一律替换**（见 §5）。

- 触发器：高 44px，圆角 `--r-md`，`padding: 0 14px`，右内嵌 16×16 箭头（本地 SVG `asset-icon-chevron-down`）
- 面板：`--surface-raised` 底 + `--elev-3`，圆角 `--r-md`，`padding: 6px`，最大高 320px 可滚
- 选项行：高 40px，圆角 `--r-xs`，`padding: 0 12px`，字号 `--fs-body`（14px，A-18：以权威表为准，不设 15px 档）
- **载荷不变（冻结项）**：替换后必须保留一个 `<input type="hidden">` 承载原 `name` / `value`，
  请求序列与载荷键集合逐条不变（`acceptance.md` G-1）

| 状态 | 触发器 | 面板 / 选项 |
|---|---|---|
| 默认 | `--surface-card` 底 + 1px `--rule-control`；箭头朝下 | 关闭 |
| hover | `border-color: var(--ink-disabled)` | 关闭 |
| active | `border-color: var(--ink-disabled)` | 关闭 |
| focus-visible | `border-color: var(--role-blue)`；`box-shadow: 0 0 0 3px var(--role-blue-wash)` | 关闭 |
| disabled | `--surface-base` 底；`color: var(--ink-disabled)`；箭头 `--ink-disabled` | 关闭 |
| loading | `aria-busy="true"`；右侧 12px 指示器替代箭头 | 关闭 |
| selected（当前值） | 文字 `--ink-strong` | 当前项：`background: var(--role-blue-wash)`；`color: var(--role-blue)`；**行尾 8px 蓝实心点**（冗余几何通道） |
| error | `border-color: var(--role-red)`；`box-shadow: 0 0 0 3px var(--role-red-wash)` | 关闭 |
| 面板打开 | 箭头旋转 180°，`transition: transform var(--dur-base)` | `--elev-3`；出现用「上浮 4px + 淡入」160ms |

- 角色色：默认 R0；选中项 R1（蓝）。
- **键盘**：`↑`/`↓` 移动、`Enter`/`Space` 选中、`Esc` 关闭并回焦触发器、输入字母前缀跳转、`Home`/`End`。
- **ARIA**：`role="combobox"` + `aria-expanded` + `aria-controls` + `aria-activedescendant`；
  面板 `role="listbox"`，项 `role="option"` + `aria-selected`。

```css
.lk-select { position: relative; }
.lk-select__trigger {
  display: flex; align-items: center; justify-content: space-between; gap: var(--sp-2);
  width: 100%; min-height: 44px; padding: 0 14px;
  border: 1px solid var(--rule-control); border-radius: var(--r-md);
  background: var(--surface-card); color: var(--ink-strong);
  font-family: var(--font-ui); font-size: var(--fs-body); text-align: left; cursor: pointer;
  transition: border-color var(--dur-fast) var(--ease-out),
              box-shadow var(--dur-fast) var(--ease-out);
}
.lk-select__trigger:hover:not(:disabled) { border-color: var(--ink-disabled); }
.lk-select__trigger:focus-visible { outline: 2px solid transparent; outline-offset: 2px;
  border-color: var(--role-blue); box-shadow: 0 0 0 3px var(--role-blue-soft); }
.lk-select__trigger:disabled { background: var(--surface-base); color: var(--ink-disabled); cursor: not-allowed; }
.lk-select__trigger svg { width: 16px; height: 16px; flex: none; fill: none; stroke: currentColor;
  stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;
  transition: transform var(--dur-base) var(--ease-out); }
.lk-select[data-open="true"] .lk-select__trigger svg { transform: rotate(180deg); }
.lk-select__panel {
  position: absolute; z-index: var(--z-dropdown); top: calc(100% + 6px); left: 0; min-width: 100%;
  max-height: 320px; overflow-y: auto; padding: 6px;
  background: var(--surface-raised); border-radius: var(--r-md);
  box-shadow: var(--elev-3);
  opacity: 0; transform: translateY(-4px); pointer-events: none;
  transition: opacity var(--dur-base) var(--ease-out),
              transform var(--dur-base) var(--ease-out);
}
.lk-select[data-open="true"] .lk-select__panel { opacity: 1; transform: translateY(0); pointer-events: auto; }
.lk-select__option {
  display: flex; align-items: center; justify-content: space-between; gap: var(--sp-2);
  min-height: 40px; padding: 0 12px; border-radius: var(--r-xs);
  font-family: var(--font-ui); font-size: var(--fs-body); color: var(--ink-strong);
  cursor: pointer;
}
.lk-select__option:hover, .lk-select__option[data-active="true"] { background: var(--veil-hover); }
.lk-select__option[aria-selected="true"] { background: var(--role-blue-wash); color: var(--role-blue); }
.lk-select__option[aria-selected="true"]::after {
  content: ""; width: 8px; height: 8px; border-radius: var(--r-pill);
  background: var(--role-blue); flex: none;
}
```

### 4.8 复选框（Checkbox）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **B 整行选中**（`check-row`）。选中时**整行**铺一层蓝洗底（不是只把方框染色）
> ⇒ 需要行级容器（`.lk-check__row`）；框本身仍走 spec 的几何。

**定位**：多选或二元开关。**点击目标应是整行标签**，不是 20px 的小方框。

- 方框：`20 × 20`，圆角 `--r-xs`（6px），边框 1.5px
- 命中区：伪元素扩到 44×44
- 勾号：本地 SVG `asset-icon-check`（16×16），`stroke: var(--ink-on-role)`
- 行高：命中区 ≥ 44px（`padding: 6px 0` + `min-height: 44px`）

| 状态 | 表现 |
|---|---|
| 默认 | `background: var(--surface-card)`；`border: 1.5px solid var(--ink-disabled)` |
| hover | `border-color: var(--role-blue)` |
| active | `border-color: var(--role-blue-press)`；`background: var(--role-blue-wash)` |
| focus-visible | 外层双环焦点环（蓝色，内环用纸面色） |
| disabled | `background: var(--surface-base)`；`border-color: var(--rule-control)`；`color: var(--ink-disabled)`；`cursor: not-allowed` |
| loading | 不适用 |
| checked | `background: var(--role-blue)`；`border-color: var(--role-blue)`；白勾；勾以 120ms 绘制出现 |
| indeterminate | `background: var(--role-blue)`；白色横杠（无勾） |
| error | `border-color: var(--role-red)`；`box-shadow: 0 0 0 3px var(--role-red-wash)` |

- 角色色：默认 R0；checked R1（蓝）。**红色仅用于 error，不用于 checked**。

```css
.lk-check { position: relative; display: inline-flex; align-items: center; gap: var(--sp-2);
  min-height: 44px; cursor: pointer; }
.lk-check__box {
  width: 20px; height: 20px; flex: none; border-radius: var(--r-xs);
  border: 1.5px solid var(--ink-disabled); background: var(--surface-card);
  display: inline-flex; align-items: center; justify-content: center;
  transition: background-color var(--dur-fast) var(--ease-out),
              border-color var(--dur-fast) var(--ease-out);
}
.lk-check__box::before { content: ""; position: absolute; width: 44px;
  height: 44px; }
.lk-check:hover .lk-check__box { border-color: var(--role-blue); }
.lk-check__box svg { width: 14px; height: 14px; fill: none; stroke: var(--ink-on-role);
  stroke-width: 3; stroke-linecap: round; stroke-linejoin: round;
  opacity: 0; transform: scale(.7);
  transition: opacity var(--dur-fast) var(--ease-out),
              transform var(--dur-fast) var(--ease-rebound); }
.lk-check input:checked + .lk-check__box,
.lk-check input[aria-checked="true"] + .lk-check__box { background: var(--role-blue); border-color: var(--role-blue); }
.lk-check input:checked + .lk-check__box svg { opacity: 1; transform: scale(1); }
.lk-check input:disabled + .lk-check__box { background: var(--surface-base); border-color: var(--rule-control); }
.lk-check:has(input:disabled) { cursor: not-allowed; color: var(--ink-disabled); }
.lk-check:has(input:focus-visible) .lk-check__box {
  outline: 2px solid transparent; outline-offset: 2px;
  box-shadow: 0 0 0 2px var(--surface-base), 0 0 0 4px var(--focus-outer); }
.lk-check--error .lk-check__box { border-color: var(--role-red); box-shadow: 0 0 0 3px var(--role-red-wash); }
```

```css
/* 半选（indeterminate）：蓝底 + 白色横杠，无勾 */
.lk-check input[aria-checked="mixed"] + .lk-check__box {
  background: var(--role-blue); border-color: var(--role-blue);
}
.lk-check input[aria-checked="mixed"] + .lk-check__box svg { display: none; }
.lk-check input[aria-checked="mixed"] + .lk-check__box::after {
  content: ""; width: 10px; height: 2px; border-radius: 1px; background: var(--ink-on-role);
}
/* 命中区：整行标签 ≥ 44px，小方框本身另补 44px 命中 */
.lk-check__row { display: flex; align-items: center; min-height: 44px; }
```

### 4.9 单选（Radio）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **B 整行卡选中**（`radio-row`）。选中时**整行蓝洗底 + 圆环内填** ⇒
> 选项读成「卡片」而不是「控件」。

**定位**：一组互斥选项（选一个）。选项容器是 `fieldset` + `legend`。

- 圆：`20 × 20`，圆角 `--r-round`，边框 1.5px
- 选中表现：**蓝实心圆 + 白色内核点**（6px），与复选框的方框在几何上区分
- 行高：命中区 ≥ 44px

| 状态 | 表现 |
|---|---|
| 默认 | `background: var(--surface-card)`；`border: 1.5px solid var(--ink-disabled)` |
| hover | `border-color: var(--role-blue)` |
| active | `border-color: var(--role-blue-press)` |
| focus-visible | 双环焦点环 |
| disabled | `--surface-base` 底；`border-color: var(--rule-control)`；`color: var(--ink-disabled)` |
| loading | 不适用 |
| checked | `background: var(--role-blue)`；`border-color: var(--role-blue)`；中心 6px 白点，`transform: scale` 从 .6 弹到 1（`--ease-rebound`） |
| error | `border-color: var(--role-red)`；`box-shadow: 0 0 0 3px var(--role-red-wash)` |

- 角色色：默认 R0；checked R1（蓝）。

```css
.lk-radio { position: relative; display: inline-flex; align-items: center; gap: var(--sp-2);
  min-height: 44px; cursor: pointer; }
.lk-radio__dot {
  width: 20px; height: 20px; flex: none; border-radius: var(--r-round);
  border: 1.5px solid var(--ink-disabled); background: var(--surface-card);
  display: inline-flex; align-items: center; justify-content: center;
  transition: background-color var(--dur-fast) var(--ease-out),
              border-color var(--dur-fast) var(--ease-out);
}
.lk-radio__dot::before { content: ""; position: absolute; width: 44px;
  height: 44px; }
.lk-radio:hover .lk-radio__dot { border-color: var(--role-blue); }
.lk-radio__dot::after {
  content: ""; width: 6px; height: 6px; border-radius: var(--r-pill);
  background: var(--ink-on-role); opacity: 0; transform: scale(.6);
  transition: opacity var(--dur-fast) var(--ease-out),
              transform var(--dur-fast) var(--ease-rebound);
}
.lk-radio input:checked + .lk-radio__dot,
.lk-radio input[aria-checked="true"] + .lk-radio__dot { background: var(--role-blue); border-color: var(--role-blue); }
.lk-radio input:checked + .lk-radio__dot::after,
.lk-radio input[aria-checked="true"] + .lk-radio__dot::after { opacity: 1; transform: scale(1); }
.lk-radio input:disabled + .lk-radio__dot { background: var(--surface-base); border-color: var(--rule-control); }
.lk-radio:has(input:disabled) { cursor: not-allowed; color: var(--ink-disabled); }
.lk-radio:has(input:focus-visible) .lk-radio__dot {
  outline: 2px solid transparent; outline-offset: 2px;
  box-shadow: 0 0 0 2px var(--surface-base), 0 0 0 4px var(--focus-outer); }
.lk-radio--error .lk-radio__dot { border-color: var(--role-red); box-shadow: 0 0 0 3px var(--role-red-wash); }
```

```css
/* 单选组：fieldset 无框，legend 作组名 */
.lk-choicegroup { border: 0; margin: 0; padding: 0; }
.lk-choicegroup > legend { padding: 0 0 var(--sp-2); color: var(--ink-muted);
  font-family: var(--font-ui); font-size: var(--fs-meta); }
/* 选项行：整行可点，命中区 ≥ 44px */
.lk-choicegroup .lk-radio { display: flex; width: 100%; padding: var(--sp-2) var(--sp-3);
  border-radius: var(--r-md); }
.lk-choicegroup .lk-radio:hover { background: var(--veil-hover); }
```

### 4.10 开关（Switch）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **B 迷你开关**（`switch-mini`）。轨道 **32×18**；**命中区另补**（伪元素撑到 ≥44px）。
> 关态墨色仍走 `--ink-disabled`（**A-84 第 4 条不变**）。

**定位**：**立即生效**的二元设置（主题 / 动效 / 声音 / 章节透镜 / 显示自评）。
**与复选框的区别**：开关 = 立即生效且视觉上「开/关」；复选框 = 随表单提交。
设置视图里的四个偏好（主题 / 阅读字面 / 动效 / 声音）里，**主题、动效、声音用开关**，
**阅读字面用分段控件**（二选一，不是开/关）。

- 轨道：`44 × 26`，圆角 `--r-pill`（**胶囊**；用 `--r-round` 50% 会得到 22×13 的椭圆角）
- 滑块：`20 × 20` 圆形，白底 + `--elev-1`，`translateX(4px → 20px)`
- 命中区：整行 ≥ 44px（`min-height: 44px`），轨道本体 26px 不单独算命中区

| 状态 | 表现 |
|---|---|
| 默认（关） | `background: var(--ink-disabled)`；滑块 `translateX(4px)`；`transition 160ms` |
| hover | 关态 `background: var(--ink-faint)`；开态 `--role-blue-press` |
| active | 滑块 `scale(.94)` |
| focus-visible | 轨道上双环焦点环（内环用纸面色） |
| disabled | `background: var(--veil-active)`；滑块 `background: var(--surface-card)`；`opacity: .7`；`cursor: not-allowed` |
| loading | 不适用；异步保存时在轨道右侧显示 12px 指示器并 `aria-busy="true"` |
| 开（on） | `background: var(--role-blue)`；滑块 `translateX(20px)` |
| error | 不适用（开关无错误语义）；设置保存失败由行内错误条承担 |

- 角色色：**蓝**（开态），R1。关态是中性墨，不是第四色。

```css
.lk-switch { position: relative; display: inline-flex; align-items: center;
  min-height: 44px; cursor: pointer; }
.lk-switch__track {
  width: 44px; height: 26px; flex: none; border-radius: var(--r-pill);
  background: var(--ink-disabled); padding: 3px;
  transition: background-color var(--dur-base) var(--ease-out);
}
.lk-switch__thumb {
  width: 20px; height: 20px; border-radius: var(--r-round);
  background: var(--surface-card); box-shadow: var(--elev-1);
  transform: translateX(0);
  transition: transform var(--dur-base) var(--ease-rebound);
}
.lk-switch input:checked + .lk-switch__track { background: var(--role-blue); }
.lk-switch input:checked + .lk-switch__track .lk-switch__thumb { transform: translateX(18px); }
.lk-switch:hover input:not(:disabled) + .lk-switch__track { filter: brightness(.96); }
.lk-switch input:focus-visible + .lk-switch__track {
  outline: 2px solid transparent; outline-offset: 2px;
  box-shadow: 0 0 0 2px var(--surface-base), 0 0 0 4px var(--focus-outer); }
.lk-switch input:disabled + .lk-switch__track { background: var(--veil-active); }
.lk-switch:has(input:disabled) { cursor: not-allowed; }
```

### 4.11 分段控件（Segmented control）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **C 药丸分段**（`seg-pill`）。整组一个**胶囊槽**；**选中项是白色药丸**
> （`--surface-raised`）⇒ ⚠️ **选中项不用角色蓝**（回答 **A-84 第 2 条**），
> 与 A-31「沉底面旁不得挨蓝洗底」一致。

**定位**：**互斥但可见全貌**的 2–4 个选项（阅读字面：衬线 / 无衬线；自评 1–5；
难度档位）。**超过 4 项不用分段控件**，改用自绘下拉。

- 容器：内联 flex，`background: var(--surface-base)`，圆角 `--r-md`（12px），`padding: 4px`，`gap: 4px`
- 项：高 36px，圆角 `--r-xs`（6px），`padding: 0 14px`，字号 `--fs-meta`（13px）/ 600
- 命中区：容器高 = 36 + 8 = 44px，项本身 36px → **项内命中区用伪元素补到 44 高会溢出容器**，
  因此分段控件**整体**保证 44px 高（项高 40 + padding 4 + padding 4 = 48 容器高，取 44），
  项高 36 + 上下 padding 4 = 44 ✔

| 状态 | 表现 |
|---|---|
| 默认 | 容器 `--surface-base`；项 `background: transparent`；`color: var(--ink-muted)` |
| hover | 项 `color: var(--ink-strong)`；`background: var(--veil-hover)` |
| active | 项 `background: var(--veil-active)` |
| focus-visible | 当前项双环焦点环（roving tabindex，只有当前项可聚焦） |
| disabled | 整组 `opacity: .6`；项 `cursor: not-allowed` |
| loading | 不适用 |
| selected | 项 `background: var(--surface-raised)`；`color: var(--ink-strong)`；`box-shadow: var(--elev-1)`；`font-weight: 600`；**若该分段承载角色语义（如连对档位），选中项底色改 `--role-yellow-soft` 且字取 `--ink-strong`** |
| error | 整组外框 `box-shadow: 0 0 0 3px var(--role-red-wash)`（`aria-invalid`） |

- 角色色：默认 R0；selected R1（蓝），语义型 selected 可用黄洗底（仍为 R1）。
- **键盘**：`←`/`→`/`Home`/`End` 移动并**立即选中**（roving tabindex），`Space` 选中。
- **ARIA**：`role="radiogroup"` + 每项 `role="radio"` + `aria-checked`。

```css
.lk-seg { display: inline-flex; gap: 4px; padding: 4px; border-radius: var(--r-md);
  background: var(--surface-base); }
.lk-seg__item {
  min-height: 36px; padding: 0 14px; border: 0; border-radius: var(--r-xs);
  background: transparent; color: var(--ink-muted);
  font-family: var(--font-ui); font-size: var(--fs-meta); font-weight: 500;
  cursor: pointer; white-space: nowrap;
  transition: background-color var(--dur-fast) var(--ease-out),
              color var(--dur-fast) var(--ease-out),
              box-shadow var(--dur-fast) var(--ease-out);
}
.lk-seg__item:hover:not(:disabled) { color: var(--ink-strong); background: var(--veil-hover); }
.lk-seg__item[aria-checked="true"], .lk-seg__item[aria-selected="true"] {
  background: var(--surface-raised); color: var(--ink-strong); font-weight: 600;
  box-shadow: var(--elev-1); }
.lk-seg__item:focus-visible { outline: 2px solid transparent; outline-offset: 2px;
  box-shadow: 0 0 0 2px var(--surface-base), 0 0 0 4px var(--focus-outer); }
.lk-seg__item:disabled { color: var(--ink-disabled); cursor: not-allowed; }
.lk-seg[aria-invalid="true"] { box-shadow: 0 0 0 3px var(--role-red-wash); }
```

```css
/* 语义型分段（承载角色色，如连对档位 / 复习轮次）：选中项用角色洗底 */
.lk-seg--semantic .lk-seg__item[aria-checked="true"] {
  background: var(--role-yellow-soft); color: var(--ink-on-warm);
  box-shadow: inset 0 0 0 2px var(--role-yellow); }
.lk-seg--semantic .lk-seg__item[aria-checked="true"]::before {
  content: ""; width: 8px; height: 8px; border-radius: var(--r-pill);
  background: var(--role-yellow); flex: none; }
/* 横向可滚形态（记录中心筛选 chip） */
.lk-seg--scroll { overflow-x: auto; scrollbar-width: none; max-width: 100%; }
.lk-seg--scroll::-webkit-scrollbar { display: none; }
```

### 4.12 标签（Tag / Chip）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **C 角色色标签**（`tag-role`）。**角色色洗底 + 左侧状态点**（蓝 / 黄 / 红三变体）；
> 黄**不承载文字**（权威表 §3.4）；同一张卡上的语义标签 **≤2 个**。
> ⚠️ 新标签**不许复用 `.chip`**（A-78 的命名口径不变）。

**定位**：**静态**的分类或属性标记（章节名、状态名、难度）。**不可点击**。
可点击的应改用次按钮或文字按钮。

- 高 24px（大号 28px），圆角 `--r-md`（12px）
- 内外边距：`padding: 0 10px`（大号 `0 12px`）
- 字族字号：`--font-ui` / `--fs-label`（12px）/ `font-weight: 500`
- 图标（可选）：12×12 本地 SVG，`gap: 4px`

| 状态 | 表现 |
|---|---|
| 默认（中性） | `background: var(--veil-hover)`；`color: var(--ink-muted)` |
| hover / active | **不适用**（静态元素） |
| focus-visible | 不适用；若标签内含链接，焦点环落在链接上 |
| disabled | 不适用 |
| loading | 不适用 |
| selected | `background: var(--role-blue-wash)`；`color: var(--role-blue)` |
| 语义变体 · 蓝 | `background: var(--role-blue-wash)`；`color: var(--role-blue)` |
| 语义变体 · 黄 | `background: var(--role-yellow-soft)`；`color: var(--ink-on-warm)`（**黄不承载文字**） |
| 语义变体 · 红 | `background: var(--role-red-wash)`；`color: var(--role-red-ink)` |
| error | 语义变体 · 红（错误态标签用红洗底 + 红字） |

- 角色色：中性 R0；每个语义变体 R1。**同一张卡上的语义标签不超过 2 个**。

```css
.lk-tag {
  display: inline-flex; align-items: center; gap: 4px;
  min-height: 24px; padding: 0 10px; border-radius: var(--r-md);
  background: var(--veil-hover); color: var(--ink-muted);
  font-family: var(--font-ui); font-size: var(--fs-label); font-weight: 500;
  white-space: nowrap;
}
.lk-tag--blue { background: var(--role-blue-wash); color: var(--role-blue); }
.lk-tag--yellow { background: var(--role-yellow-soft); color: var(--ink-on-warm); }
.lk-tag--red { background: var(--role-red-wash); color: var(--role-red-ink); }
.lk-tag svg { width: 12px; height: 12px; fill: none; stroke: currentColor;
  stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
```

```css
/* 选中态标签 + 大号变体 + 带状态点的标签 */
.lk-tag--selected { background: var(--role-blue-wash); color: var(--role-blue); }
.lk-tag--lg { min-height: 28px; padding: 0 12px; font-size: var(--fs-meta); }
.lk-tag__dot { width: 8px; height: 8px; border-radius: var(--r-pill); flex: none; }
```

### 4.13 徽标（Badge）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **B 胶囊计数**（`badge-pill`）。**胶囊轮廓 + 沉底实心**（比实心圆安静）；11px 字。

**定位**：**计数**徽标，附着在图标 / 按钮 / Tab 角上（待办数、阻塞数）。
与标签的区别：徽标**只装数字**，且形状是圆 / 圆角方。

- 尺寸：最小 `20 × 20`（半径 `--r-round`），计数 ≥ 100 时显示 `99+`
- 内外边距：`padding: 0 6px`（两位数以上改圆角方 `--r-xs`）
- 字族字号：`--font-ui` / `--fs-label`（12px）/ `font-weight: 700` / `tabular-nums`

| 状态 | 表现 |
|---|---|
| 默认 | `background: var(--surface-sunken)`；`color: var(--ink-strong)`（中性计数，如未读）。**A-23**：不再用近黑墨块 |
| hover / active | 不适用 |
| focus-visible | 不适用（徽标本身不可聚焦） |
| disabled | 不适用 |
| loading | 不适用 |
| selected | 不适用 |
| 阻塞 / 失败计数 | `background: var(--role-red)`；`color: var(--ink-on-role)`（夜纸下 `--ink-on-role` = 墨色） |
| error | 同「阻塞 / 失败计数」 |

- 角色色：**红**（阻塞计数）R1；中性计数 R0。**蓝与黄不做徽标色**——蓝已被「当前选中」占用，
  黄已被「内容层当前」占用，重复使用会让状态解码失效。

```css
.lk-badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 20px; height: 20px; padding: 0 6px;
  border-radius: var(--r-round); background: var(--surface-sunken); color: var(--ink-strong);
  font-family: var(--font-ui); font-size: var(--fs-label); font-weight: 700;
  font-variant-numeric: tabular-nums; line-height: 1;
}
.lk-badge--alert { background: var(--role-red); color: var(--ink-on-role); }
```

### 4.14 状态圆点（Status dot）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **A spec 全几何集**（`dot-spec`）。按 §3.6 的几何集 + §4.14 的映射补齐现状缺的
> **ring / half / filled** 三档；**尺寸收到 10px**（它不是可点目标，命中区不受影响）。

**定位**：**冗余状态通道**的载体。零文字、零标签。**只表达状态，不表达数量**。

- 尺寸：`10 × 10`（密集列表 8px，强调位置 12px）
- 圆角：`--r-pill`（圆点用胶囊档，不用 `--r-round` —— 权威表 §2.1）
- 几何集与映射：见 §3.6（`filled` / `ring` / `half` / `dash` / `cross` / `check`）
- **不得**单独出现无颜色差异的灰点以外的中性点以外的无意义点

| 状态 | 表现（色 / 几何） |
|---|---|
| 未开始 / 待办 | `--ink-disabled` / `ring` |
| 当前 · 交互层 | `--role-blue` / `ring` |
| 进行中 | `--role-blue` / `half` |
| 已完成 / 通过（流程进度） | `--role-blue` / `filled` |
| 当前 · 内容层 | `--role-yellow` / `filled` |
| 到期 / 需复习 | `--role-yellow` / `dash` |
| 判定正确 / 答对 | `--ink-strong` / `check`（墨色勾形；**不用绿、不用蓝**，见 §3.6 的 A-20-3 说明） |
| 失败 / 错误 | `--role-red` / `filled` |
| 阻塞 / 卡住 | `--role-red` / `cross` |
| hover | 不适用（装饰性状态点不响应指针） |
| focus-visible | 不适用 |
| disabled | 宿主元素禁用时点降到 `--ink-disabled` 且不改变几何（几何仍可辨） |
| loading | 进行中（`half`） |
| selected | 随宿主选中态切换到对应几何 |
| error | 见「失败 / 错误」 |

- 角色色：每点 R1。
- **ARIA**：状态点是 `aria-hidden="true"` 的装饰；状态语义由宿主元素的
  `aria-label` / `aria-current` / `aria-disabled` 承担。**状态点本身不带文字**。

```css
.lk-dot {
  --_dot-color: var(--ink-disabled);
  width: 10px; height: 10px; flex: none; border-radius: var(--r-pill);
  background: transparent; box-shadow: inset 0 0 0 2px var(--_dot-color);
}
.lk-dot--filled { background: var(--_dot-color); box-shadow: none; }
.lk-dot--half { box-shadow: inset -5px 0 0 0 var(--_dot-color); }
.lk-dot--dash {
  background: transparent; box-shadow: none;
  border-top: 2px solid var(--_dot-color); border-radius: 0;
  transform: rotate(45deg) scale(.7);
}
.lk-dot--cross {
  background: transparent; box-shadow: none; border-radius: 0;
  position: relative;
}
.lk-dot--cross::before, .lk-dot--cross::after {
  content: ""; position: absolute; inset: 50% 0 auto 0; height: 2px;
  background: var(--_dot-color); transform: translateY(-50%) rotate(45deg);
}
.lk-dot--cross::after { transform: translateY(-50%) rotate(-45deg); }
/* 勾形（判定正确 / 答对）：左短下斜 + 右长上斜，仍是 CSS 绘制，不引图标字体 */
.lk-dot--check {
  background: transparent; box-shadow: none; border-radius: 0;
  position: relative;
}
.lk-dot--check::before, .lk-dot--check::after {
  content: ""; position: absolute; left: 0; top: 0; height: 2px;
  border-radius: 1px; background: var(--_dot-color); transform-origin: 0 50%;
}
.lk-dot--check::before { width: 4px; left: 1px; top: 6px; transform: rotate(45deg); }
.lk-dot--check::after { width: 8px; left: 3px; top: 8px; transform: rotate(-45deg); }
.lk-dot--blue { --_dot-color: var(--role-blue); }
.lk-dot--yellow { --_dot-color: var(--role-yellow); }
.lk-dot--red { --_dot-color: var(--role-red); }
.lk-dot--ink { --_dot-color: var(--ink-strong); }
.lk-dot--muted { --_dot-color: var(--ink-disabled); }
```

```css
/* 尺寸变体：密集列表 8px / 强调位 12px */
.lk-dot--sm { width: 8px; height: 8px; }
.lk-dot--lg { width: 12px; height: 12px; }
/* 承载在纸面上的点：加一圈纸色垫，避免与背景同色糊在一起 */
.lk-dot--on-paper { box-shadow: 0 0 0 2px var(--surface-card), inset 0 0 0 2px var(--_dot-color); }
.lk-dot--filled.lk-dot--on-paper { box-shadow: 0 0 0 2px var(--surface-card); }
/* 点在暗底上：垫圈改墨色 */
.lk-dot--on-ink { box-shadow: 0 0 0 2px var(--ink-strong), inset 0 0 0 2px var(--_dot-color); }
```

### 4.15 进度条（Progress bar）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **A 胶囊进度**（`progress-pill`）。轨道 `--veil-active` · 填充角色蓝 · **8px 胶囊**
> （`border-radius: 999px`）。

**定位**：**单一**连续量的完成度（练习进度、目标进度、复习负荷）。

- 轨道：高 8px（大号 12px），圆角 `--r-pill`（胶囊），`background: var(--veil-active)`
- 填充：同高，圆角继承，`background: var(--role-blue)`
- 宽度：`100%` 容器；`padding: 0`；无内外边距（外层容器负责）

| 状态 | 表现 |
|---|---|
| 默认 | 填充宽度 = 当前百分比；`transition: width var(--dur-base) var(--ease-out)` |
| hover / active | 不适用（静态展示） |
| focus-visible | 不适用；若进度条可点击跳转，加 `role="link"` + 焦点环 |
| disabled | 轨道 `opacity: .5` |
| loading | **不确定态**：轨道上跑一段 32% 宽的滑块，`1.2s linear infinite` |
| selected | 不适用 |
| error | 填充改 `--role-red`（失败态进度，如批改未通过） |
| 语义变体 · 连对 / 复习 | 填充改 `--role-yellow`（黄不承载文字，此处是纯面积 ✔） |

- 角色色：R1（蓝或黄，二选一，不混用）。

```css
.lk-progress { width: 100%; height: 8px; border-radius: var(--r-pill);
  background: var(--veil-active); overflow: hidden; }
.lk-progress__fill { display: block; height: 100%; width: 0; border-radius: inherit;
  background: var(--role-blue);
  transition: width var(--dur-base) var(--ease-out); }
.lk-progress--yellow .lk-progress__fill { background: var(--role-yellow); }
.lk-progress--error .lk-progress__fill { background: var(--role-red); }
.lk-progress--indeterminate .lk-progress__fill {
  width: 32%; animation: lk-indeterminate 1.2s var(--ease-standard) infinite; }
@keyframes lk-indeterminate {
  0% { transform: translateX(-100%); } 100% { transform: translateX(312%); } }
```

### 4.16 分段进度条（Segmented progress）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **B 编号点串**（`steps-num`）。⚠️ **本条属 B 类** —— 产品里**没有**这个界面 ⇒
> **先改 OpenSpec**。形态：编号圆点 + 连接线（「第几轮」一眼可数）。

**定位**：**离散**步数的完成度（连对计数、复习轮次、目标里程碑）。
用**颜色 + 几何双编码**，让「已完成 / 当前 / 未开始」不依赖颜色。

- 段：高 8px（大号 12px），圆角 `--r-pill`（胶囊），`gap: 4px`
- 段宽：`flex: 1`，最小 12px；总宽 100%
- 几何：已完成 = `filled`；当前 = `half`；未开始 = `ring`（2px 环）

| 状态 | 表现 |
|---|---|
| 未开始 | `background: transparent`；`box-shadow: inset 0 0 0 2px var(--veil-active)` |
| 进行中（当前段） | `background: var(--veil-active)`；`box-shadow: inset -50% 0 0 0 var(--role-yellow)`（半填充） |
| 已完成 | `background: var(--role-yellow)`（连对语义）或 `var(--role-blue)`（通用语义） |
| 失败 | 该段 `background: var(--role-red)`（连对中断） |
| hover / active | 不适用 |
| focus-visible | 容器可聚焦时（`tabindex="0"` + `role="progressbar"`）给双环焦点环 |
| disabled | `opacity: .5` |
| loading | 不适用 |
| selected | 不适用 |

- 角色色：R1（黄或蓝二选一）。**失败段额外引入红**，属于 R2 上限内的例外：
  连对中断是**唯一**允许同时出现黄与红的组件。

```css
.lk-steps { display: flex; gap: 4px; width: 100%; }
.lk-steps__seg { flex: 1; min-width: 12px; height: 8px; border-radius: var(--r-pill);
  background: transparent; box-shadow: inset 0 0 0 2px var(--veil-active); }
.lk-steps__seg--done { background: var(--role-yellow); box-shadow: none; }
.lk-steps__seg--current { background: var(--veil-active);
  box-shadow: inset -50% 0 0 0 var(--role-yellow); }
.lk-steps__seg--failed { background: var(--role-red); box-shadow: none; }
.lk-steps--blue .lk-steps__seg--done { background: var(--role-blue); }
```

### 4.17 题号格（Question cell）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **A spec 形态**（`qcell-spec`）。**36px 方 + 12px 圆角** + 六态
> （未答 / 已答 / 当前 / 正确 / 错误 / 卡住）。⚠️ 旧的 34px **圆形**作废；
> 「当前」用**黄实心**（不是 outline）。§3.1 的「36px + 间隙 8px = 44px 步距」正好对上。

**定位**：练习 / 试卷的**题号导航格**（现状 `.paper-dot`，`workbench.css:1888-1894`）。
每格 = 一道题，点击跳转。

- 视觉尺寸：`36 × 36`，圆角 `--r-md`（12px）
- 命中区：格 + 8px 间隙 = **44px 步距** ✔
- 内外边距：`padding: 0`
- 字族字号：`--font-mono`（编号等宽）/ `--fs-meta`（13px）/ `font-weight: 600` / `tabular-nums`
- 现状是 34px 圆 + 1px 描边 + 5 个硬编码色（`#f2c94c` / `#dce7ff` / `#d9ebdd` / `#f6d8d5`）→ 全部换成 §3.6 状态映射
  （其中 `#d9ebdd` + `#245d32`（`workbench.css:1892` `.paper-dot.state-correct`）是**契约外绿**，
  本轮随 A-20-3 退役：**答对改中性墨 `--ink-strong` + 勾形几何**，不设绿 token）

| 状态 | 色 / 几何 |
|---|---|
| 未作答 | `--ink-disabled` / `ring`（`background: var(--surface-card)`，2px 环） |
| 已作答 | `--role-blue` / `filled` |
| 当前题 | `--role-yellow` / `filled`；`transform: scale(1.06)`（120ms 回弹） |
| 判定正确 | `--ink-strong` / `check`（墨色环 + 勾形标记；**不用绿、不用蓝**，见 §3.6 的 A-20-3 说明） |
| 判定错误 | `--role-red` / `filled` |
| 卡住 / 阻塞 | `--role-red` / `cross` |
| hover | 未作答态 `border-color: var(--role-blue)`；已填态 `filter: brightness(1.06)` |
| active | `transform: scale(.94)` |
| focus-visible | 双环焦点环，内环用纸面色 |
| disabled | `opacity: .45` |
| loading | 不适用 |
| selected | = 「当前题」（黄实心）；交互层语义由 `aria-current="step"` 标注 |
| error | 判定错误即 error（红实心） |

- 角色色：R1。
- **几何不只靠颜色**：未答（环）与已答（实心）在灰度打印 / 色觉障碍下仍可区分；
  判定正确（墨环 + 勾）与判定错误（红面 + 叉）同样可区分。
- **判定正确不替换题号**：它是**导航格**，题号必须始终可读 —— 判定态用
  「中性墨环 + 角标勾形」叠加表达，**不**把数字换成符号（与 §3.6 的勾形通道一致）。

```css
.lk-qcell {
  width: 36px; height: 36px; min-width: 36px; padding: 0;
  border: 0; border-radius: var(--r-md); cursor: pointer;
  display: inline-flex; align-items: center; justify-content: center;
  background: var(--surface-card); color: var(--ink-muted);
  box-shadow: inset 0 0 0 2px var(--ink-disabled);
  font-family: var(--font-mono); font-size: var(--fs-meta); font-weight: 600;
  font-variant-numeric: tabular-nums;
  transition: transform var(--dur-fast) var(--ease-rebound),
              box-shadow var(--dur-fast) var(--ease-out),
              background-color var(--dur-fast) var(--ease-out);
}
.lk-qcell:hover:not(:disabled) { box-shadow: inset 0 0 0 2px var(--role-blue); color: var(--ink-strong); }
.lk-qcell:active:not(:disabled) { transform: scale(.94); }
.lk-qcell:focus-visible { outline: 2px solid transparent; outline-offset: 2px;
  box-shadow: 0 0 0 2px var(--surface-base), 0 0 0 4px var(--focus-outer); }
.lk-qcell--answered { background: var(--role-blue); color: var(--ink-on-role); box-shadow: none; }
/* 判定正确：题号保留（中性墨）+ 中性墨环 + 角标勾形（不用绿、不用蓝） */
.lk-qcell--correct {
  background: var(--surface-card); color: var(--ink-strong);
  box-shadow: inset 0 0 0 2px var(--ink-strong); position: relative;
}
.lk-qcell--correct::before, .lk-qcell--correct::after {
  content: ""; position: absolute; height: 2px; border-radius: 1px;
  background: var(--ink-strong); transform-origin: 0 50%;
}
.lk-qcell--correct::before { width: 6px; left: 21px; top: 24px; transform: rotate(45deg); }
.lk-qcell--correct::after { width: 12px; left: 25px; top: 28px; transform: rotate(-45deg); }
.lk-qcell--current { background: var(--role-yellow); color: var(--ink-on-warm); box-shadow: none;
  transform: scale(1.06); }
.lk-qcell--wrong { background: var(--role-red); color: var(--ink-on-role); box-shadow: none; }
.lk-qcell--stuck { background: var(--surface-card); color: var(--role-red); box-shadow: inset 0 0 0 2px var(--role-red); }
.lk-qcell:disabled { opacity: .45; cursor: not-allowed; }
```

```css
/* 题号格容器：36px 格 + 8px 间隙 = 44px 步距（命中区达标） */
.lk-qgrid { display: flex; flex-wrap: wrap; gap: var(--sp-2); }
.lk-qgrid__legend { display: flex; flex-wrap: wrap; gap: var(--sp-3);
  margin-top: var(--sp-2); font-size: var(--fs-label); color: var(--ink-faint); }
.lk-qgrid__legend > span { display: inline-flex; align-items: center; gap: 4px; }
```

### 4.18 卡片（Card）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **A spec 留白**（`card-spec`）。留白 **24px**（`--sp-5`）；12px 圆角 + `--elev-1` 柔影
> + 无描边（不变）。

**定位**：内容分组的基本单元（知识点分组卡、试卷卡、记录卡片流、Agent 消息卡）。

- 圆角：`--r-md`（12px）
- 内外边距：`padding: var(--sp-5)`（24px）；紧凑卡 `16px`（`--sp-4`）；宽松卡 `32px`（`--sp-6`）
- 背景：L1 `--surface-card`；`box-shadow: var(--elev-1)`；**无描边**
- 字号：标题 `--fs-title`（18px）/ 600；正文 `--fs-body`（14px）；计数 `--fs-meta`（13px）

| 状态 | 表现 |
|---|---|
| 默认 | `--surface-card` 底 + `--elev-1`；`border: 0` |
| hover（可点击卡） | `transform: translateY(-2px)`；`box-shadow: var(--elev-2)`；160ms |
| active（可点击卡） | `transform: translateY(0)`；`box-shadow: var(--elev-1)` |
| focus-visible | 双环焦点环，内环 `--surface-card`（卡在 `--surface-base` 上时内环改 `--surface-base`） |
| disabled | `opacity: .6`；`box-shadow: none` |
| loading | 卡片内换成骨架屏（§4.22），卡片本体保持高度 |
| selected | `box-shadow: var(--elev-1), inset 0 0 0 2px var(--role-blue)`；**内环是 2px 蓝，不是描边**；`aria-selected="true"` |
| error | 顶部 3px 红条？→ **不用条**：改用左上角 10px 红状态点（§4.14）+ 卡内行内错误文案 |

- 角色色：默认 R0；selected R1（蓝）+ 可选状态点 1 色 → R2。

```css
.lk-card {
  background: var(--surface-card); border: 0; border-radius: var(--r-md);
  box-shadow: var(--elev-1); padding: var(--sp-5); color: var(--ink-strong);
  transition: transform var(--dur-base) var(--ease-out),
              box-shadow var(--dur-base) var(--ease-out);
}
.lk-card--interactive { cursor: pointer; }
.lk-card--interactive:hover { transform: translateY(-2px); box-shadow: var(--elev-2); }
.lk-card--interactive:active { transform: translateY(0); box-shadow: var(--elev-1); }
.lk-card:focus-visible { outline: 2px solid transparent; outline-offset: 2px;
  box-shadow: 0 0 0 2px var(--surface-base), 0 0 0 4px var(--focus-outer); }
.lk-card[aria-selected="true"] { box-shadow: var(--elev-1), inset 0 0 0 2px var(--role-blue); }
.lk-card:disabled, .lk-card[aria-disabled="true"] { opacity: .6; box-shadow: none; }
```

### 4.19 纸面层级（Paper level · 4 层）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **A spec 四层**（`surface-spec`）。底 / 卡 / 浮起 / 沉底四层，靠**圆角 + 柔影 +
> 内发丝线**分层（spec §4.19）。

**定位**：全站表面分层的唯一规则来源。相邻两级靠**圆角 + 柔影**拉开，
**不用描边、不用背景图案、不用渐变**。

| 级别 | 名称 | token | 典型用途 | 圆角 | 阴影 |
|---|---|---|---|---|---|
| L0 | 底 | `--surface-base` | 页面底、左栏 / 中栏 / 右栏底 | — | 无 |
| L1 | 卡 | `--surface-card` | 卡片、输入框、下拉触发器、列表行、内层面板 | 12px | `--elev-1` |
| L2 | 浮起 | `--surface-raised` | 下拉面板、吐司、对话框、悬浮条、hover 抬起的次按钮 | 12px | `--elev-3` |
| L3 | **沉底** | `--surface-sunken` | **内容块**：作答区、用户消息、题号大字块、连对计数器底、强调引文 | 12px | 无（**凹层**）+ 1px 内发丝线 |

> **A-23（2026-10-22）**：L3 由「**墨块**」改为「**沉底**」——
> 近黑深底退出内容块，该 token **更名为 `--surface-code`**（语义 = 仅代码块 / 等宽代码区反白面，
> 取值不变，**不再是一层纸面**）。L3 沉底 = 浅底深字（浅 #f2ece1 / 夜 #272319）。
> ⚠️ L3 是**凹层**：它**不抬升**（无 `--elev-*`），边界靠「**底色差 + 1px 内发丝线**」
> 与 L1 卡面分开（权威表 §3.1【A-23-3】/ §6.3 例外 4）。

- 状态：

| 状态 | 表现 |
|---|---|
| 默认 | 上表取值 |
| hover | 面**不变**，靠内部元素反馈；可点击面整体 `translateY(-2px)` + 升一级阴影 |
| active | `translateY(0)` + 回落一级阴影 |
| focus-visible | 双环焦点环，内环取该面的纸色 |
| disabled | `opacity: .6`（沉底降到 `--ink-muted`） |
| loading | 保持面的尺寸，内容换骨架屏 |
| selected | 内环 2px 蓝（`inset 0 0 0 2px var(--role-blue)`），**不加边框** |
| error | 面不变，加红状态点 |

- 角色色：R0（面本身不带角色色）。
- **深浅差异**：夜纸下 L0 `#1c1a16` → L1 `#232019` → L2 `#2b2620` 逐级提亮，
  **L3 沉底 `#272319` 取卡与浮起的中点（比卡面略亮 +1.49、比浮起略暗 −1.66）**——
  A-23 要求夜纸**反向**（沉底比卡面略亮 + 浅墨字）；
  阴影改为**更深的不透明黑**（因为夜纸底色已深，暖调柔影不可见）。
  ⚠️ 夜纸的沉底与卡面**底色差只有 ΔL\* 1.49** → **必须靠内发丝线兜底**，不得省。

```css
.lk-surface-0 { background: var(--surface-base); }
.lk-surface-1 { background: var(--surface-card); border-radius: var(--r-md);
  box-shadow: var(--elev-1); }
.lk-surface-2 { background: var(--surface-raised); border-radius: var(--r-md);
  box-shadow: var(--elev-3); }
/* L3 = 沉底：凹层，不抬升；文字是墨字（不是反白） */
.lk-surface-3 { background: var(--surface-sunken); color: var(--ink-strong);
  border-radius: var(--r-md); box-shadow: inset 0 0 0 1px var(--rule-hair); }
```

```css
/* 相邻层差的唯一实现：只靠圆角 + 柔影，不加描边、不加图案 */
.lk-surface-1 { box-shadow: var(--elev-1); }
.lk-surface-2 { box-shadow: var(--elev-3); }
/* 浮起层在夜纸下改用更深的墨色垫圈，避免与 L1 糊在一起 */
[data-theme="night"] .lk-surface-2 { box-shadow: 0 0 0 1px var(--rule-hair), var(--elev-3); }
```

### 4.20 沉底块（Sunken block）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **C 竖线沉底**（`sunken-rail`）。**沉底面 + 左侧 4px 黄竖线**；黄**只承载面积、
> 不承载文字**（权威表 §3.4）。借用「单侧结构线」语言；
> `.msg.user` 同一形态（**A-23 的沉底面不变**，竖线是面左的一条线）。

**定位**：**最强的一层强调**（凹层）。用于：题面里的大号题号、连对计数器底、
引文 / 结论块、以及「唯一主角」区域。

> **A-23（2026-10-22）**：本节原为「**墨块**（Ink block）」，用近黑深底做强调。
> 所有者反馈「这些黑色底色太突兀了」→ 改为**沉底块**：**浅底深字**，
> 强调力由**近黑反差**改为「**尺度 + 挖坑感**」（36px 英雄数字仍是主角）。
> 原近黑 token **更名为 `--surface-code`**，只服务代码块，**本节不再使用**。

- 圆角：`--r-md`（12px）
- 内外边距：`padding: var(--sp-5)`（24px）；紧凑块 `12px 16px`
- 背景：`--surface-sunken`（浅色 `#f2ece1` ／ 夜纸 `#272319`）——**浅底深字**
- 边界：**1px 内发丝线** `--rule-hair`（浅 `#e6dcc4` ／ 夜 `#332d25`），
  以 `inset` 阴影落地（**不用 `border`**）；它与卡面的**底色差**共同把「坑」读出来
- 文字：`--ink-strong`（标题 / 数字）/ `--ink-body`（正文）；
  **大号数字 `--fs-hero`（36px）/ 700 / `tabular-nums`**
  （庆祝数字 / 连对计数器主数字同此档 —— A-18：不得压到 `--fs-display` 28px）
- **禁止**：沉底块上放黄色文字（黄不承载文字）；只用墨 / 纸两色 + 至多 1 个角色色块
- **不带柔影**：凹层不抬升（权威表 §3.1【A-23-3】）

| 状态 | 表现 |
|---|---|
| 默认 | `--surface-sunken` 底 + `--ink-strong` 字 + 内发丝线 |
| hover | 不适用（静态强调块） |
| active | 不适用 |
| focus-visible | 内部若含可聚焦元素，焦点环落在该元素上 |
| disabled | `opacity: .6` |
| loading | 数字位跑「滚动数字」动效（庆祝动效规格定义）；未定义时保持原值 |
| selected | 不适用 |
| error | 改为红底？→ **不**：失败语义用**红状态点 + 墨字**表达，沉底块本身保持中性 |

- 角色色：R0（可嵌 1 个角色色块 → R1）。

```css
.lk-sunkenblock {
  background: var(--surface-sunken); color: var(--ink-strong);
  border-radius: var(--r-md);
  box-shadow: inset 0 0 0 1px var(--rule-hair);
  padding: var(--sp-5);
}
.lk-sunkenblock__figure { font-family: var(--font-ui); font-size: var(--fs-hero);
  font-weight: 700; line-height: 1; font-variant-numeric: tabular-nums; }
.lk-sunkenblock:disabled, .lk-sunkenblock[aria-disabled="true"] { opacity: .6; }
```

### 4.21 空态（Empty state）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **B 卡面空态**（`empty-card`）。**卡面 + 柔影**（不是沉底面）；插画 + 一句 +
> 满宽主按钮不变。⇒ 旧的沉底形态作废。

**定位**：**没有任何内容**时的面板。形态固定为 **静物插画 + 一句 + 满宽主按钮**。

- 插画：`144 × 144`（紧凑 96px），本地 SVG `asset-still-<name>.svg`（写意线稿 + 淡彩）
- 一句：`--font-ui` / `--fs-body`（14px）/ `--ink-muted`，**≤ 18 字**，居中
- 按钮：**满宽**（`width: 100%`，容器 `max-width: 240px`），文案**就是动作**（不写「点击这里」）
- 容器：`padding: 48px 24px`；`display: flex; flex-direction: column; align-items: center; gap: 16px`
- **少字原则**：不写「暂无数据」+「请稍后再试」这类解释句

| 状态 | 表现 |
|---|---|
| 默认 | 插画 + 一句 + 主按钮 |
| hover / active | 主按钮走标准反馈 |
| focus-visible | 主按钮焦点环 |
| disabled | 不适用（空态总给得出动作） |
| loading | 不适用；加载中显示骨架屏而非空态 |
| selected | 不适用 |
| error | **加载失败不是空态**：错误态 = 静物插画（换「墨水泼洒」静物）+ 一句 + **次按钮**「重试」，红点提示 |

- 角色色：蓝（主按钮）R1。

```css
.lk-empty {
  display: flex; flex-direction: column; align-items: center; gap: var(--sp-4);
  padding: 48px 24px; text-align: center;
}
.lk-empty__art { width: 144px; height: 144px; display: block; }
.lk-empty__art svg { width: 100%; height: 100%; }
.lk-empty__text { margin: 0; max-width: 32em;
  font-family: var(--font-ui); font-size: var(--fs-body); line-height: 22px;
  color: var(--ink-muted); }
.lk-empty__action { width: 100%; max-width: 240px; }
```

```css
/* 空态的错误变体：换静物插画 + 次按钮「重试」，红点提示（不是空态） */
.lk-empty--error .lk-empty__text { color: var(--ink-muted); }
.lk-empty__alert { display: inline-flex; align-items: center; gap: var(--sp-2);
  color: var(--role-red-ink); font-size: var(--fs-meta); }
.lk-empty--error .lk-empty__action .lk-btn { background: var(--surface-card); color: var(--ink-strong);
  border: 1px solid var(--rule-control); box-shadow: var(--elev-1); }
```

### 4.22 骨架屏（Skeleton）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **B 呼吸式**（`skeleton-breathe`）。**不做横扫**：只让底色**整体明暗呼吸**
> （动 `opacity` 或 `background-color`，**不动位置**）；**无表面渐变** ⇒
> **A-74 的「微光是渐变的明确例外」不再被行使**。降级档：静止灰块（终态直出）。
> 始终**有可见体积**。

**定位**：**加载中**的面。现状全仓 `skeleton|spinner|aria-busy` **0 命中**，
本组件是新增能力（`acceptance.md` M-9）。

- 块高：随被替换内容（行 16px / 卡片 96px / 头像 40px）
- 圆角：`--r-xs`（6px）；头像 `--r-round`
- 底色：`--skeleton-base`
- **微光**：一块 **32% 宽的半透明实色**（`--skeleton-sheen`）横向平移，
  **不用渐变**（全局禁用界面渐变）；`1.2s linear infinite`
- 错峰：相邻块 `animation-delay` 递增 24ms
- **高度锁定**：骨架屏必须与真实内容**同高**，否则加载完成时页面跳动

| 状态 | 表现 |
|---|---|
| 默认 | 底色 + 微光扫过 |
| hover / active | 不适用 |
| focus-visible | 不适用（骨架不可聚焦） |
| disabled | 不适用 |
| loading | 常态 |
| selected | 不适用 |
| error | 骨架撤除，换错误态 / 空态 |
| reduced-motion | **微光停止平移**，只保留静态底色（状态直切） |

- 角色色：R0。
- **ARIA**：容器 `aria-busy="true"`；骨架块 `aria-hidden="true"`；
  容器内放一条 `.visually-hidden` 的「加载中」文本。

```css
.lk-skeleton { position: relative; overflow: hidden; border-radius: var(--r-xs);
  background: var(--skeleton-base); }
.lk-skeleton::after {
  content: ""; position: absolute; inset: 0 auto 0 0; width: 32%;
  background: var(--skeleton-sheen);
  transform: translateX(-100%); animation: lk-sheen 1.2s var(--ease-standard) infinite;
}
.lk-skeleton--text { height: 16px; border-radius: var(--r-xs); }
.lk-skeleton--block { height: 96px; border-radius: var(--r-md); }
.lk-skeleton--avatar { width: 40px; height: 40px; border-radius: var(--r-round); }
@keyframes lk-sheen { to { transform: translateX(312%); } }
@media (prefers-reduced-motion: reduce) {
  .lk-skeleton::after { animation: none; transform: none; }
}
```

### 4.23 吐司（Toast）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **A spec 吐司**（`toast-spec`）。**右上角浮起面** + 12px 圆角 + 13px 字 +
> **左侧状态点**；**浅底深字**（A-23 之后不再是墨块）。
> ⇒ 图谱页那条仿古硬编码 `.toast` 归 `graph-node-visual-language` change（图谱冻结）。

**定位**：**瞬时**反馈（保存成功、提交失败、复制成功）。位置：**右上角**圆角小卡
（与「活动浮层」同侧同规格）。

- 尺寸：`max-width: 320px`，`min-width: 240px`，`padding: 12px 16px`
- 圆角：`--r-md`（12px）
- 背景：**浮起面**（L2）：`--surface-raised` 底 + `--ink-strong` 字
  ⚠️ **A-23**：原为「**墨块**（近黑深底 + 白字）」，近黑面已退出内容块
  （`--surface-code` 只服务代码块）→ 吐司改**浅底深字**，靠 `--elev-3` 柔影 + 状态点读出「浮起」
- 字号：`--fs-meta`（13px）/ `line-height: 1.4`
- 左侧可选 10px 状态点（§4.14）
- 阴影：`--elev-3`；`z-index: var(--z-toast)`
- **层序**：`--z-toast`（200）**在模态之下**——模态打开时盖住吐司
  （权威表 §2.7 层序铁律 `modal > toast > dropdown > raised`，A-18）
- 停留：成功 3s；错误 5s（可手动关闭）

| 状态 | 表现 |
|---|---|
| 默认 | 浮起面 + 墨字；进入用「上浮 8px + 淡入」160ms |
| hover | `transform: translateY(-2px)`；阴影升一级 |
| active | `translateY(0)` |
| focus-visible | 吐司**不抢焦点**（`pointer-events: none` 于容器，`auto` 于内部按钮）；内部按钮有焦点环 |
| disabled | 不适用 |
| loading | 不适用（吐司不做加载态） |
| selected | 不适用 |
| error | 左侧 **红状态点**（`--role-red` / `filled`）+ 文字仍取 `--ink-strong`（不用红底）；`role="alert"` |
| 成功 | 左侧 **蓝状态点**；`role="status"`；`aria-live="polite"` |

- 角色色：R0 / R1（错误红点）。
- **不抢焦点**：`acceptance.md` §3.1「浮层出现时焦点不被抢走」。

```css
.lk-toast {
  position: fixed; top: 16px; right: 16px; z-index: var(--z-toast);
  display: flex; align-items: flex-start; gap: var(--sp-2);
  min-width: 240px; max-width: 320px; padding: 12px 16px;
  border-radius: var(--r-md); background: var(--surface-raised); color: var(--ink-strong);
  box-shadow: var(--elev-3); pointer-events: none;
  font-family: var(--font-ui); font-size: var(--fs-meta); line-height: 20px;
  opacity: 0; transform: translateY(-8px);
  transition: opacity var(--dur-base) var(--ease-out),
              transform var(--dur-base) var(--ease-out);
}
.lk-toast[data-show="true"] { opacity: 1; transform: translateY(0); }
.lk-toast__action { pointer-events: auto; }
```

### 4.24 对话框（Dialog）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **A spec 对话框**（`dialog-spec`）。⚠️ **本条属 B 类** —— 产品里**没有**真正的
> 模态对话框 ⇒ **先改 OpenSpec**（Esc 关闭 + 焦点陷阱 + 焦点归还）。
> 形态：暖墨面纱遮罩 + 浮起面板 + 右对齐动作区。

**定位**：**需要打断**的模态（确认删除、组卷确认、放弃作答）。轻反馈一律用吐司。

- 遮罩：`background: var(--veil-modal)`（**暖墨半透明面纱**：亮 42% / 夜纸 58%）——
  **遮罩是面纱、不是纸面**，不占用任何 `--surface-*` token
  （`--surface-code` 只服务代码块，A-23；权威表 §3.5 已补 `--veil-modal`）；
  半透明落在**背景色自身**上（不用容器的 `opacity`），避免把面板一起变半透明；
  **不用 backdrop-filter 模糊**（禁玻璃拟态）
- 面板：`--surface-raised` 底，圆角 `--r-md`（12px），`padding: 24px`
- 宽度：`min(480px, calc(100vw - 32px))`；最大高 `min(70vh, 640px)`，内容区可滚
- 阴影：`--elev-3`；`z-index: var(--z-modal)`
- 标题：`--font-ui` / `--fs-title`（18px）/ 700；正文 `--fs-body`（14px）
- 动作区：右对齐横排，`gap: 8px`，上边距 24px

| 状态 | 表现 |
|---|---|
| 默认 | 遮罩 + 面板；进入用「上浮 8px + 淡入」160ms |
| hover | 面板内按钮走标准反馈 |
| active | 同上 |
| focus-visible | 打开时焦点移到面板内**第一个可聚焦元素**（默认「取消」）；焦点环用双环 |
| disabled | 遮罩下背景内容 `inert`；面板内按钮可禁用（如「确认」在必填未满足时） |
| loading | 「确认」按钮切 loading 态（§4.1），面板不关闭，`aria-busy="true"` |
| selected | 不适用 |
| error | 面板内顶部行内错误条（红点 + 文字），面板不关闭 |

- 角色色：R0（确认按钮可用主按钮蓝，但那属于按钮自身配额）。
- **键盘**：`Esc` 关闭；`Tab` 在面板内循环（焦点陷阱）；关闭后焦点**回到触发元素**。

```css
.lk-dialog-backdrop { position: fixed; inset: 0; z-index: var(--z-modal);
  background: var(--veil-modal); display: flex; align-items: center; justify-content: center; }
.lk-dialog {
  width: min(480px, calc(100vw - 32px)); max-height: min(70vh, 640px);
  background: var(--surface-raised); color: var(--ink-strong);
  border-radius: var(--r-md); box-shadow: var(--elev-3);
  padding: 24px;
}
.lk-dialog__title { margin: 0 0 12px; font-family: var(--font-ui);
  font-size: var(--fs-title); font-weight: 700; }
.lk-dialog__body { color: var(--ink-muted); font-size: var(--fs-body); line-height: 22px; }
.lk-dialog__actions { display: flex; justify-content: flex-end; gap: var(--sp-2);
  margin-top: 24px; }
```

### 4.25 工具调用卡（Tool-call card）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **B 单行流水**（`tool-line`）。⚠️ **本条属 B 类** —— 产品里**没有** ⇒
> **先改 OpenSpec**。形态：一行摘要（工具名 + 耗时），细节靠点击 / 悬停再看。

**定位**：Agent 执行计划里的**一次工具调用**。折叠时只给 ≤ 240 字摘要。

- 卡片：`--surface-card` 底，圆角 `--r-md`（12px），`padding: 12px 14px`
- 头行：`状态点(10px) + 工具名(--font-mono, 13px) + 耗时(--font-mono, 12px, --ink-faint) + 折叠箭头(16px)`
- 摘要区：`--fs-meta`（13px），`--ink-muted`，**折叠态最多 240 字**
- 展开区：参数 / 结果，`--font-mono` 12px，`--surface-base` 底 + `--r-xs`（6px），
  `padding: 12px`，`overflow-x: auto`
- 头行高 ≥ 44px（命中区）

| 状态 | 表现 |
|---|---|
| 默认 | 折叠态；头行 + 摘要 |
| hover | `background: var(--veil-hover)`；箭头轻微位移 |
| active | 同上 |
| focus-visible | 展开箭头是 `<button>`，有双环焦点环 |
| disabled | 不适用 |
| loading | 状态点 `--role-blue` / `half`；摘要位换 2 行骨架屏 |
| selected | 展开态 |
| error | 状态点 `--role-red` / `filled`；摘要末尾 3 个字符省略号（**不加红字**，红由点承担） |
| 阻塞 | 状态点 `--role-red` / `cross` |

- 角色色：R1（状态点）。
- **ARIA**：头行为 `<button aria-expanded>`，内容区 `role="region"` + `aria-labelledby`。

```css
.lk-tool { background: var(--surface-card); border-radius: var(--r-md);
  box-shadow: var(--elev-1); overflow: hidden; }
.lk-tool__head { display: flex; align-items: center; gap: var(--sp-2);
  width: 100%; min-height: 44px; padding: 12px 14px;
  background: transparent; border: 0; color: var(--ink-strong); cursor: pointer; text-align: left;
  font-family: var(--font-ui); font-size: var(--fs-meta); }
.lk-tool__head:hover { background: var(--veil-hover); }
.lk-tool__name { font-family: var(--font-mono); font-weight: 600; }
.lk-tool__cost { margin-left: auto; font-family: var(--font-mono);
  font-size: var(--fs-label); color: var(--ink-faint); }
.lk-tool__body { padding: 0 14px 14px; font-size: var(--fs-meta); color: var(--ink-muted); }
.lk-tool__payload { margin-top: 8px; padding: 12px; border-radius: var(--r-xs);
  background: var(--surface-base); font-family: var(--font-mono); font-size: var(--fs-label);
  overflow-x: auto; white-space: pre-wrap; }
```

```css
/* 工具调用卡的运行中骨架：摘要位两行灰块 */
.lk-tool--running .lk-tool__summary { display: grid; gap: var(--sp-2); }
.lk-tool--running .lk-tool__summary span { display: block; height: 12px;
  border-radius: var(--r-xs); background: var(--skeleton-base); }
.lk-tool--running .lk-tool__summary span:last-child { width: 62%; }
.lk-tool--failed .lk-tool__summary { text-overflow: ellipsis; overflow: hidden;
  white-space: nowrap; }
```

### 4.26 时间线节点（Timeline node）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **B 分隔线时间线**（`timeline-flat`）。**不画竖线**，只用**发丝线分隔 + 小圆点**；
> 安静、省横向空间（代价：「先后」靠上下顺序读）。
> ⚠️ 现有的两套几何（`.agent-milestone` 18px 圆环 vs `.ai-plan-step` 9px 方块）
> **统一到这一套**。

**定位**：**执行计划 / 步骤序列**（Agent 计划、复习轮次、里程碑路径）。圆点时间线。

- 连接线：2px 竖线 `--rule-structure`（**单侧结构线语言**，与知识点正文一致）；`gap: 12px`
- 节点：`12 × 12` 圆点（§4.14 几何集）；当前节点 `14px` + `--elev-1`
- 内容卡：`--surface-card`，圆角 `--r-md`，`padding: 12px 16px`
- 行间距：`--sp-3`（12px）

| 状态 | 点 / 线 |
|---|---|
| 默认（已完成） | 点 `--role-blue` / `filled`；线 `--rule-structure` |
| hover | 内容卡 `translateY(-1px)`；点不变 |
| active | 同上 |
| focus-visible | 节点可聚焦时（`tabindex="0"`）双环焦点环 |
| disabled | 点 `--ink-disabled` / `filled` |
| loading | 当前节点 `--role-blue` / `half`；节点旁 12px 指示器 |
| selected（当前步骤） | 点 `--role-blue` / `ring` + 14px + 柔影；连接线在当前点之后加粗到 3px |
| error | 点 `--role-red` / `filled`；连接线**不**变红（线保持中性，避免整条线被红淹没） |
| 阻塞 | 点 `--role-red` / `cross` |

- 角色色：R1。

```css
.lk-timeline { list-style: none; margin: 0; padding: 0; }
.lk-timeline__item { position: relative; display: grid; grid-template-columns: 12px 1fr;
  gap: var(--sp-3); padding-bottom: var(--sp-3); }
.lk-timeline__item::before { content: ""; position: absolute; left: 5px; top: 14px; bottom: -4px;
  width: 2px; background: var(--rule-structure); }
.lk-timeline__item:last-child::before { display: none; }
.lk-timeline__dot { width: 12px; height: 12px; margin-top: 4px; border-radius: var(--r-pill);
  background: var(--role-blue); }
.lk-timeline__item--current .lk-timeline__dot { width: 14px; height: 14px; margin-left: -1px;
  box-shadow: var(--elev-1); }
```

### 4.27 折叠段（Disclosure）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **C 手风琴折叠段**（`disc-accordion`）。**卡面 + 48px 头 + 内容在同一张卡里**；
> 四处各写各的原生 `<details>` **统一**。

**定位**：**可展开的内容块**（计划详情、目标编辑器、辅助说明）。现状用 `<details>`。

- 头行（summary）：高 ≥ 44px，`padding: 0 16px`，圆角 `--r-md`
- 箭头：16×16 本地 SVG `asset-icon-chevron-down`，展开时旋转 180°（160ms）
- 内容区：`padding: 0 16px 16px`
- 展开动画：`grid-template-rows: 0fr → 1fr`（160ms），避免 `max-height` 猜高度

| 状态 | 表现 |
|---|---|
| 默认 | 折叠；箭头朝下；标题 `--fs-body` / `--ink-strong` |
| hover | `background: var(--veil-hover)`；`color: var(--ink-strong)` |
| active | `background: var(--veil-active)` |
| focus-visible | 头行双环焦点环 |
| disabled | `color: var(--ink-disabled)`；`pointer-events: none`；`aria-disabled="true"` |
| loading | 内容区骨架屏；头行不变 |
| selected | 展开态 `aria-expanded="true"`；标题字重 600 |
| error | 内容区顶部行内错误条（红点 + 文字） |

- 角色色：R0（可选尾部状态点 → R1）。
- **ARIA**：`<button aria-expanded aria-controls>` + 目标容器 `role="region"`。

```css
.lk-disclosure__head { display: flex; align-items: center; gap: var(--sp-2);
  width: 100%; min-height: 44px; padding: 0 16px;
  border: 0; border-radius: var(--r-md); background: transparent;
  color: var(--ink-strong); font-family: var(--font-ui); font-size: var(--fs-body);
  font-weight: 500; cursor: pointer; text-align: left;
  transition: background-color var(--dur-fast) var(--ease-out); }
.lk-disclosure__head:hover:not(:disabled) { background: var(--veil-hover); }
.lk-disclosure__head:active:not(:disabled) { background: var(--veil-active); }
.lk-disclosure__head:focus-visible { outline: 2px solid transparent; outline-offset: 2px;
  box-shadow: 0 0 0 2px var(--surface-base), 0 0 0 4px var(--focus-outer); }
.lk-disclosure__head svg { width: 16px; height: 16px; fill: none; stroke: currentColor;
  stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;
  transition: transform var(--dur-base) var(--ease-out); }
.lk-disclosure__head[aria-expanded="true"] svg { transform: rotate(180deg); }
.lk-disclosure__body { display: grid; grid-template-rows: 0fr;
  transition: grid-template-rows var(--dur-base) var(--ease-out); }
.lk-disclosure__body[data-open="true"] { grid-template-rows: 1fr; }
.lk-disclosure__body > * { overflow: hidden; }
```

### 4.28 Tab（标签页）

> **形态裁定（A-115 · 2026-10-22 所有者样式板）**：
> **B 分段式标签页**（`tab-seg`）。用**分段控件的形态**（与 §4.11 共用一套语言）；
> 代价是它不像链接。⇒ 旧的 3px 蓝下边框 + 容器底发丝线作废。

**定位**：**同层内容**的切换（记录中心：概览 / 作答明细 / 错题 / 复习负荷）。

- Tab 条：高 48px，`display: flex; gap: 4px`，`border-bottom: 0`（**不用描边分隔**）
- Tab：高 48px，`padding: 0 16px`，圆角 `--r-md`（12px，只在 hover 时可见底）
- 字号：`--fs-body`（14px）/ 未选中 500、选中 600
- 指示条：选中项底部 3px `--role-blue`，圆角 3px，宽度 = 文字宽 + 24px
- 命中区：高 48px ✔

| 状态 | 表现 |
|---|---|
| 默认（未选中） | `color: var(--ink-muted)`；无底色 |
| hover | `background: var(--veil-hover)`；`color: var(--ink-strong)` |
| active | `background: var(--veil-active)` |
| focus-visible | 双环焦点环，内环用纸面色 |
| disabled | `color: var(--ink-disabled)`；`pointer-events: none` |
| loading | 不适用（Tab 切换不异步）；面板内容可独立骨架屏 |
| selected | `color: var(--role-blue)`；`font-weight: 600`；底部 3px `--role-blue` 指示条；可带徽标计数 |
| error | 不适用 |

- 角色色：蓝（当前指示）R1。
- **键盘**：`←`/`→` 移动（roving tabindex，移动即激活）、`Home`/`End`；
- **ARIA**：`role="tablist"` / `role="tab"` + `aria-selected` + `aria-controls`；
  面板 `role="tabpanel"` + `aria-labelledby` + `tabindex="0"`。

```css
.lk-tablist { display: flex; gap: 4px; }
.lk-tab { position: relative; display: inline-flex; align-items: center; gap: var(--sp-2);
  min-height: 48px; padding: 0 16px; border: 0; border-radius: var(--r-md);
  background: transparent; color: var(--ink-muted);
  font-family: var(--font-ui); font-size: var(--fs-body); font-weight: 500;
  cursor: pointer;
  transition: background-color var(--dur-fast) var(--ease-out),
              color var(--dur-fast) var(--ease-out); }
.lk-tab:hover:not(:disabled) { background: var(--veil-hover); color: var(--ink-strong); }
.lk-tab:active:not(:disabled) { background: var(--veil-active); }
.lk-tab:focus-visible { outline: 2px solid transparent; outline-offset: -2px;
  box-shadow: 0 0 0 2px var(--surface-base), 0 0 0 4px var(--focus-outer); }
.lk-tab[aria-selected="true"] { color: var(--role-blue); font-weight: 600; }
.lk-tab[aria-selected="true"]::after {
  content: ""; position: absolute; left: 12px; right: 12px; bottom: 0; height: 3px;
  border-radius: 3px; background: var(--role-blue); }
.lk-tab:disabled { color: var(--ink-disabled); cursor: not-allowed; }
```

---

## 4.30 组件形态裁定表（2026-10-22 · A-115 · 所有者样式板）

> **本表是 §4.1–§4.28 各组件的「唯一形态定义」。**
> 来源：`design-notes/styleboard-picks.md`（所有者从 `tmp/frontend-audit/styleboard-v2/`
> 样式板导出的选择，导出时间 `2026-10-22T23:31:32.731Z`）。
> **冲突时：本表 > 各节的「形态裁定」框 > 各节正文**（各节的框与本表一致，
> 保留它们是为了让每节自洽可读）。
> 落地分类：**A 类** = 现有产品的形态变更（只改外观）⇒ 可直接实现；
> **B 类** = 新界面 / 新交互面 ⇒ **必须先改 OpenSpec**（AGENTS.md 纪律 1）。

| § | 组件 | 选定形态 | 变体 id | 落地类别 |
|---|---|---|---|---|
| §4.1 | 按钮 · 主按钮 | **B 无影平底** | `btn-primary-flat` | A |
| §4.2 | 按钮 · 次按钮 | **C 沉底次按钮** | `btn-secondary-sunken` | A |
| §4.3 | 按钮 · 文字按钮 | **B 带箭头** | `btn-text-arrow` | A |
| §4.4 | 按钮 · 图标按钮 | **C 圆形图标按钮** | `iconbtn-round` | A |
| §4.5 | 输入框 | **A spec 输入框** | `input-spec` | A |
| §4.6 | 文本域 | **A spec 文本域** | `textarea-spec` | A |
| §4.7 | 自绘下拉 | **A spec 自绘下拉** | `select-spec` | **B** |
| §4.8 | 复选框 | **B 整行选中** | `check-row` | A |
| §4.9 | 单选 | **B 整行卡选中** | `radio-row` | A |
| §4.10 | 开关 | **B 迷你开关** | `switch-mini` | A |
| §4.11 | 分段控件 | **C 药丸分段** | `seg-pill` | A |
| §4.12 | 标签 | **C 角色色标签** | `tag-role` | A |
| §4.13 | 徽标 | **B 胶囊计数** | `badge-pill` | A |
| §4.14 | 状态圆点 | **A spec 全几何集** | `dot-spec` | A |
| §4.15 | 进度条 | **A 胶囊进度** | `progress-pill` | A |
| §4.16 | 分段进度条 | **B 编号点串** | `steps-num` | **B** |
| §4.17 | 题号格 | **A spec 形态** | `qcell-spec` | A |
| §4.18 | 卡片 | **A spec 留白** | `card-spec` | A |
| §4.19 | 纸面层级 | **A spec 四层** | `surface-spec` | A |
| §4.20 | 沉底块 | **C 竖线沉底** | `sunken-rail` | A |
| §4.21 | 空态 | **B 卡面空态** | `empty-card` | A |
| §4.22 | 骨架屏 | **B 呼吸式** | `skeleton-breathe` | A |
| §4.23 | 吐司 | **A spec 吐司** | `toast-spec` | A |
| §4.24 | 对话框 | **A spec 对话框** | `dialog-spec` | **B** |
| §4.25 | 工具调用卡 | **B 单行流水** | `tool-line` | **B** |
| §4.26 | 时间线节点 | **B 分隔线时间线** | `timeline-flat` | A |
| §4.27 | 折叠段 | **C 手风琴折叠段** | `disc-accordion` | A |
| §4.28 | Tab | **B 分段式标签页** | `tab-seg` | A |

### 4.30.1 B 类四条：为什么必须先改 OpenSpec

这四条**在产品里没有对应界面**，实现它们会**引入新的用户可观察行为**
（键盘与 ARIA、Esc、焦点陷阱、焦点归还），而不只是换一层皮：

| § | 组件 | 新增的可观察行为 | 必须先写清的事 |
|---|---|---|---|
| 4.7 | 自绘下拉 | 8 处原生 `<select>` 换成自绘控件 | 键盘操作（↑↓ / Enter / Esc / 首字母）、焦点模型（`role=listbox` + `aria-activedescendant` 或 roving tabindex）、**载荷仍由 hidden input 承载**（G-1 请求序列与载荷**不得变**）、原生控件在窄屏与打印下的回落 |
| 4.16 | 分段进度条 | 一个新界面 | 段数上限、溢出时的形态、是否可点（可点就要新行为） |
| 4.24 | 对话框 | 一个真正的模态 | Esc 关闭、焦点陷阱、**焦点归还**到触发元素、遮罩点击是否关闭、`role=dialog` + `aria-modal` |
| 4.25 | 工具调用卡 | 一个新界面 | 「工具名 + 耗时」的取值来源、折叠与展开的键盘路径、失败态的语义 |

⇒ 这四条**单开一个 OpenSpec change**（`workbench-component-forms`）承载，
**先 proposal → specs，再实现**；A 类不阻塞。

### 4.30.2 尺寸的可调性（所有者的原话）

> 「按钮、卡片等的大小可以根据具体布局与视觉效果做微调，**数字不是定死的**。」

⇒ **本节各条与 §4.30 里的尺寸数字是设计默认值，不是硬约束。**
实现时按具体布局与视觉效果微调，**以「看起来对」为准**。
**唯一不可让步的两条**：

1. **命中区 ≥ 44×44 CSS px**（§3.1，无障碍硬约束）——
   视觉尺寸可以小于它（40×40 的圆形图标按钮、32×18 的迷你开关、10px 的状态圆点），
   但**命中区必须补到 44px**（伪元素或容器间距补偿）。
2. **焦点环**（§3.2）—— 不得被 `outline: none` 压死、不得被 `overflow: hidden` 裁掉。

### 4.30.3 这次裁定的**连带影响**（已识别）

1. **§4.22 骨架屏「呼吸式」否掉了「微光扫过」** ⇒ 主 change 的
   `specs/workbench-ui/spec.md`（"View transition and skeleton loading state"）
   与 `acceptance.md` §2 的 **M-9** 判据**已同步改写**；
   ⇒ **A-74**（微光是渐变的明确例外）**不再被行使**（账本不改写，只记它不再适用）。
2. **§4.11 的「白色药丸」** ⇒ 回答 **A-84 第 2 条**（`.lk-seg` 选中项要不要角色蓝）：
   **不用角色蓝**，选中由白色药丸承载。
3. **§4.4 的 40×40 圆形** ⇒ 回答 **A-84 第 3 条**的「视觉尺寸 32 vs 40」：选 **40**。
4. **§4.26 统一两套时间线几何** ⇒ `.agent-milestone`（18px 圆环）与
   `.ai-plan-step`（9px 方块）**合成一套**（发丝线 + 小圆点）。
5. **§4.28 Tab 改分段式** ⇒ 与 §4.11 共用语言 ⇒ 两处 CSS 应合并成**同一个**类，
   避免再次出现「同一组件两套实现」。

## 5. 控件一致性对照表

### 5.1 统计核实（grep 实测，2026-10-21）

> 命令：`grep -c "<select" workbench/server/pages.py` 等。任务书给的数字与实测的差异在此登记，
> 以**实测**为准（`F08.md` §6.5 的口径是「服务端渲染页面」，本表口径是「全仓字面量」）。

| 控件 | 任务书给的数 | **grep 实测** | 差异说明 |
|---|---|---|---|
| `<select>` | 8 | **8** | 全部在 `workbench/server/pages.py`；JS 创建数 0 |
| `<input>` | 9 | **9**（`pages.py`）+ 3（JS 字面量）+ 1（`createElement`）= **13** | 任务书只统计了 `pages.py` |
| `<textarea>` | 6 | **6**（`pages.py`）+ 1（`experience_page.py`）= **7** | 同上 |
| `<button>` | 60 | **66**（58 `pages.py` + 4 `experience_page.py` + 2 `records.py` + 2 `practice-flow.js`） | 任务书少统计 6；`F08.md` 只数到 60（`pages.py` 58 + `records.py` 2） |

**字面量定位（可直接 grep 复核）**

```
grep -n "<select"   workbench/server/pages.py          # 8
grep -n "<input"    workbench/server/pages.py          # 9
grep -n "<textarea" workbench/server/pages.py          # 6
grep -n "<textarea" workbench/server/experience_page.py # 1
grep -ro "<button"  workbench/ | wc -l                 # 66
```

### 5.2 `<select>` → 自绘下拉（§4.7）

**8 处，全部替换，无例外。** 保留一个同名 `hidden` input 承载原 `name` / `value`，
保证**请求载荷键集合逐条不变**（`acceptance.md` G-1）。

| # | 定位 | id | 语义 | 替换为 | 备注 |
|---|---|---|---|---|---|
| 1 | `workbench/server/pages.py:62` | `#chapter-lens-select` | 章节透镜选章 | `.lk-select`（触发器 + 面板，每项带章节名；**不带每章计数** —— 既有 spec「Chapter switch in the top bar」明令不得显示 per-chapter statistics / counts） | 现状 `hidden` 时不显示；透镜关闭时同样不渲染 |
| 2 | `workbench/server/pages.py:206` | `#paper-reveal-timing` | 试卷答案展示时机 | `.lk-select` | 值读取于 `paper-practice.js:357` / `:365` / `:460` / `:475` |
| 3 | `workbench/server/pages.py:263` | `#goal-kind` | 目标类型（阶段 / 长期） | `.lk-select` | 在目标表单内，选项 2 个 → 也可降级为 §4.11 分段控件；**本规格统一用下拉**以保持表单一致性 |
| 4 | `workbench/server/pages.py:395` | `#knowledge-sort` | 知识点排序 | `.lk-select` | 在 `.knowledge-sort-bar` 内 |
| 5 | `workbench/server/pages.py:657` | `#workspace-select` | 切换工作区 | `.lk-select` | 顶栏 |
| 6 | `workbench/server/pages.py:665` | `#setting-running-send` | 运行中发送方式 | `.lk-select` | 设置视图 |
| 7 | `workbench/server/pages.py:744` | `#ai-model-switch` | 切换模型 / Agent | `.lk-select` | 右栏，下一轮生效 |
| 8 | `workbench/server/pages.py:770` | `#ai-send-action` | 发送方式 | `.lk-select` | 右栏输入区上方 |

### 5.3 `<input>` → 自绘控件（§4.5 / §4.8 / §4.10）

| # | 定位 | id / 类型 | 语义 | 替换为 | 备注 |
|---|---|---|---|---|---|
| 1 | `workbench/server/pages.py:60` | `#chapter-lens-switch` / checkbox | 章节透镜开关 | **§4.10 开关** | 紧邻 `#chapter-lens-select`，两者不冲突 |
| 2 | `workbench/server/pages.py:180` | `#rating-input` / number | 自评 1–5 | **§4.5 输入框（数字变体）**，`min-width: 72px` | 现状宽 90px（`workbench.css:1899`） |
| 3 | `workbench/server/pages.py:261` | `#goal-id` / hidden | 目标 id | **不自绘**（隐藏域，无视觉） | 保留原样 |
| 4 | `workbench/server/pages.py:262` | `#goal-title` / text | 目标名称 | **§4.5 输入框** | |
| 5 | `workbench/server/pages.py:264` | `#goal-start-date` / date | 开始日期 | **§4.5 输入框（日期变体）** | 原生 `type=date` 保留（换日期选择器会引入新交互面）；**仅重绘外壳**，原生指示器用 `accent-color` 调色 |
| 6 | `workbench/server/pages.py:265` | `#goal-deadline` / date | 截止日期 | **§4.5 输入框（日期变体）** | 同上 |
| 7 | `workbench/server/pages.py:420` | `#graph-search` / text | 图谱搜索 | **不改** | **知识图谱页在范围外** |
| 8 | `workbench/server/pages.py:446` | `#graph-gravity` / range | 图谱节点间距 | **不改** | 同上 |
| 9 | `workbench/server/pages.py:668` | `#setting-show-rating` / checkbox | 显示自评 | **§4.10 开关** | 设置视图 |
| 10 | `workbench/server/static/kp-experience.js:99` | checkbox（JS 模板） | 关联题目多选 | **§4.8 复选框** | 命中区按行 |
| 11 | `workbench/server/static/practice-flow.js:872` | checkbox \| radio（JS 模板） | 选项作答 | **§4.8 复选框** / **§4.9 单选** | 按 `multiple` 分支；`fieldset` + `legend` 结构保留 |
| 12 | `workbench/server/static/practice-flow.js:1553` | checkbox（JS 模板） | 筛选维度 | **§4.8 复选框** | |
| 13 | `workbench/server/static/paper-practice.js:649` | `createElement("input")`，`type` 为 checkbox \| radio | 试卷选项 | **§4.8 复选框** / **§4.9 单选** | `paper-practice.js:640-660` |

### 5.4 `<textarea>` → 文本域（§4.6）

| # | 定位 | id | 语义 | 替换为 | 备注 |
|---|---|---|---|---|---|
| 1 | `workbench/server/pages.py:172` | `#answer-box` | 练习作答 | **§4.6 文本域** | 现状 `rows=3` |
| 2 | `workbench/server/pages.py:182` | `#feedback-note` | 卡点 / 心得（可选） | **§4.6 文本域（紧凑）**，`rows=1` → 最小高 56px | 现状 `workbench.css:603` 有独立覆写 |
| 3 | `workbench/server/pages.py:219` | `#paper-answer` | 试卷作答 | **§4.6 文本域** | `rows=5` |
| 4 | `workbench/server/pages.py:266` | `#goal-description` | 目标说明 | **§4.6 文本域** | |
| 5 | `workbench/server/pages.py:272` | `#goal-nl` | 自然语言目标 | **§4.6 文本域** | 紧邻「一句话让 Agent 帮你填」按钮 |
| 6 | `workbench/server/pages.py:773` | `#ai-input` | Agent 输入 | **§4.6 文本域（`--composer` 变体）** | 贴底、聚焦变蓝 + 轻微抬起 |
| 7 | `workbench/server/experience_page.py:82` | `#experience-content` | 经验正文 | **§4.6 文本域** | `rows=8` |

### 5.5 `<button>` → 按钮族（§4.1–§4.4 / §4.11 / §4.17）

**66 处，按现有 class 归并到 6 个规格**：

| 现有 class（出现处数） | 定位 | 替换为 | 变体要点 |
|---|---|---|---|
| `primary`（14） | `pages.py:169,175,183,208,214,220,225,230,267,547,615,757,775` + `experience_page.py:88` | **§4.1 主按钮** | `--fs-body`（14px，A-18）/600、蓝实心、柔影；命中区 44px |
| `outline`（17） | `pages.py:171,174,176,187,212,213,224,231,268,273,549,550,730,756,765,774,1125` + `experience_page.py:75` | **§4.2 次按钮** | 纸面底 + 1px 发丝边 + 卡级柔影 |
| `ghost`（14） | `pages.py:78,80,118,131,177,184,187,226,252,253,399,551,741` + `experience_page.py:76,89` + `practice-flow.js:1571` | **§4.3 文字按钮** | 透明底、hover 洗底 |
| `icon-only` / `icon-btn`（7） | `pages.py:78,80,118,131,427,428,741` | **§4.4 图标按钮** | 40×40 + 44px 命中区；**必须有 `aria-label`**（现状 78/80 已有，427/428 需补） |
| `sm`（26，与上面 class 叠加） | 同上各行 | **尺寸变体 S** | 高 36px，命中区仍 44px（伪元素补） |
| `rate`（0 静态 / 试卷评分） | `workbench.css:403-413` 定义 | **§4.11 分段控件** | 1–5 自评；现状是胶囊按钮组 |
| `legend-item`（5）+ 图谱缩放（3） | `pages.py:463-467,469-471` | **不改** | **知识图谱页在范围外** |
| `chip`（1） | `pages.py:440`（记录中心筛选） | **§4.11 分段控件**（横向滚动形态） | 现状 `class='chip active'` |
| `control-toggle`（1） | `pages.py:433` | **§4.27 折叠段**（头） | 图谱侧栏开关 → 图谱页，**不改**；同名类仅在图谱内使用 |
| `goal-edit` / `goal-delete`（2） | `pages.py:252,253` | **§4.4 图标按钮** | 各自带 `aria-label` |
| `agent-activity-toggle` / `agent-aux-collapse`（2） | `pages.py:118,131` | **§4.4 图标按钮** | 已有 `aria-expanded` + `aria-label` |
| 无 class（3） | `pages.py:423`（记录视图切换）、`469-471`（图谱缩放） | `423` → **§4.3 文字按钮 + `aria-selected`**；`469-471` → **不改**（图谱） | |
| `records.py:92,95` | 「查看本次答卷」/「再做一次」 | **§4.3 文字按钮** / **§4.2 次按钮** | 作答明细卡片流内 |
| `practice-flow.js:1572` | `#filter-close`「关闭」 | **§4.3 文字按钮** | 筛选浮层 |

### 5.6 图谱页冻结项（**不替换、不重绘**）

| 定位 | 控件 | 处置 |
|---|---|---|
| `workbench/server/pages.py:420` | `#graph-search` | 原样 |
| `workbench/server/pages.py:446` | `#graph-gravity` | 原样 |
| `workbench/server/pages.py:423` | 记录视图切换按钮 | **改**（在记录中心，不在图谱） |
| `workbench/server/pages.py:433` | `.control-toggle` | 原样 |
| `workbench/server/pages.py:463-467` | `.legend-item` × 5 | 原样 |
| `workbench/server/pages.py:469-471` | 图谱缩放 × 3 | 原样 |
| `workbench/server/static/workbench.css:1560-1903` | `.graph-*` 全套 | 原样；`--surface-sheet` 保持 `#fffdf7` |

### 5.7 替换总量小结

| 类别 | 数量 | 替换率 |
|---|---|---|
| `<select>` | 8 | 8 / 8 = **100%** |
| `<input>` | 13 | 10 / 13 = **77%**（1 hidden + 2 图谱除外） |
| `<textarea>` | 7 | 7 / 7 = **100%** |
| `<button>` | 66 | 57 / 66 = **86%**（9 个图谱除外） |

---

## 6. 可访问性要求（逐组件）

### 6.1 全局硬规则

| # | 规则 | 落点 |
|---|---|---|
| A-1 | **每个可交互控件在 Tab 时有可见焦点环**；不得出现 `outline: none` | 现有 3 处 `outline: none`（`workbench.css:338` / `:427` / `:833`）必须清除；本规格 §3.2 双环焦点环 |
| A-2 | 焦点环在**任何底色**上都可见：内环取所在纸面色，外环取蓝 | §3.2 |
| A-3 | 正文 ≥ 4.5:1；次要文字 ≥ 4.5:1（底线 3:1）；占位 / 禁用 ≥ 3:1 | §2.2 对比度表 |
| A-4 | **状态不得只靠颜色**：每个状态都有几何编码（圆点 / 形状 / 竖条） | §3.6 状态映射表（色 + 几何唯一映射） |
| A-5 | 状态点本身 `aria-hidden="true"`；语义由宿主的 `aria-label` / `aria-current` / `aria-disabled` 承担 | §4.14 |
| A-6 | 所有可交互控件命中区 ≥ 44 × 44 CSS px | §3.1；紧凑控件用伪元素 / 步距补偿 |
| A-7 | 图标有可访问名（`aria-label` 或视觉隐藏文本）；纯图标按钮**不得**无 `aria-label` | §4.4；`pages.py:427,428` 需补 |
| A-8 | 动效全部尊重 `prefers-reduced-motion`，降级为状态直切 | §3.3；骨架屏微光单独降级（§4.22） |
| A-9 | 页面转场与浮层出现时**不抢焦点** | §4.23 吐司 `pointer-events: none`；§4.24 对话框才接管焦点 |
| A-10 | 装饰层一律 `pointer-events: none`（`acceptance.md` G-7） | 装饰层在 §4.22 骨架、§4.21 插画、§4.23 吐司 |
| A-11 | `forced-colors: active` 下焦点环退回系统色 | §3.2 `@media (forced-colors: active)` |
| A-12 | 界面注释能删则删；改造后说明性文字**数量不增加** | §4.21 空态一句、§4.25 摘要 ≤ 240 字 |

### 6.2 逐组件 ARIA / 键盘表

| 组件 | 角色 / 属性 | 键盘行为 |
|---|---|---|
| 按钮（主 / 次 / 文字） | 原生 `<button type="button">`；`aria-busy` 表示 loading；`aria-pressed` 表示 toggle | `Enter` / `Space` 触发 |
| 图标按钮 | 原生 `<button>` + **必须** `aria-label`；折叠类加 `aria-expanded` + `aria-controls` | `Enter` / `Space`；`Esc` 关闭父浮层 |
| 输入框 | 原生 `<input>` + `<label for>`；错误加 `aria-invalid="true"` + `aria-describedby` 指向行内错误 | `Tab` 进出；`Esc` 清空（可选） |
| 文本域 | 同上 | 同上；`Enter` 换行，`Ctrl/Cmd+Enter` 提交（若绑定） |
| 自绘下拉 | `role="combobox"` + `aria-expanded` + `aria-controls` + `aria-activedescendant`；面板 `role="listbox"`；项 `role="option" aria-selected` | `↑`/`↓` 移动，`Enter`/`Space` 选中，`Esc` 关闭回焦，`Home`/`End`，前缀跳转 |
| 复选框 | 原生 `<input type="checkbox">`（视觉隐藏，保留语义）+ `aria-checked="mixed"` 表示半选 | `Space` 切换 |
| 单选 | 原生 `<input type="radio">` + 同 `name` 的分组；`fieldset` + `legend` | `↑`/`↓` 在组内移动并选中，`Space` 选中 |
| 开关 | 原生 `<input type="checkbox" role="switch">` + `aria-checked` | `Space` 切换 |
| 分段控件 | `role="radiogroup"` + 项 `role="radio" aria-checked`；roving tabindex | `←`/`→` 移动并选中，`Home`/`End` |
| 标签 | 静态文本；若可交互则必须用按钮 | — |
| 徽标 | 纯装饰 `aria-hidden="true"`；计数文本由宿主 `aria-label` 承载 | — |
| 状态圆点 | `aria-hidden="true"` | — |
| 进度条 | `role="progressbar"` + `aria-valuenow` / `aria-valuemin` / `aria-valuemax`；不确定态 `aria-valuenow` 省略 | 不可聚焦；若可点击跳转则加 `role="link"` |
| 分段进度条 | 同上 | — |
| 题号格 | 原生 `<button>` + `aria-label="第 N 题"`（含状态文字在 `aria-label` 内，**视觉上零文字**）+ `aria-current="step"` | `Enter`/`Space` 跳转；方向键在网格内移动 |
| 卡片 | 容器 `<article>` 或 `<li>`；可点击卡用 `<button>` / `role="button"` + `aria-pressed` | `Enter`/`Space` 激活 |
| 纸面 / 沉底块 | 静态容器；`aria-hidden` 不适用（内容需读出） | — |
| 空态 | 容器 `role="status"`？→ **否**（静态内容不抢播报）；主按钮正常可聚焦 | `Tab` 到主按钮 |
| 骨架屏 | 容器 `aria-busy="true"`；骨架块 `aria-hidden="true"`；容器内 `.visually-hidden` 的「加载中」 | 期间不可聚焦 |
| 吐司 | 成功 `role="status" aria-live="polite"`；错误 `role="alert"` | **不抢焦点**；内部按钮可聚焦 |
| 对话框 | `role="dialog" aria-modal="true" aria-labelledby`；背景 `inert` | `Esc` 关闭；`Tab` 焦点陷阱；关闭后焦点回触发元素 |
| 工具调用卡 | 头 `<button aria-expanded aria-controls>`；内容 `role="region"` | `Enter`/`Space` 展开收起 |
| 时间线节点 | `role="list"` / `<ol>`；当前项 `aria-current="step"` | 可聚焦节点 `tabindex="0"` |
| 折叠段 | `<button aria-expanded aria-controls>` + `role="region"` | `Enter`/`Space` 展开收起 |
| Tab | `role="tablist"` / `role="tab" aria-selected aria-controls`；面板 `role="tabpanel" aria-labelledby tabindex="0"` | `←`/`→` 移动并激活，`Home`/`End` |

### 6.3 装饰层与非交互元素

- 状态点、徽标、插画、背景装饰一律 `aria-hidden="true"` + `pointer-events: none`。
- 图标 SVG 一律 `aria-hidden="true"` + `focusable="false"`，可访问名由按钮的
  `aria-label` 或相邻 `.visually-hidden` 文本承担。

---

## 7. 组件总览

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  柔和蒙德里安 v2 · 组件总览                                            底 #fdf8ef · 圆角 12px │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│  ┌── 纸面层级 ─────────────────────────────────────────────────────────────────────────────┐ │
│  │  L0 底 #fdf8ef    L1 卡 #fffdf7    L2 浮起 #ffffff    L3 沉底 #f2ece1                   │ │
│  │  ▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢  │ │
│  └────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                              │
│  ┌── 按钮 ──────────┐ ┌── 输入 ─────────┐ ┌── 自绘下拉 ──────┐ ┌── 开关 / 复选 / 单选 ──┐    │
│  │ ▐ 主要操作 ▌  ▌  │ │ ┌─────────────┐ │ │ 当前章节      ⌄ │ │ ┌──┐  ⬤ 已选           │    │
│  │ ▐ 次要 ▌ ▐ 按钮   │ │ │ 请输入…      │ │ ├───────────────┤ │ │☑  │  ○ 未选  ⬤ 选中   │    │
│  │ 文字按钮  ◎ 图标  │ │ └─────────────┘ │ │ │ 第三章    ●  │ │ └──┘  ⬛ 开关(开)      │    │
│  └──────────────────┘ └────────────────┘ └─────────────────┘ └─────────────────────────┘    │
│                                                                                              │
│  ┌── 分段控件 ──────────┐ ┌── 标签 / 徽标 ──────┐ ┌── 状态圆点（冗余通道）────────────────┐  │
│  │ ┌────┬────┬────┐    │ │ 中性  蓝  黄  红   │ │  ○ 未开始   ◯ 当前(交互)  ◐ 进行中      │  │
│  │ │衬线│无衬│    │    │ │ (3)  ● 状态徽标    │ │  ● 已完成   ● 当前(内容)  ▨ 到期       │  │
│  │ └────┴────┴────┘    │ └───────────────────┘ │  ● 失败   ✕ 阻塞                          │  │
│  └─────────────────────┘                       └──────────────────────────────────────────┘  │
│                                                                                              │
│  ┌── 进度 ──────────────┐ ┌── 题号格 ──────────┐ ┌── 卡片 / 沉底块 ─────────────────────┐  │
│  │ ▓▓▓▓▓▓▓▓░░░░░░      │ │  1  2  3  4  5  6  │ │ ┌─────────────────────────────┐      │  │
│  │ ▓▓▓▓▓▓░░░░░░ (分段) │ │  ◯  ●  ●  ▨  ●  ✕ │ │ │ 标题                [状态点] │      │  │
│  └─────────────────────┘ └───────────────────┘ │ └─────────────────────────────┘      │  │
│                                               │ ┌──────────────┐                       │  │
│  ┌── Tab ─────────────────────┐ ┌── 折叠段 ────┐ │ │   沉 底      │ ← L3 凹层           │  │
│  │  概览  作答明细  错题  负荷 │ │ ▸ 计划详情  ⌄ │ │ │   36 24px    │                       │  │
│  └────────────────────────────┘ └──────────────┘ └───────────────────────────────┘      │  │
│                                                                                              │
│  ┌── 空态 ──────────────────┐ ┌── 骨架屏 ────────┐ ┌── 吐司 / 对话框 ───────────────────┐  │
│  │      ( 静物插画 )         │ │ ▭▭▭▭  ▭▭▭▭▭▭   │ │                    ┌──────────┐    │  │
│  │      这里还没有内容        │ │ ▭▭▭▭▭  ▭▭▭▭     │ │                    │ ● 提示   │    │  │
│  │   ┌──────────────┐        │ │ ▭▭▭▭  ▭▭▭▭▭▭▭  │ │  ╔══════════════╗ │ └──────────┘    │  │
│  │   │  开始练习     │        │ └─────────────────┘ │  ║ 对话框        ║ │                  │  │
│  │   └──────────────┘        │                      │  ║ 正文…        ║ │                  │  │
│  └───────────────────────────┘                      │  ║ [取消][确认] ║ │                  │  │
│                                                     │  ╚══════════════╝ │                  │  │
│  ┌── 工具调用卡 / 时间线 ────────────────────────┐  └──────────────────┘                  │  │
│  │ ● read_file   0.2s  ⌄                        │  ┌── 流程 ────────────────────────────┐  │
│  │ │ payload…                                │  │  ●────  步骤一                      │  │
│  │ ○ 读取中…                                  │ │  ◐────  步骤二（当前）              │  │
│  │ ●────●────○────●────✕   时间线              │ │  ●────●────○────●  时间线            │  │
│  └─────────────────────────────────────────────┘  └──────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. 自检

| # | 检查项 | 方法 | 结果 |
|---|---|---|---|
| S-1 | 组件规格条目数 ≥ 28 | 计数 §4.1–§4.28 | **28 条**（按钮 4 变体各占 1 条） |
| S-2 | 每个组件都有 尺寸 / 圆角 / 字族字号 / 内外边距 / 最小点击区 | 逐节人工核对 | ✔（题号格以「格 36 + 间隙 8 = 44px 步距」满足） |
| S-3 | 每个组件都覆盖 默认 · hover · active · focus-visible · disabled · loading · selected · error | 逐节人工核对 | ✔ 全部 8 态给出（不适用者显式写「不适用」并给出替代承载） |
| S-4 | CSS 片段不含硬编码色值 | `awk '/^### 4\./,0' component-spec.md \| awk '/^```css/,/^```$/' \| grep -n "#[0-9a-fA-F]\{3\}\|#[0-9a-fA-F]\{6\}\|rgb("` | 实跑 | ✔ **输出为空**；§4 片段只用 `var(--r-*)` / `var(--sp-*)` / `var(--fs-*)` / `var(--font-*)` / `var(--dur-*)` / `var(--ease-*)` / `var(--surface-*)` / `var(--ink-*)` / `var(--role-*)` / `var(--rule-*)` / `var(--veil-*)` / `var(--elev-*)` 等权威表 token；硬编码色值只出现在 §2.2 的 token 定义块 |
| S-5 | 不新增颜色角色 | 核对 §2.2 / §3.6 | ✔ 只有蓝 / 黄 / 红 三个角色色 + 墨色中性 |
| S-6 | 状态映射「色 + 几何」唯一，无两条状态共用组合 | 核对 §3.6 | ✔ 9 条唯一（新增「判定正确 / 答对 = 中性墨 `--ink-strong` + `check`」，与「已作答 = 蓝 + `filled`」不再共用组合） |
| S-7 | 黄色不承载文字 | 核对 §2.2 / §3.5 / §4.12 / §4.15 / §4.16 | ✔ 黄底文字一律取 `--ink-on-warm` |
| S-8 | 无界面渐变 / 无玻璃拟态 / 无霓虹 / 无背景图案 | `grep -n "gradient\|backdrop-filter\|blur("` | ✔ 仅骨架屏用平移实色块（§4.22）；§4.24 遮罩为纯色不透明度 |
| S-9 | 图标全部引用本地 SVG 资产名，不定义资产 | 核对 §4.4 / §4.11 / §4.21 / §4.25 / §4.27 | ✔ 只引用 `asset-icon-*.svg` / `asset-still-*.svg` |
| S-10 | 命中区 ≥ 44px | 核对 §3.1 与各组件 | ✔ 全部有机制说明 |
| S-11 | 焦点环无双 `outline: none` | `grep -n "outline: none"` | ✔ §4 无一处；§3.2 显式禁止 |
| S-12 | 控件一致性对照表覆盖全部原生控件 | grep 实测 8 / 13 / 7 / 66 | ✔ §5.2–§5.5 全部逐条给出行号 |
| S-13 | 图谱页控件列入冻结项 | 核对 §5.6 | ✔ 9 处列入不改 |
| S-14 | 载荷不变的兼容说明 | 核对 §4.7 | ✔ 明确要求 hidden input 承载原 `name`/`value` |
| S-15 | 深浅两套差异逐组件给出 | 人工核对 | ✔ 每节均有「深浅差异」或标注「唯一形状、值集自动切换」 |
| S-16 | 引用本文件之外的文件不越权 | 核对 | ✔ 只引用 `decisions.md` / `proposal.md` / `acceptance.md` / `SYNTH.md` / `F08.md` / `F03.md` / `F06.md` 的既有事实 |

### 8.1 待核项（不臆断，留给实现阶段实测）

| # | 待核 | 查证方式 |
|---|---|---|
| U-1 | §2.2 对比度为手算近似值 | token 层定稿时用脚本复算 WCAG 相对亮度；本文数值**不得**作为放行依据 |
| U-2 | `pages.py:427,428` 两个 `icon-btn` 是否已有可访问名 | 读 `pages.py:427-428`，缺则补 `aria-label` |
| U-3 | `pages.py:440` 的 `chip` 筛选是否可横向滚动（决定用分段控件还是标签行） | 读 `records.py` 渲染逻辑与实测宽度 |
| U-4 | `#goal-kind` 只有 2 个选项，是否值得降级为分段控件 | 产品判断；若改，需同步 §5.2 第 3 行 |
| U-5 | `#paper-rating` 的 `button.rate` 是 JS 生成还是服务端渲染（决定 §5.5 定位行） | `grep -rn "rate" workbench/server/static/*.js` |
| U-6 | 吐司是否与「活动浮层」（`pages.py:113` `_agent_activity_float`）共用右上角区域 | 决定两者是否需上下错位 |

### 8.2 与其它工件的接口

| 工件 | 本文件对它的要求 |
|---|---|
| token 规格（`design.md`） | 提供 §2.1–§2.3 的**同名** token；改动对比度相关值需回到 §2.2 复算 |
| 资产规格书 | 提供 `asset-icon-*.svg` / `asset-still-*.svg` / `asset-lamp.svg`；笔触与圆角语言须满足「图案适配原则」 |
| `specs/workbench-ui/spec.md` delta | 把本文件的状态映射、角色色配额、命中区与焦点要求写成可测 Requirement |
| `acceptance.md` | §3.1 可访问性清单、§3.6 图案资产清单、§3.4 交互反馈清单与本文件逐条对应 |
| `tasks.md` | 落地顺序建议：token 层 → 按钮 / 输入 → 下拉 → 其余控件 → 空态 / 骨架屏 → 吐司 / 对话框 |

