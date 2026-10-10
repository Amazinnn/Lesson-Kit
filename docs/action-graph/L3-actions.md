# L3 · 动作层登记（人 / Agent 可执行的动作）

> 权限列按 2026-08-29 问卷 B1 口径：**人** = 界面操作；**Agent** = 可经 CLI/对话直接执行；**双** = 两边都有入口。
> 状态：`已实现 / 已定义未实现 / 未定义挂名 / 冻结 / 待退役`。

## 一、练习回路

| 动作 | 入口 | 权限 | 写 | 状态 |
|---|---|---|---|---|
| 切换章透镜（关 = 全课程；开着时选一章） | UI 顶栏「章」开关 | 人 | 注册表 `active_chapter`（与 `use` 同源） | 已实现（dashboard-chapter-filter） |
| 选定练习范围（选择是唯一来源） | UI 勾选 | 人 | 选区键 | 已实现 |
| 加入今日要练 | UI 建议区 | 人 | 选区键 | 已实现 |
| 开始本轮练习（模式+自评时机必选） | UI | 人 | 牌组 | 已实现 |
| 拉题/拉卡 | API/CLI | 双 | 牌组 | 已实现 |
| 组一次练习（范围/单题/条件筛选/薄弱·到期·错题；逐题 reason） | CLI `pull` | Agent | —（只读选择） | 已实现（2026-09-25） |
| 按来源证据筛题（`--source-evidence` 子串、可重复；与 `--source-kind`/`--origin-kinds`/`--exam-year` 同为「维度内 OR、维度间 AND」） | CLI `pull` | Agent | —（只读选择） | 已实现（2026-09-26） |
| 按题目来源方式筛题（`--origin-kinds` 可重复：历年原题/改编/AI生成，取并集） | CLI `pull` | Agent | —（只读选择） | 已实现（2026-10-06） |
| 按题干/来源关键词筛题（`--search-stem`/`--search-source`，空格多词、域内 AND、跨域 AND） | CLI `pull` | Agent | —（只读选择） | 已实现（2026-10-06） |
| 落练习清单（可重跑，零写入读取） | CLI `pull --plan` / `--input` | Agent | 练习清单 JSON（非池数据） | 已实现（2026-09-25） |
| 出练习集两份 Markdown（学生卷无答案/无内部标识，解答卷题号对齐、缺解「待补」） | CLI `pull --print` | Agent | `output/…-problem-set.md` + `-solutions.md` | 已实现（2026-09-25） |
| 练习集零写入预检（题数/缺口/缺解/重复/泄漏） | CLI `pull --check` | Agent | — | 已实现（2026-09-25） |
| 浏览已保存试卷（折叠卡片、展开题目预览） | UI `/practice-sets` | 人 | —（只读；卡片展开状态按标签页保存在 sessionStorage） | 已实现（2026-10-06/07） |
| 作答+本地判分（横幅 2s+高亮） | UI | 人 | 牌组 + **一条 attempts 行**（作答/选项/判定；2026-09-26 起落库） | 已实现 |
| 来源筛选浮窗（四维多选 + 池内计数 + 两个关键词域搜索选题；存 `wb_practice_filters_v2_<ws>`，不改池） | UI 练习页 | 人 | —（只读筛选，选择随标签页） | 已实现（2026-09-26，四维与双搜索框 2026-10-06） |
| 揭示（卡背/解析） | UI | 人 | 牌组 | 已实现 |
| 闪卡方向偏好与 ⇄ 交换 | UI | 人 | 牌组方向 | 已实现 |
| 闪卡回翻（上一张/下一张，末尾拉新） | UI | 人 | 牌组游标 | 已实现 |
| 即时自评 1–5 | UI | 人 | 四件套 | 已实现 |
| 学习者设置：练习与组卷显示自评（左栏勾选框，localStorage 持久；off 轮客观题判定折算为学习结论，不写评分事件） | UI | 人 | 浏览器偏好（不写池）+ off 轮判定落库时的折算写入 | 已实现（2026-10-07） |
| 关闭自评轮次的「下一题」（判分/解析后显式点击推进，无反馈写入） | UI | 人 | 牌组游标 | 已实现（2026-10-07） |
| 跳到下一道（已答/已玩不降级） | UI | 人 | 牌组 state | 已实现 |
| 提前结束→收束页统一评分 | UI | 人 | 四件套×未评 | 已实现 |
| 再练同类 | UI 收束页 | 人 | 新 session | 已实现 |
| 刷新恢复（游标+视图态） | 被动 | 人 | — | 已实现 |
| 切换图谱指标投影（大小/色谱/气泡式过渡） | UI | 人 | — | 已实现（只读、内存） |
| 图谱多状态筛选与分群 | UI | 人 | — | 已实现（只读、内存） |
| 练习页发消息附聚焦草稿（当前题目 + 未提交作答/选项/备注/当前可见图片；服务端限长） | UI 对话 | 人 | —（临时上下文，不写池、不写会话镜像） | 已实现（2026-09-24） |

