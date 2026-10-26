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

## 契约治理

### 契约权威 / Contract Authority
某一类事实的规范定义由指定职责文件承担：live OpenSpec 定义可观察行为，DATA_MODEL 定义持久字段，FILE_CONTRACT 定义交换工件，ARCHITECTURE 定义分层，PRODUCT-MANUAL 说明用户操作。本术语不表示一个文件可以覆盖其他职责，也不按更新时间决定权威。
出处：AGENTS.md「契约权威与冲突处理」

### 契约漂移 / Contract Drift
职责文件或实现证据对同一事实给出互相冲突的定义。必须显式登记，由该事实的契约拥有者协调；历史审计记录不是当前规范。
出处：AGENTS.md「契约权威与冲突处理」

### 契约协调 / Contract Reconciliation
交付行为、字段、接口或工件变更时，核对并同步被该变更影响的职责文件；未决冲突保留为明确的后续决策，不以代码现状或文件日期静默裁决。
出处：AGENTS.md「开发纪律」；docs/DATA_MODEL.md「字段变更纪律」

## 内容与池

### 工作区布局 / Workspace Layout
Lesson Kit 在一个课程工作区中存放内部产物的路径约定。隐藏布局将知识池放在 `.lessonkit/pool/`、构建中间工件放在 `.lessonkit/intermediate/`；旧布局使用课程根目录的 `pool/`、`intermediate/`。旧工作区只在显式迁移后切换；课程资料与用户明确指定位置的导出不属于内部产物。
_Avoid_：课程资料重排、外部 Agent 工具目录治理、学习数据迁移
出处：docs/design/2026-10-21-course-artifact-layout-alignment.md

### 课程标识符 / Course Identifier（slug）
一门课程（一本教材）的机器名：小写 ASCII（字母、数字、连字符），既当池库名（`<course>.db`，位置见工作区布局）又当每条内容 id 的前缀段（`dmath-ch06-kp-001` 里的 `dmath`）。它与人看的工作区名是两样东西——中文文件夹名照样可以当工作区名。注册时按「显式 `--course` › 已有池名 › ASCII 文件夹名推导 › 自动顺序短码 `c01`、`c02`…」取一个：前三条是人认得的名字，最后一条只是机器内部的下标（自动分配，顶栏不显示）。显式给的值一律按本式样校验，不合就带理由拒绝——ingest 各条门禁只认这个字符集。
_Avoid_：工作区名（人看的、可中文）、自由命名的课程名、把短码当成课程名

出处：openspec/specs/review-workbench「Unified CLI entry point」「Course and chapter switching」；workbench/cli/main.py

### 知识池 / Knowledge Pool
课程级的 SQLite 存储（新建或显式迁移工作区为 `.lessonkit/pool/<course>.db`，未迁移旧工作区为 `pool/<course>.db`，`<course>` 即「课程标识符」），保存提取好的知识点、正式题与全部学习状态。整个工作台的数据底座。
_Avoid_：章节数据库、压缩包版本
出处：CONTEXT.md（迁入）；pool_schema.py

### 作者内容投影 / Authored-Content Projection
知识池中受治理的作者字段在独立 Git 内容仓库中的 JSON 表示。它允许审阅和提出字段编辑；Lesson Kit 仍须通过现有内容校验与写入路径接收编辑，学习者状态只留在知识池。v1 投影知识点、正式题和知识关系，包括知识点/题目的逻辑图像引用与正式题四维客观难度组；不投影闪卡实体、图片字节或学习者状态，也不支持仓库侧创建新实体。逻辑图像引用的投影不决定全仓库的图片命名策略。
_Avoid_：工作区镜像、数据库镜像、学习状态同步
出处：ADR 0024；`json-content-repository-sync` 与 `expand-content-mirror-fields` changes

### 作者内容镜像 / Authored-Content Mirror
`lesson-kit mirror` 命令组与其同步机制的整体称呼：把「作者内容投影」在知识池与本地作者内容仓库之间按单实体对齐。概念定义以「作者内容投影」为准；本文档不再为镜像另立语义。
_Avoid_：工作区镜像、数据库镜像（避免与整库快照混淆）
出处：ADR 0024；`json-content-repository-sync` change；FILE_CONTRACT.md「Git Authored-Content Repository」

### 本地作者内容仓库 / Local Authored-Content Repository
由用户提供路径的本地 Git checkout，按课程标识符保存作者内容投影 JSON。`lesson-kit mirror` 只读写所选课程目录和目标课程的删除请求；Git clone/pull/commit/push 不属于 Lesson Kit 的职责。
_Avoid_：工作区备份、知识池数据库副本、自动远端同步
出处：ADR 0024；`FILE_CONTRACT.md`「Git Authored-Content Repository」

### 作者内容修订号 / Authored-Content Revision
某一实体作者内容的正整数版本。每次被接受的语义修改向前增加一版；它用于比较池、仓库文件与上次同步内容，不通过哈希计算，也不会因格式整理而倒退。
_Avoid_：Git commit id、数据库主键、内容哈希
出处：ADR 0024；`json-content-repository-sync` change

### 删除请求 / Deletion Request
本地作者内容仓库中的 JSON 意图记录，点名课程和实体并附理由。镜像会校验并报告它，但不据此删除池记录、实体文件或学习历史。
_Avoid_：删除命令、可执行删除清单
出处：`FILE_CONTRACT.md`「Git Authored-Content Repository」；`json-content-repository-sync` spec

### 章 / Chapter
一本教材（课程）内部的内容分段，只以内容 id 的前缀段存在：`dmath-ch06-kp-001` 里的 `<course>-<chapter>-`（`<course>` 即「课程标识符」；知识点、正式题、微测、闪卡同理）。一个池（`pool/<course>.db`）容纳多章（「单库多章」）；章的名单从池内容派生，不是一张表、也没有登记动作。工作台的**章透镜**（顶栏那个「章」开关）把注册表的 `active_chapter` 指向某一章，关掉开关 = 空值 = 全课程；透镜只改"看什么"（知识点页/图谱页/复习/练习建议），不改选区，也不锁题。
_Avoid_：章节数据库、chapters 表的行、跨库切章、把透镜当练习范围
出处：pipeline/commands/extract-chapter.md（单库多章）；openspec/specs/review-workbench「Chapter list derived from pool content」「Chapter lens scoping」

### 知识点 / Knowledge Point
从源材料中提取、入池的可复用知识单元，是练习、调度、图谱、信号的共同挂载对象。每章一章（如 `dmath-ch06-kp-001`）。
_Avoid_：卡片、笔记条
出处：CONTEXT.md（迁入）；openspec/specs/review-workbench

### 可见字符 / Visible Characters
一段文本的字符数，计数前先剔掉行内公式（`$$…$$`、`$…$`）与反引号代码。之所以要剔：`ncmc` 一个段落的总字符里约 44% 是 LaTeX 源码（`\frac{...}` 五个字符只渲染成一个分数），用总字符会把段落长度虚高 1.76 倍，而 `c04` 只虚高 1.09 倍——同一把尺在两门课上含义完全不同；改数汉字更糟，`dmath` 是英文课，51 字符的段落只有 15 个汉字。**剔除只发生在计数这一步，文本一个字都不改。**
_Avoid_：字符数、字数、汉字数、len()、文本长度上限
出处：kp-text-typesetting-check design「The measurement」

### 排版检出 / Typesetting Check
对知识点 `body` 的**只读**排版检查：把正文按空行切成段落，用「可见字符」量每段长度，任一段落在 40–300 之外就报出这个知识点，并注明两侧各几段、最长段与最短段各多少。它跑在两个时机（入池前读 content-bundle 清单、入池后读池），两边共用同一把尺和同一套报告口径。
**它不是门禁**：只报、不拒、不改文本、不退出非零，也不告诉你该怎么排版——不给目标字数、不推荐小节名、不提示切分位置。**不触发就说明没有可报的问题**；41 字符和 300 字符同样可以。区间 40–300 记在 workbench-content-governance spec 里，不是实现常量。
_Avoid_：门禁/gate（那是一失败就整批拒绝、零写入）、审计/audit（那个会退出非零）、字数上限、格式校验、自动重排/自动分段
实现使用正文的空行边界；跨空行的反引号代码仍整体剔除后计数。正文段落的零可见字符计入统计，但不触发过短检出。报告中入池前可用清单 key 标识知识点，入池后使用 kp_id。
出处：kp-text-typesetting-check（spec + proposal + design）；implement-kp-text-typesetting-check；ADR 0023

### 知识关系 / Knowledge Relation
两个知识点之间经审核的点对点边（如 prerequisite / applies_to / contrasts / variant_of），存于 `knowledge_relations`。图谱的事实层。
_Avoid_：算法臆造的关系、隐藏关系
出处：CONTEXT.md（迁入）；review-workbench spec「Semantic graph attraction」

### 正式题 / Problem（durable problem）
作为独立学习资产入池的练习题：题干、关联知识点、来源类型、题型、解析（非空，过门禁后入库）。只读练习，不是待审稿。
_Avoid_：练习册条目、题目草稿
出处：CONTEXT.md（迁入）；review-workbench spec「Problem pull engine」「Formal problems are reveal-ready」

### 内容身份 / Content Identity
由完整题干规范化得到的严格比较键：忽略大小写、空白、标点、已知数学标记/渲染差异与常见导出噪声，不截断题干；相同键表示同一道题，跨来源、跨章节也只保留一条。相似但确实不同的题干保留。
_Avoid_：题目 id、截断前缀、模糊相似度
出处：workbench-content-governance spec「Content identity dedup at ingest」；`workbench/domain/content_identity.py`

### 内容审计 / Content Audit
对课程题池运行的只读卫生检查：重复题、疑似片段、未标练习模式的客观题、缺展示标题、失效图片引用和孤儿图片。命令为 `lesson-kit data <workspace> audit`；按 `--check` 选择检查，`--json` 输出机器可读报告，发现问题退出码为 1，不修改数据库或文件。
_Avoid_：自动修复、正式题源审计、会写入的检查
出处：workbench-content-governance spec「Read-only pool content audit」；`workbench/data/content_audit.py`

### 客观题目难度 / Objective Problem Difficulty
正式题或微题自身的认知复杂度，由知识跨度、推理深度、迁移距离、构造开放性四个
1–5 整数维度组成；总分由 `cognitive-v1-equal-mean` 等权平均并按 Decimal
`ROUND_HALF_UP` 保留一位小数。评级整组可空，且只能由显式 `lesson-kit difficulty`
事务写入；内容入池、练习和显示均不依赖评级。闪卡不评级，题型本身不决定分数。
_Avoid_：学习者自评、能力等级、把 `problem_type` 当难度、在出题 manifest 内写难度、`difficulty_basis`
出处：problem-difficulty spec；problem-difficulty-and-provenance design

### 个人难度 / Learner Difficulty
这名学习者当前觉得某知识或练习有多难的证据集合，来自显式自评、作答、卡点、学习信号
和到期状态；不新增主观难度星级字段。它只参与知识范围和优先级，不覆盖客观题目难度，
也不从一次自评推导持久“能力等级”。
_Avoid_：客观题目难度、统一能力分、自动升降题目难度
出处：problem-difficulty spec「Objective and learner difficulty remain separate」

### Legacy 知识内容复杂度 / Legacy Knowledge Complexity
`knowledge_points.difficulty` 的冻结 pipeline 语义。旧提取路径缺失时仍默认 2；它不使用
题目的四维量尺，也不与 `problems.difficulty` 互相换算。
_Avoid_：客观题目难度向量、学习者自评
出处：pipeline/skills/pool-field-inference/SKILL.md；problem-difficulty-and-provenance design

### 候选题 / Problem Candidate
**已退役（2026-08-30 remove-candidate-store）**：概念与机制整体移除，候选题不复存在。
历史含义（留档）：尚未进入正式题池的、有源可依的练习条目；先后过结构门禁与审计门禁，
再经显式晋升（promote）成为正式题。
状态注记（2026-08-29 专题 22）：随 Check 管线立项退役——pull/mastery/hub 停止读取。
状态注记（2026-08-30）：观察期结束，所有者拍板物理清除——candidate_problems 表 DROP、
`lesson-kit data` 的 candidate 实体与 gate/promote 动作移除；Agent 内容唯一通道为 Check 管线
（见「Check 管线」条目）。

