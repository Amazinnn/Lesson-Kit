# IMPL-C1c —— A-132 的三件收尾：`g5.py` 的 R-1 假绿修复 + `.sm` 两处

> 任务书：`decisions.md` **A-132**（缺陷 1 / 2 / 3）的执行版。
> 分支：`feat/workbench-visual-language-v2`；基线 commit：`905e280b`。
> 交付日期：2026-10-23。

## 0. 摘要

| # | 任务 | 结果 |
|---|---|---|
| 1 | `tools/walkthrough/g5.py` 的 R-1 **假绿缺陷** | **已修**：判据改成「像素数」；mask 改成「划分」；共享外壳（右栏）整列排除且差异**单独报出**（`shellDiff`）。自证用例（2 个）已写进 `tests/test_g5_diff_pixels.py`（10 项，全绿） |
| 2 | `pages.py:1087` 去掉 `.sm` | **已改**：`class='primary sm'` → `class='primary'`；实测高 **28px → 40px**，命中区 44px，同容器相邻中心距 **75px → 84.21px**（≥44px ✔） |
| 3 | `button.sm` 的圆角 | **已改**：`14px` → `var(--r-md)`；实测 computed `border-radius` **14px → 12px**，与 `.primary` 一致 ✔ |

**门禁的诚实性**：修好之后，图谱页的 R-1 = **0（图谱专属区）**，
**共享外壳的差异被如实报出**（`bc488a40` → 当前 = **10,849 px**；C1c 自身增量 =
**280 px**）—— **这两个数分开报**（见 §2.5）。**没有**为了让 R-1 变绿而调阈值、
改基线或把右栏的差异也藏起来。

---

## 1. 三个 commit

| commit | 内容 | 文件 |
|---|---|---|
| `3c0113e3` | `fix(walkthrough)`: g5.py 的 R-1 算术 —— 逐像素计数 + 共享外壳整列排除 + shellDiff 单独报出（A-132） | `tools/walkthrough/g5.py`、`tests/test_g5_diff_pixels.py`（新增） |
| `55e517eb` | `fix(workbench)`: 去掉 `#ai-paper-approval-approve` 的 `.sm` —— 该容器给不出 44px 中心距（A-132 缺陷 2） | `workbench/server/pages.py` |
| `4294fc78` | `fix(workbench)`: `button.sm` 的圆角 14px ⇒ `var(--r-md)` —— 尺寸变体不改形状语言（A-132 缺陷 3） | `workbench/server/static/workbench.css` |

> 三个 commit 都是**单文件/单主题**的小步提交（AGENTS.md 纪律 5）；
> `git add -- <路径>` + `git commit -- <路径>`（两个都带路径）。

---

## 2. 任务一：`g5.py` 的 R-1 假绿缺陷（**最重要**）

### 2.1 改前 → 改后

**改前**（`g5.py:302-337`）：

```python
total = 0
for band in bands:
    total += sum(band.histogram()[1:])     # ← 三通道求和
if mask is not None:
    masked = 0
    for y in range(height):
        for x in range(width):
            if mask_pixels[x, y]: masked += 1   # ← mask 区的【全部】像素数
    total = max(0, total - masked)               # ← 减掉【全部】masked
```

**改后**（`tools/walkthrough/g5.py`）：

```python
per_band = [sum(band.histogram()[1:]) for band in bands]
# the differing pixels: a pixel differs as soon as one channel differs
differing = bands[0]
for band in bands[1:]:
    differing = ImageChops.lighter(differing, band)
differing = differing.point(lambda value: 255 if value else 0)
pixel_diff = sum(differing.histogram()[1:])
detail = {"perBand": per_band, "channelSum": sum(per_band),
          "pixelDiff": pixel_diff, "size": list(left.size)}
if mask is None:
    return pixel_diff, detail
outside = ImageChops.multiply(differing, mask.point(lambda value: 255 - value))
inside = ImageChops.multiply(differing, mask)
detail["outsideMaskDiff"] = sum(outside.histogram()[1:])
detail["maskedDiff"] = sum(inside.histogram()[1:])
return detail["outsideMaskDiff"], detail
```

逐条对账 A-132 的三条裁决：

