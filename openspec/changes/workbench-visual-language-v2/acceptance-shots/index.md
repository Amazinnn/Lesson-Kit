# 对照截图索引（第 22 组 · S 系列 · 12 张 before/after 对照）

> **这些数字对应那一轮；后续修复后需要重跑。**
> 本索引里的每一张图、每一个 sha256、每一条差异率，都来自
> **`tmp/wt-run-7/`** 这一次走查的产物。走查期间另有 agent 在并行改产品代码，
> after 侧采的是**当时工作区的那一份** —— 现在重跑，出来的图**不会**和这里一样。
> 人工判读结论见 `../acceptance-manual-review.md`。

---

## 0. 那一轮的代码状态（先看这个，再看图）

| | before 侧 | after 侧 |
|---|---|---|
| **跑的是哪一份代码** | git worktree，基线提交 **`cf9d596d`**（A-49；本分支第一个产品提交 `16d3ff89` 的父提交） | 主仓库**工作区**（**HEAD 在采集期间一直在动** ⇒ 不能只记一个 HEAD 号；见下面「指纹怎么对上哪个提交」那一行） |
| **worktree 路径** | `tmp/wt-run-7/worktree-before/`（**跑完已删**，`run.py` 收尾时 `git worktree remove --force`） | 仓库根目录 |
| **服务端口** | `http://127.0.0.1:3281` | `http://127.0.0.1:3282` |
| **CSS 指纹（served == onDisk）** | **74,935 字节** | **173,948 字节** |
| **指纹怎么对上哪个提交** | `cf9d596d` 的 `workbench.css` 是 73,032 字节 / 1,903 行；**+1,903 = CRLF 换行转换**（本仓 `core.autocrlf=true`，Windows 检出时 LF→CRLF）⇒ 74,935 **正好**是 `cf9d596d` 的检出结果 ⇒ before 侧就是 `cf9d596d` | 173,948 字节**与 `git show 4b4be87f:workbench/server/static/workbench.css` 逐字节相同** ⇒ after 侧的**内容指纹 = 提交 `4b4be87f` 的树**（该提交于 22:42:56 落地，而截图在 22:40–22:42:02 采集 ⇒ 内容当时就已在盘上） |
| **采集时刻** | shots `index.json` 的 `generated_at = 2026-10-22T22:39:53+0800` | `2026-10-22T22:42:02+0800` |
| **工作区** | — | `walk`（隔离注册表里的工作区名，`run.json` 的 `sides.*.scratch`） |

> ⚠️ **HEAD 在采集期间还在动**（reflog：`22:38:50 → 90e76734` → `22:40:36 → aa04a6eb`
> → `22:42:10 回到 90e76734` → `22:42:56 → 16114ca3 / 83d726fb / c00d52ae / 4b4be87f`）。
> 所以「那一轮的代码状态」**不能只写一个 HEAD 号** —— **以 CSS 字节指纹为准**（`4b4be87f`）。
> 现在仓库的 `workbench/server/static/workbench.css` 是 **177,728 字节**（本文件写就时的值，
> 且仍在被并行改动），**已经**不是采集时那一份。

---

## 1. 12 张对照图（每张一行）

**路径相对仓库根目录**（`tmp/` 在 `.gitignore:51` 里 ⇒ **这些图不在版本控制内**，
新克隆的仓库里**点不开**，必须按 §3 重跑）。

