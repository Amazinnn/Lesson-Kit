# 走查执行器设计说明 — workbench-visual-language-v2

> 状态：设计已落盘，供实现照写。**本文件不是代码**，只给到「照着能写出来」的粒度：
> 模块划分、数据流、命令行接口、目录布局、判定逻辑。
>
> 依据：`acceptance.md`（验收口径，唯一判定依据）、
> `decisions.md`「# 收口：最终基线」（视觉基线）、
> `docs/GLOSSARY.md:843`（走查 / Scratch Walkthrough 定义）、
> `docs/PRODUCT-MANUAL.md:501`（走查一律用副本）、
> `tmp/frontend-audit/F02.md:10`（基线视口实测）。
>
> 约束遵守：
> - **复用既有设施**，不另造注册表机制、不另造服务框架（注册表 = `workbench/registry.py`，
>   服务 = `workbench/server/app.py`）。
> - **不改任何产品代码**：`workbench/`、`pool/`、`pipeline/`、`lessonkit.py` 零改动。
>   执行器是**旁挂**的新文件（见 §0.3 落点）。
> - 每条结论带 `文件:行号`；每条命令行经核实存在（§9 自检表）。

---

## 0. 总览

### 0.1 一句话

**同一个脚本、同一个池副本、同一个隔离注册表、同一组端口，跑两遍（改造前 / 改造后），
把「服务端收到的请求序列」「池里落下的持久化」「屏幕上看到的画面」三类证据分别采集，
再做逐项 diff，最后合成一份可裁决的验收报告。**

### 0.2 三条边界

| 边界 | 约束 |
|---|---|
| 分层方向 | 执行器**旁挂**在服务进程内（请求捕获器）与浏览器侧（截图/关键帧）两处；不进入 Domain / Data 层，不新增持久化写入路径 |
| 兼容边界 | 执行器**不得**改变任何用户可感知行为；它只观察与留证。采集器对被测代码的侵入必须可一键关闭（§2.7 关闭开关） |
| scope 边界 | 本文件只管**怎么跑验收**；不管视觉怎么改（`decisions.md` 收口基线）、不管 spec 怎么写（`specs/`） |

### 0.3 落点（执行器自身的文件）

> 这些是**新文件**，不是产品代码。建议放在 `tools/walkthrough/`（仓库已有 `tools/` 吗？
> **待核**：若不存在则新建；若已存在则并列）。全部为脚本，不进 `workbench/` 包。

| 文件 | 职责 | 对应本文 |
|---|---|---|
| `tools/walkthrough/env.py` | 隔离环境构造：池副本、注册表隔离、端口分配、硬断言 | §1 |
| `tools/walkthrough/launch.py` | 服务启动器：注入请求记录器后再 `app.serve()` | §2 |
| `tools/walkthrough/recorder.py` | 请求序列记录与规范化 | §2 |
| `tools/walkthrough/exercise.py` | 脚本化练习（浏览器驱动） | §3 |
| `tools/walkthrough/dbexport.py` | 持久化与学习投影导出 | §4 |
| `tools/walkthrough/shots.py` | 对照截图采集器 | §5 |
| `tools/walkthrough/frames.py` | 关键帧序列采集器 | §6 |
| `tools/walkthrough/report.py` | 判定与报告汇总 | §7 |
| `tools/walkthrough/run.py` | 总编排：`before` / `after` / `diff` 三段 | §7.4 |
| `tools/walkthrough/selftest.py` | §9 自检表里的每条断言 | §9 |

### 0.4 数据流

```
                    ┌──────────────── 改造前代码（git worktree） ────────────────┐
                    │                                                            │
  池副本 seed.db ──►│ 隔离 ws 目录 ──► 服务进程（launch.py + recorder.py） ◄─────┼── 浏览器（Playwright）
                    │   ▲              │  127.0.0.1:PORT_BEFORE                    │    ├─ exercise.py（脚本化练习）
                    │   │              └── 请求序列 ──► requests.jsonl              ├─ shots.py（对照截图）
                    │   │                                                       │    └─ frames.py（关键帧）
                    │   └──────────── 隔离注册表（LESSONKIT_WB_HOME）              │
                    └────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                    ┌──────────────── 改造后代码（当前工作树） ─────────────────┐
                    │                    同上，同样的端口约定、同样的脚本         │
                    └────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                    diff( before , after ) ──► report.md / report.json
```

---

## 1. 隔离环境的搭法

### 1.1 三重隔离的落点（全部是**既有机制**，不新造）

| 隔离维度 | 既有机制 | 锚点 |
|---|---|---|
| 注册表 | `LESSONKIT_WB_HOME` 环境变量改写注册表根目录 | `workbench/registry.py:11-12` |
| 池 | 池 DB 必须位于工作区目录内，否则**硬拒绝** | `workbench/registry.py:46-50`、`workbench/data/pool.py:19-22` |
| 端口 | `serve --port` / `daemon start --port` 传参；`service.start()` 先探测端口占用 | `workbench/cli/main.py:799-801`、`workbench/cli/service.py:165-166` |

**关键结论**：`workbench/data/pool.py:19-22` 是一道**现成的硬闸**——
`Pool.__init__` 在 `db_path` 逃出 `root` 时直接 `raise ValueError`。
所以「不可能写真实池」的第一道保证不必新写，只要**把工作区目录指向副本**即可。

### 1.2 目录布局

```
<scratch>/                          # 建议 %TEMP%\lessonkit-walkthrough-<runid>
├── registry/                       # ← LESSONKIT_WB_HOME 指向这里
│   ├── workspaces.json             #   隔离注册表（workbench/registry.py:26-31）
│   ├── daemon.json                 #   隔离的守护进程状态（workbench/cli/service.py:15-16、:25-30）
│   └── daemon.log
├── ws-before/                      # 改造前的隔离工作区（池副本）
│   ├── pool/dmath.db               #   池副本（workbench/registry.py:208-212 认这种布局）
│   └── .lessonkit/
│       ├── figures/                #   图资源副本（workbench/server/app.py:326 由此读）
│       ├── explain/
│       ├── practice-sets/ps-001.json  # 试卷 JSON 副本（workbench/data/practice_sets.py:161-162）
│       └── plan.json               #   daily_plan 缓存（workbench/server/api.py:105-121）
├── ws-after/                       # 改造后的隔离工作区（同一 seed 复制而来）
│   └── ...同上
├── before/                         # git worktree：改造前代码（只提供代码与静态资产）
├── after/                          # 当前工作树（只提供代码与静态资产）
└── evidence/
    ├── before/ requests.jsonl db.*.json due.json weak.json shots/ frames/
    ├── after/  同上
    └── diff/    requests.diff.json db.*.diff.json report.md report.json
```

> `ws-before` 与 `ws-after` **必须从同一个 seed 复制**，否则持久化 diff 无意义。
> 池副本用 `shutil.copy2`（保留 mtime，但比较时**忽略 mtime**，见 §4.3）。

### 1.3 逐步命令（Windows / Git Bash，全部经核实）

```bash
# ── 0. 变量 ────────────────────────────────────────────────
REPO="D:/Projects/Academic Workflow/lesson-kit"
SCRATCH="${TEMP:-/tmp}/lessonkit-walkthrough-$(date +%Y%m%d-%H%M%S)"
COURSE=dmath ; CHAPTER=ch06 ; WS=walk
PORT_BEFORE=3091 ; PORT_AFTER=3092

# ── 1. 造隔离工作区（池副本） ──────────────────────────────
mkdir -p "$SCRATCH/registry" "$SCRATCH/ws-before/.lessonkit" "$SCRATCH/ws-after/.lessonkit"
mkdir -p "$SCRATCH/ws-before/pool" "$SCRATCH/ws-after/pool"
cp "$REPO/pool/dmath.db"            "$SCRATCH/ws-before/pool/dmath.db"
cp "$REPO/pool/dmath.db"            "$SCRATCH/ws-after/pool/dmath.db"
# 试卷 / 图 / 解析是工作区文件而非池表，必须一并复制，否则页面会走空态
cp -r "$REPO/.lessonkit/figures"    "$SCRATCH/ws-before/.lessonkit/" 2>/dev/null
cp -r "$REPO/.lessonkit/figures"    "$SCRATCH/ws-after/.lessonkit/"  2>/dev/null
cp -r "$REPO/.lessonkit/practice-sets" "$SCRATCH/ws-before/.lessonkit/" 2>/dev/null
cp -r "$REPO/.lessonkit/practice-sets" "$SCRATCH/ws-after/.lessonkit/"  2>/dev/null

# ── 2. 隔离注册表 + 注册工作区 ─────────────────────────────
export LESSONKIT_WB_HOME="$SCRATCH/registry"
python -m workbench.cli.main init "$SCRATCH/ws-before" --name "$WS" --course "$COURSE" --chapter "$CHAPTER"
python -m workbench.cli.main init "$SCRATCH/ws-after"  --name "$WS" --course "$COURSE" --chapter "$CHAPTER"
python -m workbench.cli.main ls            # 必须只列出 walk 一条，且 path 落在 $SCRATCH 内
```

命令核实：
- `python -m workbench.cli.main` 是模块入口（`workbench/cli/main.py:1207-1209`）；安装后亦可用
  `lesson-kit`（`pyproject.toml` `[project.scripts] lesson-kit = "workbench.cli.entry:lesson_kit_main"`）。
- `init` 的参数集：`path` / `--name` / `--course` / `--chapter`（`workbench/cli/main.py:875-884`）。
- `ls` 存在（`workbench/cli/main.py:899-900`）。
- `init` 在目录里已有池时**不会**重建：`registry.looks_like_workspace()` 因 `pool_candidates()` 非空
  而返回真（`workbench/registry.py:199-212`），故 `_bootstrap_workspace` 被跳过
  （`workbench/cli/main.py:129-130`）。**副本池因此不会被覆盖**。
- `init` 选池走 `find_pool(folder, course)`，命中 `pool/<course>.db`
  （`workbench/registry.py:215-234`）。

