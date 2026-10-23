# 动效验收报告 — M-1…M-13（分镜条 + 降级孪生对照）

> **本波的任务**：把 `acceptance.md` §2 的 **13 条动效**逐条**量**一遍，
> 产出**分镜条**与**降级孪生对照**，给出 PASS / FAIL / PENDING 的判定与证据。
> `tasks.md` 的 **8.6 / 8.10** 两条阶段验收指向的正是这件事。
>
> **本波不改判据、不改阈值、不改产品**：`workbench/**` 一行未动
> （`git diff --stat -- workbench/` 为空，见 §9）。判据的原文逐条抄在下面，
> 实测数据全部来自本轮跑出来的产物（路径逐条给出）。

---

## 0. 结论速览

| # | 动效 | 判定 | 一句话 |
|---|---|---|---|
| M-1 | 台灯主题转场 | **FAIL** | ①②③ 三段在；**④ 收回段没有动画** —— `lk-lamp-retract` 的触发类 `.lk-lamp.is-in` 全仓库无人挂，灯是 700ms 被**直接移除**的 |
| M-2 | 交卷庆祝（日常档） | **PASS** | 数字滚动（采到中间值）+ 进度带 0→100% + **零彩带** + CTA 可点 |
| M-3 | 交卷庆祝（里程碑档） | **PENDING** | 全对那一档已采到并通过（爆点 + 12 张纸片 + CTA 不被遮挡）；**「章节首次完成」那一档不可判定**（服务端没有这个事实） |
| M-4 | 连对升级横幅 | **PASS** | 横幅出现 → 数字替换（5 / 10 两轮）→ 退场；**只有一份** |
| M-5 | 连对计数器三档 | **PASS** | 灰（`rgb(141,133,120)`）→ 黄（`rgb(245,197,24)`）→ **黄蓝渐变**（`linear-gradient(245,197,24 → 43,98,232)`），不靠文字 |
| M-6 | 连对进度火苗簇 | **PASS** | 同帧内五簇透明度不同（`1 / .958 / .554 / 0 / 0`）⇒ 逐簇点亮；错峰 80ms |
| M-7 | 挤压回弹（答对） | **FAIL** | 总时长 **517ms** ✔、落点=**被选中的那一行** ✔；但**回弹曲线是 0.6→1.1→…→1，不是判据写的 0.92→1.06→1** ⇒ 按字面判 FAIL（见 §7.3 的漂移登记） |
| M-8 | 视图转场 | **PASS** | 上浮峰值 **12px**（判据 8–12）+ 淡入；转场挂在 `#middle-page > *`（容器）上 |
| M-9 | 骨架屏 | **PASS** | 灰块**整体明暗呼吸**（自身 opacity 1 → .87 → .57 → .47 → .45）、**无横扫**、**无表面渐变**；降级档是等体积静止灰块 |
| M-10 | 数据层（负荷柱 / 日历） | **FAIL** | 负荷柱从 0 生长 + **逐柱错峰 24ms** ✔；日历格**颜色 + 高度双编码** ✔；但**格子自身没有任何动画** ⇒「按强度扩散」的过程不存在 |
| M-11 | 连对断裂负反馈 | **PASS** | 负反馈 = 计数器摆动（实测峰值 **3.93px ≤ 4px**，祖先层与 body/html 位移 0）+ 火苗**逐簇熄灭**（5→4→3→2→1→0）+ 计数器归零 |
| M-12 | 分级降级（四组合） | **FAIL** | 四种组合的档位/数字/火苗/横幅内容**逐项一致** ✔、显式优先于系统 ✔；但**降级档的横幅永不退场**（终态 opacity 1 vs 动效档 0） |
| M-13 | 关键反馈音效 | **PASS** | 四个时刻齐备，**140 / 140 / 185 / 190ms**（全部 < 200ms）；首个音效在用户手势之后；静音后四段全静音而**视觉终态逐项一致** |

**计数：PASS 8 · FAIL 4（M-1 / M-7 / M-10 / M-12）· PENDING 1（M-3）。**

> ⚠️ **和 `frames.py` 的判定有三处不同**，全部在 §7 里逐条交代：
> M-9（框架判据陈旧）、M-4（框架的触发顺序让横幅不可见，判据看不见）、
> M-1 / M-10（框架的判据没量到缺的那一段）。**本波没有改 `frames.py` 一个字**，
> 它仍是那 10 条的原始产物来源。

---

## 1. 测量锚点（锚点会漂，日后复核先看这里）

| 项 | 值 |
|---|---|
| `git rev-parse --short HEAD` | **`9d050949`** |
| `workbench/server/static/workbench.css` 字节数（磁盘） | **237 052** |
| 服务返回的 `workbench.css` 字节数（A-39 核对） | **237 052** ⇒ **served == onDisk ✔** |
| 工作树 | 与 HEAD 一致（`git status --short -- workbench/` 为空） |
| 服务 | `python tools/walkthrough/launch.py --port 3311 --side after`（3311 不在禁用端口表内） |
| 隔离 | 池**副本** `tmp/wt-motion/scratch/ws-walk/pool/dmath.db`（源 `pool/dmath.db`，sha256 前后未变）· 注册表 `LESSONKIT_WB_HOME=tmp/wt-motion/scratch/registry` |
| 种子 | `--seed-records 120 --seed-sessions 40`（`realPoolUnchanged: true`）· 另补 13 天作答（见 §8.2） |
| 视口 / 配色 / 时区 | 1440×900 · `light` · `zh-CN` · `Asia/Shanghai`（`shots.py::CONSISTENCY`） |
| 代理 | 所有命令都带 `env -u http_proxy -u https_proxy -u all_proxy` |

> ⚠️ **本波与「版式候选」并行**（另一个执行体在改 `workbench.css`）。
> 上表的 HEAD 与字节数是**我测量时的快照**；锚点漂移时以本表的字节数反查，
> 不要拿别的时刻的 CSS 结论套到本报告上。

---

## 2. 怎么跑的（命令原样）

