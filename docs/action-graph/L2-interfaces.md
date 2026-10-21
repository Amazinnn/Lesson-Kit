# L2 · 接口层登记（API 路由 + CLI 命令）

> 「给谁」：**浏** = 浏览器工作台专用；**CLI** = 外部 Agent/终端；**双** = 两者；**只读 API** = 可供查询，不是浏览器选题入口。

## API 路由（`/api/w/{ws}` 前缀，62 条）

| 方法 路径 | 读写 | 服务层 | 给谁 |
|---|---|---|---|
| GET `/hub/workspaces` | 读 | 查询 | 浏 |
| GET `/weak` | 读 | 查询 | 双 |
| POST `/chapter` | 写 | 注册表（顶栏章透镜；空串 = 全课程，与 `use` 同源） | 浏 |
| GET `/due` | 读 | 查询 | 双 |
| GET `/calendar` | 读 | 查询 | 浏 |
| GET `/plan` · POST `/plan/recalculate` | 读/写 | 计划 | 浏 |
| GET·POST `/goals`；PATCH·DELETE·GET `/goals/{id}` | 读/写 | goals.json | 浏（UI 仅用创建） |
| GET `/practice-sets` | 读 | 已保存 Paper 列表与独立进度 | 浏览器；Agent `papers list` |
| POST `/practice-sets` | 写 | 保存 Agent/CLI authoring 产出的 Paper，使用现有 Data 写入器 | Agent/CLI |
| GET `/practice-sets/{practice_set_id}` | 读 | 显式 Paper 详情与不可用题目引用 | 浏览器预览；Agent `papers get` |
| PATCH `/practice-sets/{practice_set_id}` | 写 | 浏览器可直接改标题；结构性成员/顺序更新仍经有影响预览与确认的 Agent 审批 | 浏览器改标题；Agent/CLI + 审批流程改结构 |
| DELETE `/practice-sets/{practice_set_id}` | 写 | 删除 Paper 容器和未完成状态，不删题目与学习证据 | 浏览器；Agent `papers delete` |
| GET `/practice-sets/{practice_set_id}/render` | 读 | 已保存 Paper 题面与导出渲染 | 浏览器 |
| POST `/practice-sets/{practice_set_id}/start` | 写 | 开始或继续既有 Paper；恢复该卷独立进度 | 浏览器 |
| POST `/practice-sets/{practice_set_id}/preview` | 读 | 预览 Agent 更新与其进度影响 | 浏览器审批流程；Agent `papers preview` |
| POST `/pull` | 读 | Agent/CLI authoring 拉取（`filters` 四维：来源类型/题目来源方式/年份/文档，维度内 OR、维度间 AND；顶层 `origin_kinds` 同义） | Agent/CLI；无学习者选题页 |
| GET `/pull-facets` | 读 | 兼容筛选维度与计数查询；浏览器不再呈现来源筛选浮窗 | 只读 API |
| GET `/search/problems?stem=&source=` | 读 | 只读题目发现（题干/来源域多词 AND）；不接入浏览器选题或 Paper 组装，精确题号仍由 Agent/CLI `pull --problem` 在组卷前指定 | 只读 API |
| POST `/pull-cards` | 读 | 拉卡（direction_mode + 独立方向排除） | 双 |
| POST `/practice` | 写 | practice 记录 | 双 |
| POST `/attempts` | 写 | 尝试（浏览器每次提交落一条：作答+选项+判定，不碰进度与调度） | 双 |
| POST `/practice/current/navigate` | 写 | 保存 Paper 内任意题目导航位置与草稿，不提交 | 浏览器 |
| POST `/practice/current/stuck` | 写 | `per_item` 立即写卡点 Attempt 并锁题；`on_submit` 更新可改草稿；两种方式均披露可用参考材料 | 浏览器 |
| POST `/practice/current/submit` | 写 | 显式提交并归档普通 Paper；未提交且未标卡点的答案与空白/仍标卡点 Attempt 和完成快照同事务写入 | 浏览器 |
| GET `/practice/runs/{run_id}` | 读 | 读取已完成 Practice Run 的答卷 | 浏览器 |
| POST `/practice/runs/{run_id}/replay` | 写 | 从已完成轮次创建独立的新 Practice Run | 浏览器 |
| GET `/records` | 读 | 记录中心页（概览/练习·试卷/作答明细/错题，`?view=` 切换、`?problem=` 过滤） | 浏 |
| POST `/feedback` | 写 | 四件套（可带 `attempt_id` 链回本次作答） | 双 |
| GET `/problem/{id}` · GET `/kp/{id}` | 读 | 查询 | 双 |
| GET `/graph/model` · POST `/graph/state` · POST `/graph/kp` | 读/写 | 查询+图谱编辑 | 浏（模型可双） |
| GET `/ai/providers` | 读 | 对话 provider（PATH 发现+overrides） | 浏 |
| GET·POST `/ai/sessions`；PATCH·DELETE·GET `/ai/sessions/{id}` | 读/写 | 对话（id 必须是 `conv-NNN`，越界 400） | 浏 |
| POST `/ai/sessions/{id}/turns` · GET/PATCH/DELETE `…/turns/{turn}` · POST `…/queue/continue` · POST `…/cancel` | 读/写 | 对话（turn 必须是 `turn-NNN`；POST 可带 `submission_id`、`retry_of` 和 `queue_action`；编辑/删除带 `expected_revision`；continue 返回 `{conversation_id, queue_paused, turn}`，`turn` 可为 null；pending 读取不暴露捕获上下文） | 浏 |
| POST `/ai/sessions/{id}/queue/reorder` | 读/写 | `{expected_order,turn_ids}`：完整队列排列的顺序 CAS；返回 `{conversation_id,queue_order}`，不改变消息上下文 | 浏 |
| POST `/ai/sessions/{id}/turns/{turn}/interrupt` | 读/写 | `{expected_revision}`：原待发消息立即发送；复用身份与原上下文，审批/交接/过期版本冲突不修改 | 浏 |
| GET `/graph`（artifact 页） | 读 | 管线产物 | 浏 |
| POST `/ingest/rollback` | 写 | Check 整批回滚 | 双 |

