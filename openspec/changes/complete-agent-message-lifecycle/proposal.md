## Why

可靠消息接收、失败历史与 Tool Call Card 由 `preserve-agent-messages-and-tool-outcomes` 独立负责；队列与中断行为由 focused change `queue-agent-messages-and-interrupt` 拥有。本 change 保留同工作区右栏导航和既有审批交互。HTML 功能演示不是美学设计标准。

本 change 使用已定义的 Agent Artifact、Approval Gate；队列与中断合同以 focused change `queue-agent-messages-and-interrupt` 为准。

## What Changes

- 可靠消息接收、失败历史、重试与 Tool Call Card 归 `preserve-agent-messages-and-tool-outcomes`。
- 队列顺序、中断、恢复与运行中发送偏好由 `queue-agent-messages-and-interrupt` 定义。
- 中间页面仅切换中间内容，保留右栏实例、会话、输入草稿、滚动和运行活动。
- 将试卷更新中已确认的影响审批接入既有审批机制；保留现有回滚门禁。
- Activity Float/Bottom Dock 的任务进度呈现与收起行为由独立 change `use-collapsible-agent-activity-float` 定义；本 change 不拥有该 UI 行为。
- 只补功能，不复制 HTML 的调参器、预设和美学细节。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-ui`: persistent conversation rail and existing supported approval controls.

## Impact

Reuse existing conversation/turn JSON, provider workers and cancellation, activity normalization and Agent surface components. Thin server/CLI paths delegate to Bridge/Data authorities. Queue artifacts and settings are documented by `queue-agent-messages-and-interrupt`; this change owns rail navigation and approval documentation. Do not fabricate provider-native pause/resume capability or automatically replay partially committed writes.
