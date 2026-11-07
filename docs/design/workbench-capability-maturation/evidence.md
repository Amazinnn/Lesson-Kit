# 证据与核对清单

## 检出与时间范围

2026-11-05 核对主检出 main 为 b5054e8d，教学工作树 feat/exam-prep-engine 为 9e640332。后续引用前检查对应检出是否变化。本树同时考察两者，保留合入状态区别。

## 已有证据与限制

- 作者内容镜像 workbench/data/content_mirror.py 当前实体为 kp/problem/relation，Paper 未进入该实体集合。现行 GLOSSARY 将本地镜像与 Git 网络操作分开，扩展前需要确认产品意图。
- 教学分支的检验提交接口在临时 fixture 中接受不存在的选项，同一 check 可多次追加 check.result。属于局部复现，尚未执行真实浏览器验收。
- 教学分支的 guardrails 模块有纯规则与测试，本轮静态搜索未发现生产调用入口。需结合实际事件路径继续核对，暂不宣称全部护栏均未生效。
- ARCHITECTURE 的 Domain 零 IO、Data 不导入 Domain 声明，与 feedback 的事务/Pool 调用及 Data 导入 Domain 规则存在漂移。裁决需登记权威协调，不可仅依代码现状改写规范。
- 活跃 change 中部分任务状态与已有代码覆盖存在差异。每项需核对已实现、已验证、已合入及已上线，禁止只按勾选推断。
- 主目录此前全量检查为 1302 passed、13 failed，失败集中于 Pi 相关测试。开启 PYTHONUTF8 后相关三个套件 125 passed。尚未在该模式重跑全量，编码根因需进一步定位。
- 主目录编译、当前规范 21 项与提取 guard 通过。教学分支三个选定套件 31 passed。以上均不代表真实课程或浏览器交互接受。
- 默认 3081 端口在上次检查时拒绝连接，当前实际运行版本未确认。历史状态文档中的已上线描述不能替代当前运行证据。

## 后续每项证据要求

记录来源位置、检出版本、核对时间、复现步骤、输入范围、观察结果、结论限制及受影响决定。历史审计数字重新核实后才用于工作量或风险估计。
# 2026-11-06 发送恢复补充核对

主检出 workbench/server/static/workbench.js 的 ai 轮询状态处理将 failed 和 cancelled 都通过 aiUpdateOutbox 写成 failed。aiRenderOutbox 将 unknown、rejected、failed 作为可操作恢复记录呈现。这支持所有者关于停止后出现恢复记录的报告。静态证据不证明它会自动重发，也不证明重复消息的根因。

Q025–Q027 已记录新的期望行为及验收门槛，尚未修改产品实现。重复消息须追踪提交身份、接受次数、内容执行和呈现后复现。

## 2026-11-06 学习与复习研究核查

主目录 docs/research/2026-11-02-learning-efficiency-algorithms.md 明确标为研究提案，综合调度、知识追踪、学习科学等分报告并提出分期路线。已读取总提案开头及相关主题索引，本轮未独立重验论文原始结论和数字，不将研究建议自动纳入实施范围。这些研究文件当前为未跟踪资产，规划引用不代表已纳入版本交付，后续交接须解决可获取性。

教学分支 9e640332 的 workbench/domain/session_machine.py 已定义 created、briefing、running、concluding、closed 及 suspended、abandoned 的受控转移。此处是教学会话生命周期，不能直接当作诊断、加强和跨日维护的学习进程。workbench/domain/engine/registry.py 已列出 FSRS、加权选题、时间估计及 Elo 策略；workbench/data/forms.py 已消费薄弱、能力、到期等事实形成候选和原因。存在实现不等于已合入主目录、接通用户目标或通过真实学习验收。

后续需建立研究依据、现行契约、分支实现、入口消费和验收证据的对应关系。先复用已有会话与调度语义，再决定是否存在必须新增的持久目标信息。

## 2026-11-06 作答证据与基础检查

