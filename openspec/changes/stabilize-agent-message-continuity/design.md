## Context

消息连续性与极简发送队列 follows Q022/Q025–Q027/Q030/Q042–Q043/Q046–Q047/Q051/Q065/Q069–Q072，S005/S008. Current implementation evidence, authority ownership and contract drift are recorded in the program's evidence.md and contract-reconciliation.md. The package is independently scoped in packages/wp04.md.

## Goals / Non-Goals

本包目标以 specs/agent-message-continuity/spec.md 为准。实现边界与文件归属见对应 package 卡，Shell → Domain → Data，Bridge 旁挂。既有可满足的能力直接复用，只修改命中本包的规则、数据和入口。

## Decisions

### 提交身份与历史

沿用 submission_id、原始/当前文本、捕获上下文和 linked retry。前端状态只投影服务端接受事实，排队列表是同一消息的待处理视图，不能创建第二份历史消息。原失败消息和实际部分输出留在流中，编辑重发使用新关联身份与原对象上下文。未知送达先核对同一身份，不能直接生成另一个发送。

显式停止后服务端暂停整个待处理队列，直到既有会话级继续入口。普通执行失败不自动入重试，独立后项按现有流程继续。异常重启保留 never-started 项并暂停，恢复不自动执行 provider。无需新增任务/DAG/依赖识别系统。

### 极简表面

aiRenderPendingQueue 和 aiRenderOutbox 都进入逐路径检查。常态队列仅正文、编辑、删除；移除排序/立即发送/字段详情。继续采用既有会话级入口，失败恢复沿对话内用户显式动作，普通队列不增加按钮。编辑/删除提交仍校验 revision，晚到响应不能改运行消息。

捕获课程和题目在发送时持久，导航只改变后续新消息上下文。等待只用短状态与停止，不显示原因面板。重复发送需复现 UI重复与真实重复操作两种情况，以接受次数及写入次数证明修复。

## Risks / Trade-offs

- 旧库和活跃 change 可能与静态阅读不同。开工以当前 checkout、真实 schema 和正常入口重新核对，记录差异，不以历史任务勾选覆盖实际结果。
- 跨层职责冲突在被命中范围内修正，并同步对应职责文件；避免为本包启动无关全仓重构。
- 部分成功必须准确表达，单元内错误不能产生半条实体或静默默认值。对未知行为保留真实失败，按 AGENTS 审查任何 fallback。
- 数值门槛由工程规划选择，尚未实测。以 CHAT-01–05 固定夹具建立基线后公开实际结果，不虚报当前性能。

## Migration Plan

1. 冻结旧数据和接口样本，登记本包每个受影响字段及旧状态。
2. 首先完成旧 requirement 的同职责 delta 协调及失败回归检查，再改产品实现。
3. SQLite 变更仅通过 ensure_* 增量迁移，副本升级后验证原内容、历史及引用。
4. 受影响文件工件更新 FILE_CONTRACT、字段更新 DATA_MODEL、名词更新 GLOSSARY、入口更新 ACTION-GRAPH/surface/手册与 Agent 契约。
5. 真实入口和仓库检查通过后，按 S008 直接执行已准备切换，并记录安装/运行身份。数据故障以可恢复备份和直接修正处理，成功批次撤销已退役。
6. 任务只按实际证据勾选，完整验收交接使用 execution-guide.md 和 benchmarks/catalog.md。
