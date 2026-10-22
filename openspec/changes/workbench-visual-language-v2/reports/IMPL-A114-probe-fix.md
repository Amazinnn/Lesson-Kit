# IMPL-A114 —— 走查执行器的两条探针修复（3.4-2 / 3.4-3）

> **范围**：只改**走查执行器**（`tools/walkthrough/probe.py`）。**产品代码一行未动**
> （`workbench/**`、`tests/**`、`docs/**`、`pool/**` 零改动；`openspec/` 里只新增本报告）。
> **依据**：`decisions.md` 的 **A-114**（这两条 FAIL 是探针缺陷）+ 主会话转达的
> **A-115**（骨架屏形态由「微光扫过」改「明暗呼吸」，判据随之改口径）。
>
> **一句话结论**：
> `3.4-2` 的探针已修好并 **PASS**；`3.4-3` 的探针已修好（能测到中栏换页骨架、能测到体积），
> 但按 **A-115 的新口径**（呼吸）判 **FAIL** —— 因为**产品现在还是「横扫」形态**。
> 这是**真的产品未达标**，不是探针缺陷：等 `IMPL-C1`（骨架呼吸那一波）落地后重跑即应转 PASS。
> 本报告附**判据有分辨力**的证据（注入一个呼吸块 ⇒ 判据判它 PASS；产品的横扫块 ⇒ 判据判它 FAIL）。

---

## 1. 已落盘路径 + commit

| 路径 | 性质 | 说明 |
|---|---|---|
| `tools/walkthrough/probe.py` | **改** | 两条探针的修复（唯一被改的产品外文件） |
| `openspec/changes/workbench-visual-language-v2/reports/IMPL-A114-probe-fix.md` | **增** | 本报告 |

**没有动** `tools/walkthrough/seed.py`、`tools/walkthrough/run.py` —— 二者都不需要动：
`seed.py` 只负责造种子数据，`run.py` 只负责起服务 / 收集 / 出报告，两条判据的采集与判定
全在 `probe.py` 里。

commit（`git commit -- <明确路径>`，**没有** `git add -A`）：

- `65e0eb4d` `fix(walkthrough): A-114 两条探针修复 —— 3.4-2 测候选元素本身 · 3.4-3 采集宽高 + 中栏换页场景（A-115 呼吸口径）`
  → **只含** `tools/walkthrough/probe.py`（`1 file changed, 504 insertions(+), 116 deletions(-)`）
- `docs(walkthrough): A-114/A-115 探针修复报告`
  → **只含** `openspec/changes/workbench-visual-language-v2/reports/IMPL-A114-probe-fix.md`
  （本报告这个 commit 的 hash 随内容变化、无法自指，见 `git log -1` 与最终回报）

```bash
$ git show --stat --oneline 65e0eb4d
65e0eb4d fix(walkthrough): A-114 两条探针修复 —— 3.4-2 测候选元素本身 · 3.4-3 采集宽高 + 中栏换页场景（A-115 呼吸口径）
 tools/walkthrough/probe.py | 620 ++++++++++++++++++++++++++++++++++++---------
 1 file changed, 504 insertions(+), 116 deletions(-)
```

> 注：仓库里同时有另外两个 agent 在改 `workbench/server/static/workbench.css` /
> `workbench/server/static/agent-ui.css` / `workbench/server/pages.py` 等**产品文件**。
> 本次提交**只含**上表两个路径；工作区里 `workbench/**` 的改动**不是**本波的（见 §5）。

---

## 2. 改前 → 改后

### 2.1 `3.4-2`（按下反馈可感知）

#### 改前（`git show HEAD:tools/walkthrough/probe.py`）

hover 侧与 active 侧**都**用 `document.elementFromPoint(x, y)` 取元素 ——
它返回的是**最内层**那个：

```python
        hover_state = page.evaluate("""([x, y, watched]) => {
          const el = document.elementFromPoint(x, y);          # ← 最内层
          if (!el) return null;
          const st = getComputedStyle(el);
          const out = {};
          watched.forEach((name) => { out[name] = st.getPropertyValue(name); });
          return {tag: el.tagName.toLowerCase(),
                  cls: String(el.className || "").slice(0, 60), state: out};
        }""", [candidate["x"], candidate["y"], list(WATCHED_PROPERTIES)])
        ...
        page.mouse.down()
        page.wait_for_timeout(80)
        active_state = page.evaluate("""([x, y, watched]) => {
          const el = document.elementFromPoint(x, y);          # ← 同一个最内层
          ...
        }""", [candidate["x"], candidate["y"], list(WATCHED_PROPERTIES)])
        page.mouse.up()
        if active_state:
            pressed = [name for name in WATCHED_PROPERTIES
                       if active_state.get(name) != hover_state["state"].get(name)]
```

