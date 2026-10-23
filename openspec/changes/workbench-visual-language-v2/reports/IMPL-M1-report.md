# IMPL-M1 报告 — 动效四条 FAIL 的修复 + 执行器两处口径修正

> **本波的任务**：`decisions.md` **A-134** 派工的 `IMPL-M1` ——
> 把动效验收的**四条 FAIL** 修掉，并把 `tools/walkthrough/frames.py` 的
> **两处口径分歧**（D-2 / D-3）修对。
> **判据一个字未改**（`acceptance.md` / `motion-spec.md` / `decisions.md` /
> `tasks.md` / `component-spec.md` / `docs/**` / `tests/**` 全部零改动）。
>
> **上游产物**：`reports/MOTION-VERIFICATION.md`（689 行，PASS 8 · FAIL 4 · PENDING 1）
> + `reports/MOTION-VERIFICATION/`（分镜条 / strip / 孪生对 / 逐条 JSON）。
>
> **本波产物**：本报告 + `reports/MOTION-VERIFICATION-AFTER/`（改后证据）
> + 两个 commit（产品一处、执行器一处）。

---

## 0. 结论速览

| # | 条目 | 改前 | 改后 | 一句话 |
|---|---|---|---|---|
| **M-1** | 台灯转场第四段（收回） | **FAIL** | **PASS** | 收回关键帧此前**无人挂** ⇒ 灯是到 700ms 被**直接删掉**的；现在 590–700ms 真的演收回 |
| **M-10** | 数据层 · 日历扩散 | **FAIL** | **PASS** | 规格 §2.1 第 19 项的**日历扩散**此前只做了负荷柱；现在日历格按列展开 |
| **M-12** | 分级降级 · 横幅退场 | **FAIL** | **PASS** | 降级档横幅**永不退场**（opacity 1 vs 动效档 0）；现在四组合都在 hold 后退场 |
| **D-2** | `frames.py` 的 M-9 判据 | FAIL（**口径作废**） | **PASS**（按 A-117） | 判的是 A-115 已作废的「微光位置」；改成「块自身表面随时间变化」 |
| **D-3** | `frames.py` 的 M-4 触发顺序 | PASS（**看不见**） | **PASS**（看得见） | 顺序与产品相反 ⇒ 横幅从不亮；判据只数 DOM 个数 |
| M-11 / M-12 终态铁律 | 降级帧 vs 动效帧 | 唯一不一致 = **横幅退场** | **13/13 逐项一致，差异 0** | 横幅这一处也归零了 |

**动效验收总账**：改前 **PASS 8 · FAIL 4 · PENDING 1** ⇒
改后 **PASS 11 · FAIL 0 · PENDING 1**
（M-3 的「章节首次完成」那一档仍不可判定，与服务端没有章事实有关，**与本波无关**；
M-7 的 FAIL 已由 **A-134**（commit `086ff607`）以「改判据」结案 ——
**它不是本波修的**，本波只是在新判据下复跑：`frames.py` 的 M-7 = **PASS**
（517ms、落点 = 被选中的那一行）。逐条说明见 §3 与 §8.2）。

---

## 1. commit

| hash | 内容 | 文件 |
|---|---|---|
| **`0d9ac911`** | `fix(workbench): 台灯收回段真的演 + 日历扩散 + 降级档横幅退场` | `workbench/server/static/workbench.css` · `workbench/server/static/workbench.js` · `workbench/server/records.py` |
| **`9a262f7a`** | `fix(walkthrough): frames.py 的 M-9 判据口径与 M-4 触发顺序（执行器侧）` | `tools/walkthrough/frames.py` |
| **`（本 commit）`** | `docs(v2): IMPL-M1 报告 —— 四条 FAIL 修完（PASS 11 · FAIL 0 · PENDING 1）+ 终态铁律 13/13` | `reports/IMPL-M1-report.md` · `reports/MOTION-VERIFICATION-AFTER/**` |

> ⚠️ 第三个 commit 的 hash **不写在本文件里**（写进去就会改动自己 ⇒ hash 变 ⇒ 再写又变）——
> 用 `git log --oneline -3` 查。前两个 commit 的 hash 是稳定的（它们不含本文件）。

> 两个 commit 都只 `git add -- <路径>` + `git commit -- <路径>`，
> **未**使用 `git add -A` / `-a` / 目录级 add。

---

## 2. 四条逐条：改前 → 改后 + 实测

### 2.1 M-1 台灯转场的第四段（收回）

**根因（上游已取证）**：`@keyframes lk-lamp-retract`（`workbench.css:3876`）与
`.lk-lamp.is-in`（`:4344`）**都在 CSS 里**，但 `is-in` **全仓库无人挂**
⇒ 灯是到 700ms 被 `removeLayers()` **直接删掉**的，不是「收回」。

**改法（`0d9ac911`）**

1. `workbench.css` —— `.lk-lamp.is-in` 从「一条收回动画」改成
   **① 与 ④ 串成一条时间线**：

   ```css
   .lk-lamp.is-in {
     animation: lk-lamp-lean-out 140ms var(--ease-rebound) both,
                lk-lamp-retract 110ms var(--ease-in) 590ms forwards;
   }
   ```

   后者带 `animation-delay: 590ms`，而 `forwards` **不在延迟段回填**
   ⇒ ① 照常演（0–140ms），④ 到 **590ms** 才接手（110ms），
   结束后终态（`opacity 0` + 收回位）**留在元素上**。
   ⚠️ 这与涟漪层的退场**同构**（`.lk-ripple.is-on.is-clear` 的
   `lk-ripple-clear 110ms … 590ms forwards`）⇒ 两层退场同起同止。