### Check 管线 / Check pipeline
内容入池的唯一 Agent 通道（原名 generate 桥）：Agent 产出合规清单 → 确定性门禁校验 → **直接入正式池**（无候选中间态）。清单形态以 `content-bundle` 为主（可同时含知识点、正式题、微题、闪卡与必需原图，条数无上限，大清单暂存于本对话 jobs 目录），`flash-card-patch` / `micro-quiz-patch` 作为兼容通道保留。题目身份在整个课程池比较，不因跨来源或跨章重复入库。每次 apply 记批次 id、内容行带批次标记、图片按字节落 `figures/`；整批回滚先核对 apply 后状态，若后续内容有改动则在创建备份前拒绝；门禁失败逐条显式报错、零写入。对话桥的控制动作仍叫 `check_ingest`，但**不再有浏览器关键词意图门**——合法的纯新增动作自动执行；门禁是决断辅助不是权限闸门，AI 永不直写池数据库。
_Avoid_：generate 桥（旧称）、候选中间态、staging 区、逐题人工确认、关键词意图门
出处：DISCUSSION-RECORD 专题 20/21/22；workbench-content-governance spec（introduce-check-pipeline）；first-use-conversation-content-fidelity

### 来源类型 / Source Kind
正式题或微题所依据材料的类别：textbook / quiz / midterm / final / makeup / other。
它不回答题目是不是 AI 生成；生成题仍需如实记录其依据材料。
_Avoid_：题目来源方式、把 quiz 当作“微题”、考试年份、作者
出处：CONTEXT.md（迁入）；review-workbench spec「Provenance-filtered problem pull」

### 题目来源方式 / Origin Kind
题目相对依据材料的形成方式：`source_problem`（材料中的原题）、`adapted_problem`
（改编题）、`generated_grounded`（基于材料生成的新题）。它与来源类型正交。
_Avoid_：来源类型、题型、难度、把所有 AI 题的 `source_kind` 写成 quiz
出处：workbench-content-governance spec「Problem provenance axes」

### 来源便捷组 / Source Group
由来源类型和题目来源方式派生的互斥筛选组：生成题优先归 `ai_generated`；其余
quiz/midterm/final/makeup 归 `exam`，其余 textbook 归 `textbook`，剩余归 `other`。
它不落库，也不抹掉两条原始来源轴。
_Avoid_：第三条存储轴、题型分组、难度分组
出处：review-workbench spec「Provenance-filtered problem pull」

### 题目尝试 / Problem Attempt
与一道正式题的一次已持久记录的交互，保存当时的作答文本、卡点标记与评分。学生在练习页提交后，服务端接受写入时创建状态为 `answered` 的行（含选项文本与客观判定）；浏览器已提交但写入尚未确认的内容仍是浏览器状态，不等于一条已保存的尝试。另一来源是学生明确要求后由 Agent 经 `lesson-kit attempts` 提交。开启自评时浏览器作答等待评分才改变学习投影；关闭自评的客观判定按「判定」的关闭自评规则更新进度、当前状态与调度。主观、无答案键和 Agent 无评分尝试不因此折算；旧池需要运行迁移命令后才能使用浏览器请求重试。
_Avoid_：当前状态、浏览记录、草稿（未提交的作答不是尝试）
出处：CONTEXT.md（迁入）；review-workbench spec「Practice session」；agent-assisted-practice-records spec「Agent transcription and optional learning rating」

### 浏览器练习请求 / Browser Practice Request
一次提交作答或保存自评及其稳定 `request_id`。练习页先保存完整请求，再发送；响应丢失或刷新后原样重试只取回首次结果。同一个 id 改变作答、评分或操作类型会被拒绝，不多写尝试或学习状态。
_Avoid_：把一次重试当成第二次作答、把判定当评分
出处：review-workbench spec「Retry-safe browser practice writes」

### 判定 / Verdict
客观题（判断题、小测题）在**浏览器本地**比对答案键得到的一次对错结论（对 / 错），随那次提交一起存进尝试行；综合题不判分，判定为空。它是这一次作答的事实，不是学习状态：进度、信号、调度仍然只在自评时改变——**例外**：关闭自评的轮次（见「学习者设置」）里，判定就是学习结论，落库时一次性折算为进度与排期（对 → mastered、错 → wrong），不写带评分的反馈事件。答案键缺失时不判分，页面如实写明「本题未录入答案键」。
_Avoid_：评分（1–5 自评才是评分）、掌握度、把判定当成绩、把折算出的进度当自评分
出处：review-workbench spec「Durable practice records」；workbench-ui spec；rating-toggle-setting change

### 学习者设置 / Learner Settings
左栏「设置」区块里的浏览器偏好，按工作区存于 `localStorage`（`wb_settings_<工作区>`），**跨标签页与重启持久**；它与可选的本地布局种子共同构成工作台当前的持久 `localStorage` 用法，其余客户端状态仍是会话级。第一项是「练习与试卷显示自评」（默认开）：关闭后自评在练习与试卷流程里完全消失（不选自评时机、无反馈面板、不进统一自评页、记录页标「关闭自评」），客观题按判定折算学习状态。设置在**下一轮开始时生效**，进行中的轮次保持开始时的模式。设置只表达偏好，不是学习事实，不写池。
_Avoid_：把设置当学习记录、按工作区写进数据库、对进行中的轮次即时生效
出处：rating-toggle-setting change「Learner settings in the left rail」

### 做题记录 / Practice Record
把尝试、判定与自评合成一行的历史视图：练习页揭示区的「历史作答」折叠段（这道题我做过的每次作答），以及左侧「记录」中心的**作答明细 / 错题**视图（可按题过滤）。同一行读作「作答了什么、判定如何、评为几分」——自评通过 `attempt_id` 链回那次提交。**作答记录只增不改**：重新作答会追加 Attempt。唯一相关例外是浏览器在同一 Paper Practice Run 回看中再次保存自评时，只原位覆盖该 Attempt 关联反馈的评分和评语；不新增 Attempt/反馈，也不重放学习影响。此例外不扩展 Agent Attempt Correction。
_Avoid_：学习状态、排期表、把记录页当批改结果
出处：review-workbench spec「Durable practice records」；workbench-ui spec

### 答卷目录 / Answer-image Directory
学生为某个工作区显式配置的一个或多个目录，只作为 Agent 的**只读**取图来源；可位于工作区之外。Lesson Kit 只记住目录路径，不复制、不归档图片字节，不在尝试上保存单张图片路径，也不建扫描索引，因此不承诺跨扫描的图片去重。
_Avoid_：图片库、答案附件、图片索引、把答卷图片读进池
出处：agent-assisted-practice-records spec「Answer-image discovery without image retention」

### 尝试清单 / Attempt Manifest
Agent 提交给 `lesson-kit attempts check|apply --input <文件|->` 的 UTF-8 JSON 对象：`request_id` + `items[]`，每项只有 `problem_id` / `answer_text` / `note` / `rating`（1–5，可选）。一份清单可含多题，一次调用就是一个事务：任一条不合法即整批零写入。清单**不接受**图片字节、图片路径、卷面分或批改者身份字段。
_Avoid_：卷面分、批改者字段、把整份清单当一次尝试
出处：agent-assisted-practice-records spec「Workspace attempt CLI」

### 请求标识 / Request Id
清单与更正里的调用方自述幂等键（`request_id`）：同一标识 + 完全相同内容重复提交 → 返回第一次的结果、不重复记分；同一标识 + 不同内容 → 拒绝（零写入）。换新标识 = 同一道题也可以再记一次尝试。
_Avoid_：把 request id 当内容 id、靠重试去重
出处：agent-assisted-practice-records spec「Workspace attempt CLI」

### 尝试更正 / Attempt Correction
`lesson-kit attempts <工作区> correct <attempt-id> --input <文件>`：按**指定尝试 id** 整体替换其作答原文、评语与可选评分（是替换不是补丁），并撤销旧评分留下的影响后按新评分重算。仅当该尝试由 Agent 记录、仍是该题最新一次尝试、且没有更晚的学习活动改过它涉及的题目/知识点投影时才执行；否则零写入并提示改记一次新尝试。更正不新建尝试、不留更正历史、不保留旧评分。
_Avoid_：历史更正流水、静默改写后续学习记录
出处：agent-assisted-practice-records spec「Explicit attempt correction」

### 聚焦草稿 / Focused Draft
练习页上**尚未提交**的作答文本、已选选项、评语备注与当前可见图片引用。学生从练习页发消息时随该轮一起送给 Agent，只作这一轮的临时上下文，不是池事实、不是尝试，也不写会话镜像；页面上的草稿本身照旧随标签页消失。
_Avoid_：把草稿当尝试、把浏览器内容当权威事实、整页 DOM
出处：workbench-ui spec「Authoritative page context for Agent turns」

### 页面锚点 / Page Anchor
练习页当前可见、并已由知识池解析出的正式题。它标明学生正在看的题；即使消息明确把轮次焦点指向上一题或近期题目组，页面锚点仍保留当前题。
_Avoid_：随轮次焦点移动、把浏览器提交的裸 id 当题目事实
出处：`agent-context` spec「Current page is an anchor rather than a forced turn target」

### 近期练习工作集 / Recent Practice Working Set
练习页 Agent 轮次中的有界题目上下文：先包含页面锚点对应的正式题；仅当该题也是同一 active practice 的题目时，再附最近最多四道已结算的前序正式题。前序题按练习顺序选取，闪卡不占题目槽；题面、尝试与反馈由服务端从知识池重建。
_Avoid_：整轮次展开、从别的 active practice 借前序题、把闪卡当正式题
出处：`agent-context` spec「Practice turns carry bounded recent settled problem context」

### 轮次焦点 / Turn Focus
当前 Agent 轮次要回答的题目目标。练习页默认以页面锚点为焦点；只有消息明确且无歧义地指向同一 active practice 中的上一道题或近期题目组时，才改用对应的已解析正式题。否定相对指代或同时提及当前与前序目标时，保留页面默认焦点；没有可解析的页面正式题时不构造题目焦点。
_Avoid_：被否定的目标、浏览器原始 id、由上下文窗口替学生消解歧义
出处：`agent-context` spec「Current page is an anchor rather than a forced turn target」

### 试卷 / Paper
Lesson Kit 的**最小可执行作答单位**：开始、暂停、继续、提交与完成状态都围绕一张已经冻结 item 顺序的 Paper 发生。Paper 可由 Agent / CLI authoring 按明确范围和筛选组装；浏览器管理和练习已有 Paper，不提供手工选题或组卷。内容与题序在 Practice Run 中不动态改变。当前 `.lessonkit/practice-sets/`、`ps-NNN`、manifest `kind: practice-set` 与 `/practice-sets/...` 是迁移期兼容实现名，不改变本条产品定义。
_Avoid_：Practice Run 本身、动态知识点查询、把兼容名 practice-set 当产品题单
出处：practice-set-export spec「Paper is the Practice Run boundary」；review-workbench spec「Paper-backed Practice Run」「Practice Run interruption recovery」；workbench-ui spec「Flash card item stacked presentation」

### 题单 / Practice Set
**组织多份 Paper 的容器**，用于按课程进度、专题能力、真题来源等组织练习路径；题单本身不直接进入作答。地图形、桶形等只是题单的视觉布局，不产生新的内容类型。v1 允许题单容器尚未完整实现，但不得再把一张可执行 Paper 命名为产品级 Practice Set。
_Avoid_：试卷、一次 Practice Run、旧 `.lessonkit/practice-sets/` 目录名的字面解释
出处：practice-set-export spec「Paper manifest」「Managed saved Paper」；FILE_CONTRACT.md「Agent Saved Papers」

### 练习轮次 / Practice Run
对**一张已经确定的 Paper**从开始到完成，或到被显式替换 / 清除的一次执行。运行中仍只有一个 `active_practice`；每张已保存 Paper 可独立保留自己的未完成进度。新执行的来源语义统一为 `paper`。普通题 Practice Run 只有显式提交整卷才完成归档；逐题作答、判定和可选自评仍以 `problem_attempts` / `feedback_events` 为学习证据。
_Avoid_：第二套 attempt 表、动态拉题器、把 Practice Run 当 Paper 定义
出处：practice-set-export spec「Paper is the Practice Run boundary」；review-workbench spec「Paper-backed Practice Run」「Durable practice run archive」

