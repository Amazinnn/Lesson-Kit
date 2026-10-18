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

### 课程标识符 / Course Identifier（slug）
一门课程（一本教材）的机器名：小写 ASCII（字母、数字、连字符），既当池库名（`pool/<course>.db`）又当每条内容 id 的前缀段（`dmath-ch06-kp-001` 里的 `dmath`）。它与人看的工作区名是两样东西——中文文件夹名照样可以当工作区名。注册时按「显式 `--course` › 已有池名 › ASCII 文件夹名推导 › 自动顺序短码 `c01`、`c02`…」取一个：前三条是人认得的名字，最后一条只是机器内部的下标（自动分配，顶栏不显示）。显式给的值一律按本式样校验，不合就带理由拒绝——ingest 各条门禁只认这个字符集。
_Avoid_：工作区名（人看的、可中文）、自由命名的课程名、把短码当成课程名

出处：openspec/specs/review-workbench「Unified CLI entry point」「Course and chapter switching」；workbench/cli/main.py

### 知识池 / Knowledge Pool
课程级的 SQLite 存储（`pool/<course>.db`，`<course>` 即「课程标识符」），保存提取好的知识点、正式题与全部学习状态。整个工作台的数据底座。
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
左栏「设置」区块里的浏览器偏好，按工作区存于 `localStorage`（`wb_settings_<工作区>`），**跨标签页与重启持久**；它与可选的本地布局种子共同构成工作台当前的持久 `localStorage` 用法，其余客户端状态仍是会话级。第一项是「练习与组卷显示自评」（默认开）：关闭后自评在练习与组卷流程里完全消失（不选自评时机、无反馈面板、不进统一自评页、记录页标「关闭自评」），客观题按判定折算学习状态。设置在**下一轮开始时生效**，进行中的轮次保持开始时的模式。设置只表达偏好，不是学习事实，不写池。
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
Lesson Kit 的**最小可执行作答单位**：开始、暂停、继续、提交与完成状态都围绕一张已经冻结 item 顺序的 Paper 发生。Paper 可以由 Agent、预先编排、题库筛选或其他组卷方式产生；知识范围和题型策略只约束组卷，不在 Practice Run 中动态改题。当前 `.lessonkit/practice-sets/`、`ps-NNN`、manifest `kind: practice-set` 与 `/practice-sets/...` 是迁移期兼容实现名，不改变本条产品定义。
_Avoid_：Practice Run 本身、动态知识点查询、把兼容名 practice-set 当产品题单
出处：practice-set-export spec「Paper is the Practice Run boundary」；review-workbench spec「Paper-backed Practice Run」「Practice Run interruption recovery」；workbench-ui spec「Flash card item stacked presentation」

### 题单 / Practice Set
**组织多份 Paper 的容器**，用于按课程进度、专题能力、真题来源等组织练习路径；题单本身不直接进入作答。地图形、桶形等只是题单的视觉布局，不产生新的内容类型。v1 允许题单容器尚未完整实现，但不得再把一张可执行 Paper 命名为产品级 Practice Set。
_Avoid_：试卷、一次 Practice Run、旧 `.lessonkit/practice-sets/` 目录名的字面解释
出处：practice-set-export spec「Paper manifest」「Managed saved Paper」；FILE_CONTRACT.md「Agent Saved Papers」

