# Architecture — lesson-kit Review Workbench (Backend)

> 阶段 1 产物（开工检查清单）：架构即契约。底层（数据模型/核心接口/协议）规划死，上层留灵活。
> 本文件是后端契约；前端页面形态在壳层内灵活演进。

## 0. 分层总则（ADR 0009，硬规则）

```
Shell（lesson-kit CLI + HTTP 服务）   ← 无业务逻辑，只编排
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
├── surface.py         # 接口归属表：每个路由/命令的受众，测试与真实 parser/ROUTES 对账
├── domain/            # 学习模型层（纯规则）
│   ├── __init__.py
│   ├── weak.py        # 弱项排序 + 级联信号提升（ADR 0015）
│   ├── pull.py        # 拉题引擎（正式 problems → 缺口报告）
│   ├── feedback.py    # 1-5 与自然语言 → signals/events（ADR 0011）
│   ├── schedule.py    # SM-2 变体（review_schedule，方向复合键，永不锁题）
│   ├── planning.py    # 确定性今日计划与有界 Agent 调整
│   ├── difficulty.py  # 四维客观题目难度校验、Decimal 汇总与档位投影
│   ├── practice_set.py # 练习集渲染纯规则（题号、遮答案、缺解写「待补」、泄漏扫描）
│   ├── cards.py       # 闪卡内容规则
│   ├── micro_quiz.py  # 微题内容规则与判分
│   └── mastery.py     # 只读掌握度实验规则
├── data/
│   ├── __init__.py
│   ├── pool.py        # Pool：工作区级只读/写连接 + 查询（weak/due/problem/kp/figures）
│   ├── queries.py     # 视图查询（hub 统计、练习页合流列表/到期提醒/日历）
│   ├── content.py     # Agent 内容 CRUD/历史/顺序 ID/事务级联
│   ├── difficulty.py  # 显式难度 check/apply 整批事务
│   ├── attempts.py    # Agent 代录尝试：清单校验、单事务 apply、快照守卫的 correct
│   ├── practice_sets.py # 练习清单校验/解析与出卷（两份 Markdown，零写入预检）
│   ├── goals.py       # 工作区本地目标存储
│   ├── mastery.py     # 掌握度实验的只读数据投影
│   └── display_metadata.py # 展示字段回填
├── bridge/
│   ├── __init__.py
│   ├── conversation_providers.py # PATH Agent 发现、原生新建/续聊命令、活动事件归一化与轮次预算
│   ├── conversations.py # conv-###、串行 turn、取消、成功镜像（含执行计划、静默预算看门狗）
│   └── pi_rpc.py       # 每对话一个隐藏 `pi --mode rpc` 常驻进程（LF JSONL、abort、空闲回收）
├── ingest/
│   └── __init__.py    # 内容 prepare/run/gate/apply/batch/rollback
├── cli/
│   ├── __init__.py
│   └── main.py        # lesson-kit 入口（argparse；纯数据命令，无教学语义）
├── server/
│   ├── __init__.py
│   ├── app.py         # BaseHTTPRequestHandler 路由（单进程单端口 127.0.0.1）
│   ├── api.py         # JSON API 处理器（hub/weak/pull/practice/feedback/schedule/figures/ai）
│   ├── context.py     # 按路由/对象 ID 重建 Agent 权威页面上下文（练习页额外附带限长的聚焦草稿）
│   └── pages.py       # 服务端渲染 HTML（KaTeX 资产静态复用 editable-graph/dist）
└── tests/             # pytest；tests/test_*.py 与 tests/workbench/ 分开
```

## 2. 数据契约（全部增量，ADR 0017/0019）

- 新表 `review_schedule(item_type, item_id, direction, state, repetitions, ease,
  interval_days, due_at, last_rating, last_reviewed_at)`，PK `(item_type, item_id, direction)`，
  direction 默认空串（普通项无方向；卡片按方向独立调度）。
- 新表 `feedback_events(id, item_type, item_id, rating, note, attempt_id, created_at)` 追加日志；
  `attempt_id` 只用于 Agent 代录（指回那次尝试），浏览器自评与旧行为 NULL。
- 新表 `attempt_operations(request_id, problem_id, attempt_id, kind, rating, fingerprint,
  batch_fingerprint, result, pre_state, post_state, created_at)`：一次 Agent 清单操作一行，
  含幂等键与内容指纹、返回给调用方的结果、以及该次操作前后**受影响投影**的快照
  （题目进度/当前状态/调度行 + 关联知识点的状态与信号）；`correct` 靠它判断
  「还能不能改」并在能改时精确撤回旧评分影响。