2. `workbench.js` —— 转场开始时把 `is-in` 挂上（时刻由样式表给）：

   ```js
   lamp.classList.add("is-out", "is-lit", "is-in");
   ```

   ⇒ 与涟漪的 `is-clear` 同一套约定（**类**在开始时挂，**时刻**在样式表里）。

**为什么不是「590ms 时用 `setTimeout` 挂 `is-in`」**（取舍，登记在 §7）：
那样收回动画的**时间轴不锚在转场起点**，走查探针的 `setTime(t)` 会把它
寻址到任意时刻（t≥110ms 的每一帧都会显示「已收回」），分镜条会失真；
CSS 延迟锚定后 `setTime(590…700)` 逐帧都能寻址到正确的相位。

**实测（改后 · `reports/MOTION-VERIFICATION-AFTER/extra/M-1-extra.json`）**

| 帧 | 改前（`MOTION-VERIFICATION.md` §3 M-1） | 改后 |
|---|---|---|
| 0ms | 灯层 opacity 0，在画面外下方 | opacity **0**，`matrix(0.841207, -0.178804, 0.178804, 0.841207, 0, 158.4)`（画面外下方） |
| 90ms | opacity 1，探出约 2/3 | opacity **1**，identity 附近 |
| 180ms | opacity 1 + 涟漪起 | opacity **1** |
| 330ms | 涟漪推过大半 | opacity **1** |
| 500ms | opacity 1，涟漪接近铺满 | opacity **1**（**未提前消失**） |
| **700ms** | **opacity 仍为 1、transform 仍是单位矩阵、animation 仍是 `lk-lamp-lean-out`** —— **没有收回** | **opacity 0，transform `matrix(0.891241, 0.125256, -0.125256, 0.891241, 0, -36.96)`（scale .9 / translateY −36.96px / rotate ≈8°），`animationName = lk-lamp-lean-out, lk-lamp-retract`** —— **收回了** |

- **四段全在**：`① 探出 → ② 点亮 → ③ 涟漪扩散 → ④ 收回`（`checks` 9/9 全 true）。
- **700ms 后终态干净**：三层 `0 / 0 / 0`（`terminalAfter700ms`）。
- **时序未动**（A-27）：探出 140ms → 点亮 → 涟漪 140–590ms → 收回 590–700ms，
  共 ~700ms；`LAMP_CLEAN_MS = 700` **未改**。
- **涟漪层级未动**（A-1）：涟漪 `z-index = 0`（内容层之下），
  卡片六帧 `borderTopWidth 0px / borderRadius 12px / 660×264 / opacity 1`，
  命中测试**每帧命中卡片本身**（`hitIsCard: true`），`outlineChanged: false`。

---

### 2.2 M-10 数据层 · 日历扩散

**根因**：`motion-spec.md` **§2.1 第 19 项**把「**日历扩散**」列为进度带动效的
三个使用方之一，实现**只做了负荷柱** ⇒ 84 格日历 `animationName` 全程 `none`。

**规格原文（`motion-spec.md:273`，一字不改地抄）**：

> `| 19 | **进度带** | 数据层负荷柱 / 日历扩散 / 庆祝进度 | scaleX 0→1（transform-origin: left），逐柱错峰 24ms | 320ms | out | 纯 CSS | 直接落终值（柱高 100%），无生长 |`

**改法（`0d9ac911`）**

1. `workbench.css` —— 日历格落该行的形态 / 时长 / 缓动：

   ```css
   .record-activity-day {
     transform-origin: left center;
     transform: scaleX(1);                                   /* 静态样式 = 终态 */
     animation: lk-calendar-grow 320ms var(--ease-out) both;
   }
   @keyframes lk-calendar-grow {
     from { transform: scaleX(0); }
     to   { transform: scaleX(1); }
   }
   ```

2. `workbench/server/records.py` —— **逐柱错峰 24ms**：
   「柱」= 日历的**列**（网格 `grid-auto-flow: column`，7 行 = 7 个星期，
   一列 = 一周）⇒ 第 `index` 个格子在第 `index // 7` 列，
   **同一列的格子一起动**（行内 `animation-delay`，与 `.bar-fill` 同一套做法）：

   ```python
   delay = (index // _CALENDAR_ROWS) * _CALENDAR_STAGGER_MS   # 0 / 24 / 48 … 264ms
   ```

**实测（改后 · `extra/M-10-extra.json`）**

| 项 | 改前 | 改后 |
|---|---|---|
| 日历格 `animationName` | 全程 **none**（差 0 个动画） | **`lk-calendar-grow`**（84 格全带） |
| 同一列的格子 | — | **相位相同**：列 0 的 7 格在 t=120 全是 `scaleX 0.766032` |
| 逐列错峰 | — | 列 0 = `0.766032` · 列 1 = `0.672573` · 列 2 = `0.549638` · 列 10 = `0`（t=120） |
| 生长曲线 | — | t=0 `scaleX 0` → t=120 `0.766` → t=240 `0.976` → t=480 `1` |
| 行内 `animation-delay` | 无 | `0ms / 24ms / 48ms … 240ms / 264ms`（按列） |
| 双编码（颜色 + 高度） | ✔（静态） | ✔（**动画期间照常可读** —— 生长只动宽度这条不承载信息的轴） |
| 负荷柱那一半 | ✔ | ✔（**未受影响**：从 0 生长 + 24ms 错峰 + 终态满格） |