```bash
# ① 起隔离服务（A-39：仓库根为 cwd ⇒ 服务的是当前工作区）
env -u http_proxy -u https_proxy -u all_proxy python tools/walkthrough/launch.py \
  --port 3311 --side after \
  --out tmp/wt-motion/evidence/after/requests.jsonl \
  --scratch tmp/wt-motion/scratch \
  --seed-records 120 --seed-sessions 40 \
  --seed-pool pool/dmath.db \
  --seed-out tmp/wt-motion/evidence/after/seed \
  --ready-file tmp/wt-motion/ready.json

# ② 分镜条（M-1…M-10）+ 静音孪生（3.3-5）
env -u http_proxy -u https_proxy -u all_proxy python tools/walkthrough/frames.py \
  --base-url http://127.0.0.1:3311 --ws walk \
  --out "openspec/changes/workbench-visual-language-v2/reports/MOTION-VERIFICATION" \
  --plan tmp/wt-motion/evidence/after/seed/plan.json \
  --mute-check

# ③ 补充测量（本波新增的辅助脚本，不改任何已有模块的行为）
env -u http_proxy -u https_proxy -u all_proxy python tools/walkthrough/motion_verify.py \
  --base-url http://127.0.0.1:3311 --ws walk \
  --out "openspec/changes/workbench-visual-language-v2/reports/MOTION-VERIFICATION/extra" \
  --plan tmp/wt-motion/evidence/after/seed/plan.json \
  --pool tmp/wt-motion/scratch/ws-walk/pool/dmath.db --seed-days 13 \
  --only M-1,M-2,M-3,M-4,M-5,M-6,M-9,M-10,M-11,M-12,twins

# ④ 既有探针（M-13 的音效、3.1-6 的 reduced-motion）
env -u http_proxy -u https_proxy -u all_proxy python tools/walkthrough/probe.py \
  static --base-url http://127.0.0.1:3311 --ws walk \
  --out tmp/wt-motion/evidence/after-static --side after --repo-root .
env -u http_proxy -u https_proxy -u all_proxy python tools/walkthrough/probe.py \
  flow   --base-url http://127.0.0.1:3311 --ws walk \
  --out tmp/wt-motion/evidence/after --side after --repo-root . \
  --plan tmp/wt-motion/evidence/after/seed/plan.json
```

**新增文件只有一个**：`tools/walkthrough/motion_verify.py`（辅助脚本）。
`frames.py` / `probe.py` / `launch.py` / `run.py` / `shots.py` / `seed.py` / `g5.py`
**一个字节都没有改**（`git diff --stat -- tools/walkthrough/` 只列出新增文件）。

---

## 3. 逐条判定

> 每条给四样：**判据原文**（`acceptance.md` §2 抄录）· **实测** · **判定** · **证据路径**。

### M-1 台灯主题转场 — **FAIL**

- **判据原文**：`| M-1 | **台灯主题转场** | M-L | 0 / 90 / 180 / 330 / 500 / 700 ms 六帧 | 台灯探出 → 点亮 → 涟漪扩散 → 收回，**四段都在**；700ms 后终态干净；**涟漪期间卡片轮廓不被压平**（只有底色在变） |`
- **实测**：
  | 段 | 实测 | 判定 |
  |---|---|---|
  | ① 探出 | 灯层 `.lk-lamp` 出现，`lk-lamp-lean-out` 140ms：t=0 opacity 0 / `matrix(0.841, …, 158.4)`（在画面外下方），t=90 opacity 1 | ✔ |
  | ② 点亮 | 灯罩暖光层 `.lk-lamp__glow` 挂 `lk-lamp-light-up`：t=0 opacity 0 → t=180 opacity 0.989938 → t=330 opacity 1 | ✔ |
  | ③ 涟漪扩散 | `.lk-ripple` 的 scale：t=0 `0.06` → t=180 `1.76652` → t=330 `4.18976` → t=500 `4.75832` → t=700 `4.8` | ✔ |
  | ④ **收回** | **t=700 时灯层 opacity 仍为 1、transform 仍是单位矩阵、animation 仍是 `lk-lamp-lean-out`** —— 灯**没有收回动画**，它是到点被 `removeLayers()` 从 DOM **直接删掉**的 | ✘ |
  | 700ms 后终态干净 | 另起一趟（不延迟清理计时器）跑到 1200ms：`.lk-lamp` / `.lk-ripple` / `.lk-ripple-glow` 的数量 **0 / 0 / 0** | ✔ |
  | 涟漪期间卡片轮廓不被压平 | 在**有真卡片**的练习页上量：卡片的 `borderTopWidth` `0px`、`borderRadius` `12px`、尺寸 `660×264`、`opacity 1`、`filter`、`z-index` **六帧全同**；命中测试在卡片中心始终命中卡片本身（涟漪 `z-index: 0`，在内容层之下，`pointer-events: none`） | ✔ |
  | 皮肤在转场内换 | 主题在 t=500 已切到 `night`（换肤计时器 590ms） | ✔ |
- **判定**：**FAIL**（四段里 **④ 收回** 不成立）
- **根因**：`@keyframes lk-lamp-retract` 与 `.lk-lamp.is-in { animation: lk-lamp-retract 110ms … }`
  都写在 `workbench.css:3876 / 4344`，但 **`is-in` 全仓库没有任何代码挂上去**
  （`grep -rn "is-in" workbench/` 只命中 CSS 自身）。`workbench.js::runLampTransition`
  只 `lamp.classList.add("is-out", "is-lit")`，收尾靠 `LAMP_CLEAN_MS = 700` 的
  `setTimeout(removeLayers)` ⇒ **收回段是「突然消失」，不是「收回」**。
- **证据**：`extra/M-1/`（六帧）+ `extra/M-1-strip.png` + `extra/M-1-cards/`（卡片对照六帧）
  + `extra/M-1-cards-strip.png` + `extra/M-1-extra.json`
  （`checks` / `stages` / `cardMeasurement` / `terminalAfter700ms`）

### M-2 交卷庆祝（日常档）— **PASS**

- **判据原文**：`| M-2 | **交卷庆祝（日常档）** | M-F | 0 / 120 / 300 / 600 / 900 ms 五帧 | 数字滚动 + 进度带 0→100%；**无彩带**（彩带只在里程碑档） |`
- **实测**：
  - **数字滚动** ✔：完成页的数字槽位是 `.lk-stat__value[data-lk-value]`，由 `window.lkTicker.set`
    （rAF 写 `textContent`）驱动 ⇒ **不是 CSS 动画**，`frames.py` 的 `setTime` 地址不到它。
    改用 16ms 间隔的**密采样**（32 个样本）⇒ 采到 **6 次中间值**（数字从 0 逐格滚到终值）。
  - **进度带 0→100%** ✔：`.lk-progress__fill`（**两个下划线**；`frames.py` 的 watch 表里写的是
    `.lk-progress-fill` **一个下划线**，选不中）⇒ 补测：`scaleX` 序列 **0 → 0.672573 → 0.975622 → 1 → 1**；
    终态动效档与降级档都是 `scaleX(1)`。
  - **无彩带** ✔：五帧里 `.lk-confetti` 数量 **0**、`.lk-celebrate-burst` 数量 **0**
    （纸片与爆点在日常档**根本没有创建**）。
  - **CTA 不被遮挡**（M-3 的判据，M-2 一并量）：完成页主按钮「查看本次答卷」
    （`BUTTON.primary`）中心命中测试每帧都命中按钮本身。
