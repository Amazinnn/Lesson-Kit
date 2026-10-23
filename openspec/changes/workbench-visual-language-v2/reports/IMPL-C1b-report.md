# IMPL-C1b 报告 —— CSS 收尾（`.sm` 级联 bug + §4.27 折叠段 5 处）

> **本波范围**：`decisions.md` **A-126 裁决 2**（`.sm` 被形态规则盖掉 = 级联 bug）
> 与 **裁决 3**（5 处「零规则」原生 `<details>` 折叠段 ⇒ 归 CSS 波）。
> **文件所有权**：本波只写 `workbench/server/static/workbench.css` + 本报告。
> **一行 markup / 一行 JS / 一行交互都没碰**；只用既有 token；不硬编码色值；
> 图谱区段与 12 个裸名**逐字节未动**。
>
> **权威源**：`decisions.md` A-126 · `component-spec.md` §3.1（尺寸与最小点击区）·
> §4.1 / §4.2（主次按钮形态）· §4.4（图标按钮）· §4.27（折叠段）。
> **走查环境**：仓库根 cwd · 独立端口 **35711**（避开全部禁列端口）·
> `tools/walkthrough/launch.py` 的池副本 + `LESSONKIT_WB_HOME`（A1/A2/A3 硬断言通过）·
> 全程 `env -u http_proxy -u https_proxy -u all_proxy`。
> **A-39**：服务字节数 == 磁盘字节数（`served 237009 / onDisk 237009`）✔

---

## 0. 状态摘要

| 项 | 值 |
|---|---|
| **任务一（`.sm` 级联）** | **已修** —— `.sm` 真正 28px；默认 `primary`/`outline` 保持 **40px** + 44px 命中区 |
| **任务二（折叠段 5 处）** | **已落** —— 5 处同一套（48px 头 / 14px·500 / 同一条共享规则画 `▸▾`）；内距分 16px / 8px 两档；**零处卡里套卡面** |
| **仓库级验证** | **6 条命令全绿**（见 §5，原样贴出） |
| **图谱零差异** | 图谱区段**逐字节相同**（sha256 一致）✔ · **R-2 = 0** ✔ · **R-3 画布 = 0** ✔ · 三处采样点同色 ✔ |
| **命中区** | **29 个 `.sm` 调用点**逐点实测；**28 个 ≥44px ✔**；**1 个 <44px**（`#ai-paper-approval-approve`）⇒ 登记待裁决（§6.1） |
| **发现并修掉的真回归** | **1 处**（并发执行体的 `:where()` 修法把默认形态打成 36px）—— 见 §1.2 |
| **本波没做 / 打折** | **如实登记 5 项**（见 §7） |

---

## 1. 起点：并发冲突 + 一个已实测的回归

### 1.1 事件顺序（事实）

1. 本棒开工时 `workbench.css` = `bc488a40`（A-126 刚落裁决，未落 CSS）。
2. **另一个并发执行体**在本棒工作期间先提交了 A-126 的 CSS 波：
   `4e0c61b2`（`fix(workbench): A-126 三条裁决落地 —— .sm 级联 / 图标按钮中心距 / 折叠段 5 处补齐`），
   落法是 `:where(button.primary, button.outline) { height: 40px; }` + 把形态的
   `height: 40px` 从 `button.primary` / `button.outline` 里**拿掉**。
3. 本棒发现该落法有**真回归**（§1.2），报给主会话；主会话裁定**按 B 修法**，
   并把 `workbench.css` 的所有权转交本棒、叫停了对方。
4. 本棒在 `4e0c61b2` 之上改出 `54fb45dc`（本报告的 commit 1）。

### 1.2 `:where()` 单挑形态高度 = **错**（实测已否）

`:where()` 的特异度是 **0**，**低于**基类 `button { height: 36px }`（0,0,1）⇒
形态高度从 `button.primary` 里拿掉之后，**不带 `.sm` 的 `primary` / `outline`
从 40px 掉到 36px**。

实测（改动当时的工作树，真实服务 35711，Chromium 1440×900）：

```
#paper-start.primary            h=36px     ← 应为 40px
#paper-return.outline           h=36px
#paper-pause.outline            h=36px
#paper-final-submit.primary     h=36px
#paper-prev.outline             h=36px
#paper-next.primary             h=36px
#paper-review.primary           h=36px
#paper-again.outline            h=36px
#resume-practice.primary        h=36px
#answer-submit.primary          h=36px
#show-answer.outline            h=36px
#next-problem.primary           h=36px
#goto-session-end.outline       h=36px
```

⇒ 连带 §3.1 命中区回归：`button.primary::before { inset: -2px 0 }` 是**按
「40px 视觉 → 44px 命中」**写的；40 → 36 之后命中区只剩 **40px**（< 44px 硬约束）。