### 试卷清单 / Paper Manifest
`pull --plan <文件>` 写出的 v1 UTF-8 JSON：标题、按序排列且各含 `problem_id` 与可选 `reason` 的 `items`，以及复现这些问题组卷所需的输入。v1 清单只编码问题条目，不编码闪卡条目；Paper 产品模型可以包含闪卡 item。`pull --input <文件>` 可重放同一有序问题结果；清单是 **Paper 的可复现输入 / 交换工件**，不是学习记录。v1 wire-level `kind: practice-set` 属兼容 token。
_Avoid_：Practice Set 容器、学习记录、在清单里塞题目正文
出处：practice-set-export spec「Paper manifest」；FILE_CONTRACT.md「Agent Saved Papers」；workbench-ui spec「Flash card item stacked presentation」

### 考察年份 / Exam Year
正式题可空的一个来源事实：这道题的**来源考试属于哪一届**，例如 `2023` 或 `2023-2024秋冬`。填了必须以 4 位年份开头、不超过 20 字符；不填就是「不知道」。`pull --exam-year 2023` 按**前缀匹配**（所以能命中 `2023-2024秋冬`）。它是 `source_kind`（材料类型）与 `origin_kind`（产生方式）之外的第三项可选来源事实，不是卷面分。
_Avoid_：卷面分、难度、把年份当 id 或当作试卷实体
出处：practice-set-export-and-cli-audit spec；workbench-content-governance spec「Problem provenance axes」

### 组卷 / Paper Assembly
生成或挑选一张具体 Paper 内容的过程。`lesson-kit pull` 当前是确定性组卷引擎：Agent / CLI authoring 可用范围（`--kp`）、来源/难度条件、薄弱 / 到期 / 错题证据决定候选与排序。`--problem` 精确题号能力只作为 Agent/CLI 的作者工具保留。知识点阅读、图谱筛选与节点聚焦不建立组卷边界；浏览器不提供学生手工组卷入口。每个结果仍回报 `scope` / `weak` / `due` / `wrong` / `explicit` 等入卷理由。
_Avoid_：手动选题 UI、把组卷直接等同 Practice Run、把 `--problem` 当学生侧练习动作
出处：practice-set-export spec「Paper assembly」；review-workbench spec「Paper assembly engine」；workbench-ui spec「Practice page」

### 筛选维度 / Filter Dimension
Paper authoring 的来源筛选有四个**多值**维度：`source_kinds`（来源类型）、`origin_kinds`（题目来源方式）、`exam_years`（考察年份，仍按前缀）、`docs`（来源文档，对 `source_evidence` 做不区分大小写的子串匹配，值就是「文档键」）。语义是**维度内 OR、维度间 AND**。这些筛选由 Agent / CLI `pull` authoring 使用；浏览器不提供练习页来源筛选面板，也不提供「搜索后挑某一道题加入练习」的 `include_ids` 产品语义。只读题目搜索与图谱状态筛选仍是阅读功能。CLI 精确题号只属于作者工具。
_Avoid_：把维度内的多个值当 AND、把筛选当扩范围、手动挑题进入 Practice Run
出处：review-workbench spec「Source dimensions and facets」；workbench-ui spec

### 题干域 / 来源域 / Stem & Source Keyword Domains
一道题上回答两个不同问题的两组文字，全仓库只有一份定义（`domain.facets.stem_text` / `source_text`），搜索端点与选题引擎都读它——所以一道题不可能「按一套规则搜得到、按另一套规则筛不出来」。**题干域** = `display_title` + `problem_text`（题目**说了什么**）；**来源域** = `source_evidence` + `exam_year` + `problem_text` 开头的连续 `【…】` 标签段（题目**从哪来**）。`【…】` 只在题面开头算来源：早于来源字段的老池把卷面身份只写在题面开头（如 `【2023期末】【合集A】`），那里是它唯一的容身处。
每个域的查询按空白切成多个词、逐词 casefold，**域内 AND**（每个词都必须在该域文字里出现）；两域都给则跨域 AND。空查询返回空集，不是全池。
_Avoid_：把两域合成一个 haystack、只取第一个词、把词序当语义、把来源词算进题干域或反过来
出处：review-workbench spec「Multi-dimension source filters」「Source filter panel on the practice page」

### 文档键 / Document Key
把 `source_evidence` 折叠成**一份文档一个键**的纯规则（`domain.facets.document_key`）：写成路径的（`题库/final·A.md`）原样就是键；教材类（`教材 …`）统一折成「教材」（它的证据逐题不同、没有文档级身份）；其余取第一段。两个真实池里两套书写格式因此归得进同一组，浮窗的「来源文档」维度与计数都由它聚合。
_Avoid_：把它当第三个来源字段落库、按整串证据精确匹配
出处：review-workbench spec「Source dimensions and facets」

### 接口归属表 / Declared Interface Surface
`workbench/surface.py`：逐条声明每个 API 路由与每条 CLI 命令的**受众**（Agent / 人 / 双 / 仅浏览器）与状态，并由 `tests/workbench/test_cli_surface.py` 与真实的参数解析器、`ROUTES` 对账。它是「谁该有 CLI」这个问题的机器权威：声明了却不存在、存在却没声明、标「双」却缺一边，测试都失败；仅浏览器保留的能力必须写明理由。
_Avoid_：靠文档计数描述接口覆盖（会漂移）、把归属当许可闸门
出处：review-workbench spec「Declared interface surface」

### 附图 / Figure
题干自带的教材原图或生成图：文件落在工作区 `.lessonkit/figures/{course}/{chapter}/`，文件名 = **内容 sha256 + 原扩展名**（由门禁计算，不由 manifest 声明）；池里只存逻辑路径（`figure_paths` 列）+ 题干里的标准 Markdown 引用。入池唯一通道 = figure-patch 门禁（图与替换后的题干全文同批校验，失败零写入）；回滚恢复题干与 figure_paths 前值，已落盘文件保留。
_Avoid_：`{owner_id}-fig-{NNN}.png`（旧命名规则，2026-09-20 作废）、图片入库（base64）、任意路径引用
出处：knowledge-figures spec「Declared figure area / Gated figure patch channel / Legacy source-image migration」；ADR 0017

### 图像文件投影 / Figure file projection
把池中 `figure_paths` 已引用的图像字节显式复制到本地作者内容仓库 `figures/<logical-path>` 的文件系统投影；它与逐实体 JSON 作者内容镜像相邻，但不是 JSON 实体、池表或第二份成员关系。`check` 只读，`push` / `pull` 由调用者明确选方向；不修剪未引用文件，也不调用 Git 网络操作。转换期间，旧身份检查通过后，push 优先读工作区顶层 `figures/`，缺失时读现有 `.lessonkit/figures/`；pull 写两处以保留当前渲染与入库布局。既有文件名主体为 64 个字符的小写十六进制时仍表示旧内容哈希身份，不能把字节差异当普通编辑来覆盖；更广泛的命名策略仍未决定。
_Avoid_：把图像字节装进 JSON/SQLite、由投影创建池引用、把文件投影称为 JSON 镜像台账
出处：versioned-figure-assets change「Version-controlled figure assets」

### 图像归属索引 / Figure owner index
本地作者内容仓库 `figures/<course-id>/_index.json` 中由当前池引用推导出的 UTF-8 导航文件，列出逻辑图像路径及其知识点/题目所有者，供仓库浏览器查找图像。它是派生物：只在 push 时按池重写，不能增加、删除或改写 `figure_paths` 引用。
_Avoid_：把索引当作内容权威、当成 `content_mirror_state`、用索引反向导入题目或知识点
出处：versioned-figure-assets change「Version-controlled figure assets」

## 工作区与工作台

### 工作区 / Workspace
一个 lesson-kit 文件夹的注册身份：名称 → 文件夹路径、池数据库、激活的课程/章节。名称是给人看的（可用中文，取自文件夹名或 `--name`），与「课程标识符」无关。注册表在用户级 `~/.lessonkit-workbench/`。

**硬性局限**：一个工作区**只碰自己文件夹里的文件**，且**只装一门课**——池库、`.lessonkit/figures`、`.lessonkit/jobs`、`plan.json`/`goals.json` 都在工作区文件夹内；页面、API、CLI、桥接构造的每个路径都先校验落在这个文件夹里，跨工作区的 id（会话、轮次、附图、池）一律拒绝。因此**不同学科必须各自一个工作区**：切换的是工作区（Dashboard 或命令的位置名），不是在一个工作区里混装多门课。文件夹自己复制粘贴出来的第二份 = 另一个工作区（各写各的），不会被认成同一个。
_Avoid_：项目、数据库别名、把两个学科的内容放进一个工作区、把另一个工作区的池注册进来
出处：review-workbench spec「Workspace file containment」「Workspace registry」；2026-09-21 workspace-file-isolation
出处：review-workbench spec「Workspace registry」

### 工作台 / Workbench
浏览器里的学习界面：三栏壳层（左导航 + 中页面 + 右 Agent 对话），五个页面——练习 / 组卷 / 知识点 / 知识图谱 / **记录**。前三个来自专题 18/19 的既定模型（DISCUSSION-RECORD 专题 17、B6.2 的两次在案纠正）；记录从 2026-09-26 的只读历史页扩为 2026-09-29 的**记录中心**（四个只读视图 + 练习轮次快照），不是第六种练习方式（复习页仍然废弃）。
_Avoid_：把做题记录当复习页或练习方式、再开别的页面
出处：workbench-ui spec Purpose；DISCUSSION-RECORD 专题 18/19；attempt-records-filters-and-model-entries

### 守护进程 / Daemon
后台运行的工作台服务：`lesson-kit daemon start|stop|status` 管理**唯一**一个实例，绑定固定本地端口（默认 3081）。进程号与日志记在用户级注册表目录 `~/.lessonkit-workbench/`（`daemon.json`、`daemon.log`），与工作区注册表同级。`start` 只在端口真的应答后才报成功；`stop` 遇到进程号已被回收成非 Python 进程时拒绝终止并清理记录。它不排程、不自启，没有客户端对话时不消耗 Agent 调用。
_Avoid_：Heartbeat 后台服务（不做）、任务计划程序、开机自启
出处：ADR 0022；review-workbench spec「Background workbench service」

### 工作台命令 / lesson-kit Command
本项目的唯一命令名，模块形式 `python -m workbench.cli.main` 等价。`lesson-kit init` 注册工作区；`lesson-kit dashboard` 确保服务在跑并打开浏览器，**不新增页面**。
_Avoid_：`lesson-kit`（另一个同名程序是 Weights & Biases，与本项目无关）、`lessonkit.py init`（根 CLI，语义不同：写 `.lessonkit/state.yaml`）
出处：review-workbench spec「Unified CLI entry point」；ADR 0022

### 显式可执行文件 / Pinned Executable
`bridges.json` 中为某个 provider 配置的 `command`：它**优先于** PATH 探测决定实际运行哪个可执行文件。存在理由：同一台机器可能装有多份同名 Agent CLI（本机即有两份 `pi` 与两个 npm 前缀），否则"用哪个"完全由 PATH 顺序决定。解析结果由 `lesson-kit bridge list` 报告。
_Avoid_：PATH 探测优先（旧行为，已推翻）、静默回退
出处：ai-teacher-bridge spec「Provider-native conversation discovery」

### 柔和蒙德里安 v2 / Soft Mondrian v2
**2026-10-21 重新定义**（方向转向后的定案）。Lesson Kit 的视觉语言总纲：
**暖色 + 现代圆润**——底色偏暖（浅奶油 `#fdf8ef`），骨架是大圆角、饱和色块、
圆润图标与活泼动效；底色纯色，**不铺任何背景纹理**。

- **三角色色配额**（不引入第五色）：学习蓝 = 主要动作 + 链接 + 当前选中；
  阳光黄 = 当前 + 复习强调 + 连对进度；注意红 = 失败 + 阻塞。黄色对比度不足，
  只承载面积与形状，不承载文字。
- **纸面分层**：抬升序列是**底 / 卡 / 浮起**三层，靠圆角与暖调柔影分层，**不用描边**；
  内容块另用**沉底面**（凹层，底色差 + 内发丝线，不带柔影），代码块另用唯一的
  深色**代码块反白面**。
- **圆角 12px**：按钮 / 卡片 / 标签 / 输入框统一。
- **双字体**：阅读面衬线（正文 17px / 行高 1.75 / 行宽 38em），界面与标题无衬线，
  等宽为第三族。
- **状态不得只靠颜色**：颜色之外必有几何冗余通道（彩色圆点）。
- **两条全局原则**：「少字原则」与「图案适配原则」。