`checks` **9/9 全 true**（含「日历格按强度扩散（格子自身有生长动画）」
与「日历格终态两档一致」）。

---

### 2.3 M-12 分级降级 · 连对横幅的退场

**根因**：`showBanner()` **只加** `is-on` **从不移除**；退场只存在于
`lk-combo-out` 的 `forwards` 填充里；而降级闸门
（`animation-name: none` / `animation: none !important`）把那条动画关掉
⇒ **横幅永远留在屏上**。

**规格原文（`motion-spec.md:1137`，§7.2 第 18 行）**：

> `| 18 | 连对横幅 | 已退场 | 横幅**直接以终态出现**并在 hold 后直接消失 | 去掉 animation；**用 setTimeout 控制显隐** |`

⇒ **「用 `setTimeout` 控制显隐」那一半此前没实现。**

**改法（`0d9ac911` · `workbench.js`）**

```js
if (motionMode() !== "full") {                    /* 降级档（weak / off） */
  var hold = bannerCount >= STREAK_BANNER_EVERY * 2
    ? BANNER_HOLD_LARGE_MS : BANNER_HOLD_MS;      /* 900ms / 700ms（§6.2 的 duration） */
  banner.style.opacity = "";
  bannerTimer = window.setTimeout(function () {
    bannerTimer = null;
    if (banner.parentNode) banner.style.opacity = "0";
  }, hold);
}
```

**终态铁律怎么保住的**（这是本条最容易做坏的地方）：
动效档退场后横幅是「**`is-on` 还在 + opacity 0**」，
所以降级档**只写不透明度、绝不摘 `is-on`** ——
若摘掉 `is-on`，两档的终态类名就不同，终态铁律当场破。

**实测（改后 · `extra/M-12-extra.json`）**

| 组合 | 改前：横幅终态 opacity | 改后：横幅终态 opacity | 改后：`is-on` | 改前：与动效档的终态差异 | 改后 |
|---|---|---|---|---|---|
| 系统 reduce + 偏好未设（weak） | **1**（永不退场） | **0** | true | 横幅一项 ⚠️ | **0** |
| 系统 reduce + 偏好显式「开」（full） | 0 | **0** | true | 0 | **0** |
| 系统允许 + 偏好未设（full） | 0 | **0** | true | 0 | **0** |
| 系统允许 + 偏好显式「关」（off） | **1**（永不退场） | **0** | true | 横幅一项 ⚠️ | **0** |

`checks` **5/5 全 true**（含「四种组合的终态与「动效开启」逐项一致」与
「横幅在四种组合下都退场（hold 后不透明度 = 0）」）。
档位分级、显式优先于系统、台灯层是否创建，**全部未受影响**。

---

### 2.4 D-2 / D-3 —— 执行器的两处口径（**改怎么测，不改测什么**）

> 两处都在 `tools/walkthrough/frames.py`（`9a262f7a`）。
> `acceptance.md` / `motion-spec.md` / `decisions.md` **一个字未改**。

#### D-2 · `judge_skeleton`：按 A-117 定稿口径判 M-9

| | 改前 | 改后 |
|---|---|---|
| 判据 | A-115 **已作废**的「微光**位置**是否变化」（读 `::after` 的 transform） | **A-117 §1**：块**自身表面**（`opacity` 或 `background-color`）随时间变化 |
| `::after` 横扫 | 被当成动效证据 | **不算**（动的是覆盖层，不是块的表面） |
| 降级档 | 未判 | **只判「等价静态灰块有体积」** |
| 「有动画名就算」 | — | **不算**（要看改的是哪个属性） |
| 选择器 | `.lk-skeleton`（**降级档选不到**：降级档的灰块不带这个类） | 新增 `[data-lk-skeleton] > div` 进 `WATCH` —— **两档都选得到** |

**实测（改后 · `reports/MOTION-VERIFICATION-AFTER/frames/M-9.json`）**

- 改前：`FAIL`「骨架块有尺寸，但微光位置全程不变（动效侧）」
- 改后：`PASS`「骨架块有体积且自身表面随时间变化（**5/5 块**的不透明度变化，
  取到 **3** 个值）；降级档是等体积静止灰块」
- 证据：`ownOpacities = [1, 0.573441, 0.473633]`（块**自身**的 opacity）、
  `ownAnimations = ["lk-skeleton-breathe"]`（挂在块自身）、
  `afterAnimations = ["none"]`（横扫那一族已删）、
  `animatedSizes = 304×26 / 502×16 / 568×16 / 607×16 / 660×128`、
  `reducedBlockCount = 5` + `reducedHasVolume = true`。

#### D-3 · `act_streak` 的顺序 + `judge_streak_banner` 看可见性