### 1.4 「改造前代码」怎么来

改造前的代码用 **git worktree** 取一份，不改当前工作区：

```bash
git -C "$REPO" worktree add "$SCRATCH/before" <PRE_CHANGE_COMMIT>
git -C "$REPO" worktree remove "$SCRATCH/before"   # 跑完清理
```

`<PRE_CHANGE_COMMIT>` = 本变更第一个实现提交之前的提交（在 `feat/workbench-visual-language-v2`
上取「最后一个只改文档的提交」）。**待核**：由实现者按实际提交序列填入。

**为什么必须用 worktree 而不是「切分支跑」**：
1. 静态资产（CSS/JS）由 `workbench/server/app.py:20` 的 `STATIC_DIR` 决定，
   而 `STATIC_DIR = Path(__file__).resolve().parent / "static"`——**跟着代码走**。
   worktree 天然带上改造前的 CSS/JS。
2. 切分支会污染当前工作区，违反 `AGENTS.md`「工作区不留脏」。

`frontend/editable-graph/dist` 同理来自 worktree（`workbench/server/app.py:17-19`）。

### 1.5 独立端口

| 运行 | 端口 | 启动命令 |
|---|---|---|
| 改造前 | `3091` | `python -m workbench.cli.main serve --port 3091`（前台）或 `daemon start --port 3091` |
| 改造后 | `3092` | 同上，换端口 |

- `serve --port`：`workbench/cli/main.py:908-910`。
- `daemon start --port`：`workbench/cli/main.py:912-916`；`service.start()` 会先探测端口是否已被占用
  （`workbench/cli/service.py:165-166`：`port_answers(port)` 为真则抛
  `"port {port} already answers but is not a recorded service"`），**这本身就是一道端口隔离闸**。
- 两个端口必须**不同**，且都不得是 `3081`（`app.serve` 的默认端口，`workbench/server/app.py:403`）。

**重要副作用**：`daemon` 的 pid 状态与日志写在 `registry.base_dir()` 下
（`workbench/cli/service.py:15-16`、`:25-30`），所以隔离的 `LESSONKIT_WB_HOME` **顺带隔离了
守护进程状态**——不会误停用户的真实工作台，反之亦然。

### 1.6 「不可能写真实池」的硬断言（5 处）

> 断言写在 `tools/walkthrough/env.py` 的 `assert_isolated()`，在**每个阶段前后各调一次**。
> 任何一条不成立 → 立即中止整个走查（抛异常，不是警告）。

| # | 断言 | 依据 |
|---|---|---|
| A1 | `os.environ["LESSONKIT_WB_HOME"]` 的绝对路径 ≠ `Path.home()/".lessonkit-workbench"` | `workbench/registry.py:11-12` |
| A2 | 隔离注册表 `workspaces.json` 里**每一条** workspace 的 `path` 与 `db` 解析后都落在 `$SCRATCH` 之下 | `workbench/registry.py:26-31` |
| A3 | 隔离池的 `db_path.resolve()` 与真实池 `pool/dmath.db.resolve()` **不是同一个文件**（`os.path.samefile` 为假） | `workbench/data/pool.py:19-22` |
| A4 | 真实池文件与真实注册表文件的 **SHA-256 + 字节数 + mtime** 在整轮走查前后完全一致 | 兜底：证明没有任何写入 |
| A5 | 服务进程启动后，用 `GET /api/hub/workspaces` 读回所有工作区，逐个断言其 `path` 在 `$SCRATCH` 下 | `workbench/server/api.py:39-57`（`hub_workspaces` 直接吐 `ws["path"]`） |

**A4 的必要性**：A1–A3、A5 都是「配置正确性」断言，挡不住「代码里某个忘了的路径」。
A4 是**结果断言**——真实池一个字节没变，才算没写真实池。

**额外一层（可选但推荐）**：走查期间把真实池文件设为只读
（Windows：`attrib +R "$REPO/pool/dmath.db"`），跑完还原（`attrib -R`）。
> **待核**：`attrib +R` 会不会挡住 SQLite 的 `-wal` / `-shm` 旁文件创建——
> 需要实测；若挡住 WAL 就改用「复制法」（把真实池改名、只留副本，跑完换回），
> 但**改名法风险更高**，不作为默认。

### 1.7 服务进程的启动方式（与请求捕获器耦合）

服务**不**用 `lesson-kit serve` 直接起（那样装不进记录器），而是走 §2 的启动器：

```bash
export LESSONKIT_WB_HOME="$SCRATCH/registry"
export PYTHONPATH="$SCRATCH/before:$PYTHONPATH"       # 让 workbench 包解析到 worktree
python "$SCRATCH/before/tools/walkthrough/launch.py" --port 3091 --out "$SCRATCH/evidence/before/requests.jsonl"
```

`PYTHONPATH` 指向 worktree，确保 `import workbench` 拿到的是**改造前**的包
（`python -m` 时 cwd 也在 `sys.path[0]`，双保险）。

---

## 2. 请求序列捕获器（支撑 G-1 / G-2 / G-3）

### 2.1 拦截点选择

**选点：`workbench/server/app.py:128` 的 `WorkbenchHandler._dispatch`。**

```
workbench/server/app.py
  113  class WorkbenchHandler(BaseHTTPRequestHandler):
  116      def do_GET(self):        self._dispatch("GET")
  119      def do_POST(self):       self._dispatch("POST")
  122      def do_PATCH(self):      self._dispatch("PATCH")
  125      def do_DELETE(self):    self._dispatch("DELETE")
  128      def _dispatch(self, method):     ◄── 拦截点
```

**为什么在服务进程内，而不是外部代理**：

| 维度 | 服务进程内拦截 | 外部反向代理 |
|---|---|---|
| 覆盖面 | 全量：页面、静态资源、figures、graph artifact、API、404 **全部**经过 `_dispatch` | 只能看到穿过代理的流量；代理自己发的健康检查会污染序列 |
| 时序真实性 | 请求进入业务代码的**那一刻**被记录，`seq` 与服务端处理顺序一致 | 代理记录的是「到达代理」的时刻，与服务端顺序可能错位（并发时） |
| 改动面 | **零产品代码改动**：在启动器里 monkeypatch 后再 `app.serve()` | 需要另一个进程 + 端口转发 + Host 头改写，可能改变浏览器可见行为 |
| 载荷可见性 | 可读 `self.rfile` 的原始字节（见 §2.3） | 只能看到转发的字节流 |
| 代价 | 启动器要维护 monkeypatch；`app.py` 升级时 monkeypatch 点可能失效（**需在 §9 里断言 `_dispatch` 仍存在**） | 多一个进程；代理配置本身可能成为误判源 |

**外部代理的致命伤**：`GET /` 与 `/static/*` 会被代理当成「资源请求」处理，
但业务上它们与「请求序列」无关；更糟的是代理往往需要「先转发再记录」，
会把**响应耗时**混进顺序里，制造假阳性。

**服务进程内的代价（明写）**：
1. monkeypatch 依赖 `app.WorkbenchHandler._dispatch` 这个具体名字。§9 有一条断言守着它。
2. `_dispatch` 之前的 `do_*` 四个方法只透传方法名——**若将来新增 `do_PUT`**，
   记录器仍会覆盖（因为它包的是 `_dispatch`），但**方法名记录**依赖 `_dispatch(method)` 的入参，
   这一点不受影响。好。
3. 记录器与业务在**同一线程**（`ThreadingHTTPServer`，`workbench/server/app.py:400`），
   记录失败绝不能影响业务响应 → 记录器内部**全 try/except 吞异常**，写盘失败只降级为 stderr 警告。

### 2.2 记录格式（原始层）

每条请求一行 JSONL，追加写：

```jsonc
{
  "seq": 7,                        // 全局单调递增（线程安全计数器）
  "t_ms": 1234.567,                // 相对服务启动的毫秒
  "method": "POST",
  "raw_path": "/api/w/walk/practice/current/submit",
  "route": "POST /api/w/{name}/practice/current/submit",  // 路由模板（见 §2.4）
  "query": {},                     // 解析后的 query（§2.4 规范化）
  "body_keys": ["drafts","execution_id","request_id"],   // 顶层键（排序后）
  "body_shape": {"drafts":"[]", "execution_id":"scalar","request_id":"scalar"},
  "body_raw": "{\"execution_id\":...}",   // 原文（可选，默认关闭；开启时进 .raw.jsonl）
  "status": 200,                   // 响应码（见 §2.5）
  "phase": "measure",              // 见 §3.3 分段
  "group": "exercise"              // 见 §3.3 分组
}
```

> `body_raw` 默认**不落盘**（含用户答案文本，且体积大）。
> 需要留证时用环境开关 `WALKTHROUGH_KEEP_BODY=1` 打开，且落在 `evidence/` 目录里。

### 2.3 载荷捕获：tee reader（不读走业务流）

`_dispatch` 在 `workbench/server/app.py:154-184` 里读请求体：

```
155  if method in {"POST", "PATCH", "DELETE"}:
156      has_body = bool(self.headers.get("Content-Length"))
...
168      raw = self.rfile.read(length) if length else b"{}"
169      body = json.loads(raw.decode("utf-8")) if raw else {}
```

关键：**只读一次** `self.rfile.read(length)`。因此在进入原 `_dispatch` 之前，
把 `self.rfile` 换成 tee 包装器即可截获**同一批字节**，业务读到的内容完全不变：

```python
class _TeeReader:
    """包住 rfile：read() 的字节原样返回，同时复制到 sink。"""
    def __init__(self, source, sink): self._source, self._sink = source, sink
    def read(self, size=-1):
        data = self._source.read(size)
        self._sink.write(data)
        return data
    def readline(self, *a): 
        data = self._source.readline(*a); self._sink.write(data); return data
    def __getattr__(self, name): return getattr(self._source, name)
```

记录器包 `_dispatch` 的形状（**伪代码**，实际实现见 `tools/walkthrough/recorder.py`）：

