# complete-goals-loop 提案

## Why

所有者 2026-08-29 问卷与追问（DISCUSSION-RECORD 专题 21 第 5/6 条、队列③）：
目标功能两处断点——① 目标卡片**只能创建不能改不能删**（API 的 PATCH/DELETE
早已存在，界面没有入口，所有者原话「非常 frustrating」）；② 设定目标时有些
字段用户处理不了（比如筛选哪些知识点归属这个目标），需要**自然语言输入 →
Agent 代填字段**，且结果**版面原位呈现**（融入型动作，非对话流内）。
另按问卷 B1/B2 口径，Agent 侧需要 goals 的 CLI 读写通道。

## What Changes

- **目标卡编辑/删除**：卡片加「编辑/删除」入口——编辑把字段载回同一张表单
  （提交走 PATCH），删除带确认（走 DELETE），完成即时刷新。表单复用，无新
  界面模式。
- **自然语言助填**：目标表单区加「一句话让 Agent 帮你填」输入——作为对话
  轮次发出（带 `goal_intent` 显式意图）；Agent 回复可附 `prefill_goal_form`
  结构化动作（服务端按意图门与字段契约校验，普通对话绝不代填），客户端把
  title/kind/deadline/description **原位填进表单**，用户确认后才提交——
  创建仍是人的动作。无 provider 或无活动会话时如实提示（切换到 Agent 选择
  视图），不装可用。
- **goals CLI**：`goals list/add/update/rm`——纯数据接口（21→22 命令），
  Agent 依 B1 口径直接读写。
- 对话动作机制扩展：`_prompt` 说明第二种动作类型；`_extract_action` 双类型
  分支（practice_intent → replace_practice_selection 不变；goal_intent →
  prefill_goal_form 新增，字段白名单校验）。

## Capabilities

### Modified Capabilities

- `calendar-workload`：新增「目标生命周期管理」条款（创建/编辑/删除全在
  练习页学习安排区完成；删除需确认；空态诚实）。
- `ai-teacher-bridge`：新增「目标表单助填动作」条款（goal_intent 门控、
  字段契约、原位应用、提交留给人；普通对话不得代填）。

## Impact

代码：`workbench/server/pages.py`（卡片按钮 + NL 输入 + 编辑态）、
`workbench/server/static/workbench.js`（编辑/删除/助填/aiApplyAction 扩展）、
`workbench/server/context.py`（goal_intent）、`workbench/bridge/conversations.py`
（_prompt/_extract_action 双动作）、`workbench/cli/main.py`（goals 子命令）、
测试两侧。行为兼容：既有创建流不变；无 AI 时助填如实降级。
文档同步：PRODUCT-MANUAL 2.1/5 章、ACTION-GRAPH（L2/L3/L4 + 队列③状态）。
