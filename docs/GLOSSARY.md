# GLOSSARY — 全局术语表（定义文档）

> **本文档是全部设计名词的唯一权威定义源。** 纪律（AGENTS.md 同步）：
> 正式文档（openspec specs、proposal、REQUIREMENTS、PRODUCT-MANUAL）引入新名词前，
> 必须先在这里建条目；还没有定义的概念一律先进 `docs/PENDING-DEFINITIONS.md`，
> 不允许以未定义状态混入正式文档。
>
> 条目格式：`### 中文名 / english_term` + 定义 + _Avoid_（易混淆的错称）+ 出处。
> 英文术语与 openspec specs（英文正文）对应；中文界面文案以本表中文名为准。
> 行为细节以 openspec 规格原文为准，本表只承担「名词是什么」。

---

## 内容与池

### 知识池 / Knowledge Pool
课程级的 SQLite 存储（`pool/<course>.db`），保存提取好的知识点、正式题与全部学习状态。整个工作台的数据底座。
_Avoid_：章节数据库、压缩包版本
出处：CONTEXT.md（迁入）；pool_schema.py

### 知识点 / Knowledge Point
从源材料中提取、入池的可复用知识单元，是练习、调度、图谱、信号的共同挂载对象。每章一章（如 `dmath-ch06-kp-001`）。
_Avoid_：卡片、笔记条
出处：CONTEXT.md（迁入）；openspec/specs/review-workbench

### 知识关系 / Knowledge Relation
两个知识点之间经审核的点对点边（如 prerequisite / applies_to / contrasts / variant_of），存于 `knowledge_relations`。图谱的事实层。
_Avoid_：算法臆造的关系、隐藏关系
出处：CONTEXT.md（迁入）；review-workbench spec「Semantic graph attraction」

### 正式题 / Problem（durable problem）
作为独立学习资产入池的练习题：题干、关联知识点、来源类型、题型、解析（非空，过门禁后入库）。只读练习，不是待审稿。
_Avoid_：练习册条目、题目草稿
出处：CONTEXT.md（迁入）；review-workbench spec「Problem pull engine」「Formal problems are reveal-ready」

### 候选题 / Problem Candidate
**已退役（2026-08-30 remove-candidate-store）**：概念与机制整体移除，候选题不复存在。
历史含义（留档）：尚未进入正式题池的、有源可依的练习条目；先后过结构门禁与审计门禁，
再经显式晋升（promote）成为正式题。
状态注记（2026-08-29 专题 22）：随 Check 管线立项退役——pull/mastery/hub 停止读取。
状态注记（2026-08-30）：观察期结束，所有者拍板物理清除——candidate_problems 表 DROP、
`wb data` 的 candidate 实体与 gate/promote 动作移除；Agent 内容唯一通道为 Check 管线
（见「Check 管线」条目）。

### Check 管线 / Check pipeline
内容入池的唯一 Agent 通道（原名 generate 桥）：Agent 产出合规 manifest → 确定性门禁校验 → **直接入正式池**（无候选中间态）。每次 apply 记批次 id、内容行带批次标记，整批回滚是安全网；门禁失败逐条显式报错、零写入。Agent 可直接触发（CLI 或对话桥 `check_ingest` 动作），门禁是决断辅助不是权限闸门；AI 永不直写池数据库。
_Avoid_：generate 桥（旧称）、候选中间态、staging 区、逐题人工确认
出处：DISCUSSION-RECORD 专题 20/21/22；workbench-content-governance spec（introduce-check-pipeline）

### 来源类型 / Source Kind
正式题的出身大类：textbook / quiz / midterm / final / makeup / other。
_Avoid_：考试年份、作者
出处：CONTEXT.md（迁入）

### 题目尝试 / Problem Attempt
与一道正式题的一次被记录的交互，保存当时的作答文本、卡点标记与评分。只有显式提交自评才产生。
_Avoid_：当前状态、浏览记录
出处：CONTEXT.md（迁入）；review-workbench spec「Practice session」

## 工作区与工作台

### 工作区 / Workspace
一个 lesson-kit 文件夹的注册身份：名称 → 文件夹路径、池数据库、激活的课程/章节。注册表在用户级 `~/.lessonkit-workbench/`。
_Avoid_：项目、数据库别名
出处：review-workbench spec「Workspace registry」

### 工作台 / Workbench
浏览器里的学习界面：三栏壳层（左导航 + 中页面 + 右 Agent 对话），三个页面——练习 / 知识点 / 知识图谱。三页导航是两次在案决定（DISCUSSION-RECORD 专题 17、B6.2）与专题 18/19 的既定模型。
_Avoid_：第四个页面、复习页（已废弃）
出处：workbench-ui spec Purpose；DISCUSSION-RECORD 专题 18/19

