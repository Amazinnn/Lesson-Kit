# introduce-flash-card 设计

## D1 名词处置

- 现「闪卡」模式 = 微题卡片式渲染 → 改名 `micro`（小测）；GLOSSARY
  「闪卡模式」条目改写为「小测模式 / Micro Mode」；`flash_card` mode id
  让给新功能。
- 新「闪卡 / Flash Card」定义（所有者 2026-08-29 确认）：从知识点解构的
  键值对记忆卡（类似 Python dict 的一条键值对），使用时对着正面回忆背面；
  背单词、背概念等场景；比小测更轻（无选项、无判分）。

## D2 数据模型（Note/Card 两层最小版）

- 知识点 = Note（唯一事实源，存于 `knowledge_points`，不动）；卡 = 派生
  视图，`flash_cards` 恰 5 字段：`card_id`（`^[a-z0-9-]+-fc-\d{3}$`）、
  `kp_id`、`front`、`back`、`source_evidence`。
- 最小信息原则（SuperMemo）：一卡一原子事实——这是**内容纪律**（写进
  recipe 文档与说明书），不做程序化度量。front ≤100、back ≤300 字符；
  `source_evidence` 必填（来源留痕，与微题同纪律）。
- 调度：`item_type='card'`，每卡一行 `review_schedule`；direction 键留空
  （每方向调度键与 `feedback.direction` API 已存在，反向卡本期不启用）。

## D3 练习形态

- 第四种 content mode，会话内复用既有机制：选区过滤（`card.kp_id ∈ 选区`）、
  自评时机双选、session-end 统一自评（卡片条目显示正面/背面 + 1–5）。
- `/pull-cards`：请求 `{kp_ids}`，响应 `{cards:[{card_id,kp_id,front,back}]}`
  ——到期优先（`review_schedule` 到期 card 行），其余按 card_id 稳定序；
  不带 micro-quiz 判分语义。
- JS 会话按 `MODE_KEY='flash_card'` 分支：渲染正面卡 → 「揭示」按钮 →
  背面 → 自评（immediate）或标记完成（batch）→ 下一张；已玩卡不重复。

## D4 micro 收敛

- 题型集 = `yes_no / single_choice / multiple_choice`；门禁显式拒绝
  `short_answer`/`closest_answer`；`practice_modes` 推导：单/多选→
  `["micro"]`，判断→`["yes_no"]`。
- 渲染：微题三类必有选项 → 有 micro 载荷即隐藏 composer 自由文本框，
  只留选项点选 + 提交；本地判分逻辑不变。

## D5 会话聚焦

- `startSession` 对**所有模式**隐藏 `.practice-columns`（学习安排/准备
  列表/建议/模式选择/时间视图）并把练习流滚入视野；`finishExhausted` 与
  刷新恢复分支同步处理；提前结束跳 session-end 页（返回练习页时无进行中
  会话，服务端默认展开，无需额外持久状态）。

## D6 迁移与内容

- `ensure_workbench_schema` 内幂等 `UPDATE problems SET practice_modes =
  REPLACE(practice_modes, '"flash_card"', '"micro"')`（只影响仍含旧值的行）。
- 真实池 4 道 short_answer 题删除后按单选题型重制（内容 PR，
  `pool/backups/` 备份先行，删除+重入都走备份对照）。
- 微题第二批 15 道（kp-007/029/004/030/031 × 单选/多选/判断）与闪卡首批
  （5 KP × 3–5 卡）走既有门禁流程。
