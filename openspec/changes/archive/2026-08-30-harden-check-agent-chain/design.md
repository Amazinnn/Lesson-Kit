# harden-check-agent-chain 设计

## D1 范围与问卷映射

专题 23 四答为准：真 Agent 产出链+benchmark、manifest 完备格式（标签）、
Agent CLI 面补全（综合题出题除外）；界面闭环/综合题配方/候选表 DROP 不做。
问卷与答案归档 `docs/superpowers/plans/2026-08-30-check-agent-chain-
questionnaire.md`。

## D2 反馈回路

- `start_turn()` 在锁内 best-effort 读 `transcript.jsonl` 最后一行：末条
  exchange 带 `action` 且 `type=="check_ingest"` 时，把裁决拟成一句话并入
  `context["last_check_outcome"]`（随整体 context JSON 注入提示词）。
  读取失败/损坏/无 action → 静默跳过，不影响 turn。
- 文案（成功 / 拒收 / 区块无效三态）：
  - 成功：`上一轮出题动作已成功入库：批次 {batch_id}（{kind}，{n} 条）。不要重复提交相同内容。`
  - 拒收：`上一轮出题动作被门禁拒收（零写入），逐条原因：\n{error}\n请修正 manifest 后重新提交完整的 lessonkit-action 区块。`
  - 无效：`上一轮出题动作区块无效：{error}。请重新提交符合契约的完整区块。`
- `_prompt()` 在 check_ingest 契约段末尾追加一句：`若上下文含 last_check_outcome：成功则不要重复提交相同内容；被拒收则按逐条原因修正后重新提交完整区块。`
- 只认 check_ingest 动作；practice/goal 动作不注入（scope 克制）。

## D3 提示词契约硬化（Lane B 按此原文替换现有 check_ingest 契约段）

```
仅当学生明确要求出题、补池或给某知识点加内容时，才可在回答末尾附出题入库区块；
对话内出题一律用 lessonkit-action 区块，禁止直接运行 wb ingest 或写数据库。
manifest 规则：kind 为 flash-card-patch 或 micro-quiz-patch。
闪卡 item 字段：card_id/kp_id/front/back/source_evidence，可选 topic_label。
微题 item 字段：problem_id/kp_id/stem/quiz_type/options/answer_key/error_reason/source_evidence，
可选 topic_label/display_title/display_summary。
id 形如 <course>-<chapter>-fc-NNN 或 -mq-NNN（NNN 为三位数字；与池内已有 id
重复会被拒收，收到拒收原因后改用其他编号重试）；kp_id 必须取自下方上下文的
knowledge_point_ids。
长度与取值：front≤100 字、back≤300 字、stem≤200 字、options 为 2–6 个互不相同的
字符串且 answer_key 必须是其中之一（yes_no 用默认 是/否 对）、quiz_type 仅
yes_no/single_choice/multiple_choice、topic_label≤40 字、display_title≤80 字、
display_summary≤200 字；数学乘号一律用 ×；source_evidence 必填（如
"textbook ch06 §3.1"）；一次产出 3–6 条。
闪卡 item 示例：{"card_id":"dmath-ch06-fc-901","kp_id":"dmath-ch06-kp-001",
"front":"乘法规则针对的是什么情形？","back":"一个过程可分解为先后的两个任务，各自都有若干种做法——分步计数用乘法。",
"source_evidence":"textbook ch06 product rule","topic_label":"计数原理"}
微题 item 示例：{"problem_id":"dmath-ch06-mq-901","kp_id":"dmath-ch06-kp-001",
"stem":"自然数 1 是质数吗？","quiz_type":"yes_no","answer_key":"否",
"error_reason":"1 只有 1 个正因数，不算质数。","source_evidence":"Rosen 6th, §3.1 定义",
"topic_label":"计数原理"}
若上下文含 last_check_outcome：成功则不要重复提交相同内容；被拒收则按逐条原因
修正后重新提交完整区块。
```

## D4 manifest 标签字段

- 闪卡：新增可选 `topic_label`（additive 列 `flash_cards.topic_label TEXT`，
  建表语句与 ensure_columns 同步）。仅 topic_label——卡在界面无标题/摘要面，
  不加 display_*（克制）。
- 微题：可选 `topic_label`/`display_title`/`display_summary`（problems 既有
  列，零迁移）。