| # | 页面 / 状态 | 视口 | 主题 | before 路径 | after 路径 | 该页对应的判据 |
|---|---|---|---|---|---|---|
| S-1 | hub 首页 | 1440×900 | light | `tmp/wt-run-7/evidence/before/shots/S-1-hub-1440.png` | `tmp/wt-run-7/evidence/after/shots/S-1-hub-1440.png` | 3.4-5 空态（插画 + 一句 + 满宽主按钮）· 3.1-3 状态几何编码 —— 也是 S-10 / S-11 的基准页 |
| S-2 | 练习页（未开练） | 1440×900 | light | `tmp/wt-run-7/evidence/before/shots/S-2-practice-1440.png` | `tmp/wt-run-7/evidence/after/shots/S-2-practice-1440.png` | 3.6-2 / 3.6-4 左栏五个导航图标 · 3.1-1 可见焦点环 · 3.1-5 说明性文字数 |
| S-3 | 练习页（进行中） | 1440×900 | light | `tmp/wt-run-7/evidence/before/shots/S-3-practice-in-progress.png` | `tmp/wt-run-7/evidence/after/shots/S-3-practice-in-progress.png` | 3.4-4 错误态与负反馈 · 3.1-5 · 3.6-2 —— **由 `exercise.py` 在脚本化练习途中拍**，不进 `index.json`、**也没有像素比对产物** |
| S-4 | 知识点列表 | 1440×900 | light | `tmp/wt-run-7/evidence/before/shots/S-4-kps-1440.png` | `tmp/wt-run-7/evidence/after/shots/S-4-kps-1440.png` | 3.1-3 状态不只靠颜色 · 3.1-4 状态的文字辅助 · 3.4-4 |
| S-5 | 知识点详情 | 1440×900 | light | `tmp/wt-run-7/evidence/before/shots/S-5-kp-detail-1440.png` | `tmp/wt-run-7/evidence/after/shots/S-5-kp-detail-1440.png` | 3.1-2 正文对比度 · 3.6-2 线宽语言（阅读面插画） |
| S-6 | 记录中心 · 概览 | 1440×900 | light | `tmp/wt-run-7/evidence/before/shots/S-6-records-overview-1440.png` | `tmp/wt-run-7/evidence/after/shots/S-6-records-overview-1440.png` | 3.4-4（**「重日」负荷红点**、逾期红）· 3.2-2 夜纸对比度 |
| S-7 | 记录中心 · 作答明细 | 1440×900 | light | `tmp/wt-run-7/evidence/before/shots/S-7-records-detail-1440.png` | `tmp/wt-run-7/evidence/after/shots/S-7-records-detail-1440.png` | 3.4-4（判定红 / `bad` 轨）· 3.6-2 |
| S-8 | 试卷列表 | 1440×900 | light | `tmp/wt-run-7/evidence/before/shots/S-8-practice-sets-1440.png` | `tmp/wt-run-7/evidence/after/shots/S-8-practice-sets-1440.png` | 3.4-4 · **3.6-2 / 3.6-4（左栏导航图标 + 空态插画）** · 3.4-5 空态三段 |
| S-9 | 设置视图 | 1440×900 | light | `tmp/wt-run-7/evidence/before/shots/S-9-settings-1440.png` | `tmp/wt-run-7/evidence/after/shots/S-9-settings-1440.png` | 3.2-1 台灯转场 · 3.2-5 / 3.2-6 主题偏好 · 3.3-3 / 3.3-4 声音与静音 · 3.4-4（右栏 AI 面板的「查看输出」红） |
| S-10 | 夜纸（hub，同一页） | 1440×900 | **dark** | `tmp/wt-run-7/evidence/before/shots/S-10-night-dark.png` | `tmp/wt-run-7/evidence/after/shots/S-10-night-dark.png` | **3.2-3 圆底降饱和 + 提亮** · 3.2-2 夜纸对比度 · 3.2-4 同一套 SVG 换变量 · 3.6-5 深浅共用同一批 SVG |
| S-11 | 窄屏 1024 | 1024×800 | light | `tmp/wt-run-7/evidence/before/shots/S-11-narrow-1024.png` | `tmp/wt-run-7/evidence/after/shots/S-11-narrow-1024.png` | 3.5-1 四档无横向滚动 · 3.5-2 抽屉 |
| S-11 | 窄屏 768 | 768×900 | light | `tmp/wt-run-7/evidence/before/shots/S-11-narrow-768.png` | `tmp/wt-run-7/evidence/after/shots/S-11-narrow-768.png` | 3.5-1 · 3.5-2 · 3.5-3 背景仍可交互 · 3.4-6 会话列表可滚动 |

**「该页对应的判据」怎么来的**：按 `acceptance.md` §1 的「必看的点」列与 §3 的 38 条清单
**推**出来的对应关系 —— **探针并没有按页绑定判据**（`probe.py` 是一次性在页面上取全部事实）。
所以这张列是**导航用的线索**，不是判据的正式归属。

**⚠️ 一处两侧数据不一致（判读 S-7 时要知道）**：`S-7` 用 `resolve: first_problem_link` 解析题目，
两侧**解析到的题目不同** —— before 是 `?…&problem=dmath-ch06-mq-010`，
after 是 `?…&problem=dmath-ch06-mq-001`。
⇒ **S-7 的 before/after 不是「同一道题」的对照**，像素差异里有**内容差异**这一项，
不能全算到视觉头上。（其余 11 张的 URL 两侧一致。）

