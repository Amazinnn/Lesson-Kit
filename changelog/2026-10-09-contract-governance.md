# 契约治理 PR #98 当前核对

2026-10-09 对照远端 main `000db53` 核对字段职责。此记录为本次交接，10 月 1 日审计快照保持原文。

- 合入当前 main；保留知识点练习、题目主题分组退役与 Markdown 分隔线等既有成果。
- DATA_MODEL 将 `problems.topic_label` 标为 unresolved：#106 的 CRUD 与迁移已退役，但 micro-quiz-content spec、FILE_CONTRACT、旧 GLOSSARY/ARCHITECTURE 以及 bridge 的内容提示仍请求它。后续以 `reconcile-problem-topic-retirement` 协调已批准的退役，不在 #98 偷改行为；闪卡同名字段仍保留。
- 明确 `ingest_batch_id` 是受治理 ingest/apply 来源批次：兼容的 `problems` recipe 更新已有行时会覆盖该列，problem-patch 与直接编辑不保证覆盖；不把它当通用最后修改标记。此次不改实现。
- GLOSSARY 定义契约权威、契约漂移与契约协调。
- 图片命名、display_summary、graph_label、related_kp_ids 新写入职责及 schema 重建边界仍待独立决策；不得借治理文档改变行为。

验证结果由本次 PR 的检查与后续收尾交接记录承载；未通过的检查不声明完成。
