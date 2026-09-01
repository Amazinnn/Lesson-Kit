# Architecture — lesson-kit Review Workbench (Backend)

> 阶段 1 产物（开工检查清单）：架构即契约。底层（数据模型/核心接口/协议）规划死，上层留灵活。
> 本文件是后端契约；前端页面形态在壳层内灵活演进。

## 0. 分层总则（ADR 0009，硬规则）

```
Shell（wb CLI + HTTP 服务）   ← 无业务逻辑，只编排
  ↓ 只调用
Domain（弱项/拉题/反馈/调度） ← 纯规则，零 IO 副作用，可单测
  ↓ 只调用
Data（池子读写 + 迁移）       ← 唯一碰 SQLite 的地方
  ↑
Content（视图查询/渲染）      ← 读 Domain/Data 产物，服务端渲染
  ↑
Intelligence（Bridge）       ← 旁挂：任务+契约+外部 CLI；只被 Shell 请求
```

- **单向依赖，禁止反向**：Domain 不 import 任何 Shell/Server；Data 不 import Domain；
  Bridge 不 import Server。
- **依赖注入**：Domain 函数接收 `Pool`（Data 层对象），不自己开连接。
- 现有 `pipeline/`、`pool/scripts/`、`lessonkit.py` 一律不动；工作台是新增旁挂树。

## 1. 目录契约（workbench/ 全部 stdlib-only）

```
workbench/
├── __init__.py
├── registry.py        # 工作区注册表（~/.lessonkit-workbench/workspaces.json）
├── domain/            # 学习模型层（纯规则）
│   ├── __init__.py
│   ├── weak.py        # 弱项排序 + 级联信号提升（ADR 0015）
│   ├── pull.py        # 拉题引擎（正式 problems → 缺口报告）
│   ├── feedback.py    # 1-5 与自然语言 → signals/events（ADR 0011）
│   ├── schedule.py    # SM-2 变体（review_schedule，方向复合键，永不锁题）
│   ├── planning.py    # 确定性今日计划与有界 Agent 调整
│   ├── cards.py       # 闪卡内容规则
│   ├── micro_quiz.py  # 微题内容规则与判分
│   └── mastery.py     # 只读掌握度实验规则
├── data/
│   ├── __init__.py
│   ├── pool.py        # Pool：工作区级只读/写连接 + 查询（weak/due/problem/kp/figures）
│   ├── queries.py     # 视图查询（hub 统计、练习页合流列表/到期提醒/日历）
│   ├── content.py     # Agent 内容 CRUD/历史/顺序 ID/事务级联
│   ├── goals.py       # 工作区本地目标存储
│   ├── mastery.py     # 掌握度实验的只读数据投影
│   └── display_metadata.py # 展示字段回填
├── bridge/
│   ├── __init__.py
│   ├── conversation_providers.py # PATH Agent 发现、原生新建/续聊命令与 JSONL 归一化
│   └── conversations.py # conv-###、串行 turn、取消、成功镜像
├── ingest/
│   └── __init__.py    # 内容 prepare/run/gate/apply/batch/rollback
├── cli/
│   ├── __init__.py
│   └── main.py        # wb 入口（argparse；纯数据命令，无教学语义）
├── server/
│   ├── __init__.py
│   ├── app.py         # BaseHTTPRequestHandler 路由（单进程单端口 127.0.0.1）
│   ├── api.py         # JSON API 处理器（hub/weak/pull/practice/feedback/schedule/figures/ai）
│   ├── context.py     # 按路由/对象 ID 重建 Agent 权威页面上下文
│   └── pages.py       # 服务端渲染 HTML（KaTeX 资产静态复用 editable-graph/dist）
└── tests/             # pytest；tests/test_*.py 与 tests/workbench/ 分开
```

## 2. 数据契约（全部增量，ADR 0017/0019）

- 新表 `review_schedule(item_type, item_id, direction, state, repetitions, ease,
  interval_days, due_at, last_rating, last_reviewed_at)`，PK `(item_type, item_id, direction)`，
  direction 默认空串（普通项无方向；卡片按方向独立调度）。