| | 改前 | 改后 |
|---|---|---|
| 调用顺序 | `apply(judge)` → `render`（**与产品相反**）⇒ `showBanner()` 刚挂的 `is-on` 被随后的整块重绘冲掉 | **先重绘、后 apply** —— 与 `paper-practice.js:1141` / `practice-flow.js:1697` 同序 |
| 判据 | 只数 DOM 里有没有 `.lk-combo-banner` 元素 | **看实际可见性**：出现（opacity > 0）/ 只有一份 / 数字是参数化输入的结果 / 末帧退场（opacity 0） |

**实测（改后 · `frames/M-4.json`）**

- 改前：`PASS`「横幅只有一份」—— 但**横幅每帧 opacity 都是 0**（从没亮起来），
  判据看不见这个差别。
- 改后：`PASS`「横幅出现（**0 / 100 / 250 / 450ms**）、只有一份、
  数字是参数化输入的结果（**['5']**）、末帧退场（opacity 0）」。

---

## 3. 动效验收的前后对照

**探针**：`tools/walkthrough/motion_verify.py`（上游新增的可复用探针，本波**未改它一个字节**）
+ `tools/walkthrough/frames.py`（本波只改了执行器口径）。

**改前**（`reports/MOTION-VERIFICATION.md`，锚点 HEAD `9d050949`）
vs **改后**（本波，锚点见 §5）。

| # | 动效 | 改前 | 改前关键实测 | 改后 | 改后关键实测 |
|---|---|---|---|---|---|
| **M-1** | 台灯转场 | **FAIL** | ④ 收回段无动画；t=700 opacity 1 / 单位矩阵 | **PASS** | t=700 opacity **0** / `matrix(0.891…, 0.125…, -0.125…, 0.891…, 0, -36.96)`；9/9 checks |
| M-2 | 交卷庆祝（日常） | PASS | 数字滚动 + 进度带 + 零彩带 | PASS | 同（**未受影响**） |
| M-3 | 交卷庆祝（里程碑） | PENDING | 「章节首次完成」不可判定 | PENDING | 同（**与服务端缺章事实有关，与本波无关**） |
| M-4 | 连对横幅 | PASS | 出现 → 替换(5/10) → 退场 | PASS | 同（**且降级档也退场了** —— 见 M-12） |
| M-5 | 计数器三档 | PASS | 灰 → 黄 → 黄蓝渐变 | PASS | 同（**未受影响**） |
| M-6 | 火苗簇 | PASS | 5 簇透明度不同 | PASS | 同（**未受影响**） |
| M-7 | 挤压回弹 | FAIL | 判据漂移（**已由 A-134 改判据**，不在本波） | — | 见 §8.3 |
| M-8 | 视图转场 | PASS | 上浮峰值 12px | PASS | 同（**未受影响**） |
| **M-9** | 骨架屏 | PASS（探针）/ FAIL（`frames.py`） | `frames.py` 按作废口径判 FAIL | **PASS**（两处都 PASS） | 5/5 块自身 opacity 变化；`::after` 无动画 |
| **M-10** | 数据层 | **FAIL** | 负荷柱 ✔；日历格 `animationName` 全程 none | **PASS** | 负荷柱 ✔；日历格 `lk-calendar-grow`，按列错峰；9/9 checks |
| M-11 | 断裂负反馈 | PASS | 摆动峰值 3.93px | PASS | 同（**未受影响**） |
| **M-12** | 分级降级 | **FAIL** | 降级档横幅 opacity **1**（永不退场） | **PASS** | 四组合横幅 opacity 全 **0**；5/5 checks |
| M-13 | 关键反馈音效 | PASS | 140/140/185/190ms | — | 本波**未触**（音效资产与判据未动） |

**总账**：**PASS 8 · FAIL 4 · PENDING 1** ⇒ **PASS 11 · FAIL 0 · PENDING 1**
（M-7 的 FAIL 在 **A-134**（commit `086ff607`）里已由「改判据」结案 ——
`acceptance.md` 的 M-7 行已改成 motion-spec 的值（`.6 → 1.1 → .9603 → 1.0067 → 1`），
**本波没有再动判据，也没有再动实现**；改后复跑 `frames.py` 的 M-7 = **PASS**
「回弹动画时长 [517]」、落点 = 被选中的那一行。
⚠️ **但逐帧曲线三个数没有重测**：`motion_verify.py` 没有 M-7 条目，
`frames.py` 的 M-7 判据量的是「动画在不在 + 时长」，**不量曲线形状** ——
这一点在 §8.2 里明写，不当作「已按新判据逐帧复核」。）

### 3.1 `frames.py`（执行器口径修好之后）

| # | 改前 | 改后 |
|---|---|---|
| M-1 | PASS | PASS |
| M-2 | PASS | PASS |
| M-3 | PENDING | PENDING |
| **M-4** | PASS「横幅只有一份」（**横幅从不亮**） | **PASS**「横幅出现（0/100/250/450ms）、只有一份、数字是参数化输入的结果（['5']）、末帧退场（opacity 0）」 |
| M-5 | PASS | PASS |
| M-6 | PASS | PASS |
| M-7 | PASS | PASS |
| M-8 | PASS | PASS |
| **M-9** | **FAIL**「骨架块有尺寸，但微光位置全程不变（动效侧）」 | **PASS**「骨架块有体积且自身表面随时间变化（5/5 块…取到 3 个值）；降级档是等体积静止灰块」 |
| M-10 | PASS | PASS |

---

