# 2026-11-01 — Agent 对话区简化与修复（agent-chat-simplify）

分支 `codex/agent-chat-simplify`（自 `main@55ee5cee`）。响应所有者 2026-11-01 反馈：
工具卡「影响未知」无用、标语组件泛滥、出错不可见、对话与答题字体过小、输入框被挤在
左侧随输入变宽、Enter 无法发送、审批卡重复出现、审批处理完后消息仍静默入队。

## 根因与修复

- **Enter 失效 + 输入框贴左变宽（同根因）**：`live-editor.js` 接管了 `#ai-input`，
  真实 textarea 被 `display:none`，替换为无宽度规则的 CodeMirror 容器，且 CM 按键层
  消费 Enter。修复：composer 加 `data-plain-text` 退出实时编辑（既有 keydown 逻辑
  即恢复 Enter/Ctrl+Enter 发送、Shift+Enter 换行、满宽布局）。答题框等其余输入保留
  实时 Markdown。`source-preserving-live-markdown` change 的 scope 同步移除
  "Agent input"。
- **审批后仍入队**：`resolve_paper_approval` 全路径置 `queue_paused=True` 且无人清除。
  修复：决议落盘后，若无 pending 审批且队列为空则解除暂停（新消息按当前发送方式直发）；
  队列有遗留消息则维持暂停。spec 同步改为"暂停保护的是遗留排队消息，不是空队列"。

## 退役与新增

- 退役：工具卡 impact 行整组件（含「已知影响」；W-89/W-90 冻结裁决由所有者推翻并登记
  于 copy-table）；对话流 pending 审批重复卡；side-label（对话/选择 Agent/待处理消息/
  试卷更新待确认）；常态解说句（queue-status 常态句、恢复卡教学尾巴、审批默认句）；
  中栏 kicker（Agent 活动/正在处理/工件/最新工件）；上下文 chips；输入 placeholder。
  保留：`#ai-status` 状态栏全部文案、错误/失败/暂停/中断交接（`#ai-handoff-status`，
  spec 要求的 interrupt 独立状态显示）文案。
- 新增：`.wb-collapse` 长卡虚化折叠（阈值 320px，悬浮箭头，命中区 ≥44px，aria-expanded，
  焦点环不裁）。AI 气泡默认展开，工具卡输出/审批详情/恢复卡默认收起；工具卡输出块从
  `<details>` 换为带 `role="region"` 的折叠宿主。
- 字号：对话气泡与输入 14→16px、`#paper-answer` 14→16px、`#ai-status` 11→12px、
  候选区 12→13px。

## 文档

PRODUCT-MANUAL（8.4/8.5/导航句）、ACTION-GRAPH 变更留痕、copy-table 裁决推翻记录、
`agent-part-grading` 之外的三个 change 工件（agent-chat-simplify 新增；
source-preserving-live-markdown / workbench-component-forms 修订）。

## 验收

见 change `tasks.md` 第 6 组；全套 pytest/node/compileall/openspec/guard 与真实浏览器
走查记录在实施对话中回填。