- **判定**：**PASS**
- **证据**：`extra/M-2/` + `extra/M-2-strip.png` + `extra/M-2-extra.json`（`derived`）

### M-3 交卷庆祝（里程碑档）— **PENDING**

- **判据原文**：`| M-3 | **交卷庆祝（里程碑档）** | M-G | 0 / 150 / 400 / 800 / 1200 ms 五帧 | 在 M-2 基础上叠几何爆点 + 纸片；时长更长但**不遮挡完成页 CTA**；触发条件只有**两个**（全对 / 章节首次完成），两个条件各采一次，其余轮次留在日常档 |`
- **实测**：
  - **叠几何爆点 + 纸片** ✔：`.lk-celebrate-burst` **1** 个、`.lk-confetti` **12** 张，五帧都在。
  - **不遮挡 CTA** ✔：主按钮中心命中测试每帧命中按钮本身；装饰层 `pointer-events: none`。
    （诚实补充：t=150 与 t=400 各有 **1** 张纸片的**盒子**与 CTA 的盒子相交，
    但纸片是 `pointer-events:none` 的小图形、不是不透明覆盖层，按钮始终可点可读。）
  - **触发条件「本轮全对」** ✔：本轮 **3/3 全对**（`data-lk-total=3` / `data-lk-correct=3`）
    ⇒ 里程碑档正确触发。
  - **触发条件「章节首次完成」** ✘ **不可判定**：客户端恒写 `data-lk-chapter-first="false"`
    —— `practice_runs` **没有章列**，服务端没有「该章此前未完成」这个事实，
    `paper-practice.js::writeCompletionFacts` 无从判断。`decisions.md` **A-29** 明令
    **不许用代理指标近似**，所以这一档既采不到也**不许推算** ⇒ 判 **PENDING**（不是 FAIL）。
- **判定**：**PENDING**（一条条件已通过，另一条缺数据）
- **证据**：`extra/M-3/` + `extra/M-3-strip.png` + `extra/M-3-extra.json`
  + `frames/M-3.json`（`completionFacts` / `conditions`）

### M-4 连对升级（5 连 / 10 连插播）— **PASS**

- **判据原文**：`| M-4 | **连对升级（5 连 / 10 连插播）** | M-I | 0 / 100 / 250 / 450 / 700 ms 五帧 | 横幅出现 → 数字替换 → 退场；**横幅只有一份**，数字是参数化输入的结果 |`
- **实测**：
  - **横幅出现** ✔：`.lk-combo-banner` 带 `is-on`，opacity 序列 `1 / 1 / 1 / 1 / 0`（末帧退场）。
  - **数字替换** ✔：5 连那轮横幅数字 **5**，10 连那轮 **10** —— 同一份 DOM、同一套动画，
    只有数字不同 ⇒ **参数化**成立。
  - **退场** ✔：t=700 opacity 回到 **0**。
  - **横幅只有一份** ✔：每帧 `.lk-combo-banner` 元素数 = **1**。
  - ⚠️ **一处必须交代**：`frames.py` 的 M-4 分镜条里，横幅**每帧 opacity 都是 0**
    （横幅从没亮起来）—— 它的触发是 `streak.apply(...)` **在** `host.innerHTML = streak.html()`
    **之前**调用的，而 `showBanner()` 挂的 `is-on` 类随后被整块重绘冲掉了。
    **产品自己的两条流都是「先重绘、后 apply」**
    （`paper-practice.js:1141` / `practice-flow.js:1697`）⇒ 本条按**产品的顺序**复测，
    结论如上。`frames.py` 的 M-4 判定（`横幅只有一份`）只数元素个数，**看不见**这个差别。
- **判定**：**PASS**
- **证据**：`extra/M-4/` + `extra/M-4-strip.png` + `extra/M-4-10/` + `extra/M-4-10-strip.png`
  + `extra/M-4-extra.json`

### M-5 连对计数器三档 — **PASS**

- **判据原文**：`| M-5 | **连对计数器三档** | M-H | 三张静帧（0 / >0 / ≥30） | 灰 → 黄 → 黄蓝渐变，**不靠文字** |`
- **实测**（`extra/M-5/00.png` · `05.png` · `31.png`）：

  | 档 | 类名 | 档位色条（`::before`） | 火苗 | 内边距 | 数字 |
  |---|---|---|---|---|---|
  | 0 连 | `lk-streak` | 灰 `rgb(141,133,120)` | 无 | 14px | 0 |
  | 5 连 | `lk-streak is-warm` | 黄 `rgb(245,197,24)` | 黄 | 14px | 5 |
  | 31 连 | `lk-streak is-hot` | **渐变** `linear-gradient(rgb(245,197,24), rgb(43,98,232))` | **同款渐变** | 18px | 31 |

  ⇒ 灰 → 黄 → **黄蓝渐变** 三档俱全；档位由**颜色 + 形状（色条/火苗）+ 内边距**承载，
  **文字被遮住仍能读出档位** ⇒ 不靠文字成立。
- **判定**：**PASS**
- **证据**：`extra/M-5/`（三张静帧）+ `extra/M-5-extra.json`

### M-6 连对进度火苗簇 — **PASS**

- **判据原文**：`| M-6 | **连对进度火苗簇** | M-J | 0 / 200 / 500 ms 三帧 | 火苗逐簇点亮；**答案错时必须出现负反馈**（不得沉默） |`
- **实测**：
  - **逐簇点亮** ✔：点燃动画挂在**簇**（`.lk-flame`）上，同一帧内五簇的 opacity 为
    **1 / .957848 / .55385 / 0 / 0**（t=200）⇒ 同一时刻有的簇已亮、有的还没到；
    错峰写在行内 `animation-delay`：**0 / 80 / 160 / 240 / 320ms**。
  - **答错时的负反馈** ✔：见 M-11（同一个状态机，负反馈通道实测在位）。
- **判定**：**PASS**
- **证据**：`extra/M-6/` + `extra/M-6-strip.png` + `extra/M-6-extra.json`

### M-7 挤压回弹（答对）— **FAIL（按判据字面）**

