# L1 · 服务层登记（域逻辑模块）

> 模块只经 L2 接口被调用，不直接暴露。依赖 = 主要触及的 L0 表。

| 模块 | 职责 | 依赖 | 被谁调用 |
|---|---|---|---|
| **拉取 pull** | 按选区 KP + 模式拉题：exclude 已见、到期优先、n 条、诚实空态 | problems、review_schedule | `/pull`（API/CLI）、练习页 |
| **拉取 pull-cards** | 同上，闪卡版（选区过滤/到期行优先/exclude_ids） | flash_cards、review_schedule | `/pull-cards`、练习页 |
| **feedback 四件套** | 一次自评原子写四件事：事件→信号→状态→调度；支持 item_type=problem/card + direction 键 | feedback_events、learner_signals、kp 状态、review_schedule | `/feedback`（API/CLI）、收束页 |
| **practice 记录** | 记一次尝试（作答原文/卡点/状态） | problem_attempts | `/practice`（API/CLI） |
| **门禁配方 micro-quiz** | manifest（micro-quiz-patch）确定性校验→备份→单事务 apply；重复 id 拒收 | problems | CLI `ingest recipe` |
| **门禁配方 flash-card** | 同构（flash-card-patch）：五字段契约/正则 id/来源必填 | flash_cards | CLI `ingest recipe` |
| **ingest 链** | prepare/run/gate/apply/render 六环节编排与中间产物 | 中间产物目录 | CLI `ingest` 家族 |
| **桥 runner/contracts/teacher** | 任务状态机（queued/running/done/failed）、输出契约校验、教学契约渲染 | jobs/、explain/ | `/ai/*`、CLI `ai` |
| **对话 conversations** | provider 原生会话的建立/轮次/事件流/取消/最小镜像 | jobs/conv-### | `/ai/sessions/*` |
| **provider 发现/配置** | PATH 发现（对话）与 bridges.json（任务）两套口径 | bridges.json | `/ai/providers`、`/ai/task-providers` |
| **查询 queries** | hub 统计/due 列表/图谱模型/kp 详情/review 概览（标签全长） | 全表只读 | 多个 GET API |
| **计划 planning** | 每日建议（≤3 条人话）+ 失败保留上次结果 | 全表只读 + plan.json | `/plan`、建议区 |

> 已知边界：任务 provider 与对话 provider 是**两套配置**（bridges.json vs PATH 发现），
> 界面按钮门槛以任务 provider 为准（`GET /ai/task-providers`）。