## 选择与练习

### 范围 / Scope
用户在知识点页或图谱中**显式勾选**的知识点集合，是练习内容的唯一合法来源；存在工作区会话存储（`wb_kp_selection_{ws}`）。弱项排序、每日建议都不得隐式扩大范围。
_Avoid_：弱项自动抓题、隐式范围
出处：REQUIREMENTS.md 2026-08-28 段；consolidate-practice-views（专题 19）

### 准备练习列表 / Staged Practice List
练习页上唯一「真正要练的」清单 = 当前范围（选区）的行视图：每行知识点名 + ✕ 清除，与知识点页/图谱勾选双向同步。零独立存储。
_Avoid_：今日计划队列（旧称，已解散）、自动合流列表
出处：DISCUSSION-RECORD 专题 19 第 1 条；workbench-ui spec「Practice page staged list and on-demand suggestions」

### 建议 / Suggestion
练习页上**按需拉取**的今日练习建议：计划队列 ∪ 到期调度映射到知识点级去重后的结果。行 = 名称 · 一个短语 · 加入；已选定的不出现在候选中；不常驻、不做独立页面。
_Avoid_：候选题（Problem Candidate 的中文名带「候选」，两回事）、到期列表（已废弃的常驻视图）
出处：专题 19 第 2 条；workbench-ui spec 同上

### 原因短语 / Reason Phrase
建议行里的唯一一句人话解释：`拖了 N 天`（逾期）/ `今天到期` / `覆盖仍低`（计划命中，沿用计划原因文案）。纯函数生成，零调度参数外露，不拼接。
_Avoid_：徽标、日期数字、ease/interval 等裸参数
出处：consolidate-practice-views design D2（修订版）

### 练习模式 / Content Mode
一轮练习的题型入口，四选一：综合题（exam）/ 小测（micro）/ 判断（yes_no）/ 闪卡（flash_card）。每次会话只允许一种。**「practice path」是它在旧计划语境的别名，统一以本条为准。**
_Avoid_：practice path（旧别名）、答题方式
出处：workbench-ui spec「Practice page」；daily-learning-plan spec（别名裁决）；introduce-flash-card

### 综合题模式 / Exam Mode
练习模式之一：按范围拉取常规正式题，作答 → 查看解析 → 1–5 自评。未标注 practice_modes 的存量题只在此模式可用。
_Avoid_：考试模式（不是考试，是常规练习）
出处：review-workbench spec「Problem pull engine」「Grading input modes」

### 小测模式 / Micro Mode
练习模式之一：微题的选择题点选（single_choice / multiple_choice），提交后浏览器本地判分、显示对错与错因，之后仍走 1–5 自评。只拉取标注 micro 可用的微题，无内容时如实空态。**原名「闪卡模式」，2026-08-29 正名出让**：该模式实为微题的卡片式渲染，不是记忆卡。
_Avoid_：闪卡（旧称，现指另一功能）、自由文本作答（微题一律点选）
出处：introduce-flash-card；micro-quiz-content spec

### 闪卡 / Flash Card
从知识点解构出的键值对记忆卡（类似 dict 的一条键值对）：正面（front）→回忆→揭示背面（back）→1–5 自评，无选项、无判分。知识点是唯一事实源（Note），卡是派生视图（Card），一卡只放一个原子事实；每卡一行独立调度。练习会话第四种模式的练习对象；也可用于背单词、背概念等场景。AI 自动解构知识点成卡（含 cloze 挖空成卡，见 DISCUSSION-RECORD 专题 22 澄清）属 Check 管线后置实验，不在当前范围。
_Avoid_：小测（微题的卡片式渲染，旧「闪卡」）、方向卡（已拆除 UI）、普通题冒充
出处：introduce-flash-card；openspec/specs/flash-card（随归档落位）

### 判断模式 / Yes-No Mode
练习模式之一：判断题（是/否），选择后浏览器本地立即判分并显示错因；判分只是即时反馈，不写学习记录，之后仍走 1–5 自评。只拉取标注了 yes_no 可用的微题（quiz_type = yes_no），无内容时如实空态。
_Avoid_：机器批改作业（只判对错，不产生学习结论）
出处：micro-quiz-content spec；workbench.js gradeMicroQuiz

