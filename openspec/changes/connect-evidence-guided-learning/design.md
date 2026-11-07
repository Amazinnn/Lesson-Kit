## Context

诊断、针对性练习与复习接线 follows Q003/Q021/Q028–Q029/Q032–Q041/Q044/Q066/Q074–Q077/Q086–Q091/Q103/Q107，S009. Current implementation evidence, authority ownership and contract drift are recorded in the program's evidence.md and contract-reconciliation.md. The package is independently scoped in packages/wp06.md.

## Goals / Non-Goals

本包目标以 specs/evidence-guided-learning/spec.md 为准。实现边界与文件归属见对应 package 卡，Shell → Domain → Data，Bridge 旁挂。既有可满足的能力直接复用，只修改命中本包的规则、数据和入口。

## Decisions

### 复用分支与证据

接线前对教学分支 registry、session_machine、forms、策略引擎、guardrails/provisioning 和正常入口做调用图。只合入需要且已验证的能力，不复制第二套状态机。DATA_MODEL 学习状态、Attempt、评价和排期是既有持久语义；V3.1 的教学用语是判断，不直接覆盖字段枚举。

外部 Tutor 通过 WP01 的目标、资料、原始作答、误解记录及续接文件获得上下文。Agent 判断以 evidence 原始事实为依据，材料“讲过”不产生掌握。学生自述作为自述依据，和独立新题表现分开。原文/推导/补充可内部追溯，默认不加来源或理由面板。

### 流程策略

目标明确则直接使用，模糊对象用一句澄清。专题小诊断、代表题应用；完整新章按知识图谱分段诊断，15–25是可缩减的累计范围。优先已有真题/题库，缺答案可有依据推导并保留来源，不伪造原书解析。用户求助才给渐进提示，用户“继续”立即推进，用户纠正诊断立即改变安排。

维护主线位置、插问返回点、待补内容、真实时间与预算，短消息承载当前步骤，持久课程文件承载详细记录。Normal/Fast/Rescue 可复用策略，但必须基于真实时间和显式目标，协议里的宿主降级方案不能自动成为后端 fallback。

复习通过既有合法 writer，主观批改不能自动重放评分与排期。未见新题的独立应用和少无关题是核心指标，模拟学习者的流程结果不当作真实用户学习收益。

## Risks / Trade-offs

- 旧库和活跃 change 可能与静态阅读不同。开工以当前 checkout、真实 schema 和正常入口重新核对，记录差异，不以历史任务勾选覆盖实际结果。
- 跨层职责冲突在被命中范围内修正，并同步对应职责文件；避免为本包启动无关全仓重构。
- 部分成功必须准确表达，单元内错误不能产生半条实体或静默默认值。对未知行为保留真实失败，按 AGENTS 审查任何 fallback。
- 数值门槛由工程规划选择，尚未实测。以 LEARN-01–05、LP-03–06 固定夹具建立基线后公开实际结果，不虚报当前性能。

## Migration Plan

1. 冻结旧数据和接口样本，登记本包每个受影响字段及旧状态。
2. 首先完成旧 requirement 的同职责 delta 协调及失败回归检查，再改产品实现。
3. SQLite 变更仅通过 ensure_* 增量迁移，副本升级后验证原内容、历史及引用。
4. 受影响文件工件更新 FILE_CONTRACT、字段更新 DATA_MODEL、名词更新 GLOSSARY、入口更新 ACTION-GRAPH/surface/手册与 Agent 契约。
5. 真实入口和仓库检查通过后，按 S008 直接执行已准备切换，并记录安装/运行身份。数据故障以可恢复备份和直接修正处理，成功批次撤销已退役。
6. 任务只按实际证据勾选，完整验收交接使用 execution-guide.md 和 benchmarks/catalog.md。