## 4. 终态铁律的前后对照

**判据**（`acceptance.md` §2 通用判据 / §3.8）：「降级帧的终态必须与动效开启时的
终态一致（数字、进度带、计数器档位、灯与涟漪层、纸片、火苗簇、内容位置
逐项比对），不得停在中间态或不可见。」
**怎么比**：`frames.py::compare_terminal` 对 `TERMINAL_CONTRACT` 枚举的项逐项比
（契约外的差异如实登记，不参与判定）。

| 契约项（`TERMINAL_CONTRACT`） | 改前（动效档 vs 降级档） | 改后 |
|---|---|---|
| `.lk-ticker` / `.lk-ticker-digit`（数字） | 一致 | 一致 |
| `.lk-combo-banner__count`（横幅数字） | 一致 | 一致 |
| `.lk-progress` / `.lk-progress-fill`（进度带） | 一致 | 一致 |
| `.lk-streak`（计数器档位） | 一致 | 一致 |
| `.lk-lamp` / `.lk-ripple` / `.lk-ripple-glow`（灯与涟漪层） | 一致 | 一致 |
| `.lk-flame` / `.lk-flames`（火苗簇） | 一致 | 一致 |
| `.lk-paper` / `.paper-slice`（纸片） | 一致 | 一致 |
| `#middle-page > *`（内容位置） | 一致 | 一致 |
| **契约内枚举项的差异总数** | **0** | **0** |

**契约外的差异（如实登记）**

| 项 | 改前 | 改后 |
|---|---|---|
| **连对横幅的 opacity** | **动效档 0（已退场）vs 降级档 1（永不退场）** ⚠️ **不一致** | **动效档 0 vs 降级档 0** ✔ **一致** |
| 连对横幅的 transform | 同因不一致 ⚠️ | 一致 ✔ |
| 骨架屏的类名（降级档不带 `.lk-skeleton`） | 登记 | 登记（**并已进 `WATCH`**，机器可查） |
| 骨架屏块自身 opacity（无限呼吸的相位 vs 静止 1） | 登记 | 登记（机器可查） |
| 骨架块 1px 高度差（16 vs 15） | — | 登记（机器可查） |
| 设置页的档位标签 | 登记 | 登记 |

**孪生对照（`extra/twins.json`，动效档 vs 降级档的终态）**

| # | 改前 | 改后 |
|---|---|---|
| M-1 / M-2 / M-3 / M-4 / M-5 / M-6 / M-7 / M-8 / M-9 / M-10 | 契约差异 **0**；**M-4 / M-6 契约外有横幅差异** | **10/10 `terminalEqual = true`，契约差异 0，契约外差异 0** |

**M-11 / M-12 的终态铁律**（`extra/M-12-extra.json`）：
四种组合的 `terminalDifferencesVsFullTier` **全为空数组**
（数字 / 档位 / 火苗簇 / 横幅内容 / 横幅是否点亮 **逐项一致**），
横幅终态 opacity **四组合全 0**。

---

## 5. 测量锚点

| 项 | 值 |
|---|---|
| 分支 | `feat/workbench-visual-language-v2` |
| 改前锚点 | `9d050949`（上游报告的 HEAD）· `workbench.css` **237 052** 字节 |
| 改后锚点 | `0d9ac911`（产品）+ `9a262f7a`（执行器）· `workbench.css` **239 607** 字节 |
| **并行波次** | 本波开工时 HEAD = `086ff607`；期间**另一执行体**（版式候选）落了 `941571c5`（**只改 `decisions.md`**，**未碰 `workbench.css` / `.js`**）⇒ 本波的测量与提交都不受其影响，且**没有回退**它的改动 |
| **A-39 核对** | 服务返回 **239 607** == 磁盘 **239 607**（sha256 `cb8d1bd54e4cd02c…`）⇒ **served == onDisk ✔** |
| 走查环境 | 仓库根 cwd · **两个独立端口**（3315 = 动效探针 / 3316 = `frames.py`）· 各自**独立池副本** + `LESSONKIT_WB_HOME` |
| 池隔离 | `realPoolUnchanged: true`（`launch.py` 自证）· 真实 `pool/dmath.db` 未写入 |
| 种子 | `--seed-records 120 --seed-sessions 40` · 另补 **13 天**作答（只写副本，使错峰可测） |
| 视口 / 配色 / 时区 | 1440×900 · `light` · `zh-CN` · `Asia/Shanghai` |
| 代理 | 所有命令都带 `env -u http_proxy -u https_proxy -u all_proxy` |
| 图谱区段 | 从 `/* Knowledge graph V2 …` 到文件尾**逐字节未变**（sha256 `18601dd6d3268fef…` 两边相同） |

**命令（原样）**