- **判据原文**：`| M-7 | **挤压回弹（答对）** | M-B | 0 / 17 / 33 / 83 / 167 / 217 / 517 ms 七帧 | scale 0.92 → 1.06 → 1 的回弹曲线可见；总时长 ≈517ms |`
- **实测**（真实判定：答对 → 产品自己把回弹挂在**被选中的那一行**
  `label.option-row.lk-squash` 上，`.micro-verdict` 显示「判定：正确」）：
  | 帧 | 0 | 17 | 33 | 83 | 167 | 217 | 517 |
  |---|---|---|---|---|---|---|---|
  | scale | **0.6** | **1.1** | 1.1 | 1.00513 | 0.974381 | 0.997669 | **1** |

  - **总时长** ✔：`animation-duration: 0.517s`（= 517ms）。
  - **落点** ✔：`squashCorrectOption` 把 `.lk-squash` 挂在**被选中的那一行**（A-89）——
    实测两个 `.lk-squash` 的文字正是本次选中的两个选项。
  - **回弹曲线** ✘：判据写的三个数 **0.92 / 1.06 / 1** 在实测里**一个都没出现**
    （实测是 0.6 / 1.1 / … / 1）。
- **判定**：**FAIL** —— 按 `acceptance.md` §2 的**字面数字**判；曲线本身是「压扁→过冲→回落」的
  回弹曲线，形态在，**数字不在**。
- **根因 / 漂移登记**：实现与 `design-notes/motion-spec.md` §3.1 的 CSS **逐字相同**
  （`scale(.6) → scale(1.1) → scale(1.1) → scale(.9603) → scale(1.0067) → scale(1)`，
  百分比 3.288 / 9.671 / 25.725 / 58.027 / 100 = 517ms 归一化），
  OpenSpec delta 也只要求「squash-and-stretch rebound」而**不写数字**。
  ⇒ **不是实现走样，是 `acceptance.md` §2 M-7 这一行的数字与 motion-spec 对不上**
  （本波不改判据、不改实现 ⇒ 登记为漂移，见 §7.3）。
- **证据**：`frames/M-7/`（七帧）+ `frames/M-7-strip.png` + `frames/M-7.json`
  （`verdictElements`：回弹目标 = 两个被选中的选项行，时长 0.517s）

### M-8 视图转场 — **PASS**

- **判据原文**：`| M-8 | **视图转场** | M-C / M-E | 0 / 60 / 120 / 240 ms 四帧 | 内容**上浮 8–12px + 淡入**；不得出现「硬生生蹦出来」；转场**挂在页面容器上**（切页整体替换 innerHTML 后仍播放） |`
- **实测**：`#middle-page > *` 的 transform / opacity：
  | 帧 | 0 | 60 | 120 | 240 |
  |---|---|---|---|---|
  | translateY | **12px** | 4.86899 | 1.52529 | 0 |
  | opacity | 0 | 0.594251 | 0.872893 | 1 |

  上浮峰值 **12px**（判据 8–12 ✔）· 淡入 ✔ · 动画挂在 **`#middle-page > *`**
  （容器动画，`#middle-page` 的 `innerHTML` 整体被替换后仍播放）✔。
- **判定**：**PASS**
- **证据**：`frames/M-8/` + `frames/M-8-strip.png` + `frames/M-8.json`

### M-9 骨架屏 — **PASS**（按 A-115 / A-117 定稿口径）

- **判据原文**（`acceptance.md` §2 M-9，**已按 A-115 / A-117 改成呼吸式**）：
  `灰块**整体明暗呼吸**（底色变化可见；**无横扫、无表面渐变**，见 decisions.md A-115）`
- **实测**（六次采样 0 / 200 / 400 / 600 / 800 / 900ms）：
  - **有体积** ✔：五块 `304×26 · 660×128 · 607×16 · 502×16 · 568×16`。
  - **块自身表面随时间变化** ✔：块**自身**的 `opacity` 走 **1 → .869877 → .573441 →
    .473633 → .45 → .472348**（动画 `lk-skeleton-breathe`，只动 opacity）。
  - **无横扫** ✔：`::after` 的 `animationName` 全程 **none**（横扫覆盖层整族已删）。
  - **无表面渐变** ✔：块自身的 `background-image` 与 `::after` 的 `background-image`
    全程 **none**。
  - **降级档** ✔：同样 5 块、同样体积、**静止**（opacity 恒为 1、无动画）。
    ⚠️ 降级档的块**不带 `.lk-skeleton` 类**（产品用等价的静态灰块替身，
    `middle-navigation.js::skeletonBlock`），所以要用 `[data-lk-skeleton] > div` 选。
- **判定**：**PASS**
- **诚实交代**：`frames.py` 的 M-9 判据**已经陈旧**——它还在量「微光**位置**是否变化」
  （A-115 已作废的横扫口径），因此给出 **FAIL**「骨架块有尺寸，但微光位置全程不变」。
  同一轮的既有探针 `3.4-3`（按 A-117 定稿口径）判 **PASS**
  「骨架屏有体积，且加载期有呼吸动效」⇒ **独立佐证**本条的 PASS。
- **证据**：`extra/M-9/`（六帧）+ `extra/M-9-strip.png` + `extra/M-9-extra.json`
  + `frames/M-9/`（旧口径的三帧）

### M-10 数据层（负荷柱 / 日历）— **FAIL**

- **判据原文**：`| M-10 | **数据层（负荷柱 / 日历）** | — | 0 / 240 / 480 ms 三帧 | 负荷柱从 0 生长、逐柱错峰；日历格按强度扩散（**颜色 + 高度双编码**） |`
- **实测**：
  - **负荷柱从 0 生长** ✔：14 根柱在 t=0 的 `scaleY` 全为 **0**；
    终态（动画跑完）全部 **1**。
  - **逐柱错峰** ✔：行内 `animation-delay` = **0 / 24 / 48 / 72 / … / 312ms**；
    t=120 时各柱 `scaleY` = **.766 / .673 / .550 / .393 / .205 / 0 / 0 / …**
    ⇒ 错峰**看得见**。
  - **日历格颜色 + 高度双编码** ✔：`.record-activity-day` 共 **84** 格，
    三档实测（level-0 / level-1 / level-4）——
    底色 `srgb(.925,.937,.963)` / `srgb(.850,.883,.958)` / `srgb(.352,.518,.923)`，
    高度 **4px / 7px / 28px**（颜色与高度同向）。
  - **日历格「按强度扩散」** ✘：**格子自身没有任何动画**
    （`animationName` 全程 **none**，帧间高度与 transform 均不变）
    ⇒ 颜色 + 高度双编码是**静态编码**，「扩散」这个**过程**不存在。
- **判定**：**FAIL**（负荷柱那一半全对；日历那一半缺「扩散」的过程）
- **根因**：`workbench.css` 的 `.record-activity-day` 只有 `--level-bg`（颜色）与
  服务端给的行内 `height`（高度）——**没有 `animation`**。
  `design-notes/motion-spec.md` §2.1 第 19 项把「**日历扩散**」列为进度带动效的三个使用方之一
  （`scaleX 0→1` + 24ms 错峰），实现里只落地了负荷柱那一份。