| A-132 裁决 | 落地 |
|---|---|
| 1「算术必须改成『排除 mask 区外的差异』」 | mask **划分**差异像素：mask 外计入判据，mask 内另计 `maskedDiff`；**不再有任何减法** |
| 「差异像素按像素算，不按通道求和」 | `ImageChops.lighter` 取三通道**最大值** ⇒ 任一通道不同即该像素不同，**计 1 次**；`perBand`（分通道）保留在 detail 里只作溯源，**判据不再用它** |
| 2「口径对齐 A-126 裁决 1」 | R-1 = **图谱专属区** ⇒ 共享外壳**整列排除**：左栏 `x < 280` · 顶栏 `y < 52` · **右栏（新增）** |
| 「右栏边界从数据里取」 | `_shell_rect()` 读采集到的 `#ai-column` 实际 rect（`assertions.right`），**两侧取并集**；取不到 ⇒ **如实记进报告**（note 里明写「NOT in the artefacts」），**不猜边界** |
| 「排除区的差异像素数必须单独报出（`shellDiff`）」 | `ae.json` 的 R-1 一节新增 `shellDiff`（= `maskedDiff`），命令行摘要也打印 |
| 3「不许调阈值、不许改基线」 | **没有阈值可调**（门禁就是 `== 0`），**基线文件一个字没动** |
| 4「R-2 / R-3 不受影响」 | 两者**不用 mask** ⇒ 路径不变，仍是硬门禁；`ae` 口径统一成「像素数」（两者实测都是 0 ⇒ 数字不变；`channelSum` 仍在 detail 里可对照旧口径） |

### 2.2 右栏边界的**实测来源**（不是写死的 420）

采集协议（g5.py §6.5 九步）产出的 `assertions`：

```
before.right = [1020, 52, 420, 848]     ← #ai-column 的实际 rect
after.right  = [1020, 52, 420, 848]
⇒ excluded as [1020.0, 52.0, 420.0, 848.0]
```

> ⚠️ **一个实测纠偏**：任务书里写的备选 `.side-sections` **不是右栏** ——
> 它是**左栏**的纸面 wrapper（实测 rect = `[0, 52, 279, 697]`）。
> ⇒ `R1_SHELL_KEYS = ("right",)`（**只认 `#ai-column`**），并在代码注释里写明这条事实。
> （`420` 恰好与 `#layout` 的三栏几何 `280px minmax(0,1fr) 420px` 一致 ——
> `design-notes/graph-isolation.md:529` 记着这一条 —— 但本实现**不依赖**这个常数。）

### 2.3 自证用例 A：mask 区里有差异（**复现旧 bug**）

构造：两张 1440×900 的图，**只在 mask 区（左栏）里**有 100×100 = 10,000 px 变白，
**mask 区外完全相同**。

```
mask pixels = 312320  ⇒ old false-green threshold = 104106

A: 100x100 px difference INSIDE the mask (shared shell)
  old algorithm  : total = max(0, 30000 - 312320) = 0   ⇒ R-1 PASS (FALSE GREEN)
  new algorithm  : R-1 (graph's own area) = 0   shellDiff (maskedDiff) = 10000
                   pixelDiff = 10000   channelSum = 30000
```

⇒ **旧算法报 PASS（假绿）**；新算法：该 scope 本来就该是 **0**，
但 **maskedDiff = 10,000** 在报告里**看得见**。

### 2.4 自证用例 B：mask 区**外**有差异（**反向用例**）

构造：**mask 外**有 100×50 = **5,000 px** 差异。

```
B: 100x50 px (5,000 px) difference OUTSIDE the mask (graph's own area)
  old algorithm  : total = max(0, 15000 - 312320) = 0   ⇒ R-1 PASS (FALSE GREEN)
  new algorithm  : R-1 (graph's own area) = 5000   shellDiff (maskedDiff) = 0
                   pixelDiff = 5000   channelSum = 15000
```

⇒ 旧算法**同样**把它吞成 0；新算法**必须报非 0** ⇒ **5,000**（不再被减掉）。

### 2.5 自证用例**在仓库里**（不是一次性脚本）

`tests/test_g5_diff_pixels.py`（新增，**10 项，全绿**）把两个用例固定下来：

- `test_difference_inside_the_mask_is_reported_not_swallowed` ——
  断言**旧算法在此仍是 0**（reference 实现留在测试里），新算法 `ae == 0`
  且 `maskedDiff == 10,000`；
- `test_difference_outside_the_mask_is_counted` —— 旧算法 0，新算法 `ae == 5,000`；
- `test_the_count_is_a_pixel_count_not_a_channel_sum` —— 1 个差异像素 = **1**，
  `channelSum == 3`（分通道分解只作溯源）；