### 自评时机 / Rating Mode
二选一：每题作答后自评（immediate）或 完成后统一自评（batch）。开始练习前必选。
_Avoid_：评分方式（与 1–5 自评本身混淆）
出处：workbench-ui spec「Practice session」

### 练习会话 / Practice Session
一次进行中的练习：单一练习模式 + 不重复的题目队列 + 当前题 + 已见题集合。标签页级存在（sessionStorage），刷新同标签页可恢复；关闭标签页不留任何未提交记录。
_Avoid_：Agent 对话会话（另一个「会话」，见该条）
出处：review-workbench spec「Practice session」「Session interruption recovery」

### 自评 / Self-Rating
学习者对一道完成题的显式 1–5 打分（可带自然语言备注）。是唯一触发学习记录（反馈事件、信号、进度、调度）的动作。
_Avoid_：客观题自动判分（micro quiz 的前端判分，不写记录）、浏览即记录
出处：review-workbench spec「Flexible feedback」

### 揭示再自评 / Reveal-then-Rate
开放题的作答约定：先自己作答 → 查看解析 → 再打分。系统不自动判开放题。
_Avoid_：机器判卷
出处：review-workbench spec「Grading input modes」

### 跳题 / Skip
不提交任何记录跳到下一题。跳题、草稿、查看解析、翻看计划都**不写**任何学习记录。
_Avoid_：放弃（无贬义，也无记录代价）
出处：review-workbench spec「Practice session」

### 会话末统一自评 / Unified (Session-End) Rating
batch 时机下的收束页：只列尚未评分的题，逐题补 1–5 分或跳过全部，一条「再练同类」入口。
_Avoid_：批量评分历史、补打卡
出处：DISCUSSION-RECORD B6.5；workbench-ui spec

### 微题 / Micro Quiz
带结构化载荷的短题干快反馈题：一个原子知识点 + 显式练习模式标记 + 结构化载荷（题型、选项、答案关键、错因、来源证据）。三种题型：yes_no / single_choice / multiple_choice，一律点选作答（short_answer / closest_answer 已于 2026-08-29 退役）。客观题在前端本地判分，判分本身不写学习记录。
_Avoid_：小题（口语）、判断题系统（判断只是题型之一）、填空作答
出处：openspec/specs/micro-quiz-content/spec.md

### 答案关键 / Answer Key
微题载荷里的标准答案字段（是/否、选项、答案串）。前端比对判分用，不展示为解析。
_Avoid_：解析（solution，正式题的完整解答）
出处：micro-quiz-content spec；workbench/domain/micro_quiz.py

## 记录、调度与提醒

### 学习信号 / Learner Signal
一条学习者注意力信号（如 confusion / weak_node），挂在知识点上，只增不自动消除；证据层，重复做错会加强。由显式自评（通常 1–2 分）或备注映射产生。
_Avoid_：Signal Map（旧称，退役）、尝试历史
出处：CONTEXT.md Learner Signal（更新）；review-workbench spec「Cascade signal boosts」

### 当前学习状态 / Current State
知识点或题目的覆盖式当前值：`needs_work`（重点练习）/ `review`（可以复习）/ `mastered`（掌握）。图谱直接编辑只替换该值并经对应评分更新调度，不追加历史事件。
_Avoid_：掌握度百分比、历史轨迹
出处：review-workbench spec「Current learning state」

### 调度 / Scheduling
每条学习项一行调度状态（repetitions / ease / interval_days / due_at / last_rating），SM-2 变体，按（item_type, item_id, direction）为键；方向行各自独立推进。调度**只影响排序与建议**，永不隐藏、锁定、拒绝任何内容，参数永不对学生露出。
_Avoid_：锁题机制、记忆曲线展示
出处：review-workbench spec「Forgetting-curve scheduling as background」

### 到期 / Due
一条调度行的 due_at 日期已到（≤ 今天）；早于今天为「逾期」。到期项以**按需建议**形式出现（非常驻列表、无独立复习页）。
_Avoid_：复习页、到期分组列表（均已废弃）
出处：专题 19；review-workbench spec（consolidate 修订版）

### 行动提醒 / Action Reminder
学生可见的三态提醒词：有明确薄弱证据 → `重点练习`；无薄弱证据但到期 → `可以复习`；其余保持中性（不显示任何掌握断言）。这是学生侧唯一允许的状态词汇。
_Avoid_：掌握度、分数、调度参数
出处：review-workbench spec「Action-oriented learning reminders」

### 弱项 / Weak Point（weakness score）
按学习者信号与到期状态推导出的知识点排序权重：分数只调顺序，不过滤，任何知识点都不会被藏掉。**规格未定义具体公式**，属排序实现细节。
_Avoid_：成绩、能力值
出处：review-workbench spec「Weak knowledge point list」

