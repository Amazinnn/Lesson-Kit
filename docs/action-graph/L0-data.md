# L0 · 数据层登记（表 / 文件 / 会话键）

> 谁写 = 唯一合法写入路径；谁读 = 主要消费方。所有写入必须能回溯到 L3 的某个动作。

## 池数据库（`pool/dmath.db`，经门禁或 feedback 写入）

| 表 | 存什么 | 谁写 | 谁读 |
|---|---|---|---|
| `knowledge_points` | 知识点：条目名/正文/类型/重要性及逻辑 `figure_paths` 引用 | 抽取管线（一次性）；图谱编辑（正文）；`data.content_mirror`（仅显式同步时写入已校验引用） | 拉取、图谱、覆盖审计、`data.evidence`、`data.figure_mirror` |
| `knowledge_relations` | KP 关系（类型/方向/强度） | 抽取管线 | 图谱布局 |
| `problems` | 正式题目（题干/解答/kp_ids/micro_quiz/`exam_year` 可空来源年份/逻辑 `figure_paths`/可空完整四维客观难度组） | 门禁配方 ingest、content-bundle、CLI `data`；`data.content_mirror`（校验引用；难度经 `data.difficulty.check`） | 拉取、选题组练习、练习、`data.evidence`、`data.figure_mirror` |
| `candidate_problems` | **已物理移除**（2026-08-30 remove-candidate-store：表 DROP，pipeline 侧脚本成为无调用方退役物） | —— | —— |
| `flash_cards` | 闪卡内容 + directions 方向能力（缺省 forward，双向不复制内容行） | 门禁配方 ingest | 拉卡、收束页 |
| `active_practice` + `active_practice_items` | 当前选中的 Paper 执行及其固定题序、游标、可空 `reveal_timing`（`per_item` / `on_submit`；旧轮次保持 `NULL`）和每题草稿/不会/参考材料已查看/锁定状态；按 Paper 独立保存检查点，同一工作区只激活一卷。仅 draft 不构成学习证据 | `data.active_practice`（开始、导航、显式不会、提交、暂停） | 练习页、`data.paper_progress`、Agent 页面上下文 |
| `practice_runs` | 已提交或显式替换/清除的轮次快照；普通题保留 `reveal_timing` 与答卷/展示事实，整卷只在显式交卷后归档；旧 `NULL` 模式/闪卡轮次沿原兼容路径 | `data.active_practice.submit`（Attempt 与快照同事务）；既有替换/清理流程 | 记录中心、完成页/本次答卷、Agent 页面上下文 |
| `problem_attempts` | 尝试记录（状态/备注/作答原文/卡点）；`per_item` 的逐题答案提交或「不会」立即写 Attempt；`on_submit` 只在整卷交卷时写未标卡点答案，空白或仍标「不会」的题写卡点 Attempt | 浏览器 `/attempts` 与显式 Paper submit、`POST /practice`、CLI `practice`、CLI `attempts apply|correct`（2026-09-24） | Agent 上下文、查询、CLI `attempts list|get`、`data.evidence` |
| `feedback_events` | 自评事件（评分/备注，含 item_type=card；Agent 代录的事件用 `attempt_id` 指回那次尝试）；Paper 同轮回看可原位覆盖确切 Attempt 的评分/评语，不新增事件或重放学习影响 | `POST /feedback`（首次评分及受限的同轮编辑）、CLI `attempts`（带评分的尝试） | 查询、信号、`data.evidence` |
| `learner_signals` | 弱项信号（只加强不自动消除） | 四件套之一 | 建议排序、Agent 上下文 |
| `review_schedule` | 调度行（每题/每卡/每方向一行：间隔/熟悉度/到期） | 四件套之一；图谱状态编辑 | due/weak/日历工作量 |
| `ingest_batches` 的批次 | 一次导入按章各一行（batch-NNN + kind + counts + 快照路径 + 备份 + 回滚时刻）；内容行带自己的批次标记，因此可按章撤销 | CLI `ingest apply`/桥内容动作 | `ingest batches`、rollback、结果卡 |
| `attempt_operations` | Agent 代录尝试的操作留痕：请求标识（幂等）、尝试 id、kind、评分、两条内容指纹、结果 JSON、effect 前后的投影快照（更正守卫用） | CLI `attempts apply|correct` | CLI `attempts check|get`、更正守卫 |
| `content_mirror_state` | 作者内容镜像同步状态：每实体最后同步修订号 + 规范化作者内容（无哈希，含有效扩展字段） | `data.content_mirror`（init/sync 成功路径） | `mirror check/status/sync` |
| `content_mirror_log` | 只追加的成功方向台账（五个方向枚举 + 前后修订号） | 同上 | 审计/证据 |

## 工作区文件（`.lessonkit/`，注册表 `LESSONKIT_WB_HOME` 下）