- **证据**：`extra/M-10/`（四帧）+ `extra/M-10-strip.png` + `extra/M-10-extra.json`
  + `frames/M-10/`（原三帧）

### M-11 连对断裂负反馈 — **PASS**

- **判据原文**：`| M-11 | **连对断裂负反馈** | M-K | 0 / 80 / 200 / 400 ms 四帧 | 连对 > 4 时答错**必须**出现明确负反馈（**不得沉默**）；计数器归零；火苗簇逐簇熄灭；**不做屏幕级震动**（摆动幅度 ≤4px） |`
- **判据的手段**：`frames.py` **没有** M-11 条目 ⇒ 本波**自写最小探针**
  （`tools/walkthrough/motion_verify.py::run_m11`），驱动的是**产品自己的**
  `window.lkStreak` 状态机，顺序照产品（先重绘、后 apply）。
- **实测**（先连对 5 次，再答错）：
  - **明确负反馈，不得沉默** ✔：计数器挂上 `lk-error-nudge`（`animationName: lk-error-nudge`）。
    摆动采样 `0 → -3.93 → +3.36 → -0.65 → -1.09 → 0`。
  - **摆动幅度 ≤4px** ✔：实测峰值 **3.93px**（关键帧写死 ±4px）。
  - **不做屏幕级震动** ✔：计数器的**祖先链**与 `body` / `html` 的水平位移实测 **0.00px**
    （位移只发生在计数器自己身上）。
  - **计数器归零** ✔：数字 **5 → 3 → 2 → 1 → 0**（ticker 滚动）。
  - **火苗簇逐簇熄灭** ✔：亮着的簇数 **5 → 4 → 3 → 2 → 2 → 1 → 0**（40ms 一簇），终态全灭。
  - 负反馈**不由横幅承担**（断裂时横幅没有 `is-on`）——走的是**摆动 + 火苗**两条通道。
- **判定**：**PASS**
- **证据**：`extra/M-11/`（四帧）+ `extra/M-11-strip.png` + `extra/M-11-extra.json`
  （`evidence.litFlamesDensePoll` / `counterShiftsDensePoll` 是 30 点的密采样）

### M-12 动效偏好与系统 reduced-motion 的分级降级 — **FAIL**

- **判据原文**：`| M-12 | **动效偏好与系统 reduced-motion 的分级降级** | M-M | 四张静帧（系统 reduce + 偏好未设 / 系统 reduce + 偏好显式「开」/ 系统允许 + 偏好未设 / 系统允许 + 偏好「关」） | 四种组合下的**终态与「动效开启」时逐项一致**；系统 reduce + 偏好显式「开」⇒ 动效恢复（显式选择优先于系统）；偏好显式「关」⇒ 全部直切 |`
- **判据的手段**：`frames.py` 只取**一种**孪生（系统 reduce + 偏好未设）；
  四组合由本波探针手工跑（`run_m12`：Playwright 的 `reduced_motion` 模拟系统设置
  + `localStorage["wb_settings_walk"].motion` 写显式偏好）。
- **实测**：

  | 组合 | `lkMotion.mode()` | `<html data-motion>` | 台灯层是否创建 | 计数器档位 | 数字 | 火苗 | 横幅内容 | **横幅终态 opacity** |
  |---|---|---|---|---|---|---|---|---|
  | 系统 reduce + 偏好未设 | `weak` | （无） | **否** | 1 | 5 | 5/5 亮 | 5 | **1** ❌ |
  | 系统 reduce + 偏好显式「开」 | `full` | `on` | **是** | 1 | 5 | 5/5 亮 | 5 | 0 ✔ |
  | 系统允许 + 偏好未设 | `full` | （无） | **是** | 1 | 5 | 5/5 亮 | 5 | 0 ✔ |
  | 系统允许 + 偏好显式「关」 | `off` | `off` | **否** | 1 | 5 | 5/5 亮 | 5 | **1** ❌ |

  - **档位分级** ✔：四种组合的 `mode()` 与 A-2 的分级**逐条吻合**。
  - **显式优先于系统** ✔：系统 reduce + 偏好显式「开」⇒ `mode()=full`、**台灯层被创建**
    （动效恢复）；偏好显式「关」⇒ `mode()=off`、**台灯层不创建**（全部直切）。
  - **终态逐项一致**（数字 / 计数器档位 / 火苗簇 / 横幅内容 / 横幅是否点亮）✔：**四行完全相同**。
  - **但横幅的「退场」不一致** ❌：动效档的横幅在 hold 结束时 opacity 归 **0**；
    **降级档（weak 与 off）停在 opacity 1** —— 横幅**留在屏幕上不退场**。
- **判定**：**FAIL**
- **根因**：`showBanner()` 只**加** `is-on`（`workbench.js:589`），**没有任何代码移除它**；
  横幅的退场**只存在于 `@keyframes lk-combo-out` 的 `forwards` 填充**里。
  降级档把 `animation-name` 置 none（weak）或 `animation: none !important`（off）
  ⇒ **`lk-combo-out` 不再跑 ⇒ 横幅永远不消失**。
  `design-notes/motion-spec.md` §7.2 第 18 行本来就写着降级档要
  「横幅**直接以终态出现**并在 `hold` 后直接消失 | 去掉 `animation`；用 `setTimeout` 控制显隐」
  —— **`setTimeout` 那一半没有实现**。
  ⇒ 这是**实现缺口**（不是判据问题），且它同时是 M-4「退场」在降级档的落空。
- **证据**：`extra/M-12/`（四张静帧）+ `extra/M-12-extra.json`（`rows` / `checks`）

### M-13 关键反馈音效 — **PASS**

- **判据原文**：`| M-13 | **关键反馈音效** | M-N | 四段波形（答对 / 答错 / 完成 / 里程碑） | 每条 **< 200ms**；**只在**这四个时刻发声（其它任何状态变化零发声）；首条之前**必须**有一次用户手势；静音时四段均为静音且**视觉反馈一个不少** |`
- **判据的手段**：`frames.py` 没有 M-13 条目 ⇒ 走**既有探针**
  `3.3-1` / `3.3-2` / `3.3-3` / `3.3-4`（`probe.py static` + `probe.py flow`）+ 静音孪生 `3.3-5`。
