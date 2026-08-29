# introduce-flash-card 提案

## Why

所有者澄清（2026-08-29）：当前实现中名为「闪卡 flash_card」的练习模式其实是
微题（micro quiz）的卡片式渲染——短题干、揭示「答案+为什么」、自评——并非
所有者心中独立的 Flash Card 功能（辅助记忆的键值对小卡片，背单词/背概念场景，
从知识点内容解构而来）。同名两物已造成心智模型冲突。同时微题的定位被澄清为
「选择题（单选/多选）+ 判断」，而现契约中的 `short_answer`/`closest_answer`
以填空大文本框作答，与定位不符；练习会话开始后中间栏仍堆满目标卡与备练
列表（UX 清单「练习会话注意力不聚焦」）。

本变更一次解决四件事：

1. **正名**：现有微题卡片模式改名 `micro`（小测），`flash_card` 这个名字让给
   新的真·闪卡功能。闪卡定义经所有者本轮确认，走「先定义后使用」流程
   （GLOSSARY 新条目先于本提案落档）。
2. **闪卡最小实现**：Anki Note/Card 两层模型的最小版——知识点是唯一事实源
   （Note），闪卡是从知识点解构出的键值对问答卡（Card：front→回忆→back→
   1–5 自评，无判分），作为练习会话第四种模式，复用既有选区、调度与自评机制。
3. **micro 收敛**：微题题型集收窄为 single_choice / multiple_choice / yes_no，
   微题一律点选作答；既有 4 道 short_answer 题删除重制为单选（内容 PR）。
4. **会话聚焦**：任何模式开始会话后，中间栏收敛为练习流，会话结束恢复。

## What Changes

- 练习模式从三种变四种：`exam`（综合题）、`micro`（小测，原 flash_card
  改名）、`yes_no`（判断）、`flash_card`（闪卡，新功能，数据来自
  `flash_cards` 表而非题目池）。
- 新增 additive 表 `flash_cards(card_id, kp_id, front, back, source_evidence)`
  （恰 5 字段）与 `wb ingest recipe flash-card`（kind=`flash-card-patch`，
  确定性门禁 + 可恢复备份 + 单事务 apply）。
- 新增 `/pull-cards`：按选区知识点过滤、到期优先；卡片自评走既有 `/feedback`
  （`item_type='card'`），每卡独立调度行（direction 键留空备用，本期不启用）。
- 微题契约收窄：移除 `short_answer`/`closest_answer`（门禁显式拒绝）；
  微题渲染一律选项点选，选项类题目不再显示自由文本作答框。
- 会话聚焦：开始练习后隐藏学习安排区（目标卡/准备列表/建议/模式选择/
  时间视图），中间栏只留练习流；耗尽/结束/刷新恢复分支同步处理。
- 数据迁移：`practice_modes` 值 `flash_card`→`micro` 幂等 REPLACE；
  真实池 4 道 short_answer 题重制（内容 PR，备份先行）。

## Capabilities

### New Capabilities

- `flash-card`：闪卡内容契约（5 字段键值对卡、知识点为唯一事实源、
  一卡一原子事实）、可组合入池配方与门禁、第四模式练习语义（正面→回忆→
  揭示→自评、双自评时机、session-end 卡片条目、无重复）、每卡独立调度行。
  leech 闭环 / cloze 自动拆卡 / 反向卡记入未来段，本期不实现。

### Modified Capabilities

- `micro-quiz-content`：题型集收窄三种；模式改名 micro 口径
  （REMOVED+ADDED 显式标注）；渲染一律点选。
- `workbench-ui`：四种 content mode；会话聚焦行为。
- `daily-learning-plan`：练习路径变四条（exam / Micro / Yes-No / Flash Card）。

## Impact

代码集中：`pool/scripts/pool_schema.py`（建表 + 幂等迁移）、
`workbench/domain/`（pull、micro_quiz）、`workbench/ingest/`（新配方）、
`workbench/server/`（pages、api、app）、`workbench.js`、两侧测试。
`/feedback` 写语义不变（新 `item_type='card'` 走既有通道）。
真实池迁移幂等且有备份。GLOSSARY / PENDING-DEFINITIONS / PRODUCT-MANUAL
随本变更同步。
