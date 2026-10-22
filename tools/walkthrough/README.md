# 走查执行器（tools/walkthrough）

**规格**：`openspec/changes/workbench-visual-language-v2/design-notes/walkthrough-harness.md`
——本目录是它的实现，**按它写，不另发明一套**。

执行器是**旁挂**的：它不进入 Domain / Data 层，不新增任何持久化写入路径，
不改 `workbench/`、`pool/`、`pipeline/`、`lessonkit.py` 的任何字节
（红线 X-1…X-12）。

---

## 0. 本目录现在有什么

| 文件 | 职责 | 状态 |
|---|---|---|
| `launch.py` | 隔离环境（池副本 + 隔离注册表 + 独立端口）+ 服务启动 + 隔离硬断言 | ✅ 已实现 |
| `recorder.py` | 进程内请求序列捕获 + 规范化 + diff + **可判定报告** | ✅ 已实现 |
| `shots.py` | 对照截图采集（§5.6 清单）+ 像素判定（§5.4 / §5.7 两套判据） | ✅ 已实现 |
| `exercise.py` | 脚本化练习 E0…E9：喂 G-1 的请求序列，并拍 S-3「练习进行中」 | ✅ 已实现 |
| `dbexport.py` | 持久化 / 学习投影 / 到期与薄弱 / schema 导出与比对（G-2 / G-3 / G-4 / G-6） | ✅ 已实现 |
| `frames.py` | M-1…M-10 分镜条 + reduced-motion 对照帧（终态逐项比对） | ✅ 已实现 |
| `probe.py` | 浏览器探针：G-7 / G-8 + §3 的 38 条交互清单 | ✅ 已实现 |
| `g5.py` | G-5 图谱页九步冻结采集 + 三口径比对（A-48 / A-65） | ✅ 已实现 |
| `run.py` | before / after / diff 三段编排（`--only` 可只跑选定判据） | ✅ 已实现 |
| `README.md` | 本文 | ✅ |

**一键跑完整走查**：

```bash
cd "D:/Projects/Academic Workflow/lesson-kit"
python tools/walkthrough/run.py --out tmp/wt-run
# 只跑某几条判据：
python tools/walkthrough/run.py --out tmp/wt-run --only G-1 G-5
python tools/walkthrough/run.py --out tmp/wt-run --only M-7
```

`run.py` 做的事：取「改造前」基线 → 起两侧服务 → 逐侧跑采集器 → 三段 diff → 出报告。

---

## 1. 两条已定的口径（照做，不再问）

### 1.1 A-49 ——「改造前」基线 = `cf9d596d` 的 git worktree

`run.py` 用 `git worktree add --detach <scratch>/worktree-before cf9d596d`
（本分支第一个产品提交 `16d3ff89` 的父提交）取基线，**以该 worktree 为根**起服务。

**不使用** `tmp/frontend-audit/00-baseline-*.png`：那些图的视口
（2040×1230 / 1555×1114）与 DPR（1.5）不可控，**未纳入像素判定**。

worktree 里没有 `pool/`、`output/`、`.lessonkit/figures/`（都不在 git 里），
所以 `run.py` 把当前 checkout 的 figures / output 复制进去 —— 否则两侧的
内容不同，截图会因为与本次改造无关的原因而不同。

### 1.2 A-48 / A-65 —— G-5 的三口径并列

| 口径 | 比对区域 | 通过标准 |
|---|---|---|
| **R-1** | 整页，**排除**左栏（`x < 280`）与顶栏（`y < 52`） | 差异像素 = 0 |
| **R-2** | `.graph-workspace` 的裁剪矩形 | 差异像素 = 0，**不接受任何掩膜** |
| **R-3** | 画布矩形 + 三栏各一个纯色采样点 | 画布差异 = 0，采样点两侧同色 |

- **R-3 的左栏采样点固定在左栏纸面区域内（顶部）** —— 那里改造前后都是
  `--surface-sunken`；**采样坐标写进产物**（`diff/g5/ae.json` 的
  `scopes.R-3.samples[].point`），before 侧按**同一坐标**采样，坐标不随内容漂移。
- 报告里照实写一条：**「左栏纸面以下的底色由 `--surface-sunken` 变为
  `--surface-base` —— 属 15.3 的既定改造，非图谱误伤」**。
  ⚠️ **这条不许把 R-3 判成 FAIL** —— 它在规定口径（纸面内）下应当 PASS；
  但它必须出现在报告里。
