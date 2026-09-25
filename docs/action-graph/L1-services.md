# L1 · 服务层登记（域逻辑模块）

> 模块只经 L2 接口被调用，不直接暴露。依赖 = 主要触及的 L0 表。

| 模块 | 职责 | 依赖 | 被谁调用 |
|---|---|---|---|
| **拉取 pull** | 按选区 KP + 模式拉题：exclude 已见、到期优先、n 条、诚实空态 | problems、review_schedule | `/pull`（API/CLI）、练习页 |
| **选题组练习**（2026-09-25） | 六种方式组合：范围/单题追加/条件筛选（含 `exam_year` 前缀）/薄弱（`weak` 薄弱分）/到期/错题（进度或最近尝试为错）；每题回报 reason，缺口进 shortage，零写入；练习清单校验与出卷（两份 Markdown 纯规则渲染 + 泄漏扫描） | problems、problem_progress、problem_attempts、review_schedule、learner_signals | CLI `pull`（含 `--plan`/`--print`/`--check`） |
| **拉取 pull-cards** | 闪卡按方向能力展开；选区过滤、每方向到期优先、整卡/方向键排除 | flash_cards、review_schedule | `/pull-cards`、练习页 |
| **feedback 四件套** | 一次自评原子写四件事：事件→信号→状态→调度；支持 item_type=problem/card + direction 键 | feedback_events、learner_signals、kp 状态、review_schedule | `/feedback`（API/CLI）、收束页 |
| **practice 记录** | 记一次尝试（作答原文/卡点/状态） | problem_attempts | `/practice`（API/CLI） |
| **attempts 代录与更正**（2026-09-24） | 尝试清单校验（字段白名单、题目存在、评分 1–5、题内不重复）→ check 零写入预检 → apply 单事务写尝试 + 复用 feedback 四件套（带评分时）+ 操作留痕（含 effect 前后投影快照）；同 `request_id` 同内容幂等回放、异内容拒绝；correct 按 attempt-id 整体替换：先比对快照（投影被更晚活动改过、或还有更晚尝试即拒），再恢复前快照、按新评分重算、更新快照；无评分的尝试不碰任何投影 | problem_attempts、feedback_events、attempt_operations、learner_signals、learning_current_state、problem_progress、review_schedule | CLI `attempts`（check/apply/correct/list/get） |
| **答卷目录 sources**（2026-09-24） | 每工作区一份只读目录清单（可位于工作区之外）；只存目录路径，不复制图片、不建索引 | answer-sources.json | CLI `attempts sources add/list/remove` |
| **内容批次 content-bundle**（2026-09-23；2026-09-25 起可跨章） | 一份清单同时含知识点/正式题/微题/闪卡/必需原图：整批预检（引用、契约、来源证据、图片字节、目标冲突）→一份备份→单事务 apply→**按章各一个批次 id**；条数无上限、章数无上限；每项可声明自己的 `chapter`（缺省顶层；推不出章即点名拒收，**不回退当前章**），发号/图片目录/重复检查都跟随该项的章；内联清单照收（`kind` 或 `type` 写 `content-bundle`）；任一条不合法或缺图即整批零写入；图片按原始字节落对应章的 `.lessonkit/figures/{course}/{chapter}/`。**题型在入库时可选**：不给 `quiz_type`=综合题，`yes_no`=判断，`single_choice`/`multiple_choice`=小测；**客观题允许无答案键**（不判分、计入 `keyless` 计数并披露，可事后用 `data update problem` 补键）；普通题声明小测/判断模式而不给 `quiz_type` 即拒收并给修法 | knowledge_points、problems、flash_cards、figures | 桥内容动作、CLI `ingest` |
| **门禁配方 micro-quiz** | manifest（micro-quiz-patch）确定性校验→备份→单事务 apply；重复 id 拒收；**id 前缀必须等于本工作区课程**；**难度可选（1-5 + 依据同现，依据不落盘）**（2026-09-21；2026-09-23 起为兼容通道，推荐 content-bundle） | problems | CLI `ingest recipe` |
| **门禁配方 flash-card** | flash-card-patch：内容契约/正则 id/来源必填/directions 两种合法值；**id 前缀必须等于本工作区课程**（2026-09-21） | flash_cards | CLI `ingest recipe` |
| **原地改题 problem-patch**（2026-09-25） | 只改**已有**题目，不插入、不换题号：单题走 `data update problem`，批量走 `problem-patch` 清单（一次预检→一份备份→一个事务→逐条报错→批次号 + **每行改前旧值**快照）；可改描述字段、`practice_modes`、整份 `micro_quiz`、来源三字段与 `answer_key`；改不了题号，难度仍走 `difficulty`，未知字段名报错；回滚是**写回旧值**（不删行），学习记录与题号一起保住 | problems | CLI `data update problem`、CLI `ingest recipe problem-patch`、桥 problem-patch 动作 |
| **批次溯源与整批回滚** | apply 记批次 id（batch-NNN）+行戳记+manifest 快照+ingest_batches 登记；rollback 按批次删行（有练习/反馈依赖即拒绝），回滚前自动备份；content-bundle 批次同时删除本批创建且已无引用的图片文件（仍被引用的保留） | ingest_batches、problems、flash_cards、knowledge_points、figures | CLI `ingest rollback`、`POST /ingest/rollback`、桥结果卡、`GET /ingest/batches` |
| **ingest 链** | prepare/run/gate/apply/render 六环节编排与中间产物 | 中间产物目录 | CLI `ingest` 家族 |
| **对话 conversations** | provider 原生会话的建立/轮次/事件流/取消/最小镜像；失败原因含进程退出码、超时、取消与**流内错误**（provider 退出码为 0 也算失败）；会话/轮次 id 只认 `conv-NNN`/`turn-NNN`，越界拼路径直接拒绝（2026-09-21）；**Pi 走每对话一个隐藏 `--mode rpc` 常驻进程**（空闲 30 分钟回收、abort 优先、接受后崩溃不重放），Codex/Claude 仍每轮一进程，全部子进程 Windows 无窗口（2026-09-23）；**轮次预算是静默预算**（输出行/事件重置时钟、命令在飞时用更长的工具预算），只截停真正静默的轮次（2026-09-25） | jobs/conv-### | `/ai/sessions/*` |
| **provider 发现/配置** | 单一发现口径：先取 bridges.json 为该 provider 配置的 `command`，否则退回 PATH 探测；配置另可覆盖 args / model / 两个轮次预算（`timeout_s` 静默、`tool_timeout_s` 工具在飞），生效值经归一化（工具预算不低于静默预算，Pi 再压到 RPC 空闲窗以内） | bridges.json | `/ai/providers`、CLI `bridge add`/`bridge list` |
| **后台服务 service** | 工作台服务的 pid 记录、分离启动、终止与存活探测；`start` 只在端口应答后报成功，`stop` 拒绝终止已被回收的进程号 | `~/.lessonkit-workbench/daemon.json`、`daemon.log` | CLI `daemon start\|stop\|status`、`dashboard` |
| **查询 queries** | hub 统计（四项整课程口径）/due 列表/图谱模型/kp 详情/review 概览（标签全长）；章透镜下的取数走 `Pool.scope_prefix()` | 全表只读 | 多个 GET API |
| **计划 planning** | 每日建议（≤3 条人话）+ 失败保留上次结果 | 全表只读 + plan.json | `/plan`、建议区 |

> `bridge/` 现存两个模块：`conversation_providers.py`（发现 + 命令构建 + 事件归一化）
> 与 `conversations.py`（轮次生命周期）。旧的 runner/contracts/teacher 三件套与
> `lesson-kit ai` 子命令、`GET /ai/task-providers` 门槛端点已于 remove-explain-diagnose 退役。
>
> `surface.py`（接口归属表）不是服务，是登记：每条路由/命令的受众，由测试与真实
> parser、ROUTES 对账（2026-09-25）。
>
> `registry.py`（工作区注册表）不属上表任何服务，是 Shell 与 Data 之间的身份层：
> 一个名字 → 一个文件夹、一个池、一个激活课程/章，且**注册时校验池在工作区内、
> 路径与池不重复、同名冲突不覆盖**（2026-09-21 workspace-file-isolation）。
