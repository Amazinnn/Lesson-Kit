# changelog — introduce-flash-card 实现（PR2 部分）

日期：2026-08-29　变更：`openspec/changes/archive/2026-08-29-introduce-flash-card/`
代码 PR：#22（feat/introduce-flash-card）

## 概要

闪卡正名与最小实现：现有「闪卡」模式（微题的卡片式渲染）改名 **micro（小测）**，
`flash_card` 这个名字让给新的真·闪卡功能——从知识点解构出的键值对记忆卡
（Anki Note/Card 两层模型的最小版），作为练习会话**第四种模式**。
顺带收敛微题题型与修复「练习会话注意力不聚焦」。

## 改名与迁移

- 练习模式三变四：`exam`（综合题）/ `micro`（小测，原 flash_card）/ `yes_no`（判断）/
  `flash_card`（闪卡，新）。
- `ensure_workbench_schema` 幂等迁移：`practice_modes` 值 `"flash_card"`→`"micro"`
  REPLACE；`review_schedule`/`feedback_events` 两表 item_type CHECK 加宽 `'card'`
  （数据保留式重建）；新增 `flash_cards` 表。真实池迁移验证：312 题无损、
  3 行旧标记改名、0 残留。

## micro 收敛（选择题化）

- 题型集收窄为 `yes_no / single_choice / multiple_choice`；
  `short_answer / closest_answer` 退役（门禁显式拒绝「retired quiz type」）。
- 微题一律点选作答：有选项的题目隐藏自由文本框（composer 按
  text / choice / card 三态布局）。
- `practice_modes` 推导：单/多选 → `["micro"]`，判断 → `["yes_no"]`。

## 闪卡第四模式

- 新表 `flash_cards(card_id, kp_id, front, back, source_evidence)`（恰 5 字段；
  front ≤100 / back ≤300 字符；来源证据必填）。
- 新配方 `wb ingest <ws> recipe flash-card`（kind=`flash-card-patch`，
  id 规则 `^[a-z0-9-]+-fc-\d{3}$`，门禁 + 备份 + 单事务 apply）。
- 新端点 `POST /api/w/{name}/pull-cards`：选区 kp 过滤、到期行优先、exclude 支持。
- JS 闪卡会话：正面 →「揭示背面」→ 1–5 自评；统一自评下揭示即标记
  unrated、就地评分隐藏，**session-end 收束页列出已玩卡（正面/背面）补评分**。
- 调度：`item_type='card'` 每卡一行独立调度（方向键留空备用）；
  评分照常经 `/feedback`（`_targets` 把卡映射到其知识点，信号与状态挂知识点）。
- 到期卡片照常进入建议/时间视图（`_item_label` 加 card 分支）。

## 会话聚焦（UX 清单项修复）

任何模式、任何自评时机：点「开始本轮练习」后 `.practice-columns`
（目标卡/准备列表/建议/模式选择/时间视图）整体隐藏，中间栏只留练习流并滚动
到位；耗尽、提前结束、刷新恢复分支同步恢复/收敛。

## 走查中发现并当场修复

- **统一自评的闪卡没有收束路径**（走查发现）：揭示后既无 unrated 标记、
  session-end 永远没有卡片条目。修复：batch 下揭示即标 `unrated`，
  `跳到下一道` 对已揭示的卡保留 `unrated`（未揭示仍算跳过）。
- 记入 UX 清单（未修）：统一自评下微题的即时判分被立即翻页覆盖，
  对错只能等收束页的答案——建议 batch 也短暂显示对错再翻页。

## 测试

pytest 324 全绿（净 +12：cards 契约/配方/pull-cards/调度/migration、retired 拒绝、
路由四模式）；node 74→78 全绿（改名、微题隐藏文本框、闪卡揭示流、batch 卡片、
session-end 卡片条目）；`openspec validate --specs --strict` 10 passed；
guards（extract-problems / problem-set）PASS。