它是既有「柔和蒙德里安 / Soft Mondrian」的**精修，不是替代**：2026-10-21 之前该词条
把「暖纸色与深色结构线占主体」写成了定义，本轮按所有者方向转向（暖色 + 现代圆润，
不再一味仿古）重写该定义；**词条保留，不另造同义条目**。
_Avoid_：视觉风格偏好、个人审美主张、独立深色主题
出处：openspec/changes/workbench-visual-language-v2（decisions.md「收口：最终基线」、proposal.md）；workbench-ui spec「Soft Mondrian visual foundation」

### 纸面层级 / Paper level
表面所处的层。**抬升序列是三层**：底（页底）/ 卡（卡片）/ 浮起（浮层、抽屉、弹层），
分层靠**圆角 + 暖调柔影**表达，**不用描边**；暗色主题下同一层级改用夜纸的值集。
**内容块另有两块专用面**：沉底面（内容块专用，凹层，见「沉底面」）与**代码块反白面**
（`--surface-code`，全站唯一的深色内容面，**仅**代码块 / 等宽代码区可用）。
_Avoid_：z-index 层级、阴影层级、卡片层级
出处：openspec/changes/workbench-visual-language-v2（decisions.md A-23）

### 沉底面 / Sunken surface
纸面层级里的**内容块专用面**（`--surface-sunken`）：它是**凹层**，不参与「底 → 卡 →
浮起」的抬升序列，因此**不带柔影**、与卡面**同为 12px 圆角**；它靠**底色差 + 1px 内
发丝线**（`box-shadow: inset`）与卡面分开。浅色主题比卡面暗，夜纸里则比卡面略亮
（浅色 ΔL\* 5.73 / 夜纸 1.49 —— 夜纸差得小，所以内发丝线是必须的）。
用途：**作答区**、**用户在对话里的话**、**空态面板**（空态是独立面板，用沉底块才不与
上方的卡面抢层级）。全站除**代码块反白面**外不再有第二个深色内容面。
_Avoid_：深色块、墨块、抬升面、投影面
出处：openspec/changes/workbench-visual-language-v2（decisions.md A-23-3 / A-23-4 / A-31 / A-73）

### 夜纸 / Night paper
暗色主题下的暖调深色纸面值集（基色 `#1c1a16`），与亮色的浅奶油同源——白天是米色纸，
夜里是台灯照着的纸。它是**第二套值**，不是新色系：角色色仍是学习蓝 / 阳光黄 / 注意红，
只把圆底降饱和并提亮；同一套 SVG 用 CSS 变量换前景与背景色，一套资产服务两个主题。
_Avoid_：深色主题岛、护眼模式、夜间模式开关（那是偏好不是值集）
出处：openspec/changes/workbench-visual-language-v2

### 冗余状态通道 / Redundant state channel
状态除颜色之外的**几何**编码：颜色是主通道，形状是冗余通道（彩色圆点）。状态不得
只靠颜色，但冗余通道**不是文字标签**——凡要靠加说明文字来解决视觉问题的，改用形态或
色彩方案（见「少字原则」）。零文字。
_Avoid_：状态徽标、状态文字标签、颜色语义、无障碍标签（那是另一件事）
出处：openspec/changes/workbench-visual-language-v2

### 焦点环 / Focus ring
控件获得**键盘焦点**时画出的可见轮廓。它画在控件的 **focus-visible** 状态上，
所以键盘操作时必然出现。规格由 token 决定：外圈色 `--focus-outer`（暖纸 `#2b62e8` /
夜纸 `#9dbcff`）、外圈宽 **2px**、偏移 **2px**。
**单圈还是双圈**：控件本身有底色（卡面 / 透明底）的画**单圈**；把原生控件**视觉隐藏**
的（开关轨道、分段控件的项）画**双圈**——内圈 **2px** 取所在面的色、外圈 **2px** 取
`--focus-outer`。
⚠️ **可输入文本的元素例外**：浏览器对**可输入文本**的控件**恒匹配 focus-visible**
（UA 启发式，产品改不了）⇒ **用鼠标点进输入框也会出现焦点环**；而按钮、下拉这类
不接受文本的控件，鼠标点击**不**冒环。**不得**写成「鼠标点击一律不冒焦点环」。
_Avoid_：焦点描边、选中态描边、被控件自己压死的焦点样式
出处：openspec/changes/workbench-visual-language-v2（decisions.md A-1 / A-75 / A-84-1；workbench-ui spec「Focus visibility and contrast floors」）

### 分组卡片 / Grouped knowledge cards
知识点列表的呈现形态：**按章分组**，每组一个**组头**（组头是章标识本身，如 `ch06`，
不是翻译名），组内是一叠**圆角卡**（每张卡 = 一个知识点：名称 + 关联题数 + 状态标记）。
组块**本身不是卡片**——它只有间距（与上一组相隔 **24px**），没有卡面也没有描边；
组标题**比正文标题小一号**（**12px** / 行高 **18px** / 次级墨色），不抢正文层级；
组内的卡彼此相隔 **8px**，卡内边距**竖 8px / 横 16px**，圆角 **12px**（比普通卡片的
18px 紧——列表是信息密度更高的面）。
**排序跨分组可用，但只重排组内的行**：组头不随排序移动，行也不跨组迁移（一行永远留在
它所属的那一章里）。分组只用已有的知识点列表，**零新增请求、零写池**。
_Avoid_：折叠分组、按状态分栏、知识点表格、可拖拽排序
出处：openspec/changes/workbench-visual-language-v2（workbench-ui spec「Knowledge-point list grouped by chapter」；decisions.md A-79）

### 开关 / Switch
二态开关控件（实现名 `.lk-switch`）：一条**胶囊轨道**（**44 × 26**）加一枚**正圆滑块**（**20 × 20**）。
**开 = 学习蓝**（当前选中），**关 = 中性灰**（失活墨色，**不是第四色**）；滑块位置**只由
位移切换**，状态色**瞬切**。原生的复选框**视觉隐藏但仍可聚焦** ⇒ 焦点环画在**轨道**上。
命中区：整行 **44px** 高（轨道本体 26px 不单独算命中区）。
_Avoid_：复选框（那是另一种控件）、滑杆、开关的色块语义（开关是状态不是色）
出处：openspec/changes/workbench-visual-language-v2（decisions.md A-75 / A-76；design-notes/component-spec.md §4.10）

### 分段控件 / Segmented control
一组**互斥选项**的控件（实现名 `.lk-seg`）：容器是一道**沉底槽**（`--surface-sunken` + **1px 内发丝线**、
**不描边**、不带柔影，圆角 **12px**），每个选项是一个**项**（**36px** 高，左右内距
**14px**，项间距 **4px**，容器上下内距 **4px** ⇒ 容器总高 **44px**；项文字 **13px** /
行高 **20px**）。**选中项 = 一块学习蓝色块 + 纸白文字**，并用**字重加粗**做第二通道
（不靠颜色单通道）。⚠️ 沉底槽旁**不**用蓝洗底块（两者亮度太近，会被误读成「被选中的
行」）。原生的单选钮**视觉隐藏但仍可聚焦** ⇒ 焦点环画在**项**上。
_Avoid_：图谱的 `.seg`（那是图谱区段内的 tablist，名字不同）、下拉、单选按钮组、标签芯片
出处：openspec/changes/workbench-visual-language-v2（decisions.md A-75 / A-76 / A-84-2；design-notes/component-spec.md §4.11）

### 图标按钮 / Icon-only button
只放一个图标的按钮（实现名 `.icon-only`）：**32 × 32 正方形**、圆角 **12px**、**不描边**、图标居中，
平时图标取次级墨色、**悬停提到标题墨色**。命中区就是 **32 × 32**（视觉尺寸即命中区）。
图标目前是**字符**（☰ ◌ − × ‹）不是矢量图；换图标属资产问题，不在视觉改造这一轮。
⚠️ **待裁决**：无障碍硬约束是**命中区 ≥ 44px**，而现状是 **32 × 32**；
「命中区下限」与「视觉尺寸取 32 还是 40」已拆成两半，**视觉尺寸仍待样式板裁决**。
_Avoid_：文字按钮、图形按钮（那是另一类）、图标字体集
出处：openspec/changes/workbench-visual-language-v2（decisions.md A-75 / A-84-3；design-notes/component-spec.md §4.4）

### 主题偏好 / Theme preference
亮 / 暗主题的浏览器偏好，按工作区存于 `localStorage`。它只表达偏好，不写池，
不影响任何学习事实；默认跟随系统，切换时走「台灯转场」。
_Avoid_：工作台设置项、显示设置、系统主题（那是来源不是偏好）
出处：openspec/changes/workbench-visual-language-v2

### 阅读面 / Reading surface
连续阅读 ≥ 3 行的内容表面：知识点正文、题面、解析、Agent 长文、练习页的作答与反馈
段落等。它挂**共享阅读版式层**（实现名 `.wb-reading`；题面变体 `.wb-reading--stem`
是同刻度的语义变体，可独立挂载），刻度全部走 token：正文 **17px** / 行高 **1.75** /
行长 **38em** / 段距 **0.7em** / 对齐 `start`（不 justify）/ 标题 h2·h3·h4 = 22·19·17px。
**题面与知识点正文同档**（17px / 1.75 / 38em，见 decisions.md A-6）——两者分属两个页面，
不存在同页竞争。界面面（导航、按钮、表格、选项控件、状态标签、统计数字、空态文案等）
一律留在无衬线的界面字族，不挂阅读层。
⚠️ **当前事实**：`.rich-text` 这个过渡期的旧挂载名**已经整体退役**——HTML 挂载点早已全部
迁到 `.wb-reading`，剩下的 36 条死 CSS 规则也在别名期收尾（任务 2.3）里删掉了
（并列选择器只去掉 `.rich-text` 那半，保留 `.wb-reading` 那半，取值逐项未动）。
⇒ **现在产品代码里 `.rich-text` 只剩三行说明性注释，选择器命中 0**。
_Avoid_：富文本类、`.rich-text`（那是过渡期的旧挂载名，**已退役**）、正文容器、题面卡片
出处：openspec/changes/workbench-visual-language-v2（decisions.md A-6 / A-41；design.md D-5）

### 阅读字面 / Reading face
阅读面（知识点正文、题面、解析等长文）所用字族——衬线或无衬线——的浏览器偏好，
按工作区存于 `localStorage`。界面与标题始终无衬线，等宽为第三族；正文 17px /
行高 1.75 / 行宽 38em 不随该偏好改变。
_Avoid_：字体、字族、正文字体（那是实现资源不是偏好）
出处：openspec/changes/workbench-visual-language-v2

### 动效偏好 / Motion preference
动效开 / 关的浏览器偏好，按工作区存于 `localStorage`；默认跟随系统
`prefers-reduced-motion`。关闭时所有动效降级为状态直切：主题切换不做涟漪，庆祝直接落终态。
_Avoid_：动画开关、减弱动效、性能模式
出处：openspec/changes/workbench-visual-language-v2

### 声音偏好 / Sound preference
音效开 / 关的浏览器偏好，按工作区存于 `localStorage`。只有关键反馈（答对 / 答错 /
完成 / 里程碑）各有 <200ms 的短音效；受浏览器自动播放限制，首次音效必须挂在一次
用户手势之后。
_Avoid_：静音（那是结果不是偏好）、音频资产、提示音库
出处：openspec/changes/workbench-visual-language-v2

### 工作台设置视图 / Workbench settings view
中栏新增的外观设置页，由**左栏设置区的开关**打开与关闭。它承载**外观**偏好：
主题偏好、阅读字面、动效偏好、声音偏好；偏好按工作区存于浏览器 `localStorage`，
不写池。左栏原有的「学习者设置」（练习与试卷显示自评等**学习行为**偏好）**不搬家**，
仍在左栏——两者分属外观与学习行为两件事，不可混为一谈。
_Avoid_：学习者设置（左栏的学习行为偏好）、设置页、偏好面板
出处：openspec/changes/workbench-visual-language-v2（`workbench-settings` spec）

### 静物插画 / Still-life illustration
空态用的**具象器物**插画（花瓶、果篮、画布、杯子、书本、台灯、钢笔…）：写意线稿 +
淡彩晕染 + 克制高光，与图标同一套线宽与圆角语言，像同一支笔画的。纯 CSS / SVG 画，
不外链；同一套 SVG 经 CSS 变量换色，一套资产服务两个主题。
_Avoid_：抽象几何团块、照片、背景图案、图标字体
出处：openspec/changes/workbench-visual-language-v2