### 练习轮次 / Practice Run
对**一张已经确定的 Paper**从开始到完成，或到被显式替换 / 清除的一次执行。运行中仍只有一个 `active_practice`；新执行的来源语义统一为 `paper`，结束时把 Paper 身份、固定 item 顺序、最终状态与时间写入 `practice_runs` 最小快照。逐题作答、判定、自评仍以 `problem_attempts` / `feedback_events` 为学习证据。
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
生成或挑选一张具体 Paper 内容的过程。`lesson-kit pull` 当前是确定性组卷引擎：范围（`--kp`）、来源/难度等条件筛选、薄弱 / 到期 / 错题驱动共同决定候选与排序。`--problem` 精确题号能力只作为 Agent/CLI 的**作者工具**保留，用于确定性固定某题；它不得重新暴露成学生在练习页、知识点页或图谱里逐题手选的入口。每个结果仍回报 `scope` / `weak` / `due` / `wrong` / `explicit` 等入卷理由。
_Avoid_：手动选题 UI、把组卷直接等同 Practice Run、把 `--problem` 当学生侧练习动作
出处：practice-set-export spec「Paper assembly」；review-workbench spec「Paper assembly engine」；workbench-ui spec「Practice page」

### 筛选维度 / Filter Dimension
来源筛选的四个**多值**维度：`source_kinds`（来源类型）、`origin_kinds`（题目来源方式）、`exam_years`（考察年份，仍按前缀）、`docs`（来源文档，对 `source_evidence` 做不区分大小写的子串匹配，值就是「文档键」）。语义是**维度内 OR、维度间 AND**：勾中的同一维度里任意一个命中即可（`final` 或 `midterm`），不同维度必须同时满足（是 final **且** 属于 2023）。浏览器中的来源维度只用于约束 Paper Assembly：按维度分组勾选并显示池内实际计数；`origin_kinds` 一组显示为历年原题 / 改编 / AI生成。浏览器不再提供「搜索后挑某一道题加入练习」的 `include_ids` 产品语义；CLI 的精确题号只属于作者工具。其余多值维度仍遵循维度内 OR、维度间 AND。
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

### 柔和蒙德里安 / Soft Mondrian
Lesson Kit 的视觉语言：暖纸色与深色结构线占主体，蓝/黄/红只承担主要动作、
当前或复习强调、重点练习或失败等有限语义。状态同时保留文字或几何提示。
出处：workbench-ui spec「Soft Mondrian visual foundation」

## 选择与练习

### 范围 / Scope
用户用知识点、图谱区域或其他课程语义明确的**组卷边界**。范围回答「想练什么」，用于约束 Paper Assembly；它本身不是待执行题目清单，也不能直接开始 Practice Run。弱项、到期与建议可以影响组卷排序或成为新的范围建议，但不得静默扩大用户已经明确的范围。
_Avoid_：待练题目列表、Practice Run 的内容本体、弱项自动抓题、把知识点选择直接当成一次练习
出处：review-workbench spec「Chapter lens scoping」；workbench-ui spec「Practice page」

### 准备练习列表 / Staged Practice List（已退役）
**已退役（2026-10-15）**。历史含义是把知识点选区在练习页再显示成一份「真正要练的」清单，并由它直接拉题开练。Paper 成为最小作答单位后，这个中间层不再有产品身份：知识范围直接进入组卷，组卷得到 Paper，Practice Run 只执行已经冻结的 Paper。
_Avoid_：重新建立「知识点队列 → 直接练习」中间态、把范围列表称为试卷
出处：workbench-ui spec「Practice page suggestions and assembly entry」

### 建议 / Suggestion
练习页按需给出的**组卷起点或练习方向建议**，可来自每日计划、到期调度、薄弱证据等。建议可以预填范围、题型策略或触发「据此组卷」，但不直接向当前 Practice Run 加题，也不维护一份独立的待练知识点队列。
_Avoid_：Staged Practice List、自动扩充正在执行的 Paper、到期列表（已废弃的常驻视图）
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
规定某类课程内容适合以哪些作答形式练习或检测的**组卷约束**。例如知识点内容可偏判断，记忆型内容可用闪卡，阶段检测可混合多种形式。策略作用于 Paper Assembly，不把整张 Paper 锁成一种题型；用户可以限定策略，但不因此逐题手选。
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
判断题或单选题入库时题源没有正确答案，`answer_key` 省略或为 `null` 的形态。它照样进判断/小测模式（`quiz_type` 与 `options` 照常），但不参与判分：练习页明确显示「本题未录入答案键，请对照课本或解析自评」，作答文本仍记录，学习状态仍由 1–5 自评写入。答案键可以事后补：`lesson-kit data <工作区> update problem <id> --input '{"answer_key":"…"}'`（按该题的 `quiz_type` 校验形状；空值清回无键）。带键的题必须有 `error_reason`，无键的可以没有。
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
一轮练习保存的自评安排：每题作答后自评（immediate）、完成后统一自评（batch），或关闭自评（off）。开启自评时开始前选择前两种时机；偏好关闭时直接以 off 开始。偏好变化只影响下一轮，进行中的轮次保留原安排。
_Avoid_：评分方式（与 1–5 自评本身混淆）
出处：workbench-ui spec「Practice session」

