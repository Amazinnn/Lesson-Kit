## Why

现行 practice-review 只允许回看紧邻的上一题，主动展示参考答案和解析，并禁止修改自评。学习者需要在同一张卷内反复查看更早的作答，先看自己的答案与判定，再自行展开参考答案，也能修改自评。

## What Changes

- 扩展到当前 Paper 同次 Practice Run 内所有已有作答或“不会”状态的普通题，可以连续前后浏览、反复回看并返回当前题。
- 每次进入某题回看，默认显示题目、原作答、已有判定及自评；参考答案和解析默认收起，必须主动展开。
- 按用户 2026-10-17 的简化决定，在本卷本轮内原位覆盖该次作答上一次自评的分数和评语，不改答案、客观判定或 Attempt 身份。修改不追加反馈、不再次累计学习影响，不重放全库历史或追溯修改后续轮次；首次自评保留原流程。
- 保留当前草稿、试卷独立进度、刷新恢复和 Agent 当前可见题上下文。回看本身不产生学习写入。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- practice-review：多题往返回看、默认隐藏参考答案及自评更改的边界。

## Impact

预期影响 practice-deck.js、practice-flow.js、作答和自评的 Data 写入口及薄 API。实施前审计并优先复用现有持久记录和事务机制。

GLOSSARY 的“作答记录只增不改”及 Agent-only Attempt Correction 不能直接解释为浏览器自评可改。本 change 提出仅自评编辑的增量例外；实施 PR 同步 GLOSSARY、DATA_MODEL、PRODUCT-MANUAL、ACTION-GRAPH，实际受影响时同步 ARCHITECTURE 和 FILE_CONTRACT，不静默放宽 Agent 更正接口。

不修改题目、卷结构、原作答、客观判定、其他卷进度或闪卡导航。本 change 仅完成规划，尚未实现或验收，不依赖 Agent 消息生命周期 change，不执行真实库写入。