`.nav-item`（div）里的 `<a>`、`.ai-session-entry`（button）里的
`<span class="ai-session-entry-title">` **身上没有 `:active` 规则**
（`:active` 挂在 `.nav-item` / `button` 上）⇒ 两边读的是**同一个内层元素的同一样式**
⇒ `pressed` 恒为空 ⇒ **恒判 FAIL**。

#### 改后（`tools/walkthrough/probe.py`）

候选元素在采集时进一个**页内稳定索引** `window.__lkHoverTargets`，
hover 侧与 active 侧**都按索引读同一个候选元素**；命中测试保留（证明候选真在指针下），
但**样式读在候选身上**：

```python
HOVER_READ_JS = """([index, x, y, watched]) => {
  const el = (window.__lkHoverTargets || [])[index];   # ← 候选元素本身
  if (!el || !el.isConnected) return null;
  const hit = document.elementFromPoint(x, y);          # ← 只用来做命中关系
  if (!hit) return null;
  const st = getComputedStyle(el);                      # ← 读候选
  const state = {};
  watched.forEach((name) => { state[name] = st.getPropertyValue(name); });
  let relation = "other";
  if (hit === el) relation = "self";
  else if (el.contains(hit)) relation = "descendant";
  else if (hit.contains(el)) relation = "ancestor";
  return {relation: relation, ..., state: state};
}"""
```

`relation` 的语义（A-114 的事实一：Chromium 的 `:active` 命中被按下元素**及其祖先**）：

| relation | 含义 | hover 侧 | active 侧 |
|---|---|---|---|
| `self` | 候选就是指针下的元素 | 悬停成立 | 在 `:active` 链上 |
| `descendant` | 指针在候选的**后代**上 | 悬停成立 | 在 `:active` 链上（祖先也命中） |
| `ancestor` | 指针在候选的**祖先**上 | 悬停成立 | **不在** `:active` 链上（`:active` 不下传到后代） |
| `other` | 指针在别处 | **不悬停**（跳过） | — |

判定式**一个字没改**：

```python
            pressed = [name for name in WATCHED_PROPERTIES
                       if active_state["state"].get(name) != hover_state["state"].get(name)]
```

#### 附带修掉的一个探针自伤（**判据未动**）

把 3.4-2 改成「读候选本身」之后，暴露出老探针的第二个自伤：
**按下就是一次点击**，产品的点击处理器会**换页**（左栏链接换中栏）。
老探针的「静止态」是**开跑前一次性**采的 ⇒ 按下换页之后，
**静止态**与**悬停态**来自**两个不同的页面状态**，差出来的是
「刚刚变成 active 的那个导航项」（导航副作用），**不是 hover 反馈**。
实测证据（老探针在同一页面上）：

```
OLD 3.4-1: FAIL 1 个 hover 反馈不在 120–180ms
   cls="outline button-link"  changed=["color","border-color"]  durationMs=0.0
```

⇒ 修法：**把探针拆成两趟**
（每趟内部的交互序列与老探针**逐字相同**：`move → 260ms → 读`，
第二趟再加 `down → 80ms → 读 → up`）：

- **第 1 趟**只测 hover 反馈（3.4-1 的证据），**全程不按鼠标** ⇒ 静止态与悬停态同属一个页面状态；
- **第 2 趟**测按下反馈（3.4-2 的证据），按下态与悬停态**紧接着**读 ⇒ 同一页面状态。

> 这是探针的**测量卫生**修复，不是判据放宽：阈值、判定式、被测元素集合的取法
> （仍是「有 hover 反馈才按下」）全部原样。

### 2.2 `3.4-3`（加载态有骨架 + 加载期动效）

#### 改前

**(a) 采集没量尺寸** —— `SKELETON_JS.record()` 只记
`cls / animationName / animationDuration / afterContent / afterAnimation /
afterDuration / afterBackground / afterTransform`，**没有 width / height**；
而判定读的是：

```python
    sized = [item for item in elements
             if (item.get("width") or 0) > 0 and (item.get("height") or 0) > 0]
    if not sized:
        return _bad(data, "骨架屏没有尺寸（0×0）—— 灰块与微光都无从显示")
```