- 三口径**全跑并列**；`PENDING ≠ PASS`。

---

## 2. 判据现在能跑到什么程度（**不藏着**）

| 判据 | 能跑？ | 说明 |
|---|---|---|
| **G-1** 请求序列 | ✅ 能跑 | `exercise.py` 驱动真实 UI 走完建卷→开始→逐题提交→自评→交卷→取答卷；两侧序列逐条 diff |
| **G-2** 持久化写入 | ✅ 能跑 | `dbexport.py` 导出 `problem_attempts` / `feedback_events` / `practice_runs` 三张表并比对 |
| **G-3** 学习投影 | ✅ 能跑 | `learning_current_state` / `review_schedule` / `problem_progress` / `learner_signals` |
| **G-4** 到期与薄弱 | ✅ 能跑 | 到期列表的日期部分、薄弱列表逐条比对 |
| **G-5** 图谱未被误伤 | ✅ 能跑 | 三口径并列（A-48 / A-65），九步冻结协议照抄 `graph-isolation.md` §6.5 |
| **G-6** schema | ✅ 能跑 | schema 比对 + 表行数比对 |
| **G-7** 装饰层不拦交互 | ✅ 能跑 | 主题转场进行中用 `elementFromPoint` 取行为证据（不是 CSS 扫描） |
| **G-8** 焦点顺序 | ✅ 能跑 | Tab 遍历录**语义**序列（role + 可访问名，不用 id）；新增的设置入口 / 主题开关记 `ADDED-EXPECTED` |
| **S-1…S-12** 对照截图 | ✅ 能跑 | `shots.py`；S-3 由 `exercise.py` 在练习进行中拍 |
| **M-1…M-10** 分镜条 | ✅ 能跑 | `frames.py`；每条另出降级对照帧，**终态逐项脚本化比对**（不目视） |
| **§3 的 38 条交互清单** | ✅ 能跑 | `probe.py`；**只有 AUTO 自动判定**，SEMI / MANUAL 一律 `PENDING` + 证据 + 阅读指引 |

### 2.1 跑不出来的部分（**记 PENDING，不记 PASS**）

| 项 | 为什么 | 证据里的记法 |
|---|---|---|
| **3.3-5** 无音效时视觉仍完整 | 需要「开静音 / 关静音」两轮分镜条逐帧比对 | 由 `frames.py` 产帧，探针侧只登记 |
| **M-3** 里程碑档庆祝 | 需要一次**里程碑轮次**（全对或章节首次完成） | `frames/M-3.json` → `PENDING` |
| **M-11…M-13** | 本设计只列 M-1…M-10 的帧表 | 不在本轮范围 |
| **3.7-2** 98+ 条记录滚动 | 池里只有 3 条 `problem_attempts`，**不足 98 条** | `probe/3.7-2.json` → `PENDING` + 实际条数 |
| **3.4-5** 空态（若触达不到） | 空态要「无试卷」的数据状态；`run.py` 已让静态探针**先于**练习跑 | 触达不到就 `PENDING` |
| **3.2-3 / 3.4-4 / 3.6-2 / 3.6-4** | 分别是 SEMI / MANUAL：机器只能给数值与证据 | 一律 `PENDING` + 阅读指引（§7.5.1） |

### 2.2 判定纪律

- 只有 **AUTO** 条目能自动写 `PASS` / `FAIL`；SEMI / MANUAL 一律 `PENDING`。
- 改造前**没有对照物**的 11 条（3.2-1 / 3.2-2 / 3.2-4 / 3.3-1 / 3.3-2 /
  3.3-3 / 3.3-4 / 3.4-3 / 3.6-1 / 3.6-3 / 3.6-5 / 3.7-3）在 before 侧记 `N/A`
  （**不是 PASS**），after 侧照常判定。
- 缺证据 = `PENDING` / `BLOCKED`，**永远不是通过**。

---

## 3. 前置条件

| 依赖 | 本机实测 | 不满足时 |
|---|---|---|
| Python | 3.14.3 | — |
| `playwright`（Python 包） | `D:\Python\Lib\site-packages\playwright` | `pip install playwright` |
| chromium 内核 | **已装**：`chromium-1223` / `chromium_headless_shell-1223` | `python -m playwright install chromium`（需要联网） |
| `PIL` | 12.1.1 | `pip install pillow` |
| `curl` | Git Bash 自带 | 用 `python -c` 取字节数代替 |