- `test_the_right_column_is_excluded_from_the_captured_geometry` ——
  右栏内的差异 ⇒ `ae == 0` 且 `maskedDiff == 10,000`；
- `test_shell_rect_is_read_from_the_artefacts` —— 两侧取并集；**没有几何时
  返回 `None` 而不是猜**；**`.side-sections`（左栏）不得被当成右栏**；
- `test_a_missing_geometry_is_recorded_in_the_scope`、
  `test_the_mask_marks_the_excluded_area`（4 个参数）。

```
$ python -m pytest tests/test_g5_diff_pixels.py -q
..........                                                               [100%]
10 passed in 0.30s
```

### 2.6 真实图谱页的四个数

**协议**：照抄 `g5.py` 的 §6.5 九步（reduced-motion + 字体就绪 + 滚动归零 +
求解器静默 + 视口截图；1440×900 / dpr 1 / `zh-CN` / `Asia/Shanghai` /
`--force-color-profile=srgb --disable-lcd-text`），工作区 `lesson-kit`，
两侧**只差静态 CSS**（用路由拦截供给旧版 CSS，另一侧用磁盘当前版）。
产物是 g5 自己的格式 ⇒ 直接喂 `python tools/walkthrough/g5.py compare`。

**比对 ①（A-132 的场景）：`bc488a40`（**C1 的 CSS 实现之前**） → 当前工作树**

> 口径校准：`bc488a40` 与 `4e0c61b2`（C1 的实现 commit）的父 `c706c74b`
> 的 `workbench.css` **逐字节相同**（sha256 `6046575b1b2045453f6d3b0374c034e98d557f918cbabb7f8aa1d154564f17b9`
> = C1b 报告 §4.1 记的「full css sha256 before」）⇒ 「before 侧」**就是 C1 之前的 CSS**。

```
$ python tools/walkthrough/g5.py compare --before tmp/c1c-graph --after tmp/c1c-graph --out tmp/c1c-graph/out
{
  "verdict": "PASS",
  "detail": "R-1 / R-2 / R-3 are all 0 — the graph was not damaged",
  "R-1": 0,
  "R-2": 0,
  "R-3": 0,
  "shellDiff": 10849,
  "samplesEqual": true
}
```

| 口径 | 数字 |
|---|---|
| **R-1（图谱专属区）** | **0** ✔ |
| **R-2**（`.graph-workspace` 裁剪 `[320,272,660,608]`） | **0**（`perBand: [0,0,0]`）✔ |
| **R-3**（画布 `[320,284,660,596]`） | **0** ✔ |
| **shellDiff**（共享外壳的差异，**单独报出**） | **10,849 px** |
| R-1 detail | `perBand [10828, 10828, 10834]` · `channelSum 32490` · `pixelDiff 10849` · `outsideMaskDiff 0` · `maskedDiff 10849` |
| 采样点（左栏纸面 / 右栏纸面 / 画布左上） | `243,241,234`=`243,241,234` · `255,254,250`=`255,254,250` · `252,250,246`=`252,250,246` ✔ |
| 整页差异 bbox | **(1037, 80, 1424, 300)** ⇒ **整体落在右栏内**（右栏 x ≥ 1020） |

**同一对图上，旧算法会算出什么**（证明「假绿」在真实数据上确实发生）：

```
OLD arithmetic: max(0, 32490 - 668480) = 0   ⇒ R-1 would report PASS (false green)
```

⇒ **旧口径的 0 是「减没了」的 0**，新口径的 0 是「**图谱专属区逐像素没变**」的 0，
**而且**外壳那 10,849 px 被如实报了出来。

**比对 ②（C1c 自身的增量）：`905e280b`（HEAD，即 C1b 之后） → 当前工作树**

```
  "R-1": 0,  "R-2": 0,  "R-3": 0,  "shellDiff": 280
  R-1 detail: perBand [272, 272, 278] · channelSum 822 · pixelDiff 280
               outsideMaskDiff 0 · maskedDiff 280
  整页差异 bbox: (1380, 83, 1424, 111)
```

⇒ C1c 自己的改动（`.sm` 圆角 14px → `var(--r-md)`）**只落在右栏**，
**图谱专属区 = 0**。bbox `(1380,83,1424,111)` 与 C1b 报告记的
「并发版 → 本波 = 274 px（bbox `(1380,83,1424,111)`）」**同一处、同一现象**
（计数 280 vs 274 的差 = 圆角弧长差）。