- 新表 `content_sequences(scope, entity_type, next_value)` 只为显式内容创建分配可读顺序 ID；浏览和搜索不触碰序列。
- 题目与闪卡可增量拥有 `display_title`（可读短标题）与 `topic_label`（单一主题标签）；它们是内容展示字段，不替代稳定 ID。
- 闪卡可增量拥有 `directions`：只存 `["forward"]` 或 `["forward", "reverse"]`；旧卡缺省单向，双向内容仍只占一行，练习方向复用 `review_schedule` 复合键。
- 当前学习状态是知识点/题目的覆盖式值（`needs_work` / `review` / `mastered`），与 `feedback_events` 的追加历史分离；图谱直接编辑当前状态时只更新该值与调度。
- 新列：`knowledge_points.figure_paths`、`problems.figure_paths`（逻辑路径 JSON）、
  `problem_attempts.answer_text`、`problems.origin_kind`、`problems.exam_year`（可空来源
  年份，如 `2023-2024秋冬`，前缀匹配筛选），以及 `problems` 的可空四维
  客观难度、REAL 总分和 `difficulty_model`。四维、总分与模型全空或全有；旧标量
  迁移清空，不伪造向量。`knowledge_points.difficulty` 保留 legacy 语义。
- 内容批次：一次门禁 apply 一份清单、一次预检、一份可恢复备份；清单可跨章，按每一项声明的章发号与落图（`figures/{course}/{chapter}/`），并**按章各记一个批次**，因此 rollback 的粒度是「一章」而不是「一次导入」。
- 运行时布局：`.lessonkit/figures/{course}/{chapter}/{owner_id}-fig-{NNN}.png`（跟踪；`{course}`
  是「课程标识符」而不是工作区名）、
  `.lessonkit/jobs/conv-###/`（provider 会话指针、运行事件与成功问答镜像，gitignored）、
  `.lessonkit/plan.json` 与 `.lessonkit/goals.json`（工作区本地计划/目标；目标可含
  `start_date`→`deadline` 展示区间，旧目标无开始日期兼容）、
  `~/.lessonkit-workbench/workspaces.json` + `bridges.json`（用户级，JSON——stdlib 无 YAML 解析）。
- ID 一律可读顺序标识（`job-003`），无哈希。

## 3. 核心接口（模块边界）

- `registry`：`load() / save() / register(path, name?) -> Workspace / list() -> [Workspace] /
  get(name) -> Workspace`；Workspace = dataclass(name, path, db, active_course, active_chapter)。
- `domain.weak.score(pool, course, chapter, now) -> [(kp, score, reasons)]`——原因可解释。
- `domain.pull.select(pool, kp_ids, n, mode, source_kind?, origin_kind?, source_group?,
  difficulty_ranges?, strategy?) -> {problems:[...],
  shortage:[kp_id...]}`——永不伪造内容；候选机制已物理移除（2026-08-30）。
- `domain.difficulty`：唯一模型 `cognitive-v1-equal-mean`；四维等权 Decimal
  `ROUND_HALF_UP` 一位小数，并提供 balanced 使用的 1–5 档位投影。
- `domain.cards.select(cards, schedule_rows, preference, excluded_*) -> [card action]`——把内容方向能力展开为独立练习动作并按各自调度行排序，零 IO。
- `domain.feedback.apply(pool, item_type, item_id, rating?, note?, direction?, attempt_id?) -> changes`——映射规则全在
  feedback.py，单测覆盖关键词表；`attempt_id` 只把事件链回尝试，不改映射语义。
- `domain.schedule.after_result(pool, item, result, now)`——SM-2 变体；`due(pool, days) -> [...]`。
- 图谱状态动作经 Domain 规则映射到现有调度质量值；Shell 不直接写 SQLite，Data 层执行覆盖式存储。
- 图谱指标投影完全位于浏览器表示层：`graph-physics.js` 只为现有节点计算内存中的目标位置、目标半径与过渡力；关系结构/题量/重要性/学习状态均不产生数据写入。
- 图谱状态筛选分群完全位于浏览器表示层：四个既有状态按多选并集决定可见子图，`graph-physics.js` 只计算内存聚类目标；筛选值仅随页面上下文提供给 Agent，不写 Pool。
- `data.content`：结构化读、显式 CRUD、状态与门禁/晋升编排；所有物理删除级联由一个 SQLite 事务完成。
- `data.difficulty.check/apply`：1–N 题完整清单的零写入预览与整批原子覆盖；内容语义变化
  统一清空整组评级，未评级不影响任何主流程。
