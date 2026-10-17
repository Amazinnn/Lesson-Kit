## Why

可靠消息接收、失败历史与 Tool Call Card 由 `preserve-agent-messages-and-tool-outcomes` 独立负责。本 change 保留其余生命周期范围：队列与中断策略、同工作区右栏导航和既有审批交互。HTML 功能演示不是美学设计标准。

本 change 使用已定义的 Pending Message、Interrupt and Send、Agent Artifact、Approval Gate。所有者已纠正此前的“并发”措辞：一个对话同一时刻只执行一个任务，新消息排队或显式中断后发送。

## What Changes

- 可靠消息接收、失败历史、重试与 Tool Call Card 归 `preserve-agent-messages-and-tool-outcomes`。
- 默认运行中发送进入队列，另可中断后发送；默认策略可在设置中修改。任务失败暂停队列；中断原任务处理新消息后，原任务不续、旧队列仍暂停。
- 中间页面仅切换中间内容，保留右栏实例、会话、输入草稿、滚动、运行活动和队列。新提交消息随当前页面上下文，已提交的上下文不变。
- 将试卷更新中已确认的影响审批接入既有审批机制；保留现有回滚门禁。
- Activity Float/Bottom Dock 的任务进度呈现与收起行为由独立 change `use-collapsible-agent-activity-float` 定义；本 change 不拥有该 UI 行为。
- 只补功能，不复制 HTML 的调参器、预设和美学细节；不引入同一对话多任务并行或自动续原任务。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ai-teacher-bridge`: single-worker queue and interruption/recovery lifecycle.
- `workbench-ui`: persistent conversation rail, configurable running-message policy, and existing supported approval controls.

## Impact

Reuse existing conversation/turn JSON, provider workers and cancellation, activity normalization and Agent surface components. Thin server/CLI paths delegate to Bridge/Data authorities. Update persisted conversation artifacts in FILE_CONTRACT, settings ownership, Architecture, DATA_MODEL where affected, Product Manual, Action Graph and live OpenSpec in the implementation PR. Do not fabricate provider-native pause/resume capability or automatically replay partially committed writes.