### 2.7 报告产物里新增了什么

`ae.json` 的 **R-1 一节**：

```json
"R-1": {
  "ae": 0,
  "detail": {"perBand": [...], "channelSum": 32490, "pixelDiff": 10849,
             "size": [1440, 900], "outsideMaskDiff": 0, "maskedDiff": 10849},
  "scope": "the graph's own area (A-126 ruling 1)",
  "excluded": {"leftColumnX": 280, "topBarY": 52,
               "rightColumn": [1020.0, 52.0, 420.0, 848.0],
               "rightColumnSource": "the right column's rectangle comes from the
                 captured geometry: before.right = [1020, 52, 420, 848];
                 after.right = [1020, 52, 420, 848] ⇒ excluded as [...]"},
  "shellDiff": 10849,
  "mask": "the shared shell — the left column (x < 280), the top bar (y < 52)
           and the right column — is excluded (A-48 / A-126 ruling 1 / A-132);
           the differing pixels inside it are reported as shellDiff, they are
           NOT subtracted away"
}
```

命令行摘要也多了 `"shellDiff"`（`g5.py compare` 的 stdout）。

---

## 3. 任务二：`pages.py:1087` 去掉 `.sm`

**改前**：`"<button id='ai-paper-approval-approve' class='primary sm' type='button'>批准更新</button>"`
**改后**：`"<button id='ai-paper-approval-approve' class='primary' type='button'>批准更新</button>"`

**只改 class 名**：id / 文案 / 事件 / 位置**一个字没动**（`git diff` 只有这一行）。

**理由**（A-132 缺陷 2 引 A-126 裁决 2 第 4 条自己写的规则）：该处容器
（`.ai-paper-approval-actions`，`gap: 7px`）给不出 44px 中心距 ⇒ 那就不该用 `.sm`。

**实测**（1440×900，揭示隐藏的审批面板后）：

| 量 | 改前（`class='primary sm'`，旧 CSS `905e280b`） | 改后（`class='primary'`，当前） | 判定 |
|---|---|---|---|
| computed `height` | **28px** | **40px** | ✔ 任务书要求 40px |
| computed `font-size` | 12px | 14px | 默认形态 |
| computed `border-radius` | 14px | **12px** | 与 `.primary` 一致（任务三） |
| `::before`（命中区补偿） | `content: none` | `top: -2px; bottom: -2px` | 命中区 = 40 + 2 + 2 = **44px** ✔ |
| 同容器相邻按钮（`#ai-paper-approval-cancel`）中心距 | **75px** | **84.21px** | **≥44px ✔** |
| 文档内最近可点目标 | — | 84.21px（`/practice` `/records` `/kps`）· 61.84px（`/graph`，图谱节点 `<a>`） | **≥44px ✔** |

> ⚠️ **C1b 那个 33.84px 没能复现**（见 §6 待裁决 1）：它是**会话列表视图**里的
> 40×40 圆形图标按钮与会话列表视图**互斥** ⇒ 那个数是**揭示手法下的几何**，
> 不是用户可达的态；本工作区**没有任何 Agent 会话**（`pool/jobs/conv-*` 不存在）
> ⇒ 那个态**在本机无法构造**。

---

## 4. 任务三：`button.sm` 的圆角

**改前**：`button.sm { height: 28px; font-size: 12px; line-height: 18px; padding: 0 10px; border-radius: 14px; }`
**改后**：`button.sm { height: 28px; font-size: 12px; line-height: 18px; padding: 0 10px; border-radius: var(--r-md); }`

**只改这一条属性**（`height 28px` / `font-size 12px` / `line-height 18px` /
`padding 0 10px` 全部不动）。上方那段解释「连带效果」的注释同步改成现在的口径
（否则注释会描述一个已经不存在的取值）。

**理由**（A-132 缺陷 3）：形态族（`button.primary` / `button.outline`）是
`--r-md`（12px）；**尺寸变体不该改形状语言**（28px 高 + 14px 圆角 = 药丸 = 另一套形态）。

**实测**（1440×900）：

