# 工作台能力成熟度计划集

## 当前状态

实现已按用户要求暂停，当前接力入口为 [2026-11-07 实现交接](HANDOFF-2026-11-07.md)。WP01 仍未完整交付，以下规划基线及原文档交付描述保留为阶段背景。

规划基线 v1，2026-11-07。103 个有效回答，Q001–Q107 中 Q053–Q055/Q071 已撤销。六个 OpenSpec change 已具备 proposal、delta specs、design 和未勾选 tasks。计划按完整课程同步先行组织，用户数据、兼容与跨层约束逐包落实。

本轮交付为设计与实施指导文档。数值 benchmark 是明确的待实测验收门槛，运行时功能及真实学习效果均未由本轮文档工作证明。旧库字段、活跃分支与当前安装在实施开工时按任务重新核对。

## 从这里开始

1. [实施与维护协议](execution-guide.md) 给接手 Agent 的阅读顺序、交付和多轮修订规则。
2. [工作包与依赖](work-packages.md) 给实施顺序及六个 change 的入口。
3. [决策追踪](traceability.md) 将已确认使用需求映射到工作包与验收。
4. [契约协调](contract-reconciliation.md) 登记当前行为与批准目标的差异。
5. [完整交换矩阵](data-exchange-matrix.md) 覆盖内容、附件、学习事实、草稿、偏好和课程学习文件。
6. [可执行 benchmark](benchmarks/catalog.md) 给固定数据集、实际步骤、次数、门槛及证据要求。
7. [外部 Tutor 使用场景](scenarios/external-tutor.md) 给近期主路径与新旧设备往返。

## 工作包

| 顺序 | 工作包 | 实施卡 | OpenSpec |
|---|---|---|---|
| 1 | 全课程文件交换、Git、每小时定时、外部 Tutor | [WP01](packages/wp01.md) | [提案](../../../openspec/changes/expand-file-mediated-course-sync/proposal.md) |
| 2 | 知识点查询、提炼、章节迁移、独立有效写入 | [WP02](packages/wp02.md) | [提案](../../../openspec/changes/mature-course-content-operations/proposal.md) |
| 3 | 审批与成功批次撤销退役 | [WP03](packages/wp03.md) | [提案](../../../openspec/changes/retire-project-approval-gates/proposal.md) |
| 后续 | 消息连续性和极简队列 | [WP04](packages/wp04.md) | [提案](../../../openspec/changes/stabilize-agent-message-continuity/proposal.md) |
| 后续 | 未完成练习和标题渲染 | [WP05](packages/wp05.md) | [提案](../../../openspec/changes/complete-practice-continuity-and-rich-titles/proposal.md) |
| 后续 | 诊断、针对性练习、复习接线 | [WP06](packages/wp06.md) | [提案](../../../openspec/changes/connect-evidence-guided-learning/proposal.md) |

首包内部可分可验证提交，完整接受必须覆盖所有已确认资产和媒介路径。全局审批退役的后续清理不阻挡首包局部直接执行；首包命中的审批先按 S008 去除。内容和消息等后续包可复用首包正常入口，不能复制一套交换机制。

## 原始讨论与依据

- [决策台账](decisions.md) 保存原始回答、修订与依赖，S005–S010 为关键收口。
- [覆盖表](coverage.md) 保存有效问数及取消记录。
- [证据清单](evidence.md) 区分静态核查、历史检查与未验证推断。
- [V3.1 对照](learning-protocol-v3.1.md) 和 [原包](sources/learning-protocol-v3.1.zip) 保留用户提供的学习模式来源。
- [同步场景](scenarios/file-sync.md) 和 [访谈期 benchmark 框架](benchmarks.md) 保存逐轮形成的验收背景，具体执行以 catalog 及对应 change 为准。

## 权威与修订

当前行为归 live OpenSpec，字段归 DATA_MODEL，术语归 GLOSSARY，交换工件归 FILE_CONTRACT，分层归 ARCHITECTURE，用户操作归 PRODUCT-MANUAL，动作归 ACTION-GRAPH。changes 表示批准目标，不能把规划写成程序已实现事实。

每次改变需求先更新决策替代关系、delta 和设计，再同步任务、矩阵、追踪与 benchmark。实现/独立验收/部署各有证据。用户看到精简交付摘要，接手 Agent 获得完整文件树和实际失败信息。