### 1.1 没有的一张：`S-12`（空态 · 插画）

| | |
|---|---|
| 判据要求的位置 | `acceptance.md` §1 的 S-12「空态（无试卷 / 无记录 / 无对话）· 1440 · 插画 + 一句 + 满宽主按钮」 |
| 采集清单里的条目 | `tools/walkthrough/shots.py:98-100` —— `requires: 空工作区种子（第二份 seed）——本交付未包含` |
| 本轮结果 | **未产出**。`find tmp/wt-run-7 -iname "*S-12*"` **零命中**；两侧 `shots/` 下各 12 张 PNG 里没有 S-12 |
| 连带影响 | 判据 **`3.6-4`（插画为具象器物）** 指定的证据文件 `shots/S-12-*.png` **不存在**；探针 `3.6-4.json` 的 `data.illustrations` 也是空数组 —— 当页**一张插画都没进 DOM**（空态插画是 `c45eeb6c`（23:38）才接进页面的，**晚于本轮采集 22:42**） |
| 要补 | 补第二份空工作区种子后重跑；或你当场人工签字（见 `../acceptance-manual-review.md` §4.5） |

---

## 2. 指纹表（判定「图还是不是那张图」用）

`tmp/wt-run-7/evidence/{before,after}/shots/index.json` 里记的 sha256（前 16 位）。
**12 对全部不同** ⇒ 每一页的 after 都和 before 不同。

| 文件 | before sha256 | after sha256 | before 字节 | after 字节 |
|---|---|---|---|---|
| `S-1-hub-1440.png` | `4be9eeef2cfc…` | `1623593e679c…` | 17,781 | 18,351 |
| `S-2-practice-1440.png` | `b883d40df066…` | `c18d817a7701…` | 71,119 | 57,967 |
| `S-3-practice-in-progress.png` | `f8c5dcf9a38b…` | `a0cdc9796cf2…` | 67,856 | 89,174 |
| `S-4-kps-1440.png` | `7f6efcd11945…` | `09540d294497…` | 76,157 | 92,924 |
| `S-5-kp-detail-1440.png` | `1e6fbfe8971a…` | `c41225857754…` | 101,388 | 151,662 |
| `S-6-records-overview-1440.png` | `a765bd770f37…` | `153100abdaba…` | 52,634 | 66,190 |
| `S-7-records-detail-1440.png` | `761c97ef9a1b…` | `28125401d326…` | 61,597 | 89,081 |
| `S-8-practice-sets-1440.png` | `c099a417dd0c…` | `a6b4c526aff4…` | 55,826 | 73,288 |
| `S-9-settings-1440.png` | `c12c94edbc42…` | `2ebe5c5b8973…` | 74,991 | 49,797 |
| `S-10-night-dark.png` | `4be9eeef2cfc…` | `6a9614d41853…` | 17,781 | 18,240 |
| `S-11-narrow-1024.png` | `c268af89fbbb…` | `2ce787e6c714…` | 15,831 | 16,331 |
| `S-11-narrow-768.png` | `0fd65d058f33…` | `037d176f062a…` | 15,081 | 15,584 |

**两条值得留意的指纹事实：**

1. **before 的 S-1 与 S-10 完全同一张**（`4be9eeef2cfc…`，17,781 字节）
   ⇒ 改造前**没有夜纸主题**，`color_scheme=dark` 不起作用。
   after 侧两者才分叉（`1623593e…` vs `6a9614d4…`）⇒ 夜纸主题**这一轮才生效**。
2. **before 的 S-10 与 S-1 相同，after 的 S-10 画面里仍看不到导航图标**
   —— S-10 拍的 URL 是 `/`（hub），画面上只有「工作区选择卡」。
   ⇒ **S-10 不能当「图标圆底」的证据**（`3.2-3` 要看的圆底在左栏，hub 页没有左栏）。

---

## 3. 怎么把这一轮重新跑出来

```bash
cd "D:/Projects/Academic Workflow/lesson-kit"

# 全量走查（before + after + diff），产物落在 tmp/wt-run-7/
python tools/walkthrough/run.py --out tmp/wt-run-7

# 只跑某几条判据
python tools/walkthrough/run.py --out tmp/wt-run-7 --only 3.2-3 3.4-4 3.6-2 3.6-4
python tools/walkthrough/run.py --out tmp/wt-run-7 --only S-1 S-8 S-10

# 只跑 after 侧（自检；不建 before worktree）
python tools/walkthrough/run.py --out tmp/wt-run-7 --skip-before
```

