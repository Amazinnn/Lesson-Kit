## Why

用户要求单独立项清理学生侧手动选题渠道。当前 `workbench-ui` 已禁止逐题手选，但 Practice page 仍声明允许 Scope、来源/难度筛选和组卷输入。必须先区分既有禁止项的实现遗漏与需要退役的条件组卷操作，避免把新开始页精简误写成保留所有原入口。

## What Changes

- 清点学生可见的选题、筛选、组卷入口及相应操作文档，清理用户确认退役的渠道。
- 用户已要求立项；是否一并移除 Scope、题量和条件组卷控件，仍在提问确认。未确定范围不作为已批准实现契约。
- 保留 Paper 作为练习容器，以及已有试卷的练习、进度和记录；本 change 不授权删除真实题目、试卷或作答记录。
- 与 `free-navigation-paper-practice` 协调开始页，避免重复保留退役控件。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-ui`: learner-facing Paper assembly and selection entry points.

## Impact

当前仅为设计立项，不修改运行时代码。实现前核对 `docs/GLOSSARY.md`、`docs/PRODUCT-MANUAL.md`、`docs/ACTION-GRAPH.md` 与组卷相关 capability；若涉及 Agent/CLI 组卷边界，需先明确并协调对应契约。保留 Shell → Domain → Data，不改变 pipeline、pool scripts 或顶层 CLI 的行为契约。代码事实与现行规范若有冲突，应记录实际入口证据，而不能仅凭本 proposal 推定存在手选控件。