```python
_original_dispatch = app.WorkbenchHandler._dispatch

def _recording_dispatch(self, method):
    sink = _ByteSink()
    original_rfile = self.rfile
    self.rfile = _TeeReader(original_rfile, sink)      # 只在读体期间生效
    try:
        return _original_dispatch(self, method)
    finally:
        self.rfile = original_rfile
        try:
            recorder.record(method, self.path, self.headers, sink.bytes())
        except Exception:                               # 记录失败绝不影响业务
            print("[walkthrough] recorder failed", file=sys.stderr)
```

**关于 tee 的一个坑**：`_dispatch` 对 **GET** 不读体（`app.py:155`），所以 GET 的 `sink` 恒为空——
这是期望行为（GET 无载荷）。DELETE 无 body 时 `body = {}`（`app.py:157-158`），
载荷键集合为空集。

### 2.4 规范化（diff 前的 canonical 形式）

**目标**：两次运行之间，唯一允许不同的是「具体生成的 ID」与「时间戳」。
规范化把这两类抹掉，其余全部保留。

#### (a) 路径 → 路由模板

不要靠正则猜 ID 段，**直接复用服务自己的路由表** `workbench/server/app.py:39-104`。
`app.ROUTES` 的每一项是 `("GET", "/api/w/{name}/weak", handler)`。
记录器自己实现一个与 `_match_route`（`app.py:361-377`）同构的匹配器，
返回**命中的模板字符串**：

```
POST /api/w/walk/practice/current/submit   →  POST /api/w/{name}/practice/current/submit
POST /api/w/walk/practice-sets/ps-004       →  POST /api/w/{name}/practice-sets/{practice_set_id}
GET  /api/w/walk/practice/runs/17           →  GET  /api/w/{name}/practice/runs/{run_id}
```

未命中路由（404）的请求：`route` 记为 `"<UNMATCHED> " + 归一化后的 raw_path`。
归一化规则：路径段里凡是**形似生成的 ID**（`ps-\d+`、纯数字、`kp-\w+-\d+`、`conv-\w+` 等）
替换成 `{id}`。**未命中路由本身就是异常信号**，会原样出现在 diff 里。

> 为什么不用路由模板而不用「段数 + 形状」：路由模板**恰好**是冻结契约的一部分
> （`workbench/server/app.py:39-104` 就是 API 表面），模板变了 = API 变了 = FAIL。
> 段数相同但模板不同（`/practice/current/stuck` → `/practice/current/stuck2`）会被模板 diff 抓到。

#### (b) query

`query` 的**键集合**保留，值默认丢弃（值常含 `limit` 等非语义参数）；
若某个 query 键在**白名单**里（默认空），值也保留并参与 diff。

#### (c) 载荷键集合 + 形状

```
canonical_payload_shape(body) -> {key: shape}
  shape ∈ {"scalar", "[]", "{}", "[]{}"}
  # [] = 数组；{} = 对象；[]{} = 对象数组
```
- 顶层键排序后写入 `body_keys`。
- 对象数组 `[]{}`：再记录**并集**的子键名，写进 `body_shape` 的附加字段 `body_subkeys`，
  例如 `drafts[]` → `["draft","position","sequence"]`。
- **值不参与主 diff**（G-1 的口径是「载荷**键集合**」）。

#### (d) 值白名单（**加强项**，不替代键集合 diff）

键集合相同但值不同，也是行为变化。以下字段的值**参与 diff**（枚举型，跨运行必然稳定）：

| 字段 | 出现在 | 取值 |
|---|---|---|
| `practice_mode` | start / practice/current | `exam` / `micro` / `yes_no` |
| `rating_mode` | start / practice/current | `immediate` / `batch` / `off` |
| `reveal_timing` | start / practice/current | `per_item` / `on_submit` |
| `stuck` | /attempts | `true` / `false` |
| `edit_existing` | /feedback | `true` / `false` |
| `item_type` | /feedback | `kp` / `problem` / `card` |
| `verdict` | /attempts | 见 §4.2 |

#### (e) 排除纯读请求

**主 diff 只含写请求**：

```
写请求 = method ∈ {POST, PATCH, PUT, DELETE} 且 path 以 /api/ 开头
```

被排除的（但**仍然记录**在原始 JSONL 里）：所有 `GET`、页面路由 `/` 与 `/w/...`、
静态资源 `/static/...`、`/api/w/.../figures/...`、`/api/w/.../graph/artifact`。

> 理由：`GET` 是「读」，G-1 的冻结对象是「API 请求序列与载荷」中**会改变学习事实**的那部分；
> 读请求的差异单独出一张表（§2.6 的 L2），由人工判读，不自动判 FAIL。

**但必须写清楚**：G-1 的字面口径是「一次完整练习的**请求序列**不变」，
严格读法包含 GET。执行器的做法是**双层报告**：
- **L1（自动判定，阻断）**：写请求序列 + 载荷键集合 + 值白名单。
- **L2（必须人工签字，不自动阻断）**：GET 序列差异表。报告里以「⚠ 需人工判读」呈现，
  并在 §7.2 的判定表里占一行由人填「接受 / 不接受」。
  —— 若自动判 FAIL，会把「视觉改造顺带多读一次设置项」误伤；
  若完全不报，会漏掉「改造后少发了一次读请求导致页面状态不对」。

### 2.5 状态码捕获

`_dispatch` 用 `self._send_json(status, payload)` / `_send_html(status, text)` 收尾
（`workbench/server/app.py:199-209`）。记录器再包一层 `_send_json`，
把**最终状态码**记到该请求上。因为 `_dispatch` 是同步的，可以在 `_dispatch` 前后
用「线程局部当前记录」把状态码挂回去。

> 简化方案：包 `_send_json` / `_send_html`，用 `threading.local()` 存「当前记录」，
> 在 `_dispatch` 的 `finally` 里统一落盘。

### 2.6 diff 算法与证据文件

**规范化后的签名序列**：

```
signature[i] = f"{method} {route} | keys={body_keys} | shape={body_shape} | vals={白名单值}"
```

**diff 用 `difflib.SequenceMatcher`**（标准库，无需第三方）：

```python
import difflib
sm = difflib.SequenceMatcher(a=[sig_before], b=[sig_after], autojunk=False)
ops = sm.get_opcodes()   # 'equal' / 'replace' / 'delete' / 'insert'
```

`replace` 段落里再做**成对比较**：若两段的 `route` 相同 → 判为「**载荷变了**」（G-1 FAIL）；
若 `route` 不同 → 判为「**请求被改名/替换**」（G-1 FAIL）。

**证据文件**：

| 文件 | 内容 |
|---|---|
| `evidence/before/requests.jsonl` | 原始记录（含 GET） |
| `evidence/after/requests.jsonl` | 同上 |
| `evidence/diff/requests.norm.json` | 两侧的规范化签名数组 |
| `evidence/diff/requests.diff.json` | 结构化差异：`{added:[], removed:[], changed:[], read_added:[], read_removed:[]}` |
| `evidence/diff/requests.diff.md` | 人读的 unified diff + 逐条说明（改哪条、为什么） |

**「新增/删除/改名任意一条即 FAIL」**（`acceptance.md:18`）的机器判定：
`len(added) + len(removed) + len(changed) > 0` → G-1 = FAIL。

### 2.7 关闭开关（侵入性可一键关闭）

`WALKTHROUGH_RECORD=0` → 启动器**不装** monkeypatch，直接 `app.serve()`。
用于两件事：
1. 证明「装了记录器不影响业务」（对照跑一次，见 §9 自检 D2）。
2. 出现记录器自身 bug 时可绕开。

---

## 3. 脚本化练习的脚本设计

### 3.1 驱动方式：**浏览器驱动，不是 HTTP 直调**

**这是本设计最关键的一条。**

如果脚本用 `requests.post(...)` 直接打 API，那么「请求序列」是**脚本写死的**，
无论前端怎么改，diff 永远为空——**G-1 变成空检查**。
视觉改造最容易出的事故恰恰是「前端多发/少发/改发了一次请求」，
只有让**真实 UI** 去发，才能抓到。

因此：脚本用 Playwright 驱动**真实页面**，让 UI 自己发请求；
记录器在服务端收。

> 工具前提：`playwright` 已在本机可用（`D:\Python\Lib\site-packages\playwright`）。
> 浏览器内核需已 `playwright install`——**待核**：本机是否已装 chromium。

### 3.2 步骤表

| # | 步骤 | UI 锚点（稳定语义） | 期望 API（服务端实际会看到） | 前置状态 |
|---|---|---|---|---|
| E0 | 打开练习页 | `GET /w/{ws}/practice` | GET `/api/w/{ws}/practice/current` | 服务已起 |
| E1 | 选卷并开始 | `?paper=ps-001` → `#paper-start` | POST `/api/w/{ws}/practice-sets/{practice_set_id}/start` 载荷 `{practice_mode, rating_mode, reveal_timing}` | 试卷存在且 `can_start` |
| E2 | 第 1 题作答 | `#paper-options` 内选项 / `#paper-answer` 输入 → `#paper-item-submit` | POST `/api/w/{ws}/attempts` 载荷含 `{problem_id, answer_text, practice_position, practice_context, request_id}` | `reveal_timing=per_item` |
| E3 | 第 1 题自评 | `#paper-rating` 内评分控件 → 保存 | POST `/api/w/{ws}/feedback` 载荷含 `{item_type, item_id, attempt_id, rating, note, request_id, practice_context}` | E2 已确认（拿到 `attempt_id`） |
| E4 | 草稿落库 | 输入框触发 `queueDraft` | POST `/api/w/{ws}/practice/draft` 载荷 `{execution_id, position, practice_context, sequence, draft}` | **计时敏感**，见 §3.4 |
| E5 | 翻到下一题 | `#paper-next` | POST `/api/w/{ws}/practice/current/navigate` 载荷 `{execution_id, position, practice_context}` | — |
| E6 | 重复 E2–E5 | — | 同上 | 每题都走一遍 |
| E7 | 交卷 | `#paper-final-submit` | POST `/api/w/{ws}/practice/current/submit` 载荷 `{execution_id, request_id, drafts}` | 全部题目已作答 |
| E8 | 取答卷 | 自动（`prepareRun`） | GET `/api/w/{ws}/practice/runs/{run_id}` | E7 返回 `run_id` |
| E9 | 完结页 | `#paper-completion` | （无写请求） | E8 完成 |