### 练习会话 / Practice Session（已退役产品术语）
**已退役（2026-10-15）**。历史上指「单一练习模式 + 动态题目队列 + 当前题」的标签页状态。产品层统一使用「试卷 / Paper」描述固定作答内容，使用「练习轮次 / Practice Run」描述一次开始、暂停、继续到结束的执行。代码中的 sessionStorage key 或旧 spec 标题可以暂时保留为兼容实现名，但不得继续据此设计新的产品行为。
_Avoid_：把 Practice Session 与 Practice Run 并列成两种执行实体、把单一模式队列重新定义成练习本体
出处：review-workbench spec「Paper-backed Practice Run」「Practice Run interruption recovery」；workbench-ui spec「Practice page」

### 上一题结果视图 / Previous Result View
练习页已有的只读作答回看界面。没有服务端 Practice Run 身份时，仍只回看紧邻上一道普通题；选中 Paper Practice Run 时，可在同一次执行内往返浏览所有已有作答或「不会」状态的普通题，且不设回看次数上限。Paper 回看位置独立于练习游标；每次进入都先显示自己的作答、已有判定和自评，参考答案与解析收起，需主动展开。未确认提交明确标注且不可评分；不可用的判定如实显示。返回当前题恢复草稿，新 Agent 消息聚焦当前可见回看题。回看不移动练习游标，也不表示浏览器提交已持久保存。闪卡仍使用「上一张 / 下一张」移动游标。
_Avoid_：把回看当作重新作答、把浏览器已提交视为服务端已保存、把闪卡回翻当作本视图
出处：practice-review spec

### 自评 / Self-Rating
学习者对一道完成题的显式 1–5 打分（可带自然语言备注），首次评分写入对应反馈并按评分更新学习投影。Paper 回看中再次保存只覆盖同一执行、同一 Attempt 关联反馈里的评分与评语，不新建作答或反馈，不重复更新学习投影；Agent Attempt Correction 是独立路径。关闭自评不合成 1–5 分或评分反馈；客观尝试的判定可另按 off 规则折算。
_Avoid_：把自动判定伪装成自评分、浏览即掌握
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
batch 时机下的收束页：只列尚未评分的题，逐题补 1–5 分或跳过全部；「再练同类」若提供，只能据当前结果重新组一张 Paper，不能给已结束的 Practice Run 动态加题。
_Avoid_：批量评分历史、补打卡
出处：DISCUSSION-RECORD B6.5；workbench-ui spec

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
_Avoid_：掌握度、分数、调度参数
出处：review-workbench spec「Action-oriented learning reminders」

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
图谱在 Worker 布局稳定后保存在浏览器中的可选坐标缓存。它只在节点 ID 与关系起点、终点、类型和方向完全匹配时作为临时锚点恢复，随后由原 Worker 继续求解；不保存筛选、选中、作者内容或学习事实。清除或无法读取该缓存只会失去上次图谱布局起点。
_Avoid_：布局编辑器、持久学习状态、数据库字段
出处：graph-lod-layout-seeds change；ADR 0028