**⇒ 修法改为 B（主会话裁定）**：形态高度**留在形态规则里**（`height: 40px`，0,1,1），
把 `button.sm` 整条**挪到 §4.1 / §4.2 之后**（同特异度 0,1,1 ⇒ 靠**源顺序**取胜）。
（备选 B② `:where(...):not(.sm)` = (0,1,0) 也能守住，但**没选**：① `:not(.sm)`
是个「负向守卫」，将来任何新的尺寸修饰符（`.lg` 之类）都得记得改它；② 形态高度
离开形态规则会让「主按钮 40px」这条 §4.1 的事实变得不明显。B① 把整条 `.sm`
规则原样搬走，**不动 `.sm` 的任何声明**。）

---

## 2. 任务一：`.sm` 级联 bug —— 改前 → 改后 + 实测

### 2.1 CSS 改动（`workbench/server/static/workbench.css`）

**改前**（`bc488a40`，也是 A-126 之前的原状）：

```css
button { … height: 36px; … }                       /* 基类，0,0,1 */
button.sm { height: 28px; font-size: 12px; line-height: 18px;
            padding: 0 10px; border-radius: 14px; }   /* ← 984 行 */
…
button.primary { position: relative; height: 40px; … }  /* ← 1010 行 */
button.outline  { position: relative; height: 40px; … }  /* ← 1031 行 */
```

⇒ `button.sm`（0,1,1）在前、`button.primary` / `button.outline`（0,1,1）在后
⇒ 同特异度**靠后者胜** ⇒ `class="primary sm"` / `class="outline sm"` 的
**28px 被盖成 40px**。

**改后**（`54fb45dc`）：

```css
button.primary { position: relative; height: 40px; … }   /* 高度留在形态规则里 */
button.outline  { position: relative; height: 40px; … }
…
/* §4.2 之后 —— 尺寸修饰符 `.sm`（必须排在形态规则之后） */
button.sm { height: 28px; font-size: 12px; line-height: 18px;
            padding: 0 10px; border-radius: 14px; }

/* `.sm` 档不挂命中区伪元素（不许用 inset: -8px 的外溢伪元素） */
button.primary.sm::before,
button.outline.sm::before { content: none; }
```

⚠️ **`button.icon-only` 必须排在 `button.sm` 之后**（两者同特异度 0,1,1）——
这条不变量**改后依然成立**（`button.sm` 现在在 1048 行附近，`button.icon-only`
在 1122 行附近）⇒ `class="ghost sm icon-only"` 的**形态**（§4.4 的 40×40 圆）
压过 `.sm`（28px 药丸）⇒ **图标按钮不受 `.sm` 影响**。

### 2.2 实测：`.sm` 的高度（暖纸 / 夜纸各一次）

| 类别 | 改前 | 改后 | 判定 |
|---|---|---|---|
| `class="primary sm"` / `class="outline sm"` / `class="outline sm hidden"` | **40px** | **28px** | ✔ `.sm` 真正生效 |
| `class="ghost sm"` / `class="ghost sm hidden"` | 28px | **28px** | ✔ 不变 |
| `class="ghost sm icon-only"` | 40 × 40 | **40 × 40** | ✔ §4.4 形态不受影响 |
| **不带 `.sm`** 的 `button.primary` / `button.outline` | 40px | **40px** | ✔ 默认形态不变（**回归已修**） |

实测取样（`getComputedStyle(el).height`，真实服务 35711，暖纸 / 夜纸两态同值）：

```
#goal-submit.primary.sm          40px -> 28px      #ai-new-session.outline.sm      40px -> 28px
#goal-cancel.outline.sm          40px -> 28px      #ai-paper-approval-cancel       40px -> 28px
#goal-assist-send.outline.sm     40px -> 28px      #ai-paper-approval-approve       40px -> 28px
#save-rating.primary.sm          40px -> 28px      #ai-queue-continue.outline.sm    40px -> 28px
#cancel-rating.ghost.sm          28px -> 28px      #ai-stop.outline.sm              40px -> 28px
#retry-practice.outline.sm       40px -> 28px      #ai-send.primary.sm              40px -> 28px
#review-rating-action.outline.sm 40px -> 28px      #settings-close.outline.sm       40px -> 28px
#workload-prefill.outline.sm     40px -> 28px      .primary.sm / .outline.sm / .ghost.sm（试卷卡动作区）
goal-edit / goal-delete .ghost.sm 28px -> 28px      #mobile-nav-toggle / #mobile-ai-toggle / #agent-activity-toggle
                                                 / .agent-aux-collapse / #ai-session-back（icon-only）40x40 -> 40x40
```