**关键锚点核实**（全部来自 `workbench/server/static/paper-practice.js` 与
`workbench/server/pages.py`）：

| 锚点 | 出处 |
|---|---|
| `#paper-start` | `workbench/server/pages.py:208` |
| `#paper-options` / `#paper-answer` / `#paper-item-submit` | `workbench/server/pages.py:217-220` |
| `#paper-rating` | `workbench/server/pages.py:222` |
| `#paper-toolbar` / `#paper-next` / `#paper-stuck` / `#paper-final-submit` | `workbench/server/pages.py:211-214` |
| `#paper-dots` / `#paper-question` / `#paper-reference` | `workbench/server/pages.py:215-216`、`:221` |
| `#paper-completion` / `#paper-completion-stats` | `workbench/server/static/paper-practice.js:49-50` 取 id（页面侧区块见 `workbench/server/pages.py:222-226`） |
| `?paper=<id>` 入口 | `workbench/server/static/paper-practice.js:57`、`:1540` |
| start 请求体 | `paper-practice.js:471-477` |
| attempt 请求 | `paper-practice.js:1026`（`post("/attempts", payload)`） |
| feedback 请求 | `paper-practice.js:817`（`post("/feedback", body)`） |
| submit 请求 | `paper-practice.js:1210`（`post("/practice/current/submit", body)`） |
| 取答卷 | `paper-practice.js:1214`（`api("/practice/runs/" + run_id)`） |

### 3.3 「建卷」——**当前没有浏览器入口**（重要发现）

`acceptance.md:18` 的练习序列第一步是「建卷」。
现状核实：

- `workbench/server/pages.py:156` 注释写明：**"Practise a saved Paper; authoring is delegated to Agent/CLI."**
- 浏览器端确有 `post("/practice-sets", …)`（`workbench/server/static/practice-flow.js:1353`），
  但它所在的 `saveCurrentSelectionAsPaper()` 依赖 `legacyModeControls`
  （`practice-flow.js:202`、`:1338`），而 `legacyModeControls` 要求页面上存在
  `#practice-rating-immediate` / `#practice-rating-batch`——
  **这两个 id 在 `workbench/server/pages.py` 中不存在**（已 grep 确认），
  即当前构建**不渲染**保存试卷的控件（`#save-practice-set` 同样不存在）。
- 权威建卷入口是 CLI：`lesson-kit papers <ws> save --input <manifest.json>`
  （`workbench/cli/papers.py:17-21` 参数、`:48-50` save 分支），或 `POST /api/w/{ws}/practice-sets`
  （`workbench/server/api.py:336-344` → `workbench/data/practice_sets.py:314-316`）。

**执行器的处理（分三段，见 §3.4）**：

| 段 | 内容 | 是否进 G-1 主 diff |
|---|---|---|
| `seed` 段 | 建卷（CLI 或 API）+ 种子数据准备 | **否**——但**单独出一张 diff 表**（`requests.diff.md` 的「建卷组」） |
| `measure` 段 | E0–E9 全流程 | **是**（L1 主 diff） |
| `verify` 段 | 只读核对（`/due`、`/weak`） | 否（进 L2） |

**这样处理的理由**（必须写进报告，避免读者误以为「建卷」被覆盖了）：
建卷在当前构建里**没有浏览器路径**，所以「改造是否影响建卷」无法通过浏览器观察。
执行器仍跑一次建卷（两侧用**完全相同**的命令与参数），证明
「脚手架一致、且建卷请求未被改造影响」；但它**不具备回归检测力**，
报告里必须标注为 ⚠ 覆盖缺口，并列入 §8 的风险清单。
**若后续产品补上浏览器建卷入口，本段升级为 measure 段的一部分。**

### 3.4 幂等与确定性要求

| 要求 | 做法 |
|---|---|
| 种子数据一致 | before / after 两个工作区从**同一个** `seed.db` 复制；试卷 JSON 逐字节相同 |
| 试卷 ID 相同 | 建卷后把 ID 钉死为 `ps-001`（ID 形如 `ps-NNN`，`workbench/data/practice_sets.py:158`）；两侧用同一份 `practice-sets/ps-001.json` 种子，**不靠 `POST /practice-sets` 现场生成**（生成会扫描 `practice_runs` 抢号，见 `practice_sets.py:173-198`） |
| 题目确定 | 固定 `problem_ids` 列表（3 题：1 道选择题 + 1 道填空/文字题 + 1 道判断题），写死在脚本常量里 |
| 作答内容确定 | 每次输入**同样的字符串**（如 `"42"`、`"x=1"`、`"对"`）。文本入 `draft` → 进 `practice_runs.items_json` → 进 §4 的持久化 diff |
| **草稿请求的时序** | `queueDraft` 用 **350ms 防抖**（`paper-practice.js:952`）→ `POST /practice/draft` 的**次数**取决于打字节奏，天然不稳定。**处理**：脚本在每次输入后**显式等待**草稿落库（轮询记录器里 `/practice/draft` 计数 +1，或直接等到 UI 的 `pendingDrafts` 清空），把草稿请求数**钉死为每题 1 次**；若无法钉死，则把 `/practice/draft` 移出 L1 主 diff、单独列为「时序敏感组」（报告里明示） |
| 请求 ID | `request_id` 每次随机（`paper-practice.js` 的 `requestId()`）→ 载荷**值**不进 diff，只进键集合。**但** `practice_runs.items_json` 里可能落 `request_id` → §4 导出时**剥离**随机 ID |
| 时间戳 | `started_at` / `finished_at` / `created_at` / `updated_at` → §4 导出时替换为 `<TS>` |
| 执行 ID | `execution_id` 是生成的 → §4 导出时替换为 `<EXEC>` |
| 重试噪声 | 脚本不得触发失败重试。若某步超时，**脚本整体失败**，不做「重试到成功」——重试会制造额外的写请求，污染 diff |

### 3.5 脚本骨架（伪代码）

```python
# tools/walkthrough/exercise.py
def run_exercise(base_url, ws_name, paper_id, out_dir):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True,
                                    args=["--force-color-profile=srgb",
                                          "--disable-lcd-text"])     # 字体渲染稳定
        ctx = browser.new_context(viewport={"width": 1440, "height": 900},
                                  device_scale_factor=1,
                                  color_scheme="light",
                                  reduced_motion="no-preference")
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept(TITLE))   # 建卷时的 window.prompt

        phase("measure")
        page.goto(f"{base_url}/w/{ws_name}/practice?paper={paper_id}",
                  wait_until="networkidle")
        wait_enabled("#paper-start")
        page.click("#paper-start")
        wait_for_request("POST", "/practice-sets/.*/start")

        for item in SEED_ITEMS:                       # 3 题
            answer_item(page, item)                  # 选/填 → #paper-item-submit
            wait_for_request("POST", "/attempts")
            rate_item(page, item)                    # #paper-rating → 保存
            wait_for_request("POST", "/feedback")
            if not last(item):
                page.click("#paper-next")
                wait_for_request("POST", "/practice/current/navigate")

        page.click("#paper-final-submit")
        wait_for_request("POST", "/practice/current/submit")
        wait_for_request("GET",  "/practice/runs/")

        phase("verify")
        due = get(f"{base_url}/api/w/{ws_name}/due")
        weak = get(f"{base_url}/api/w/{ws_name}/weak?limit=200")
        write(out_dir / "due.json", due)
        write(out_dir / "weak.json", weak)
        ctx.close(); browser.close()
```

`wait_for_request` **必须等服务端记录**（记录器落盘）而不是浏览器事件，
否则会与记录器有竞态。实现：记录器提供 `/__walkthrough__/events` 只读端点，
或脚本直接 tail `requests.jsonl`。

### 3.6 与 G-4 的衔接

G-4「复习建议集合不变」＝ `due` 集合与 `weak` 排序不变。
- `GET /api/w/{name}/due` → `workbench/server/api.py:96-99` → `queries.due_list(pool)`
  （`workbench/data/queries.py:71-77`）。
- `GET /api/w/{name}/weak` → `workbench/server/api.py:87-94` → `weak.score_all(...)`。
两者都是 GET，**落在 L2 组**；但它们比较的是**学习事实**，所以单独抽出一张
`due.diff.json` / `weak.diff.json`，**自动判 FAIL**（集合或顺序不同即 FAIL）。

---

## 4. 持久化与学习投影比对

### 4.1 比对范围（表 × 列）

G-2（`acceptance.md:19`）点名 `problem_attempts` / `feedback_events` / `practice_runs`；
G-3（`acceptance.md:20`）点名「知识点当前状态与调度行」。

| 表 | DDL 出处 | 关键列 | 归一化 |
|---|---|---|---|
| `problem_attempts` | `pool/scripts/pool_schema.py:286-301` | `id, problem_id, status, note, created_at` | `created_at` → `<TS>`；`id` 保留 |
| `feedback_events` | `pool/scripts/pool_schema.py:630-643` | `id, item_type, item_id, rating, note, created_at` | `created_at` → `<TS>`；`id` 保留 |
| `practice_runs` | `pool/scripts/pool_schema.py:722-742` | `id, source_kind, source_ref, source_label, kp_ids_json, practice_mode, rating_mode, items_json, status, started_at, finished_at` | `started_at`/`finished_at` → `<TS>`；`items_json` 解析后按 §4.2 规范化；`id` 保留 |
| `learning_current_state` | `pool/scripts/pool_schema.py:746-760` | `item_type, item_id, state, updated_at` | `updated_at` → `<TS>`；按 `(item_type,item_id)` 排序 |
| `review_schedule` | `pool/scripts/pool_schema.py:610-628` | `item_type, item_id, direction, state, repetitions, ease, interval_days, due_at, last_rating, last_reviewed_at` | `last_reviewed_at` → `<TS>`；`due_at` 的**日期部分**参与比较（`due_at` 由 `datetime('now')` 派生，绝对时刻会差几秒 → 只比日期） |

