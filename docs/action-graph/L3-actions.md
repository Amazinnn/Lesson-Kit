# L3 · 动作层登记（人 / Agent 可执行的动作）

## 工作区布局迁移（2026-10-21）

人通过 `workspace <name> migrate-layout` 预览，通过 `--apply` 显式应用：仅收纳已确认的内部目录，不清理内容、不改变学习事实。新建课程直接采用隐藏布局；未迁移课程保持兼容。迁移前须停止访问该课程的服务与活动轮次；冲突拒绝，不合并目标。

> 权限列按 2026-08-29 问卷 B1 口径：**人** = 界面操作；**Agent** = 可经 CLI/对话直接执行；**双** = 两边都有入口。
> 状态：`已实现 / 已定义未实现 / 未定义挂名 / 冻结 / 待退役`。

## 一、练习回路

Paper 操作补充（2026-10-19）：练习页只管理既有 Paper，不提供学习者选题、组卷条件、数量、成员或题序编辑。切卷暂停/恢复各自的游标和草稿；新一轮选择答案展示方式，继续轮次恢复原设置。Agent 使用 `papers list/get/preview/update/delete` 管理显式 ID；更新预览与确认保留既有治理边界。删除 Paper 保留题目，删除题目清当前引用但保留其他 Paper 进度和历史证据。重复的 AI 解析展示退役，正常解析和来源数据保留。

| 动作 | 入口 | 权限 | 写 | 状态 |
|---|---|---|---|---|
| 切换章透镜（关 = 全课程；开着时选一章） | UI 顶栏「章」开关 | 人 | 注册表 `active_chapter`（与 `use` 同源） | 已实现（dashboard-chapter-filter；只影响阅读） |
| 查看、改名、导出或删除既有 Paper | UI「试卷」页 | 人 | 改名/容器删除；不改题目成员与顺序 | 已实现；删除不删题目或学习证据 |
| 开始或继续既有 Paper | UI「试卷」页 | 人 | 该 Paper 的 active checkpoint | 已实现；继续恢复独立进度 |
| 选择答案展示方式 | UI 开始 Paper 时 | 人 | `reveal_timing`：`per_item` 或 `on_submit`，随轮次持久化 | 已实现（free-navigation-paper-practice） |
| Paper 自由导航（上一题/下一题/题号点；首尾不循环） | UI 练习页 | 人 | 当前题位置与未提交草稿；不提交、不判定、不锁题 | 已实现；可访问未答、已答及「不会」题 |
| 逐题提交普通 Paper 答案 | UI 练习页 | 人 | 原子写 Attempt；成功后锁题并展示可用结果/参考材料 | 已实现；单选/判断自动提交，多选/文字显式提交 |
| 标记「不会」并查看参考材料 | UI 练习页 | 人 | `per_item` 立即写卡点 Attempt 并锁题；`on_submit` 保存可改的 `stuck` 草稿 | 已实现；修改答案可清除卡点标记，保留 `reference_viewed` 事实 |
| 显式提交普通 Paper | UI 练习页 | 人 | 保存未提交且未标记不会的答案；空白或仍标记不会的题作为卡点 Attempt；锁定并归档 Practice Run | 已实现；到达末题、导航和暂停均不自动提交 |
| 完成页查看答卷并返回 | 完成页 / 答卷页 | 人 | —（只读；返回不重复提交） | 已实现 |
| 再练一次 | 完成页 | 人 | 新 Practice Run；保留原完成轮次 | 已实现 |
| 普通 Paper 可选自评 1–5 | UI 练习页 / 完成答卷 | 人 | 按已提交 Attempt 写或更新关联 feedback | 已实现；可跳过，不阻止交卷 |
| 按来源证据筛题（`--source-evidence` 子串、可重复；与 `--source-kind`/`--origin-kinds`/`--exam-year` 同为「维度内 OR、维度间 AND」） | Agent/CLI `pull` | Agent | —（只读选择） | 已实现（2026-09-26） |
| 按题目来源方式筛题（`--origin-kinds` 可重复：历年原题/改编/AI生成，取并集） | Agent/CLI `pull` | Agent | —（只读选择） | 已实现（2026-10-06） |
| 按题干/来源关键词筛题（`--search-stem`/`--search-source`，空格多词、域内 AND、跨域 AND） | Agent/CLI `pull` | Agent | —（只读选择） | 已实现（2026-10-06） |
| 落练习清单（可重跑，零写入读取） | CLI `pull --plan` / `--input` | Agent | 练习清单 JSON（非池数据） | 已实现（2026-09-25） |
| 出练习集两份 Markdown（学生卷无答案/无内部标识，解答卷题号对齐、缺解「待补」） | CLI `pull --print` | Agent | `output/…-problem-set.md` + `-solutions.md` | 已实现（2026-09-25） |
| 练习集零写入预检（题数/缺口/缺解/重复/泄漏） | CLI `pull --check` | Agent | — | 已实现（2026-09-25） |
| 保存练习集为 Paper（保留题目顺序与 request） | CLI `lesson-kit papers <workspace> save --input <manifest>` | Agent（明确 authoring 请求） | `.lessonkit/practice-sets/ps-NNN.json`（现有原子写入器；不写 SQLite/学习状态） | 已实现（agent-save-reusable-papers, 2026-10-14） |
| 闪卡揭示、方向偏好与 ⇄ 交换 | UI | 人 | 牌组方向与视图态 | 既有语义保留 |
| 兼容自评时机设置（immediate/batch/off） | 旧练习/闪卡路径 | 人 | 既有浏览器偏好与旧反馈语义 | 旧记录兼容；不决定普通 Paper 的展示/锁定 |
| 闪卡回翻（上一张/下一张，在本轮固定卡片间移动；末尾不追加） | UI | 人 | 牌组游标 | 已实现；闪卡沿用既有揭示与自评语义 |
| 刷新或切换 Paper 后恢复（游标、草稿、展示时机） | 被动 / UI「试卷」页 | 人 | 独立 Paper checkpoint | 已实现 |
| 切换图谱指标投影（大小/色谱/气泡式过渡） | UI | 人 | — | 已实现（只读、内存） |
| 图谱多状态筛选与分群 | UI | 人 | — | 已实现（只读、内存） |
| 练习页发消息附页面锚点与近期练习工作集（可见正式题 + 同一练习最多四道前序已结算正式题；明确相对指代才改轮次焦点；显式附带的未提交作答/选项/备注/可见图片由服务端限长并只保存在本轮上下文快照，不写 Pool；成功 transcript 仍只保留既有 `context_anchor` 元数据） | UI 对话 | 人 | 上下文读取不写池、不移动游标；快照供同标识核对；显式重试创建新关联轮次，后续普通轮次不自动继承原草稿 | 已实现（2026-09-24；Agent focus 2026-10-12；preserve-agent-messages-and-tool-outcomes） |