- **实测**：
  - **四个时刻齐备、每条 < 200ms** ✔：直接量资产本身（`wave` 模块）——
    `sfx-right.wav` **140.0ms** · `sfx-wrong.wav` **140.0ms** ·
    `sfx-complete.wav` **185.0ms** · `sfx-milestone.wav` **190.0ms**；
    与 `sfx.js` 的 `CUES` 表（0.140 / 0.140 / 0.185 / 0.190）逐条一致。
  - **只在四个时刻发声** ✔：`3.3-1`（真卷跑）判 **PASS**「答完题后 playCue 调用 3 次，
    播放 3 次，浏览器没有拦截」—— `summary = {gradedAnswers: 3, cueCalls: 3, plays: 3,
    answersWithoutCue: [], browserBlocked: false}`，控制组另播了 `sfx-complete.wav`；
    四个 cue 之外的调用数为 0。
  - **首条之前有一次用户手势** ✔：`3.3-2` 判 **PASS**「手势之前无声，手势之后有播放」
    （`userActivationAfterGesture: true`）。
  - **静音开关** ✔：`3.3-3` / `3.3-4` 判 **PASS**「静音开关存在，静音后四个时刻全部无声」。
  - **静音时视觉反馈一个不少** ✔：`3.3-5`（`frames.py --mute-check`）判 **PASS**
    「静音与开静音的终态一致 —— 声音不是唯一通道」，
    `terminalDifferences = []`（逐项比对零差异）。
    （诚实补充：中途帧的像素有差（ae 0 / 2910 / 6187 / 189 / 189）——
    庆祝的挂件是**挂钟驱动**的，两趟跑的墙钟相位不同；判据关心的是终态，终态零差异。）
- **判定**：**PASS**
- **证据**：`tmp/wt-motion/evidence/after-static/probe/3.3-*.json`（探针原始产物，留在 `tmp/`）
  + `reports/MOTION-VERIFICATION/3.3-5.json`（静音孪生，已入库）
  + `frames/mute-on/` · `frames/mute-off/`

---

## 4. 终态铁律对照表（降级帧的终态 vs 动效帧的终态）

> **判据**（`acceptance.md` §2 通用判据 / §3.8）：
> 「降级帧的终态必须与动效开启时的终态一致（数字、进度带、计数器档位、灯与涟漪层、
> 纸片、火苗簇、内容位置**逐项比对**），**不得停在中间态或不可见**。」
>
> **怎么比**：同一触发、同一时刻（终态），两档各跑一趟；
> 用 `frames.py::compare_terminal` 对 **`TERMINAL_CONTRACT`** 里枚举的项**逐项**比
> （数字 / 进度带 / 计数器档位 / 灯与涟漪层 / 纸片 / 火苗簇 / 内容位置），
> 契约外的差异**如实列出但不参与判定**。

| # | 动效 | 契约项差异 | 契约外的差异（如实登记） | 终态一致？ | 怎么比的 |
|---|---|---|---|---|---|
| M-1 | 台灯转场 | **0** | 设置页自己的档位标签（动效「完整」vs「弱动效」）——产品对当前档位的显示，不是动效终态 | ✔ | `frames/M-1.json` + `extra/twins.json` |
| M-2 | 交卷庆祝（日常） | **0** | 0 | ✔ | 同上 |
| M-3 | 交卷庆祝（里程碑） | **0** | 降级档**不画**爆点与纸片（`motion-spec` §7.2 第 14 行明写「爆点与纸片不画」）⇒ 设计如此 | ✔ | 同上 |
| M-4 | 连对横幅 | **0** | **横幅 opacity：动效档 0（已退场）vs 降级档 1（永不退场）**；transform 同因 | ⚠️ **不一致** | `extra/twins.json` |
| M-5 | 计数器三档 | **0** | 0 | ✔ | `frames/M-5.json` + `extra/twins.json` |
| M-6 | 火苗簇 | **0** | 同 M-4 的横幅差异 | ⚠️ **不一致** | `extra/twins.json` |
| M-7 | 挤压回弹 | **0** | 0 | ✔ | `frames/M-7.json` + `extra/twins.json` |
| M-8 | 视图转场 | **0** | 0 | ✔ | `frames/M-8.json` + `extra/twins.json` |
| M-9 | 骨架屏 | **0** | 降级档的 5 块**不带 `.lk-skeleton` 类**（等价的静态灰块替身，`motion-spec` §7.2 第 9 行）；中栏高度 264 vs 261px（3px） | ✔（体积与外观等价） | `extra/M-9-extra.json` + `extra/twins.json` |
| M-10 | 数据层 | **0** | 0 | ✔ | `extra/M-10-extra.json` + `extra/twins.json` |
| M-11 | 断裂负反馈 | 0（数字 / 档位 / 火苗簇全等） | 计数器上的 `lk-error-nudge` 类与摆动 —— 降级档不摆（设计如此：§7.2 第 11 行） | ✔ | `extra/M-11-extra.json`（reduced 跑同触发） |
| M-12 | 分级降级 | **0**（四组合对「动效开启」逐项一致） | 横幅 opacity（见 M-4 行） | ⚠️ **不一致**（横幅一项） | `extra/M-12-extra.json` |
| M-13 | 关键反馈音效 | — | 静音 vs 不静音：终态**零差异**（`3.3-5`） | ✔ | `reports/MOTION-VERIFICATION/3.3-5.json` |

**逐帧孪生图**（每条动效的「动效档终态 / 降级档终态」并排）
`reports/MOTION-VERIFICATION/extra/twins/M-<n>-animated.png` 与 `M-<n>-reduced.png`
（M-1…M-10 各一对，共 20 张）。

**结论**：**契约内枚举的项，13 条全部一致（差异 0）**；
唯一的不一致是**连对横幅的退场**（M-4 / M-6 / M-12 三条指向同一个根因，见 §7.4）。

---

## 5. 三条 `frames.py` 没有条目的动效 —— 用的什么手段

| 动效 | 手段 | 结论 |
|---|---|---|
| **M-11** 连对断裂负反馈 | **本波自写最小探针**（`tools/walkthrough/motion_verify.py::run_m11`）：驱动产品自己的 `window.lkStreak` 状态机（顺序照产品：先重绘、后 apply），四帧分镜 + 30 点密采样 | **PASS** |
| **M-12** 分级降级 | 走**既有探针** `3.1-6`（`probe_reduced_motion`）**+** 本波探针手工补齐**四种组合**（Playwright `reduced_motion` 模拟系统设置 × `localStorage` 显式偏好），逐项与「动效开启」比 | **FAIL**（横幅退场） |
| **M-13** 关键反馈音效 | 走**既有探针** `3.3-1` / `3.3-2` / `3.3-3` / `3.3-4`（`probe.py static` + `probe.py flow`，真卷跑）+ 静音孪生 `3.3-5`；四段时长另用 `wave` 直接量资产 | **PASS** |

---

## 6. 分镜条产物清单