### 2.3 实测：默认形态的命中区（`primary` / `outline` **不带** `.sm`）

| 项 | 实测 |
|---|---|
| 视觉高 | **40px**（14 处默认形态调用点全部） |
| `::before` | `content: ""` · `inset: -2px 0px` ⇒ **命中区 40 + 2 + 2 = 44px** ✔ |
| 探针实测 | `#paper-item-submit.primary`（真实可见）：**5/5 探针点命中按钮本体**（中心 + 上下 ±21px）✔ |

> 其余默认形态调用点（`#paper-start` / `#resume-practice` / `#answer-submit` …）
> 位于**默认折叠/隐藏**的容器里，探针落在覆盖它们的别的元素上 ⇒ **不可测**，
> 只以「视觉 40px + `::before` inset -2px」这条**确定性 CSS 事实**为据（见 §7.3）。

### 2.4 实测：29 个 `.sm` 调用点的**相邻命中区中心距**

判定口径（A-126 裁决 2 第 4 条 + §3.1 方法 2）：**相邻可点目标的中心距 ≥ 44px**。
「相邻」取两个口径各测一遍：**① 同一容器里的相邻可点目标**；**② 全文档最近的可点目标**（更严）。

| # | 调用点（`file:line`） | 类别 | 改前 h | 改后 h | 改前半径 | 改后半径 | 同容器相邻中心距 | 全文档最近中心距 | 判定 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `pages.py:238` `#mobile-nav-toggle` | ghost sm icon-only | 40 | 40 | 50% | 50% | — | 89.73 | ✔ |
| 2 | `pages.py:240` `#mobile-ai-toggle` | ghost sm icon-only | 40 | 40 | 50% | 50% | — | 89.73 | ✔ |
| 3 | `pages.py:279` `#agent-activity-toggle` | ghost sm icon-only | 40 | 40 | 50% | 50% | — | 240.25 | ✔ |
| 4 | `pages.py:292` `.agent-aux-collapse` | ghost sm icon-only | 40 | 40 | 50% | 50% | — | 212.57 | ✔ |
| 5 | `pages.py:335` `#retry-practice` | outline sm hidden | 40 | **28** | 12px | 14px | — | 403.30 | ✔ |
| 6 | `pages.py:340` `#review-rating-action` | outline sm hidden | 40 | **28** | 12px | 14px | — | 322.67 | ✔ |
| 7 | `pages.py:347` `#save-rating` | primary sm | 40 | **28** | 12px | 14px | — | 230.87 | ✔ |
| 8 | `pages.py:348` `#cancel-rating` | ghost sm hidden | 28 | 28 | 14px | 14px | — | 225.76 | ✔ |
| 9 | `pages.py:445` `.goal-edit` | ghost sm | 28 | 28 | 14px | 14px | 60 | 60 | ✔ |
| 10 | `pages.py:446` `.goal-delete` | ghost sm | 28 | 28 | 14px | 14px | 60 | 60 | ✔ |
| 11 | `pages.py:460` `#goal-submit` | primary sm | 40 | **28** | 12px | 14px | — | 158.56 | ✔ |
| 12 | `pages.py:461` `#goal-cancel` | outline sm hidden | 40 | **28** | 12px | 14px | 68 | 68 | ✔ |
| 13 | `pages.py:469` `#goal-assist-send` | outline sm | 40 | **28** | 12px | 14px | 219.54 | 158.56 | ✔ |
| 14 | `pages.py:654` `#knowledge-sort-direction` | ghost sm | — | — | — | — | **89（按容器 gap 8px + select 118px 推算）** | — | ✔（推算，见 §7.2） |
| 15 | `pages.py:801` `[data-set-start]` | primary sm | 40 | **28** | 12px | 14px | 63 | 63 | ✔ |
| 16 | `pages.py:803` `[data-set-rename]` | outline sm | 40 | **28** | 12px | 14px | 110 | 110 | ✔ |
| 17 | `pages.py:804` `[data-set-export]` | outline sm | 40 | **28** | 12px | 14px | 110 | 110 | ✔ |
| 18 | `pages.py:805` `[data-set-delete]` | ghost sm | 28 | 28 | 14px | 14px | 110 | 110 | ✔ |
| 19 | `pages.py:892` `#settings-close` | outline sm | 40 | **28** | 12px | 14px | — | 300.83 | ✔ |
| 20 | `pages.py:1061` `#ai-new-session` | outline sm | 40 | **28** | 12px | 14px | — | 53.04 | ✔ |
| 21 | `pages.py:1071` `#ai-session-back` | ghost sm icon-only | 40 | 40 | 50% | 50% | — | 130.05 | ✔ |
| 22 | `pages.py:1086` `#ai-paper-approval-cancel` | outline sm | 40 | **28** | 12px | 14px | — | 62.61 | ✔ |
| 23 | `pages.py:1087` `#ai-paper-approval-approve` | primary sm | 40 | **28** | 12px | 14px | — | **33.84** | **✘**（见 §6.1） |
| 24 | `pages.py:1095` `#ai-queue-continue` | outline sm hidden | 40 | **28** | 12px | 14px | — | 75.31 | ✔ |
| 25 | `pages.py:1104` `#ai-stop` | outline sm hidden | 40 | **28** | 12px | 14px | — | 129.99 | ✔ |
| 26 | `pages.py:1105` `#ai-send` | primary sm | 40 | **28** | 12px | 14px | — | 129.47 | ✔ |
| 27 | `pages.py:1511` `#workload-prefill` | outline sm hidden | 40 | **28** | 12px | 14px | — | 706.95 | ✔ |
| 28 | `practice-flow.js:1616` `#filter-clear` | ghost sm | — | — | — | — | **64（按 `.filter-actions { gap: 8px }` 推算）** | — | ✔（推算，见 §7.2） |
| 29 | `practice-flow.js:1617` `#filter-close` | outline sm | — | — | — | — | 同上 | — | ✔（推算，见 §7.2） |