⇒ `sized` **恒为空** ⇒ 无论产品怎么改都判「0×0」。

**(b) 场景错位** —— 老探针拖慢 `**/api/w/*/practice-sets` 后**重载首屏**，
但中栏骨架只由 `middle-navigation.js` 的 `showLoadingState()` 在**换页时**渲染
（`middlePage.innerHTML = skeletonMarkup()`），**首屏加载不经过它**。

**(c) 降级档** —— reduced-motion / 动效偏好关时走的是**等价静态灰块**
（**没有** `.lk-skeleton` 类，只有外层 `data-lk-skeleton="1"`），
老探针找不到 `.lk-skeleton` ⇒ 判不了。

#### 改后

**(a) 量尺寸** —— `SKELETON_JS` 每条记录带 `getBoundingClientRect()` 的
`width` / `height`（并新增 `role` / `container` / `samples` / `ownAnimations` /
`pseudoAnimations`，见下）。

**(b) 场景改成中栏换页** —— 新增 `_skeleton_switch()`：
拖慢**目标页**（`/w/{ws}/kps`）的请求 ⇒ 点左栏那个链接（**产品自己的**点击处理器
→ `navigate()` → `showLoadingState()` → fetch）⇒ 请求在飞的那 1.5 秒里，
观察器把中栏的骨架块记下来。

```python
        page.route("**/w/*/" + target, slow)          # 目标页的请求被拖慢
        page.goto(base_url + PAGES["practice"], ...)
        clicked = page.evaluate("""(href) => {
          const links = Array.from(document.querySelectorAll("#left-column a[href]"));
          const link = links.find((a) => a.getAttribute("href") === href);
          if (!link) return false;
          link.click();                                 # 产品自己的点击处理器
          return true;
        }""", href)
```

**(c) 降级档** —— 观察器同时盯 `[data-lk-skeleton] > *`（降级档的静态灰块），
每条记录带 `role`（`"sweep"` = 带微光/呼吸标记的块，`"block"` = 静态灰块）
与 `container`（`"middle"` = 中栏换页骨架，`""` = 别的加载标记，例如试卷列表自己的
`.lk-skeleton--text`）。判定按**动效档**分层：

| 档 | 判据 |
|---|---|
| 动效档（`window.lkMotion.mode() === "full"`） | 有体积 **且** 加载期动效（呼吸） |
| 降级档（`weak` / `off`） | **等价静态灰块有体积**（降级档不要求动效） |

#### A-115：判据口径从「微光扫过」改成「呼吸」

**本探针的 3.4-3 判据用的是「呼吸」口径**（供主会话核对两边一致）：

> **有体积**（`width > 0 且 height > 0`）**且** 加载期动效 =
> 块的**自身表面**（`background-color` / `opacity`）随时间变化。

两条互相独立的证据，任一成立即可：

1. **实测采样**：观察器在块插入时取一次 `background-color` / `opacity`，
   再在 **+400ms**、**+800ms** 各取一次；三次里底色或 opacity **真的变了**；
2. **元素自身的动画**：`el.getAnimations()` 里 `effect.pseudoElement === null`
   （动画挂在**元素自己**身上，不是伪元素）的那些动画，其 keyframes
   **变化过** `opacity` / `background-color` / `background`。

**`::after` 覆盖层上的横扫不算**：它动的是覆盖层，块的自身表面没动。
（Chromium 的 `Element.getAnimations()` **不**把伪元素的动画还回来，
所以横扫是用计算样式里的 `::after` 动画名识别的 —— 只作证据，永不判过。）

⚠️ **不要求底色必须变**：`opacity` 与 `background-color` **两种实现都合规**。
（权威表 §3.3「状态色瞬切」⇒ 实现方**优先用 `opacity`**；
若实现方选 `background-color`，本判据同样判过。）

判据**没有**被弱化成「只要有动画名就算」——
没有 keyframes 变化、也没有实测表面变化的块，一律判不过。

---

## 3. 重跑结果

命令（**在仓库根执行**）：

```bash
env -u http_proxy -u https_proxy -u all_proxy python tools/walkthrough/run.py \
  --skip-before --only 3.4-1 3.4-2 3.4-3 3.7-1 --port-after 35544 --out tmp/wt-a114-final
```