```
reports/MOTION-VERIFICATION/
├── MOTION-VERIFICATION.md            ← 本报告（在 reports/ 下，与本目录同级）
├── 3.3-5.json                        ← 静音孪生（3.3-5）的判定与逐帧 ae
├── frames/                           ← frames.py 的原始产物
│   ├── M-<n>/0000.png …              ← 每条动效的分镜帧序列
│   ├── M-<n>-strip.png               ← 分镜条（拼图）
│   ├── M-<n>.json                    ← frames.py 的逐帧元数据 + 终态对照
│   ├── mute-on/ · mute-off/          ← 3.3-5 的静音孪生两套帧
└── extra/                            ← 本波补充探针的产物
    ├── M-1/ · M-1-cards/             ← 台灯转场（设置页 / 有真卡片的练习页）
    ├── M-2/ · M-3/                   ← 庆祝两档
    ├── M-4/ · M-4-10/                ← 横幅（5 连 / 10 连）
    ├── M-5/                          ← 计数器三档静帧
    ├── M-6/                          ← 火苗簇
    ├── M-9/ · M-10/                  ← 骨架屏 / 数据层
    ├── M-11/                         ← 断裂负反馈
    ├── M-12/                         ← 四组合静帧
    ├── twins/M-<n>-{animated,reduced}.png   ← 终态孪生对（20 张）
    ├── M-<n>-strip.png                ← 各条 strip
    ├── M-<n>-extra.json               ← 各条的判定 + 逐项实测
    └── twins.json                     ← 终态对照表（机器可读）
```

---

## 7. FAIL 项的实情（差多少 + 根因）

> 不给「建议」当结论，只给**实测差值**与**根因定位**（文件 + 行 + 差多少）。

### 7.1 M-1 台灯转场 — **④ 收回段没有动画**

- **差多少**：判据要求「四段都在」。实测 **三段**（探出 / 点亮 / 涟漪扩散）齐备，
  **第四段缺失**：t=700ms 时灯层 `opacity = 1`、`transform = 单位矩阵`、
  `animationName = lk-lamp-lean-out`（仍是探出那条），**没有收回**。
  按设计，④ 应该是 590–700ms 内 `opacity 1→0` + `translateY 0→-28%` + `scale .9`。
- **根因**：`workbench/server/static/workbench.css:3876` 定义了 `@keyframes lk-lamp-retract`，
  `:4344` 定义了 `.lk-lamp.is-in { animation: lk-lamp-retract 110ms … }`，
  但 **`is-in` 从未被任何代码挂上**（`grep -rn "is-in" workbench/` 只命中 CSS 自身）。
  `workbench.js::runLampTransition`（:733 起）只 `add("is-out", "is-lit")`，
  收尾是 `LAMP_CLEAN_MS = 700` 的 `setTimeout(removeLayers)` ⇒ **直接删除，不是收回**。
  ⇒ 差的是**一段动画**（0 个关键帧被播放），不是参数偏差。

### 7.2 M-7 挤压回弹 — **曲线数字与判据不符**

- **差多少**：判据写 `scale 0.92 → 1.06 → 1`；实测 **0.6 → 1.1 → 1.1 → 1.00513 →
  0.974381 → 0.997669 → 1**（t = 0 / 17 / 33 / 83 / 167 / 217 / 517ms）。
  起点比判据**更扁**（0.6 vs 0.92，差 0.32），过冲比判据**更大**（1.1 vs 1.06，差 0.04），
  中段的回落点也不同（1.00513 / 0.974381 / 0.997669 vs 判据没写的三段）。
  时长 517ms ✔、落点（被选中的那一行）✔。
- **根因（漂移，不是实现走样）**：实现与 `design-notes/motion-spec.md` §3.1 的 CSS
  **逐字相同**；OpenSpec delta（`specs/workbench-ui/spec.md:159`）只要求
  「squash-and-stretch rebound」，**不写数字**。
  ⇒ **`acceptance.md` §2 M-7 这一行的三个数字与 motion-spec 不一致**（本波不改判据）。
  ⚠️ 另有一处内部不一致（不影响判定）：`tasks.md` 8.2 写「17 / 33 / 83 / 167 / 217ms」，
  而 motion-spec 的归一化是 **17 / 50 / 133 / 300 / 517ms**。

### 7.3 M-9 — 判据已改，**执行器没跟上**（登记为漂移，非产品缺陷）

- `frames.py::judge_skeleton` 仍按 A-115 **作废**的「微光**位置**是否变化」判定 ⇒ 它给 FAIL；
  而产品自 A-115 改的就是**呼吸式**（`lk-skeleton-breathe`，只动 opacity）⇒ 按新判据**该判 PASS**。
  既有探针 `3.4-3`（A-117 定稿口径）也判 **PASS**。
- **本波的处理**：不改 `frames.py`（**禁改已有模块的行为**），另用本波探针按新口径复测并给出 PASS。
- **根因**：`frames.py` 的 M-9 判据与 `acceptance.md` §2 的现行口径（及 `decisions.md` A-115 / A-117）
  **不同步** ⇒ 执行器侧漂移，需要执行器单独打一个补丁（**下一波**，本波不动）。

### 7.4 M-12 / M-4 / M-6 — **降级档的连对横幅永不退场**

- **差多少**：横幅终态 opacity —— 动效档 **0**（已退场），降级档（weak 与 off）**1**（留在屏幕上）。
  其余全部逐项一致（数字 5 / 档位 1 / 火苗 5 簇 / 横幅内容 5 / 横幅 `is-on`）。
- **根因**：`showBanner()`（`workbench.js:589`）**只加** `is-on`，**从不移除**；
  退场完全依赖 `@keyframes lk-combo-out` 的 `forwards` 填充。
  降级闸门（`workbench.css:4362` 的 `animation: none !important` 与 `:4371` 的
  `animation-name: none !important`）把这条动画关掉 ⇒ **横幅永远不消失**，
  直到下一次整卡重绘把 `is-on` 一起冲掉。
  `motion-spec` §7.2 第 18 行要求降级档「在 `hold` 后直接消失 | 去掉 `animation`；
  **用 `setTimeout` 控制显隐**」—— **`setTimeout` 那一半没有实现**。

### 7.5 M-10 — **日历格没有「扩散」的过程**

- **差多少**：判据的日历半句是「日历格按强度扩散（颜色 + 高度双编码）」。
  **颜色 + 高度双编码实测存在**（三档：底色 3 种 + 高度 4 / 7 / 28px）；
  **「扩散」这个过程不存在**：84 格日历的 `animationName` 全程 **none**，
  帧间高度与 transform 零变化（**差 0 个动画**）。
  负荷柱那一半全对（从 0 生长 ✔、逐柱错峰 24ms ✔、终态满格 ✔）。
