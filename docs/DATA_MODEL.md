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
| `figure_paths` | **unresolved** | 该知识点引用的逻辑图片路径 JSON；**路径命名策略当前存在仓库级冲突**。`data.content_mirror` 可在显式 JSON 同步中写入通过既有路径校验的引用；`data.figure_mirror` 只读消费池引用并同步图像文件 | 图像渲染/回滚、`data.content_mirror`、`data.figure_mirror` |
| `ingest_batch_id` | active | 受治理 ingest/apply 的批次 provenance；原地修改的批次不保证覆盖此列，不能当作通用最后修改标记 | 回滚/审计 |
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
| `display_summary` | **unresolved** | 当前 ingest 允许 ≤200；旧 backfill validator 要求 ≤48 且长题才允许；当前主页面无实际消费 | 
| `practice_modes` | active | 存储的练习 shell 资格 JSON。空值 = exam-only；客观题时必须与 `micro_quiz.quiz_type` 相容 |
| `micro_quiz` | active | 客观交互 payload JSON：`quiz_type/options/answer_key/error_reason/source_evidence` 等；决定判断/单选/多选 |
| `figure_paths` | **unresolved** | 题目逻辑图片路径 JSON；文件命名策略存在仓库级冲突。`data.content_mirror` 可在显式 JSON 同步中写入通过既有路径校验的引用；`data.figure_mirror` 只读消费池引用并同步图像文件 |
| `difficulty` | active | 四维客观难度的派生 REAL 总分；不得由内容 ingest 直接赋值，显式评级与 JSON 镜像均须使用既有难度校验 |
| `difficulty_knowledge_breadth` | active | 客观难度：知识跨度 1–5 |
| `difficulty_reasoning_depth` | active | 客观难度：推理深度 1–5 |
| `difficulty_transfer_distance` | active | 客观难度：迁移距离 1–5 |
| `difficulty_construction_openness` | active | 客观难度：构造开放性 1–5 |
| `difficulty_model` | active | 难度汇总模型 id；六个 difficulty 字段必须全空或全有 |
| `ingest_batch_id` | active | 受治理 ingest/apply 批次 provenance；`problems` recipe 会在已有行上更新该列，problem-patch 与通用直接编辑不保证更新；后两者不把该列视为通用最后修改批次 |
| `created_at`, `updated_at` | active | 行生命周期时间戳 |

对知识点与题目的 `figure_paths`，`data.content_mirror` 是受治理的 JSON 引用 writer：写入前复用现有课程相对路径规则预检两侧引用；它不创建、复制或改名图像字节。`data.figure_mirror` 仍只读消费池引用并按显式方向同步文件。现有文件名主体为 64 个小写十六进制字符的路径继续按 `knowledge-figures` 的内容哈希身份处理；mirror 在无法从现存副本保留该身份时拒绝同步。全仓库的图片命名策略仍为 unresolved。

正式题的四维难度、派生总分与模型必须全空或全有。`data.difficulty.check/apply` 保持现有校验/事务 authority；`data.content_mirror` 只在显式仓库同步时接受四维评级，先调用 `data.difficulty.check` 重算总分与模型，再在其逐实体事务内写入完整组。内容轴变更清除当前池投影中实际存在的难度列；旧 schema 不迁移列，显式评级要求完整组。

已删除字段：`problems.topic_label`。schema ensure 物理删除旧池同名列，重建表也不含该列；
这取代 PR111 的普通 ensure 保留语义。历史值仅可留在数据库之外的恢复备份，不能留在当前池
的替代列或表中。problem manifest 与 patch 继续拒绝该字段，搜索与 UI 不使用它。
独立的 `flash_cards.topic_label` 及其历史值保持 active，不受题目列删除影响。

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

## content_mirror_state / content_mirror_log（作者内容镜像台账）

两张表由 `pool/scripts/pool_schema.py` 的 `ensure_content_mirror_schema` 增量创建，
只服务 `workbench/data/content_mirror.py` 的本地 JSON 作者内容投影；不存哈希、指纹
或 Git 对象 id。它们是同步**状态与成功记录**，不是第二份内容，也不是学习者状态。

| 字段 | 表 | 状态 | 语义 / 写入边界 | 当前主要消费者 |
|---|---|---|---|---|
| `entity_type`, `entity_id` | state | active | 复合主键；只限 `kp`/`problem`/`relation`（CHECK 约束）。id 是语义身份，与文件路径无关 | 镜像规划/应用器 |
| `revision` | state | active | 最后同步的作者内容正整数修订号；只随被接受的修改 +1，不倒退、不由哈希派生 | 三方比较（池/仓库/记住的内容） |
| `content_json` | state | active | 上次同步的规范化作者内容 JSON（排序键、无哈希）；比较基线 | `mirror check/status/sync` |
| `updated_at` | state | active | 行生命周期时间戳 | 审计 |
| `entity_type`, `entity_id` | log | active | 同 state；只追加成功记录 | 审计 |
| `direction` | log | active | 成功方向枚举（CHECK）：`init` / `repo_to_pool` / `pool_to_repo` / `restore_repo_file` / `recover_converged` | 审计/证据 |
| `from_revision`, `to_revision` | log | active | 该次成功同步的前后修订号；`from_revision` 可为空（首次），`to_revision` 必须为正 | 审计 |
| `created_at` | log | active | 行生命周期时间戳 | 审计 |

