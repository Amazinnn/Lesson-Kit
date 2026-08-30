# 2026-08-30 remove-candidate-store

## 候选机制物理退役

candidate_problems 自 introduce-check-pipeline（2026-08-30）起停止读取，
表与 CLI 标「待退役」留观察期。观察期内无任何消费者，Check ingest 已是
Agent 内容唯一通道，所有者拍板物理清除。

## 移除内容

- `wb data` 的 `candidate` 实体（CRUD）与仅服务候选的 `gate`/`promote` 动作。
- pull 输出的 `candidates` 字段及 domain/data 层全部候选代码路径。
- 掌握评估中已短路的候选证据分支：证据面只剩正式题、知识点复核、闪卡、微题。
- `pool_schema.py` 不再为新库创建 candidate_problems；ensure_* 不做自动 DROP，
  真实池的物理删除由所有者流程执行（先整池备份）。

## 保留与边界

- `pipeline/scripts/insert-candidates.py` 等 pool/pipeline 脚本按分层铁律不动，
  退役后成为无调用方脚本。
- `content_sequences` CHECK 值域中的 `'candidate'` 保留（避免表重建，无行为影响）。
- knowledge-figures 的 "candidate" 是图布局算法候选项，同名异义，不受影响。
- 学习者信号（learner_signals）不受影响（ADR 0008 仅候选部分被取代）。

## 规格

- `remove-candidate-store`：mastery-evaluation（保守传播 requirement 改述为
  物理移除口径）、review-workbench（pull 短缺与真题覆盖门改指 Check 管线）、
  workbench-content-governance（变异边界去掉 gate/promote 动词）。
- ADR 0008 标注 Superseded；GLOSSARY「候选题」条目改记退役完成。