```bash
# ① 动效验收（改后）
env -u http_proxy -u https_proxy -u all_proxy python tools/walkthrough/launch.py \
  --port 3315 --side after \
  --out tmp/wt-m1-final/evidence/after/requests.jsonl \
  --scratch tmp/wt-m1-final/scratch \
  --seed-records 120 --seed-sessions 40 \
  --seed-pool pool/dmath.db \
  --seed-out tmp/wt-m1-final/evidence/after/seed \
  --ready-file tmp/wt-m1-final/ready.json

env -u http_proxy -u https_proxy -u all_proxy python tools/walkthrough/motion_verify.py \
  --base-url http://127.0.0.1:3315 --ws walk \
  --out tmp/wt-m1-final/evidence/extra \
  --plan tmp/wt-m1-final/evidence/after/seed/plan.json \
  --pool tmp/wt-m1-final/scratch/ws-walk/pool/dmath.db --seed-days 13

# ② 执行器（改后）
env -u http_proxy -u https_proxy -u all_proxy python tools/walkthrough/launch.py \
  --port 3316 --side after \
  --out tmp/wt-m1-final-frames/evidence/after/requests.jsonl \
  --scratch tmp/wt-m1-final-frames/scratch \
  --seed-records 120 --seed-sessions 40 \
  --seed-pool pool/dmath.db \
  --seed-out tmp/wt-m1-final-frames/evidence/after/seed \
  --ready-file tmp/wt-m1-final-frames/ready.json

env -u http_proxy -u https_proxy -u all_proxy python tools/walkthrough/frames.py \
  --base-url http://127.0.0.1:3316 --ws walk \
  --out tmp/wt-m1-final-frames/evidence/frames \
  --plan tmp/wt-m1-final-frames/evidence/after/seed/plan.json
```

**产物**：`reports/MOTION-VERIFICATION-AFTER/`（本 commit 入库）
—— `extra/*.json`（九条逐条判定 + 终态孪生表）、`frames/M-{1,4,9,10}.json`、
`M-1-strip.png` / `M-10-strip.png` / `frames/M-{4,9}-strip.png` / `M-12/*.png`。
分镜条的全套 PNG 留在 `tmp/wt-m1-final*/`（不入库，避免 +21MB）。

---

## 6. 六条验证命令的原样结果

> 全部在**仓库根**执行。

### ① `python -m pytest tests -q`

```
........................................................................ [  6%]
........................................................................ [ 12%]
........................................................................ [ 18%]
........................................................................ [ 24%]
........................................................................ [ 30%]
........................................................................ [ 36%]
........................................................................ [ 42%]
........................................................................ [ 48%]
........................................................................ [ 54%]
........................................................................ [ 60%]
........................................................................ [ 66%]
........................................................................ [ 72%]
........................................................................ [ 78%]
........................................................................ [ 84%]
........................................................................ [ 90%]
........................................................................ [ 96%]
.......................................                                  [100%]
1191 passed in 240.90s (0:04:00)
EXIT=0
```

> ⚠️ **第一次跑出现过 31 个 ERROR**（`tests/workbench/test_workspace_layout.py`），
> 全部是 `tmp_path` fixture 的 `FileNotFoundError:
> C:\Users\yanwei\AppData\Local\Temp\pytest-of-yanwei\pytest-831` ——
> **环境问题**（临时目录被并发清理），与本波改动无关：
> 单独重跑该文件 `31 passed`，重跑全套 `1191 passed`。
> **上面这一份是「三个 commit 都落完之后」在最终工作树上重跑的读数。**

### ② `python -m compileall -q lessonkit.py workbench pipeline pool tests`

```
（无输出 = 全部编译通过）
EXIT=0
```

### ③ `openspec validate --specs --strict`

```
- Validating...
✓ spec/agent-assisted-practice-records
✓ spec/agent-context
✓ spec/agent-contract-disclosure
✓ spec/agent-learning-evidence
✓ spec/ai-teacher-bridge
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

### ④ `python lessonkit.py guard extract-problems --course dmath --chapter ch06`

```
Gate: extract-problems
Course: dmath
Chapter: ch06
Result: PASS