## 二、记录与调度

| 动作 | 入口 | 权限 | 写 | 状态 |
|---|---|---|---|---|
| feedback 四件套 | API/CLI | 双 | 事件/信号/状态/调度（可带 `attempt_id` 链回那次作答） | 已实现 |
| 浏览器作答落库（服务端接受提交后写入，判定/选项同存；不碰信号·状态·进度·调度） | API `POST /attempts` / UI 提交 | 双 | attempts（status `answered`） | 已实现（2026-09-26） |
| 记录中心（概览/练习·试卷/作答明细/错题四视图；按题过滤；练习页「历史作答」折叠段） | UI / API `GET /records` | 浏（CLI 侧为 `attempts list`） | —（只读） | 已实现（2026-09-26 建，2026-09-29 扩为记录中心） |
| practice 尝试记录（CLI 与页面同一事务、同一存在性校验） | API/CLI | 双 | attempts + progress + schedule（单事务） | 已实现（2026-09-25 对齐） |
| 闪卡反馈与方向（CLI 补齐 card/direction） | API/CLI | 双 | 四件套（含方向调度键） | 已实现（2026-09-25 对齐） |
| 目标变更失效每日计划缓存（CLI 与 API 同一 helper） | API/CLI | 双 | plan.json（删除） | 已实现（2026-09-25 对齐） |
| 读命令 JSON 形态（人读默认不变） | CLI `weak`/`due`/`ls --json` | Agent | — | 已实现（2026-09-25） |
| Agent 代录尝试（转录 + 可选 1–5，可一次多题） | CLI `attempts apply` | Agent（学生明确要求） | attempts +（带评分时）事件/信号/状态/进度/调度 + `attempt_operations` 留痕 | 已实现（agent-assisted-practice-records） |
| 尝试清单预检（零写入） | CLI `attempts check` | Agent | — | 已实现（同上） |
| 指定尝试更正（撤回旧评分后重算；有更晚活动即零写入拒绝） | CLI `attempts correct <attempt-id>` | Agent（学生明确要求） | attempts 原文/评语/状态 + 事件/信号/状态/进度/调度 + 快照更新 | 已实现（同上） |
| 尝试与操作留痕读取 | CLI `attempts list\|get` | Agent | — | 已实现（同上） |
| 按知识点读取学习证据（有界近期作答 + 可读题面，不推断学习特征） | CLI `lesson-kit evidence <workspace> kp <kp-id> [--limit N]` | Agent | —（只读） | 已实现（agent-learning-evidence） |
| 答卷目录登记（只存路径，不复制图片） | CLI `attempts sources add\|list\|remove` | Agent | `answer-sources.json` | 已实现（同上） |
| 图谱状态显式编辑（不记反馈） | UI | 人 | 状态+调度 | 已实现 |
| 图谱关系绘制与 viewport/label LOD（WebGL2 单一路径；启动失败停止本次运行；可选本地布局种子不改图谱事实） | UI | 系统 | 浏览器可选布局缓存；不写 Pool | 已实现（graph-relation-pipes；graph-lod-layout-seeds） |
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
| 作者内容镜像同步（逐实体三方比较：仓库修改经既有内容/关系校验器写池；逻辑图像引用先按现有路径规则预检，题目难度经 `data.difficulty.check` 规范化；内容+状态+日志同事务；池修改导出下一修订；旧投影按下一修订升级；收敛恢复；冲突/无效逐条报告、成功兄弟保留；删除请求只校验报告、永不执行；不碰 Git 网络） | CLI `mirror sync --repo [--entity] [--dry-run]` | Agent | 池内容（经 `data.content`/关系校验器/难度校验）+ checkout JSON + 台账 | 已实现（字段扩展：expand-content-mirror-fields/PR123） |
| 图像文件投影（仅池中已引用路径；显式 check/push/pull；64-hex 旧身份冲突或缺少 pull 基线时拒绝；根/目标/索引均受工作区或 checkout 锚定；push 写派生归属索引；不修剪、不碰 Git 网络） | CLI `mirror <workspace> figures --repo <checkout> --direction check|push|pull [--dry-run]` | Agent | 工作区/checkout 图像文件 + checkout `figures/<course>/_index.json`；池只读 | 已实现（2026-10-12/13，versioned-figure-assets/PR113） |