**⇒ 29 个调用点里 28 个 ≥44px ✔、1 个 <44px ✘（`#ai-paper-approval-approve`）**
⇒ 按 A-126 裁决 2 第 4 条，**没有需要退掉 `.sm` 的调用点**（唯一那一处的成因见 §6.1，
它不是「容器给不出 44px」，而是**该状态在真实 UI 里不可达**）。
⇒ **没有改任何 markup**（`.sm` 全部保留）。

**顺带核到的一条**（并发执行体已修、本波保留）：`.ai-session-actions { gap: 2px }`
里两个 40×40 圆形图标按钮中心距只有 **42px** ⇒ 两个 44×44 命中盒**重叠 2px**
⇒ 该容器 gap 改 **4px** ⇒ 中心距 **44px** ✔（`4e0c61b2` 已落，本波实测确认：
**改前 42 → 改后 44**，重叠由「有」变「无」）。

### 2.5 改动的连带效果（**必须知道**）

`.sm` 挪到形态规则之后 ⇒ `.sm` 自己的 `border-radius: 14px`（药丸）现在也
**压过**形态的 `--r-md`（12px）⇒ **`primary sm` / `outline sm` 的圆角从 12px 变 14px**。

- **好处**：`.sm` 档**四类形态一致**（都是 14px 药丸），与本来就已经是 14px 的
  `ghost sm` 对齐 ⇒ 「`.sm` 就是小号药丸」这一语义自洽。
- **代价**：`.sm` 主/次按钮的圆角变了（**用户可感知**）。这是 B 修法（源顺序）
  相对 B②（`:not(.sm)` 守卫）**唯一**的视觉差；B② 会保留 12px。
  ⇒ 登记为**待裁决项**（§6.2）。

---

## 3. 任务二：§4.27 折叠段 —— 6 处逐条「改前 → 改后」

### 3.0 落地口径（主会话裁定的「外观一致 + 内距分两档」）

| 项 | 取值 | 5 处是否一致 |
|---|---|---|
| 头行 `min-height` | **48px** | ✅ 完全一致 |
| 头行字号 / 字重 / 行高 | `--fs-body` (14px) / **500** / 继承（22px） | ✅ 完全一致 |
| 展开标记 | **`▸` → `▾`**，11px `--ink-faint`，头行第一个 flex 项 | ✅ **同一条共享选择器列表** ⇒ 由构造保证 |
| 焦点环 | 全局 `:focus-visible` 单圈（`--focus-width` 2px / `--focus-offset` 2px / `--focus-outer`） | ✅ 本块**不写** `outline` |
| 内距 | 独立页块 **16px** / 卡内宿主 **8px** | ⚠️ **允许分两档**（宿主已有一张卡的留白） |
| 卡面 | 只有**独立页块**带；卡内 4 处**不套第二层卡面** | ⚠️ 允许（**不许卡里套卡面**） |

### 3.1 六处逐条

