# Requirements — lesson-kit Review Workbench

> 当前人话版需求与验收摘要。规范性行为以 `openspec/specs/` 与尚未归档的
> `openspec/changes/` 为准；历史设计只在 OpenSpec archive、
> `docs/DISCUSSION-RECORD.md` 与 Git 中保留。

## 产品目标

Lesson Kit 把课程源材料整理为课程级 SQLite 知识池，并提供每天可打开的本地学习工作台。
系统优先帮助学习者回到知识来源、练习薄弱处和处理到期内容；AI 只通过外部 Agent CLI
旁挂，核心学习闭环在没有 Agent 时仍可运行。

## 当前范围

- 三页工作台：练习、知识点、知识图谱；顶栏章透镜只改变浏览范围，不改变练习选区。
- 课程级知识池保存知识点、正式题、微题、闪卡、学习信号、反馈、调度、目标与计划。
- `lesson-kit` 是唯一公开 CLI；Shell 只编排，Domain 保存纯规则，Data 是唯一 SQLite 写层。
- 练习由弱项、显式选区、题型、来源、到期和可选难度条件拉取；任何排序都不得锁题。
- 开放题遵循“先作答、再揭晓、后自评”；机器可判题按内容契约判分。
- 普通 Agent 对话零学习写入；内容写入只经显式 Data 命令或带意图门的 Check 管线。
- Check 管线直接把合规闪卡/微题写入正式池并记录批次；失败整批零写入，成功批次可整批回滚。
- Candidate、按题 explain/diagnose 任务和独立复习页均已退役，不得在当前入口恢复。

## 题目来源

每道新 Agent 管理的正式题或微题必须同时声明：

- `source_kind`：`textbook | quiz | midterm | final | makeup | other`，表示依据材料；
- `origin_kind`：`source_problem | adapted_problem | generated_grounded`，表示原题、改编或生成。

派生 `source_group` 互斥：生成来源优先归 `ai_generated`；其余考试材料归 `exam`，
课本材料归 `textbook`，剩余归 `other`。CLI/API 可组合筛选两轴和便捷组；练习页本轮
不新增来源控件。

## 题目难度

正式题与微题可拥有惰性的客观四维评级：知识跨度、推理深度、迁移距离、构造开放性，
每维为整数 1–5。整组评级要么全空，要么四维、REAL 总分和模型 id 全有；未评级题照常
入池、显示、练习和调度。闪卡不评级，`knowledge_points.difficulty` 仅保留 legacy
知识内容复杂度语义。

唯一 v1 汇总模型是 `cognitive-v1-equal-mean`：四维等权平均，使用 Decimal
`ROUND_HALF_UP` 保留一位小数。调用方只提交四维，不提交总分、模型或文字依据。
评级只能由显式 `lesson-kit difficulty <workspace> check|apply --input <file|->` 触发；
内容入池、页面读取和后台任务不得自动评级、排队或提示评级。题干、解析、知识点关联或
题型变化会原子清空整组评级。

不带难度参数的 pull 保持原顺序；显式范围排除未评级题。显式 `balanced` 按总分半数进位
到 1–5 档，并按 `3→2→4→1→5` 在非空档轮转，未评级题只在末尾补足。计划可给系统或
Agent 提供隐藏分布和建议配比，学生界面不显示裸分、分维或星级。个人反馈只影响知识点
范围和优先级，不推导能力等级，也不回写客观难度。

## Agent 对话与 Pi 活动

- 每个对话固定一个 provider；Codex、Claude、Pi 使用各自原生 session。
- 350 ms 轮询、normalized activity 和事件文件是唯一流链路，不新增 WebSocket/SSE。
- Pi 每个对话一个隐藏 `--mode rpc` 常驻进程，严格 LF JSONL 与关联命令；空闲 30 分钟回收，
  不设并发上限；取消先发 abort，失效才 terminate/kill；启动/握手失败可重启一次，
  prompt 接受后崩溃不得重放。全部 provider 子进程在 Windows 下隐藏启动。
- 新增内容一律走 `content-bundle`：知识点、正式题、微题、闪卡与必需原图同一份清单、
  同一次预检、一个批次 id、一份备份；条数无上限；任一条不合法或缺必需图片即整批零写入。
  清单可暂存于本对话 jobs 目录，服务端只接受该目录内的相对 JSON 路径。
- 合法的纯新增内容动作自动执行（浏览器关键词意图门已删除）；修改、删除、回滚与难度评级
  仍只按明确指令执行；无动作的普通回答零写入。
- 教材原题保留原题文字、数值、选项、作答形式与 `origin_kind=source_problem`；只有明确要求
  才改编为微题。来源证据显示在题目下方；教材答案存 `source_answer`；AI 解析按需生成并显示
  「AI 生成解析」。图片按原始字节复制到 `.lessonkit/figures/{course}/{chapter}/`。
- Agent 消息与知识点关联题统一支持安全 Markdown 子集与 GFM 表格，窄面横向滚动。
- Pi 的读文件、更新文件、搜索、运行命令、Lesson Kit 操作和其他具体工具显示为独立紧凑
  消息；同一 activity id 原位更新。Codex/Claude 保持现有执行计划。
- Pi 连续文本 delta 合并为一个气泡；具体活动结束当前文本段，后续文本新开气泡。
- provider 通用阶段、thinking、隐藏推理和原始协议事件永不显示。
- 工具输出默认折叠；路径、查询与经遮盖/截断的命令可见，写入内容不作活动摘要。
- 只有成功轮次保存合并后的具体活动；失败和取消过程不进入长期镜像。

## 数据与安全边界

- 单工作区只使用自己的目录和一个课程池；运行文件位于 `.lessonkit/`。
- 所有内容 ID 使用可读顺序号，不使用哈希 ID。
- Runtime 保持 stdlib-only、单进程、单端口；不新增第二套事件协议或 AI 内核。
- 冻结的 `pipeline/` 行为继续兼容；新 workbench schema 只通过
  `pool/scripts/pool_schema.py` 的幂等 ensure 入口演进。
- 仓库 `pool/dmath.db` 是可丢弃测试池；开发和验收不得迁移外部或真实学习池。

## 发布验收

- Python 全量、Node 交互测试、compileall、OpenSpec strict、doctor 与 guards 通过。
- Windows 会话镜像并发用确定性同步测试证明读写串行且无 sharing violation。
- schema 重建在 `foreign_keys=ON` 下保留行、外键、约束和索引，`foreign_key_check` 为空。
- 难度 check 零写入；apply 覆盖且整批原子；内容变化清空评级；普通 pull 顺序不变。
- content-bundle 在副本上完成 25 题规模导入：知识点/题目/图片同批预检，图片按字节落盘，
  回滚只删无引用图片；真实 Pi 0.85.1 三轮同一 PID、abort 生效、重启后恢复会话、无可见窗口。
- Pi 各工具映射、原位更新、文本分段、折叠输出、成功恢复及失败/取消边界均有自动化测试。
- 最终真实 Pi 只在隔离 registry、工作区和池副本中完成一轮读、写、Lesson Kit CLI 与回答；
  不触碰外部工作区或真实学习数据。

## 明确不做

- 真题拟合、IRT、自动个体校准、评分历史和文字评分依据。
- 给闪卡或知识点套用题目四维难度。
- 练习页来源/难度筛选控件。
- 自动评级、后台评级或内容入池时评级。
- Codex/Claude 活动消息样式改造、新依赖或第二套流协议。