### 方向 / Direction
记忆回忆类知识点的练习朝向（如中→英、英→中）。每个方向是独立学习动作、独立调度行；评分可携带 direction 写对应方向行。方向卡 UI 已随复习页拆除，待真实使用再议（专题 19）。
_Avoid_：正反面卡片页（已拆除的 UI）
出处：review-workbench spec「Directional schedule entries」

## 目标、计划与时间

### 目标 / Goal
真实持久化的学习目标，两种：长期目标（long_term）与阶段目标（stage），含标题、截止日期、可选说明。目标卡只展示真实数据，不虚构课程目标。
_Avoid_：系统生成的课程规划
出处：daily-learning-plan spec；REQUIREMENTS.md 2026-08-28 纠偏段

### 每日计划 / Daily Plan
确定性基线算法产出的当日粗粒度建议队列（最多三项），每天首次打开自动重算一次、可手动重算。**专题 19 后计划输出降为「建议」的来源之一**，不再作为独立卡片展示。
_Avoid_：精细操作手册、强制任务单
出处：daily-learning-plan spec；专题 19 第 2 条

### 覆盖 / Coverage
「知识点被练习/掌握的程度」的统称。**规格未定义计算公式**；目标卡的覆盖进度、计划的覆盖仍低短语都引用此概念。
_Avoid_：正确率、完成度百分比（未经定义前不使用具体数字承诺）
出处：daily-learning-plan spec；consolidate-practice-views design D2

### 重日 / Heavy Day
14 天任务量柱状里被标「重」的日子：当日到期项数达到非零日均值的两倍（且有项）。出现重日时给出一个「让 Agent 看看」动作，把重排请求预填进 Agent 输入框（不发送）。
_Avoid_：自动重排（视图只读，重排永远由你发起）
出处：calendar-workload spec「Calendar and workload view」

### 时间安排 / Time View
练习页右栏的实验性只读视图：目标月历（deadline 落格、可堆叠、今日高亮）+ 14 天任务量柱状。重日（某天到期数 ≥ 非零日均 2 倍）标「重」，可一键预填重排请求到 Agent 输入框（不发送）。只读，不改任何数据。
_Avoid_：日历应用、自动重排
出处：openspec/specs/calendar-workload/spec.md

## 图谱

### 知识图谱页 / Knowledge Graph Page
工作台第三页：章节知识点的力导向图，支持搜索、投影切换（关系结构/题目数量/重要性/学习状态）、聚拢滑杆、缩放、节点勾选（与选区同步）与学习看板。默认关系布局，不持久化坐标。
_Avoid_：Obsidian、数据库编辑器
出处：workbench-ui spec；REQUIREMENTS.md 2026-08-27 段

### 课程知识网络 / Course Learning Network
课程范围的知识点网络：已审核的知识点 + 已审核的知识关系 + 查询时的图谱发现。图谱页是它在工作台的可视化。
_Avoid_：人生地图、最终本体
出处：CONTEXT.md（迁入）

### 图谱发现 / Graph Finding
查询时从课程知识网络推导出的临时发现（最短路、共同邻居、桥节点等），除非后续审核，不固化为关系。
_Avoid_：提取出的事实
出处：CONTEXT.md（迁入）

### 级联增强 / Cascade Boost
排序时的查询期推导：有信号的知识点沿 prerequisite / applies_to / part_of 边反向增强相邻点，最多 2 跳、每跳衰减 0.5、按关系强度加权。推导**绝不写**学习信号表，且须在界面说明原因。
_Avoid_：伪造证据、自动标弱
出处：review-workbench spec「Cascade signal boosts」

## Agent 对话

### Agent 对话会话 / AI Conversation
右栏的师生对话：一个 provider 固定的会话流。**「会话」在此指对话，与练习会话（Practice Session）严格区分。**
_Avoid_：练习会话（同词两义，注意上下文）
出处：workbench-ui spec；ai-teacher-bridge spec

### Agent 提供方 / Provider
一次 Agent 对话创建时固定选择的底层 AI 服务。创建后不可更换；未配置 provider 时如实提示。
_Avoid_：模型热切换、多模型混用
出处：workbench-ui spec；ai-teacher-bridge spec

### 讲解 / Explain、诊断 / Diagnose（已移除）
曾是与题相关的两种桥任务，2026-08-29 经所有者问卷决定彻底移除（Agent 上下文本就是整个版面，无需按题特化）；想聊某道题直接在对话里说。
_Avoid_：任何按题特化的预设任务按钮
出处：remove-explain-diagnose 归档；DISCUSSION-RECORD 问卷记录