**Chromium 内核自检**：

```bash
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True); print(b.version); b.close()"
```

---

## 4. ⚠️ 必须知道的两件事

### 4.1 `import workbench` 会解析到 pip 安装的旧快照

本机 `pip show lesson-kit` → **0.1.0 已安装**（editable install），
它指向 **`.worktrees/runtime-main`**：

```
$ cd /tmp && python -c "import workbench; print(workbench.__file__)"
D:\Projects\Academic Workflow\lesson-kit\.worktrees\runtime-main\workbench\__init__.py
```

后果：**不报错**，但服务会发旧版本的 CSS/JS（新 token 全部取不到值）。

`launch.py` 对此有三重防线：

1. 把仓库根插到 `sys.path[0]`，并 `os.chdir(repo_root)`；
2. 启动后断言 `workbench.__file__` 在仓库根之内，否则抛 `IsolationBreach`；
3. **字节数比对**（`run.py` 每轮自动做一次；手工确认用这两条）：

   ```bash
   curl -s http://127.0.0.1:<端口>/static/workbench.css | wc -c
   wc -c workbench/server/static/workbench.css
   ```

   **两个数必须相等**；不等就换端口重启。
   （数字随 `workbench.css` 的改动而变，以**当场比对**为准。）

### 4.2 端口

`3081` 是用户自己的默认工作台端口，**执行器拒绝使用**（`launch.py` 与
`run.py` 都直接退出）。`run.py` 默认 before=`3281` / after=`3282`。

---

## 5. 怎么跑（分步）

### 5.1 起一个隔离服务（带请求捕获器）

```bash
cd "D:/Projects/Academic Workflow/lesson-kit"
python tools/walkthrough/launch.py \
    --scratch tmp/walkthrough-scratch \
    --port 3191 \
    --side after \
    --out tmp/walkthrough-scratch/evidence/after/requests.jsonl
```

它会：

1. 把仓库根放到 `sys.path[0]`、切到仓库根为 cwd、断言 `workbench` 来自仓库；
2. 设 `LESSONKIT_WB_HOME=<scratch>/registry`（**隔离注册表**）；
3. 把 `pool/<course>.db` **按字节复制**到 `<scratch>/ws-<name>/pool/`（**池副本**），
   并复制 `.lessonkit/figures/` 与 `output/`；
4. 在隔离注册表里注册工作区（跳过 bootstrap，副本池不会被重建）；
5. 跑隔离硬断言 **A1/A2/A3**，任何一条不成立 → **抛异常终止**；
6. 装上请求捕获器（monkeypatch `WorkbenchHandler._dispatch` 与
   `BaseHTTPRequestHandler.send_response`），然后 `app.serve(port)`。

只建环境、只做断言、不起服务：

```bash
python tools/walkthrough/launch.py --check-only --scratch tmp/walkthrough-scratch --port 3191
```

不装捕获器（对照跑，证明捕获器不改变业务）：

```bash
WALKTHROUGH_RECORD=0 python tools/walkthrough/launch.py ...   # 或 --no-record
```

### 5.2 脚本化练习（G-1 + S-3）

```bash
python tools/walkthrough/exercise.py \
    --base-url http://127.0.0.1:3191 --ws walk --out <evidence>/after
```

产出 `exercise/summary.json`（步骤表 + 观测到的写序列）、`exercise/due.json`、
`exercise/weak.json` 与 `shots/S-3-practice-in-progress.png`。

### 5.3 池导出与比对（G-2 / G-3 / G-4 / G-6）

```bash
python tools/walkthrough/dbexport.py export --pool <池副本> --out <evidence>/after/db
python tools/walkthrough/dbexport.py diff \
    --before <before>/db --after <after>/db \
    --due-before <before>/exercise/due.json --due-after <after>/exercise/due.json \
    --weak-before <before>/exercise/weak.json --weak-after <after>/exercise/weak.json \
    --out <evidence>/diff
```

### 5.4 浏览器探针（G-7 / G-8 + 38 条清单）

```bash
python tools/walkthrough/probe.py static --base-url http://127.0.0.1:3191 \
    --ws walk --out <evidence>/after --side after
python tools/walkthrough/probe.py flow   --base-url http://127.0.0.1:3191 \
    --ws walk --out <evidence>/after --side after
python tools/walkthrough/probe.py diff --before <before> --after <after> --out <diff>
```

