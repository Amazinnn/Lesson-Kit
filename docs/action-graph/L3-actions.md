# L3 · 动作层登记（人 / Agent 可执行的动作）

> 权限列按 2026-08-29 问卷 B1 口径：**人** = 界面操作；**Agent** = 可经 CLI/对话直接执行；**双** = 两边都有入口。
> 状态：`已实现 / 已定义未实现 / 未定义挂名 / 冻结 / 待退役`。

## 一、练习回路

| 动作 | 入口 | 权限 | 写 | 状态 |
|---|---|---|---|---|
| 选定练习范围（选择是唯一来源） | UI 勾选 | 人 | 选区键 | 已实现 |
| 加入今日要练 | UI 建议区 | 人 | 选区键 | 已实现 |
| 开始本轮练习（模式+自评时机必选） | UI | 人 | 牌组 | 已实现 |
| 拉题/拉卡 | API/CLI | 双 | 牌组 | 已实现 |
| 作答+本地判分（横幅 2s+高亮） | UI | 人 | 牌组（不写库） | 已实现 |
| 揭示（卡背/解析） | UI | 人 | 牌组 | 已实现 |
| 闪卡回翻（上一张/下一张，末尾拉新） | UI | 人 | 牌组游标 | 已实现 |
| 即时自评 1–5 | UI | 人 | 四件套 | 已实现 |
| 跳到下一道（已答/已玩不降级） | UI | 人 | 牌组 state | 已实现 |
| 提前结束→收束页统一评分 | UI | 人 | 四件套×未评 | 已实现 |
| 再练同类 | UI 收束页 | 人 | 新 session | 已实现 |
| 刷新恢复（游标+视图态） | 被动 | 人 | — | 已实现 |

## 二、记录与调度

| 动作 | 入口 | 权限 | 写 | 状态 |
|---|---|---|---|---|
| feedback 四件套 | API/CLI | 双 | 事件/信号/状态/调度 | 已实现 |
| practice 尝试记录 | API/CLI | 双 | attempts | 已实现 |
| 图谱状态显式编辑（不记反馈） | UI | 人 | 状态+调度 | 已实现 |
| 方向写入（direction 键，UI 无入口） | API | Agent | 方向调度行 | 已实现（仅数据层） |

## 三、内容治理（唯一合法写池）

| 动作 | 入口 | 权限 | 写 | 状态 |
|---|---|---|---|---|
| ingest 配方（micro-quiz / flash-card） | CLI | 双（Agent 可直跑） | problems/flash_cards 单事务（记批次 id+行戳记+manifest 快照） | 已实现 |
| 全池备份 | ingest --backup | 同上 | pool/backups | 已实现 |
| **Check 管线**（生成→校验→**直接入正式池**，无候选中间态；批次 id+整批回滚；候选组织并入校验环节） | CLI `ingest rollback --batch <id>` + 结果卡回滚按钮 + `POST /ingest/rollback` | Agent 主导 | 经门禁写池+批次标记+ingest_batches 登记 | **已实现**（introduce-check-pipeline，队列④） |
| 抽取管线入池（教材→KP→题） | 管线脚本 | 人 | 全部内容表 | 已实现（一次性） |

## 四、Agent 桥

| 动作 | 入口 | 权限 | 写 | 状态 |
|---|---|---|---|---|
| 对话轮次（自动带页面上下文） | UI/CLI | 双 | conv 留痕 | 已实现 |
| 新建会话/选 provider（锁定不换） | UI | 人 | conversations | 已实现 |
| 停止轮次 | UI | 人 | turn=cancelled | 已实现 |
| replace_practice_selection（明确练习意图才生效） | 对话产出动作 | Agent | 浏览器选区（一次性） | 已实现 |
| check_ingest（出题入库：出题/补池意图→内联 manifest→服务端门禁→批次 apply；失败逐条显式回对话流） | 对话产出动作 | Agent | 池内容（经门禁+批次标记） | 已实现（introduce-check-pipeline） |
| 整批回滚（结果卡按钮，与 CLI 同源 rollback） | UI 结果卡 | 人 | 池内容（按批次删行） | 已实现（introduce-check-pipeline） |

## 五、目标与时间

| 动作 | 入口 | 权限 | 写 | 状态 |
|---|---|---|---|---|
| 目标创建 | UI 表单 | 人 | goals.json | 已实现 |
| 目标自然语言助填（NL→对话轮次→prefill_goal_form→表单原位填充，提交留给人） | UI 目标表单 | Agent+人 | 表单字段（不直接写 goals.json） | 已实现（complete-goals-loop） |
| 目标编辑/删除 | UI 卡片入口（同表单 PATCH/DELETE） | 人 | goals.json | 已实现（complete-goals-loop） |
| 月历/工作量只读视图 | UI | 人 | — | 已实现（实验） |
| 每日计划重算 | UI | 人 | plan.json | 已实现 |
| 重日 prefill（只预填不发送） | UI | 人 | AI 输入框 | 已实现 |
| 复习重排建议 / 重日主动提醒（视图类，给 Agent 用） | 无 | Agent | — | 未定义挂名（问卷 C：延后） |

## 六、未定动作区（挂名池，定义见 PENDING-DEFINITIONS）

速成模式视图 · 批量揭晓 · 扩展摘要 · 教师记忆消费端 · Obsidian 打包 ·
图形资产管理 · CLI 层 agent 准备 · cloze 拆卡（闪卡 spec 未来段） ·
反向卡/leech（闪卡 spec 未来段） —— 均 `未定义挂名`。
冻结：方向卡 UI（待真实使用）、Scoropic（ADR 0021）、插件生态。

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
- 2026-08-30 加固批次 #39–#52 合并（HTTP 边界 400/415/遍历修复、对话重启恢复、
  学习写入事务化、目标库原子写、API 整数校验、前端损坏状态恢复等）。
- 2026-08-30 出题链修复（conv-023 回归）：桥解析改为全区块按意图匹配；
  check_intent 正则补自然措辞；被忽略的动作区块向下一轮上下文披露
  「未写入任何内容」（openspec：disclose-ignored-action-blocks）。
- 2026-08-30 candidate 物理退役落地（remove-candidate-store）：`wb data` 的
  candidate 实体与 gate/promote 动作下线、候选证据分支删除、candidate_problems/
  candidate_attempts 建表停止且真实池 DROP（先备份）；learner_signals 保留为核心。