## CLI 命令（`python -m workbench.cli.main …` / 安装入口 `lesson-kit …`；可用命令以 `workbench.cli.entry` 为准）

| 命令 | 性质 | 给谁 |
|---|---|---|
| `init`（空文件夹自动先建池+骨架；`path` 可省=当前目录，course 取 `--course` › 已有池名 › ASCII 文件夹名 › 自动顺序短码 `c01`+；显式值必须是 slug；池候选排除 ingest 备份，同文件夹多份池时必须用 `--course` 指名）/ `use`（换课程/章节，course 与 chapter 同样校验）/ `ls / open / serve` | 管理（创建+注册/切换/列表/URL/前台起服务） | 人 + Agent |
| `daemon start\|stop\|status` | 管理（后台服务生命周期；pid 与日志在用户级注册表目录） | 人 |
| `workspace <name> migrate-layout [--apply]` | 管理（默认只读预览；显式应用只迁移该课程根目录的 pool/intermediate，保留历史并更新注册） | 人 |
| `dashboard` | 管理（确保服务在跑 + 打开浏览器；不新增页面） | 人 |
| `doctor` | 读（环境自检：注册表/池库/provider/服务端口，只读不改） | 人 |
| `weak / due / schedule` | 读（弱项/到期/调度态） | Agent 主用 |
| `pull` | 读（**组一次练习**：范围/单题/条件筛选/薄弱·到期·错题；来源筛选 `--source-kind`·`--origin-kinds`·`--exam-year`·`--source-evidence` 均可重复，另有 `--search-stem`/`--search-source` 两个关键词域；`--plan` 落练习清单，`--print` 出学生卷+解答卷，`--check` 零写入预检，`--ids` 旧形状） | Agent |
| `practice / feedback` | 写（尝试/自评四件套） | Agent |
| `attempts`（`list --problem` / `get <id>` / `check`·`apply`·`correct --input <file\|->` / `sources add·list·remove --path`） | 读 + 写（Agent 代录尝试：check 零写入预检，apply 单事务多题，correct 按 attempt-id 撤回旧评分并重算；sources 只登记答卷目录） | Agent |
| `evidence <workspace> kp <kp-id> [--limit 1..20]` | 只读（按知识点返回有界近期作答、可读题面及实际记录结果；默认 8 条并报告 `has_more`，不推断学习标签） | Agent |
| `goals`（list/add/update/rm） | 写（目标管理） | Agent |
| `data` | 读 + **显式变更**（JSON 直改内容；`data <ws> audit` 只读报告重复、片段、标题和图片问题） | Agent |
| `mirror`（`init/check/status/sync`；`--repo` 指向本地内容仓库 checkout；支持 `--entity` 与 `sync --dry-run`） | 读 + **显式变更**（在知识池与版本化 JSON authored-content projection 之间按单实体同步；不执行 Git 网络操作，不因仓库缺文件或删除请求删池内容） | Agent |
| `mirror <workspace> figures --repo <checkout> --direction check|push|pull [--dry-run]` | 读 + 显式文件复制（池引用是成员关系；检查根目录和目标路径；push 写派生索引；不改池、不修剪、不执行 Git 网络操作） | Agent |
| `bridge add / add-model / list` | 配置 provider 与**模型条目**（显示名自定，与 harness 解耦）/ 报告解析到的可执行文件、来源与条目 | 人 |
| `guard` | 工作台守卫 | 双 |
| `ingest`（+ `prepare/run/gate/apply/render/recipe/rollback/migrate-figures` 八子链；`run --provider` 支持 codex/claude/pi；`recipe figures` 与 `migrate-figures` 落图入池） | 内容治理唯一写池通道（apply 记批次、跨章清单按章各一批；rollback 按批次撤销；figure-patch 回滚恢复前值） | 双 |
| `experiment` | 只读实验评估器 | 人 |
| `papers <workspace> save --input <manifest>` | 写（验证已导出的练习清单并保存到试卷列表；返回 JSON 回执） | Agent |
| `papers <workspace> list/get <ps-id>` | 读（缺失题目不隐藏容器，返回独立进度） | Agent |
| `papers <workspace> preview/update <ps-id> --input <manifest> [--confirmation <preview.json>]` | 显式原卷更新；结构修改须确认精确影响，不启动执行 | Agent |
| `papers <workspace> delete <ps-id>` | 仅删除容器与未完成状态，不删题目及学习证据 | Agent |