三遍的原因：静态项要在**练习之前**跑（3.4-5 的空态要「没有试卷」的数据状态），
音效项要一次真实练习（flow），3.2-6 的「重启后仍保持」要服务重启之后再问一次
（persist）。

### 5.5 动效分镜条（M-1…M-10）

```bash
python tools/walkthrough/frames.py --base-url http://127.0.0.1:3191 \
    --ws walk --out <evidence>/diff --only M-1,M-2
```

### 5.6 G-5 图谱页

```bash
python tools/walkthrough/g5.py capture --base-url http://127.0.0.1:3191 \
    --ws walk --out <evidence>/after/g5 --side after
python tools/walkthrough/g5.py compare --before <before>/g5 --after <after>/g5 \
    --out <evidence>/diff/g5
```

### 5.7 采对照截图 / 比对两侧

```bash
python tools/walkthrough/shots.py capture \
    --base-url http://127.0.0.1:3191 --ws walk \
    --out tmp/walkthrough-scratch/evidence/after/shots \
    --only S-1 S-2

python tools/walkthrough/shots.py diff \
    --before <before>/shots --after <after>/shots --out <evidence>/diff/shots
```

每次截图**钉死**的一致性要素（§5.2）：

| 变量 | 取值 |
|---|---|
| 视口 | 1440×900 / 1024×800 / 768×900 / 1280×900 |
| DPR | `device_scale_factor=1` |
| 颜色方案 | `color_scheme=light`（夜纸条目单独跑 `dark`） |
| 动效偏好 | `reduced_motion=no-preference` |
| 语言/时区 | `locale=zh-CN`、`timezone_id=Asia/Shanghai` |
| 字体渲染 | `--force-color-profile=srgb --disable-lcd-text` + `document.fonts.ready` |
| 滚动位置 | **元素锚点** `scrollIntoView({block:'start'})`，锚点 `top` 记进 `index.json` |
| 动画 | 截图前断言**没有正在跑的有限时长动画** |

**两套判据，不许混用**（§8.1 R-31）：

| 函数 | 判据 | 用于 |
|---|---|---|
| `pixel_diff_for_shots()` | `ratio == 0` → PASS；`0 < ratio ≤ 0.005` → **PENDING**（仅抗锯齿差异，人工判读）；`> 0.005` → FAIL | S-1…S-12 |
| `pixel_diff_for_g5()` | `ae == 0` → PASS；否则 FAIL（**无容差带**） | G-5（否定式断言） |

### 5.8 出报告

```bash
python tools/walkthrough/recorder.py --evidence <evidence>
```

产出 `<evidence>/diff/report.md` + `report.json`：

- **底线守卫 G-1…G-8** 逐条给 `PASS / FAIL / PENDING / BLOCKED` + 证据路径；
- **没有证据的判据一律 `BLOCKED`（无法判定），绝不记 PASS**；
- 整体结论：`PASS` / `PASS_WITH_PENDING` / `FAIL` / `INCOMPLETE`
  （`INCOMPLETE` = 有判据没有证据；这是对 §7.6.3 的**显式扩展**，
  否则「7 条没采」会被算成「通过」）；
- `--purpose selfcheck` 会在报告顶部加一条横幅：两侧证据来自同一次运行，
  **不是**验收结论。

---

## 6. 产物在哪

```
$scratch/
├── registry/                       # 隔离注册表（workspaces.json / daemon.json）
├── ws-<name>/                      # 隔离工作区
│   ├── pool/<course>.db            # 池副本
│   ├── .lessonkit/{figures,explain,jobs}/
│   └── output/                     # 图谱工件副本
└── evidence/
    ├── <before|after>/
    │   ├── requests.jsonl          # 原始请求记录（含 GET）
    │   ├── exercise/               # summary.json / due.json / weak.json
    │   ├── db/                     # db.<table>.json / db.schema.json / db.row_counts.json
    │   ├── probe/                  # checklist.json + <id>.json + g7.json + g8.json
    │   ├── g5/                     # graph-<side>.png + graph-<side>.json
    │   ├── shots/                  # S-*.png + index.json（视口/锚点/字体/动画）
    │   └── frames/                 # M-x/ 分镜帧 + M-x.json
    └── diff/
        ├── requests.norm.json      # 规范化签名
        ├── requests.diff.json/.md  # 请求序列 diff（G-1）
        ├── db.diff.json            # 池 / 投影 / schema 比对（G-2…G-4、G-6）
        ├── checklist.json          # 合并后的 38 条判定
        ├── shots/                  # 并排图 + 差异图 + 每条判定
        ├── frames/                 # M-x.json + M-x-strip.png
        ├── g5/ae.json              # G-5 三口径 AE + 采样坐标
        └── report.md / report.json
```