| # | 站点 | markup | 宿主是不是卡 | 改前 | 改后 | 双层卡面？ |
|---|---|---|---|---|---|---|
| 1 | `.practice-reference` | `practice-flow.js:958` | **否**（与 `.practice-solution` 同级的**独立页块**） | **零规则**：头高 22px、字号 14px/400、无标记、**无卡面** | **卡面**（`--surface-card` + `--elev-1` + `--r-md` + `overflow: hidden`）+ 48px 头 + `▸▾` 标记 + 头内距 16px + 内容内距 `0 16px 16px` | ❌ 无（它是**自己**那张卡） |
| 2 | `.practice-set-card-body` | `pages.py:794` | **是**（宿主 `.practice-set-card` = `article.card`，卡沿 22px 留白） | **零规则**（头 = `summary.practice-set-card-head`，自带三角） | **不套卡面**（宿主提供）+ 头 `min-height: 48px` + `align-items: center` + 排版（`--font-ui` / 14px / 500）+ **标记并进共享规则** + 题单内容内距 `0 8px 8px` | ❌ 无 |
| 3 | `.practice-set-continuation-details` | `pages.py:769` | **是**（`.practice-set-card` 之内） | **零规则**：头高 22px、无标记、无内距 | 48px 头 + `▸▾` 标记 + 14px/500 + 头内距 **8px** + 内容内距 `0 8px 8px` | ❌ 无 |
| 4 | `.practice-set-unavailable-items` | `pages.py:765` | **是**（同上） | **零规则** | 同 #3（同一套共享选择器列表） | ❌ 无 |
| 5 | `.active-practice-continuation-details` | `pages.py:330` | **是**（`.active-practice-resume.card` 之内） | **零规则** | 同 #3（同一套共享选择器列表） | ❌ 无 |
| 6 | **`.practice-set-card-head`**（#2 的**头行**，结构与前四处不同） | `pages.py:795` | — | 自带 `display:flex; align-items:flex-start; justify-content:space-between; gap:18px` + **自带三角**（`content:"▸"` / `[open]` → `"▾"`，ink-faint 11px `line-height:1.7`） | **不接管它的 flex 布局**（`gap: 18px` / `space-between` 照旧）；只并入同一套的**高度（48px）/ 纵向对齐（center）/ 排版（`--font-ui` / 14px / 500）**；**三角规则删掉**，改由**共享的 5 处标记规则**接管（同一套字符 / 颜色 / 字号 / 行高） | — |

> **第 6 处怎么处理的（任务书第 3 条）**：`.practice-set-card-body` 的头
> **不是**普通的 `summary` —— 它是 `summary.practice-set-card-head`，里面是
> 「`<h2>` 标题 + `<p class="muted">` + 三个动作按钮」。
> ⇒ **不能**照抄 `> summary { display:grid; gap: var(--sp-2); padding: 0 16px }`
> 那套（会打掉它自己的 `gap: 18px` / `space-between` 布局）。
> ⇒ 落法：**共享选择器列表只覆盖「头行取值」里与结构无关的那几项**
> （高度 / 纵向对齐 / 排版），**它自己的 flex 布局一个字没动**；
> **标记**用**同一条共享规则**接管 ⇒ 5 处的「形状与位置」由构造保证一致。

### 3.2 实测（暖纸 / 夜纸同值；`getComputedStyle`）

| class | 头 `min-height` | 头高 | 头 `padding` | 字号 / 字重 / 行高 | 标记（闭 → 开） | 焦点环 | 卡面底 / 阴影 / 圆角 | 内容内距 |
|---|---|---|---|---|---|---|---|---|
| `.practice-reference` | **48px** | 48 | `0px 16px` | 14px / 500 / 22px | `"▸"` → `"▾"` | `solid 2px rgb(43,98,232)` off 2px | `rgb(255,253,247)` / `--elev-1` / 12px | `0px 16px 16px` |
| `.practice-set-card-body` | **48px** | 112（标题块更高） | `0px`（宿主卡沿 22px 承担） | 14px / 500 / 22px | `"▸"` → `"▾"` | 同上 | 透明 / none / —（宿主提供） | `0px 8px 8px`（落在题单 `.practice-set-items` 上） |
| `.practice-set-continuation-details` | **48px** | 48 | `0px 8px` | 14px / 500 / 22px | `"▸"` → `"▾"` | 同上 | 透明 / none / — | `0px 8px 8px` |
| `.practice-set-unavailable-items` | **48px** | 48 | `0px 8px` | 14px / 500 / 22px | `"▸"` → `"▾"` | 同上 | 透明 / none / — | `0px 8px 8px` |
| `.active-practice-continuation-details` | **48px** | 48 | `0px 8px` | 14px / 500 / 22px | `"▸"` → `"▾"` | 同上 | 透明 / none / — | `0px 8px 8px` |

**改前**（`bc488a40`）同一批站点的头行：**`min-height: 0px` / 头高 22px /
字号 14px / 字重 400 / 标记 `none`（`.practice-set-card-body` 除外，它有三角）/ 内容内距 `0px`**。

### 3.3 实测：开合行为与键盘可达性（一个字都没碰交互）