| 判据 | 改前（老探针，同一产品树） | 改后（新探针） | 说明 |
|---|---|---|---|
| `3.4-1` hover 反馈 120–180ms | PASS（38 个样本 / 越界 0） | **PASS（47 个样本 / 越界 0）** | 采样更多、越界仍为 0 |
| `3.4-2` 按下比悬停再多一层 | PASS（5 个元素）* | **PASS（10 个元素）** | 读的是候选元素本身；证据更多、指向正确 |
| `3.4-3` 加载态有骨架 + 加载期动效 | **FAIL**「骨架屏没有尺寸（0×0）」 | **FAIL**「有体积 ✔，但加载期动效是 `::after` 覆盖层横扫 ✖」 | 探针已修好；**换判据口径后仍 FAIL = 真的产品未达标**（见 §4） |
| `3.7-1` 动效只动 transform/opacity | PASS | **PASS** | 未触碰 |

\* 注：老探针的 `3.4-2` 在**当前**产品树上判 PASS（靠 `#ai-new-session` 等
「内层元素恰好也带 `:active`」的元素蒙对）；第 22 组走查时它是 FAIL。
无论哪种，**新探针的证据是「候选元素本身」**，不再依赖运气。

**A-39 核对**（服务返回的字节 == 磁盘字节）：

```
css: {"served": 196861, "onDisk": 196861}      # 相等 ✔
```

### 3.4-3 的 FAIL 是**真的产品未达标**，不是探针缺陷

证据链（三条都实测过）：

1. **判据能测到中栏换页的骨架**：`scenario: "middle-column switch"`、
   `switch: {"clicked": true, "tier": "full", "target": "/w/walk/kps"}`，
   采到 **5 块**中栏骨架，尺寸 `304×26 / 660×128 / 607×16 / 502×16 / 568×16`
   ⇒ **有体积 ✔**（老探针恒判 0×0）。
2. **降级档也测到了**：`degradedTier.tier = "weak"`，5 块静态灰块
   `304×26 / 660×128 / 607×15 / 502×15 / 568×15` ⇒ 降级档判「有体积」**通过**。
3. **产品的动效是横扫不是呼吸**：5 块的 `afterAnimation = "lk-skeleton-sweep"`、
   `ownAnimations = []`、三次采样 `background` / `opacity` **完全不变**
   ⇒ `_breathes() = False` ⇒ **判不过**，与 A-115 的裁定一致。

### 判据**有分辨力**（不是恒 FAIL）

一次性脚本（`tmp/`，未落盘进仓库）在**同一个页面**里注入一个**呼吸**块
（元素自身的 `opacity` 动画，keyframes 变化），再用**同一套**判据去判：

```
=== ① the product's mark (the ::after sweep) ===
  cls='lk-skeleton' 304x26 | afterAnimation='lk-skeleton-sweep' | ownAnimations=[]
     surfaceChanged=False samples=[{...opacity: "1"}, {...opacity: "1"}, {...opacity: "1"}]
     -> _breathes(): False
  sized=5 breathing=0 sweepOnly=5          # ← 5 块全被拒

=== ② the injected breathing mark ===
  cls='lk-skeleton' 300x26 | ownAnimations=[{"name": "lk-breathe-test", "playState": "running",
      "pseudoElement": null, "properties": ["opacity"], "varied": ["opacity"]}]
     -> _breathes(): True
  injected accepted: True                  # ← 呼吸块被判过
```

⇒ 判据能**分辨**「有可见的加载期变化」与「静止灰块 / 横扫」：
产品的横扫块被拒，注入的呼吸块被收。**不是恒 FAIL。**

---

## 4. 判据没被放宽的证据（逐项对照）