### WebGL2 图谱渲染 / WebGL2 Graph Rendering
知识图谱关系线的唯一当前绘制路径，要求浏览器提供 WebGL2。关系几何仍由图谱物理核心提供，DOM 节点继续承担节点外观、选择、拖拽与无障碍交互；渲染初始化失败时显示错误并停止本次图谱运行，不回退到 SVG。
_Avoid_：可选 WebGL 增强、运行时 SVG 回退
出处：graph-webgl-rendering change；ADR 0027

### 指标投影 / Metric Projection
知识图谱对同一组节点的只读视觉重排：当前指标越高，节点越大且越靠近中心，并使用对应色谱；切换时节点以力场目标连续迁移。关系结构仍以知识关系决定位置。投影不新增指标、不改变选区或写入 Pool；稳定坐标的可选本地缓存遵循本地布局种子规则。
_Avoid_：排行榜、自动学习决策、持久投影状态
出处：workbench-ui spec「Metric projection morphology」
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
_Avoid_：原始协议事件墙、完整终端日志、思维链、把每个底层事件拆成独立卡片
出处：`preserve-agent-messages-and-tool-outcomes`；workbench-ui spec「Provider activity cards show evidenced outcomes」

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
Agent 提议更新既有 Paper 的题目名单或题序时，对该更新及其未完成进度、草稿影响的显式批准 / 取消决定。审批与普通输入区并存，输入消息进入暂停队列；点击批准后由页面发起受版本校验的写入，而非让 Agent 自行执行 CLI。保留 Paper ID、题目本身、历史作答与其他 Paper 的进度。待审批决定可恢复，批准或取消后仍由用户手动继续队列。
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
一张 Paper 的未完成 Practice Run 所附带的执行状态，包括题目完成标记、当前游标和未提交作答草稿；不等于题目本体，也不等于逐题作答、评分、调度等学习证据。目标行为允许各卷分别保留一份未完成进度，同一工作区同一时刻只激活一卷。
_Avoid_：把题目掌握度当作卷内游标、把清卷进度当作删除学习证据
出处：2026-10-17 所有者需求确认；`decouple-paper-progress-and-content`

### 历史保留题目 / Historical Question Row
被用户删除后，仅为既有作答、评分与轮次保留身份的题目行，以 `problems.deleted_at` 标记。
它不再属于可练习或可编辑的当前题库，原题号不得被另一个题目复用；保留行不是恢复到当前题库。
_Avoid_：删题同时删历史作答、把保留行继续用于组卷
出处：2026-10-17 所有者确认的题目删除边界；`decouple-paper-progress-and-content`

### 待发消息 / Pending Message
用户已经提交、尚未开始由 Agent 处理的消息。它保留原文和提交时的页面上下文，可属于某个对话的有序队列；同一对话始终最多执行一个轮次。待发状态不是 Agent 已开始工作，也不是已经回答。
_Avoid_：同一对话并发执行多个任务、按稍后页面覆盖原消息上下文
出处：2026-10-17 所有者纠正并确认；`complete-agent-message-lifecycle` 提议（尚未实现）

### 中断后发送 / Interrupt and Send
用户显式中断当前 Agent 轮次，保留已经完成的操作，在确认当前轮次停止后处理指定的新消息。处理完新消息不自动续原任务；这不是自动回滚，也不是把新消息与旧任务同时运行。
_Avoid_：无停止确认就并发启动、自动恢复原任务、把未完成工作标为成功
出处：2026-10-17 所有者需求确认；`complete-agent-message-lifecycle` 提议（尚未实现）

### 走查 / Scratch Walkthrough
交付前的真实浏览器验证：在池数据库副本 + 隔离注册表 + 独立端口上种子数据逐项点检（截图自检清单）。**永不写真实池。**
_Avoid_：测试通过即完成（明确的反模式）
出处：2026-08-29 交接文档；FUTURE-DEVELOPMENT-NOTES UX 清单
