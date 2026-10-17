## Why

现有 attempt 状态迁移将父表临时改名，SQLite 随之把子表外键改成 `problem_attempts_widening_old`，随后临时表被删除。正式 CO 库已存在这种悬空外键，且内存数据库调用原函数能够复现。该结构缺陷需要与试卷生命周期设计分开修复。

这证明外键重写有问题，但没有证明该迁移删掉了 CO 的 19 条作答。真实数据缺失的来源和恢复必须保持为独立证据问题。

## What Changes

- 使 attempt 状态迁移在保留全部行、字段、ID、关联关系及非目标结构的同时，保持子表外键指向有效父表。
- 为已经指向临时父表的池提供明确、可重复执行的结构修复路径，不自动编造缺失父记录。
- 健康池迁移后要求外键检查通过；已有缺失数据必须被准确报告，不能把修正外键目标当成恢复作答。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-content-governance`: lossless schema migration and explicit diagnosis of legacy dangling attempt references.

## Impact

Implementation is limited to the existing authorized `pool/scripts/pool_schema.py` ensure/migration boundary and relevant regression checks/documentation. No frozen pipeline behavior change, automatic real-pool migration or production repair is included. Coordinate its healthy legacy migration acceptance with the Paper progress change.
