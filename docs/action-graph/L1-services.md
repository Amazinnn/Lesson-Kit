# L1 · 服务层登记（域逻辑模块）

> 模块只经 L2 接口被调用，不直接暴露。依赖 = 主要触及的 L0 表。

| 模块 | 职责 | 依赖 | 被谁调用 |
|---|---|---|---|
| **拉取 pull** | 按选区 KP + 模式拉题：exclude 已见、到期优先、n 条、诚实空态 | problems、review_schedule | `/pull`（API/CLI）、练习页 |
| **拉取 pull-cards** | 闪卡按方向能力展开；选区过滤、每方向到期优先、整卡/方向键排除 | flash_cards、review_schedule | `/pull-cards`、练习页 |
| **feedback 四件套** | 一次自评原子写四件事：事件→信号→状态→调度；支持 item_type=problem/card + direction 键 | feedback_events、learner_signals、kp 状态、review_schedule | `/feedback`（API/CLI）、收束页 |
| **practice 记录** | 记一次尝试（作答原文/卡点/状态） | problem_attempts | `/practice`（API/CLI） |
| **内容批次 content-bundle**（2026-09-23） | 一份清单同时含知识点/正式题/微题/闪卡/必需原图：整批预检（引用、契约、来源证据、图片字节、目标冲突）→一份备份→单事务 apply→一个批次 id；条数无上限；任一条不合法或缺图即整批零写入；图片按原始字节落 `.lessonkit/figures/{course}/{chapter}/` | knowledge_points、problems、flash_cards、figures | 桥内容动作、CLI `ingest` |
| **门禁配方 micro-quiz** | manifest（micro-quiz-patch）确定性校验→备份→单事务 apply；重复 id 拒收；**id 前缀必须等于本工作区课程**；**难度可选（1-5 + 依据同现，依据不落盘）**（2026-09-21；2026-09-23 起为兼容通道，推荐 content-bundle） | problems | CLI `ingest recipe` |
| **门禁配方 flash-card** | flash-card-patch：内容契约/正则 id/来源必填/directions 两种合法值；**id 前缀必须等于本工作区课程**（2026-09-21） | flash_cards | CLI `ingest recipe` |
| **批次溯源与整批回滚** | apply 记批次 id（batch-NNN）+行戳记+manifest 快照+ingest_batches 登记；rollback 按批次删行（有练习/反馈依赖即拒绝），回滚前自动备份；content-bundle 批次同时删除本批创建且已无引用的图片文件（仍被引用的保留） | ingest_batches、problems、flash_cards、knowledge_points、figures | CLI `ingest rollback`、`POST /ingest/rollback`、桥结果卡、`GET /ingest/batches` |
| **ingest 链** | prepare/run/gate/apply/render 六环节编排与中间产物 | 中间产物目录 | CLI `ingest` 家族 |
| **对话 conversations** | provider 原生会话的建立/轮次/事件流/取消/最小镜像；失败原因含进程退出码、超时、取消与**流内错误**（provider 退出码为 0 也算失败）；会话/轮次 id 只认 `conv-NNN`/`turn-NNN`，越界拼路径直接拒绝（2026-09-21）；**Pi 走每对话一个隐藏 `--mode rpc` 常驻进程**（空闲 30 分钟回收、abort 优先、接受后崩溃不重放），Codex/Claude 仍每轮一进程，全部子进程 Windows 无窗口（2026-09-23） | jobs/conv-### | `/ai/sessions/*` |
| **provider 发现/配置** | 单一发现口径：先取 bridges.json 为该 provider 配置的 `command`，否则退回 PATH 探测；配置另可覆盖 args / model / timeout | bridges.json | `/ai/providers`、CLI `bridge add`/`bridge list` |
| **后台服务 service** | 工作台服务的 pid 记录、分离启动、终止与存活探测；`start` 只在端口应答后报成功，`stop` 拒绝终止已被回收的进程号 | `~/.lessonkit-workbench/daemon.json`、`daemon.log` | CLI `daemon start\|stop\|status`、`dashboard` |
| **查询 queries** | hub 统计（四项整课程口径）/due 列表/图谱模型/kp 详情/review 概览（标签全长）；章透镜下的取数走 `Pool.scope_prefix()` | 全表只读 | 多个 GET API |
| **计划 planning** | 每日建议（≤3 条人话）+ 失败保留上次结果 | 全表只读 + plan.json | `/plan`、建议区 |

> `bridge/` 现存两个模块：`conversation_providers.py`（发现 + 命令构建 + 事件归一化）
> 与 `conversations.py`（轮次生命周期）。旧的 runner/contracts/teacher 三件套与
> `lesson-kit ai` 子命令、`GET /ai/task-providers` 门槛端点已于 remove-explain-diagnose 退役。
>
> `registry.py`（工作区注册表）不属上表任何服务，是 Shell 与 Data 之间的身份层：
> 一个名字 → 一个文件夹、一个池、一个激活课程/章，且**注册时校验池在工作区内、
> 路径与池不重复、同名冲突不覆盖**（2026-09-21 workspace-file-isolation）。
