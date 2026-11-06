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
