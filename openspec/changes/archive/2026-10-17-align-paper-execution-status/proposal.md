## Why

2026-10-17 的 CO API 对同一 ps-001 返回 count=22 和 progress=19/70。旧执行的 70 项与当前卷的 22 项不匹配，后端 start 会拒绝，列表却仍显示可继续。这是 Data 摘要、API 与 UI 的状态不一致。

## What Changes

- 后端统一核验容器与执行的有序题目身份、版本、题目可用性及清单有效性，返回一致的可继续状态和原因。
- 列表与练习页使用同一结果，不把旧执行进度显示为当前卷进度，不启用后端已经判定不可继续的按钮。
- 当前卷不能暂停时，目标卷单独显示开始阻塞原因，保留目标卷自己的进度。
- 被拒绝的操作重新读取状态，并更新数量、进度、按钮文字和原因，同时保留本地编辑。
- 长题号列表默认折叠；导出、改名和删除分别判断，不因旧执行异常锁住有效容器。
- 保留提交时校验，不自动清除、映射或恢复旧学习记录。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- practice-set-export：保存卷及当前执行的读取状态与实际开始、继续和暂停校验一致。

## Impact

影响 paper_progress、practice_sets、active_practice 及 pages/practice-flow/workbench 的呈现。复用 Data 校验，不在 UI 重建业务规则。同步 PRODUCT-MANUAL、ACTION-GRAPH、DATA_MODEL 与 ARCHITECTURE，名词沿用现有 GLOSSARY。不新增 schema、依赖或 Agent 工件。

CO 的一次性处理另见 docs/audits/2026-10-17-co-paper-resume.md：用户授权保留旧执行历史并启动新版，不能把这次操作当作通用产品修复。
