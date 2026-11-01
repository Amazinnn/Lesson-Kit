# 2026-11-01 — 综合题小问的作者通道：契约补齐（Agent 可见）

背景：所有者要求“新能力暴露给内接 Agent 的说明文档齐全”。审计发现 `agent-part-grading`
的批改侧（grading 契约主题、FILE_CONTRACT 批改边界、L2-interfaces、DATA_MODEL、
PRODUCT-MANUAL、GLOSSARY）都齐，但**作者侧有一处实质缺口**：`problems.parts` 只被
`problem-patch` 接受，而 Agent 契约规定“创建走 content-bundle”——bundle 的问题白名单里
没有 `parts`，且 bundle 对未知字段是静默忽略。即：Agent 按契约用 bundle 创作综合题，
**小问会被无声丢弃**。

## 修复

- `workbench/ingest/__init__.py`：`_bundle_problem_fields` 增加 `parts`；bundle 预检用
  `workbench.domain.problem_parts.validate` 校验，并在 `problems.parts` 列缺失时给出
  可操作的迁移指引；`parts` 与 `quiz_type/micro_quiz` 同时出现时报错（此前是 parts 静默
  遮蔽 micro_quiz）；写入列按 `has-column` 守卫，旧池不会因新列名报 SQL 错误。
- `workbench/bridge/agent_contracts.py` 的 `content` 主题：题目字段与 patchable 字段补
  `parts`；新增第 18 条 parts 契约（id/type/prompt 规则、客观题的 options/answer_key、
  证明题只写过程、short_answer 语义、保存顺序权威、治理编辑与迁移要求）。
- `workbench/bridge/conversations.py` 的 `_prompt` 紧凑地图：题目字段补
  `parts（综合题小问，按小问声明题型）`（prompt 3235 字，仍在 7000 上限内）。
- `FILE_CONTRACT.md`：新增 “Authored problem parts (`problems.parts`)” 小节（字段表 +
  禁区 + 迁移要求）。

## 已知限制（登记，不在本次修）

content-bundle 各资产类型（kp/problem/card）对**未知字段一律静默忽略**。`parts` 已从
“被忽略”变为“被支持”，但该模式本身仍是陷阱：未来新增字段若忘记加白名单会再次静默丢数据。
改动它会影响既有 manifest 的宽容度，需单独决策。

## 验收

`python -m pytest tests -q`：1308 passed（新增 bundle 三个用例：parts 持久化、
非法 parts 整份拒收、parts+quiz_type 组合拒收；契约测试补 parts 断言）。