## 二、记录与调度

| 动作 | 入口 | 权限 | 写 | 状态 |
|---|---|---|---|---|
| feedback 四件套 | API/CLI | 双 | 事件/信号/状态/调度（可带 `attempt_id` 链回那次作答） | 已实现 |
| 浏览器作答落库（提交即写，判定/选项同存；不碰信号·状态·进度·调度） | API `POST /attempts` / UI 提交 | 双 | attempts（status `answered`） | 已实现（2026-09-26） |
| 记录中心（概览/练习·试卷/作答明细/错题四视图；按题过滤；练习页「历史作答」折叠段） | UI / API `GET /records` | 浏（CLI 侧为 `attempts list`） | —（只读） | 已实现（2026-09-26 建，2026-09-29 扩为记录中心） |
| practice 尝试记录（CLI 与页面同一事务、同一存在性校验） | API/CLI | 双 | attempts + progress + schedule（单事务） | 已实现（2026-09-25 对齐） |
| 闪卡反馈与方向（CLI 补齐 card/direction） | API/CLI | 双 | 四件套（含方向调度键） | 已实现（2026-09-25 对齐） |
| 目标变更失效每日计划缓存（CLI 与 API 同一 helper） | API/CLI | 双 | plan.json（删除） | 已实现（2026-09-25 对齐） |
| 读命令 JSON 形态（人读默认不变） | CLI `weak`/`due`/`ls --json` | Agent | — | 已实现（2026-09-25） |
| Agent 代录尝试（转录 + 可选 1–5，可一次多题） | CLI `attempts apply` | Agent（学生明确要求） | attempts +（带评分时）事件/信号/状态/进度/调度 + `attempt_operations` 留痕 | 已实现（agent-assisted-practice-records） |
| 尝试清单预检（零写入） | CLI `attempts check` | Agent | — | 已实现（同上） |
| 指定尝试更正（撤回旧评分后重算；有更晚活动即零写入拒绝） | CLI `attempts correct <attempt-id>` | Agent（学生明确要求） | attempts 原文/评语/状态 + 事件/信号/状态/进度/调度 + 快照更新 | 已实现（同上） |
| 尝试与操作留痕读取 | CLI `attempts list\|get` | Agent | — | 已实现（同上） |
| 答卷目录登记（只存路径，不复制图片） | CLI `attempts sources add\|list\|remove` | Agent | `answer-sources.json` | 已实现（同上） |
| 图谱状态显式编辑（不记反馈） | UI | 人 | 状态+调度 | 已实现 |
| 图谱关系强度管线与有限消交叉 | UI | 系统 | —（纯视图） | 已实现（graph-relation-pipes） |
| 方向写入（最终使用的 direction 键） | UI/API | 双 | 方向调度行 | 已实现 |

## 三、内容治理（唯一合法写池）