## 已安装的 Agent 契约模块

`python -m workbench.bridge.agent_contracts list` 列出 `commands`、`attempts`、`practice`、`actions`、`content` 五个主题；`python -m workbench.bridge.agent_contracts <topic>` 只打印对应静态契约，不读取或写入学习数据。这是模块入口，不增加 `lesson-kit` 顶层命令。

> **机器权威**：每条路由与命令的受众（Agent / 人 / 双 / 仅浏览器）与状态登记在
> `workbench/surface.py`，由 `tests/workbench/test_cli_surface.py` 与真实 parser /
> ROUTES 对账——新增或改名而不登记即测试失败（2026-09-25 practice-set-export-and-cli-audit）。
>
> 问卷 B1 口径：Agent 对池子增删改查全开——`data`（变更）、`ingest --apply`、
> `practice/feedback` 均可由 Agent 直跑；门禁是决断辅助不是闸门。
> `lesson-kit` 是本项目唯一的命令名（模块形式 `python -m workbench.cli.main` 等价）。
>
> 所有 `w/{name}` 路由与工作区命令都**只碰该工作区文件夹内的文件**：池、`.lessonkit/`、
> 计划与目标文件都在其中；会话 id、轮次 id、附图课程/章都先按裸名字校验再拼路径
> （2026-09-21 workspace-file-isolation）。多个工作区注册时，不带名的命令拒绝猜，
> 报错给出「`lesson-kit <cmd> <工作区名>`」的可粘贴形式。

2026-10-20 新增同会话操作：`POST /ai/sessions/{id}/queue/reorder` 接收 `{expected_order,turn_ids}`，返回 `{conversation_id,queue_order}`；`POST /ai/sessions/{id}/turns/{turn}/interrupt` 接收 `{expected_revision}`，返回该原 turn 的 canonical response。重排仅接受完整排列和匹配的旧顺序；revision/dispatch/审批/另一中断冲突返回 409 且无变更，非法请求 400。重复已提升 turn 的立即发送返回同一结果，不重跑。
