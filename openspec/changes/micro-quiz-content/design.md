# micro-quiz-content 设计

## 关键决策

### D1 微题是 problems 池内带显式标记的行（不是平行表）

练习循环的每一段——pull、会话、attempts、feedback、schedule、progress、
显示元数据（display_title 等）、`wb data` 接口、弱点与计划查询——都以
`problem_id` 为键。为微题另立一张表意味着平行复制整套调度与反馈机器，
违反 Ponytail 阶梯（有没有现成？）。因此：

- 微题 = `problems` 行 + `practice_modes` 标记 + `micro_quiz` 结构化载荷；
- 复用可读顺序 ID 规则：`{course}-{chapter}-mq-NNN`（无哈希）；
- `problem_type` 保持既有 CHECK 词表不变（题型分类进载荷，不动旧词表）；
- 单知识点是契约校验规则（`kp_ids` 恰好一个），不是新约束。

### D2 两个可空列，additive 迁移

`pool_schema.py` ensure_columns 增量迁移，旧行两列为 NULL：

- `practice_modes TEXT`：JSON 字符串数组，如 `["flash_card"]`；NULL 即 exam-only
  （与 `pull._eligible_for_mode` 既有语义一致，该函数不用改）；
- `micro_quiz TEXT`：JSON 载荷
  `{quiz_type, options, answer_key, error_reason, source_evidence}`；
  `problem_text` 即题干，复用既有列，不另设 stem。

`data/pool.py::_problem_row` 负责把两列 JSON 解析为 dict 字段（与 kp_ids 同法）。

### D3 契约词表与确定性校验

```text
quiz_type      ∈ {yes_no, single_choice, multiple_choice, closest_answer, short_answer}
options        yes_no 固定为 ["是", "否"]（可省略，渲染时补默认）
               single_choice / multiple_choice 恰好 2–6 项、无重复
               closest_answer / short_answer 必须为空
answer_key     yes_no ∈ options；choice 类型必须 ∈ options；
               multiple_choice 为选项子集（JSON 数组）；
               closest_answer / short_answer 为参考答案文本（不自动判分）
error_reason   非空（回答错误时展示的原因）
source_evidence 非空（指向源材料：书页/章节/题号）
题干           problem_text 非空且 ≤ 200 字符（超长内容属于试卷模式，不冒充小测）
practice_modes 与 quiz_type 一致：yes_no→["yes_no"]，其余→["flash_card", ...] 按内容定
```

校验只有确定性规则（ingest 门 + data 层插入前双保险）。独立审计维度
（AUDIT_DIMENSIONS 那套）是给 AI 准备内容的；本变更内容来源是人工按源材料
整理的清单，AI 生成微题（FUTURE-NOTES「AI 生成微题」条目）另行立项后再补审计。

### D4 入池走 `wb ingest micro-quiz` 配方

对齐 workbench-content-governance 的 composable 形态：

```bash
wb ingest recipe micro-quiz --db pool/dmath.db --input mq-patch.json --output-dir .lessonkit/ingest/mq-001 --apply --backup ...
```

- 清单 artifact：`{"kind": "micro-quiz-patch", "items": [...]}`；
- 门：`_gate_micro_quiz(conn, items)` 逐条校验 D3 + ID 序号衔接 + 知识点存在；
- apply：`BEGIN IMMEDIATE` → 备份（与 problems 配方同法）→ 门复验 →
  逐条 INSERT（problem_id/kp_ids/problem_text/practice_modes/micro_quiz/
  source_kind='quiz'，problem_type 取条目声明、默认 'other'）→ commit；
  任何一步失败整体回滚。

### D5 渲染与判分（auto-grade 是输入辅助，不是新评分模式）

- 练习过程区按 `micro_quiz.quiz_type` 渲染：
  yes_no →「是 / 否」两个按钮；single/multiple_choice → 选项点击
  （多选可累积）；closest_answer / short_answer → 文本框；
  flash_card 模式 → 先题后揭（载荷 answer_key 或 solution 揭示）。
- 客观题（yes_no / single_choice / multiple_choice）提交时本地对照
  answer_key 判对错，界面给出对/错与 error_reason 提示；最终仍由学生
  在既有「每题自评 / 完成后统一自评」里确认——评分与学习写入语义零改动
  （沿用 grading input modes 的 auto-grade 位）。
- 选项与题干沿用既有安全渲染子集（HTML 转义、sup/sub、KaTeX）。
- 结构化选项仅当 `micro_quiz.options` 提供时渲染；旧 `problem_type` 与
  旧 `choice` 字段永不推断（契约空壳条款）。
- 无内容时行为不变：pull 返回 shortage，入口显示既有空状态。

## 明确不做

- AI 生成微题、微题权重统计（FUTURE-NOTES 1.2 / 5.6，另行立项）。
- 匹配题型（FUTURE-NOTES 提及 matching，本轮词表不含，需要时再议）。
- 服务端判分接口（答案本就随 pull 下发，与 exam 模式同一信任模型；
  引入服务端判分是独立决策）。
- 微题的独立调度参数（与正式题共用 SM-2 变体，不加新状态机值）。
