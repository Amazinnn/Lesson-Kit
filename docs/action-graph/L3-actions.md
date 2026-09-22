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
| 作答+本地判分（横幅 2s+高亮） | UI | 人 | 牌组（不写库） | 已实现 |
| 揭示（卡背/解析） | UI | 人 | 牌组 | 已实现 |
| 闪卡方向偏好与 ⇄ 交换 | UI | 人 | 牌组方向 | 已实现 |
| 闪卡回翻（上一张/下一张，末尾拉新） | UI | 人 | 牌组游标 | 已实现 |
| 即时自评 1–5 | UI | 人 | 四件套 | 已实现 |
| 跳到下一道（已答/已玩不降级） | UI | 人 | 牌组 state | 已实现 |
| 提前结束→收束页统一评分 | UI | 人 | 四件套×未评 | 已实现 |
| 再练同类 | UI 收束页 | 人 | 新 session | 已实现 |
| 刷新恢复（游标+视图态） | 被动 | 人 | — | 已实现 |
| 切换图谱指标投影（大小/色谱/气泡式过渡） | UI | 人 | — | 已实现（只读、内存） |
| 图谱多状态筛选与分群 | UI | 人 | — | 已实现（只读、内存） |

## 二、记录与调度

| 动作 | 入口 | 权限 | 写 | 状态 |
|---|---|---|---|---|
| feedback 四件套 | API/CLI | 双 | 事件/信号/状态/调度 | 已实现 |
| practice 尝试记录 | API/CLI | 双 | attempts | 已实现 |
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

## 四、Agent 桥

| 动作 | 入口 | 权限 | 写 | 状态 |
|---|---|---|---|---|
| 对话轮次（自动带页面上下文） | UI/CLI | 双 | conv 留痕 | 已实现 |
| 执行计划（命令/工具/搜索/回答活动归一化，同行状态更新，成功轮次可恢复） | UI 对话流 | 双 | conv 成功留痕 | 已实现（render-agent-execution-plan） |
| 新建会话/选 provider（锁定不换） | UI | 人 | conversations | 已实现 |
| 停止轮次 | UI | 人 | turn=cancelled | 已实现 |
| replace_practice_selection（明确练习意图才生效） | 对话产出动作 | Agent | 浏览器选区（一次性） | 已实现 |
| content-bundle（内容批次：合法的纯新增动作自动执行，无关键词意图门；大清单暂存本对话 jobs 后由区块引用→整批预检→一份备份→单事务 apply→一个批次 id；失败逐条显式回对话流、零写入） | 对话产出动作 | Agent | 池内容 + `.lessonkit/figures/{course}/{chapter}/`（经门禁+批次标记） | 已实现（first-use-conversation-content-fidelity，2026-09-23 取代 check_ingest 的关键词门与内联清单） |
| 整批回滚（结果卡按钮，与 CLI 同源 rollback） | UI 结果卡 | 人 | 池内容（按批次删行） | 已实现（introduce-check-pipeline） |

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
| provider 解析清单（可执行文件、来源 config/path、路径是否缺失） | CLI `bridge list` | 人 | —（只读） | 已实现（同上） |
| 显式钉死 provider 可执行文件（优先于 PATH 探测） | CLI `bridge add --command` | 人 | bridges.json | 已实现（同上） |

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
