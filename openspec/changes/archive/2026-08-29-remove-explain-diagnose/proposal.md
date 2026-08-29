# remove-explain-diagnose 提案

## Why

所有者 2026-08-29 问卷定案（A1/A3，DISCUSSION-RECORD 专题 21 待补记）：
讲解/诊断是「针对一道题的特化工作」——Agent 拿到的上下文本就是整个版面，
没必要只拿一道题展开；两个动作**彻底移除**（前端按钮 + API + spec 条款），
`.lessonkit/explain/` 产物随功能一并清理。

结构事实：讲解/诊断是任务桥（bridges.json 任务 provider → runner →
契约校验 → explain 产物）的唯一消费者。移除它们后，任务机整体失去消费者：
`runner/teacher/contracts/providers(jobs)` 五模块、`POST /ai/{operation}`、
`GET /ai/jobs`、`GET /explain`、`GET /ai/task-providers`（按钮门槛端点）、
CLI `ai` 子命令一并退役。**对话桥完整保留**：会话、页面上下文、
provider 锁定、结构化动作（replace_practice_selection）、
`wb bridge add`（conversation provider 的 overrides 通道）不动。

## What Changes

- 删除任务机五模块与 `pool.explain_dir()`；conversations 不受影响
  （只用 `pool.jobs_dir()` 路径助手存 conv-###）。
- API 删四路由四 handler；CLI 删 `ai` 子命令（`bridge add` 保留）。
- 前端删讲解/诊断按钮、任务状态/结果容器及全部门槛与轮询逻辑
  （闪卡 card-nav、判分横幅不涉）。
- 测试：整删 test_teacher/test_contracts/test_jobs/test_providers；
  方法删 test_api×3、test_cli×3、test_conversation_api×1（task-providers）、
  JS 交互套件 one-click 用例×1。
- 文档同步：PRODUCT-MANUAL 8 章、ACTION-GRAPH 各层、GLOSSARY 条目处置。

## Capabilities

### Modified Capabilities

- `ai-teacher-bridge`：REMOVED——Task lifecycle、Output-contract validation、
  Explain operation、Teacher conduct contract、Diagnose operation、
  Practice-page one-click tasks、Bridge artifact locations（任务产物条款）；
  MODIFIED——Purpose（收窄为对话桥）、Provider configuration（bridge add
  仍为 provider 配置 CLI）、CLI is a data interface（去任务措辞）、
  Workbench operates without AI（降级语义改为对话不可用）。

## Impact

代码：`workbench/bridge/`（-5 文件）、`workbench/server/api.py`、
`workbench/server/app.py`、`workbench/cli/main.py`、`workbench/server/pages.py`、
`workbench/server/static/workbench.js`、pool 模块（explain_dir）、测试如上。
对话链路（conversations/conversation_providers/agent_context）零改动。
`.lessonkit/explain/`（空目录）删除。GLOSSARY / PRODUCT-MANUAL /
ACTION-GRAPH 随本变更同步。
