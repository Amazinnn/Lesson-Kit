# L2 · 接口层登记（API 路由 + CLI 命令）

> 「给谁」：**浏** = 浏览器工作台专用；**CLI** = 外部 Agent/终端；**双** = 两者。

## API 路由（`/api/w/{ws}` 前缀，32 条）

| 方法 路径 | 读写 | 服务层 | 给谁 |
|---|---|---|---|
| GET `/hub/workspaces` | 读 | 查询 | 浏 |
| GET `/weak` | 读 | 查询 | 双 |
| POST `/chapter` | 写 | 注册表（顶栏章透镜；空串 = 全课程，与 `use` 同源） | 浏 |
| GET `/due` | 读 | 查询 | 双 |
| GET `/calendar` | 读 | 查询 | 浏 |
| GET `/plan` · POST `/plan/recalculate` | 读/写 | 计划 | 浏 |
| GET·POST `/goals`；PATCH·DELETE·GET `/goals/{id}` | 读/写 | goals.json | 浏（UI 仅用创建） |
| POST `/pull` | 读 | 拉取 | 双 |
| POST `/pull-cards` | 读 | 拉卡（direction_mode + 独立方向排除） | 双 |
| POST `/practice` | 写 | practice 记录 | 双 |
| POST `/feedback` | 写 | 四件套 | 双 |
| GET `/problem/{id}` · GET `/kp/{id}` | 读 | 查询 | 双 |
| GET `/graph/model` · POST `/graph/state` · POST `/graph/kp` | 读/写 | 查询+图谱编辑 | 浏（模型可双） |
| GET `/ai/providers` | 读 | 对话 provider（PATH 发现+overrides） | 浏 |
| GET·POST `/ai/sessions`；PATCH·DELETE·GET `/ai/sessions/{id}` | 读/写 | 对话（id 必须是 `conv-NNN`，越界 400） | 浏 |
| POST `/ai/sessions/{id}/turns` · GET `…/turns/{turn}` · POST `…/cancel` | 读/写 | 对话（turn 必须是 `turn-NNN`） | 浏 |
| GET `/graph`（artifact 页） | 读 | 管线产物 | 浏 |
| POST `/ingest/rollback` | 写 | Check 整批回滚 | 双 |

## CLI 命令（`python -m workbench.cli.main …` / `lesson-kit …`，22 条顶层命令）

| 命令 | 性质 | 给谁 |
|---|---|---|
| `init`（空文件夹自动先建池+骨架；`path` 可省=当前目录，course 取 `--course` › 已有池名 › ASCII 文件夹名 › 自动顺序短码 `c01`+；显式值必须是 slug；池候选排除 ingest 备份，同文件夹多份池时必须用 `--course` 指名）/ `use`（换课程/章节，course 与 chapter 同样校验）/ `ls / open / serve` | 管理（创建+注册/切换/列表/URL/前台起服务） | 人 + Agent |
| `daemon start\|stop\|status` | 管理（后台服务生命周期；pid 与日志在用户级注册表目录） | 人 |
| `dashboard` | 管理（确保服务在跑 + 打开浏览器；不新增页面） | 人 |
| `doctor` | 读（环境自检：注册表/池库/provider/服务端口，只读不改） | 人 |
| `weak / due / schedule` | 读（弱项/到期/调度态） | Agent 主用 |
| `pull` | 读（**组一次练习**：范围/单题/条件筛选/薄弱·到期·错题；`--plan` 落练习清单，`--print` 出学生卷+解答卷，`--check` 零写入预检，`--ids` 旧形状） | Agent |
| `practice / feedback` | 写（尝试/自评四件套） | Agent |
| `attempts`（`list --problem` / `get <id>` / `check`·`apply`·`correct --input <file\|->` / `sources add·list·remove --path`） | 读 + 写（Agent 代录尝试：check 零写入预检，apply 单事务多题，correct 按 attempt-id 撤回旧评分并重算；sources 只登记答卷目录） | Agent |
| `goals`（list/add/update/rm） | 写（目标管理） | Agent |
| `data` | 读 + **显式变更**（JSON 直改内容；candidate 实体与 gate/promote 动作已物理移除，2026-08-30） | Agent |
| `bridge add / list` | 配置 provider / 报告解析到的可执行文件与来源 | 人 |
| `guard` | 工作台守卫 | 双 |
| `ingest`（+ `prepare/run/gate/apply/render/recipe/rollback/migrate-figures` 八子链；`run --provider` 支持 codex/claude/pi；`recipe figures` 与 `migrate-figures` 落图入池） | 内容治理唯一写池通道（apply 记批次、跨章清单按章各一批；rollback 按批次撤销；figure-patch 回滚恢复前值） | 双 |
| `experiment` | 只读实验评估器 | 人 |

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
