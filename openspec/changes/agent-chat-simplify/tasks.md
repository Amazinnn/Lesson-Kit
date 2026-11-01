# Tasks

## 1. Composer 行为修复

- [ ] 1.1 `pages.py` 给 `#ai-input` 加 `data-plain-text`，浏览器确认 Enter/Ctrl+Enter 发送、Shift+Enter 换行、输入框满宽。
- [ ] 1.2 修订 `openspec/changes/source-preserving-live-markdown/` 的 spec/acceptance/tasks：scope 移除 "Agent input"，登记 2026-11-01 所有者决定。

## 2. 队列暂停语义修复

- [ ] 2.1 先写失败测试：审批全部决议且队列空 → 新消息直发；队列有遗留 → 维持暂停入队（`test_conversations.py`）。
- [ ] 2.2 `conversations.py`：`submit_turn` 的 `start_now` 允许 `queue_paused and not order`；`resolve_paper_approval` 成功/取消路径按 design 决策 2 清除暂停；stale/invalid 保持暂停。
- [ ] 2.3 同步前端队列状态文案与 `agent_session_ui.test.js` 相关断言。

## 3. 删除类

- [ ] 3.1 删工具卡 `.ai-plan-impact` 创建/更新/渲染（workbench.js），测试断言反转为元素不存在（`agent_session_ui.test.js:581-614`）。
- [ ] 3.2 删对话流 pending 审批卡渲染，保留历史决议卡；`agent_session_ui.test.js:1351` 区域断言同步。
- [ ] 3.3 删 side-label、常态解说句、`#ai-handoff-status`、恢复卡说明句、审批默认句、中栏 kicker、placeholder、chips；保留错误/失败/暂停文案与 `#ai-status`。
- [ ] 3.4 同步全部受影响测试桩与断言（workbench_ui_interactions/agent_session_ui/agent_ui_v1/test_ui_routes）。

## 4. 体验类

- [ ] 4.1 字号批次：对话气泡/输入框/`#paper-answer` 16px，`#ai-status` 12px，候选区 13px。
- [ ] 4.2 `.wb-collapse` 组件（CSS+JS 初始化，320px 阈值，气泡展开、工具输出/审批详情/恢复卡收起，≥44px 命中区+焦点环+aria-expanded）。
- [ ] 4.3 工具卡 output `details` 改用 `.wb-collapse`；node 用例覆盖展开/收起与默认态。

## 5. 契约同步

- [ ] 5.1 修订 `openspec/changes/workbench-component-forms/`：`Tool call card is one line` 去掉 impact 展示，acceptance SC-26、tasks 6.3/6.6、copy-table W-89/W-90 登记裁决推翻。
- [ ] 5.2 `docs/PRODUCT-MANUAL.md` 对话区章节（删「影响未知」表述、审批单卡、队列新语义、字体/折叠交互说明）。
- [ ] 5.3 `docs/ACTION-GRAPH.md` 登记退役与新交互。

## 6. 验收

- [ ] 6.1 `python -m pytest tests -q`、`node --test` 全套件、`python -m compileall -q lessonkit.py workbench pipeline pool tests` 全绿。
- [ ] 6.2 `openspec validate --specs --strict` 通过。
- [ ] 6.3 `python lessonkit.py guard extract-problems --course dmath --chapter ch06` PASS。
- [ ] 6.4 真实浏览器验收：Enter/Ctrl+Enter 发送、Shift+Enter 换行、满宽输入框、无影响行、审批单卡、空队列审批后直发、三类长卡折叠/展开、`#ai-status` 可见；临时 workspace，不写真实学习记录。