- `domain.practice_set.render_*`：练习集两份 Markdown 的纯文本规则（连续题号、学生卷
  不含答案与内部标识、缺解写「待补」、`leaks` 扫描）；`data.practice_sets` 负责清单
  校验/解析与出卷，写文件由 Shell 完成。
- `data.attempts.record_result`：`/practice` 与 CLI `practice` 共用的单事务写法
  （尝试 + 进度 + 调度一起写，未知题拒写）。
- `data.attempts.check/apply/correct/list/get`：Agent 代录尝试的零写入预检、单事务多题、
  按 attempt-id 的守卫式更正与只读回看；带评分的条目在**同一事务内**调用既有
  `domain.feedback.apply(..., attempt_id=…)`（不经过 categorical 的 `practice` 映射），
  无评分的条目只落尝试文本，任何投影都不改。
- `bridge.conversations`：每工作区 `list/create/get/start/cancel`；同一会话单轮串行，
  provider 事件归一为命令/工具/搜索/回答活动，成功轮次将合并后的执行计划随答案镜像；
  隐藏推理与原始协议包不进镜像，完整上下文仍留在 provider 原生 store。
  轮次预算是**静默预算**而非总时长：任一输出行或事件都重置时钟，命令/工具在飞时改用
  更长的工具预算（`bridge add --timeout/--tool-timeout`），因此长回答与慢命令都不会被
  截停；真正卡住的轮次仍如实记为 `provider timed out`。
- Pi 在同一 normalized activity + 350ms polling 链路上把读、写、搜索、命令和
  Lesson Kit 操作呈现为独立消息；Codex/Claude 继续使用执行计划，不新增流协议。
- `ingest.content-bundle`：一份清单原子提交知识点/正式题/微题/闪卡/图片；预检即校验引用、
  契约、来源证据、图片字节与目标冲突，apply 在单事务内落库并按字节复制图片，回滚连带删除
  本批创建且无引用的图片文件。清单可跨章（每项自己的 `chapter`，推不出即点名拒收），预检/
  备份/事务覆盖整份清单而**按章各记一个批次**；题型由 `quiz_type` 决定（综合题/判断/小测），
  **客观题允许没有答案键**——这类题不判分、计入 `keyless` 计数并披露，答案键可在
  `data.content` 里事后补写（按该题 `quiz_type` 校验形状，空值清回无键）。
- `ingest`：`prepare/run/gate/apply/apply_batch/rollback_batch`；生成内容只有通过
  确定性门禁后才能以批次事务写入，并保留整批回滚边界。
- `ingest.problem-patch`（+ `data.content.plan_problem_patch`）：**原地**改已有题目——
  单题与批量共用同一份校验（未知字段/题号身份/难度归属/微题契约），批量记录批次号与
  每行改前旧值，`rollback_batch` 对它走「写回旧值」而不是「删行」，因此学习记录不受影响。
- `server.context`：按浏览器提供的路由与对象 ID 重新读取 Pool，生成权威 Agent 上下文；不接收整页 DOM。
- `server.api`：handler 注册表 {method, path_pattern, handler(pool, ws, args) -> json}；
  HTML 页面经 pages.py，JSON 经 api.py，二者不混。

## 4. 扩展点（明确留口）

- Bridge 新浏览器动作：先扩展意图门与结构化 action 契约，再复用现有 Data/ingest
  写入边界；普通对话始终只读。
- 新学习动作：domain 加模块，data.queries 加查询，Shell 加命令/页面。
- AI 教师记忆消费端：读 trace（jobs 归档）+ feedback_events，独立后置模块。
- 前端：pages.py 服务端渲染升级为更顺滑交互时，改 pages.py 与静态资产即可，不动后端接口。
- 图谱关系管线是纯展示映射：现有 attraction 决定宽度/深浅，候选布局执行有限
  确定性消交叉；三层 SVG 路径和位置均不进入 SQLite。
- 前端内容边界：主学习文本完整换行；代码、展示公式与表格局部滚动；主要
  flex/grid 子项显式允许收缩，避免改变三栏几何。
- 视觉 token 以暖纸、墨线、学习蓝、阳光黄、注意红为固定角色；页面不得把
  颜色作为状态的唯一信息载体。
- 练习题与知识正文共享主阅读层级；模式选择、解析和关联题只作次级表面，
  不改变练习状态机或任何写入契约。

## 5. 工程约束（硬规则）

stdlib-only；单进程单端口；无哈希；无防御性编程（不写不可能分支、不包 try 兜底一切）；
函数短小、单一职责；每个 domain 模块配一个测试文件；改动同步本文档与 OpenSpec。