| class | 点击 | 点击（再点） | 键盘 Enter | 键盘 Space | `summary` 可聚焦 | `tabIndex` |
|---|---|---|---|---|---|---|
| `.practice-reference` | 开 ✔ | 关 ✔ | 开 ✔ | 关 ✔ | ✔ | 0 |
| `.practice-set-card-body` | 开 ✔ | 关 ✔ | 开 ✔ | 关 ✔ | ✔ | 0 |
| `.practice-set-continuation-details` | 开 ✔ | 关 ✔ | 开 ✔ | 关 ✔ | ✔ | 0 |
| `.practice-set-unavailable-items` | 开 ✔ | 关 ✔ | 开 ✔ | 关 ✔ | ✔ | 0 |
| `.active-practice-continuation-details` | 开 ✔ | 关 ✔ | 开 ✔ | 关 ✔ | ✔ | 0 |

⇒ 原生 `<details>` 的开合与键盘可达性**完全保留**（CSS 只动了外观）。
⇒ 头行高 48px ⇒ **命中区 ≥44px 天然达标** ✔。

---

## 4. 图谱零差异（逐字节 + 逐像素）

### 4.1 图谱区段**逐字节不变**

```
graph region bytes  before=23235 after=23235  identical=True
graph region sha256 before=18601dd6d3268fef23cde06aefde17a52c91ed2233e88f727c7b316799429292
graph region sha256 after =18601dd6d3268fef23cde06aefde17a52c91ed2233e88f727c7b316799429292
full css sha256 before=6046575b1b2045453f6d3b0374c034e98d557f918cbabb7f8aa1d154564f17b9
full css sha256 after =ec58a857aa995698890fc26ad2417508c3d6b2ca1646160cb6593a48bb35d135
```

⇒ 从 `/* Knowledge graph V2` 到文件尾，**逐字节相同**。
⇒ **12 个裸名**各声明 **1 次**，改前改后同值：

```
--paper 1/1   --ink 1/1    --hair 1/1   --blue 1/1   --blueSoft 1/1  --yellow 1/1
--yellowSoft 1/1  --red 1/1  --redSoft 1/1  --green 1/1  --graphite 1/1  --shadow 1/1
```

### 4.2 逐像素：R-2 = 0 / R-3 = 0

采集协议照抄 `tools/walkthrough/g5.py`（§6.5 九步：reduced-motion + 字体就绪 +
滚动归零 + 求解器静默 + 视口截图），**两侧只差 `workbench.css`**：

| 口径 | 结果 |
|---|---|
| **R-2**（`.graph-workspace` 裁剪矩形 `[320,272,660,608]`） | **AE = 0**（`perBand: [0,0,0]`）✔ |
| **R-3**（画布矩形 `[320,284,660,596]`） | **AE = 0** ✔ |
| **R-3 采样点**（左栏纸面 / 右栏纸面 / 画布左上） | `243,241,234` = `243,241,234`；`255,254,250` = `255,254,250`；`252,250,246` = `252,250,246` ✔ |
| 图谱页整页差异 | **38,650 px**，差异 bbox = **(1037, 80, 1424, 734)** = **Agent 右栏**（`rightPaper` rect `[1037,80,387,788]`）—— **共享外壳**，按 A-126 裁决 1「R-1 = 图谱专属区」**不在图谱冻结范围** ✔ |
| 归因（同一协议下） | `bc488a40` → 并发版（`4e0c61b2`）= 38,472 px（同一 bbox）；`bc488a40` → 本波 = 38,650 px（同一 bbox）；并发版 → 本波 = **274 px**（bbox `(1380,83,1424,111)`，即右栏顶部——**默认形态 36px→40px 的还原** + `.sm` 圆角 12→14） |

> ⚠️ **`tools/walkthrough/g5.py` 的 R-1 数字不可用**：它的 `_diff_pixels` 把
> **被 mask 的全部像素**（不是「被 mask 且不同」的像素）从总数里减掉 ⇒
> 本例 `115,950 − 312,320 → 0` ⇒ R-1 会**假绿**。本报告因此**不引用 g5 的 R-1**，
> 改用「差异 bbox」直接说明差异区域。**这不是本波改的**，只是如实登记（§6.4）。

---

## 5. 六条验证命令（原样结果）

```
$ python -m pytest tests -q
........................................................................ [ 42%]
...
.............................                                            [100%]
1181 passed in 240.03s (0:04:00)
```

```
$ python -m compileall -q lessonkit.py workbench pipeline pool tests
（无输出，exit 0）
```