| 项 | 改前 | 改后 | 结论 |
|---|---|---|---|
| `HOVER_MIN_MS` / `HOVER_MAX_MS` | `120` / `180` | `120` / `180` | **未动**（`probe.py:1718` 附近） |
| 3.4-1 判定式 | `duration < HOVER_MIN_MS or duration > HOVER_MAX_MS` ⇒ offender | **逐字相同** | **未动** |
| 3.4-1 时长来源 | `max(_parse_duration(candidate["transitionDuration"]))` | **逐字相同** | **未动** |
| 3.4-2 判定式 | `pressed = [name for name in WATCHED_PROPERTIES if active != hover]` | **逐字相同** | **未动**（仍是「按下比悬停**再多一层**」） |
| 3.4-2 的「再多一层」口径 | 悬停已改过的属性不算（pressed 必须 ≠ hover） | **逐字相同** | **未动**，**没有**弱化成「有任何差别就算」 |
| 3.4-2 被测元素 | hover 侧与 active 侧**同一个** `elementFromPoint` 结果 | hover 侧与 active 侧**同一个**候选元素（稳定索引） | 口径**更严**（同一个元素，不是两个不同元素） |
| 3.4-3 「有体积」 | `width > 0 且 height > 0` | **逐字相同**（且这次**真的量到了** width/height） | **未动** |
| 3.4-3 「加载期动效」 | 「有微光动画」（`afterAnimation != none`） | 「**呼吸**」：自身表面随时间变化（实测采样**或**元素自身 keyframes 变 opacity/background-color） | 口径按 A-115 改；**且更严**（横扫不算、静止灰块不算、「有动画名就算」不算） |
| 3.4-3 降级档 | 无（找不到 `.lk-skeleton` ⇒ 判不了） | 判「等价静态灰块**有体积**」 | 补齐，**不要求**降级档有动效 |
| 3.4-3 场景 | 首屏加载（产品不走这条路径） | 中栏换页（产品真实路径） | 场景**对准**产品 |
| `WATCHED_PROPERTIES` | 6 个属性 | **逐字相同** | **未动** |
| `judge_hover()` | 见上 | **逐字未动**（`git diff` 中无该函数） | 判据函数**未动** |

---

## 5. 产品代码零改动的证据

本波的提交只含两个路径（§1）。工作区里 `workbench/**` 的改动来自**并发的另外两个 agent**
（CSS 收口三之二 / A-115 前的组件波），**不是**本波。

```bash
$ git show --stat --oneline 65e0eb4d          # 本波的第一个 commit
 tools/walkthrough/probe.py | 620 ++++++++++++++++++++++++++++++++++++---------
 1 file changed, 504 insertions(+), 116 deletions(-)
                                                   ← 只有探针，没有产品文件
```

```bash
$ git diff --name-only 65e0eb4d~1 65e0eb4d
tools/walkthrough/probe.py                       ← 没有 workbench/**、tests/**、
                                                 docs/**、pool/**、openspec/**
```

本波**没有**改过：`workbench/**`（产品代码）· `tests/**` · `docs/**` ·
`pool/**`（真实池）· `openspec/**` 里除本报告外的任何文件
（`decisions.md` / `IMPLEMENTATION-LOG.md` / `contract-drift.md` / `tasks.md` /
`component-spec.md` / `acceptance.md` / 任何 spec —— 那些都是主会话的台账）。

---

## 6. 六条验证命令的原样结果

> 下面是**最终树**（并发 agent 的改动已落盘）上跑出来的结果。
> 过程中曾出现过 2 条 pytest 失败与 5 条 node 失败 —— 那是**并发 agent 正在改产品文案**
> 造成的中间态，与本波无关，证据见 §6.1。

```bash
$ python -m pytest tests -q
........................................................................ [ 79%]
........................................................................ [ 85%]
........................................................................ [ 91%]
........................................................................ [ 97%]
.............................                                            [100%]
1181 passed in 247.26s (0:04:07)

$ python -m compileall -q lessonkit.py workbench pipeline pool tests
（无输出）exit=0

$ openspec validate --specs --strict
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
✓ spec/review-workbench
✓ spec/workbench-content-governance
✓ spec/workbench-ui
Totals: 19 passed, 0 failed (19 items)

$ python lessonkit.py guard extract-problems --course dmath --chapter ch06
Gate: extract-problems
Course: dmath
Chapter: ch06
Result: PASS

All required artifacts exist and check files contain no blocking markers.

$ node --test tests/workbench/*.test.js
ℹ tests 264
ℹ pass 264
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0

$ python -m compileall -q tools/walkthrough      # 本波自己的文件
（无输出）exit=0
```

### 6.1 过程中的中间态失败（与本波无关的证据）

在并发 agent 改产品文案的中间态上，同一套命令曾给出：

```
FAILED tests/workbench/test_conversation_api.py::ConversationApiTests::test_a_running_turn_refuses_a_model_switch
FAILED tests/workbench/test_ui_interactions.py::test_workbench_browser_interactions
ℹ fail 5   （node：五条断言产品文案「入库完成 / 为什么」的用例）
```

证据它们**不是**本波造成的：

1. `tests/**` 里**零处**引用 `tools/walkthrough`
   （`grep -rn "walkthrough" tests/` 无命中），而本波只改了 `tools/walkthrough/probe.py`；
2. 把 `tools/walkthrough/probe.py` **还原成 HEAD 版本**后重跑，
   `test_workbench_browser_interactions` **依然失败**
   （断言撞的是并发 agent 正在改的 `workbench/server/static/workbench.js` 的「入库完成 / Check 入库完成」文案）；