**额外两张（防「改了学习投影的写入路径」漏网）**：

| 表 | 出处 | 为什么 |
|---|---|---|
| `problem_progress` | `pool/scripts/pool_schema.py:257-284` | 题目级进度（`status`）是浏览器作答的落点之一 |
| `learner_signals` | `pool/scripts/pool_schema.py:375+` | 学习信号（权重 / 证据数）是学习投影的组成部分 |
| `active_practice` / `active_practice_items` | `pool/scripts/pool_schema.py:682-721` | 练习轮当前状态；交卷后应清空，两侧应一致 |

### 4.2 `items_json` 与 `draft` 的规范化

`practice_runs.items_json`（`docs/DATA_MODEL.md:242`）保存每题的
`content_revision` / `draft` / `draft_sequence`。规范化规则：

```
normalize_items_json(text):
  obj  = json.loads(text)
  for item in obj:
      item["draft"]["request_id"] = "<RID>"        # 随机请求 ID
      item["draft"]["updated_at"]  = "<TS>"        # 若有
      item["draft"]["reference_viewed_at"] = "<TS>" # 若有
      item["attempt_id"] = "<AID>"  # 仅当其值随运行变化时
      # draft_sequence 保留 —— 它反映草稿写入次数，正是我们要盯的
  return json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=1)
```

**`draft_sequence` 必须保留**：它直接反映「草稿写了几次」，
是 §3.4 幂等性是否成立的硬指标；两侧不等 ⇒ 交互节奏变了 ⇒ G-1 FAIL（写请求组）。

`verdict`（`docs/DATA_MODEL.md:150`）是客观判定，落 `problem_attempts` 或 draft；
它是**事实**，参与比较。

### 4.3 导出格式

每张表导出成一个 JSON 文件（**不是 CSV**：嵌套 JSON 字段需要无损承载）：

```jsonc
// evidence/before/db.problem_attempts.json
{
  "table": "problem_attempts",
  "columns": ["id","problem_id","status","note","created_at"],
  "normalization": ["created_at -> <TS>"],
  "row_count": 3,
  "rows": [
    {"id": 41, "problem_id": "dmath-ch06-prob-007", "status": "answered",
     "note": null, "created_at": "<TS>"}
  ]
}
```

排序：按主键 / 复合主键升序（`problem_attempts.id`、`feedback_events.id`、
`practice_runs.id`、`learning_current_state.(item_type,item_id)`、
`review_schedule.(item_type,item_id,direction)`）。
**行序必须稳定**，否则 diff 全是噪声。

### 4.4 diff 与判定

```python
def diff_table(before, after):
    if before["row_count"] != after["row_count"]:
        return {"verdict": "FAIL", "reason": "row count differs",
                "before": before["row_count"], "after": after["row_count"]}
    b = {row_key(r): r for r in before["rows"]}
    a = {row_key(r): r for r in after["rows"]}
    changed = [k for k in b if k in a and b[k] != a[k]]
    return {"verdict": "FAIL" if changed else "PASS",
            "changed_keys": changed,
            "only_before": sorted(set(b) - set(a)),
            "only_after": sorted(set(a) - set(b))}
```

- **G-2**（`acceptance.md:19`）：`problem_attempts` / `feedback_events` / `practice_runs`
  三张表**行数与关键列逐行相同** → PASS。任何一张 FAIL ⇒ G-2 FAIL。
- **G-3**（`acceptance.md:20`）：`learning_current_state` + `review_schedule` +
  `problem_progress` + `learner_signals` **完全相同** → PASS。
- **G-4**：`due.json` / `weak.json` 的集合与顺序完全相同 → PASS。

### 4.5 G-6：池 schema 零变更

G-6（`acceptance.md:23`）要求「池内零新增列、零新增行」。
schema 比对用 `sqlite_master`：

```sql
SELECT type, name, sql FROM sqlite_master
 WHERE name NOT LIKE 'sqlite_%'
 ORDER BY type, name;
```

导出 `schema.before.json` / `schema.after.json` 并 diff。
两侧 schema **必须逐字相同**（DDL 文本也进 diff，因为 `ALTER TABLE ADD COLUMN` 会改 `sql`）。
> **注意**：真实池若本来就有历史遗留的 schema 差异，两侧都来自同一个 seed，
> 所以 diff 必然为 0；G-6 的真实检查对象是「**改造后**的真实池 vs **改造前**的真实池」，
> 而真实池不在走查范围内。执行器能做到的是：
> ① 证明走查期间真实池未变（A4）；② 证明走查期间副本的 schema 未变（schema diff = 0）。
> 「改造后的真实池 schema 是否与改造前相同」由**代码审阅 + `git diff --stat pool/`** 兜底——
> 写进报告的「需人工确认」栏。

---

## 5. 截图对照采集器

### 5.1 视口表

`acceptance.md:31-52` 给了每条的视口宽度。执行器统一成一张表：

| 组 | 视口宽 | 视口高 | deviceScaleFactor | 对应条目 |
|---|---|---|---|---|
| V1440 | 1440 | 900 | 1 | S-1…S-10、S-12 |
| V1024 | 1024 | 800 | 1 | S-11 |
| V768 | 768 | 900 | 1 | S-11 |
| V1280 | 1280 | 900 | 1 | §3.5 响应式检查 |

**deviceScaleFactor = 1**：比对用 `difflib`/像素差时 1× 足够，且文件小。
（现存基线是 1.5×，见 §5.5。）

### 5.2 一致性要素（每次截图必须钉死的变量）

| 变量 | 固定方式 | 理由 |
|---|---|---|
| 视口 | `viewport={width, height}` | 布局断点 |
| DPR | `device_scale_factor=1` | 像素尺寸 |
| 颜色方案 | `color_scheme="light"`（夜间单独跑 `dark`） | `prefers-color-scheme` 会切 token |
| 动效偏好 | `reduced_motion="no-preference"`（降级帧单独跑 `reduce`） | `prefers-reduced-motion` 会切动画 |
| 字体 | 同机同浏览器；禁字距优化 `--disable-lcd-text` | 抗锯齿差异 |
| 时区/语言 | `locale="zh-CN"`，`timezone_id="Asia/Shanghai"` | 日期渲染 |
| **滚动位置** | 截图前 `window.scrollTo(0, Y)`，Y 由**元素锚点**决定（见下） | 「同一滚动位置」的可复现定义 |
| **数据状态** | 同一 seed 副本 + 同一脚本跑出的状态 | 「同一数据状态」 |
| **等待** | `wait_for_load_state("networkidle")` + 目标元素可见 + **无进行中的动画** | 动效中途的截图不可比 |
| 主题 | 走 `/w/{ws}/…` 的正常路径 + 设置视图切主题 | 不能靠注入 CSS 变量伪造 |

**滚动位置的锚点定义**（比「固定像素」稳）：每个条目指定一个**锚点元素选择器**，
截图前执行 `scrollIntoView({block:'start'})`，并把该元素的 `getBoundingClientRect().top`
记进元数据。两次运行的锚点元素可能 DOM 结构不同（改造允许改 DOM 结构），
所以**锚点选择器必须用稳定语义**（id / `data-*` / 可访问名），不能用 class 或 nth-child。

### 5.3 命名规则

```
evidence/<before|after>/shots/
  S-<n>-<slug>-<variant>.png
```
- `S-<n>`：对应 `acceptance.md` §1 的条目号（S-1…S-12）。
- `<slug>`：条目名（`hub` / `practice` / `kps` / `kp-detail` / `records-overview` /
  `records-detail` / `practice-sets` / `settings` / `night` / `narrow` / `empty`）。
- `<variant>`：`1440` / `1024` / `768` / `dark` / `reduced` / `before-submit` …
- 主题与视口在文件名里显式出现，**不靠目录区分**（避免漏拷）。

**成对命名**：同一 `<n>-<slug>-<variant>` 在 `before/` 与 `after/` 各一张 →
并排图由 §5.4 的拼图器生成。

### 5.4 产出与并排图

| 产物 | 路径 |
|---|---|
| 单页截图 | `evidence/<side>/shots/S-*.png` |
| 并排对照图 | `evidence/diff/shots/S-*.png`（左 before / 右 after，中间 2px 分隔线） |
| 像素差图 | `evidence/diff/shots/S-*-delta.png`（差异像素染红，相似处灰化） |
| 元数据 | `evidence/<side>/shots/index.json`（条目、视口、滚动锚点、wait 条件、文件 sha256） |

**像素差算法**：无第三方库，用 `PIL`（本机可用，基线 PNG 就是它读的）+ `ImageChops.difference`：
```
diff = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
bbox = diff.getbbox()          # 全黑则完全一致
ratio = 差异像素数 / 总像素数
```
- `ratio == 0` → 完全一致。
- `0 < ratio <= 0.005` → 「仅抗锯齿/字体渲染差异」→ 人工判读（`acceptance.md:51`
  允许「肉眼不得出现配色被改/圆角被改/信息被删」，但 G-5 图谱页要求「像素级一致」，
  阈值要严）。
- `ratio > 0.005` → **FAIL**，必须在报告里列出 bbox 与差异区域。

> **PIL 是第三方库**：本机已有（基线 PNG 用它读过）。执行器应**优先**用它，
> 但要在 §9 自检里断言 `import PIL` 可用；不可用时降级为「只出并排图，人工比对」，
> 并在报告里标注「像素差未自动判定」。

### 5.5 与现存基线图的关系（**重要**）

`acceptance.md:34` 说基线图已在 `tmp/frontend-audit/00-baseline-*.png`（7 张）。
实测这 7 张的像素尺寸**不一致**：