| 页面 | `--r-md` | `.sm` 按钮的 computed `border-radius` | `.primary` 的 computed `border-radius` |
|---|---|---|---|
| `/practice` | 12px | **12px**（`#goal-submit` = `primary sm` · `#ai-new-session` = `outline sm`） | **12px**（`#paper-start`）✔ 一致 |
| `/records` | 12px | **12px**（`#ai-new-session`） | 12px ✔ |
| `/kps` | 12px | **12px**（`#knowledge-sort-direction` = `ghost sm` · `#ai-new-session`） | 12px ✔ |
| `/graph` | **6px**（图谱页把 `--r-md` 钉回旧值，`body:has(#layout[data-page="graph"])`） | **6px** | 6px ✔ 一致 |

> `ghost sm icon-only` 仍是 `50%`（`button.icon-only` 的形态规则在 `.sm` 之后，
> 压过它）—— **一字未动**。
> 图谱页的 6px 是**图谱自己的 token 钉回值**（旧稿就是 6px），
> **`.sm` 与 `.primary` 在该页同样一致** ⇒ 不构成图谱页的视觉变化。

---

## 5. 六条验证命令（原样结果）

```
$ python -m pytest tests -q
........................................................................ [ 42%]
...
.......................................                                  [100%]
1191 passed in 240.04s (0:04:00)
```

（改前是 1181 ⇒ **+10** = 本波新增的 `tests/test_g5_diff_pixels.py`。）

```
$ python -m compileall -q lessonkit.py workbench pipeline pool tests
（无输出，exit 0）
```

```
$ openspec validate --specs --strict
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
✔ running immediate mode survives the preference change (0.7304ms)
✔ running batch mode survives the preference change (0.6522ms)
✔ running off mode survives the preference change (0.6175ms)
✔ an empty rating input is rejected inline instead of dying on the server (0.9287ms)
ℹ tests 264
ℹ suites 0
ℹ pass 264
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 856.9603
```

```
$ node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json
...
[summary]
  compared nodes  : 96
  coordinate diffs: 0
  seed diffs      : 0
  id set diffs    : 0
  total differences: 0

RESULT: PASS — converged coordinate diff = 0 (SI-0 green)
```

---

## 6. 图谱零差异证据

```
graph region 字符数 = 23235
graph region UTF-8 字节 = 24422
graph region sha256 = 18601dd6d3268fef23cde06aefde17a52c91ed2233e88f727c7b316799429292
（C1b 报告的 sha256 **完全相同** ⇒ 从 “/* Knowledge graph V2” 到文件尾**逐字节相同**；
 C1b 记的 “23235” 是**字符数**，本处 24422 是 **UTF-8 字节数** —— 单位不同，sha256 相同才是内容相同）

12 个裸名各声明 1 次：
  --paper 1/1   --ink 1/1    --hair 1/1   --blue 1/1   --blueSoft 1/1  --yellow 1/1
  --yellowSoft 1/1  --red 1/1  --redSoft 1/1  --green 1/1  --graphite 1/1  --shadow 1/1

R-2 = 0    R-3 = 0    R-1（图谱专属区）= 0
graph-layout-diff: total differences = 0
```

> `grep -n "Knowledge graph V2" workbench/css` ⇒ 仍在 `workbench.css:4505`，
> 该行**以下的内容一个字节都没动**（本波只改了 `:1068` 的一行 + 上面那段注释）。

---

## 7. 待裁决项（**拿不准的登记，不自行拍板**）

### 7.1 C1b 的 33.84px **没能复现**（任务二的原始争点）

- **事实**：A-132 缺陷 2 引用的是 C1b §6.1 的数：审批按钮与**会话列表视图**里
  一个 40×40 圆形图标按钮（`.ai-session-actions`）中心距 **33.84px**。
- **本波实测到的**：能同时含审批面板的态是**聊天视图**（`#ai-chat-view`），
  那里离它最近的可点目标是**同容器的「取消更新」**，中心距 **84.21px**（≥44px ✔）。
- **为什么复现不了**：那个 40×40 图标按钮属于**会话列表视图**，与聊天视图
  **互斥**；而本工作区**没有 Agent 会话**（`pool/jobs/conv-*` 不存在）
  ⇒ 那个态在本机根本构造不出来。
- **不自行拍板**：C1b 已说明「该态在真实 UI 里不可达」；本波按 A-132 的裁决
  做了（去掉 `.sm` ⇒ 40px 形态 + `::before` ⇒ 命中区 44px）。
  **若所有者认为「揭示手法下的几何」也要达标**，候选是
  ① 审批面板出现时收起会话列表（**属交互改动**，归下一波）；
  ② 给 `.ai-paper-approval-actions` 的 gap 加大（**属 CSS 改动**，
  但会让两个按钮离得更远 —— 本波**没做**，因为 A-132 只裁了「去掉 `.sm`」）。

