## Why

计算机组成的同一批 70 道题在修正题型时被重新建成另一批题号；原卷已更新为 22 题，旧执行仍引用已经消失的 70 个题号。试卷容器、题目身份、执行进度和学习证据之间缺少明确的更新边界，切卷还会丢失可继续的状态。

所有者已确认：各卷独立保存未完成进度及草稿，不要求串行完成；修题保留题号，删卷保留题目和历史学习记录。定义见 GLOSSARY 的 Paper、Practice Run、Paper Execution Progress；事实证据与逐项决策见 `docs/audits/2026-10-17-paper-agent-investigation.md`。

## What Changes

- 每张保存的 Paper 独立持久化一份未完成执行；切卷只暂停，刷新或重启后可继续，当前选中卷不限制未完成卷数量。
- 保留 Paper ID 更新原卷；手动增删、替换、重排题目先展示影响并确认，再清该卷进度；改标题/说明不清进度。
- 保留题目 ID 修正内容。影响作答/判分的变化仅重置各未完成卷中的该题，保留其他题及历史作答；元数据变化不重置。
- 按每题实际内容类型呈现选择、判断、开放题，旧整卷模式不能把客观题强制变成自由作答。
- 删卷只删容器与未完成进度；删题自动清当前引用，但保留其他题进度、历史学习证据和历史轮次。
- 区分可读取/可修复的容器与可开始执行的卷；缺失引用不得让原卷从列表静默消失或无法删除/修复。
- 所有相关提交核验当前卷和题目版本，防止旧页面提交到已经变化的内容。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `practice-set-export`: stable container identity, explicit existing-target updates and independent deletion.
- `review-workbench`: per-Paper durable progress, pause/resume, scoped reset and historical evidence preservation.
- `micro-quiz-content`: per-item rendering and type correction without identity replacement.
- `workbench-content-governance`: coordinated in-place edits and question deletion across current references.

## Impact

Implementation will touch Data-owned Paper storage/execution/content writers, thin CLI/API adapters and practice UI. Reuse `update_saved`, `problem-patch`, existing attempt/feedback paths and existing type renderers. No new dependencies, no hash identity, no pipeline contract expansion. Future implementation must reconcile DATA_MODEL, FILE_CONTRACT where affected, Architecture, Product Manual, Action Graph and live specs in the same PR. This proposal does not change those current implementation facts or repair the real CO database.