| 动作 | 入口 | 权限 | 写 | 状态 |
|---|---|---|---|---|
| ingest 配方（micro-quiz / flash-card） | CLI | 双（Agent 可直跑） | problems/flash_cards 单事务（记批次 id+行戳记+manifest 快照）；**id 必须带本工作区课程前缀**；**难度可选、填了必带依据**（2026-09-21） | 已实现 |
| 全池备份 | ingest --backup | 同上 | pool/backups | 已实现 |
| **Check 管线**（生成→校验→**直接入正式池**，无候选中间态；批次 id+整批回滚；候选组织并入校验环节） | CLI `ingest rollback --batch <id>` + 结果卡回滚按钮 + `POST /ingest/rollback` | Agent 主导 | 经门禁写池+批次标记+ingest_batches 登记 | **已实现**（introduce-check-pipeline，队列④） |
| 抽取管线入池（教材→KP→题） | 管线脚本 | 人 | 全部内容表 | 已实现（一次性） |
| 作者内容镜像引导（pool-first：池写修订号 1 JSON + 台账；已有同 id 文件按嵌入身份采纳/冲突拒绝；不可读文件进报告、被其点名 id 的实体拒绝建档、其余实体照常；逐实体可恢复） | CLI `mirror init --repo <checkout>`（`[--entity] [--dry-run]`） | Agent | 池 `content_mirror_state`/`content_mirror_log` + checkout JSON | 已实现（2026-10-10，json-content-repository-sync/PR110） |
| 作者内容镜像只读分类（零写入；区分 noop/仓库→池/池→仓库/文件恢复/收敛/无效/冲突） | CLI `mirror check`·`mirror status --repo [--entity]` | Agent | — | 已实现（同上） |
| 作者内容镜像同步（逐实体三方比较：仓库修改经既有内容/关系校验器写池，内容+状态+日志同事务；池修改导出下一修订；缺失文件按新修订恢复；收敛恢复；冲突/无效逐条报告、成功兄弟保留；删除请求只校验报告、永不执行；不碰 Git 网络） | CLI `mirror sync --repo [--entity] [--dry-run]` | Agent | 池内容（经 `data.content`/关系校验器）+ checkout JSON + 台账 | 已实现（同上） |

## 四、Agent 桥

| 动作 | 入口 | 权限 | 写 | 状态 |
|---|---|---|---|---|
| 对话轮次（自动带页面上下文） | UI/CLI | 双 | conv 留痕 | 已实现 |
| 执行计划（命令/工具/搜索/回答活动归一化，同行状态更新，成功轮次可恢复） | UI 对话流 | 双 | conv 成功留痕 | 已实现（render-agent-execution-plan） |
| 新建会话/选 provider（harness 锁定不换） | UI | 人 | conversations | 已实现 |
| 模型条目配置（显示名自定、与 harness 解耦；无条目时回退「一 harness 一条」） | CLI `bridge add-model` | 人 | bridges.json `models` | 已实现（2026-09-26） |
| 对话内切换模型（头部下拉；丢弃缓存进程、下一轮生效；运行中 409；跨模型续接失败则开新会话并写明） | UI / API `PATCH /ai/sessions/{id}` | 人 | conversations `model` | 已实现（2026-09-26） |
| 停止轮次 | UI | 人 | turn=cancelled | 已实现 |
| replace_practice_selection（明确练习意图才生效） | 对话产出动作 | Agent | 浏览器选区（一次性） | 已实现 |
| content-bundle（内容批次：合法的纯新增动作自动执行，无关键词意图门；大清单暂存本对话 jobs 后由区块引用、小清单内联（`kind`/`type` 都认）→整份清单预检→一份备份→单事务 apply；**清单可跨章**，按每项声明的章发号/落图并**按章各记一个批次**，推不出章的条目点名拒收；**一轮里每个区块都应用**，学生说清几章就一轮导完；**题型（综合题/判断/小测）入库时可选，客观题允许无答案键**；失败逐条显式回对话流、零写入） | 对话产出动作 | Agent | 池内容 + `.lessonkit/figures/{course}/{chapter}/`（经门禁+按章批次标记）；补答案键走 `data update problem` | 已实现（2026-09-23；2026-09-25 跨章与多区块、题型与无键客观题） |
| problem-patch（原地改已有题目：补答案键/改题型/补来源/把选项从题面拆进 `options`；单题 `data update problem`、批量 `ingest recipe problem-patch --apply`；未知字段与难度字段拒收，题号不可改；批次记旧值可回滚） | 对话产出动作 / CLI | Agent（仅明确指令）+人 | problems（原地 UPDATE，不插入不删行） | 已实现（2026-09-25） |
| 内容审计（重复题/疑似片段/未标客观题/缺标题/图片引用；只读，可 `--check` 筛选、`--json` 输出） | CLI `data <ws> audit` | Agent | —（数据库与文件零写入；有发现返回 1） | 已实现（content-dedup-and-audit） |
| 整批回滚（结果卡按钮，与 CLI 同源 rollback；跨章导入时**每章一行、各撤各的**） | UI 结果卡 | 人 | 池内容（按批次删行） | 已实现（introduce-check-pipeline；2026-09-25 按章细化） |

## 五、目标与时间

