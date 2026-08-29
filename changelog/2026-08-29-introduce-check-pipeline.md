# 2026-08-29 — introduce-check-pipeline（队列④ Check 管线）

## 交付

一个 OpenSpec change（PR #33 规格 + PR #34 实现 + PR3 走查归档），
DISCUSSION-RECORD 专题 22 记录立项五答。

- **定名 Check**：generate 桥 → Check 管线（所有者确认，强调校验准入）；
  PENDING 条目迁移标注、「Agent 组织面板」挂名了结。
- **批次溯源**：三个 recipe apply（micro-quiz / flash-card / problems 正式回填）
  统一记批次 id（`batch-NNN`，content_sequences pool 级 scope 取号，禁哈希），
  内容行戳 `ingest_batch_id`，manifest 快照落 `<db目录>/ingest/<batch_id>.json`，
  登记 `ingest_batches`（kind/counts/backup_path/applied_at/rolled_back_at）。
  schema additive：两列一表 + content_sequences CHECK 扩宽 `batch`（数据保留）。
- **整批回滚**：`wb ingest rollback --batch <id>` + 桥结果卡回滚按钮 +
  `POST /ingest/rollback`，三个入口同源 `rollback_batch`：校验批次存在、
  未滚过、无练习/反馈依赖（命中逐条列出），回滚前自动备份，单事务删行。
- **桥结构化动作 `check_ingest`**（首个桥内池写）：出题/补池意图
  （check_intent 正则，宁缺毋滥）→ 内联 manifest → 服务端过既有门禁 →
  批次 apply → 独立结果卡片进对话流；门禁失败逐条显式呈现、零写入
  （仅本动作改变坏 JSON 静默丢弃行为）；transcript 携带 action，
  会话重渲染还原结果卡。
- **candidate_problems 退役**：pull/mastery/hub 停读候选与候选尝试；
  表与 `wb data candidate` 子命令保留标**待退役**，不 DROP；
  pull 返回形状兼容（candidates 恒空列表）。

## 验证

- 全量 pytest 333 通过（基线 310；批次往返/依赖拒绝/双滚拒绝/CLI 负例/
  意图门/端点/退役语义等新增），Node UI 90 通过（基线 87）。
- `openspec validate --specs --strict`：11 passed。
- scratch 走查（真实池副本 + 隔离注册表 + 端口 3091 + stub provider）：
  真实库结构迁移幂等（4 项 additive）；CLI apply→批次登记/行戳记/快照/
  备份→rollback→66 卡还原；CLI 负例（双滚/未知批次）如实报错；
  桥对话出题→batch 卡片→闪卡会话出现新卡（pull-cards 含 fc-901~903）→
  UI 回滚→卡片翻转「已整批回滚（撤销 3 行）」→池还原；
  门禁失败（重复 id）→「入库未执行」卡片逐条原因、零写入；
  刷新后卡片从 transcript 还原；gate_passed 候选在 pull 中不再出现。
  截图自检清单 4 张。

## 走查发现并当场修复

- 桥内 apply 撞固定备份名（FileExistsError 曾崩 turn 线程、turn 永远
  running）→ apply_batch 增 backup_path 参数，桥按 会话-turn 传唯一名。
- 回滚默认备份名固定 → 同池第二次回滚必拒 → 名字带批次 id。
- 结果卡片把布尔 applied 当计数显示 → 改读 counts；备份只显示文件名。

## 遗留（显式后续项）

- 综合题（大题）AI 出题配方：问卷已勾意愿，留 Check 管线后续期
  （spec 未来段，不复用本期两种 kind）。
- candidate_problems 物理清理（DROP 表 + data candidate 子命令移除）：
  待退役观察期后另办。
- cloze 挖空批量拆卡：闪卡 spec 未来段（专题 22 已向所有者澄清概念来源）。