### 骨架屏 / Skeleton loading state
切到另一个中栏页面时、页面还没取回来之前，中栏显示的一组**占位灰块**（实现名
`.lk-skeleton`）。它只是占位，不承载任何真实内容，也不表达任何学习事实。完整动效档
下灰块有一层微光扫过；降级档改用同色的静态灰块（不扫光）。**知识图谱页不呈通用骨架屏**
——它有自己的加载表达。
_Avoid_：加载动画（那是泛称）、占位图、真实内容占位、进度条
出处：openspec/changes/workbench-visual-language-v2（spec「View transition and skeleton loading state」）

### 台灯转场 / Lamp transition
主题切换时的叙事转场：一盏台灯从角落探出 → 点亮 → 暖色涟漪自灯下扩散铺满
（切夜纸）或反向收拢（切回暖纸），约 700ms。涟漪只动 `transform` / `opacity`，
不阻塞交互、不改请求时序；系统开启「减少动态效果」时直接切换，不做涟漪。
_Avoid_：页面转场、加载动画、视图切换动画
出处：openspec/changes/workbench-visual-language-v2

### 少字原则 / Minimal-annotation principle
全局设计原则：信息优先由**元素形态与色彩**表达，不靠文字注释堆砌；界面注释本身
**能删就删**，而不是换成更漂亮的说明文字。与「状态不得只靠颜色」合起来是
「颜色 + 几何」，不是「颜色 + 文字」。
_Avoid_：文案风格、语气偏好、信息不足的免责声明
出处：openspec/changes/workbench-visual-language-v2

### 图案适配原则 / Contextual-graphic principle
全局设计原则：承载信息的图形（图标、状态标记、插画、纹理）必须**由背景自身的视觉
规则推导**——同一圆角语言、同一线宽阶、同一色彩寄存器、同一笔触密度；不得作为独立
装饰层贴上去，视觉逻辑必须自洽。
_Avoid_：装饰风格、贴图素材库、视觉花哨度
出处：openspec/changes/workbench-visual-language-v2

## 选择与练习

### 范围 / Scope
Agent / CLI authoring 请求中由知识点或其他课程语义明确的**组卷边界**。范围回答「这次 Paper 按什么约束组装」，它不是待执行题目清单，也不能直接开始 Practice Run。知识点页阅读、图谱搜索/筛选/聚焦、章透镜与建议不会隐式建立浏览器侧范围；弱项、到期等证据不得静默扩大明确范围。
_Avoid_：待练题目列表、Practice Run 的内容本体、弱项自动抓题、把知识点阅读选择直接当成一次练习
出处：review-workbench spec「Chapter lens scoping」；workbench-ui spec「Practice page」

### 准备练习列表 / Staged Practice List（已退役）
**已退役（2026-10-15）**。历史含义是把知识点选区在练习页再显示成一份「真正要练的」清单，并由它直接拉题开练。Paper 成为最小作答单位后，这个中间层不再有产品身份：知识范围直接进入组卷，组卷得到 Paper，Practice Run 只执行已经冻结的 Paper。
_Avoid_：重新建立「知识点队列 → 直接练习」中间态、把范围列表称为试卷
出处：workbench-ui spec「Practice page suggestions and assembly entry」

### 建议 / Suggestion
按需给出的只读练习方向提示，可来自每日计划、到期调度或薄弱证据。建议不会预填浏览器组卷表单、选择题目、改变 Paper 或直接启动组卷；Agent / CLI authoring 需要你明确提出请求。
_Avoid_：Staged Practice List、自动扩充正在执行的 Paper、把建议当作题目选择或组卷动作
出处：workbench-ui spec「Practice page suggestions and assembly entry」；review-workbench spec「Chapter lens scoping」；daily-learning-plan spec

### 原因短语 / Reason Phrase
建议行里的唯一一句人话解释：`拖了 N 天`（逾期）/ `今天到期` / `覆盖仍低`（计划命中，沿用计划原因文案）。纯函数生成，零调度参数外露，不拼接。
_Avoid_：徽标、日期数字、ease/interval 等裸参数
出处：consolidate-practice-views design D2（修订版）

### 练习模式 / Content Mode（兼容实现名）
存量内容与执行代码使用的兼容分类：exam / micro / yes_no / flash_card，用于判断某个内容可以怎样呈现和作答。**它不再定义「开始一轮时四选一」的产品模型，也不要求一张 Paper 只能包含一种形式。** `practice_modes` 等既有字段继续表达内容兼容性；题目的学科形态仍由 `problem_type` 表达。
_Avoid_：把 Content Mode 当成 Paper 类型、要求整张试卷单一题型、practice path（旧别名）
出处：review-workbench spec「Paper-backed Practice Run」；workbench-ui spec「Practice page」；docs/DATA_MODEL.md「practice_modes」

### 题型策略 / Practice Format Policy
规定某类课程内容适合以哪些作答形式练习或检测的**组卷约束**。例如知识点内容可偏判断，记忆型内容可用闪卡，阶段检测可混合多种形式。策略作用于 Agent / CLI Paper Assembly，不把整张 Paper 锁成一种题型；浏览器不提供学生侧策略或数量组卷控件。
_Avoid_：Practice Run 模式开关、单题学科形态 `problem_type`、一卷单一题型
出处：review-workbench spec「Paper-backed Practice Run」；workbench-ui spec「Practice page」「Flash card item stacked presentation」

### 原地改题 / In-place Problem Edit
不换题号、不重导，直接改一道**已有**题目的属性。单题走 `lesson-kit data <工作区> update problem <题号> --input <文件>`；批量走一份 `problem-patch` 清单（`lesson-kit ingest <工作区> recipe problem-patch --input <清单> --output <目录> --apply`，不给 `--apply` 零写入）。可改：题面、解析、kp_ids、problem_type、source_kind、origin_kind、source_evidence、source_answer、solution_origin、display_title、display_summary、exam_year、practice_modes、micro_quiz（整份 quiz_type/options/answer_key/error_reason）、answer_key。`topic_label` 已从题目字段移除，问题补丁会拒收；闪卡的同名字段仍由闪卡契约定义。**改不了题号**（它是身份），难度仍走 `lesson-kit difficulty`，不认识的字段名直接报错（不静默丢弃）。改 `kp_ids`/`problem_text`/`solution`/`problem_type` 会按既有规则清空整组难度评级；只改模式/载荷/来源不动评级。批量补丁记批次号并保存每行改前的旧值，`ingest rollback --batch` 会把旧值原样写回（不是删行），因此学习记录毫发无损。让一道已有题进小测/判断只需给 `practice_modes` + `micro_quiz`。
_Avoid_：把「改属性」当成「重导」、以为要删掉再导、以为题号可以换
出处：in-place-problem-edits

### 拆选项 / Option Splitting
把题面里自带的选项块（如 `A. … B. …`）原样搬进结构化 `options`，题面只留题干。这是原地改题的一种，用于让题库里那些「选项写在题面里」的单选题变成真正的小测题；**只搬动原文，不编造内容**，改动前的题面在补丁快照里可回滚。
_Avoid_：改写题目文字、把没有选项的题硬凑选项
出处：in-place-problem-edits

### 无答案键客观题 / Keyless Objective Item
判断题或单选题入库时题源没有正确答案，`answer_key` 省略或为 `null` 的形态。它照样进判断/小测模式（`quiz_type` 与 `options` 照常），但不参与判分：练习页明确显示「本题未录入答案键，请对照课本或解析」，作答仍会记录；「练习与试卷显示自评」开启时可另行自评更新学习状态，不评分时不推导判定或自评分数。答案键可以事后补：`lesson-kit data <工作区> update problem <id> --input '{"answer_key":"…"}'`（按该题的 `quiz_type` 校验形状；空值清回无键）。带键的题必须有 `error_reason`，无键的可以没有。
_Avoid_：拿没有答案键的题去猜答案、把无键题退回综合题、给无键题判分
出处：ingest-mode-choice-and-contract-parity；micro-quiz-content spec

### 综合题模式 / Exam Mode
Paper 中常规正式题的一种兼容作答形式：自由作答 → 查看解析 → 按当前自评设置记录学习结论。未标注 `practice_modes` 的存量题仍按 exam 兼容。它不是一种独立 Practice Run，也不要求 Paper 中只能出现综合题。
_Avoid_：考试模式、独立练习入口、一卷单一 exam 模式
出处：review-workbench spec「Grading input modes」「Paper-backed Practice Run」；docs/DATA_MODEL.md「practice_modes」

### 小测模式 / Micro Mode
Paper 中微题选择题（single_choice / multiple_choice）的兼容作答形式：点选后本地判分并显示错因，再按当前自评设置记录学习结论。它描述 item 的交互形态，不是独立 Practice Run。**原名「闪卡模式」，2026-08-29 正名出让**。
_Avoid_：闪卡（现指另一内容形式）、自由文本作答、一卷单一 micro 模式
出处：micro-quiz-content spec「Micro quiz content contract」「Type-aware practice rendering」；review-workbench spec「Grading input modes」「Paper-backed Practice Run」

### 闪卡 / Flash Card
从知识点解构出的键值对记忆卡（类似 dict 的一条键值对）：正面（front）→回忆→揭示背面（back）→按当前自评设置记录学习结论，无选项、无自动判分。知识点是唯一事实源（Note），卡是派生视图（Card），一卡只放一个原子事实；每卡一行独立调度。闪卡可以作为 Paper 的 item 形式之一，也可用于背单词、背概念等场景。
_Avoid_：小测（微题的卡片式渲染，旧「闪卡」）、把闪卡另建成绕过 Paper 的独立 Practice Run
出处：flash-card spec「Flash card practice mode」「Flash card session direction」；workbench-ui spec「Flash card item stacked presentation」

### 闪卡方向能力 / Flash-card Direction Capability
闪卡内容声明允许怎样提问：`["forward"]` 表示只能以正面问、背面答；`["forward", "reverse"]` 表示正反都具有教学意义。方向能力属于内容事实，缺省按单向兼容；它不等于当前练习采用的方向。
_Avoid_：把一张双向卡复制成两张内容卡、从文字长度猜方向
出处：flash-card spec「Flash card direction capability」

### 判断模式 / Yes-No Mode
Paper 中判断题（是/否）的兼容作答形式：有答案键时浏览器本地判分并显示错因；是否继续自评由当前设置决定。无答案键的题不判分、不折算。它描述 item 的交互形态，不是独立 Practice Run。
_Avoid_：主观题自动评分、浏览即掌握、一卷单一 yes_no 模式
出处：micro-quiz-content spec「Explicit mode marking for Micro and Yes/No」；review-workbench spec「Grading input modes」

### 自评时机 / Rating Mode
旧练习会话兼容的自评安排：每题作答后自评（immediate）、完成后统一自评（batch）或关闭自评（off）。它不决定普通 Paper 的答案展示或锁定；普通 Paper 的自评可跳过且不阻止交卷，答案展示由「答案展示方式」单独决定。
_Avoid_：评分方式（与 1–5 自评本身混淆）
出处：review-workbench spec「Paper-backed Practice Run」；`free-navigation-paper-practice`

### 练习会话 / Practice Session（已退役产品术语）
**已退役（2026-10-15）**。历史上指「单一练习模式 + 动态题目队列 + 当前题」的标签页状态。产品层统一使用「试卷 / Paper」描述固定作答内容，使用「练习轮次 / Practice Run」描述一次开始、暂停、继续到结束的执行。代码中的 sessionStorage key 或旧 spec 标题可以暂时保留为兼容实现名，但不得继续据此设计新的产品行为。
_Avoid_：把 Practice Session 与 Practice Run 并列成两种执行实体、把单一模式队列重新定义成练习本体
出处：review-workbench spec「Paper-backed Practice Run」「Practice Run interruption recovery」；workbench-ui spec「Practice page」

### 自由导航 / Free Navigation
普通 Paper 的作答与查看方式：上一题、下一题和题号点可到达所有题目，包括未答、已提交、标记「不会」和完成答卷中的题目。导航保存位置与输入，不提交、不判定、不锁题；首尾不循环。已锁定答案仍可查看，不能在原轮次重新作答。闪卡继续沿用自己的方向、揭示与上一张/下一张语义。
_Avoid_：把普通题回看当作独立只读覆盖层、把导航当作提交或完成
出处：`free-navigation-paper-practice`「Free navigation throughout a Paper」