| 文件/目录 | 存什么 | 谁写 | 状态 |
|---|---|---|---|
| `workspaces.json` | 工作区注册表 | CLI `init` | 已实现 |
| `bridges.json` | 任务 provider 配置（`lesson-kit bridge add`） | CLI `bridge` | 已实现 |
| `answer-sources.json` | 答卷目录清单（工作区名 → 目录路径数组；只存路径，不含单图路径与图片字节） | CLI `attempts sources add/remove` | 已实现（2026-09-24） |
| `jobs/conv-NNN/` | `turn-NNN.json.paper_approval` (proposal, impact snapshot, decision); `conversation.json.queue_paused` 与仅包含 queued turn 的 `queue_order`（旧工件缺省数字 ID FIFO）；provider 会话引用、事件及成功 `transcript.jsonl`；`turn-NNN.json` 的 `message`、不可变 `accepted_message`、可选提交标识和稳定字段、状态、实际部分回答、`queue_revision`、`queue_action`、可选 `interrupt_target_turn_id` 与提交时上下文；`include_draft=true` 时上下文可含有界答案/备注/选项/可见图片快照；`queued` / `waiting_for_stop` 表示 provider 尚未开始；历史合并时旧成功交换只出现一次；不写 Pool 学习记录 | 桥 | 已实现（preserve-agent-messages-and-tool-outcomes；queue-agent-messages-and-interrupt） |
| `explain/{course}/{chapter}/` | （已移除，remove-explain-diagnose） | — | 已删除 |
| `goals.json` | 目标（顶层 JSON 数组；可选 start_date + deadline 时间区间） | `POST/PATCH/DELETE /goals` | 已实现 |
| `plan.json` | 每日计划缓存 | `POST /plan/recalculate` | 已实现 |
| `pool/backups/*.db` | 入池前整池备份 | ingest `--backup` | 已实现 |
| 练习清单 JSON（任意路径） | 一次练习选题的输入清单：标题 + 逐题 id/reason + 复现输入 | CLI `pull --plan` | 已实现（2026-09-25；是输入不是学习记录） |
| `output/{course}/{chapter}/{chapter}-problem-set.md` · `-solutions.md` | 练习集两份 Markdown（学生卷不含答案与内部标识；缺解「待补」） | CLI `pull --print`（或手工视图流程） | 已实现（2026-09-25 起 CLI 可产出） |

## 本地作者内容仓库 checkout（由调用者提供）

| 文件/目录 | 存什么 | 谁写 | 谁读 |
|---|---|---|---|
| `figures/<logical-path>` | 池已引用的原始图像字节；不是 JSON 实体 | CLI `mirror figures --direction push` | CLI `mirror figures --direction check|pull`、仓库浏览器 |
| `figures/<course-id>/_index.json` | 从池当前 `figure_paths` 推导的 UTF-8 图像归属索引；不能更改池引用 | CLI `mirror figures --direction push` | 仓库浏览器 |

## 浏览器 sessionStorage（标签页本地，v2 会话牌组）

| 键（`_{ws}` 后缀） | 存什么 | 写者 |
|---|---|---|
| `wb_session` | 会话牌组 v2：`{v:2, items[], cursor, ended?}`——每项含 id/载荷/作答/选项/判分/揭示/状态 | 练习回路各动作 |
| `wb_current` | 遗留当前项载荷（v1 兼容读，仅恢复时采纳） | （不再写） |
| `wb_agent_scope_<workspace>` | Agent 明确请求的 Paper authoring 范围；只作 Agent 上下文，不是学生组卷选择器 | Agent `replace_practice_selection` 兼容动作 |
| `wb_kps` / `wb_kp_selection` | 旧练习范围/跨页选区键；不再用于普通 Paper 练习或学生手工组卷 | 旧页面恢复兼容（若仍有旧标签页） |
| `wb_practice_mode` / `wb_practice_rating_mode` | 内容模式 / 自评时机兼容偏好；不配置新的普通 Paper 执行 | 闪卡与旧练习会话 |
| `wb_practice_include` / `wb_similar_round` | 旧同类轮临时参数；不用于新普通 Paper 重练 | 旧练习会话兼容 |
| `wb_ai_conversation` / `wb_ai_recent` | 当前对话 id / 最近对象（供上下文） | AI 面板 |
| `wb_ai_message_outbox_<workspace>_<conversation>` | 按提交标识保存消息、原始请求上下文及 `sending/rejected/unknown/accepted/failed` 状态；成功完成后清除 | AI 面板 |

> 保存试卷的未完成进度与文本/选择草稿由 SQLite 独立保存（DATA_MODEL 的 paper_state / active_practice）；浏览器关闭不清除。草稿失败出站箱 `wb_paper_draft_<workspace>_<execution_id>_<position>` 用上下文和顺序校验恢复，不制造学习记录。其他临时牌组缓存沿用既有规则。

## 浏览器 localStorage（工作区偏好）

| 键 | 存什么 | 写者 |
|---|---|---|
| `wb_settings_<workspace>` | 工作区偏好，包括 `runningSendAction`（默认 `queue`，可选 `interrupt`；只影响之后的提交） | Agent 设置 |

2026-10-20：`conversation.json.queue_order` 只存 queued turn ID 的确认顺序；缺字段时兼容数字 ID FIFO。等待停止的 interrupt 不入此数组，原 turn 的身份、当前文字和原上下文继续保存在同一工件，不新增 Pool 字段。
