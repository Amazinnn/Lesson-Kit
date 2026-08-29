# introduce-flash-card 任务

## 1. 规格与名词（PR1）

- [x] flash-card 新能力 spec（内容契约 / 入池配方 / 第四模式语义 / 调度行）
- [x] micro-quiz-content delta（契约收窄、模式改名 REMOVED+ADDED、渲染点选）
- [x] workbench-ui delta（四模式 + 会话聚焦）
- [x] daily-learning-plan delta（四条练习路径）
- [x] GLOSSARY：小测模式改写、闪卡新条目、微题/练习模式条目同步
- [x] PENDING-DEFINITIONS：generate 桥条目加注「闪卡自动解构属其范围」
- [x] PRODUCT-MANUAL 回填（四模式口径、小测点选、闪卡节、会话聚焦）
- [x] `openspec validate introduce-flash-card --strict` + `--specs --strict`

## 2. 实现（PR2）

- [x] 改名迁移（schema 幂等 REPLACE）+ 全链路同步（pull / micro_quiz /
      pages / JS / 空态文案 / 测试）
- [x] micro 收敛（gate 拒绝 retired 类型 + 隐藏作答文本框）
- [x] flash_cards 建表（additive）+ `wb ingest recipe flash-card`
- [x] `/pull-cards` + JS 闪卡揭示流 + `/feedback` item_type='card' 调度
- [x] session-end 统一自评支持卡片条目
- [x] 会话聚焦（隐藏 .practice-columns + 恢复 + 刷新恢复分支）
- [x] pytest + node 全绿；review_overview/时间视图对 card 行优雅处理验证

## 3. 内容与走查（PR3）

- [x] 微题第二批 15 道（kp-007/029/004/030/031 × 单选/多选/判断）
- [x] 3 道 short_answer 删除重制为单选（备份先行；实际池中为 3 道而非
      计划时的 4 道，以实点为准）
- [x] 闪卡首批（5 KP × 3 卡，最小信息原则）走新配方入池
- [x] scratch 走查（3091 隔离）：四模式可练、改名空态、聚焦隐藏/恢复、
      闪卡揭示自评全流程、session-end 卡片条目、重制批判分；发现并当场
      修复 batch 闪卡无收束路径的缺陷
- [x] 真实池 apply（pool/backups 备份）+ demo 3082 重挂
- [x] changelog（实现 + 内容）+ 归档本变更（flash-card spec 落 Purpose）