写入边界：只有 `data.content_mirror` 的受治理路径写这两张表；`repo_to_pool` 的内容更新、
状态与成功日志在同一个池事务内提交，失败一起回滚，其余方向以「中断后下一次比较能收敛
或可重试」的顺序推进状态与文件。`mirror check`、`status`、`sync --dry-run` 零写入；
失败/冲突/无效不写日志行。闪卡实体、图片字节与学习者/运行时状态不进入镜像台账；
作者内容 JSON（包括经校验的逻辑图像引用和可用的题目难度组）属于比较基线。

## 与学习状态字段的边界

以下字段名称相似，但不是一个状态机，禁止互相覆盖或“统一”：

- `problem_attempts.status`：一次作答记录的状态，现代浏览器记录可为 `answered`；
- `problem_progress.status`：题目级 progress 投影（new/wrong/stuck/reviewing/mastered）；
- `learning_current_state.state`：知识点/题目的覆盖式学习状态（needs_work/review/mastered）；
- `review_schedule.state`：调度器内部阶段（learning/review/relearning）；
- `problem_attempts.verdict`：本次客观作答的对错事实，不是上述任何学习状态。

修改这些表之前，必须先读取对应 live OpenSpec；本文档目前只用于划清边界，不重写其完整状态转移规则。

### Attempt 状态约束迁移与外键修复

`pool/scripts/pool_schema.py` 的 `ensure_workbench_schema` 在其他 ensure 写入前，
扩展旧 `problem_attempts.status` 的枚举 CHECK 并修复指向
`problem_attempts_widening_old` 的子表声明。无枚举 CHECK 的旧表已允许 `answered`，无需重建。
重建沿用原始 DDL，保留额外列、约束、行值、ID、自增序号、索引和触发器；现代可空字段仍由
既有列增量路径补齐。不重命名原父表，因此健康的其他入向引用保持原目标。

迁移使用 savepoint，失败回滚本次结构和数据改动；保留调用方的 `foreign_keys` 与
`legacy_alter_table` 设置。外键开启且调用方已有事务时，在写入前拒绝，调用方必须先自行处理事务；
外键关闭时允许嵌入现有事务，不提交调用方写入。健康当前结构重复执行无变化。
结构修复后执行外键检查；缺失父记录以 `RuntimeWarning` 报告表、行及可解析的缺失 attempt ID，
保留子记录，不补造作答，不删除进度。结构修复成功不等于学习证据恢复。

## Paper 执行来源与持久化边界

保存的 Paper 是工作区 `.lessonkit/practice-sets/` 下的 JSON 记录，不是 SQLite 行或学习状态。
`data.practice_sets.save_manifest` 校验导出的练习清单及其课程，再委托给现有原子 JSON 写入器
`create_saved`。保存记录保留题目顺序与 request 元数据；这条写入路径不改 SQLite。

`active_practice.source_kind` 与 `practice_runs.source_kind` 的新执行值为 `paper`：
一个 Paper 在开始执行前固定有序题目，来源筛选或组卷方式不构成另一种执行类型。
`data.active_practice.create` 写入 `paper`；完成、替换或清除时，
`data.active_practice._archive` 也将新快照写成 `paper`，即使迁移后仍在执行的旧 active 行保留了历史来源值。

`active_practice.practice_mode` 与 `practice_runs.practice_mode` 是界面的兼容选择 / 渲染元数据，
不是 Paper 身份或题目队列。schema 没有枚举 CHECK；Data writer 只要求非空字符串，并在开始、归档与重放时保留该值。
当前浏览器选项是 `exam`、`micro`、`yes_no`、`flash_card`；保存 Paper 的 start API 接受前三者，
记录读取器原样返回该字段，记录页为这四个值显示对应标签。固定题目身份与顺序分别存于保存 Paper、
`active_practice_items` 与 `practice_runs.items_json`；`practice_mode` 不构造或动态补充执行队列。
它不同于题目能力字段 `problems.practice_modes`；`rating_mode` 则单独表示反馈时机。

