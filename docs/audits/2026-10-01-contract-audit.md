# Contract Audit — 2026-10-01

> **性质：一次性审计快照，不是规范。** 当前事实仍由 live OpenSpec、DATA_MODEL、
> GLOSSARY、FILE_CONTRACT 等各自职责内的权威文件承担。本文件只记录 2026-10-01
> 在 `main` 上观察到的 drift，解决后保留作为历史证据，不继续滚动维护。

## 审计范围

交叉检查：
- `openspec/specs/*` 与当前 active changes；
- `AGENTS.md`、`openspec/config.yaml`、`FILE_CONTRACT.md`；
- `docs/GLOSSARY.md`、`ARCHITECTURE.md`、`REQUIREMENTS.md`、`PRODUCT-MANUAL.md`；
- `pipeline/scripts/create-tables.py`、`pool/scripts/pool_schema.py`；
- `workbench/ingest`、`workbench/data`、`workbench/domain`、当前 Server/UI 消费路径。

## P0 — 必须先止血

### A1. Figure 命名策略四方冲突

**观察：**
- live `openspec/specs/knowledge-figures/spec.md` 要求 `<sha256>.<ext>`；
- 当前 `workbench/ingest/__init__.py::_figure_name` 实际也使用 SHA-256；
- `AGENTS.md` / `openspec/config.yaml` 又写“禁止 hash / SHA-256”；
- 较新的 `FILE_CONTRACT.md` 与 `docs/ARCHITECTURE.md` 写
  `{owner_id}-fig-{NNN}.png`。

**风险：** Agent 无法判断“代码错了”还是“文档错了”，任何一次图片修复都可能继续扩大 drift。

**本 PR 处理：** 不拍板产品策略；把该字段标记为 unresolved，并规定 Agent 遇到冲突不得猜。
后续需要一个独立决策 change：选择 content-addressed 或 owner-readable 命名，然后一次性同步
OpenSpec、ingest、FILE_CONTRACT、ARCHITECTURE、迁移/兼容策略。

### A2. `display_summary` 已经成为三义字段

**观察：**
- live micro-quiz spec / `domain/markup.py`：最多 200 字符；
- `data/display_metadata.py`：最多 48 字符，且题干 >500 才允许；
- 当前 `server/pages.py` 定义了 summary helper，但主页面无调用；
- live workbench-ui 对知识点关联题明确要求显示完整题面且不显示 summary。

**风险：** Agent 会继续“补全”一个用户根本看不到、且不同写路径校验不一致的字段。

**建议：** 单独决定 **retire** 或 **restore one explicit consumer**。在决策前禁止增加新 consumer。

## P1 — 当前字段职责不闭合

### A3. `graph_label` 可写但主图不消费

- create/ingest/data CRUD 都接受 `graph_label`；
- 当前 graph model 节点标题仍取 `knowledge_item`；
- active `ingest-integrity-and-observability` 已把 graph-label semantics 列为 NEW-GAP。

**建议：** 明确二选一：成为“图谱短标签”的正式字段并规定 fallback，或退役字段。

### A4. `related_kp_ids` 与 `knowledge_relations` 双轨

live review-workbench 明确允许图谱边来自正式关系或 existing `related_kp_ids`。
当前查询实现会把后者转换为 low-strength symmetric legacy edge，且正式边优先。

**问题不在于实现错误，而在于写入职责不清。** 新 Agent 仍可通过通用 KP update 写
`related_kp_ids`，于是“正式关系 CRUD”并没有真正成为唯一关系写路径。

**建议：** 冻结 `related_kp_ids` 新写入，后续迁移成 formal relations；这是行为变化，
需要独立 OpenSpec change，不在本治理 PR 偷改。

### A5. KP 字段语义散落在代码里

`source_location`、`knowledge_type`、`learning_action`、`graph_label`、
`related_kp_ids`、`fragile` 等字段存在于 DDL / ingest / CRUD，
但此前没有一份字段级当前契约。active defect register 已经直接记录过这一问题。

**本 PR 处理：** 新增 `docs/DATA_MODEL.md`，只承担 persisted-field semantics，
不复制产品行为。

## P2 — 明确的遗留噪声

### A6. `create-tables.py` 仍打印 retired candidate 世界

脚本的完成提示仍声称创建 candidate tables；仓库同时保留 candidate 兼容入口与旧脚本，
而 GLOSSARY 已明确 candidate store 退役。

**建议：** 后续做一次 frozen-pipeline hygiene change：不改变兼容行为，只让帮助文本、
统计和注释不再宣称 candidate 是当前能力。

### A7. legacy 内容表仍与现代 workbench 并存

`questions` / `kp_progress` / `question_progress` 仍由基础建库脚本创建，
现代练习主路径则使用 `problems`、attempts、current state、schedule 等表。

这不一定是 bug：pipeline 已被明确冻结。但在字段文档中必须把它们标成 legacy，
否则 Agent 很容易错误地给两套表同时加新功能。

### A8. “只允许 additive schema”与现有 rebuild migration 不完全一致

`AGENTS.md` / OpenSpec context 说 schema 只走 additive ensure；
`pool_schema.py::_ensure_problem_contract` 在旧 schema 升级时会重建 problems 表。

这可能是预发布迁移的历史例外，但目前没有被规则文本承认。
建议后续明确：是删除已无必要的 rebuild，还是把“已批准的兼容 rebuild”写成唯一例外。

## 已确认不是问题

- `problem_type` 与 `micro_quiz.quiz_type` 分开是正确设计：
  前者是学科形态，后者是作答交互。
- `source_kind`、`origin_kind`、派生 `source_group` 三者职责目前有清楚定义。
- objective problem difficulty 与 `knowledge_points.difficulty` 分开是有意的；
  后者是 legacy knowledge complexity。
- formal relation 与 shared-problem co-occurrence 不等价；当前 spec 明确禁止凭共现创造关系。

## 治理结论

仓库的问题不是“文档少”，而是**多个文件同时像 source of truth**。
后续采用职责分区，而不是再造一个万能总文档：

| 资产 | 唯一职责 |
|---|---|
| `openspec/specs/` | 当前用户可观察行为 / capability contract |
| `docs/DATA_MODEL.md` | 持久字段语义、状态、writer/consumer 边界 |
| `docs/GLOSSARY.md` | 设计名词定义 |
| `FILE_CONTRACT.md` | Agent / CLI 中间工件与 manifest 契约 |
| `docs/ARCHITECTURE.md` | 分层、依赖、模块边界 |
| `docs/PRODUCT-MANUAL.md` | 用户操作与可见产品说明 |
| `openspec/changes/archive/` | 历史原因；不得用于推断当前事实 |

任何交付只更新“被本次变化击中的职责文件”，但**必须执行 Contract Reconciliation**；
发现不同职责文件对同一事实冲突时，不允许按时间戳或个人猜测自动选边。