docs/DATA_MODEL.md 已区分原始作答、批改结果、显式不会及参考已查看事实，并规定主观批改不自动重放掌握度和排期。题目 micro_quiz 与 flash_cards 也已有内容表示。后续诊断须核对这些证据的实际 writer/consumer，优先复用，不因两种薄弱表现而新建一套竞争状态。此轮仅核查持久语义与候选表示，未验证闪卡或选择题定位知识缺口的准确性及耗时。

## 2026-11-06 前置预防与队列展示

主检出 workbench/ingest/__init__.py 的 content-bundle 预检路径已检查章节值、知识点 ID 前缀、引用存在性等。已读片段不能证明引用对应的学术内容与原教材一致，后续须追踪提取技能和原文核对流程。不能将本次局部静态阅读外推为全项目不存在语义核对。

workbench/server/static/workbench.js 的 aiRenderPendingQueue 已展示拖动手柄、立即发送等控件；Q042 计划将队列正常展示收敛至正文、编辑、删除，需在后续 change 显式协调现行队列 UI 契约。aiRenderPendingQueue 与失败恢复的 aiRenderOutbox 为不同路径，不能只改其中一处便宣称全部发送体验完成。

## 2026-11-06 草稿及渲染已有能力

docs/DATA_MODEL.md 的 active_practice_items.draft_json/draft_sequence、暂停检查点和 wb_paper_draft 出站箱已有草稿及恢复语义。paper-practice.js 同时使用本地存储和服务端草稿路径。300 份目标须在此基础上核对记录身份、淘汰与兼容，不能简单截断现有活动执行表。

part-practice.js 的批改长文本已有 richText 消费路径，部分状态与标签为 textContent。尚未完成全字段清单，不能把全部 textContent 一概判为错误，也不能因为部分路径支持就宣称多字段渲染完整。

S004 更新后，前段 300 份目标仅为已被替代的历史讨论。主检出 pages.py 的练习入口有 active-practice-resume，试卷列表另有逐卷继续入口；PRODUCT-MANUAL 已声明多张 Paper 独立保存未完成进度。下一步应核查练习开始界面是否暴露全部未完成卷及正常恢复路径，静态入口存在不能代替实际浏览器验收。

标题补充核查。paper-practice.js 的试卷标题存在 textContent 与 escapeHtml 显示路径。workbench.js 的重命名入口有从 heading.textContent 获取默认值的路径。后续接入富文本后必须检查此类源内容读取，防止将渲染后的文本或公式辅助节点写回标题。此处为静态风险点，尚未做渲染改动或复现原文损坏。

首优先包补充。已读取现有 agent-chat-simplify/proposal.md，它覆盖输入框、审批、字体及部分队列暂停问题，不能直接当作本轮全部发送需求已实现。当前 workbench-ui spec 明确规定失败恢复在候选列表且对话历史不显示重试控件，与 Q025–Q027 的新期望需要显式协调。并非只删前端按钮即可完成契约变更。

S005 检查。已检索规划树全部 Markdown 及 expand-file-mediated-course-sync/proposal.md 的说明、解释、披露、原因、缺口及任务用词。规划曾在 Q035/Q036/Q044/Q048/Q066/Q070 及对应 benchmark 中要求主动说明，现由 S005 统一收回默认学习 UI 展示。文件交换 proposal 的完整回执属于 CLI 工件，继续保留。此次只修改规划文档，没有新增程序中的说明机制，也未验证现有界面是否残留其他冗余字段。

Q071 现状核查。workbench-ui spec 已规定运行中发送偏好在工作区设置保存且默认 queue，Bridge Conversations.send 已有 queue_action 参数和 queue/interrupt 校验。该问题可由仓库查明，撤销不计数。未执行浏览器验证，不从静态规范和代码推断现有全部发送体验无缺陷。

