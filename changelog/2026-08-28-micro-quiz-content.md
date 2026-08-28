# micro-quiz-content：微题内容契约落地

按 `openspec/changes/archive/2026-08-28-micro-quiz-content/`（proposal/design/tasks）
实现，Flash Card 与 Yes/No 入口从契约空壳变为可用模式。

## 内容与结构

- `micro_quiz` 契约：短题干（≤200 字）、选项、正确答案、错误原因、来源证据、
  单一原子知识点；题型 `yes_no / single_choice / multiple_choice /
  closest_answer / short_answer`。
- 正式题池 additive 迁移两列：`problems.practice_modes`（显式模式标记，
  未标记仍 exam-only）与 `problems.micro_quiz`（结构化载荷 JSON）。
- `domain/micro_quiz.py` 纯规则：词表、载荷校验、模式推导、客观题判分。
- 入池走 `wb ingest recipe micro-quiz`：确定性契约门（含知识点存在性、
  ID 形如 `<course>-<chapter>-mq-NNN`、题干安全标记检查）+ 可恢复备份 +
  单事务 apply（事务内复验，失败整体回滚）。样例清单见
  `docs/examples/micro-quiz-sample.json`。

## 练习体验

- pull 引擎既有 `practice_modes` 判定首次有内容可过滤：闪卡/是否模式只拉
  显式标记的题，无内容如实报 shortage。
- 练习页按题型渲染：是/否与选项作答（多选为复选）、最接近答案/简答走
  文本框；客观题提交即本地判对错并展示错误原因；闪卡揭示改显
  答案 + 错因；会话末评分卡对微题显示答案与错因而非「无解析」。
- 评分、学习写入、调度语义零改动：仍走既有每题/统一自评与反馈通道。

## 明确不做

AI 生成微题（另行立项）、匹配题型、服务端判分、微题独立调度参数。

## 验证

- 新增 Python 测试 11 个（规则/门/apply 回滚/pull 集成），全量 302 通过；
  Node UI 测试 5 个（是/否、判分对错、多选、揭示、普通题回归），全量 66 通过。
- `openspec validate --specs --strict`：8 passed（含新能力规格）。
- 真实表结构副本端到端实测：ensure 迁移 → 样例入池（303→306，带备份）→
  Yes/No 拉题 → 浏览器作答判分 → 会话末评分 → progress/signal/schedule
  学习记录全部正确落库。