v1 兼容输入和历史行可保留 `quick`、`practice_set`、`agent`。schema 增量迁移只扩展两个字段的
CHECK 约束，并按下节添加独立进度字段，保留已存在的 active 行与 `practice_runs` 历史值；读取或重放旧轮次不会改写旧行。
既有工作区必须先显式运行池迁移，再使用 Paper 执行写入：
`python pool/scripts/migrate-progress.py --db pool/dmath.db`（将数据库路径替换为该工作区的池路径）。
表已存在不代表旧 `source_kind` CHECK 已接受 `paper`；`lesson-kit doctor` 与正常启动均不自动迁移。
`data.active_practice.replay` 读取这两类来源的历史轮次，使用归档的固定题目顺序开始新的
`paper` 执行。已保存 Paper 通过 `source_ref` 保留稳定 `ps-NNN` 身份，`source_label` 保存标题。

`data.records._practice_sets` 汇总已完成的保存 Paper 轮次：读取新 `paper` 行与旧
`practice_set` 行，并按 `source_ref` 的保存 Paper ID 分组；临时或其他未关联保存 Paper 的
`paper` 轮次不进入该分组。逐题作答、自评仍只由 attempts / feedback 提供学习证据。

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

## Paper 独立进度与题目历史身份

以下字段均为 active，经 `ensure_workbench_schema` 显式增量迁移；正常启动不自动迁移。

| 表/字段 | 语义 | writer / consumer |
|---|---|---|
| `paper_state.paper_id/generation` | 稳定 ps-NNN 和递增结构版本；删除后保留身份禁止复用 | Data Paper / 提交校验 |
| `paper_state.checkpoint_json` | 暂停卷的执行快照：题序、游标、状态、attempt 关联、草稿与版本；选中卷在 active 表 | Data 切卷/修题/删题 |
| `paper_state.pending_json/pending_delete` | 与进度变动同事务提交的待发布 JSON/删除意图；提交后幂等发布，后续读取恢复 | Data 文件协调 |
| `practice_execution_ids.id` | 自增执行身份，不复用 | Data 执行器 |
| `active_practice.execution_id/paper_generation` | 选中执行及对应结构版本 | Data 执行器 / 浏览器上下文 |
| `active_practice_items.content_revision` | 该题作答内容版本 | Data 修题 / 提交校验 |
| `active_practice_items.draft_json/draft_sequence` | 未提交文本/选择草稿和单调顺序；迟到写入拒绝，不是学习事实 | 浏览器经 Data 保存 / 恢复 |
| `problem_revisions.problem_id/revision` | 作答语义版本，缺行等价 1 | 共用 Data 更新规则 / 提交校验 |
| `practice_runs.execution_id/paper_generation` | 归档执行及结构版本；旧 execution_id 可为空 | Data 归档 / 反馈校验 |
| `problems.deleted_at` | 空为当前题，非空为历史保留题目；保留 ID，当前查询/修改排除 | Data 删除 / 记录页 |

旧健康 active 执行只补执行身份和默认版本，不改题序、attempt 关联或学习表。旧缺失引用显式报告，不补造或重绑。
题面、选项、答案键、作答类型/能力变化仅重置各未完成卷中的该题及其草稿；解析、标题、KP、来源、难度变化不重置。
手工改卷名单/题序须精确影响预览确认，重置该卷未完成状态；删题清当前引用是例外，保留其他题进度。
这些操作不删除或重新判分历史 attempts、反馈、信号、学习状态、调度和已归档轮次。删卷保留历史 source_ref/source_label，记录读取派生已删除状态。
浏览器提交的 `practice_context` 包含 execution_id、paper_id、paper_generation、item_id、content_revision、position；学习写入前核验。
本地草稿失败出站箱键 `wb_paper_draft_<workspace>_<execution_id>_<position>` 保留未确认写入；恢复要求上下文匹配，确认相同版本才清除。

## 本地图谱布局种子（浏览器缓存）

这不是 SQLite 字段、作者内容或学习事实。浏览器键为 `lk_graph_layout_v1_<workspace>`；当前页面没有工作区标签时使用 `lk_graph_layout_v1_default`。值为 JSON：`version` 是数字 `1`，`identity` 是可读拓扑 JSON，`positions` 是节点 ID 到 `[x, y]` 坐标的对象（有限坐标按 0.1 像素取整）。

`identity` 包含排序后的节点 ID 字符串，以及排序后的关系元组字符串 `source|target|type|direction`；它不包含关系强度、标题、指标或学习状态。`workbench/server/static/graph-physics.js` 是该键的唯一 reader/writer：在 Worker 首次报告布局稳定时写入一次；创建图谱时只读取版本与身份完全匹配的值，并把坐标作为临时锚点送入同一 Worker，随后释放锚点并继续求解。

清除、损坏、过期或无法读取/写入该键时，布局种子缺席，图谱仍从原确定性 Worker 初始化开始。失去此缓存只会失去显示布局的起点，不会删除或改变 Pool、作者内容或学习记录。这里没有 SQLite schema 变化。