| 动作 | 入口 | 权限 | 写 | 状态 |
|---|---|---|---|---|
| 目标创建 | UI 表单 | 人 | goals.json | 已实现 |
| 目标自然语言助填（NL→对话轮次→prefill_goal_form→表单原位填充，提交留给人） | UI 目标表单 | Agent+人 | 表单字段（不直接写 goals.json） | 已实现（complete-goals-loop） |
| 目标编辑/删除 | UI 卡片入口（同表单 PATCH/DELETE） | 人 | goals.json | 已实现（complete-goals-loop） |
| 目标时间跑道/月历/工作量只读视图（跨周切段、重叠分轨） | UI | 人 | — | 已实现（实验） |
| 每日计划重算 | UI | 人 | plan.json | 已实现 |
| 重日 prefill（只预填不发送） | UI | 人 | AI 输入框 | 已实现 |
| 复习重排建议 / 重日主动提醒（视图类，给 Agent 用） | 无 | Agent | — | 未定义挂名（问卷 C：延后） |

## 六、服务与运行

| 动作 | 入口 | 权限 | 写 | 状态 |
|---|---|---|---|---|
| 后台服务启动（分离进程；端口应答后才报成功；已在跑则幂等） | CLI `daemon start` | 人 | `~/.lessonkit-workbench/daemon.json`（pid/port） | 已实现（introduce-pi-agent-and-cli） |
| 后台服务停止（进程号被回收成非 Python 进程时拒绝终止并清记录） | CLI `daemon stop` | 人 | 清除 daemon.json | 已实现（同上） |
| 后台服务状态 | CLI `daemon status` | 人 | —（只读） | 已实现（同上） |
| 打开工作台（确保服务在跑 + 打开浏览器；不新增页面） | CLI `dashboard` | 人 | 需要时起服务 | 已实现（同上） |
| provider 解析清单（可执行文件、来源 config/path、路径是否缺失、生效的两个轮次预算） | CLI `bridge list` | 人 | —（只读） | 已实现（introduce-pi-agent-and-cli；2026-09-25 报告预算） |
| 显式钉死 provider 可执行文件（优先于 PATH 探测），并设定静默/工具两个轮次预算 | CLI `bridge add --command [--timeout --tool-timeout]` | 人 | bridges.json | 已实现（同上；2026-09-25 预算） |

## 七、未定动作区（挂名池，定义见 PENDING-DEFINITIONS）

速成模式视图 · 批量揭晓 · 扩展摘要 · 教师记忆消费端 · Obsidian 打包 ·
图形资产管理 · CLI 层 agent 准备 · cloze 拆卡（闪卡 spec 未来段） ·
leech（闪卡 spec 未来段） —— 均 `未定义挂名`。
冻结：Scoropic（ADR 0021）、插件生态。

## 变更留痕

- 2026-08-29 建图（v1 六域表）；同日 v2 分层化 + 新增权限列。
- 2026-08-29 讲解/诊断标记待退役（问卷 A1 彻底移除 + A3 explain 文件随清）。
- 2026-08-29 generate 桥登记升级意向：Agent 可直接触发 ingest、生成→校验→
  直接入正式池（无候选中间态）、候选组织并入校验环节、或更名 Check（队列④定）。
- 2026-08-29 目标编辑/删除标记缺口（API 已备、UI 无入口，队列③）。
- 2026-08-29 讲解/诊断已移除（remove-explain-diagnose，队列②落地）：任务机
  五模块、四条 API 路由、CLI `ai`、前端按钮与门槛逻辑全部退役；`bridge add`
  保留（对话 provider overrides 通道）。
- 2026-08-29 目标生命周期（编辑/删除）与目标表单助填动作落地（complete-goals-loop，队列③）；goals CLI 上线（22 命令）。
- 2026-08-29 Check 管线落地（introduce-check-pipeline，队列④）：定名 Check（专题 22）；
  三配方 apply 记批次 id+行戳记；`ingest rollback` + 桥 `check_ingest` 动作 +
  结果卡回滚按钮上线；candidate_problems 读路径退役（pull/mastery/hub 停读，
  表与 data candidate 子命令标**待退役**）。
- 2026-09-01 双向闪卡方向控件与扇形揭示落地（render-directional-flash-cards）。
- 2026-08-30 加固批次 #39–#52 合并（HTTP 边界 400/415/遍历修复、对话重启恢复、
  学习写入事务化、目标库原子写、API 整数校验、前端损坏状态恢复等）。
