# L0 · 数据层登记（表 / 文件 / 会话键）

> 谁写 = 唯一合法写入路径；谁读 = 主要消费方。所有写入必须能回溯到 L3 的某个动作。

## 池数据库（`pool/dmath.db`，经门禁或 feedback 写入）

| 表 | 存什么 | 谁写 | 谁读 |
|---|---|---|---|
| `knowledge_points` | 知识点：条目名/正文/类型/重要性 | 抽取管线（一次性）；图谱编辑（正文） | 拉取、图谱、覆盖审计 |
| `knowledge_relations` | KP 关系（类型/方向/强度） | 抽取管线 | 图谱布局 |
| `problems` | 正式题目（题干/解答/kp_ids/micro_quiz/难度可空 1-5/`exam_year` 可空来源年份） | 门禁配方 ingest、content-bundle、CLI `data` | 拉取、选题组练习、练习 |
| `candidate_problems` | **已物理移除**（2026-08-30 remove-candidate-store：表 DROP，pipeline 侧脚本成为无调用方退役物） | —— | —— |
| `flash_cards` | 闪卡内容 + directions 方向能力（缺省 forward，双向不复制内容行） | 门禁配方 ingest | 拉卡、收束页 |
| `problem_attempts` | 尝试记录（状态/备注/作答原文/卡点） | `POST /practice`、CLI `practice`、CLI `attempts apply|correct`（2026-09-24） | Agent 上下文、查询、CLI `attempts list|get` |
| `feedback_events` | 自评事件（评分/备注，含 item_type=card；Agent 代录的事件用 `attempt_id` 指回那次尝试） | `POST /feedback`（四件套之一）、CLI `attempts`（带评分的尝试） | 查询、信号 |
| `learner_signals` | 弱项信号（只加强不自动消除） | 四件套之一 | 建议排序、Agent 上下文 |
| `review_schedule` | 调度行（每题/每卡/每方向一行：间隔/熟悉度/到期） | 四件套之一；图谱状态编辑 | due/weak/日历工作量 |
| `ingest_batches` 的批次 | 一次导入按章各一行（batch-NNN + kind + counts + 快照路径 + 备份 + 回滚时刻）；内容行带自己的批次标记，因此可按章撤销 | CLI `ingest apply`/桥内容动作 | `ingest batches`、rollback、结果卡 |
| `attempt_operations` | Agent 代录尝试的操作留痕：请求标识（幂等）、尝试 id、kind、评分、两条内容指纹、结果 JSON、effect 前后的投影快照（更正守卫用） | CLI `attempts apply|correct` | CLI `attempts check|get`、更正守卫 |

## 工作区文件（`.lessonkit/`，注册表 `LESSONKIT_WB_HOME` 下）

| 文件/目录 | 存什么 | 谁写 | 状态 |
|---|---|---|---|
| `workspaces.json` | 工作区注册表 | CLI `init` | 已实现 |
| `bridges.json` | 任务 provider 配置（`lesson-kit bridge add`） | CLI `bridge` | 已实现 |
| `answer-sources.json` | 答卷目录清单（工作区名 → 目录路径数组；只存路径，不含单图路径与图片字节） | CLI `attempts sources add/remove` | 已实现（2026-09-24） |
| `jobs/` | 任务工作文件 + 对话留痕（conv-###） | 桥 | 已实现 |
| `explain/{course}/{chapter}/` | （已移除，remove-explain-diagnose） | — | 已删除 |
| `goals.json` | 目标（顶层 JSON 数组；可选 start_date + deadline 时间区间） | `POST/PATCH/DELETE /goals` | 已实现 |
| `plan.json` | 每日计划缓存 | `POST /plan/recalculate` | 已实现 |
| `pool/backups/*.db` | 入池前整池备份 | ingest `--backup` | 已实现 |
| 练习清单 JSON（任意路径） | 一次练习选题的输入清单：标题 + 逐题 id/reason + 复现输入 | CLI `pull --plan` | 已实现（2026-09-25；是输入不是学习记录） |
| `output/{course}/{chapter}/{chapter}-problem-set.md` · `-solutions.md` | 练习集两份 Markdown（学生卷不含答案与内部标识；缺解「待补」） | CLI `pull --print`（或手工视图流程） | 已实现（2026-09-25 起 CLI 可产出） |

## 浏览器 sessionStorage（标签页本地，v2 会话牌组）

| 键（`_{ws}` 后缀） | 存什么 | 写者 |
|---|---|---|
| `wb_session` | 会话牌组 v2：`{v:2, items[], cursor, ended?}`——每项含 id/载荷/作答/选项/判分/揭示/状态 | 练习回路各动作 |
| `wb_current` | 遗留当前项载荷（v1 兼容读，仅恢复时采纳） | （不再写） |
| `wb_kps` / `wb_kp_selection` | 本轮范围 / 跨页选择集（选择是唯一范围来源） | 选择动作、开始会话 |
| `wb_practice_mode` / `wb_practice_rating_mode` | 内容模式 / 自评时机 | 开始会话 |
| `wb_practice_include` | 同类轮的 include ids | 再练同类 |
| `wb_similar_round` | 同类轮标志 | 再练同类 |
| `wb_ai_conversation` / `wb_ai_recent` | 当前对话 id / 最近对象（供上下文） | AI 面板 |

> 关键性质：关标签页 = 牌组与草稿全部蒸发（设计如此，不补写）；已保存评分在池里不受影响。