3. `test_a_running_turn_refuses_a_model_switch` **单独跑通过**，是顺序/状态相关的偶发；
4. 并发 agent 落盘后重跑，**1181 passed / node 264 pass 0 fail**（见上）。

---

## 7. 待裁决项（拿不准的登记，不自行拍板）

1. **【A-115 口径登记】本探针的 3.4-3 判据 = 「有体积 + 加载期动效（呼吸）」**，
   实现口径：**元素的 `background-color` 或 `opacity` 随时间变化**
   （实测三次采样变，**或**元素自身有 keyframes 变化了这两个属性的动画）；
   `::after` 覆盖层横扫**不算**；降级档只判「等价静态灰块有体积」。
   ⇒ **不要求底色必须变**：`opacity` 与 `background-color` 两种实现都判过；
   权威表 §3.3「状态色瞬切」⇒ 实现方**优先用 `opacity`**。
2. **【先后顺序】3.4-3 现在判 FAIL 是预期的**：产品先改（`IMPL-C1` 的骨架呼吸），
   判据才可能转 PASS。本波**没有**为让判据变绿去改产品。
3. **【A-114 的事实核对】**A-114 说「走查的 `CONSISTENCY["reduced_motion"]` 一开」，
   但当前 `tools/walkthrough/shots.py` 里 `CONSISTENCY["reduced_motion"] == "no-preference"`
   ⇒ 走查的**主档其实是动效档**（`window.lkMotion.mode() == "full"`），
   「微光扫过」在走查里**是**能测到的（本次实测 `afterAnimation = "lk-skeleton-sweep"`）。
   我把判定写成了**按档分层**（动效档要动效、降级档只要体积），
   并**额外跑一遍降级档**作为补充证据 ⇒ 两种口径下都对。
   请主会话确认这是不是 A-114 原文的笔误（不影响本波结论）。
4. **【探针自伤，已修，请复核】**「按下 = 一次点击 = 产品换页」会让老探针的
   静止态基准过期，把导航副作用当成 hover 反馈（实测老探针因此把
   `.outline.button-link` 判成 0ms 的越界项）。修法是**把 hover 测量与按下测量拆成两趟**，
   每趟内部的交互序列与老探针逐字相同。**这属于探针结构改动，超出 A-114 字面授权，
   请复核是否接受。**
5. **【老探针遗留，未改，仅登记】**
   ① 候选元素上限 `if (out.length >= 20) return;` 写在 `forEach` 回调里，
   **从来没有真正截断**（本次实测采到 51 个 hover 样本）——本波**未改**（避免扩大 scope）；
   ② 3.4-1 的「时长」取的是元素的 `transition-duration`（不论被改的属性是否在
   `transition-property` 里），例如「hover 改的是 `background-color`（瞬切）而元素
   另有 `transform` 的 120ms 过渡」会被算成 120ms ——本波**未改**（判据口径问题，非探针缺陷）；
   ③ `probe_hover` 第 2 趟按下导航项会让页面换页，之后中栏里的候选元素已脱页 ⇒ 被跳过，
   所以 3.4-2 的证据集中在左栏 / 右栏 ——本波**未改**（老探针也有同样的性质）。
6. **【降级档的静态灰块】**降级档的灰块由 `middle-navigation.js` 内联
   `height:Npx;width:W%` 给尺寸、颜色取 `--skeleton-base`；
   本探针在降级档只判「有体积」，**不判颜色是否与动效档同源** —— 若要连这一条一起判，
   需要主会话给判据（当前 A-115 只说「等价静态灰块有体积」）。

---

## 8. 复现命令

```bash
# ① 走查重跑（4 条判据）
env -u http_proxy -u https_proxy -u all_proxy python tools/walkthrough/run.py \
  --skip-before --only 3.4-1 3.4-2 3.4-3 3.7-1 --port-after 35544 --out tmp/wt-a114-final

# ② 看 3.4-3 的证据
python -c "import json,pathlib;d=json.loads(pathlib.Path(
  'tmp/wt-a114-final/evidence/after/probe/3.4-3.json').read_text(encoding='utf-8'));
  print(json.dumps(d['data'], ensure_ascii=False, indent=2))"

# ③ A-39 核对
python -c "import json,pathlib;d=json.loads(pathlib.Path(
  'tmp/wt-a114-final/run.json').read_text(encoding='utf-8'));
  print(d['sides']['after']['css'])"
```