## 四、Agent 桥

| 动作 | 入口 | 权限 | 写 | 状态 |
|---|---|---|---|---|
| 对话轮次（自动带页面上下文；接收前持久化用户消息与上下文；可选 `submission_id` 同内容幂等返回原轮次，变更内容冲突；失败/取消也保留用户消息、真实状态和实际部分回答；旧成功镜像只显示一次） | UI/CLI | 双 | conv turn artifacts + 成功 transcript | 已实现（preserve-agent-messages-and-tool-outcomes） |
| 运行中发送（默认排队；中断消息独立停止交接，不入普通队列，保留活动轮次与提交上下文） | Agent composer / `POST /turns` | 人 | 现有 turn artifacts；中断绑定捕获的活动轮次 | 已实现（queue-agent-messages-and-interrupt） |
| 重排待发消息（拖动或键盘，完整顺序 CAS） | Composer / `POST /queue/reorder` | 人 | conversation.queue_order；消息身份、文字和上下文不变 | 已实现（compact-agent-queue-and-direct-interrupt） |
| 立即发送原待发消息（独立停止交接，不新增提交） | Pending row / `POST /turns/{turn}/interrupt` | 人 | 原 turn 路由及队列顺序；保留身份、当前文字与原上下文，其他消息暂停 | 已实现（compact-agent-queue-and-direct-interrupt） |
| 编辑/移除待处理消息并显式继续暂停队列 | Pending controls / `PATCH`·`DELETE /turns/{turn}` / `POST /queue/continue` | 人 | 现有 turn/conversation JSON；移除保留 cancelled 记录 | 已实现（queue-agent-messages-and-interrupt） |
| 批准/取消 Agent 提议的既有 Paper 更新（显示当前与拟议题序及进度/草稿影响；过期预览刷新后须重新点击） | Paper approval card / `POST /paper-approval` | 人 | 仅批准时更新目标 Paper，并清除受影响的未完成进度/草稿；取消零写入，历史作答与其他 Paper 保留 | 已实现（complete-agent-message-lifecycle） |
| 设置运行中发送默认动作 | 工作区浏览器设置 | 人 | `runningSendAction`；只影响后续提交 | 已实现（queue-agent-messages-and-interrupt） |
| 恢复未确认或被拒绝的 Agent 消息（本地发送箱；核对时复用原提交标识/内容；不覆盖新草稿） | UI 对话流 | 人 | 浏览器 localStorage + 原 turn | 已实现（preserve-agent-messages-and-tool-outcomes） |
| 显式重试已接收的失败轮次（新 turn 通过 `retry_of` 关联原消息；不自动重放） | UI 对话流 | 人 | 新 turn artifact | 已实现（preserve-agent-messages-and-tool-outcomes） |
| 收起 Agent 辅助工作面（本轮记住收起状态） | Activity Float / Bottom Dock / Artifact Split 折叠控件 | 人 | 当前浏览器对话轮次内存状态 | 已定义未实现（PR135 已有展示基础；运行状态映射见 PR136） |
| 执行计划与工具结果卡（命令/工具/搜索/回答活动归一化；错误为终态失败；仅展示有证据的影响，否则未知；折叠脱敏诊断；不展示不支持的单步重试） | UI 对话流 | 双 | conv 活动记录 | 已实现（preserve-agent-messages-and-tool-outcomes；render-agent-execution-plan） |
| 新建会话/选 provider（harness 锁定不换） | UI | 人 | conversations | 已实现 |
| 模型条目配置（显示名自定、与 harness 解耦；无条目时回退「一 harness 一条」） | CLI `bridge add-model` | 人 | bridges.json `models` | 已实现（2026-09-26） |
| 对话内切换模型（头部下拉；丢弃缓存进程、下一轮生效；运行中 409；跨模型续接失败则开新会话并写明） | UI / API `PATCH /ai/sessions/{id}` | 人 | conversations `model` | 已实现（2026-09-26） |
| 停止轮次 | UI | 人 | turn=cancelled | 已实现 |
| replace_practice_selection（明确练习意图才生效；只替换组卷 Paper Scope，不组卷或开始 Practice Run） | 对话产出动作 | Agent | 练习 Scope | 已实现 |
| paper_artifact（保存成功后的 Paper 工件卡：只按已保存 ps-NNN 记录展示标题/题数，不含 URL、零写入；打开试卷页是显式动作） | 对话产出动作 | Agent | —（只读已保存 Paper 记录） | 已实现（2026-10-16 PR137） |
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

