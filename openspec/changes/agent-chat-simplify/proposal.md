# Agent 对话区简化与修复

## Why

用户在真实使用中反馈 8 项体验问题：工具调用卡的「影响未知/已知影响」行无用；对话区注释性标语组件过多、出错后看不出成败；对话与答题打字区字体太小；Agent 输入框被挤在左侧且随输入变长才变宽；Enter/Ctrl+Enter 无法发送；审批卡在对话流与输入区上方重复出现；审批全部处理完后新消息仍被静默塞入暂停队列。

勘察确认两个"体验问题"同根因：`live-editor.js` 接管了 `#ai-input`，把真实 textarea 替换为无宽度规则的 CodeMirror 容器（布局塌缩 + Enter 被 CM 按键层消费）。两个行为问题分别由该根因与 `conversations.py` 的审批暂停语义（含现行 spec 条款）造成。

## What Changes

- **修复**：`#ai-input` 退出实时 Markdown 编辑（加 `data-plain-text`），恢复既有 Enter/Ctrl+Enter 发送、Shift+Enter 换行与满宽布局；`source-preserving-live-markdown` change 的 scope 同步移除 "Agent input"。
- **修复**：审批全部决议且队列为空时自动解除 `queue_paused`，新消息按当前偏好直接发送；队列仍有遗留消息时维持暂停入队。
- **删除**：工具卡 impact 展示组件整体（「影响未知」与「已知影响」都不再显示；失败摘要、detail、状态徽章、输出块保留）；对话流 pending 审批重复卡（已决议历史卡保留）；side-label 小标题、常态解说句、中栏 kicker、输入 placeholder、上下文 chips。错误/失败/暂停等功能性文案与 `#ai-status` 状态栏全部保留。
- **体验**：对话气泡、Agent 输入框、`#paper-answer` 字号提到 16px；候选区小字 12→13px、`#ai-status` 11→12px；新增长卡虚化折叠组件（阈值约 320px，底部渐隐 + 悬浮展开箭头，命中区 ≥44px），AI 气泡默认展开可收，工具卡输出/审批详情/恢复卡默认收起。

## Capabilities

### Modified Capabilities

- `workbench-ui`：
  - `Provider activity cards show evidenced outcomes` —— 卡片不再展示 impact 声明（已知/未知均不展示），失败摘要与输出保留；
  - `Existing approval controls remain truthful and scoped` —— pending 审批只在 composer 卡呈现一次；审批全部决议且队列已空时暂停自动解除；
  - `Running-send preference and pending controls are explicit` —— 空队列暂停不拦截新消息直发；
  - 新增长卡虚化折叠交互 requirement。

### Related change artifact revisions（不改变其 spec 已同步状态）

- `source-preserving-live-markdown`：scope 移除 "Agent input"（Agent 输入框回到纯文本 composer）。
- `workbench-component-forms`：`Tool call card is one line` 及 W-89/W-90 文案裁决按所有者 2026-11-01 新决定修订为「不展示 impact 行」。

## Impact

- 代码：`workbench/server/pages.py`、`static/workbench.js`、`static/agent-ui.js`、`static/workbench.css`、`static/agent-ui.css`、`workbench/bridge/conversations.py`。
- 测试：`agent_session_ui.test.js`、`workbench_ui_interactions.test.js`、`agent_ui_v1.test.js`、`test_ui_routes.py`、`test_conversations.py` 及新增队列语义用例。
- 文档：`docs/PRODUCT-MANUAL.md`（对话区说明与「影响未知」段落）、`docs/ACTION-GRAPH.md`（退役 impact 展示/对话流 pending 审批卡、新增长卡展开交互）。