**它做了什么**（`tools/walkthrough/README.md`）：

1. `git worktree add --detach tmp/wt-run-7/worktree-before cf9d596d` —— 取 before 基线，
   并把当前 checkout 的 `figures/` / `output/` 拷进去（worktree 里没有这些，且不在 git 里）。
2. 两边各起一个隔离服务（`tools/walkthrough/launch.py`）：独立池副本 + 独立注册表 + 独立端口，
   before `3281` / after `3282`。
3. 逐侧跑采集器：探针（38 条交互清单 + G-7/G-8）、脚本化练习（E0…E9 + S-3）、池导出、
   动效分镜条、图谱页九步冻结（G-5）、对照截图（`tools/walkthrough/shots.py`）。
4. diff 段：请求序列 diff、池 diff、探针 diff、G-5 三口径比对、**截图像素比对 + 差值图**。

**采集的一致性闸门**（`tools/walkthrough/shots.py` 的 `CONSISTENCY`，两侧都钉死）：

| 项 | 值 |
|---|---|
| `device_scale_factor` | 1 |
| `color_scheme` | light（`S-10` 单独用 dark） |
| `reduced_motion` | no-preference |
| `locale` / `timezone_id` | zh-CN / Asia/Shanghai |
| 浏览器参数 | `--force-color-profile=srgb` `--disable-lcd-text` |
| 字体闸门 | `document.fonts.ready + document.fonts.status === 'loaded'` |
| 滚动闸门 | 锚点 `scrollIntoView({block:'start'})` |
| 动效闸门 | 采集时**没有正在跑的有限动画** |

**每个 S 编号的锚点与焦点**（`tools/walkthrough/shots.py` 的 `SHOT_SPECS`）——
重跑后要确认**锚点还是找得到**（`anchor_found`）：

| S | URL 路径 | 锚点 | 必看的点 |
|---|---|---|---|
| S-1 | `/` | `.workspace-card` | 最近使用置顶区、卡片信息层级 |
| S-2 | `/w/{ws}/practice` | `#paper-setup` | 顶栏三段式、题面纸、题号导航 |
| S-3 | `/w/{ws}/practice` | `#paper-work` | 题面独立纸、24px 题号、解析同级纸 |
| S-4 | `/w/{ws}/kps` | `#middle-page` | 分组卡片、彩色圆点状态 |
| S-5 | `/w/{ws}/kp`（第一个 KP 链接） | `#middle-page` | 衬线阅读面 + 单侧结构线 |
| S-6 | `/w/{ws}/records` | `#middle-page` | 仪表盘卡片、热力日历 |
| S-7 | `/w/{ws}/records`（第一个题目链接） | `#middle-page` | 圆角卡片流（不得出现表格） |
| S-8 | `/w/{ws}/practice-sets` | `#middle-page` | 卡片网格、状态圆点、**无 5px 黄带** |
| S-9 | `/w/{ws}/settings` | `#middle-page` | 主题 / 阅读字面 / 动效 / 声音 |
| S-10 | `/`（`color_scheme=dark`） | `.workspace-card` | 夜纸值集、圆底降饱和提亮、插画反相 |
| S-11 | `/` | `.workspace-card` | 三栏折叠、右栏抽屉 |
| S-12 | `/w/{ws}/practice-sets` | `#middle-page` | 插画 + 一句 + 满宽主按钮 —— **需要第二份种子，本轮未采** |

> ⚠️ **重跑 ≠ 同样的结果**：after 侧采的是**当时的工作区**，现在产品代码已经变了；
> 跑出来的图会与本索引的 sha256 **对不上**，那是**预期的**。

---

## 4. 像素比对产物（11 对；S-3 没有）

每对三件套：并排图 `X.png` + 差值图 `X-delta.png` + 判定 `X.json`
（路径：`tmp/wt-run-7/evidence/diff/shots/`）。

