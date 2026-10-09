# DATA_MODEL — 持久内容字段契约

> **职责**：本文档只定义“持久字段是什么意思、谁可以写、谁消费、是否仍推荐使用”。
> 用户可观察行为仍以 `openspec/specs/` 为准；设计名词以 `docs/GLOSSARY.md` 为准；
> Agent 交换文件格式以 `FILE_CONTRACT.md` 为准。本文档不得复制完整产品行为。
>
> **冲突规则**：若本文档、live OpenSpec、DDL/代码、FILE_CONTRACT 对同一字段给出不同含义，
> 这是 contract drift，Agent 必须先登记并协调，禁止自行挑一个“看起来最新”的版本继续扩散。

## 状态标签

- **active**：当前正式字段，可以被新功能依赖。
- **compat**：仍被当前实现读取，但主要用于兼容旧数据；新设计不得扩大依赖。
- **legacy**：冻结遗留语义，只为旧 pipeline / 旧池保留。
- **retired**：已由明确变更退役；新写入不得使用，迁移后的正式 schema 不再保留。
- **unresolved**：当前资料或实现互相冲突；在决策前不得新增依赖、不得复用字段表达新含义。

## knowledge_points

| 字段 | 状态 | 语义 / 写入边界 | 当前主要消费者 |
|---|---|---|---|
| `kp_id` | active | 稳定、可读的知识点身份；创建后不可改 | 全部内容关联、URL、关系、练习 |
| `knowledge_item` | active | 知识点的正式可读名称，不是图谱专用短标签 | 知识点列表、详情页、当前图谱标题 |
| `graph_label` | **unresolved** | 原意是图谱短标签；当前可写、可入库，但主图模型仍使用 `knowledge_item` | 暂无可靠主消费者；不要让新功能依赖 |
| `source_location` | active | 知识点在源材料中的位置/出处指针；属于 provenance，不是 UI 标题 | 提取/审计/Agent 溯源 |
| `knowledge_type` | active | 内容/学习形态分类（concept/property、method/modeling 等）；**不是**练习交互模式 | 提取与内容规则 |
| `related_kp_ids` | **compat** | 旧式关系提示 JSON；当前图谱仍把它投影为 low-strength symmetric `related` 边 | 图谱兼容层 |
| `importance` | active | `core/supplementary/optional` 内容重要性，不代表掌握度 | 列表/图谱投影、规划 |
| `learning_action` | **legacy** | 提取阶段留下的学习动作/阅读提示字段；当前主工作台没有稳定展示契约 | 冻结 pipeline / 溯源 |
| `body` | active | 知识点正式正文 | 知识点详情页、Agent 内容读取 |
| `difficulty` | **legacy** | 旧知识内容复杂度 1–5；与正式题四维 objective difficulty 无换算关系 | 冻结 pipeline / 兼容查询 |
| `fragile` | active | 易错/脆弱点备注；保存内容本身，不产生学习事件 | 知识点详情、兼容编辑 API |
| `figure_paths` | **unresolved** | 该知识点引用的逻辑图片路径 JSON；**路径命名策略当前存在仓库级冲突** | 图像渲染/回滚 |
| `ingest_batch_id` | active | 受治理内容创建/导入的批次 provenance；原地 problem-patch 的修改批次另由批次清单记录，不保证覆盖此列 | 回滚/审计 |
| `created_at`, `updated_at` | active | 行生命周期时间戳；不得承载业务状态 | 审计/排序 |

### 知识关系双轨现状

正式关系事实存于 `knowledge_relations`。当前 live graph 同时读取
`knowledge_relations` 与 `knowledge_points.related_kp_ids`：前者生成正式语义边，
后者仅在不存在正式边时生成低强度对称兼容边。两者不是两个平级的新写入通道。

在后续决策明确前：
1. 新的可审计关系优先写 `knowledge_relations`；
2. 不得把 `related_kp_ids` 扩展成新的关系 schema；
3. 删除/迁移 `related_kp_ids` 必须先修改 live OpenSpec，因为当前行为规格仍显式读取它。

## knowledge_relations

| 字段 | 状态 | 语义 |
|---|---|---|
| `relation_id` | active | 稳定可读关系 id |
| `source_kp_id`, `target_kp_id` | active | 两端知识点；不得自环 |
| `relation_type` | active | `prerequisite/part_of/contrasts/generalizes/variant_of/applies_to` |
| `direction` | active | `directed/symmetric`；表示关系方向语义 |
| `strength` | active | `high/medium/low`，用于图谱 attraction 等投影 |
| `created_at`, `updated_at` | active | 审计时间戳 |

关系 CRUD 的正式入口是 workbench data/CLI 的关系操作；图谱布局不得反向创造关系事实。

## problems

