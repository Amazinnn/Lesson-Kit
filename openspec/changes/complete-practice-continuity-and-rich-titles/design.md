## Context

未完成练习与标题呈现 follows Q048–Q050/Q052/Q056–Q058/Q060–Q061/Q064，S004/S005/S008. Current implementation evidence, authority ownership and contract drift are recorded in the program's evidence.md and contract-reconciliation.md. The package is independently scoped in packages/wp05.md.

## Goals / Non-Goals

本包目标以 specs/practice-continuity-presentation/spec.md 为准。实现边界与文件归属见对应 package 卡，Shell → Domain → Data，Bridge 旁挂。既有可满足的能力直接复用，只修改命中本包的规则、数据和入口。

## Decisions

### 未完成执行

继续已有 active_practice、paper_progress、draft_sequence 和本地出站箱。开始页枚举全部未完成 Paper 执行，无额外300条缓存池或自动淘汰。再次打开同 Paper继续既有执行。清除仅针对 execution_id 和其草稿，不删除 Paper、题目或已提交记录。为清除后的晚到写入建立终止身份/当前版本校验，刷新不能从旧本地草稿复活。

### 标题原文和显示

建立 title-field-surfaces 清单，列字段 writer、存储、列表/详情/练习/历史显示及重命名回读。显示统一安全 richText，编辑初值从原字段读取，禁止 heading.textContent 或 KaTeX辅助文本回填。每字段覆盖强调、行内/块公式、长标题、特殊字符和原样保存。保留当前 Markdown 原始写法，不重做已有正文编辑器。

### 交互安全

运行中当前输入表面在非空/IME/未确认写入时按现有机制延后刷新，其他内容可更新。自然节点使用真实提交/切题完成状态，不以固定 timeout 猜测安全。恢复 last course 与执行位置时以身份和可恢复状态验证，显式启动目标优先。

## Risks / Trade-offs

- 旧库和活跃 change 可能与静态阅读不同。开工以当前 checkout、真实 schema 和正常入口重新核对，记录差异，不以历史任务勾选覆盖实际结果。
- 跨层职责冲突在被命中范围内修正，并同步对应职责文件；避免为本包启动无关全仓重构。
- 部分成功必须准确表达，单元内错误不能产生半条实体或静默默认值。对未知行为保留真实失败，按 AGENTS 审查任何 fallback。
- 数值门槛由工程规划选择，尚未实测。以 PRACTICE-01–04 固定夹具建立基线后公开实际结果，不虚报当前性能。

## Migration Plan

1. 冻结旧数据和接口样本，登记本包每个受影响字段及旧状态。
2. 首先完成旧 requirement 的同职责 delta 协调及失败回归检查，再改产品实现。
3. SQLite 变更仅通过 ensure_* 增量迁移，副本升级后验证原内容、历史及引用。
4. 受影响文件工件更新 FILE_CONTRACT、字段更新 DATA_MODEL、名词更新 GLOSSARY、入口更新 ACTION-GRAPH/surface/手册与 Agent 契约。
5. 真实入口和仓库检查通过后，按 S008 直接执行已准备切换，并记录安装/运行身份。数据故障以可恢复备份和直接修正处理，成功批次撤销已退役。
6. 任务只按实际证据勾选，完整验收交接使用 execution-guide.md 和 benchmarks/catalog.md。