All required artifacts exist and check files contain no blocking markers.
EXIT=0
```

### ⑤ `node --test tests/workbench/*.test.js`

```
ℹ tests 264
ℹ suites 0
ℹ pass 264
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 859.7419
EXIT=0
```

### ⑥ `node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json`

```
=== graph-layout-diff (diff) ===

[quantization — the comparison contract]
  decimals        : 6
  sort key        : nodeId (code-unit ascending)
  comparison      : exact string equality of toFixed(decimals) (no epsilon anywhere)

[input]
  graph           : synthetic-deterministic-v1
  nodes / edges   : 96 / 338  (12 chapters x 8)
  view / gravity  : structure / 85
  stage           : 1800 x 1550
  iteration budget: 600 ticks (settled at tick 268, via safety-valve)

[source]
  module          : workbench/server/static/graph-physics-core.js
  sha256          : c4e9e8e5d0ba2a3889691db8fe7259539cc829c0252f948903d16afc55e59997
[baseline]
  path            : tools/graph-baseline/baseline.json
  module sha256   : c4e9e8e5d0ba2a3889691db8fe7259539cc829c0252f948903d16afc55e59997
  budget / settle : 600 / 268

[node id set]
  baseline ids    : 96
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

> `guard problem-set`（工作区产物验收）**未跑**：它是产物验收，依赖 `output/`
> 下的既有产物，不在干净 checkout 的前置条件里（`AGENTS.md` §6）。
> 与上一波（`MOTION-VERIFICATION.md` §9）**同样处理**。

### 图谱零差异的**区段级**证据

```bash
git show HEAD~2:workbench/server/static/workbench.css | sed -n '/Knowledge graph V2/,$p' | sha256sum
sed -n '/Knowledge graph V2/,$p' workbench/server/static/workbench.css | sha256sum
```

```
18601dd6d3268fef23cde06aefde17a52c91ed2233e88f727c7b316799429292 *-   （改前）
18601dd6d3268fef23cde06aefde17a52c91ed2233e88f727c7b316799429292 *-   （改后）
```

⇒ **图谱区段逐字节不变**（12 个裸名一个都没碰）。
CSS 的改动只在 **3361–3401 行**（日历格 + 它的关键帧）与
**4339–4379 行**（台灯的 ① / ④）两处，**都在图谱区段之前**
（图谱区段从 `/* Knowledge graph V2` 起，现位于第 4539 行）。

---

## 7. 待裁决项（**不自行拍板**）

| # | 事项 | 我的处理 | 待裁 |
|---|---|---|---|
| **Q-1** | **日历扩散的轴**：`motion-spec` §2.1 第 19 项写的是 `scaleX 0→1`（`transform-origin: left`），但它的另一个使用方「负荷柱」实现成了 `scaleY`（`transform-origin: bottom`，见 `.bar-fill` 与 CD-174/A-94）。日历格是**高度编码**的竖条，垂直生长（`scaleY`）更贴「按强度扩散」，而 `scaleX` 是规格的**字面**且走查探针 `motion_verify.py` 的判据（`cells_move` 量的是 **X** 缩放）。 | **按规格字面落 `scaleX` + `transform-origin: left`**（且这样**双编码在动画期间照常可读**）。 | ⚠️ 若所有者要「日历从底边长起来」（`scaleY`），则：CSS 改 `transform-origin: bottom` + 关键帧改 `scaleY`，**同时** `motion_verify.py` 的 `cells_move` 判据要跟着改（它只量 X 缩放）—— **探针不在本波可写清单内**，需另派一波。 |
| **Q-2** | **「逐柱错峰」的柱 = 列**：日历网格是 `grid-auto-flow: column`（12 列 = 12 周 × 7 行），所以「柱」落成**列**（同一列 7 格一起动，延迟 0…264ms）。若所有者本意是「逐**格**错峰」（84 个延迟），改 `records.py` 一行即可（`index * 24`），但总时长会到 ~2.3s。 | 按规格「逐柱」+ 任务书「按列」落**按列**。 | 逐列 ✔ 还是逐格？ |
| **Q-3** | **降级档横幅退场后是否保留 `is-on`**：动效档退场后是「`is-on` 还在 + opacity 0」；降级档若摘 `is-on`，两档终态的**类名**就不同（探针 `bannerOn` 会报差异）。 | **保留 `is-on`，只写 opacity 0** —— 终态铁律优先。 | 若所有者认为降级档应当「干净收场」（摘掉 `is-on`），则要同步改探针的 `terminal_fields`（把 `bannerOn` 移出比较项）。 |
| **Q-4** | **M-3「章节首次完成」那一档仍不可判定**：`practice_runs` 没有章列，服务端没有「该章此前未完成」这个事实，A-29 禁止代理指标近似。 | **本波未碰**（不属本波范围）。 | 需要服务端补一个事实，或该档继续挂 PENDING。 |
| **Q-5** | **横幅的「弹入」在产品里其实看不见**（本波**顺带发现**，未修）：`.lk-combo-banner.is-on` 的两条动画里，`lk-combo-out` 带 `520ms` 延迟 + `both` 填充 ⇒ 它的**回填**（`from { opacity: 1 }`）在 0–520ms 段**盖掉**了 `lk-combo-in` 的 0%（`opacity 0`）⇒ 横幅是「直接出现」而不是「弹入」。实测：frames.py 的 M-4 序列 `opacity 1 / 1 / 1 / 1 / 0`（t=0 已经是 1）。 | **未改**（不在本波范围；且改了会影响 M-4 的既有 PASS 判据读数）。 | 是否要补：把退场动画改成 `forwards`（不回填）？—— 那会让 0ms 帧的 opacity 变 0，**分镜条与判据读数都会变**，需另派一波并同步判据。 |

---

## 8. 诚实回报

### 8.1 做到了的

- **M-1 / M-10 / M-12 三条从 FAIL 变 PASS**（每条都附逐帧实测）。
- **D-2 / D-3 两处执行器口径修对**：M-9 由 FAIL 转 PASS；M-4 的判据这次**看得见**横幅。
- **终态铁律**：契约内 13/13 一致（差异 0）；**唯一那条不一致（横幅退场）也归零了**。
- **时序未动**（A-27 的 700ms 四段）、**涟漪层级未动**（A-1 的不压平）、
  **动效红线**（只动 `transform` / `opacity`；状态色瞬切；静态样式 = 终态；
  起始态只在 `@keyframes` 内）、**只用现有 token**（`var(--ease-out)` 等，
  **零硬编码色值**）、**图谱区段逐字节不变**、
  **判据文件一个字未改**（`acceptance.md` / `motion-spec.md` / `decisions.md` /
  `tasks.md` / `component-spec.md` / `docs/**` / `tests/**` 全部零改动）。
- **现有交互逻辑零改动**：请求序列 / 载荷键 / DOM 身份 / 事件绑定 / 判定分支
  一律未动 —— 改的只有「一个装饰类名」「一个 CSS 动画」「一个行内样式属性」
  「一段服务端行内 `animation-delay`」。

### 8.2 打折 / 没做到的（如实说）

1. **M-7（挤压回弹）本波没有再动**：它的 FAIL 在 **A-134**（`086ff607`）里
   已由「`motion-spec` 是动效权威 ⇒ 改 `acceptance.md` 的 M-7 行」结案。
   本波**没有**再碰判据，也**没有**碰实现。改后复跑 `frames.py` 的 M-7 =
   **PASS**（时长 517ms、落点 = 被选中的那一行），
   ⚠️ **但那条判据不量曲线形状**（量的是「动画在不在 + 时长」），
   判据里的三个数（`.6 → 1.1 → 1`）**没有逐帧重测** ——
   `motion_verify.py` 没有 M-7 条目。⇒ 这一格是「**按新判据的复核缺一次逐帧测量**」。
2. **M-3 仍 PENDING**（服务端缺「章首次完成」的事实）—— 与本波无关。
3. **M-13（音效）本波没有重跑**：它走既有探针 `3.3-1…3.3-5`，
   而本波**没有触碰**音效资产与判据；`frames.py --mute-check` 的
   静音孪生（`3.3-5`）本波也**没有重跑**（它与本波四条无关，
   且要另起一趟服务）。⇒ M-13 的 PASS **沿用上游报告的读数**，
   不是本波实测。**这是本报告唯一的「沿用读数」项，已在此点名。**
4. **`motion_verify.py` 一个字节未改**（它不在本波可写清单内）——
   这直接决定了 Q-1 的取舍（它的 `cells_move` 只量 X 缩放）。
5. **日历扩散的「按强度」只体现在编码上**：生长是**按列**错峰的
   （规格的「逐柱」），强度仍由颜色 + 高度**静态**承载；
   生长过程本身不按强度排序。规格 §2.1 第 19 项没有写「按强度排序」，
   判据 `acceptance.md` §2 M-10 的「按强度扩散（颜色 + 高度双编码）」
   的括号也把「按强度」落在**编码**上。**若本意是「按强度排序展开」，
   那是一条规格缺口**（登记在 §7 Q-2 旁边）。
6. **`frames.py` 的 M-5 分档采集（`capture_streak_tiers`）仍是旧顺序**
   （`apply` → `render`）：它是**另一条**采集路径，M-5 的判据只看
   `.lk-streak` 的类名 / 文字 / 颜色，**不涉及横幅** ⇒ 判定不受影响。
   本波**没有**改它（避免动 M-5 的既有产物）。
7. **`WATCH` 里多了一个选择器**（`[data-lk-skeleton] > div`）⇒
   M-9 的**契约外差异**从 2 条涨到 15 条（全是骨架块自身的类名 / 不透明度 /
   1px 高度差）。这些**不参与判定**（契约项差异仍为 0），但**如实登记**在此。
8. **台灯的收回与 700ms 的清理之间有 ≤1 帧的余量**：收回动画的起点
   是「`is-in` 生效的那一帧」（比 JS 的 t=0 晚 ≤ 一帧），
   而清理计时器在 700ms 触发 ⇒ 收回的**最后 ~16ms** 可能被清理切掉。
   实测该时刻灯的不透明度已 ≈ 0.03（`ease-in` 的尾段）⇒ **肉眼不可见**。
   探针的分镜条把清理计时器延后了（`DEFER_CLEANUP_JS`），因此 t=700 帧
   能看到完整的收回终态。

### 8.3 **没有**被本波触碰的东西

- `acceptance.md` / `decisions.md` / `tasks.md` / `component-spec.md` /
  `motion-spec.md` / `openspec/` 下其它任何文件 / `docs/**` / `tests/**`：
  **零改动**（`git diff --stat 086ff607..HEAD` 只列出 `frames.py` ·
  `records.py` · `workbench.css` · `workbench.js` **四个文件** +
  本报告与证据目录；`decisions.md` 的那 63 行是**并行波次**的 `941571c5`
  —— **A-135**，不是本波写的）。
- `tools/walkthrough/motion_verify.py` / `probe.py` / `launch.py` / `run.py` /
  `shots.py` / `seed.py` / `g5.py`：**零改动**（只改了 `frames.py` 的两处口径）。
- 真实池 `pool/dmath.db`：**未写入**（两次独立副本 + `LESSONKIT_WB_HOME`
  隔离注册表，`realPoolUnchanged: true`）。
- 图谱区段与 12 个裸名：**逐字节不变**。

---

## 9. 给所有者的一句话

**四条 FAIL 里那三个产品缺口都补上了**：灯的第四段现在真的演（590–700ms 收回，
层在 DOM 里直到收完）、日历格按列展开（§2.1 第 19 项的原文形态）、
降级档的横幅在 hold 后也退场（§7.2 第 18 行缺的「`setTimeout` 那一半」）。
**终态铁律从「13/13 一致但横幅一项例外」变成 13/13 全一致、连契约外差异也是 0。**
执行器那两处也修对了：**M-9 由 FAIL 转 PASS**（按 A-117 的呼吸口径），
**M-4 的判据这次看得见横幅**（产品顺序 + 可见性）。
**剩下的都在 §7 里登记着，没有一条是本波能自行拍板的** ——
其中 **Q-1（日历的轴：字面 `scaleX` vs 垂直 `scaleY`）** 最值得先看：
它牵涉探针的判据面，改动要连着派。