### 桥 / Bridge
工作台与外部 AI 会话的旁挂通道：只被请求时运行，产物流式回传；工作台核心零 AI 依赖（无 provider 时优雅降级）。
_Avoid_：内嵌大模型、常驻后台进程
出处：ARCHITECTURE.md；ai-teacher-bridge spec

### 动作图谱 / Action Graph
系统全部「能做的事」（用户操作、CLI 命令、API 动作、桥操作、门禁配方）的常设登记文档：每个动作登记入口、读写面、状态（已实现/已定义未实现/未定义挂名/冻结/待退役）与权威出处，并给出六域关系总图。名词归 GLOSSARY/PENDING 管，动作归本图管；功能变更交付时必须同步。
_Avoid_：把动作清单散落在各 spec 里不登记、用浏览器操作代替明文
出处：docs/ACTION-GRAPH.md；DISCUSSION-RECORD 专题 20 后所有者 2026-08-29 提出

### 目标助填动作 / prefill_goal_form
目标表单发起一句话求助时，Agent 回复可附的结构化动作：仅 goal_intent 请求可生效，字段（title/kind/deadline/description）经服务端契约校验后原位填进表单，提交仍由人完成。
_Avoid_：普通对话代填、跳过人确认直接创建
出处：complete-goals-loop 归档；ai-teacher-bridge spec

### 出题入库动作 / check ingest action
Agent 对话中触发出题入库的结构化动作：仅出题/补池意图（check_intent）请求可生效，Agent 在回复末尾附内联 manifest（flash-card-patch / micro-quiz-patch），服务端过既有确定性门禁后直接入正式池并记批次 id；成功以独立结果卡片呈现（批次号、计数、备份路径、回滚按钮），门禁失败逐条显式呈现、零写入。
_Avoid_：静默丢弃失败清单、跳过门禁直写池、显式命令面板
出处：DISCUSSION-RECORD 专题 21 第 5 条、专题 22 第 5 条；ai-teacher-bridge spec（introduce-check-pipeline）

### 批次 id / Batch id
一次门禁 apply 写入池的那批内容的唯一标识（可读顺序 id，形如 batch-NNN，禁哈希）；批次内每一内容行携带该标记，用于事后溯源与整批撤销。
_Avoid_：内容版本号、逐条审计日志、哈希 id
出处：DISCUSSION-RECORD 专题 20/22；workbench-content-governance spec「Batch provenance and rollback」

### 整批回滚 / Batch rollback
按批次 id 一条命令撤销该批全部内容行的安全网（`wb ingest rollback --batch <id>`，对话桥结果卡片回滚按钮同源）；回滚前自动做安全备份，回滚后输出 accounting 核对。批次内容行已有练习/反馈记录时拒绝回滚并如实报错。
_Avoid_：逐条手工删行、全池回退、静默丢弃练习记录
出处：DISCUSSION-RECORD 专题 20/22；workbench-content-governance spec「Batch provenance and rollback」

## 工程与流程

### 运行时状态 / Runtime State
仓库内 `.lessonkit/state.yaml` 检查点：激活课程/章节、命令、阶段、必需产物、最近门禁结果、阻塞与下一步。命令按 CWD 在仓库根运行。
_Avoid_：池数据、事实来源
出处：CONTEXT.md（迁入）；AGENTS.md 运行时约定

### 阶段守卫 / Phase Guard
脚本强制的检查：判定某命令的必需产物与检查文件是否齐全，决定能否进入下一阶段。
_Avoid_：人工审阅、完工宣言
出处：CONTEXT.md（迁入）；AGENTS.md 验证节奏

### 门禁 / Gate
内容入库前的确定性检查。正式题候选过结构门禁 + 审计门禁两道；micro-quiz 清单过 `_gate_micro_quiz`、flash-card 清单过对应门禁（契约 + 标记安全 + 与库比对），失败即整体拒绝、零写入。
_Avoid_：人工抽查、事后补审
出处：review-workbench spec「Past-paper coverage gate」；micro-quiz-content spec；workbench/ingest

### 走查 / Scratch Walkthrough
交付前的真实浏览器验证：在池数据库副本 + 隔离注册表 + 独立端口上种子数据逐项点检（截图自检清单）。**永不写真实池。**
_Avoid_：测试通过即完成（明确的反模式）
出处：2026-08-29 交接文档；FUTURE-DEVELOPMENT-NOTES UX 清单