```
$ openspec validate --specs --strict
✓ spec/practice-review
✓ spec/practice-set-export
✓ spec/problem-difficulty
✓ spec/retrieval-evaluation
✓ spec/review-workbench
✓ spec/workbench-content-governance
✓ spec/workbench-ui
Totals: 19 passed, 0 failed (19 items)
```

```
$ python lessonkit.py guard extract-problems --course dmath --chapter ch06
Gate: extract-problems
Course: dmath
Chapter: ch06
Result: PASS

All required artifacts exist and check files contain no blocking markers.
```

```
$ node --test tests/workbench/*.test.js
✔ running immediate mode survives the preference change (0.8499ms)
✔ running batch mode survives the preference change (0.7986ms)
✔ running off mode survives the preference change (0.9301ms)
✔ an empty rating input is rejected inline instead of dying on the server (1.4705ms)
ℹ tests 264
ℹ suites 0
ℹ pass 264
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1003.882
```

```
$ node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json
  differences     : 0

[summary]
  compared nodes  : 96
  coordinate diffs: 0
  seed diffs      : 0
  id set diffs    : 0
  total differences: 0

RESULT: PASS — converged coordinate diff = 0 (SI-0 green)
```

```
$ python tools/verify_tokens.py
| focus-outer / surface-card                 | 3.0     | 5.14:1    | 8.57:1    | PASS          | PASS          |
| focus-outer / surface-base                 | 3.0     | 4.94:1    | 9.16:1    | PASS          | PASS          |
| focus-inner / role-blue                    | 3.0     | 5.14:1    | 6.07:1    | PASS          | PASS          |
| art-ink / art-paper                        | 3.0     | 14.78:1   | 12.06:1   | PASS          | PASS          |

不适用配对（不计入不达标项）：1 项 ['--ink-body / --surface-code']
   --ink-body / --surface-code —— 权威表 §4.4-11 —— 代码面上的文字一律用 --ink-inverse，该配对本身不成立（浅色主题 1.37:1 是设计上的反白面，不是可读性缺陷）
低于判定线的配对：0 项

结论：全部适用配对达标。
```

> `guard problem-set` **未跑** —— 按 AGENTS.md 纪律 6，它是「工作区产物验收」，
> 只在对应输出已生成时运行，且干净 checkout 不跟踪 `output/` ⇒ 不是仓库级 CI 前置条件。

---

## 6. 待裁决项（**拿不准的登记，不自行拍板**）

### 6.1 `#ai-paper-approval-approve`（`pages.py:1087`）的相邻中心距 **33.84px**（< 44px）

- **事实**：该按钮在 `#ai-paper-approval`（`class='ai-paper-approval hidden'` ⇒
  **默认隐藏**，只在 Agent 提议改卷时出现）里。实测（把隐藏容器揭示后）：
  它与右栏一个 40×40 圆形图标按钮（`.ai-session-actions` 的会话项动作钮）的
  中心距 = **33.84px**（**改前 17.46px** ⇒ 本波反而**更远**了）。
- **为什么判它不是真冲突**：那个 42→44px 的会话列表**与审批面板在真实 UI 里
  互斥**（聊天视图 vs 会话列表视图）⇒ 「同时可见」只可能出现在本报告的
  *reveal* 手法里 ⇒ 这两个数是**揭示手法下的几何**，不是用户可达的态。
- **处置**：**本波不改 markup**（不许改 DOM）⇒ 登记。若所有者认为该态需要处理，
  候选是① 审批面板出现时把会话列表滚开/收起（**属交互改动**，归下一波）；
  ② 给 `.ai-paper-approval-actions` 的按钮去掉 `.sm`（**属 markup 改动**）。

### 6.2 `.sm` 的圆角 12px → **14px**（B 修法的连带效果）

- **事实**：见 §2.5。`primary sm` / `outline sm` 的圆角随 `.sm` 一起变成 14px 药丸。
- **候选**：① 保持 14px（`.sm` 档四类形态一致，语义自洽）；
  ② 改用 B②（`:where(button.primary, button.outline):not(.sm) { height: 40px }`）
  ⇒ 圆角回到 12px，代价是引入 `:not(.sm)` 负向守卫。
- **本波未自行选边**（选了 B① 并把连带效果登记在此）。

### 6.3 第 6 处折叠段 `.practice-set-item-body` 仍是「卡面套在卡里」

- **事实**：`.practice-set-item-body`（C1 已统一的那一处）是**一张卡面**
  （`--surface-card` + `--elev-1`），而它的宿主 `.practice-set-card` 也是
  `article.card` ⇒ **双层卡面**。裁决 3 说「不许卡里再套一层卡面」，
  但这处**不在本波 5 处里** ⇒ 本波**没动它**。
