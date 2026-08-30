# 2026-08-30 — harden-check-agent-chain（Check Agent 产出链完整交付）

## 交付

一个 OpenSpec change（PR #36 规格+benchmark 定稿、PR #37 实现、PR3 实测归档），
DISCUSSION-RECORD 专题 23 与开工问卷存档范围决策。

- **反馈回路**：新 turn 开始时上一轮 check_ingest 的裁决注入 provider 上下文
  `last_check_outcome`（成功批次确认/逐条拒收/区块无效三态）；Agent 首次能看到
  门禁说了什么。
- **提示词契约硬化**：出题一律走 lessonkit-action、禁止直跑 wb ingest；id 规则
  + next_free_ids（context 按 check_intent 注入每类实体下一空闲编号）；长度/
  题型白名单/×乘号/source_evidence 红线与正确 item 示例。
- **manifest 标签字段**：题/卡 items 可携带 topic_label（微题另可带
  display_title/display_summary），门禁校验（≤40/80/200 字+markup 安全），
  flash_cards additive 增列。
- **`wb ingest batches`**：批次登记只读清单。
- **容错**：check_intent 下接受裸 manifest 区块（实测真 agent 会省略
  `"type":"check_ingest"` 包装）；修复 test_agent_context 死测试。

## benchmark 报告（design.md D6 定稿协议 · codex 单链路 20 轮 hold-out）

**验收陈述**：hold-out KP 出题请求下，真实 codex 首轮（未经修正）产出通过
确定性门禁并入库的合规 manifest；每种 kind 首轮成功率 ≥60% 为达标线。

| kind | 首轮成功率 | 判定 | 失败模式 |
|---|---|---|---|
| flash-card | **8/10 = 80%** | ✅ 达标 | timeout ×2 |
| micro-quiz | **10/10 = 100%** | ✅ 达标 | — |

- **成本**：成功轮 wall time——闪卡 155.5±52.4s（7 样本）、微题 159.0±36.7s
  （10 样本）；每轮 1 次 provider 调用。
- **失败模式分类**：2 轮均为 `timeout`（300s 默认超时标记、provider 退出后
  落盘；非契约违例，agent 当时仍在自审内容并已产出合法区块）。缓解选项（未
  实施，留待办）：bridges.json 调高 timeout_s 或指引 agent 精简会内子流程。
- **降级验证**：timeout_s=1 override 下 turn 最终 failed "provider timed out"，
  池零写入；超时轮答案整体丢弃、绝不入库（terminate 对 codex 子进程树为
  best-effort，标记在进程退出后落盘——既有行为，如实记录）。
- **20 轮明细**（固定顺序表，KP×kind 交错，无挑选）：run1-20 =
  fc-003✓ mq-003✓ fc-005✓ mq-005✓ fc-006✓ mq-006✓ fc-008✓ mq-008✓
  fc-009✓ mq-009✓ fc-010✓ mq-010✓ **fc-012✗timeout** mq-012✓
  fc-015✓ mq-015✓ **fc-020✗timeout** mq-020✓ fc-026✓ mq-026✓
  （✓=首轮入库，batch-003…020；原始 JSON 在
  `Temp/check-benchmark/results/`，池一致性 96 卡/375 题/20 批全戳记核对）。

**反向用例（构造效度，另报不入 20 轮）**：重复 id / 缺 source_evidence /
retired closest_answer（并报缺 practice_modes）/ topic_label 50 字——4/4 逐条
拒收、零写入；边界用例：单批 6 张 dry-run 放行。

**反馈回路实证**：真 codex 稳定读取上下文（next_free_ids → 精确使用 fc-067
起编）；两次拒绝提交注定失败的清单（重复 id、50 字标签——按契约预判），
即回路的目标行为以「预修正」形态呈现；拒收→修正路径由单元测试三态注入 +
门禁实弹覆盖。

## 验收自检（开工清单六步）

1. 验收陈述：design.md D6，可证伪 ✅ 2. hold-out（10 KP）与 dev 集（5 KP）
   物理分开，prompt 迭代未触碰 hold-out ✅ 3. 反向用例 4/4 跑过 ✅
   4. 真实环境回放（真 codex + 真实池结构副本）✅ 5. 成本/成功率/方差齐 ✅
   6. 退役条件：Check 废弃→benchmark 废弃；契约/反馈回路 requirement 变更
   →重审；脱节 6 个月→重审 ✅

## 遗留

- codex 会内子流程（自派子代理自审）显著拉长尾延迟并贡献 2 次超时——
  可在 bridges.json 调 timeout_s，或在对话指引中要求精简；待真实使用反馈。
- 界面闭环（卡片跳转/批次视图）、综合题配方、候选表 DROP：保持显式后续项。

## 所有者最终验收路径（真实池）

> 追记（2026-08-30）：真实池的 Check schema（`ingest_batches` 表、批次/标签列、
> `content_sequences` CHECK 放宽）已提前应用，迁移前整池备份留档于
> `pool/backups/dmath-pre-schema-20260830.db`。3081 重启加载新代码后即可直接按此路径验收。

1. 打开真实工作台（3081）→ 右栏对话新建（codex/claude 均可）。
2. 说：「帮我给 dmath-ch06-kp-XXX 出题：补 3 张闪卡」（XXX 任选）。
3. 预期：独立结果卡片显示批次号/条数；练习页闪卡模式可见新卡。
4. 想撤销：点卡片上「整批回滚」或 `wb ingest rollback --batch <批次号>`。