| 字段 | 状态 | 语义 / 写入边界 |
|---|---|---|
| `problem_id` | active | 稳定可读题目身份；已有题必须原地修改，不能通过删后重导“换题号” |
| `kp_ids` | active | 题目关联知识点 JSON；内容轴，改变会清空客观难度评级 |
| `problem_text` | active | 完整题干；内容 identity 基于其规范化完整文本 |
| `solution` | active | 完整解析/解答；与 `source_answer` 分离 |
| `problem_type` | active | 学科/解题形态：calculation/proof/modeling/...；**不是判断/单选/多选** |
| `source_kind` | active | 依据材料类别：textbook/quiz/midterm/final/makeup/other |
| `origin_kind` | active | 题目相对依据材料的形成方式：`source_problem` / `adapted_problem` / `generated_grounded` |
| `exam_year` | active | 可空来源学年/年份标签；筛选使用四位年份前缀 |
| `source_evidence` | active | 支撑该题来源与内容真实性的证据文本 |
| `source_answer` | active | 来源材料自带的短答案/答案依据；不替代完整 `solution` |
| `solution_origin` | active | `source/generated`，说明详细解析由来源还是 Agent 产生 |
| `display_title` | active | 题目短标题；UI 标题，不是身份 |
| `topic_label` | **retired** | PR #106 已退役题目主题分组与该列；迁移移除 `problems.topic_label`，通用 problem 写入不再接受它。闪卡同名列仍保留，不属于本次退役 |
| `display_summary` | **unresolved** | 当前 ingest 允许 ≤200；旧 backfill validator 要求 ≤48 且长题才允许；当前主页面无实际消费 | 
| `practice_modes` | active | 存储的练习 shell 资格 JSON。空值 = exam-only；客观题时必须与 `micro_quiz.quiz_type` 相容 |
| `micro_quiz` | active | 客观交互 payload JSON：`quiz_type/options/answer_key/error_reason/source_evidence` 等；决定判断/单选/多选 |
| `figure_paths` | **unresolved** | 题目逻辑图片路径 JSON；文件命名策略存在仓库级冲突 |
| `difficulty` | active | 四维客观难度的派生 REAL 总分；不得由内容 ingest 直接赋值 |
| `difficulty_knowledge_breadth` | active | 客观难度：知识跨度 1–5 |
| `difficulty_reasoning_depth` | active | 客观难度：推理深度 1–5 |
| `difficulty_transfer_distance` | active | 客观难度：迁移距离 1–5 |
| `difficulty_construction_openness` | active | 客观难度：构造开放性 1–5 |
| `difficulty_model` | active | 难度汇总模型 id；六个 difficulty 字段必须全空或全有 |
| `ingest_batch_id` | active | 受治理内容创建/导入批次 provenance；原地修改的批次通过 problem-patch 清单与批次表追溯，不把该列视为最后修改批次 |
| `created_at`, `updated_at` | active | 行生命周期时间戳 |

### 三个最容易混淆的“题型”字段

- `problem_type`：这道题在学科上是什么形态（计算、证明、建模……）。
- `micro_quiz.quiz_type`：学生如何作答（yes/no、single choice、multiple choice）。
- `practice_modes`：这道题允许进入哪个练习 shell；是存储的 eligibility mark，
  对 micro quiz 必须与 `quiz_type` 一致。

任何 Agent 不得从 `problem_type` 推断客观题交互形式。

## flash_cards

| 字段 | 状态 | 语义 |
|---|---|---|
| `card_id` | active | 稳定可读闪卡 id |
| `kp_id` | active | 唯一所属知识点 |
| `front`, `back` | active | 一条原子 recall 的正反面内容 |
| `source_evidence` | active | 内容依据 |
| `topic_label` | active | 可选短标签 |
| `directions` | active | `["forward"]` 或 `["forward","reverse"]` |
| `ingest_batch_id` | active | ingest 批次 provenance |

## 与学习状态字段的边界

以下字段名称相似，但不是一个状态机，禁止互相覆盖或“统一”：

- `problem_attempts.status`：一次作答记录的状态，现代浏览器记录可为 `answered`；
- `problem_progress.status`：题目级 progress 投影（new/wrong/stuck/reviewing/mastered）；
- `learning_current_state.state`：知识点/题目的覆盖式学习状态（needs_work/review/mastered）；
- `review_schedule.state`：调度器内部阶段（learning/review/relearning）；
- `problem_attempts.verdict`：本次客观作答的对错事实，不是上述任何学习状态。

修改这些表之前，必须先读取对应 live OpenSpec；本文档目前只用于划清边界，不重写其完整状态转移规则。

## 字段变更纪律

任何持久字段的新增、删除、改名、枚举变化或语义变化，必须在**同一个 PR**：

1. 先修改/新增对应 OpenSpec 行为要求（若用户可观察行为改变）；
2. 同步本文档的字段语义、状态、writer/consumer；
3. 若 Agent 工件形态改变，同步 `FILE_CONTRACT.md`；
4. 若出现新设计名词，同步 `docs/GLOSSARY.md`；
5. 若用户操作或展示改变，同步 `docs/PRODUCT-MANUAL.md`；
6. 最后使 schema、Domain/Data、CLI/Server 与这些契约一致。

禁止：
- 因为“数据库里已有这个列”就赋予它新含义；
- 新增一个近义字段绕过旧字段的语义冲突；
- 从 archive change 推导当前字段含义；
- 把本次审计快照当成长期规范。
