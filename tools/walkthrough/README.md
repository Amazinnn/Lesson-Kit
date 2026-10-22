# 走查执行器（tools/walkthrough）

**规格**：`openspec/changes/workbench-visual-language-v2/design-notes/walkthrough-harness.md`
——本目录是它的实现，**按它写，不另发明一套**。

执行器是**旁挂**的：它不进入 Domain / Data 层，不新增任何持久化写入路径，
不改 `workbench/`、`pool/`、`pipeline/`、`lessonkit.py` 的任何字节
（红线 X-1…X-12）。

---

## 0. 本目录现在有什么、没有什么

| 文件 | 职责 | 状态 |
|---|---|---|
| `launch.py` | 隔离环境（池副本 + 隔离注册表 + 独立端口）+ 服务启动 + 隔离硬断言 | ✅ 已实现 |
| `recorder.py` | 进程内请求序列捕获 + 规范化 + diff + **可判定报告** | ✅ 已实现 |
| `shots.py` | 对照截图采集（§5.6 清单）+ 像素判定（§5.4 / §5.7 两套判据） | ✅ 已实现 |
| `README.md` | 本文 | ✅ |

**尚未实现**（设计件里有、但本轮不交付；报告里一律记 `BLOCKED`，绝不记 PASS）：

| 缺什么 | 影响到的判据 | 设计件出处 |
|---|---|---|
| 脚本化练习驱动器（`exercise.py`） | G-1 的完整序列（建卷→开始→逐题提交→自评→交卷→取答卷）、S-3「练习进行中」 | §3 |
| 持久化/学习投影导出（`dbexport.py`） | G-2、G-3、G-4、G-6 | §4 |
| 关键帧采集（`frames.py`） | M-1…M-10 | §6 |
| 浏览器探针（`probe.py`） | G-7、G-8、§3 的 38 条交互清单 | §7.5 |
| G-5 图谱页九步冻结采集 | G-5 | `design-notes/graph-isolation.md` §6.3–§6.8 |
| 总编排（`run.py`） | before/after/diff 三段一键跑 | §7.4 |

> **G-5 的采集协议刻意没有在这里实现**：它有自己的冻结流程与「静止签名」，
> 在 `design-notes/graph-isolation.md` §6.3–§6.8，本目录**照抄**即可，
> 不得另造（§5.7、W-17）。`shots.py` 只提供 **AE 判定**（`pixel_diff_for_g5`，
> `ae == 0` 才 PASS，**无容差带**）。

---

## 1. 前置条件

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

## 2. ⚠️ 必须知道的两件事

### 2.1 `import workbench` 会解析到 pip 安装的旧快照

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
3. **字节数比对**（启动后手工确认一次）：

   ```bash
   curl -s http://127.0.0.1:<端口>/static/workbench.css | wc -c
   wc -c workbench/server/static/workbench.css
   ```

   **两个数必须相等**；不等就换端口重启。
   （数字随 `workbench.css` 的改动而变，以**当场比对**为准；本轮实测两数相等。）

### 2.2 端口

`3081` 是用户自己的默认工作台端口，**执行器拒绝使用**（`launch.py` 直接退出）。
默认 `3091`，冒烟用 `3191`。

---

## 3. 怎么跑

### 3.1 起一个隔离服务（带请求捕获器）

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

### 3.2 采对照截图

```bash
python tools/walkthrough/shots.py capture \
    --base-url http://127.0.0.1:3191 --ws walk \
    --out tmp/walkthrough-scratch/evidence/after/shots \
    --only S-1 S-2
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

### 3.3 比对两侧

```bash
python tools/walkthrough/shots.py diff \
    --before <before>/shots --after <after>/shots --out <evidence>/diff/shots
```

产出：每张图的并排对照图、`*-delta.png` 差异图、每条目的判定 JSON。

**两套判据，不许混用**（§8.1 R-31）：

| 函数 | 判据 | 用于 |
|---|---|---|
| `pixel_diff_for_shots()` | `ratio == 0` → PASS；`0 < ratio ≤ 0.005` → **PENDING**（仅抗锯齿差异，人工判读）；`> 0.005` → FAIL | S-1…S-12 |
| `pixel_diff_for_g5()` | `ae == 0` → PASS；否则 FAIL（**无容差带**） | G-5（否定式断言） |

### 3.4 出报告

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

## 4. 产物在哪

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
    │   └── shots/                  # S-*.png + index.json（视口/锚点/字体/动画）
    └── diff/
        ├── requests.norm.json      # 规范化签名
        ├── requests.diff.json/.md  # 请求序列 diff（G-1）
        ├── shots/                  # 并排图 + 差异图 + 每条判定
        ├── g5/ae.json              # G-5 三口径 AE（待采集器）
        └── report.md / report.json
```

**证据不进 git**：`tmp/` 已在 `.gitignore` 里（X-6）。

---

## 5. 隔离硬断言（§1.6 / §8.2）

| # | 断言 | 落点 |
|---|---|---|
| A1 | `LESSONKIT_WB_HOME` ≠ 真实注册表，且在 `$SCRATCH` 之下 | `launch.assert_isolated` |
| A2 | 隔离注册表里每条 workspace 的 `path` / `db` 都在 `$SCRATCH` 之下 | 同上 |
| A3 | 副本池与真实池**不是同一个文件**（`samefile` 为假、inode 不同） | 同上 + 复制时断言 |
| A4 | 真实池 + 真实注册表的 **sha256 + size + mtime** 整轮前后一致 | `launch.snapshot_paths` |
| A5 | 服务起来后 `GET /api/hub/workspaces` 返回的 path 在 `$SCRATCH` 下 | 手工/后续脚本 |

A1–A3 在 `init` 之后立即跑；**任何一条不成立 → 抛异常终止，不降级为警告**。

---

## 6. 请求记录格式（§2.2）

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

## 7. 已知限制（不藏着）

1. **G-1 现在只能覆盖到「真实 UI 发出什么」**：没有 `exercise.py`，
   完整练习序列（建卷→交卷）跑不出来；当前只能靠真实 UI 的写请求
   （例如章节透镜的 `POST /api/w/{name}/chapter`）。
2. **GET 差异（L2）不自动判 FAIL**：按 §2.4(e)，写请求序列是阻断层，
   GET 差异单独成表，**要人签字**。
3. **未命中路由的请求**（页面路由、静态资源）记为
   `<UNMATCHED> <归一化路径>`：它们出现在原始 JSONL 里，但被 §2.4(e)
   排除在主 diff 之外。
4. **`S-3`、`S-12` 采不到**：分别需要脚本化练习与空工作区种子；
   `index.json` 里记为 `skipped` 并写明原因。
5. **并存基线不可用于像素判定**：`tmp/frontend-audit/00-baseline-*.png`
   的视口（2040×1230 / 1555×1114）、DPR（1.5）与采集时机都不可控，
   **未纳入像素判定**（§5.5）。真正的「改造前」基线必须由本采集器
   在 worktree 上跑出来。
