# AGENTS.md — lesson-kit 开发纪律

> 阶段 2–3 产物（开工检查清单）。任何 Agent（Claude Code / Codex / Pi / DSH…）在本仓库
> 工作时必须遵守。新对话开场先复述：**分层方向、兼容边界、scope 边界**，复述不对请纠正。

## 项目地图（本文件是入口，但内容不全在本文）

不同的 Agent CLI 只自动加载 `AGENTS.md` / `CLAUDE.md` 这一层。下面这些文件**不会被自动加载**，
需要时按路径读取：

| 文件 | 内容 |
|---|---|
| `.claude/CLAUDE.md` | 运行时地图（pipeline/pool/views 结构）与池契约（字段名、id 前缀、source_kind 取值） |
| `TASK_ROUTER.md` | 任务 → 该跑哪个命令 / 读哪个技能的路由表 |
| `START_HERE.md` | 冷启动路由（当前契约速览） |
| `docs/GLOSSARY.md` | **全部设计名词的唯一权威定义源**；正式文档用词以它为准 |
| `docs/DATA_MODEL.md` | **持久字段语义的唯一权威定义源**；字段状态、含义、writer/consumer 边界以它为准 |
| `docs/ARCHITECTURE.md` | 分层与架构现状 |
| `skills/<name>/SKILL.md` | 提示词技能模块，**按路径引用**（见下） |

**关于 `skills/`**：这些技能是**路径引用的 Markdown 模块**，不是 Agent Skills 标准包——
它们**没有 YAML frontmatter**，因此不会被任何 harness 的自动发现机制加载（Pi 会警告并跳过）。
这是有意的：由 `TASK_ROUTER.md` 或具体命令指明读哪一个，缺什么读什么。
不要为了"让它们被发现"而给这些文件批量加 frontmatter。

## 兼容边界（硬规则，违反先问）

| 层 | 策略 |
|---|---|
| 用户数据格式 | 开发期可改测试数据；进入维护期必须向后兼容 |
| 用户可感知的行为 | 必须兼容，以旧为优先；有充足优化动机时先问再做 |
| 内部代码接口 | 允许删减重构，但必须在高度模块化前提下，禁止"自由重构" |
| 文档 / 规范 | 是资产不是负担；改动代码必须同步被击中的 OpenSpec / DATA_MODEL / ARCHITECTURE / ADR 等职责文件 |

## 契约权威与冲突处理

不同文档只在自己的职责内权威，**禁止按“哪个文件更新得晚”自行选边**：

| 资产 | 唯一职责 |
|---|---|
| `openspec/specs/` | 当前用户可观察行为与 capability contract |
| `docs/DATA_MODEL.md` | 持久字段语义、状态、writer/consumer 边界 |
| `docs/GLOSSARY.md` | 设计名词定义 |
| `FILE_CONTRACT.md` | Agent / CLI 中间工件与 manifest 契约 |
| `docs/ARCHITECTURE.md` | 分层、依赖与模块边界 |
| `docs/PRODUCT-MANUAL.md` | 用户操作与可见产品说明 |
| `openspec/changes/` | 尚未成为当前事实的增量变更 |
| `openspec/changes/archive/` | 历史原因；**不得用于推断当前事实** |

代码与 SQLite schema 是实现事实和审计证据，但不能单独覆盖已经声明的契约。
若上述职责文件或实现对同一事实互相冲突，这叫 **contract drift**：Agent 必须在当前任务
范围内登记并协调，无法安全裁决时保持冲突显式存在并提出独立 change，禁止静默挑一个版本继续实现。
`docs/audits/` 只保存带日期的审计快照，不是滚动规范，也不得成为新的 source of truth。

## 分层铁律

- 单向依赖：Shell → Domain → Data；Content 读产物；Bridge 旁挂只被请求。
- Domain 纯规则零 IO；Data 是唯一碰 SQLite 的地方；CLI/Server 零业务逻辑。
- 新代码进 `workbench/`；**禁止修改** `pipeline/`、`pool/scripts/`、`lessonkit.py`
  的行为契约（可在 pool_schema.py 的 ensure_* 模式内做增量迁移）。

## 开发纪律

1. **需求先落文档再动代码**：spec 未覆盖的行为必须先改 OpenSpec（proposal→specs）或
   询问用户，禁止悄悄实现。
2. **名词先定义后使用**（2026-08-29 三文档约束）：正式文档（openspec specs、
   proposal、REQUIREMENTS、PRODUCT-MANUAL）引入新名词前必须先在
   `docs/GLOSSARY.md` 建条目；未定义的概念只能进 `docs/PENDING-DEFINITIONS.md`，
   禁止以挂名状态混入正式文档；功能变更交付时同步补 `docs/PRODUCT-MANUAL.md`
   对应章节，并同步登记 `docs/ACTION-GRAPH.md`（新增/退役/改级动作必须留痕）。
3. **Contract Reconciliation**：凡是改变用户可观察行为、持久字段/schema、CLI/API、manifest/
   中间工件或字段枚举的任务，交付前必须逐项检查其职责文件并在**同一个 PR**同步；未受影响的
   文档不要机械改写。发现既有契约冲突时先显式登记/解决，不得靠时间戳、代码现状或个人猜测选边。
4. **Ponytail 阶梯**：写码前依次问——要不要写？有没有现成？标准库能否搞定？一行函数
   够不够？禁止过度工程、禁止防御性编程、禁止哈希。
5. **小步提交**：`feat/fix/docs/chore/refactor` 前缀；工作区不留脏；每完成一个可验证
   单元即提交。
6. **验证节奏**（每个 PR 必跑的仓库级检查）：
   ```bash
   python -m pytest tests -q
   python -m compileall -q lessonkit.py workbench pipeline pool tests
   openspec validate --specs --strict
   python lessonkit.py guard extract-problems --course dmath --chapter ch06
   ```
   `problem-set` guard 属于工作区产物验收，只在对应输出已经生成时运行；
   干净 Git checkout 不跟踪 `output/`，因此它不是仓库级 CI 前置条件：
   ```bash
   python lessonkit.py guard problem-set --course dmath --chapter ch06
   ```
7. **单对话职责单一**：设计对话 / 实现对话 / 重构对话分开；长任务拆段，每段可恢复。
8. **低价值探索禁止**：实现前先走阶梯（见 4），不确定的设计先问。

## 运行时约定

- 所有 `lessonkit.py` / `lesson-kit` 命令按 CWD 解析相对路径——在仓库根目录运行。
- 运行时文件进隐藏点目录（`.lessonkit/`）：figures/ 与 explain/ 跟踪，
  jobs/ 忽略（`.gitignore` 已配）。
- 工作台注册表与 bridges 配置（JSON）在用户级 `~/.lessonkit-workbench/`。

## 新对话初始化（每次必做）

1. 喂三件套：本文件 + `docs/ARCHITECTURE.md` + 状态简报（上次到哪/这次做什么/坑）。
2. Agent 先复述关键规则（分层、兼容边界、scope），确认后再动手。
3. 交付前更新交接文档（changelog 或 STATUS 风格记录）。
