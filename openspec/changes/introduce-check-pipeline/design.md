# introduce-check-pipeline 设计

## D1 定名与口径

DISCUSSION-RECORD 专题 22 五答为准：定名 Check；回滚挂 ingest 子命令族；
首期产出链闪卡+微题（综合题配方 = spec 未来段，本变更不立）；candidate_
problems 退役（读路径停、表与 CLI 保留标待退役）；产出入口对话桥结构化
动作（CLI 通道照旧可用）。

## D2 批次 id

可读顺序 id `batch-NNN`，复用 `content_sequences` 机制（新增 pool 级
scope，跨批次全局递增）；禁哈希（openspec 硬规则）。分配发生在 apply
事务内（`BEGIN IMMEDIATE` 持锁期间），天然原子。

## D3 schema（additive）

- `ALTER TABLE problems ADD COLUMN ingest_batch_id TEXT`
- `ALTER TABLE flash_cards ADD COLUMN ingest_batch_id TEXT`
- 新表 `ingest_batches(batch_id TEXT PRIMARY KEY, kind TEXT NOT NULL,
  manifest_path TEXT NOT NULL, counts_json TEXT NOT NULL, backup_path TEXT
  NOT NULL, applied_at TEXT NOT NULL, rolled_back_at TEXT)`
- 全部进 `pool/scripts/pool_schema.py` 的 `ensure_workbench_schema`，幂等；
  不 DROP、不改既有列。

## D4 跨 lane 契约（Lane A 提供，CLI 与桥消费）

- `workbench.ingest.apply_batch(pool, manifest, *, source) -> dict`
  （source ∈ {"cli", "bridge"}；返回 batch_id / kind / counts /
  backup_path）。内部：门禁重验 → 批次 id 分配 → manifest 快照写
  `pool/ingest/<batch_id>.json` → 可恢复备份 → 单事务插行（带批次戳记）
  → 登记 ingest_batches。
- `workbench.ingest.rollback_batch(pool, batch_id) -> dict`（返回 deleted /
  backup_path / accounting）。内部：批次存在且未滚 → 依赖检查 → 新备份 →
  单事务删 `WHERE ingest_batch_id=?` → 记 rolled_back_at。
- 两个函数不依赖 CLI 参数结构；`conversations.py` 可直接 import（依赖方向
  conversations → ingest → conversation_providers，无环）。
- 既有 apply_micro_quiz / apply_flash_cards / apply（problems）内部改走
  同一批次逻辑；CLI `recipe --apply` 对外行为不变（多记一笔批次）。

## D5 回滚依赖拒绝

批次内容行被练习/反馈记录引用时拒绝整批回滚（防静默删除学习资产）：
检查 problem_attempts、problem_progress、feedback_events、review_schedule、
learner_signals 对批次行的引用；命中即失败并列出阻塞项，零删除。这与
治理 spec「物理删除级联」不冲突——显式单题删除照旧级联，批次回滚是
批操作，宁可拒绝不可吞掉学习记录。

## D6 桥动作链

- 意图门：前端 `aiContextBody` 依 check_intent 正则（出题/补池/加题/入库
  等显式动词，宁缺毋滥）→ `context.build()` 透传。
- `_extract_action` 新分支：type=check_ingest；结构校验（kind ∈
  {flash-card-patch, micro-quiz-patch}、items 非空列表）。通过 → turn
  完成处理内服务端执行 apply_batch（同步、sqlite 快）；失败（坏 JSON/
  结构不符/门禁拒收）→ turn 携带显式错误——本动作不再静默丢弃。
- 前端 `aiApplyAction` 新分支：成功 → 独立结果卡片（批次号/类型/计数/
  备份路径/回滚按钮）；门禁失败 → 逐条原因错误卡片。回滚按钮 confirm
  后 POST 回滚端点，成功后卡片翻转「已回滚」并刷新版面计数。
- 回滚端点：`POST /api/w/{name}/ingest/rollback`（body {batch_id}），
  handler 复用 `_request_object`+`ApiError` 模式，调 rollback_batch。

## D7 candidate 退役读路径

- `workbench/data/pool.py` gate_passed_candidates：停用（pull 不再并入）。
- `workbench/data/mastery.py`：停读候选与 candidate_attempts。
- `workbench/data/queries.py`：hub 统计去候选数。
- CLI candidate 子命令与表保留；L3 标「待退役」随 PR3 留痕。

## D8 意图正则取向

误触发代价 > 漏触发代价（漏了还能 CLI；误触发会写池）。正则只覆盖显式
出题动词，实现时补用例（普通「练习」「复习」不触发）。