顶层准则入口核查。docs/design/philosophy.md 为产品及学习理念，ARCHITECTURE §5 为工程约束。ADR 0025–0027 已禁止图谱求解器及渲染器保留并行运行时 fallback，ADR 0007 则记有旧池 related_kp_ids fallback 的历史决定，需按现行字段契约核对实际兼容责任。S006 新规写入 AGENTS 并由架构文档引用；本轮未扫描全部后端 fallback 调用，不宣称已完成存量清理。

2026-11-07 知识点标签核查。主检出 knowledge_points 的契约字段包含 knowledge_type、importance、graph_label，未发现通用 tags 字段及对应知识点标签读写契约。workbench/data/content.py 支持读取/编辑知识点的既有字段；题目 topic_label 已退役，闪卡 topic_label 独立存在。不能把闪卡标签或图谱短名称当成知识点通用标签。此结论基于当前契约与静态路径搜索，未查询真实课程的分类填充情况。


2026-11-07 新建知识点路径核查。workbench/ingest/__init__.py 的 content-bundle 预检接受 knowledge_points，新项需有效章节、唯一非空 key 及非空 knowledge_item，可由现有逻辑分配可读 ID。同批题目可通过本地 key 引用新知识点。knowledge_type 允许缺失，提供时须属于 KP_TYPES。该静态证据说明已有入库载体，不能据此认定 Agent 生成内容的正确性、来源核对或正常入口端到端能力已经验收。FILE_CONTRACT 的 content-bundle 契约为后续协调入口，尚未变更持久字段或执行实际入库。


2026-11-07 经验与独立知识点边界。workbench/data/experience.py 在 kp_experiences 中按 kp_id 维护一份可选总结，题目引用由 kp_experience_problems 保存，更新使用 expected revision。bridge/conversations.py 已提示在持续授权下读取、合并去重并记录经验。该路径依附既有知识点，不能单独满足 Q086 从练习提炼独立知识点的需求。此处只核查静态结构与提示词，不宣称真实 Agent 已能自动选择合适的总结粒度或创建时机。


2026-11-07 回滚行为区分。PRODUCT-MANUAL 第 8 章及内容管理说明同时描述整份清单预检零写入、写入事务失败恢复、显式 ingest rollback 撤销成功批次。workbench/ingest/__init__.py 的 rollback_batch 会检查后续练习/评价及内容改动再决定是否拒绝撤销；同模块多处 conn.rollback 属于写入异常处理。相同中文词覆盖不同操作，Q096 当前未明确取消范围，不能仅按字符串删除 rollback 调用。此轮只作静态核查，未复现所有者实际感到阻断的操作。


2026-11-07 审批静态清点。GLOSSARY 包含 Approval Gate 与 Paper Progress-reset Approval；workbench-ui 定义批次回滚审批，ai-teacher-bridge 定义改卷待审批保存及暂停派发；bridge/agent_contracts.py 要求只提议改卷并等待额外点击，bridge/conversations.py 存在 pending_paper_approval、审批投影、派发阻断与 resolve_paper_approval。这些是 S008 的明确契约协调对象。本轮未修改程序，以上路径仍可能要求审批，不将顶层新规则写入误报为运行时退役完成。


2026-11-07 新参考资料。完整读取用户给定《学习协议 V3.1》主文、分页及视觉规范、Teach 方法与格式模板，原包副本逐字节一致且 ZIP 成员校验通过，见 learning-protocol-v3.1.md。资料包含教学方法及宿主动作要求，本次仅分析，未安装 Skill 或执行附录指令。静态核查 goals.py 已有 .lessonkit/goals.json 和派生 plan.json；evidence.py 仅提供作答事实，由外部 Agent 形成结论。完整教学续接与 GitHub 交接尚未经真实模型/正常用户入口验证。


2026-11-07 规划 v1 完成检查。六个新/修订 change 的行为规范、设计和未勾选任务已生成，16个修改条款保留87个原场景名称，退役功能有独立迁移说明。当前 live specs 21项通过严格检查，规划文档本地链接及103问统计通过。本轮未执行产品实现或真实使用验收，具体门槛见 benchmarks/catalog，交接状态见 STATUS。
