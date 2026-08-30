# harden-check-agent-chain 提案

## Why

introduce-check-pipeline 交付后，所有者反馈「什么都实现了一点，但好像又没
实现完全」，拷问定性为：真 Agent 出题链没走通——演示出题来自 stub 脚本，
真实 provider 从未端到端验证；门禁裁决结果只落在本端 transcript，从不回给
Agent（被拒收后无法自行修正）；提示词契约对真实 Agent 过薄；manifest 缺少
标签等完备内容字段。所有者要求按《新项目开工检查清单》交付完整的开发结果
（DISCUSSION-RECORD 专题 23、问卷
docs/superpowers/plans/2026-08-30-check-agent-chain-questionnaire.md）。

清单对生产任务的要求 = 定稿 benchmark：验收陈述、hold-out 数据隔离、反向
用例、真实环境回放、成本与成功率报告、退役条件。本轮把这套机制首次落地为
「真 Agent 出题产出链」的验收：codex 单链路 10 轮×2 kind，严格首轮成功率
每种 kind ≥60%，达标后由所有者亲自在真实池实验。

## What Changes

- **反馈回路**：新 turn 开始时，上一轮 check_ingest 动作的裁决（成功批次
  确认 / 逐条拒收原因）注入 provider 上下文（`last_check_outcome`），
  Agent 被拒收后可自行修正重提、成功后不重复提交。
- **提示词契约硬化**：出题一律走动作区块、禁止直跑 wb ingest；id 命名、
  长度/题型白名单、×乘号、source_evidence、3–6 条等红线与正确 item 示例。
- **manifest 完备格式**：题/卡 items 可携带 topic_label（微题另可携带
  display_title/display_summary），门禁校验；flash_cards additive 增列
  `topic_label`。
- **`wb ingest batches`**：批次登记只读清单（为整批回滚提供批次 id 查询面）。
- **benchmark 定稿与执行**：design.md 定稿（验收陈述/hold-out/反向用例/
  成本报告/退役条件），PR3 按 20 轮 hold-out 实测并报告。

## Capabilities

### New Capabilities

（无。）

### Modified Capabilities

- `ai-teacher-bridge`：Check ingest action requirement 增反馈回路。
- `flash-card`：内容契约增可选 topic_label。
- `micro-quiz-content`：内容契约增可选标签字段。
- `workbench-content-governance`：新增批次登记可见性 requirement。

## Impact

代码集中：`workbench/bridge/conversations.py`（反馈回路+提示词）、
`workbench/domain/cards.py`、`workbench/domain/micro_quiz.py`、
`workbench/ingest/__init__.py`、`workbench/cli/main.py`、
`pool/scripts/pool_schema.py`、两侧测试与 `docs/examples/` 修正。
GLOSSARY 无新名词（反馈回路是行为不是名词）；PRODUCT-MANUAL/ACTION-GRAPH
不动（用户不可见行为）。benchmark 结果进 changelog。