### 完成页 / Paper Completion Page
普通 Paper 显式交卷成功后显示的完成信息页。它可打开同一轮次的答卷，返回同一完成页、再练一次或回试卷列表；查看答卷与返回不会重新交卷，重练会建立新的独立 Practice Run。完成不表示全对，也不等待自评。
_Avoid_：自动收束页、要求先完成所有自评的结束页
出处：`free-navigation-paper-practice`「Paper completion and answer-sheet return」

### 进度带 / Progress band
完成页上的一条**水平带**（实现名 `.lk-progress`）：轨道**高 10px**、**胶囊圆角**
（`--r-pill`）、**沉底底槽**、**不描边**、不带柔影；填充块铺满轨道。
它的**静态样式就是终态 100%（满格）**——0 → 100% 的生长只写在关键帧里，
**由庆祝重放一次**；**降级档（减少动态效果）直接是满格**，不会停在 0%。
它只表示「这一轮已经完成」，**不是分数、不是正确率、不是完成度百分比**。
_Avoid_：进度百分比、正确率条、骨架屏、连对计数器
出处：openspec/changes/workbench-visual-language-v2（workbench-ui spec「Round completion celebration in two tiers」）

### 里程碑档 / Milestone tier
交卷庆祝的**高档**：在日常档（数字滚动 + 进度带）之外，额外出现几何爆点与纸片。
它由**两个条件**之一触发——① 本轮**全对**；② 该轮**首次完成某一章**。
⚠️ **当前事实**：条件 ② 恒不成立（`practice_runs` 没有章列，也没有「首次完成」标志，
无数据来源），所以**目前只有「全对」能触发里程碑档**；这是如实实现，不是漏实现
（`contract-drift.md` CD-167）。不得用代理指标近似补上。
_Avoid_：通关、成就、完美奖励、连续学习天数
出处：openspec/changes/workbench-visual-language-v2（decisions.md A-29；spec「Round completion celebration in two tiers」）

### 连对 / Consecutive-correct run
一轮练习里**连续答对**的一段。内部计数只用于确认五连、十连等节点；平时不显示常驻数字或火苗。达到节点时短暂显示带节点数字的横幅。连对超过 4 时答错会让题卡短促摆动，并把计数归零。
_Avoid_：连击（游戏语汇）、积分、正确率、连续学习天数
出处：`hide-persistent-combo-counter`、`practice-pixel-motion`

### 自评 / Self-Rating
学习者对一道已作答题目的可选 1–5 打分（可带自然语言备注）。启用自评时可保存，也可跳过；首次评分写入对应反馈并按评分更新学习投影。普通 Paper 中再次保存只覆盖同一执行、同一 Attempt 关联反馈里的评分与评语，不新建作答或反馈，不重复更新学习投影；自评不控制导航或交卷。关闭自评不合成 1–5 分或评分反馈；客观尝试的判定可按既有 off 规则折算。
_Avoid_：把自动判定伪装成自评分、浏览即掌握
出处：review-workbench spec「Flexible feedback」

### 揭示再自评 / Reveal-then-Rate
开放题的作答约定：自己作答后按当前 Answer Reveal Timing 查看参考材料；自评启用时可以再打分。系统不自动判开放题。
_Avoid_：机器判卷
出处：review-workbench spec「Grading input modes」

### 跳题 / Skip
**普通 Paper 不再有独立的「跳题」动作。**旧练习会话里的跳题只是把游标移到下一题，不提交答案或生成 Attempt；普通 Paper 统一使用自由导航。「不会」是独立的作答状态动作；跳过自评也不等于跳过题目。
_Avoid_：把导航离开未答题目说成放弃、把跳题当成「不会」或交卷
出处：review-workbench spec「Practice session」（旧语义）；`free-navigation-paper-practice`

### 会话末统一自评 / Unified (Session-End) Rating
旧练习会话 `batch` 时机下的兼容收束页，只适用于保留旧语义的记录与闪卡路径。普通 Paper 的完成页由显式整卷交卷触发；自评可关闭、可跳过，不是完成条件。
_Avoid_：把它当成普通 Paper 的必经完成页、把完成和自评绑定
出处：DISCUSSION-RECORD B6.5；workbench-ui spec（旧语义）；`free-navigation-paper-practice`

### 微题 / Micro Quiz
带结构化载荷的客观小题：一个原子知识点 + 显式练习模式标记 + 结构化载荷（题型、选项、答案关键、错因、来源证据）。三种题型：yes_no / single_choice / multiple_choice，一律点选作答（short_answer / closest_answer 已于 2026-08-29 退役）。前端本地判分提供即时反馈；显式提交且自评关闭时，已记录的客观判定按「判定」的关闭自评规则更新学习投影，其余轮次等待自评。题干不限长度；答案键可以缺（见「无答案键客观题」），缺键不判分、不折算。**已有题目可以原地改成微题**（见「原地改题」），不必删除重导。
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
左栏「优先回看」的每一条目带一个状态点，用**同一套三态**（颜色 + 几何双通道，红叉 / 黄斜杠 / 中性墨环，见 `component-spec` §3.6）：状态由**理由**推出（有学习信号 / 复习已到期 / 其余），不按分数阈值分档（阈值会随公式漂移，词不能漂）。第三态**没有词** ——「保持中性」就是不作任何掌握断言，**不另造第四个学生侧词汇**。
_Avoid_：掌握度、分数、调度参数
出处：review-workbench spec「Action-oriented learning reminders」；workbench-v1-baseline-convergence change（设计稿 D-3 / D-4）

### 弱项 / Weak Point（weakness score）
按学习者信号与到期状态推导出的知识点排序权重：分数只调顺序，不过滤，任何知识点都不会被藏掉。**规格未定义具体公式**，属排序实现细节。
_Avoid_：成绩、能力值
出处：review-workbench spec「Weak knowledge point list」

### 方向 / Direction
记忆回忆类知识点的练习朝向（如中→英、英→中）。每个方向是独立学习动作、独立调度行；闪卡模式可在开练前选择正向、反向或混合，也可用卡上的 ⇄ 随时交换当前双向卡的提问方向。
_Avoid_：把方向当作一张新内容卡
出处：review-workbench spec「Directional schedule entries」

## 目标、计划与时间

### 目标 / Goal
真实持久化的学习目标，两种：长期目标（long_term）与阶段目标（stage），含标题、可选开始日期、截止日期与说明。目标卡只展示真实数据，不虚构课程目标。
_Avoid_：系统生成的课程规划
出处：daily-learning-plan spec；REQUIREMENTS.md 2026-08-28 纠偏段

### 目标时间跑道 / Goal Timeline Lane
目标在月历中的细轨道：从开始日期延伸到截止日期；没有开始日期的旧目标退化为截止日上的单日轨道。同一时间重叠的目标上下分轨并列，跨周目标按自然周切段、只在首个有足够空间的可见分段显示一次标题，但每段仍保留同一个目标的完整无障碍标签。它只呈现目标时间范围，不自动修改计划。
_Avoid_：甘特任务系统、自动排期、把重叠目标合并
出处：calendar-workload spec「Calendar and workload view」

### 每日计划 / Daily Plan
确定性基线算法产出的当日粗粒度建议队列（最多三项），每天首次打开自动重算一次、可手动重算。**专题 19 后计划输出降为「建议」的来源之一**，不再作为独立卡片展示。
_Avoid_：精细操作手册、强制任务单
出处：daily-learning-plan spec；专题 19 第 2 条

### 覆盖 / Coverage
「知识点被练习/掌握的程度」的统称。**规格未定义计算公式**；目标卡的覆盖进度、计划的覆盖仍低短语都引用此概念。
_Avoid_：正确率、完成度百分比（未经定义前不使用具体数字承诺）
出处：daily-learning-plan spec；consolidate-practice-views design D2

### 重日 / Heavy Day
14 天复习负荷里带红色提示的日子：当日到期项数达到非零日均值的两倍（且有项）。出现重日时给出一个「让 Agent 看看」动作，把重排请求预填进 Agent 输入框（不发送）。
_Avoid_：自动重排（视图只读，重排永远由你发起）
出处：calendar-workload spec「Calendar and workload view」

### 复习负荷 / Review Workload
从今天起 14 天内，每天到期、建议回看的调度行数量；每个方向算一项。视图用准确柱值、总量、峰值与逾期数表达，不做趋势拟合或预测，也不自动改变计划。
_Avoid_：错题数、每日已练题数、预测曲线
出处：calendar-workload spec「Calendar and workload view」

### 时间安排 / Time View
练习页中栏日计划之下的实验性只读视图：上方是目标时间跑道月历（开始日→截止日、重叠目标分轨、今日数字高亮），下方是未来 14 天复习负荷。重日（某天到期数 ≥ 非零日均 2 倍）带红色提示，可一键预填重排请求到 Agent 输入框（不发送）。只读，不改任何数据。
_Avoid_：日历应用、自动重排
出处：openspec/specs/calendar-workload/spec.md

## 图谱

### 知识图谱页 / Knowledge Graph Page
工作台第三页（练习 / 知识点 / **图谱**）：章节知识点的力导向图，支持搜索、投影切换（关系结构/题目数量/重要性/学习状态）、聚拢滑杆、缩放、节点勾选（与选区同步）与学习看板。默认关系布局；可使用同一图谱拓扑的本地布局种子作为临时起点。
_Avoid_：Obsidian、数据库编辑器
出处：workbench-ui spec；REQUIREMENTS.md 2026-08-27 段

### 本地布局种子 / Local Layout Seed
图谱在 Worker 布局稳定后保存在浏览器中的可选坐标缓存。它只在节点 ID 与关系起点、终点、类型和方向完全匹配时生效；命中时那些坐标被**直接采纳**——原 Worker 按它们落座后即停机，不再求解，重开图谱页因此不会重播一遍落座过程。只命中一部分（有缓存点、有无缓存点）时不构成「上次那张图」，仍按原路径从这些点继续求解。不保存筛选、选中、作者内容或学习事实。清除或无法读取该缓存只会失去上次图谱布局起点。
_Avoid_：布局编辑器、持久学习状态、数据库字段
出处：graph-lod-layout-seeds change；ADR 0028；graph-settle-smoothness change（采纳语义）

### WebGL2 图谱渲染 / WebGL2 Graph Rendering
知识图谱关系线的唯一当前绘制路径，要求浏览器提供 WebGL2。关系几何仍由图谱物理核心提供，DOM 节点继续承担节点外观、选择、拖拽与无障碍交互；渲染初始化失败时显示错误并停止本次图谱运行，不回退到 SVG。
_Avoid_：可选 WebGL 增强、运行时 SVG 回退
出处：graph-webgl-rendering change；ADR 0027

### 指标投影 / Metric Projection
知识图谱对同一组节点的只读视觉重排：当前指标越高，节点越大且越靠近中心，并使用对应色谱；切换时节点以力场目标连续迁移。关系结构仍以知识关系决定位置。投影不新增指标、不改变选区或写入 Pool；稳定坐标的可选本地缓存遵循本地布局种子规则。
_Avoid_：排行榜、自动学习决策、持久投影状态
出处：workbench-ui spec「Metric projection morphology」

### 图谱暖色板 / Graph warm palette
知识图谱自有的暖色板，**与全站「柔和蒙德里安 v2」的蓝 / 黄 / 红三角色配额是两套东西**：量值色相取橙（题目数量与重要性两个投影共用同一条橙色明度阶，值越大对纸面越强）；学习状态四色为未学 = 中性灰、复习 = 琥珀、掌握 = 橙、需突破 = 砖红；关系结构投影下节点色取墨阶三档（单层平涂的一个填充色分三档），颜色不承载语义。**图谱不受三角色配额约束**，因为它是数据可视化区而不是操作界面；反过来，图谱的暖色也不占用全站的三个角色色。夜里（夜纸）同一批色相换成提亮、降饱和的夜纸值集，色相不变。
_Avoid_：全站三角色色、图谱原有的蓝 / 黄 / 红旧色谱、把状态色当角色色、把它和「柔和蒙德里安 v2」当成同一套配额
出处：openspec/changes/graph-node-visual-language（specs/graph-visual-language/spec.md「Projection colour keys」「Night paper graph adaptation」）；openspec/changes/workbench-visual-language-v2/decisions.md G-7 / G-16