### 7.2 两处**文档口径**已过时（**本波没改**，不在可写清单里）

| 文件 | 过时的那一句 | 建议的改法 |
|---|---|---|
| `tools/walkthrough/README.md:115` | 「**R-1** \| 整页，**排除**左栏（`x < 280`）与顶栏（`y < 52`） \| 差异像素 = 0」 | 改成「整页**排除共享外壳**（左栏 / 顶栏 / **右栏**，右栏边界取自 `#ai-column` 的实测 rect）；判据 = **图谱专属区的差异像素数**；外壳的差异 = `shellDiff` 单独报出」 |
| `openspec/changes/workbench-visual-language-v2/design-notes/graph-isolation.md` §6.3–§6.8 | 同上口径（A-48 时代的「左栏 + 顶栏」） | 同步 A-126 裁决 1 + A-132 的口径（**本波不许碰 openspec/，故只登记**） |

> AGENTS.md 纪律 3 要求「改变中间工件的字段 ⇒ 同一个 PR 同步职责文件」。
> 这两处的职责文件分别是 `tools/walkthrough/README.md` 与
> `design-notes/graph-isolation.md`；**前者不在本任务书的「可写」清单里，
> 后者被明令不许碰** ⇒ 本波**只登记不擅自改**，交主会话定。

### 7.3 `.sm` 的圆角从「药丸」变「圆角矩形」是**用户可感知**的

- A-132 已裁「**默认按家族一致**」⇒ 本波照办。
- **但**：A-132 自己也写了「若所有者更喜欢小药丸，**回写 `component-spec.md` 后**
  再改回」⇒ 若所有者选药丸，需要**先回写 `component-spec.md`**（本波不许碰
  `openspec/`）**再**把这一行改回 `14px`。**本波不自行选边**（已按 A-132 的默认裁执行）。

### 7.4 R-2 / R-3 的 `ae` 口径统一成了「像素数」

- 旧：R-2 / R-3 的 `ae` 是**三通道求和**；新：与 R-1 一样是**像素数**
  （`detail.channelSum` 仍保留旧口径可对照）。
- **门禁语义不变**（两者都必须 = 0）；**实测两者都是 0** ⇒ 数字没变。
- 登记原因：这是「内部工具的度量单位」统一，属**内部代码接口**的可改范围
  （AGENTS.md 兼容边界），但**写在这里**以备复核。

---

## 8. 诚实回报

- **三件都做完了**，没有打折。
- **任务一**：
  - 旧算法（假绿）**在两个用例上都被复现**，新算法的数字逐个贴出；
  - 用例**写进了仓库测试**（`tests/test_g5_diff_pixels.py`，10 项），不是一次性脚本；
  - 真实图谱页**跑了两次比对**（C1 之前 / C1c 自身增量），四个数（R-1 / R-2 /
    R-3 / **shellDiff**）都在 §2.6；
  - **没有**调阈值、**没有**改基线、**没有**把右栏的差异藏起来 ——
    右栏排除是**口径**（A-126 裁决 1），图谱专属区**必须是 0**，本次实测**就是 0**。
- **一处与任务书不一致的实测纠偏**：任务书说右栏可取 `#ai-column` / `.side-sections`
  的 rect —— 实测 **`.side-sections` 是左栏**（`[0, 52, 279, 697]`），
  右栏是 `#ai-column`（`[1020, 52, 420, 848]`）⇒ 只认后者（已在代码注释里写明）。
- **一个没做到的事**：C1b 的 **33.84px** 那个数**没能复现**（本工作区没有 Agent 会话，
  那个态构造不出来）⇒ 已在 §7.1 如实登记，**没有**假装复现。
- **没跑的**：`guard problem-set`（按 AGENTS.md 纪律 6，它是「工作区产物验收」，
  干净 checkout 不跟踪 `output/`）—— **与 C1b 同一处置**。
- **未碰的文件**：`agent-ui.css` · `static/*.js` · `docs/` ·
  `openspec/`（除本报告）· `workbench.css` 的图谱区段 · 任何现有交互逻辑
  · 任何阈值 / 基线。