- 新表 `feedback_events(id, item_type, item_id, rating, note, created_at)` 追加日志。
- 新表 `content_sequences(scope, entity_type, next_value)` 只为显式内容创建分配可读顺序 ID；浏览和搜索不触碰序列。
- 题目与闪卡可增量拥有 `display_title`（可读短标题）与 `topic_label`（单一主题标签）；它们是内容展示字段，不替代稳定 ID。
- 当前学习状态是知识点/题目的覆盖式值（`needs_work` / `review` / `mastered`），与 `feedback_events` 的追加历史分离；图谱直接编辑当前状态时只更新该值与调度。
- 新列：`knowledge_points.figure_paths`、`problems.figure_paths`（逻辑路径 JSON）、
  `problem_attempts.answer_text`。
- 运行时布局：`.lessonkit/figures/{course}/{chapter}/{owner_id}-fig-{NNN}.png`（跟踪）、
  `.lessonkit/jobs/conv-###/`（provider 会话指针、运行事件与成功问答镜像，gitignored）、
  `.lessonkit/plan.json` 与 `.lessonkit/goals.json`（工作区本地计划/目标；目标可含
  `start_date`→`deadline` 展示区间，旧目标无开始日期兼容）、
  `~/.lessonkit-workbench/workspaces.json` + `bridges.json`（用户级，JSON——stdlib 无 YAML 解析）。
- ID 一律可读顺序标识（`job-003`），无哈希。

## 3. 核心接口（模块边界）

- `registry`：`load() / save() / register(path, name?) -> Workspace / list() -> [Workspace] /
  get(name) -> Workspace`；Workspace = dataclass(name, path, db, active_course, active_chapter)。
- `domain.weak.score(pool, course, chapter, now) -> [(kp, score, reasons)]`——原因可解释。
- `domain.pull.select(pool, kp_ids, n, mode, source_kind?) -> {problems:[...],
  shortage:[kp_id...]}`——永不伪造内容；候选机制已物理移除（2026-08-30）。
- `domain.feedback.apply(pool, item_type, item_id, rating?, note?) -> changes`——映射规则全在
  feedback.py，单测覆盖关键词表。
- `domain.schedule.after_result(pool, item, result, now)`——SM-2 变体；`due(pool, days) -> [...]`。
- 图谱状态动作经 Domain 规则映射到现有调度质量值；Shell 不直接写 SQLite，Data 层执行覆盖式存储。
- `data.content`：结构化读、显式 CRUD、状态与门禁/晋升编排；所有物理删除级联由一个 SQLite 事务完成。
- `bridge.conversations`：每工作区 `list/create/get/start/cancel`；同一会话单轮串行，完整上下文留在 provider 原生 store。
- `ingest`：`prepare/run/gate/apply/apply_batch/rollback_batch`；生成内容只有通过
  确定性门禁后才能以批次事务写入，并保留整批回滚边界。
- `server.context`：按浏览器提供的路由与对象 ID 重新读取 Pool，生成权威 Agent 上下文；不接收整页 DOM。
- `server.api`：handler 注册表 {method, path_pattern, handler(pool, ws, args) -> json}；
  HTML 页面经 pages.py，JSON 经 api.py，二者不混。

## 4. 扩展点（明确留口）

- Bridge 新浏览器动作：先扩展意图门与结构化 action 契约，再复用现有 Data/ingest
  写入边界；普通对话始终只读。
- 新学习动作：domain 加模块，data.queries 加查询，Shell 加命令/页面。
- AI 教师记忆消费端：读 trace（jobs 归档）+ feedback_events，独立后置模块。
- 前端：pages.py 服务端渲染升级为更顺滑交互时，改 pages.py 与静态资产即可，不动后端接口。

## 5. 工程约束（硬规则）

stdlib-only；单进程单端口；无哈希；无防御性编程（不写不可能分支、不包 try 兜底一切）；
函数短小、单一职责；每个 domain 模块配一个测试文件；改动同步本文档与 OpenSpec。
