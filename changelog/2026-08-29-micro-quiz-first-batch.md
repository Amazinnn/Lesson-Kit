# micro-quiz 通水：真实池迁移 + 第一批 9 条微题入池

按 2026-08-29 实现会话「通水」决定执行（consolidate-practice-views 归档后
第一项内容工程）：micro-quiz 契约此前只在副本上验证过，真实池从未迁移。

## 内容

- **真实池 additive 迁移**（`pool/scripts/migrate-progress.py --db pool/dmath.db`）：
  `problems.practice_modes` / `problems.micro_quiz` 两列 + `content_sequences`
  表；303 道存量题原样（NULL 标记 → 行为不变，仍然 exam-only）。
- **第一批 manifest** `pool/ingest/mq-batch-001.json`：9 条微题，覆盖三个
  弱项知识点（learner_signals 指向的 kp-001 乘法规则 / kp-002 加法规则 /
  kp-028 计数四入口），每 KP = 2 判断（yes_no）+ 1 闪卡（short_answer）；
  `practice_modes` 按题型自动推导。素材取自知识点正文（双语定理讲解）。
- **门禁 → 备份 → apply**：`_gate_micro_quiz` 对真实库预演通过后单事务
  apply，自动在线备份 `pool/backups/dmath-pre-mq-batch-001(.b).db`
  （pool/backups/ 新加入 .gitignore）。真实池 303 → 312 题。
- **首次真实数据端到端走查**（scratch 副本）：判断模式拉到真实微题 →
  是/否作答 → 本地判分「回答正确」→ 揭示「答案 + 为什么」→ 1–5 自评 →
  调度行正确推进（mq-001 last_rating 4, due → 2026-08-30）；闪卡模式
  short_answer 卡渲染与揭示同样通过。
- **内容修复一处**：mq-003 题干初版用了裸 `*`（`26*25*10*9`），渲染层按
  Markdown 强调吃掉了星号导致表达式显示错误。修法：manifest 改用 `×`，
  删除该行后经门禁重新入池（保持门禁是唯一写入口）。
  **教训：微题题干/答案里的乘号一律用 `×`，不要用裸 `*`。**

## 意义

Flash Card / 判断两个练习模式在真实数据下第一次可用（此前必然空态）。
后续批次按「弱项优先 + 低覆盖盲区」扩展：kp-007 / kp-029 / kp-004 /
kp-030 / kp-031 题量最少（1–4 道），是下一批候选。

## 验证

- `openspec validate --specs --strict` 10 passed；pytest 312 / node 71 全绿
  （真实池数据变化不影响夹具测试）。
- 走查截图与判分、调度写入逐项核对（见上）。