**证据不进 git**：`tmp/` 已在 `.gitignore` 里（X-6）。

---

## 7. 隔离硬断言（§1.6 / §8.2）

| # | 断言 | 落点 |
|---|---|---|
| A1 | `LESSONKIT_WB_HOME` ≠ 真实注册表，且在 `$SCRATCH` 之下 | `launch.assert_isolated` |
| A2 | 隔离注册表里每条 workspace 的 `path` / `db` 都在 `$SCRATCH` 之下 | 同上 |
| A3 | 副本池与真实池**不是同一个文件**（`samefile` 为假、inode 不同） | 同上 + 复制时断言 |
| A4 | 真实池 + 真实注册表的 **sha256 + size + mtime** 整轮前后一致 | `launch.snapshot_paths` |
| A5 | 服务起来后 `GET /api/hub/workspaces` 返回的 path 在 `$SCRATCH` 下 | 手工/后续脚本 |

A1–A3 在 `init` 之后立即跑；**任何一条不成立 → 抛异常终止，不降级为警告**。

---

## 8. 请求记录格式（§2.2）

```jsonc
{
  "seq": 40,                      // 到达顺序（线程安全计数器）—— 序列以此为准
  "t_ms": 8156.222,               // 相对服务启动
  "method": "POST",
  "raw_path": "/api/w/walk/chapter",
  "route": "POST /api/w/{name}/chapter",   // 服务自己的路由模板（不是猜的正则）
  "query": {},                    // 只留键，值默认丢弃
  "body_keys": ["chapter"],       // 顶层键，排序
  "body_shape": {"chapter": "scalar"},
  "body_subkeys": {},             // 对象数组的子键并集
  "status": 200,                  // 从 send_response 取（五条出响应路径全覆盖）
  "phase": "measure",
  "group": "exercise"
}
```

- JSONL 的**行序是完成顺序**（并发请求会乱），**序列以 `seq` 为准**
  （`recorder.ordered()`）。
- `body_raw` 默认**不落盘**；需要时 `WALKTHROUGH_KEEP_BODY=1`。
- 记录失败绝不影响业务响应：捕获器内部全 try/except（§2.1）。
- 控制端点 `GET /__walkthrough__/events`、`POST /__walkthrough__/phase`
  在产品路由**之前**被拦下，不进产品代码。

---

## 9. 已知限制（不藏着）

1. **GET 差异（L2）不自动判 FAIL**：按 §2.4(e)，写请求序列是阻断层，
   GET 差异单独成表，**要人签字**。
2. **未命中路由的请求**（页面路由、静态资源）记为
   `<UNMATCHED> <归一化路径>`：它们出现在原始 JSONL 里，但被 §2.4(e)
   排除在主 diff 之外。
3. **M-4 / M-5 / M-6 的触发是「组件级」**：`frames.py` 调产品自己的
   `window.lkStreak.create` 组件（真 CSS、真组件代码），而不是整条 UI 路径
   —— 整条路径要先让 Agent 组卷才走得到。证据里写明了这一点。
4. **M-9 的骨架屏用「拦脚本」采**：把 `paper-practice.js` 挡住，让加载标记
   留在页面上再采帧；这是采集手法，不是产品改动。
5. **并存基线不可用于像素判定**：`tmp/frontend-audit/00-baseline-*.png`
   的视口（2040×1230 / 1555×1114）、DPR（1.5）与采集时机都不可控，
   **未纳入像素判定**（§5.5）。真正的「改造前」基线由 `run.py` 在
   `cf9d596d` 的 worktree 上跑出来。
6. **池不是版本化资产**：`pool/` 在 `.gitignore` 里，所以「改造前」那一侧
   用的是**当前**池的副本；两侧拿到的是同一份内容，对比对仍然成立。