| 文件 | 尺寸 |
|---|---|
| `00-baseline-hub.png` | 2322 × 2337 |
| `00-baseline-records.png` | 2322 × 1670 |
| `00-baseline-workbench.png` | 2322 × 1670 |
| `00-baseline-kps.png` | 2339 × 1143 |
| `00-baseline-kp-detail.png` | 2339 × 1143 |
| `00-baseline-practice-full.png` | 2339 × 1143 |
| `00-baseline-practice-sets.png` | 2339 × 1143 |

且 `tmp/frontend-audit/F02.md:10` 记录的视口是 `2040×1230` 与 `1555×1114`，
`devicePixelRatio 1.5`。两套宽度（2322 vs 2339）说明**这 7 张不是同一次采集**，
滚动位置、焦点态、hover 态、动画时机均无记录。

**结论与处置**：

1. **执行器自己产基线**：用 §1.4 的 worktree 把改造前代码跑一遍，
   由**同一个采集器**产出 `evidence/before/shots/*`。这样 before/after 的
   视口、DPR、滚动、wait 条件**逐项相同**，像素差才有意义。
2. **现存 7 张只作人工参考**，不进自动判定。在报告里写明
   「`tmp/frontend-audit/00-baseline-*.png` 视口与采集时机不可控，未纳入像素判定」。
3. 若因故无法拉 worktree，则**降级为并排目视比对**（`acceptance.md:51` 的口径），
   并在报告里把该项标为「⚠ 目视比对，未像素判定」。

### 5.6 采集清单（`acceptance.md` §1 的 S-1…S-12）

| # | 页面 / 状态 | 视口 | 必看点 | 锚点选择器（建议） | 备注 |
|---|---|---|---|---|---|
| S-1 | hub 首页 | 1440 | 最近使用置顶区、卡片信息层级 | `[data-workspace-card], .workspace-card` | **待核**：卡片是否有稳定钩子 |
| S-2 | 练习页（未开练） | 1440 | 顶栏三段式、题面纸、题号导航 | `#paper-setup` | |
| S-3 | 练习页（进行中） | 1440 | 题面独立纸、24px 题号、解析同级纸 | `#paper-work` | 需脚本跑出「进行中」状态 |
| S-4 | 知识点列表 | 1440 | 分组卡片、彩色圆点状态 | `#middle-page` | |
| S-5 | 知识点详情 | 1440 | 衬线阅读面 + 单侧结构线 | `/w/{ws}/kp/{id}` | |
| S-6 | 记录中心 · 概览 | 1440 | 仪表盘卡片、热力日历 | `/w/{ws}/records` | |
| S-7 | 记录中心 · 作答明细 | 1440 | 圆角卡片流（**不得出现表格**） | `/w/{ws}/records?view=…&problem=…` | `acceptance.md:44` |
| S-8 | 试卷列表 | 1440 | 卡片网格、状态圆点、**无 5px 黄带** | `/w/{ws}/practice-sets` | |
| S-9 | 设置视图 | 1440 | 主题 / 阅读字面 / 动效 / 声音 | 左栏设置开关（**新增页，改造后才存在**） | 改造前无此页 → 记为 N/A |
| S-10 | 夜纸（同一页面） | 1440 | 夜纸值集、圆底降饱和提亮、插画反相 | 同 S-1…S-4 任一页 + `color_scheme=dark` | |
| S-11 | 窄屏 | 768、1024 | 三栏折叠、右栏抽屉 | 同 S-1 | |
| S-12 | 空态（无试卷 / 无记录 / 无对话） | 1440 | 插画 + 一句 + 满宽主按钮 | 独立 seed（空工作区） | |

**S-9 的「改造前不存在」**：设置视图是本变更**新增**页面
（`decisions.md` 收口基线「工作台设置视图」）。截图采集器在 before 侧找不到入口时，
**记 `N/A（改造前不存在）**，不判 FAIL；但要判「after 侧存在且四偏好可切换」。

**S-12 的空态需要另一份 seed**：空态要「无试卷 / 无记录 / 无对话」，
所以要再准备一个**空工作区**（`ws-empty-before` / `ws-empty-after`，池为空表但 schema 齐全）。
做法：用 `pool/scripts/pool_schema.py` 的 `ensure_workbench_schema` 建空表
（`tests/workbench/fixtures.py:63-134` 的 `build_fixture_db` 是现成参考）。

---

## 6. 关键帧序列采集器

### 6.1 核心难点（`acceptance.md:58` 已点出）

> 「动效不能只靠截图验收（截图看不到运动）。每个动效采一组帧，拼成一条**分镜条**。」

而 `decisions.md` 收口基线要求一次性动效（挤压回弹 517ms、台灯 700ms、庆祝 900–1200ms）
——**这类动效无法靠 CSS 无限循环维持**（无限循环的截图会拍到任意相位，不可复现）。

**解法：不依赖动效自行播放，而是「确定性重放」**：
1. 用 `page.evaluate` 把动画**暂停在指定时刻**（Web Animations API：`anim.pause(); anim.currentTime = t`）。
2. 或对 CSS 动画用 `document.getAnimations()` 统一 `pause()` 后逐帧设 `currentTime`。
3. 若动效是 JS 驱动的（非 Web Animations），用 `page.clock`（Playwright 的虚拟时钟）
   或 `page.evaluate` 注入时间戳，逐帧推进。

**这正是「一次性动效不能靠 CSS 无限循环」这个坑的正解**：
不要求动效常驻，而是**在采集时把它变成可寻址的时间轴**。

### 6.2 采集算法

```
capture_strip(page, trigger, frames_ms, out_dir):
    # 1. 冻结
    page.evaluate("() => document.getAnimations().forEach(a => a.pause())")
    # 2. 触发（把 currentTime 归零后触发，确保从 0 开始）
    page.evaluate("() => document.getAnimations().forEach(a => { a.currentTime = 0 })")
    trigger()                       # 例如 page.click("#theme-switch")
    # 3. 若触发动画是动态创建的，等它出现
    page.wait_for_function("() => document.getAnimations().length > 0")
    # 4. 逐帧
    for t in frames_ms:
        page.evaluate("t => document.getAnimations().forEach(a => a.currentTime = t)", t)
        page.wait_for_timeout(0)   # 让一帧落地
        page.screenshot(path=out_dir / f"{t:04d}.png")
```

**必须记录的元数据**（进 `index.json`）：
`frames_ms`、`animations`（每个的 `animationName` / `effect.getTiming()` 的 duration /
`playState`）、每帧的 `getComputedStyle` 关键属性（`transform` / `opacity`）、
触发时的 `performance.now()`。

### 6.3 逐条动效的帧表（`acceptance.md` §2 的 M-1…M-10）

| # | 动效 | 帧（ms） | 触发方式 | 关键观察 | 落点 |
|---|---|---|---|---|---|
| M-1 | 台灯主题转场 | 0 / 90 / 180 / 330 / 500 / 700 | 点设置视图的主题开关 | 四段：探出 → 点亮 → 涟漪扩散 → 收回；700ms 后终态干净 | `frames/M-1/` |
| M-2 | 交卷庆祝（日常档） | 0 / 120 / 300 / 600 / 900 | 完成页出现后 | 数字滚动 + 进度带 0→100%；**无彩带** | `frames/M-2/` |
| M-3 | 交卷庆祝（里程碑档） | 0 / 150 / 400 / 800 / 1200 | 造出里程碑种子数据后交卷 | 几何爆点 + 纸片；**不遮挡完成页 CTA** | `frames/M-3/` |
| M-4 | 连对升级 | 0 / 100 / 250 / 450 / 700 | 连对到 5 / 10 时 | 横幅出现 → 数字替换 → 退场；**横幅只有一份** | `frames/M-4/` |
| M-5 | 连对计数器三档 | 0 / >0 / ≥30 三张静帧 | 造三种连对数种子 | 灰 → 黄 → 黄蓝渐变，**不靠文字** | `frames/M-5/` |
| M-6 | 连对进度火苗簇 | 0 / 200 / 500 | 答对一题 | 逐簇点亮；**答错必须出现负反馈** | `frames/M-6/` |
| M-7 | 挤压回弹（答对） | 0 / 17 / 33 / 83 / 167 / 217 / 517 | 提交正确答案 | scale 0.92 → 1.06 → 1；总时长 ≈517ms | `frames/M-7/` |
| M-8 | 视图转场 | 0 / 60 / 120 / 240 | 切中栏页面 | 上浮 8–12px + 淡入 | `frames/M-8/` |
| M-9 | 骨架屏 | 0 / 400 / 900 | 触发加载态 | 灰块 + 一道微光**扫过**（位置变化可见） | `frames/M-9/` |
| M-10 | 数据层 | 0 / 240 / 480 | 记录页数据层入场 | 负荷柱从 0 生长、逐柱错峰；日历格按强度扩散（**颜色 + 高度双编码**） | `frames/M-10/` |

**每条另出一张降级对照帧**（`acceptance.md:73-74`）：
用 `reduced_motion="reduce"` 的 context 重跑同一触发点，取**终态**一帧，
断言「无中间态」——判据：`document.getAnimations()` 在触发后长度为 0，
或所有动画的 `playState` 为 `finished` 且无中间 `currentTime` 状态。

### 6.4 分镜条拼接

把一组帧按时间顺序**横向拼接**成一条长图：

```
frames/M-1/0000.png 0000.png ... 0700.png  →  evidence/diff/frames/M-1-strip.png
```
- 拼接用 PIL：`Image.new("RGB", (w*n + gap*(n-1), h))`，`gap = 8`，底色 `#fdf8ef`。
- 每帧下方标注毫秒数（用 PIL 默认字体即可，不引字体）。
- 拼图产物：**人看**（分镜条是评审材料，不是自动判定物）。
  自动判定仍靠 §6.2 的元数据（动画时长、`transform`/`opacity` 关键帧值）。

### 6.5 自动判定（能自动判的部分）

