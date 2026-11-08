## Context

内容与知识点能力成熟化 follows Q006/Q010–Q012/Q039–Q045/Q059–Q062/Q078–Q079/Q084–Q096/Q098/Q103–Q104. Current implementation evidence, authority ownership and contract drift are recorded in the program's evidence.md and contract-reconciliation.md. The package is independently scoped in packages/wp02.md.

## Goals / Non-Goals

本包目标以 specs/knowledge-content-operations/spec.md 为准。实现边界与文件归属见对应 package 卡，Shell → Domain → Data，Bridge 旁挂。既有可满足的能力直接复用，只修改命中本包的规则、数据和入口。

## Decisions

### 查询与分类

在既有 data 命令增加可组合的 `--knowledge-type`、`--chapter` 与正文关键词过滤，参数映射由薄 CLI 完成。Data 返回基础知识点投影；经验与来源加入检索索引/查询范围，返回实体去重。题目关联查询重用 problems_for_kps，任一知识点命中即可。沿用现有 AND 关键词习惯，不增加向量服务或模型查询依赖。

### 新模型与章节迁移

复用 content-bundle 的 knowledge_points、本地 key 及正式关系入库。Agent 先查已有内容与经验再补充或新建，单模型默认正文容纳条件、公式和步骤。范围内持续授权支持提炼，写入回执作为事实依据。新模型自动给适用原题追加 kp_ids，既有有效关联保留。分类补齐仅在用户指定范围，存疑原状。

章节归属从稳定 ID 中解耦，采用 ensure_* 增量列，旧 ID 通过既有前缀回填初始章；新读写以列为当前归属，旧 ID继续可解析。所有通过 ID 推章的查询、图谱、导出及 prompt 必须改用当前归属。知识点历史、关系和经验以稳定 ID 连续，不删建换号。跨课程迁移不在本行为定义中。

### 批量内容

将 manifest 预检产出拆为独立有效单元，互相引用的新实体共享单元。原文损坏、图片缺失、错误引用等阻断该依赖单元；其他有效单元可写。每单元用现有事务、备份和操作身份，重试去重。保留批次 provenance，退役成功批次撤销入口和旧 rollback UI 提示。旧 rolled_back 历史可读，不复活已删除内容。

只重构被命中的业务规则/IO边界。预防来源归属错误需要结构预检加学术语义核对，后者使用已给原文和免费测试模型验证，禁止加载本机决策模型。

## Risks / Trade-offs

- 旧库和活跃 change 可能与静态阅读不同。开工以当前 checkout、真实 schema 和正常入口重新核对，记录差异，不以历史任务勾选覆盖实际结果。
- 跨层职责冲突在被命中范围内修正，并同步对应职责文件；避免为本包启动无关全仓重构。
- 部分成功必须准确表达，单元内错误不能产生半条实体或静默默认值。对未知行为保留真实失败，按 AGENTS 审查任何 fallback。
- 数值门槛由工程规划选择，尚未实测。以 DATA-01–05、CONTENT-01、FLOW-03 固定夹具建立基线后公开实际结果，不虚报当前性能。

## Migration Plan

1. 冻结旧数据和接口样本，登记本包每个受影响字段及旧状态。
2. 首先完成旧 requirement 的同职责 delta 协调及失败回归检查，再改产品实现。
3. SQLite 变更仅通过 ensure_* 增量迁移，副本升级后验证原内容、历史及引用。
4. 受影响文件工件更新 FILE_CONTRACT、字段更新 DATA_MODEL、名词更新 GLOSSARY、入口更新 ACTION-GRAPH/surface/手册与 Agent 契约。
5. 真实入口和仓库检查通过后，按 S008 直接执行已准备切换，并记录安装/运行身份。数据故障以可恢复备份和直接修正处理，成功批次撤销已退役。
6. 任务只按实际证据勾选，完整验收交接使用 execution-guide.md 和 benchmarks/catalog.md。
