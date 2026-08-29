# introduce-check-pipeline 任务

## 1. 规格与名词（PR1）

- [x] DISCUSSION-RECORD 专题 22（立项五答 + cloze 澄清）
- [x] PENDING-DEFINITIONS：generate 桥条目升级迁移标注、Agent 组织面板了结
- [x] GLOSSARY：Check 管线 / 出题入库动作新词条，批次 id / 整批回滚升级，
      候选题退役注记、闪卡条目旧称更新
- [x] workbench-content-governance delta（rollback 命令 + 批次溯源与整批
      回滚 + 写边界承认桥通道）
- [x] flash-card / micro-quiz-content delta（ingestion 批次戳记）
- [x] ai-teacher-bridge delta（check ingest action）
- [x] review-workbench / mastery-evaluation delta（候选退役读路径）
- [x] `openspec validate introduce-check-pipeline --strict`

## 2. 实现（PR2）

- [x] schema additive（ingest_batch_id 列 ×2 + ingest_batches 表 + 迁移测试）
- [x] Lane A：apply 三配方批次戳记 + manifest 快照落盘 + rollback_batch +
      `wb ingest rollback` 子命令 + 测试（整库 snapshot 回滚范式、依赖
      拒绝、双滚拒绝、未知批次）
- [x] Lane B：check_intent 透传 + _extract_action 分支与显式错误 + 回滚
      端点 + 测试（意图门/坏 JSON/结构不符/门禁拒收各一例）
- [x] candidate 退役读路径（pull/mastery/queries + 测试：种 gate_passed
      候选不出现在练习与掌握）
- [x] 前端结果卡片/错误卡片/回滚按钮 + node 测试
- [x] 集成缝合：桥动作全链（对话→门禁失败→成功→回滚）pytest + node 全绿

## 3. 走查与归档（PR3）

- [x] 3091 隔离副本走查：CLI apply→计数核对→rollback→还原；桥对话出题→
      成功卡片→版面出现→回滚→还原；坏 manifest→错误卡片零写入；
      候选退役核对；截图清单
- [x] PRODUCT-MANUAL 第 8 章（Agent 何时可入池+批次安全网）、第 9 章
      （唯一合法写池通道口径改写）
- [x] ACTION-GRAPH L1/L2/L3/L4 同步 + 末尾留痕；候选动作标待退役
- [x] changelog + 归档本变更 + 交接文档更新
- [x] 基线：pytest / node / `openspec validate --specs --strict` / 双 guard
