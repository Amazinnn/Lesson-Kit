## Why

当前发送失败或 Agent 执行失败后，用户消息可能在重新加载时消失；切中间页面会重建右栏并退回对话列表。HTML 功能演示也尚未完整落地，但所有者明确它不是美学设计标准。需要先修可靠消息、持久右栏与单轮执行，再补真实可操作的工具/失败/审批交互。

本 change 使用已定义的 Pending Message、Interrupt and Send、Tool Call Card、Agent Artifact、Approval Gate。所有者已纠正此前的“并发”措辞：一个对话同一时刻只执行一个任务，新消息排队或显式中断后发送。

## What Changes

- 在可靠接收时持久化用户消息；失败、取消、刷新、切页都不吞消息。区分未接收、提交状态未知、已接收但执行失败，避免盲目重发。
- 默认运行中发送进入队列，另可中断后发送；默认策略可在设置中修改。任务失败暂停队列；中断原任务处理新消息后，原任务不续、旧队列仍暂停。
- 中间页面仅切换中间内容，保留右栏实例、会话、输入草稿、滚动、运行活动和队列。新提交消息随当前页面上下文，已提交的上下文不变。
- 补齐统一 Tool Call Card、失败摘要/实际影响/折叠诊断及真实支持的恢复操作；将试卷更新中已确认的影响审批接入既有审批机制。
- 短/长任务进度都只用右上角 Activity Float，退役遮挡中间页面的 Bottom Dock；增加小型展开/收起按钮，收起后保留可重新打开的控制。
- 只补功能，不复制 HTML 的调参器、预设和美学细节；不引入同一对话多任务并行或自动续原任务。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ai-teacher-bridge`: reliable user-message acceptance/history, single-worker queue and interruption/recovery lifecycle.
- `workbench-ui`: persistent conversation rail, outgoing/queued/failed-message UI, configurable running-message policy and supported recovery/approval controls.

## Impact

Reuse existing conversation/turn JSON, provider workers and cancellation, activity normalization and Agent surface components. Thin server/CLI paths delegate to Bridge/Data authorities. Update persisted conversation artifacts in FILE_CONTRACT, settings ownership, Architecture, DATA_MODEL where affected, Product Manual, Action Graph and live OpenSpec in the implementation PR. Do not fabricate provider-native pause/resume capability or automatically replay partially committed writes.