| 判据 | 方法 |
|---|---|
| M-7 总时长 ≈517ms | 读 `anim.effect.getTiming().duration` |
| M-7 回弹曲线 | 逐帧读 `getComputedStyle(el).transform` 的 scale 分量，验 0.92→1.06→1 |
| M-1 四段都在 | 逐帧记录台灯元素的 `opacity` / `transform`，看是否出现「探出→点亮→扩散→收回」四个特征段 |
| M-8 上浮 8–12px | 逐帧读 `translateY`，断言峰值 ∈ [8, 12]px |
| M-2/M-3 无彩带 | 逐帧检查彩带元素是否存在（选择器待实现侧提供稳定钩子） |
| 通用：只用 transform/opacity | 逐帧比对 `getComputedStyle` 的 `animation-name` 涉及的属性；§3.7「性能」项要求录一次逐帧确认 |
| 通用：reduced-motion 降级 | 见 §6.3 末 |

> **钩子依赖**：M-2/M-3/M-6/M-7 都需要「庆祝层 / 火苗 / 挤压元素」有稳定选择器。
> 这是**实现侧的责任**（`design.md` / `component-spec.md` 应规定 `data-lk-*` 钩子），
> 执行器侧只负责**登记钩子清单**并在 §9 断言「钩子存在，否则该项标 N/A 而非 PASS」。
> **待核**：钩子清单需与实现侧对齐（当前实现尚无）。

---

## 7. 判定与报告

### 7.1 报告形态

产出两个文件：

| 文件 | 用途 |
|---|---|
| `evidence/diff/report.md` | 人读：逐条 G/S/M/交互清单的结论 + 证据链接 + 未过项清单 |
| `evidence/diff/report.json` | 机读：`{"gates": {...}, "screenshots": {...}, "motion": {...}, "checklist": {...}}` |

`report.md` 的骨架：

```markdown
# 走查验收报告 — workbench-visual-language-v2
生成时间：<ISO>   改造前代码：<commit>   改造后代码：<commit>

## 0. 底线守卫（任一 FAIL ⇒ 整体 FAIL）
| # | 检查项 | 结论 | 证据 |
|---|---|---|---|
| G-1 | 请求序列不变 | ✅ PASS | evidence/diff/requests.diff.md |
| G-2 | 持久化结果不变 | ✅ PASS | evidence/diff/db.problem_attempts.diff.json |
...

## 1. 对照截图（S-1…S-12）
| # | 条目 | 结论 | 差异率 | 对照图 |
...

## 2. 关键帧序列（M-1…M-10）
| # | 动效 | 结论 | 分镜条 | 降级帧 |
...

## 3. 交互清单（§3.1…§3.7，逐条勾选 + 未过说明）

## 4. 未过项清单（每条：现象、影响、复现命令、建议）

## 5. 隔离自检（真实池哈希、注册表哈希、断言 A1…A5）
```

### 7.2 编号映射（**四组**）

`acceptance.md` 的判定由四组构成，报告必须一一对应：

| 组 | 编号 | 采集器 | 自动判定 | 报告位置 |
|---|---|---|---|---|
| **底线守卫** | G-1…G-8 | §2 捕获器 + §3 脚本 + §4 导出 + §5/§6 采集 | G-1…G-4 全自动；G-5 像素差自动；G-6 schema diff 自动；G-7 **需 CSS 扫描**；G-8 **需焦点遍历录制** | §0 |
| **对照截图** | S-1…S-12 | §5 | 像素差自动 + 人工判读 | §1 |
| **关键帧** | M-1…M-10 | §6 | 时序/时长自动 + 人工判读 | §2 |
| **交互清单** | §3.1…§3.7（8 条可访问性 / 6 条主题暗色 / 5 条声音 / 8 条交互反馈 / 3 条响应式 / 6 条图案资产 / 4 条性能 = **42 条**） | §5/§6 + 浏览器探针 | 多数可半自动（见下） | §3 |

**G-7（装饰层不拦截交互）**：`acceptance.md:24` 要求「检查所有新增装饰层的 `pointer-events`」。
自动做法：扫描 `workbench/server/static/*.css` 里所有新增选择器的 `pointer-events` 值，
凡非 `none` 的装饰选择器 → 列出待人工确认。**更硬的自动做法**：在浏览器里
用 `document.elementFromPoint(x, y)` 在装饰层覆盖区域取元素，
若取到的不是装饰层而是底层控件 → 通过。执行器做**后者**（行为证据），CSS 扫描做辅助。

**G-8（焦点顺序未变）**：`acceptance.md:25` 要求录制 Tab 遍历的焦点序列。
自动做法：
```python
page.goto(url)
seq = []
for i in range(N):
    page.keyboard.press("Tab")
    seq.append(page.evaluate("""() => {
        const a = document.activeElement;
        if (!a || a === document.body) return "<body>";
        const label = a.getAttribute("aria-label") || a.textContent || "";
        return (a.tagName + "|" + (a.id || "") + "|" + (a.getAttribute("data-testid") || "")
                + "|" + label.trim().slice(0, 40));
    }"""))
```
**难点**：DOM 结构改造后，元素 id 可能变、顺序可能变，但**焦点顺序（语义顺序）不应变**。
因此焦点条目的标识必须用**语义**：`role` + `aria-label` + 可见文本，**不用 id**。
比较规则：把 `before` 与 `after` 的序列各自归一为「语义描述」再 diff；
`acceptance.md:25` 明确豁免「新增的设置视图入口与主题开关」——
这两条在 before 序列里不存在，属**预期新增**，diff 时标为 `ADDED-EXPECTED`，不判 FAIL。

### 7.3 整体通过标准

照抄 `acceptance.md:134-142`：

> 1. G-1…G-8 **全绿**（任一红 ⇒ 整体 FAIL，不进入后续评审）
> 2. S-1…S-12 对照截图**无回退**
> 3. M-1…M-10 分镜条符合各自标准，且降级对照帧**均为状态直切**
> 4. §3 交互清单**全部勾选**，或未勾选项逐条列出并说明为何可接受

**任一项不通过 → 回到 `tasks.md` 对应阶段返工。**

执行器的机器结论只覆盖第 1 条的 G-1…G-6；第 2/3/4 条的**最终裁决权在人**。
报告用 `⬜ 待人工判读` 而不是替人打勾——这是本设计的立场：
**执行器提供证据，不替代评审。**

### 7.4 编排（`run.py`）

```bash
# 一条命令跑完整轮
python tools/walkthrough/run.py \
    --repo "D:/Projects/Academic Workflow/lesson-kit" \
    --before-commit <PRE_CHANGE_COMMIT> \
    --course dmath --chapter ch06 \
    --scratch "$SCRATCH" \
    --ports 3091 3092
```

三段式：

```
段 1  before:
    建 worktree → 造 ws-before → 起服务(3091, 装记录器) → 建卷(seed 段)
      → 跑 exercise(measure 段) → 跑 shots → 跑 frames → 停服务 → 导出 db.* → 断言 A4
段 2  after:
    同样流程，代码取当前工作树，端口 3092，工作区 ws-after（同一 seed）
段 3  diff:
    requests.diff / db.*.diff / due.diff / weak.diff / schema.diff
      → shots 像素差 → frames 分镜条 → report.md + report.json
```

**段 2 必须在段 1 之后串行**（不能并行：两者都占用真实池的读，且资源争抢会让
帧采样的时序不稳）。

---

## 8. 风险与红线

### 8.1 执行器自身可能误伤真池的地方（逐条）

| # | 风险 | 机理 | 防线 |
|---|---|---|---|
| R-1 | `LESSONKIT_WB_HOME` 没生效，服务读真池 | 环境变量只在**启动器进程**里设；用 `daemon start` 起的后台进程若不继承就落回默认目录 | **只用 `serve`（前台、同进程）**；断言 A1 + A2；**禁用 `daemon` 子命令** |
| R-2 | `init` 在空目录里**重建**了池，把真实内容覆盖 | `cmd_init` → `_bootstrap_workspace` 会调 `create-tables.py` 建库 | 目录里**先放好池副本**再 `init` → `looks_like_workspace` 为真 → 不进 `_bootstrap`（`workbench/cli/main.py:129-130`）。事后断言：副本池的 `sha256` 与 seed 一致 |
| R-3 | 复制的是**符号链接/硬链接**而非独立文件 | Windows 上 `copy` 可能保留 reparse point | 复制后断言 `os.path.samefile(seed, copy) == False` 且 `st_ino` 不同；复制用「读字节 → 写新文件」而非 `shutil.copy2` 的 link 语义 |
| R-4 | 建卷时 `POST /practice-sets` 触发了池写入 | `create_saved` 写的是**工作区文件**（`practice-sets/ps-NNN.json`），但 `paper_state` / `practice_runs` 是**池表** | 建卷只在 `ws-before` / `ws-after` 里做；A4 断言真实池未变 |
| R-5 | 走查脚本跑 `lesson-kit` 子命令时忘了 `LESSONKIT_WB_HOME` | 环境变量是进程级的，脚本内 `subprocess` 默认继承（安全），但**显式 `env=` 覆盖**会丢 | 执行器**所有**子进程都显式传 `env={**os.environ, "LESSONKIT_WB_HOME": SCRATCH}`；并在每个子进程前后断言 |
| R-6 | `workbench` 包被 pip 安装到了 site-packages，`import workbench` 拿到**真仓库**的代码 | 本机 `lesson-kit` 已安装（`pip show lesson-kit` → 0.1.0） | 启动器与脚本都用 `PYTHONPATH=<worktree>` 优先；启动后断言 `workbench.__file__` 落在期望的 worktree 下 |
| R-7 | 图谱工件 / figures 指向真实仓库 | `graph_artifact_path` 在 `.lessonkit/output` 与 `output` 之间择一（`workbench/workspace_layout.py:154-160`）；figures 从工作区 `.lessonkit/figures` 读（`workbench/server/app.py:326`） | 一并复制到隔离工作区；断言 `workspace.path` 在 `$SCRATCH` 下（A2） |
| R-8 | `daily_plan` 把计划缓存写到**真实**工作区 | `_plan_path(workspace)` 挂在 workspace 上（`workbench/server/api.py:105-121`、`:168-169`） | workspace 本身就在 `$SCRATCH` → 天然隔离；A2 兜底 |
| R-9 | 采集器写盘失败拖垮服务 | 记录器与业务同线程 | 记录器内部**全 try/except**（§2.1）；写盘用「追加 + 定期 flush」，失败只告警 |
| R-10 | 帧采样太慢导致动画已播完 | `page.screenshot` 本身耗时 | **必须先 `pause()` 所有动画**再逐帧设 `currentTime`（§6.2），不依赖实时播放 |
| R-11 | 两次运行的 seed 不同（时间戳漂移） | `datetime('now')` 默认值 | seed 是**同一份文件复制**，不是重新生成的；导出时再抹时间戳（§4.1） |
| R-12 | 草稿防抖造成 `/practice/draft` 次数抖动 | 350ms 防抖（`paper-practice.js:952`） | 脚本显式等待草稿落库（§3.4）；无法钉死时降级为独立 diff 组 |
| R-13 | 浏览器把 `localStorage` 偏好带进 before/after 对比 | 主题偏好按工作区存（`decisions.md`「主题偏好」） | **每个 context 用全新 profile**（`browser.new_context()` 即隔离）；显式设 `localStorage` 初值 |
| R-14 | `git worktree` 留下 `.git/worktrees` 残留 | worktree 机制本身 | 跑完 `git worktree remove` + `git worktree prune`；并在报告里记录 worktree 路径 |

