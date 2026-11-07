## Context

审批与显式批次撤销退役 follows Q098/S008，协调 Q031/Q057/Q062/Q067 旧批准要求. Current implementation evidence, authority ownership and contract drift are recorded in the program's evidence.md and contract-reconciliation.md. The package is independently scoped in packages/wp03.md.

## Goals / Non-Goals

本包目标以 specs/direct-project-actions/spec.md 为准。实现边界与文件归属见对应 package 卡，Shell → Domain → Data，Bridge 旁挂。既有可满足的能力直接复用，只修改命中本包的规则、数据和入口。

## Decisions

### 直接动作

沿原已验证 Paper update 路径执行动作，移除“提议→等待点击→再次写入”的产品状态。当前目标和版本仍在真正提交点重新读取并校验，自动刷新可安全重建的计划，真实输入不足如实返回，不造参数。删除 approval 引起的 composer 替换、队列暂停和 dispatch 拒绝；保留用户主动停止导致的暂停。

旧 pending_paper_approval 通过一次迁移读取 workspace/conversation/turn/Paper/operation revision。已执行操作只标记消费；仍有效且未执行的操作按原身份直接执行；目标已不存在或不再对应原输入时记实际未完成结果，不能换一个 Paper 代写。实际状态通过既有 turn/artifact 保存，迁移重复运行不重复写。

Paper 改卷保持原容器及未受影响草稿。结构变化的内容协调复用当前 Data 生命周期，所需精细保留按已有批准目标修正。重做是用户已经选择的动作，不再询问第二次。准备后切换直接执行，验证 source_root 与迁移结果。

显式成功批次 undo 已由内容包退役，删除审批层的旧回滚卡及调用提示；灾难备份恢复和失败单元一致性处理归各数据契约，不用退役命令执行。

## Risks / Trade-offs

- 旧库和活跃 change 可能与静态阅读不同。开工以当前 checkout、真实 schema 和正常入口重新核对，记录差异，不以历史任务勾选覆盖实际结果。
- 跨层职责冲突在被命中范围内修正，并同步对应职责文件；避免为本包启动无关全仓重构。
- 部分成功必须准确表达，单元内错误不能产生半条实体或静默默认值。对未知行为保留真实失败，按 AGENTS 审查任何 fallback。
- 数值门槛由工程规划选择，尚未实测。以 FLOW-01–03、RELEASE-02 固定夹具建立基线后公开实际结果，不虚报当前性能。

## Migration Plan

1. 冻结旧数据和接口样本，登记本包每个受影响字段及旧状态。
2. 首先完成旧 requirement 的同职责 delta 协调及失败回归检查，再改产品实现。
3. SQLite 变更仅通过 ensure_* 增量迁移，副本升级后验证原内容、历史及引用。
4. 受影响文件工件更新 FILE_CONTRACT、字段更新 DATA_MODEL、名词更新 GLOSSARY、入口更新 ACTION-GRAPH/surface/手册与 Agent 契约。
5. 真实入口和仓库检查通过后，按 S008 直接执行已准备切换，并记录安装/运行身份。数据故障以可恢复备份和直接修正处理，成功批次撤销已退役。
6. 任务只按实际证据勾选，完整验收交接使用 execution-guide.md 和 benchmarks/catalog.md。