- **根因**：`workbench.css:3368` 的 `.record-activity-day` 只有 `--level-bg`（颜色）
  与服务端给的行内 `height`（高度），**没有 `animation`**。
  `motion-spec` §2.1 第 19 项把「**日历扩散**」列为进度带动效的三个使用方之一，
  实现只落地了负荷柱那一份。

---

## 8. 诚实回报

### 8.1 哪些**没有**跑成 / 是 PENDING

1. **M-3 的「章节首次完成」那一档 —— PENDING（不可判定）**。
   服务端 `practice_runs` **没有章列**，客户端恒写 `data-lk-chapter-first="false"`；
   `decisions.md` A-29 明令不许用代理指标近似 ⇒ **既采不到也不许推算**。
   本报告**没有**对这一档给出 PASS，也没有假装它成立。
2. **M-13 的四段「波形」没有画成图** —— 判据写的是「四段波形」，本波量的是
   **四个 WAV 资产的时长**（140 / 140 / 185 / 190ms）与**探针的播放记录**，
   没有渲染波形图（资产是仓库里的 `.wav`，不在本波交付范围）。
3. **M-11 / M-12 的分镜条是本波自写探针产的**，不是 `frames.py` 的产物
   （`frames.py` 根本没有这两条的条目）。两者的帧命名与元数据格式不完全一致。
4. **M-1 的「700ms 后终态干净」是另起一趟量的**（不延迟清理计时器的那一趟），
   因为 1440×900 的截图本身耗时超过 700ms，清理计时器会在分镜条拍完前把三层删掉。
   同理，`extra/M-1/` 与 `extra/M-1-cards/` 的分镜条是把**清理计时器延后**拍的
   （只延后这一个 `setTimeout`，CSS 动画本身没动，动画时刻仍由 `setTime` 寻址）。
   这一处**在报告里明写**，以免日后被当成产品行为。

### 8.2 哪些是**靠推算**而非实测

- **本报告里没有靠推算得出的 PASS**。所有 PASS 都附了实测数字与产物路径。
- 唯一带「据代码/据 markup」的判断是**根因定位**（如「`is-in` 全仓库无人挂」），
  那是**读代码**得出的**事实**，不是判据的推算。
- **一处为可测性而动的数据**：记录中心的「负荷柱」是**近 14 天**的图，
  而 `seed.py` 的固定时间戳落在 **2026-03** ⇒ 本轮只有 1 天有数据，**错峰看不出来**。
  为此本波往**隔离副本**里补了 **13 天**（每天 1 条作答，`--seed-days 13`），
  只写 `tmp/wt-motion/scratch/ws-walk/pool/dmath.db`（**真实池未动**，
  `launch.py` 的 `realPoolUnchanged: true` 为证）。补完之后错峰可测（t=120 时
  各柱 scaleY = .766 / .673 / .550 / .393 / .205 / 0 …）。

### 8.3 判据与实现的**漂移**登记（本波不裁决，只登记）

| # | 漂移 | 涉及文件 | 本波的处理 |
|---|---|---|---|
| D-1 | M-7 的曲线数字（0.92 → 1.06 → 1）与实现 / motion-spec（0.6 → 1.1 → … → 1）不一致 | `acceptance.md` §2 M-7 ⟷ `design-notes/motion-spec.md` §3.1 ⟷ `workbench.css:3750` | 按 `acceptance.md` 的字面判 **FAIL**；登记漂移，**不改任何一方** |
| D-2 | `frames.py::judge_skeleton` 仍按作废的「微光位置」口径判 M-9 | `tools/walkthrough/frames.py` ⟷ `acceptance.md` §2 M-9（A-115 / A-117） | **不改 `frames.py`**；另按新口径复测并给出 PASS；执行器侧待下一波打补丁 |
| D-3 | `frames.py` 的 M-4 触发顺序与产品相反 ⇒ 横幅永远不亮，而它的判据只数元素个数 | `tools/walkthrough/frames.py::act_streak` ⟷ `paper-practice.js:1141` / `practice-flow.js:1697` | 按产品的顺序复测 ⇒ PASS；执行器侧待下一波修 |
| D-4 | `tasks.md` 8.2 的关键帧时刻（17/33/83/167/217ms）与 motion-spec 的归一化（17/50/133/300/517ms）不一致 | `tasks.md` 8.2 ⟷ `design-notes/motion-spec.md` §3.1 | 只登记，不裁决（不影响本波判定） |

### 8.4 **没有**被本波触碰的东西

- `workbench/**`：**零改动**（`git diff --stat -- workbench/` 为空）。
- `tools/walkthrough/` 下**已有**模块（`probe.py` / `frames.py` / `run.py` / `shots.py` /
  `seed.py` / `g5.py` / `launch.py`）：**零改动**；只**新增**了
  `tools/walkthrough/motion_verify.py`。
- `docs/**`、`.claude/**`、`openspec/` 下除 `reports/MOTION-VERIFICATION.md` 与
  `reports/MOTION-VERIFICATION/` 之外的任何文件：**零改动**。
- 真实池 `pool/dmath.db`：**未写入**（隔离副本 + `LESSONKIT_WB_HOME` 隔离注册表）。

---

## 9. 六条验证命令的原样结果

> 全部在仓库根执行；工作树 = HEAD `9d050949`（`workbench.css` 237 052 字节）。

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
1191 passed in 250.20s (0:04:10)
EXIT=0
```

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
ℹ duration_ms 1168.9166
EXIT=0
```

### ⑥ `node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json`

```
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

> `guard problem-set`（工作区产物验收）**未跑**：它是产物验收，依赖
> `output/` 下的既有产物，且不在干净 checkout 的前置条件里（`AGENTS.md` §6）。

---

## 10. 给所有者的一句话

**动效的代码齐备这件事，现在有了分镜条级别的证据**：
13 条里 **8 条 PASS、4 条 FAIL、1 条 PENDING**；
**终态铁律在契约枚举的项上 13/13 全部一致**。
四个 FAIL 里，**两个是产品缺口**（M-1 灯的收回段没有动画、M-12/横幅在降级档永不退场
—— 后者同时让 M-4 的「退场」在降级档落空）、**一个是判据与实现的漂移**
（M-7 的曲线数字，登记表 D-1）、**一个是规格里写了但没做**（M-10 的日历扩散，
`motion-spec` §2.1 第 19 项列了「日历扩散」这个使用方）。
另有两处**执行器侧漂移**（D-2 / D-3）登记在 §8.3 —— `frames.py` 的 M-9 与 M-4
判据/触发方式落后于现行口径，**本波按规矩没有改它**。