### 单层实心圆节点 / Solid node
知识图谱节点的形态：一枚**单层实心圆点**——单层平涂的实心圆，只有一层填充色，没有描边、没有阴影、没有光晕、没有渐变、没有内高光，也**不是内外两层嵌套**。圆心**按投影决定有没有数字**：题目数量投影下是该节点关联的**正式题数**，重要性投影下是**取整后的重要度百分比**；关系结构与学习状态两个投影下**圆心不写数字**（结构由连线表达，状态由颜色表达）。任何投影下节点上都不画状态文字、进度弧、仪表、徽标或卫星点。**量值只由半径承载**（没有「外环粗细」这一说）：半径在当前投影的量程内单调映射，值越大点越大。标签画在**点的下方**（点下缘到字顶 5 屏幕 px），字号 **12 屏幕 px 恒定**，缩放到 0.5 倍以下按对数淡出。选中或悬停 = **换色 ＋ 点外缘 1 屏幕 px 细环 ＋ 轻微放大 ＋ 标签提亮**；常态节点没有环，也不靠阴影或光晕表示「抬起」。学习状态由颜色与节点几何共同表达，状态名由学习看板、悬停提示与无障碍名承载。
_Avoid_：同心圆节点、外环、内核、带边的圆片、五层叠加的节点、状态环、度量弧、进度仪表、节点上的状态文字、卫星点、节点阴影
出处：openspec/changes/graph-node-visual-language（specs/graph-visual-language/spec.md「Node appearance language」「Selection and focus」；acceptance.md / IMPLEMENTATION-LOG 写作「单层实心圆点」，同一形态）；openspec/changes/workbench-visual-language-v2/decisions.md G-1 / G-6 / G-9 / G-13 / G-15 / A-28 / A-109

### 图谱色键 / Graph colour key
一个图谱投影与「什么颜色对应什么类型」之间的对应关系。关系结构投影取墨阶三档（颜色不承载语义，关系类型由连线样式表达）；题目数量与重要性投影共用一条橙色明度阶（值越大颜色越重）；学习状态投影取图谱暖色板里的状态四色。图例分两块：上半是关系线型，下半是当前投影的节点颜色，并随投影切换。
_Avoid_：全局配色方案、状态色即角色色、以为节点颜色永远表示学习状态、图例只有一套颜色含义
出处：openspec/changes/graph-node-visual-language（specs/graph-visual-language/spec.md「Projection colour keys」「Graph colour legend follows the projection」）；openspec/changes/workbench-visual-language-v2/decisions.md G-8 / G-11 / G-12 / G-14

### 屏幕空间尺寸 / Screen-space sizing
知识图谱节点绘制尺寸的单位约定：节点的绘制半径、标签字号与点标签的间距按**屏幕像素**定义，不随画布缩放一起缩小——缩放只改变节点之间的间距。节点半径在当前投影的量程内连续映射（值越大节点越大），因此整图缩放到「适应画布」后，节点的圆心数字（只在题目数量与重要性两个投影下存在）与名称仍然可以直接读，不必再放大。
_Avoid_：世界像素尺寸、随缩放一起变小的字号、按缩放阈值隐藏标签、把这套尺寸约定套到图谱以外的页面
出处：openspec/changes/graph-node-visual-language（specs/graph-visual-language/spec.md「Screen-space sizing」）；openspec/changes/workbench-visual-language-v2/decisions.md G-24

### 状态筛选分群 / State Filter Clustering
知识图谱的只读多选筛选：从 `needs_work / review / mastered / null` 选择一个或多个状态，按并集保留节点，并让不同状态围绕各自中心聚拢。无选项表示显示全图；筛选不改变指标投影、练习选区或学习数据。
_Avoid_：状态修改器、自动分班、持久社区
出处：workbench-ui spec「Multi-state graph filtering」

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

### 按需契约披露 / On-demand Contract Disclosure
Agent 每轮只收到精简能力地图；它可通过 `python -m workbench.bridge.agent_contracts list` 发现五个既有主题，并在执行对应专门动作前读取相关主题的完整操作契约。该模块只打印静态说明，不是新的 `lesson-kit` 顶层命令，也不读取或写入学习数据。
_Avoid_：每轮重复注入整本操作手册、为每个主题新增顶层命令
出处：openspec/specs/agent-contract-disclosure/spec.md「Ordinary turns receive a small context map rather than the full operation manual」

### 本地发送箱 / Local Agent Outbox
按工作区和对话保存在浏览器本地的消息恢复记录，包含原消息、提交时请求上下文与发送状态。状态未知时用原提交标识核对；服务端拒绝时可恢复原文；已接收但失败时，只有用户明确操作才创建关联新轮次。成功完成后清除。它不排队自动发送，也不自动重放工具操作或写入。
_Avoid_：待发消息队列、自动重试
出处：`preserve-agent-messages-and-tool-outcomes`

### Agent 提供方 / Provider
一次 Agent 对话创建时固定的底层 Agent 命令行（codex / claude / pi）。对话**不会中途换 harness**；换的是同一个 harness 上的**模型条目**（见下），且只在下一轮生效。未配置 provider 时如实提示。
_Avoid_：模型热切换（当前轮不改）、把显示名当 harness 名
出处：workbench-ui spec；ai-teacher-bridge spec

### 模型条目 / Model Entry
`bridges.json` 里可选的一组具名模型：`{name, provider, model, args?}`。**显示名由你定**，与 harness、模型串解耦（例如显示成 `DeepSeek V4` 而不是 `pi · deepseek/deepseek-v4-flash`）；条目在读取时按名字挂到已发现的 harness 上（命令、预算与启动旗标仍来自 harness），harness 不在本机就跳过这条而不报错。没有任何条目时，选择器回退成「一个 harness 一条」的历史行为。命令行 `lesson-kit bridge add-model <显示名> --provider <harness> --model <串>`。
_Avoid_：把显示名当模型 id、为每条条目复制一份命令配置
出处：ai-teacher-bridge spec「Named model entries」

### 对话内切换模型 / In-chat Model Switch
对话头部下拉框（只列该对话 harness 上的条目），选中后 `PATCH /ai/sessions/{id}` 写入对话的 `model`：**下一轮**用它启动（缓存的 Pi RPC 进程立刻丢弃，免得旧进程还用旧模型），原生会话 id 保留；若该服务拒绝跨模型续接原会话，桥**放弃旧会话、开一个新会话**并在对话流里写明「本地历史不受影响」。轮次运行中切换返回 409，不猜。
_Avoid_：丢掉本地镜像、静默换 harness、当前轮热切换
出处：ai-teacher-bridge spec「Per-conversation model」

### 执行计划 / Execution Plan
Agent 单轮处理中显示在对话流里的可读活动时间线：把工具调用、命令执行、搜索与回答生成按发生顺序列成步骤，并用「进行中 / 已完成 / 失败」表示状态。它只展示提供方明确输出的活动，不展示隐藏推理，也不把底层协议事件名直接当界面文案。
_Avoid_：任务状态码、思维链、后台日志墙
出处：ai-teacher-bridge spec「Readable execution plan」

### Agent 对话栏 / Agent Rail
工作台壳层中始终可用的 Agent 对话主表面；“始终可用”指它属于会话壳层，不表示始终展开：桌面端右列可折叠，窄屏下的右列抽屉可关闭并返回中栏。消息、模型选择、上下文提示与输入均以会话为中心组织。Tool、持续任务、审批与 Artifact 的额外工作面只在运行时需要时出现，不得把右栏演化成常驻任务面板；视觉直接继承「柔和蒙德里安」与 `workbench.css` 现有 token，不建立独立深色 Agent 主题。
_Avoid_：独立 AI 应用壳、常驻 Tool Dashboard、与 Lesson Kit 脱节的深色主题岛
出处：docs/design/AGENT-UI-V1.md；workbench-ui spec「Three-column shell with navigation」

### 工具调用卡 / Tool Call Card
单次工具、命令、搜索或确定性动作的语义执行摘要，在对话流中显示可读动作名、实际状态与有证据支持的结果/影响；未知影响必须如实标为未知。诊断信息经过净化并默认折叠，摘要不超过 240 个字符。恢复控件只对应后端实际支持的操作。

**形态（单行流水）**：**一行头**（状态点 + 工具名 + 耗时 + 展开按钮）+
**一行摘要**（不展开即可读）+ **默认收起的详情区**。耗时**只取活动自报值**，
没有就**整格不显示**（不猜、不补）。失败由**状态点**承担，**不加红字**。
展开 / 收起用真按钮（`aria-expanded` + `aria-controls`），不用原生 `<details>`。
_Avoid_：原始协议事件墙、完整终端日志、思维链、把每个底层事件拆成独立卡片、工具日志、调用记录
出处：`preserve-agent-messages-and-tool-outcomes`；workbench-ui spec「Provider activity cards show evidenced outcomes」；
openspec/changes/workbench-component-forms（§4.25 · 形态裁定 A-115）

### Agent 工件 / Agent Artifact
Agent 产生的、值得交接或后续继续操作的结果对象，例如生成完成的试卷。它与 Tool Call Card 区分：Tool 表示“做了什么”，Artifact 表示“做出了什么”。Artifact 可在对话中以结果卡出现，并可由辅助工作面预览；完成 Artifact **不会自动切换当前 Lesson Kit 页面**，进入其正式页面必须由用户显式触发。此词条只定义 UI 交接概念，不引入持久化结构或试卷生命周期；保存语义归 paper model 契约。
_Avoid_：工具日志、一次 Tool 的返回文本、完成即自动跳页、把所有回复都称为 Artifact
出处：docs/design/AGENT-UI-V1.md

### 辅助工作面 / Auxiliary Work Surface
中央 Lesson Kit 页面之外、由 Agent 运行状态临时唤起的工作面总称。当前包含顶部右侧 Activity Float（短时与持续任务进度）和 Adaptive Split（用户显式预览 Artifact）；活动结束后清理，不固定为永久 chrome。

_Avoid_：第二主页面、常驻任务中心、强制展开到中央区域
出处：docs/design/AGENT-UI-V1.md
### 活动浮层 / Activity Float
位于中央工作区右上方的有界、可替换活动层，用于短时活动及持续任务的当前里程碑与最新状态。新活动替换显示内容，不累积为历史任务列表；用户可用小型可访问控件收起或展开。同一用户轮次的后续更新不会自动重新展开，新轮次恢复自动展示；活动结束后消失。历史仍由对话流与执行计划承载。

_Avoid_：通知中心、历史任务抽屉、永久悬浮工具栏
出处：docs/design/AGENT-UI-V1.md
### 底部工作坞 / Bottom Dock
已退役：当前实现不为任务进度渲染底部工作区，短时与持续任务统一使用 Activity Float。此名称仅用于解释历史文档或旧设计，不表示当前能力。

_Avoid_：第二聊天窗口、后台日志面板、永久状态栏
出处：openspec/changes/use-collapsible-agent-activity-float
### 自适应分栏 / Adaptive Split
当最新 Agent Artifact 需要可视预览时，对中央工作区进行的**临时分栏**：原 Lesson Kit 页面仍在，Artifact 预览占用辅助一侧；它是交接面而不是导航结果。用户显式进入 Artifact 的正式页面后，分栏可结束。用户已主动收起辅助工作面时，Artifact 不得强制重新展开它。
_Avoid_：完成即页面接管、自动导航、永久双栏布局
出处：docs/design/AGENT-UI-V1.md

### 审批门 / Approval Gate
风险较高、可逆性较低或产品契约明确要求确认的 Agent 动作在执行前使用的显式决策面，说明将发生什么及其影响，并提供批准 / 拒绝。现行 v1 回滚审批临时替换普通输入框；其他动作的占位方式由对应 capability contract 规定。普通可逆 Tool 不应滥用审批门，审批状态不是聊天消息，也不是所有动作都弹出的通用确认框。
_Avoid_：每次 Tool 都确认、仅凭 Agent 文字宣称已经获得批准、未区分动作就套用同一输入区规则
出处：docs/design/AGENT-UI-V1.md

### 试卷进度重置审批 / Paper Progress-reset Approval
Agent 提议更新既有 Paper 的题目名单或题序时，对该更新及其未完成进度、草稿影响的显式批准 / 取消决定。审批与普通输入区并存，显式排队消息进入暂停队列，中断后发送或立即发送会被拒绝并保留原文或队列项；点击批准后由页面发起受版本校验的写入，而非让 Agent 自行执行 CLI。保留 Paper ID、题目本身、历史作答与其他 Paper 的进度。待审批决定可恢复，批准或取消后仍由用户手动继续队列。
_Avoid_：删除历史作答、自动批准、把预览快照当作用户授权、把改题字段与改卷名单混为同一动作

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