- 2026-08-30 出题链修复（conv-023 回归）：桥解析改为全区块按意图匹配；
  check_intent 正则补自然措辞；被忽略的动作区块向下一轮上下文披露
  「未写入任何内容」（openspec：disclose-ignored-action-blocks）。
  **（2026-09-23 已被 first-use-conversation-content-fidelity 取代：关键词意图门删除，
  合法的纯新增内容动作自动执行，见本文件末条。）**
- 2026-09-23 首次真实使用修缮（first-use-conversation-content-fidelity）：对话内容通道扩为
  `content-bundle`（知识点 / 正式题 / 微题 / 闪卡 / 图片同一原子批次；key 互相引用、
  服务端按课程与章分配 id、大清单暂存到本对话 jobs 目录、暂存路径越界即拒）；浏览器
  关键词意图门删除；图片按原始字节复制到 `.lessonkit/figures/{course}/{chapter}/`，
  缺必需图片整批零写入，回滚只删该批创建且无引用者；题目新增来源证据 / 来源答案 /
  解析来源三列，并在知识点页与练习卡显示；浏览器与服务端富文本统一支持 GFM 表格；
  Pi 改为每对话一个隐藏 `pi --mode rpc` 常驻进程（空闲 30 分钟回收、abort 优先、
  接受后崩溃不重放），全部 provider 子进程 Windows 无窗口。
- 2026-08-30 candidate 物理退役落地（remove-candidate-store）：`lesson-kit data` 的
  candidate 实体与 gate/promote 动作下线、候选证据分支删除、candidate_problems/
  candidate_attempts 建表停止且真实池 DROP（先备份）；learner_signals 保留为核心。
- 2026-08-31 目标月历升级为时间跑道：目标增加可选开始日期，跨周续接、重叠分轨；
  阶段/长期/逾期采用黄/蓝/红边缘区分，旧目标按截止日单点兼容。
- 2026-08-31 Agent 执行计划落地（render-agent-execution-plan）：Codex/Claude
  命令、工具、搜索与回答活动统一成可读步骤；同一步原位更新状态，成功轮次可恢复。
- 2026-09-17 Pi 接入 + 首版 CLI（introduce-pi-agent-and-cli）：provider 集合扩为
  codex/claude/pi，bridges.json 的 `command` 开始**优先于 PATH 探测**（本机存在
  两份 pi 与两个 npm 前缀，否则"用哪个"由 PATH 顺序决定）；流内错误（进程退出码
  为 0 但 provider 自报失败）纳入失败判定；新增第六节的服务生命周期六个动作
  （`daemon start|stop|status`、`dashboard`、`bridge list`、`bridge add --command`），
  CLI 顶层命令由 16 条增至 18 条。后台服务与
  「应用未打开时不运行」的旧记载之取舍见 ADR 0022。
- 2026-09-21 工作区文件隔离（workspace-file-isolation）：本表动作**不新增**，但
  三个动作的写入边界收紧——内容治理的 id 钉在本工作区课程前缀（外课 id 拒收）；
  对话轮次/会话读写只认 `conv-NNN`/`turn-NNN`（`%2F` 穿越被拒，删除只落在本区
  `.lessonkit/jobs/`）；开局 `init` 的池选择排除 ingest 备份、多池时要求
  `--course` 指名。合同见 review-workbench「Workspace file containment」与
  workbench-content-governance「Ingest stays inside one course」。
- 2026-09-21 dashboard 章透镜（dashboard-chapter-filter）：第一节新增「切换章透镜」
  一个动作（人面入口 = 顶栏开关，写注册表 `active_chapter`，与 CLI `use` 同源；
  关 = 全课程）；读侧受影响的是知识点页/图谱页/复习与练习建议的取数口径，
  hub 卡片四项统计改整课程口径（原 kps 按章）。章名单由池内容派生，无登记动作。
- 2026-09-25 轮次静默预算（bridge-timeouts-follow-progress）：**本表动作不新增**，
  但第六节两个动作扩了参数——`bridge add` 增加 `--tool-timeout`，`bridge list` 报告
  生效的两个预算；对话轮次的失败判据由「总时长」改为「静默」：任一输出行或归一
  事件重置时钟，命令/工具在飞时改用更长的工具预算，因此长回答与慢命令都不再被
  截停，真卡住时仍如实报 `provider timed out`。生效值经归一化（工具预算不低于静默
  预算，Pi 再压到 30 分钟 RPC 空闲窗以内，否则进程会被回收在轮次之下）。

