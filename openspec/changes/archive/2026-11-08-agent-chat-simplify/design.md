# Design

## Context

- `live-editor.js` 的 `kv()` 扫描 `textarea:not([data-plain-text])` 并整体替换为 CodeMirror 容器；`#ai-input` 被替换后失去 `flex:1` 满宽（`#ai-input-row > * { min-width:0 }` 放任收缩），且 CM 按键层消费 Enter。`workbench.js:5481-5486` 的既有 keydown 处理本身已满足 Enter/Ctrl+Enter 发送、Shift+Enter 换行。
- `conversations.py`：`resolve_paper_approval` 全路径置 `queue_paused=True`（成功批准 :1847、取消 :1763、stale :1752-1755）；`submit_turn` 的 `start_now`（:922-929）要求 `not queue_paused`；只有 `continue_queue`（:1251）与新的 interrupt 能解除。`_finish` 的 interrupt 分支（:2115-2118）已有"空队列不保持暂停"的先例语义。
- 字号现状：`#ai-messages .msg` 14px（`workbench.css:2599-2600` 覆盖基类 16px）、`#ai-input` 继承 14px、`#paper-answer` 无覆盖 14px、`#answer-box` 16px（:2889-2897）。
- 契约现状：`workbench-ui:1401`（impact 展示）、`:1416`（running-send）、`:1484`（审批暂停）三处 requirement 被本 change 修订；`source-preserving-live-markdown`（活跃 change）scope 含 "Agent input"；`workbench-component-forms`（活跃 change）W-89/W-90 与 `Tool call card is one line` 计划展示 impact。

## Goals / Non-Goals

**Goals:**
- 恢复 composer 原生键盘与布局行为；修正审批后队列语义；删除装饰性标语与重复审批卡；提升对话/打字可读性；统一长卡折叠交互。

**Non-Goals:**
- 不改后端 impact 数据的产出与存储（`check-ingest` 仍带 `impact` 字段，`test_conversations.py:1502` 不动）；
- 不改答题框/备注/目标描述的实时 Markdown 编辑；
- 不动发送方式设置项（`runningSendAction` 两种取值不变）；
- 不新增通用审批门。

## Decisions

1. **composer 退实时编辑用属性开关**：`pages.py` 给 `#ai-input` 加 `data-plain-text`。替代方案（给 `.lk-live-editor` 补 flex 样式 + 改 CM keymap 桥接）被否：桥接无法表达"Enter=发送"且要维护两套按键语义；属性开关是 live-editor 自带的退出通道，一行生效。
2. **队列暂停语义**：暂停保护的是"遗留排队消息"。实现落点只在 `resolve_paper_approval` 的成功/取消路径——决议落盘后，当 `_pending_paper_approval(folder) is None and not _queue_order(folder, conversation)` 时清除 `queue_paused`（对齐 `_finish` 的 interrupt 先例）。`submit_turn` 的 `start_now` **不动**：若允许"暂停且队列为空即直发"，会在 interrupt 交接（waiting_for_stop 不入队）窗口绕过停顿保护，产生双跑风险；审批驱动的暂停由审批决议自己解除即可满足 spec。stale/invalid 路径保持暂停（审批尚未真正决议）。
3. **impact 展示整体移除**：删 `.ai-plan-impact` 的创建、语义更新与渲染；provider 不产出 impact 的既有约束（`test_conversation_providers.py:539`）不变。W-89/W-90 冻结裁决由所有者 2026-11-01 决定推翻，在 `workbench-component-forms/design-notes/copy-table.md` 登记推翻记录，不改历史条目本身。
4. **对话流审批卡**：仅删 `record.pending_paper_approval` 的 in-flow 渲染分支（workbench.js:3856-3871 一带）；`ai-paper-approval-history-*`（已决议）保留。composer 卡 `#ai-paper-approval` 不动。
5. **删除清单**（标注保留项）：side-label「对话/选择 Agent/待处理消息」、`#ai-queue-status` 的"当前回复结束后按顺序发送…"句、`#ai-handoff-status` 整元素、恢复卡说明句、审批卡默认句「确认前不会修改试卷…」、中栏 kicker（「Agent 活动/正在处理」「工件/最新工件」）、placeholder「输入问题」、上下文 chips（`agent-ui.js:81-93` + `pages.py:1179`）。保留：`#ai-status` 全部文案、错误/失败/暂停态文案（"队列已暂停""试卷更新待确认"两句、失败摘要、发送失败提示）。
6. **字号**：只覆盖目标控件（`#ai-messages .msg` 16px/24px、`#ai-input` 16px、`#paper-answer` 16px、`#ai-status` 12px、候选区 13px），不动全局 token 与 body 基线。
7. **虚化折叠组件**：`.wb-collapse`（容器）+ `.wb-collapse.is-collapsed`（`max-height` + `mask-image` 底部渐隐）+ `.wb-collapse-toggle`（绝对定位悬浮 chevron 按钮，视觉小、padding 撑出 ≥44px 命中区，`aria-expanded`，焦点环不裁）。JS 侧统一初始化函数按卡型给默认态：AI 气泡展开、工具卡输出/审批 details/恢复卡收起；工具卡现有 `details.ai-plan-output` 改用该组件。阈值 320px 常量，避免逐卡配置。

## Risks / Trade-offs

- node 测试桩以元素 id 表驱动：删元素必须同步桩表，否则分支静默跳过（已知坑，验证阶段逐套件跑）。
- `queue_paused` 语义变化影响 `agent_session_ui.test.js` 的恢复卡与队列用例；新语义用例先写失败测试再实现。
- 虚化折叠依赖 `mask-image`，旧浏览器降级为直接截断（可接受，仍可展开）。