### 8.2 「绝不写真实池」的硬断言位置（汇总）

**四道防线，缺一不可**：

1. **配置层**：`LESSONKIT_WB_HOME` 指向 `$SCRATCH/registry`（A1）。
2. **注册层**：隔离注册表里**每条** workspace 的 `path`/`db` 都在 `$SCRATCH` 下（A2）；
   服务起来后从 `/api/hub/workspaces` 再验一遍（A5）。
3. **数据层**：`Pool.__init__` 的既有硬闸（`workbench/data/pool.py:19-22`）——
   db 逃出工作区就抛错；A3 再验一次「副本与真池不是同一文件」。
4. **结果层**：真实池 + 真实注册表的 **sha256 + size + mtime** 整轮前后一致（A4）。

**执行点**：
- 起服务前：断言 A1…A3。
- 每次 `phase()` 切换：断言 A1、A2。
- 停服务后、导出前：断言 A4。
- 整轮结束：断言 A4、A5 写进报告。

**任一断言失败 → 抛异常终止，并把已发生的写入列为「疑似污染」上报**，
同时**保留现场**（不删 `$SCRATCH`）供人工核查。

### 8.3 红线（执行器不得越过）

| # | 红线 |
|---|---|
| X-1 | 执行器**不得**向 `workbench/`、`pool/`、`pipeline/`、`lessonkit.py` **写入或修改任何字节**。捕获靠 monkeypatch，隔离靠既有环境变量，导出靠只读 SQLite 连接 |
| X-2 | 执行器**不得**新增任何持久化写入路径。`tools/walkthrough/` 下的脚本不得被 `workbench` 导入 |
| X-3 | 执行器**不得**用「注入 CSS 变量 / 改 localStorage / mock fetch」的方式伪造改造后状态。主题切换必须走真实设置视图 |
| X-4 | 执行器**不得**为了让 diff 通过而放宽规范（例：把 `/practice/draft` 移出主 diff 必须**在报告里显式标注**，不能静默降级） |
| X-5 | 执行器**不得**在真实池目录里创建任何文件（连 `-wal` / `-shm` 也不行）。走查期间真实池**只读打开** |
| X-6 | 执行器的产物（`evidence/`）**不进 git**（`tmp/` 或 `evidence/` 加进 `.gitignore`），除非所有者明确要求入库作为验收证据 |

---

## 9. 自检清单（实现者跑一遍，全部绿才允许用于验收）

| # | 断言 | 方法 | 通过标准 |
|---|---|---|---|
| D1 | 服务可起、可停 | 起 `serve --port 3091`，`curl` 一次，停掉 | 200 且端口释放 |
| D2 | **记录器不改变业务** | 同一脚本跑两遍：一遍装记录器、一遍不装（`WALKTHROUGH_RECORD=0`） | 两遍的 db 导出**完全相同**；截图**逐像素相同** |
| D3 | 记录器覆盖到全部方法 | 发 GET/POST/PATCH/DELETE 各一次 | `requests.jsonl` 四种方法都出现；**PUT/OPTIONS 不出现**（服务只有四个 `do_*`，`app.py:116-126`） |
| D4 | 载荷键集合正确 | 发一个已知载荷 | `body_keys` 与实际顶层键**完全一致**、已排序 |
| D5 | 路径归一化正确 | 打 `/api/w/walk/practice/runs/17` | `route` 为 `GET /api/w/{name}/practice/runs/{run_id}` |
| D6 | **隔离成立** | 跑完整一轮后检查真实池 | sha256 / size / mtime 三项**均未变**；真实注册表 `workspaces.json` 未变 |
| D7 | 副本与真池不同源 | `os.path.samefile` | 为 `False`；`st_ino` 不同 |
| D8 | worktree 生效 | 在 worktree 起服务后 `GET /api/hub/workspaces` 或打印 `workbench.__file__` | 落在 `$SCRATCH/before` 下 |
| D9 | 脚本可重跑 | 同一脚本连跑两次 | 两次的 `requests.norm.json` **完全相同**；db 导出**完全相同**（幂等） |
| D10 | 帧采样可复现 | 同一触发点采两次 | 两次的帧序列**逐像素相同**（因已 pause + 设 currentTime） |
| D11 | 像素差工具可用 | `import PIL` + 对同一张图自比 | `import` 成功；自比差异率 `0` |
| D12 | 端口隔离 | 同时占用 3091 后再起 3092 | 3092 正常起；`daemon start --port 3091` 报「already answers」 |

---

## 10. 待核项（实现前必须查证，不得臆断）

| # | 待核 | 查证方式 |
|---|---|---|
| W-1 | `<PRE_CHANGE_COMMIT>` 的具体提交 | `git log --oneline feat/workbench-visual-language-v2`；取「第一个改产品代码的提交」的前一个 |
| W-2 | `tools/` 目录是否已存在 | `ls tools/`；不存在则新建（属新增目录，需确认是否符合仓库结构约定） |
| W-3 | Playwright 的 chromium 内核是否已装 | `python -c "from playwright.sync_api import sync_playwright; ..."` 试启动一次 |
| W-4 | PIL 是否可用 | `python -c "import PIL; print(PIL.__version__)"` |
| W-5 | `attrib +R` 是否挡住 SQLite 的 `-wal` 旁文件 | 在临时库上实测；挡住则弃用该防线（§1.6） |
| W-6 | hub 卡片 / 练习页的可访问名与 `data-*` 钩子 | 读 `workbench/server/pages.py` 的 `_left_column`（`:622`）与 hub 页渲染，确认稳定标识 |
| W-7 | 庆祝层 / 火苗 / 台灯的稳定选择器（§6.5） | 与实现侧对齐 `data-lk-*` 钩子清单；未对齐前 M-1/M-2/M-3/M-6/M-7 标 N/A |
| W-8 | `lesson-kit papers save` 生成的 `ps-NNN` 是否两侧一致 | 两次建卷后比对文件名；不一致则改用**预置 JSON 种子**（§3.4） |
| W-9 | `.gitignore` 是否已含 `evidence/` 或 `tmp/` | `cat .gitignore`；必要时补 `evidence/` |
| W-10 | `docs/ACTION-GRAPH.md` 是否需登记执行器动作 | 按 `AGENTS.md` 开发纪律第 2 条，功能交付时同步登记；本设计阶段只在此**标注**，不擅自改该文件（其它 agent 正在写同目录文件） |

---

## 附录 A：产物清单（一轮走查后 `$SCRATCH` 的完整形态）

```
$SCRATCH/
├── registry/{workspaces.json, daemon.json, daemon.log}
├── ws-before/{pool/dmath.db, .lessonkit/{figures,explain,practice-sets,plan.json}}
├── ws-after/…
├── before/                      # git worktree（改造前代码）
├── after/                       # 当前工作树（代码）
└── evidence/
    ├── before/
    │   ├── requests.jsonl
    │   ├── db.problem_attempts.json / db.feedback_events.json / db.practice_runs.json
    │   ├── db.learning_current_state.json / db.review_schedule.json
    │   ├── db.problem_progress.json / db.learner_signals.json
    │   ├── db.active_practice.json
    │   ├── schema.json / due.json / weak.json
    │   ├── shots/{S-*.png, index.json}
    │   └── frames/{M-1/0000.png …, index.json}
    ├── after/                    # 同构
    └── diff/
        ├── requests.norm.json / requests.diff.json / requests.diff.md
        ├── db.*.diff.json
        ├── due.diff.json / weak.diff.json / schema.diff.json
        ├── shots/{S-*.png, S-*-delta.png}
        ├── frames/{M-*-strip.png, M-*-reduced.png}
        └── report.md / report.json
```

## 附录 B：编号速查

| 组 | 编号 | 采集器章节 |
|---|---|---|
| 底线守卫 | G-1 请求序列 / G-2 持久化 / G-3 学习投影 / G-4 复习建议 / G-5 图谱像素 / G-6 schema 零变更 / G-7 装饰层 pointer-events / G-8 焦点顺序 | §2、§3、§4、§5、§7.2 |
| 对照截图 | S-1…S-12 | §5 |
| 关键帧 | M-1…M-10（+ 降级对照帧） | §6 |
| 交互清单 | §3.1 可访问性(8) / §3.2 主题暗色(6) / §3.3 声音(5) / §3.4 交互反馈(8) / §3.5 响应式(3) / §3.6 图案资产(6) / §3.7 性能(4) | §5、§6、§7.2 |
