# PR 与 OpenSpec 收尾

PR #98 已独立审查、通过 PR 与合并提交 CI，合并为 `f0379cf`。
其余批准功能在隔离分支整合：搜索/来源过滤、关闭自评、试卷预览与折叠、
存储解析显示、数学渲染、只读排版 advisory，以及已声明入池批次契约修复。
#110 内容镜像不在本次范围。

## 验证

独立最终验收固定代码提交 `356ceef`：Python **880**、Node **140** 全通过；
compileall、提取 guard、前端 npm ci/build 通过。归档前 strict 校验27项，
归档后当前14个 live specs 与2个 active changes 共 **16项通过**。
前端构建只生成的3个 tracked dist 文件已还原，没有扩展前端实现范围。

真实 Edge 浏览器在私有注册表与课程副本验证：折叠/记忆、真实数学预览、
同页自评切换、来源过滤、进行中模式稳定、客观 off 单次尝试/折算而无评分、
单向/双向 off 闪卡完成归档且刷新不复活。旧经验页所需既有迁移只在副本执行；
首次副本缺经验表的失败与补验均保留，未宣称未经迁移的实池已升级。

c02/ncmc 实池以 SQLite只读访问，apply、拒收、ensure、rollback仅在临时副本。
独立回归证明原内容/学习行与注册表不变；真实源数学与客户端/服务端一致。
四门课程副本保留2003条历史标签及学习行，实池写入0。
没有重跑历史数据修复、猜测答案/批次、删除题目/图片或迁移真实课程。
原始工作区的未提交修改、运行状态与备份产物保留。

## 归档与剩余工作

使用 OpenSpec CLI 归档11个 change：content-dedup-and-audit、
show-micro-quiz-explanation、problem-search-and-origin-filter、
practice-set-item-preview、rating-toggle-setting、reconcile-problem-topic-retirement、
preserve-legacy-problem-label-values、kp-text-typesetting-check、
implement-kp-text-typesetting-check、verify-ingest-conformance、ads-pool-content-repair。
机械归档冲突通过刷新完整 MODIFIED block 保留新增场景解决，没有跳过校验。

`ads-answer-gap-repair` 保持活动：零缺键/旧键未动/即时学习表全等的原验收
缺乏证明，具体任务已重开；当前1条不可判定编程题和108项审计发现如实记录。
`ingest-integrity-and-observability` 保持活动：新能力与冻结层决策仍待定；
排版 §5–6 的延期/外部课程工作已转入其 §9，未标记实现。

字段默认保留历史存储，仅退役新写入与使用；未来物理删除须明确迁移与恢复
验收，未推断实际删除授权。后续实池升级先核对备份和副本结果。
