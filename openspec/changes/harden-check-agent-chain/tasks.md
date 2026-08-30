# harden-check-agent-chain 任务

## 1. 规格与 benchmark 定稿（PR1）

- [ ] 问卷归档 + DISCUSSION-RECORD 专题 23
- [ ] ai-teacher-bridge delta（Check ingest action 反馈回路 + 2 scenario）
- [ ] flash-card delta（契约增可选 topic_label）
- [ ] micro-quiz-content delta（契约增可选标签字段）
- [ ] workbench-content-governance delta（批次登记可见性）
- [ ] design.md benchmark 定稿（验收陈述/隔离/用例/成本/退役）
- [ ] `openspec validate harden-check-agent-chain --strict`

## 2. 实现（PR2，codex 双 lane 并行 + 缝合）

- [ ] Lane B：start_turn 三态 last_check_outcome 注入 + _prompt 契约硬化
      （D2/D3 原文）+ test_conversations/test_agent_context
- [ ] Lane A：标签字段门禁校验（card_rules/micro_quiz_rules）+
      flash_cards.topic_label additive + `wb ingest batches` +
      docs/examples retired 样例修正 + 侧测试
- [ ] 缝合：conversations→ingest 接缝核对 + 全量 pytest/node +
      openspec validate --specs --strict

## 3. benchmark 执行与走查（PR3）

- [ ] 走查环境：3091 副本 + 真 codex（无 shim）；dev/hold-out 集核对
- [ ] 反馈回路实证：拒收→「按原因修正」→ 二轮自修正成功（dev KP，1 例）
- [ ] hold-out 20 轮（10 KP × 2 kind，固定顺序表，逐轮记录状态与耗时）
- [ ] 反向用例 4 条（必拒 + 零写入核对）+ 边界 1 条（6 张，信息性）
- [ ] 降级验证 1 轮（timeout override → failed 如实、零写入）
- [ ] 报告：首轮成功率（≥60% 线）/失败模式/耗时均值±标准差 → changelog
- [ ] 演示环境重置 + 归档本变更 + 交接文档（含所有者真实池实验路径）
- [ ] 基线：pytest / node / openspec validate --specs --strict / 双 guard