- 2026-09-25 入库题型与契约对齐（ingest-mode-choice-and-contract-parity）：**本表动作不新增**。
  入库时可选题型：不给 `quiz_type`=综合题、`yes_no`=判断、`single_choice`/`multiple_choice`=小测；
  **客观题允许没有答案键**（判断题/单选题题源丢答案的常态）——无键题不判分、练习页写明「未录入
  答案键」并走 1–5 自评，批次计数与下一轮上下文报出未录键条数，答案键可用 `data update problem`
  事后补（空值清回无键，按该题 `quiz_type` 校验形状）；普通题声明小测/判断模式却不给 `quiz_type`
  即拒收并给修法。契约与代码对齐：内联清单照收（`kind`/`type` 都是 content-bundle）、章规则改为
  实话（该项 chapter → 清单顶层 chapter → 点名拒收，**不回退当前章**）、成功入库后的下一轮上下文
  明确要求「学生要求但尚未导入的章直接补齐，不必让学生再说一次『继续』」，并修掉单动作轮次重开时
  结果卡渲染两遍的重复。
- 2026-09-25 原地改题（in-place-problem-edits）：新增 problem-patch 动作与批量通道（见上表），单题入口 `data update problem` 扩到 `practice_modes`/整份 `micro_quiz`/来源三字段/`answer_key`；`data update` 对不认识的字段名不再静默丢弃、`data delete` 删不存在的题号不再假装成功；客观题题干上限 200→800 字。补丁回滚是写回旧值，学习记录与题号一起保住。
- 2026-09-26 取消客观题题干上限：真题里的长篇单选/多选（多断言、长情境、内联选项块）不再因长度被退回综合题，摄入门禁与 `problem-patch` 同步取消长度校验。
- 2026-09-29 内容身份去重与只读题库审计（content-dedup-and-audit）：同一课程内题干完整规范化后跨来源、跨章节去重；`data <ws> audit` 报告重复、片段、未标客观题、缺标题与图片问题；回滚 apply 后状态变动时先拒绝且不创建备份。
- 2026-09-29 记录中心 groundwork（records-center）：左侧「记录」扩为独立记录中心——概览（作答量 14 天趋势、
  正确率、1–5 自评分布实时聚合）、练习 / 试卷（`practice_runs` 最小快照：临时练习 / 试卷名 / Agent 练习）、
  作答明细（载入上限 500 条并如实提示截断）、错题（客观判错或卡住）；旧池迁移补 `practice_runs` 与
  `active_practice.source_label`，行数据零改动。
- 2026-09-26 做题记录 + 来源筛选 + 模型条目（attempt-records-filters-and-model-entries）：
  练习回路新增「来源筛选浮窗」，记录与调度新增两条（浏览器作答落库、做题记录视图），
  Agent 桥新增两条（模型条目配置、对话内切换模型）并修正「新建会话」的措辞（harness 锁定、
  模型可换）。三处渲染随之补齐：小测选项与判定行改走同一套安全富文本（选项里的 `$…$` 不再
  以原文示人），导出练习卷的 `$…$` 原样保留、需用支持数学的 Markdown 查看器打开。
- 2026-10-06 搜索与来源维度升级（problem-search-and-origin-filter）：搜索从「一个 haystack 一次子串」变成
  **两个关键词域**（题干/来源），各域空格多词 AND、跨域 AND，域定义只有一份并被搜索与选题共用；
  `origin_kind` 由单值升为第四个筛选维度（浮窗显示历年原题/改编/AI生成，CLI `--origin-kinds` 可重复）；
  旧 `?q=`、单值 `origin_kind`、旧浮窗存储键一律删除不兼容。
- 2026-10-10 作者内容镜像 v1（json-content-repository-sync，PR110）：第三节新增三条动作——
  `mirror init`（pool-first 引导、修订号 1、逐实体可恢复；既有同 id 文件按嵌入身份采纳；
  不可读文件进报告并阻断被其点名实体的建档、逐实体写失败不再中断整轮）、
  `mirror check/status`（零写入分类）、`mirror sync`（逐实体三方比较；仓库修改经既有
  内容/关系校验器写池，内容+状态+日志同一池事务；缺失文件按新修订恢复、删除请求只报告
  不执行、永不因仓库缺文件删池）。CLI 顶层命令增至 24；不执行 Git clone/pull/commit/push。