- 门禁校验（card_rules/micro_quiz_rules）：字段缺省→存 NULL（现状不变）；
  提供时必须为非空字符串（strip 后非空）、topic_label≤40 字、
  display_title≤80 字、display_summary≤200 字、过 `_markup_errors` 同源
  标记安全检查。违例逐条拒收（`<id>: <reason>` 既有格式）。
- 上下界为 Agent 产出新增（wb data 手工路径不设限，差异在 design 记录为
  有意为之：门禁是 AI 内容的决断辅助）。

## D5 `wb ingest batches`

- CLI：`python -m workbench.cli.main ingest <name> batches`，输出
  `{"artifact": null, "result": {"batches": [{batch_id, kind, counts(解析后),
  applied_at, rolled_back_at, backup_path}, …按 applied_at 倒序]}}`，只读
  零写入；错误处理与既有 ingest 子动作一致。
- 不做分页/过滤（批次量级为个位数~两位数，Ponytail）。

## D6 benchmark 定稿（开工检查清单 · 生产任务验收机制）

**验收陈述**：此 benchmark 验收 **Check 管线的对话出题产出链**（check_ingest
动作），验证 **真实 provider（codex）在对话首轮即产出通过确定性门禁并入库的
合规 manifest**，场景是 **3091 副本池（真实池结构副本）+ hold-out KP 上
「给指定 KP 出 3 张闪卡 / 2 道微题」的出题请求**。可证伪：输入为 hold-out
KP 的出题请求时，首轮 check_ingest 动作必须通过门禁并产生 ingest_batches
登记行；20 轮中每种 kind 首轮成功率 <60% 即不达标。

**数据隔离（额外要素 2a）**：KP 全集 31 个，划分为 dev 集（prompt 迭代可用：
kp-001/002/004/007/028，即既有走查用例）与 **hold-out 集 10 个：kp-003、
kp-005、kp-006、kp-008、kp-009、kp-010、kp-012、kp-015、kp-020、kp-026**
（32%，prompt 调优期间禁止触碰）。错误/反向用例由开发会话构造（非被测
Agent 生成）。hold-out 不达标需修 prompt 时，换用剩余未用 KP 组成新鲜
hold-out 子集重测，已报数据不改。

**用例设计（额外要素 2b 构造效度）**：
- 典型输入：hold-out KP 出 3 张闪卡 / 2 道微题（每 kind 10 轮，KP 轮换，
  固定顺序表见 run-plan，禁挑选）。
- 边界输入：一次 6 张（上限）1 轮（信息性，不计入 20 轮）。
- 反向用例（必拒，验证门禁构造效度，另报不入 20 轮）：① manifest 携带池内
  已有 id（重复 id 拒收）；② 缺 source_evidence；③ quiz_type 用 retired
  `closest_answer`；④ topic_label 超 40 字。期望：整体拒收、逐条原因、
  零写入（accounting 前后一致）。
- 验收点全部为可观察行为：ingest_batches 登记、行计数、transcript 事件、
  拒收文本——不验代码结构。

**结果效度（额外要素 2c）**：环境=真实 codex CLI+真实池结构副本（贴近生产）；
真实数据回放=输入全部取自真实池 KP 与真实教材语料语境。报告性能数字：单轮
wall time（turn created_at→completed_at）。

**成本报告（额外要素 3）**：① 单轮耗时与调用次数（每 run=1 次 provider
调用）；② 20 轮成功率分布（按 kind 分列：首轮成功数/10）；③ 失败模式分类
（no-action / bad-json / contract-violation / timeout / other，逐轮标注）；
④ 方差（wall time 均值±标准差，按 kind）；⑤ 降级行为验证：timeout_s=1 的
bridges override 跑 1 轮 → turn 如实 failed、池零写入。

**面向用户必加项**：真实用户场景验证=所有者在真实池亲自出题入库（benchmark
达标后执行，操作路径写入交接文档）；降级行为=上述 ⑤。

**退役条件**：Check 管线动作废弃 → 本 benchmark 自动废弃；manifest 契约或
反馈回路 requirement 变更 → 触发重审；与生产实际脱节超过 6 个月 → 重审。

**Run 协议**：每 run 新建对话（隔离测量）；消息固定模板
「帮我给 {kp_id} 出题：补 {n} 张闪卡/道微题」；check_intent 由前端正则等效
（API 直发时显式置 true）；首轮判定=该 turn 首个 provider 回复中的
check_ingest 动作直接过门禁并 apply。run 顺序固定表（KP 交错、kind 交错）
写入 tasks 执行记录，防事后挑选。
