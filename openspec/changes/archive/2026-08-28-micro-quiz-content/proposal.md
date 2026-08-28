# micro-quiz-content 提案

## Why

Flash Card 与 Yes/No 是已上线的练习入口，但题库里没有任何为它们标记的内容——
pull 引擎的 `practice_modes` 判定（未标记内容 exam-only）让这两个模式永远拉不到题，
入口成了契约空壳。日常复习需要的是「一张卡考察一个小概念、题干短、反馈快」的小测，
而不是把长题截短冒充。此前的实地验证（2026-08-28 scratch 实测）证实了这一点：
对含题知识点发起闪卡练习，pull 直接返回 shortage。

本变更定义真正的 Micro Quiz 内容单位与它进入正式题池的唯一通道，
让既有模式拿到真实内容，而不新增任何会话系统。

## What Changes

- 新增内容契约 `micro_quiz`：短题干、选项、正确答案、错误原因、来源证据、
  单一原子知识点、题型（`yes_no / single_choice / multiple_choice /
  closest_answer / short_answer`）。
- 正式题池新增两个可空列（additive）：`practice_modes`（该题支持的模式列表，
  未标记即 exam-only，与 pull 引擎既有判定对齐）与 `micro_quiz`
  （微题结构化载荷 JSON）。
- 新增 `wb ingest micro-quiz` 配方：确定性契约门（题型/选项数/答案在选项内/
  单知识点/来源证据/可读顺序 ID），备份后单事务显式入池；本变更不引入
  AI 生成（AI 生成微题仍是后置实验，届时再议审计维度）。
- 练习页按题型渲染：是/否按钮、选项作答、最接近答案与简答的文本作答；
  闪卡揭示；客观题本地自动判对错（对照答案键），自评仍走既有评分模式；
  结构化选项仅当内容提供时渲染，绝不从旧 `problem_type` 推断。
- 永远不把长题前几十个字截短充当小测：契约门拒绝缺来源证据或超长题干的条目。

## Capabilities

### New Capabilities

- `micro-quiz-content`

### Modified Capabilities

- `workbench-ui`: 练习过程区按微题题型渲染作答控件与自动判分提示。
- `review-workbench`: pull 引擎按 `practice_modes` 显式标记做模式过滤
  （判定规则已存在，本变更让它有真实内容可过滤）。
- `workbench-content-governance`: 微题清单走 composable ingest 配方，
  确定性契约门 + 备份 + 单事务 apply。

## Impact

改动限于 `pool/scripts/pool_schema.py`（additive 列）、`workbench/`
（data/ingest/domain/UI/CLI）、测试与文档。现有题目零迁移（新列可空，
旧行不标记即保持 exam-only 行为）；学习写入语义、调度、反馈、状态机词表
全部不变；不新增页面、不新增依赖。风险点：选项含数学记号的渲染复用
既有安全子集（转义 HTML、sup/sub、KaTeX 已有约定）。