- **候选**：① 下一波把它降级成「只取头行」（与本波 4 处一致）；
  ② 保留（C1 已验收的 §4.27 样板，且 §4.27 原裁定就是「卡面 + 48px 头 + 内容在同一张卡里」）。

### 6.4 `tools/walkthrough/g5.py` 的 R-1 计算有 bug（**本波没改**，不在文件所有权内）

- **事实**：`_diff_pixels` 把**被 mask 的全部像素**（不是「被 mask 且不同」的像素）
  从总数里减掉 ⇒ 本例 `115,950 − 312,320 → 0` ⇒ **R-1 会假绿**。
- **本波处置**：不引用它的 R-1，改用「差异 bbox」直接说明差异区域（§4.2）。
  **修不修、谁修** ⇒ 登记（`tools/walkthrough/` 不在本波文件所有权内）。

### 6.5 `.practice-reference` 的真实渲染路径本波**没驱动**

- **事实**：它由 `practice-flow.js` 的**章节练习「回看上一题」**路径产出
  （`reviewResultHtml(item, paperReview=true)`）；本波走的是**试卷流**，
  未把该路径驱动起来 ⇒ 用**逐字取自 `practice-flow.js:958` 的同一份 markup**
  注入同一个页面来量它的头行与内容内距（**CSS 与插入点无关**）。
- **处置**：§3.2 / §3.3 的 5 处数值对 `.practice-reference` 而言是
  **「逐字 markup + 真实 CSS + 真实 token」**下的实测；
  **真实流程下的复测**建议归下一波页面波次。

---

## 7. 本波**没做 / 打折**的地方（诚实说明）

1. **`.practice-reference` 的真实流程没驱动** —— 见 §6.5（用逐字 markup 注入实测）。
2. **两个调用点的真实几何不可达** —— `#knowledge-sort-direction`（`pages.py:654`）
   与 `#filter-clear` / `#filter-close`（`practice-flow.js:1616-1617`）
   在本轮页面状态下**不在 DOM 里**（前者由 JS 在知识点面板打开时渲染，后者
   是筛选浮层按需创建）⇒ 中心距按**容器间距推算**（`.knowledge-sort-bar { gap: 8px }`
   ⇒ 89px；`.filter-actions { gap: 8px }` ⇒ 64px），**不是实测值**。
3. **部分默认形态按钮的命中区探针不可测** —— `#paper-start` / `#resume-practice` /
   `#answer-submit` 等位于默认隐藏的容器里，探针落在覆盖它们的别的元素上
   ⇒ 只以「视觉 40px + `::before { inset: -2px 0 }` ⇒ 44px」这条确定性 CSS 事实为据；
   真实可见的 `#paper-item-submit.primary` 探针 **5/5 命中本体** ✔。
4. **截图没交** —— 本波只交**数值证据**（未新增 `reports/IMPL-C1b-shots/`）。
5. **`guard problem-set` 未跑** —— 见 §5 末尾（按 AGENTS.md 纪律 6）。
6. **与并发执行体的落法差异**：并发版 `4e0c61b2` 已先落地；本波在其之上
   ① 把 `:where()` 修法**换成 B 修法**（修 36px 回归）、② 折叠段的「展开标记」
   从「各写各的」收成**一条共享规则**、③ `.practice-set-card-body` 的头行
   **并入同一套排版**（`--font-ui` / 14px / 500）、④ 题单补 8px 内容内距。
   ⇒ 两版的**共同部分**（`.sm` 28px、图标按钮 gap 4px、4 处卡内折叠段的头行）
   **实测结果一致**。

---

## 8. commit 清单（**只碰 `workbench/server/static/workbench.css` + 本报告**）

| # | hash | 主题 | 内容 | 改动量 |
|---|---|---|---|---|
| 1 | **`54fb45dc`** | **本波主体** | ① **`.sm` 级联改 B 修法**：`button.sm` 挪到 §4.1/§4.2 之后；形态的 `height: 40px` 还回 `button.primary` / `button.outline`（修 `:where()` 的 36px 回归）；`.sm` 档 `::before { content: none }` 保留 ② **§4.27 折叠段 5 处统一**：48px 头 / 14px·500 排版 / **一条共享规则**画 `▸▾` 标记；内距 16px（独立页块）/ 8px（卡内宿主）；4 处卡内**不套第二层卡面**；题单补 8px 内容内距 ③ 删掉 `.practice-set-card-head::before` 的旧三角规则（并进共享规则） | workbench.css **+81 / −37** |
| 2 | **（本报告）** | 报告 | `reports/IMPL-C1b-report.md` | — |

> ⚠️ 两个 commit 都是 **`git add -- <路径>` + `git commit -m "…" -- <路径>`**
> （**两个都带路径**）⇒ 并发执行体随时 add 的东西**不会**被带进来。