### 内容批次动作 / content bundle action
Agent 在对话中**新增**学习内容的结构化动作：合法的纯新增动作自动执行，不再依赖浏览器关键词意图（`check_intent` 已删除）；修改、删除、回滚与难度评级仍然只按学生的明确指令执行。清单（`content-bundle`）可同时包含新知识点、正式题、微题、闪卡与必需原图，条数没有上限；大清单先暂存到本对话的 jobs 目录，区块里只写文件名。服务端一次预检（引用、字段契约、来源、图片字节、目标冲突）、一份可恢复备份；**一份清单可以跨章**：每个知识点/题目/闪卡都可以写自己的 `chapter`，缺省用清单顶层的 `chapter`；两者都未提供时该项会被点名拒收，**不回退到工作区当前章**。服务端按每一项的章发号、按章落图、**按章各记一个批次**（各带自己的回滚标记，可单独撤销）。任一条不合法或缺必需图片即整批零写入，并逐条给出原因，Agent 修正整份清单后重提。一轮回复里的每个 content-bundle 区块都会被依次应用。成功以结果卡片呈现（每章一行：批次号、章、资产类型与数量、来源分布、工作区、备份、当前回滚状态）。
_Avoid_：关键词意图门、静默丢弃不合格条目、跳过门禁直写池、显式命令面板
出处：ai-teacher-bridge spec「Atomic staged content bundle」；FILE_CONTRACT.md

### 暂存清单 / Staged manifest
写在 `.lessonkit/jobs/conv-NNN/` 下、随对话保留的完整内容清单。服务端只接受该对话目录内的相对 `.json` 路径；绝对路径、`..` 与非 JSON 一律拒绝，回答正文不承载清单本身。

### 来源证据 / 来源答案 / AI 生成解析
来源证据（`source_evidence`）：每道 Agent 新增题必填的出处（如「教材 第12章 习题12-5」），显示在题目下方。来源答案（`source_answer`）：教材给出的短答案，单独存放、不覆盖详细解析。解析来源（`solution_origin`）：保留 `source/generated` 来源元数据；按需生成的内容可直接入库，统一进入正常解析展示，不额外出现「AI 生成解析」独立区，也不重复已展示的相同解析。
_Avoid_：用 AI 解析覆盖教材答案、把来源证据只留在批次快照里

### Pi RPC 常驻进程 / Conversation-owned Pi RPC process
Pi 对话不再每轮起一个 `--print` 进程：每个对话一个隐藏的 `pi --mode rpc` 进程，以严格 LF JSONL 收发带 id 的命令与流式事件，空闲 30 分钟回收（不设并发上限，删除对话/关闭服务工作台都会回收）；取消先发 RPC `abort`，失效才 terminate/kill；启动或握手失败可重启一次，prompt 被接受后崩溃不得重放。所有 provider 子进程在 Windows 下都不弹终端窗口。

### 批次 id / Batch id
一次门禁 apply 写入池的那批内容的唯一标识（可读顺序 id，形如 batch-NNN，禁哈希）；批次内每一内容行携带该标记，用于事后溯源与整批撤销。跨章清单一趟写出**多个**批次（一章一个），所以撤销可以按章进行；一次导入仍只有一份池级备份。
_Avoid_：内容版本号、逐条审计日志、哈希 id
出处：DISCUSSION-RECORD 专题 20/22；workbench-content-governance spec「Batch provenance and rollback」

### 整批回滚 / Batch rollback
按批次 id 一条命令撤销该批全部内容行的安全网（`lesson-kit ingest rollback --batch <id>`，对话桥结果卡片回滚按钮同源）；核对内容仍处于 apply 后状态且没有阻塞学习记录后才做安全备份，再回滚并输出 accounting。apply 后被改动的内容会在创建备份前触发冲突拒绝，不覆盖后续修改。
_Avoid_：逐条手工删行、全池回退、静默丢弃练习记录
出处：DISCUSSION-RECORD 专题 20/22；workbench-content-governance spec「Batch provenance and rollback」

### 自绘下拉 / Custom select
由**触发器 + 浮起面板**构成的单选控件，取代原生 `<select>`：触发器带 `combobox`
角色与展开态，面板是 `listbox`，选项是 `option`。三条硬约束：**焦点留在触发器**
（不进面板）、控件**只占一个 Tab 停靠点**、**无脚本时回落原生 select**
（给出同样选项、报同样值）。
_Avoid_：下拉框、原生下拉、弹出层（那是泛称）、组合框（泛称）
出处：openspec/changes/workbench-component-forms（spec「Custom select replaces the
native select」）；component-spec.md §4.7 / §6.2

### 载荷承载域 / Payload-carrying field
**承载提交值的那一个字段**。自绘下拉替换原生控件后由**隐藏域**担任，
**保留原字段名与原选项值** ⇒ 请求的方法 / 路径 / **载荷键集合逐条不变**（底线守卫 G-1）。
_Avoid_：表单字段、取值字段、状态字段
出处：openspec/changes/workbench-component-forms（spec「Custom select replaces the
native select」）

### 焦点陷阱 / Focus trap
模态打开期间，**Tab / Shift+Tab 只在对话框内部移动焦点**，不会跑到背景内容上。
它与「焦点归还」成对出现，且**只属于模态** —— 非模态界面一律不得有焦点陷阱。
_Avoid_：焦点锁定、焦点管理、键盘捕获
出处：openspec/changes/workbench-component-forms（§4.24 / §6.2）

### 焦点归还 / Focus return
模态关闭后，**焦点回到打开它的那个元素**；若该元素已不在 DOM，
焦点落到**它所在的区域**，**不得留在 body**。
_Avoid_：焦点恢复、焦点复位
出处：openspec/changes/workbench-component-forms（§4.24 / §6.2）

### 编号点串 / Numbered step rail
表达**离散步数完成度**的形态：**编号圆点 + 连接线**，每步带序号；
四态（完成 / 当前 / 未开始 / 失败）各有**不同的形状**与颜色。
它**不是控件**：不进 Tab 序列、不改值、不发请求。
_Avoid_：步骤条、进度点、阶段指示器（那是泛称）、分段进度条（同义但本词更具体）
出处：openspec/changes/workbench-component-forms（§4.16 / §4.30）

### 模态对话框 / Modal dialog
**需要打断用户**的确认界面：背景 `inert`，**Esc 关闭**、**焦点陷阱**、
**焦点归还**。遮罩点击**不关闭**（关闭须显式动作）。它是**唯一接管焦点**的界面。
_Avoid_：弹窗、弹层、确认框（泛称）
出处：openspec/changes/workbench-component-forms（§4.24 / §6.1）

## 工程与流程

### 学习证据查询 / Learning Evidence Query
按知识点读取一组有上限的近期作答记录，并附上可读题面与数据库里实际记录的作答、判定、自评或时间。题面来自当前题库内容，不是作答时的历史快照；该查询不推断薄弱、粗心或进步等学习特征。
_Avoid_：题目原始版本快照、学习者画像、自动薄弱判断
出处：`agent-learning-evidence` OpenSpec

### 检索评估 / Retrieval Evaluation
开发者运行的确定性诊断：读取已注册工作区，通过现有只读数据接口检查清单中指定事实能否被找回，并报告结果与读取次数。它不调用模型或提供方、不写入学习数据、不改变产品检索排序，也不是学生功能。
_Avoid_：产品检索、学习者能力评分、语义检索系统
出处：`retrieval-evaluation` OpenSpec；`docs/AGENT_RETRIEVAL_EVAL.md`

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

### 试卷执行进度 / Paper Execution Progress
一张 Paper 的未完成 Practice Run 所附带的执行状态，包括固定题序、当前游标、答案展示方式、未提交草稿、显式不会标记、提交/锁定状态和已显示参考材料的事实；不等于题目本体，也不等于 Attempt、自评或调度等学习证据。每张 Paper 可分别保留一份未完成进度，同一工作区同一时刻只激活一卷。普通 Paper 的整卷完成只由显式提交产生。
_Avoid_：把题目掌握度当作卷内游标、把清卷进度当作删除学习证据
出处：2026-10-17 所有者需求确认；`decouple-paper-progress-and-content`

### 历史保留题目 / Historical Question Row
被用户删除后，仅为既有作答、评分与轮次保留身份的题目行，以 `problems.deleted_at` 标记。
它不再属于可练习或可编辑的当前题库，原题号不得被另一个题目复用；保留行不是恢复到当前题库。
_Avoid_：删题同时删历史作答、把保留行继续用于组卷
出处：2026-10-17 所有者确认的题目删除边界；`decouple-paper-progress-and-content`

### 待发消息 / Pending Message
用户已经提交、尚未开始由 Agent 处理的消息。它保留原文和提交时的页面上下文；显式选择排队的消息组成有序队列，默认按提交先后执行，也可在执行前明确重排。中断后发送的停止交接不属于该队列。同一对话始终最多执行一个轮次，待发状态不是 Agent 已开始工作，也不是已经回答。
_Avoid_：同一对话并发执行多个任务、按稍后页面覆盖原消息上下文
出处：`ai-teacher-bridge` 消息生命周期契约；2026-10-20 所有者确认的 `compact-agent-queue-and-direct-interrupt`

### 中断后发送 / Interrupt and Send
用户显式中断当前 Agent 轮次，保留已经完成的操作，在确认当前轮次停止并释放 worker 后直接处理指定消息。该消息不进入普通队列，也不依赖继续队列；无活动轮次时直接执行，已有排队消息仍保留且暂停。待审批或已有另一停止交接时明确拒绝，不能自动改成排队。处理完新消息不自动续原任务；这不是自动回滚，也不是把新消息与旧任务同时运行。
_Avoid_：无停止确认就并发启动、自动恢复原任务、把未完成工作标为成功
出处：`ai-teacher-bridge` 中断契约；2026-10-20 所有者确认的 `compact-agent-queue-and-direct-interrupt`

### 走查 / Scratch Walkthrough
交付前的真实浏览器验证：在池数据库副本 + 隔离注册表 + 独立端口上种子数据逐项点检（截图自检清单）。**永不写真实池。**
_Avoid_：测试通过即完成（明确的反模式）
出处：2026-08-29 交接文档；FUTURE-DEVELOPMENT-NOTES UX 清单

### Lesson Kit 内置技能 / Bundled Lesson Kit Skill
随 Lesson Kit 安装包分发、仅由 Lesson Kit Bridge 显式加载的教学资源。当前包含材料约束型随堂练习的技能正文与局部术语表；不属于课程资料，也不写入 Pi 全局配置。它描述教学方法，不在 CLI 中增加教学业务逻辑。
_Avoid_：逐课程复制技能、将内置技能等同于 Pi 全局配置
出处：`unify-cli-and-bundle-drill-skill`

### 答案展示方式 / Answer Reveal Timing
普通题 Paper Practice Run 开始时选择的答案披露与锁定安排：逐题显示（`per_item`）或交卷后统一显示（`on_submit`）。它与题目类型、组卷方式和可选自评相互独立，并在暂停、恢复与完成答卷查看时保持不变。逐题显示时，单选/判断选择会自动提交，多选/文字需明确提交；交卷后统一显示时输入可改至整卷提交。任何模式中显式点「不会」都可提前展示可用参考材料；逐题模式会锁定该题，统一模式允许交卷前改答案并清除不会标记，但保留已看参考材料的事实。
_Avoid_：把答案展示方式当成题型、组卷方式或自评开关
出处：`free-navigation-paper-practice`「Mode-specific answer reveal and locking」


### 像素进度带 / Pixel Progress Band
Paper 练习页中表示已完成题目比例的方块色带。深橙、黄色、天蓝色随完成度变化；等宽明暗压缩带横向传播，密集处更亮。轨道圆角、无黑描边；末端为与轨道等厚的正方形像素头，脉冲抵达时由中心向外亮起，间隔时黯淡。仅为展示，不产生学习证据。

### 连对横幅 / Combo Banner
逐题判定模式中，每连续五次客观答对出现的短暂庆祝条幅。两种练习共用已批准并冻结的暖白底、左黄块、底部蓝带、红色角块、斜体矢量 combo 与 SVG 画笔动效；Paper 同时叠加临时异色进度波带。不把自评或未判定答案当作答对。视觉基准存于 `docs/design/approved-practice-combo/`，改变样式需学习者明确批准。

### 归位庆祝卡 / Settling Completion Card
成功交卷后先突出登场、随后缩退到完成页顶部的同一张庆祝卡片；下方保留真实统计与逐题回看。历史答卷直接显示稳定终态。