- 2026-10-18 Agent 消息队列与中断后发送（queue-agent-messages-and-interrupt）：运行中接受 FIFO 消息或显式中断；中断等待捕获轮次终态和 worker 清理，旧队列在失败、恢复及优先消息完成后保持暂停。待处理消息可按 revision 编辑/移除，并可显式继续。无 Pool 字段。
- 2026-10-12 普通题上一题结果回看（practice-review）：登记只读回看入口、返回时保留当前草稿、Agent 焦点跟随可见题，以及不移动游标/不写尝试或反馈；闪卡上一张/下一张仍保留游标导航。
- 2026-10-17 Paper 作答回看与自评编辑（revisit-paper-answers-and-edit-self-rating）：同一 Paper execution 内所有已提交/不会普通题可反复回看，参考答案默认收起；自评仅在再次保存时覆盖确切 Attempt 关联评分/评语，不追加记录、不重放学习影响。闪卡和无服务端执行身份的旧行为保留。
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
- 2026-10-06 搜索与来源维度升级（problem-search-and-origin-filter；历史记录：其中浏览器浮窗关键词选题已于 2026-10-16 随 PR130 退役）：搜索从「一个 haystack 一次子串」变成
  **两个关键词域**（题干/来源），各域空格多词 AND、跨域 AND，域定义只有一份并被搜索与选题共用；
  `origin_kind` 由单值升为第四个筛选维度（浮窗显示历年原题/改编/AI生成，CLI `--origin-kinds` 可重复）；
  旧 `?q=`、单值 `origin_kind`、旧浮窗存储键一律删除不兼容。
- 2026-10-10 作者内容镜像 v1（json-content-repository-sync，PR110）：第三节新增三条动作——
  `mirror init`（pool-first 引导、修订号 1、逐实体可恢复；既有同 id 文件按嵌入身份采纳；
  不可读文件进报告并阻断被其点名实体的建档、逐实体写失败不再中断整轮）、
  `mirror check/status`（零写入分类）、`mirror sync`（逐实体三方比较；仓库修改经既有
  内容/关系校验器写池，内容+状态+日志同一池事务；缺失文件按新修订恢复、删除请求只报告
  不执行、永不因仓库缺文件删池）。CLI 顶层命令增至 24；不执行 Git clone/pull/commit/push。

2026-10-20 新增/改级（compact-agent-queue-and-direct-interrupt）：输入区拖动或键盘重排待发消息（人 → 薄 API → Bridge，读写 queue_order）；排队行立即发送（人 → 薄 API → Bridge，复用原 turn 并停止交接）；中断后发送从队列优先项改为独立交接。编辑/删除/继续保持原责任层级。待审批或另一停止交接时拒绝立即发送，恢复原文不覆盖草稿。
