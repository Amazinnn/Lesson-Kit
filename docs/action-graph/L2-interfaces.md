# L2 · 接口层登记（API 路由 + CLI 命令）

> 「给谁」：**浏** = 浏览器工作台专用；**CLI** = 外部 Agent/终端；**双** = 两者。

## API 路由（`/api/w/{ws}` 前缀，30 条）

| 方法 路径 | 读写 | 服务层 | 给谁 |
|---|---|---|---|
| GET `/hub/workspaces` | 读 | 查询 | 浏 |
| GET `/weak` | 读 | 查询 | 双 |
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
| GET·POST `/ai/sessions`；PATCH·DELETE·GET `/ai/sessions/{id}` | 读/写 | 对话 | 浏 |
| POST `/ai/sessions/{id}/turns` · GET `…/turns/{turn}` · POST `…/cancel` | 读/写 | 对话 | 浏 |
| GET `/graph`（artifact 页） | 读 | 管线产物 | 浏 |
| POST `/ingest/rollback` | 写 | Check 整批回滚 | 双 |

## CLI 命令（`python -m workbench.cli.main …`，22 条）

| 命令 | 性质 | 给谁 |
|---|---|---|
| `init / ls / open / serve` | 管理（注册/列表/URL/起服务） | 人 + Agent |
| `weak / due / schedule` | 读（弱项/到期/调度态） | Agent 主用 |
| `pull` | 读（按 KP 拉题） | Agent |
| `practice / feedback` | 写（尝试/自评四件套） | Agent |
| `goals`（list/add/update/rm） | 写（目标管理） | Agent |
| `data` | 读 + **显式变更**（JSON 直改内容；candidate 实体与 gate/promote 动作已物理移除，2026-08-30） | Agent |
| `bridge add` | 配置任务 provider | 人 |
| `guard` | 工作台守卫 | 双 |
| `ingest`（+ `prepare/run/gate/apply/render/recipe/rollback` 七子链） | 内容治理唯一写池通道（apply 记批次；rollback 按批次撤销） | 双 |
| `experiment` | 只读实验评估器 | 人 |

> 问卷 B1 口径：Agent 对池子增删改查全开——`data`（变更）、`ingest --apply`、
> `practice/feedback` 均可由 Agent 直跑；门禁是决断辅助不是闸门。
> goals CLI 已上线（complete-goals-loop，22 命令）。