| S | 判定 | 差异像素 `ae` | 差异率 `ratio` | 阈值 | 产物 |
|---|---|---|---|---|---|
| S-1 | FAIL | 1,296,000 | 1.000000 | 0.005 | `diff/shots/S-1-hub-1440{,-delta}.png` + `.json` |
| S-2 | FAIL | 1,149,091 | 0.886644 | 0.005 | `diff/shots/S-2-practice-1440{,-delta}.png` + `.json` |
| S-4 | FAIL | 1,047,672 | 0.808389 | 0.005 | `diff/shots/S-4-kps-1440{,-delta}.png` + `.json` |
| S-5 | FAIL | 1,207,289 | 0.931550 | 0.005 | `diff/shots/S-5-kp-detail-1440{,-delta}.png` + `.json` |
| S-6 | FAIL | 1,277,879 | 0.986018 | 0.005 | `diff/shots/S-6-records-overview-1440{,-delta}.png` + `.json` |
| S-7 | FAIL | 1,219,801 | 0.941204 | 0.005 | `diff/shots/S-7-records-detail-1440{,-delta}.png` + `.json` |
| S-8 | FAIL | 1,205,964 | 0.930528 | 0.005 | `diff/shots/S-8-practice-sets-1440{,-delta}.png` + `.json` |
| S-9 | FAIL | 1,295,151 | 0.999345 | 0.005 | `diff/shots/S-9-settings-1440{,-delta}.png` + `.json` |
| S-10 | FAIL | 1,296,000 | 1.000000 | 0.005 | `diff/shots/S-10-night-dark{,-delta}.png` + `.json` |
| S-11 (1024) | FAIL | 819,200 | 1.000000 | 0.005 | `diff/shots/S-11-narrow-1024{,-delta}.png` + `.json` |
| S-11 (768) | FAIL | 691,200 | 1.000000 | 0.005 | `diff/shots/S-11-narrow-768{,-delta}.png` + `.json` |
| **S-3** | — | — | — | — | **无产物**（由 `exercise.py` 途中拍，不进比对） |

### 4.1 ⚠️ 这 11 个 FAIL **不是回归信号**

`decisions.md:2244` 的 **A-85** 已裁决：

> **S-1…S-12 的「整页像素比」在本变更中不作为机械门禁** —— 基线取的是整个变更之前的
> `cf9d596d`，而本变更**本来就是整版视觉重做**；阈值 `ratio > 0.005` 是给**局部改动**写的。
> ⇒ 整页的 S-* 改为**人工判读 + 亮/暗双主题对照图**（走查已产出这些图）。
> ⚠️ **不许**为了让 S-* 变绿而调大阈值或改基线。

**⇒ 这个索引里的图就是给人看的那份材料**，不是给机器过阈值的。
另注：A-85 第 3 条说 **S-3 与 S-12 仍可用机械判据**（比的是局部状态）——
但本轮 S-3 没有产出比对件、S-12 整张缺失，**这两条本轮都没走到**。

---

## 5. 本索引引用的路径（85/85 已 `ls` 核过，零缺失）

| 类别 | 路径 |
|---|---|
| 12 张 before | `tmp/wt-run-7/evidence/before/shots/*.png`（12 个文件，**已逐个核过**） |
| 12 张 after | `tmp/wt-run-7/evidence/after/shots/*.png`（12 个文件，**已逐个核过**） |
| 截图元数据 | `tmp/wt-run-7/evidence/{before,after}/shots/index.json`（各含 `sha256` / `bytes` / `viewport` / `color_scheme` / `anchor_found` / `fonts_status` / `running_animations`） |
| 像素比对产物 | `tmp/wt-run-7/evidence/diff/shots/*.png` + `*.json`（各 11 组）+ `index.json` |
| 运行元数据 | `tmp/wt-run-7/run.json`（`beforeCommit` / `sides.*.css` / `summary` / `unresolved`） |
| 走查报告 | `tmp/wt-run-7/evidence/diff/report.json`、`tmp/wt-run-7/evidence/diff/checklist.json` |
| 采集器（可读可改，但本任务没改） | `tools/walkthrough/{run,launch,shots,probe,exercise,frames,g5,dbexport,recorder}.py`、`tools/walkthrough/README.md` |
| 判据原文 | `openspec/changes/workbench-visual-language-v2/acceptance.md`（§1 截图清单、§3 交互清单）、`design-notes/walkthrough-harness.md`（§5.1/§5.6/§7.5） |
| 裁决 | `openspec/changes/workbench-visual-language-v2/decisions.md`（A-49 基线、A-85 像素比裁决） |

---

## 6. 关联

- **人工判读一页纸**（含这 12 张图各自对应的四条 SEMI / MANUAL 判据）：
  `openspec/changes/workbench-visual-language-v2/acceptance-manual-review.md`
- 本索引**不替人签字**。四条判据的签字位在 `../acceptance-manual-review.md` §5.1「需要你确认」。
