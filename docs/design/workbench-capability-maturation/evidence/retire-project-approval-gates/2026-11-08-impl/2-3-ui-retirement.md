# WP03 2.3 UI 撤除证据（2026-11-08）

环境：daemon 3123（`source_root`=主检出）+ wb64 隔离工作区 + wb64-fake 协议忠实 provider（真实 bridge/HTTP/Data 链路）；Playwright。

## 撤除代码面

- `workbench.js`：删审批卡渲染（`aiRenderPaperApproval`/`aiPaperApprovalDetails`/`aiRenderPaperProposalHistory`/`aiSetPaperApprovalOwner`/`aiDecidePaperApproval` 及 297 行相关函数）、composer 替换接线、队列暂停的审批门（`approvalPending` 三处：snapshot/continue 按钮/队列状态句）、`ai-send`/`continue` 的审批守卫；重做（records-center replay）改为单次 `POST /practice/runs/N/replay {replace: true}`，删第二次 `window.confirm`。
- `agent-ui.js`：删 `confirm` composer 替换机制及 slot；`restoreComposer` 仅恢复输入行；state 清理。
- `pages.py`：删 `#ai-paper-approval` section 与 `#ai-approval-slot`。
- `api.py`/`app.py`/`surface.py`：`ai_paper_approval` 处理器与 `POST /paper-approval` 路由退役（404）。
- `agent-ui.css`：删 70 行审批规则。
- `conversations.py`：删死块 `_invalid_paper_approval`/`_sync_paper_approval_action`/`_approval_response`/`resolve_paper_approval`（179 行）。
- 静态面净删 494 行（workbench.js 362 + agent-ui.js 58 + agent-ui.css 74，numstat 实计）+ bridge 215 行。

## 浏览器实测（Playwright，daemon 3123，隔离 wb64）

| 项 | 证据 | 结果 |
|---|---|---|
| FLOW-01 打开/刷新：旧审批动作无页面执行 | 新会话新 proposal（真实 bridge）→ Apply 后 `#ai-paper-approval` 不在 DOM、`#ai-approval-slot` 不在 DOM、正文无「批准更新/取消更新/待确认/等待确认」、无 proposal 历史卡；ps-001 题序真实翻转 | PASS |
| FLOW-01 重做直执行（学习者正常入口） | 完成页「再练一次」→ 直接到 setup，`window.confirm` 间谍零调用 | PASS |
| FLOW-02 存量 pending 迁移（浏览器） | 向 conv-001 注入合法 legacy pending（confirmation 对准当态）→ 浏览器重开：卷序复原、turn-003 `paper_approval.status=applied`、queue_paused 解除、UI 零审批元素；**第二次重开**：卷序不变、状态仍 applied、resolved_at 未动（至多一次） | PASS |
| 旧对话重开 | conv-001 重开：无审批卡、无待确认措辞、历史渲染正常（2 user 气泡 + 工具输出折叠区在） | PASS |

## node 契约

- `agent_session_ui.test.js` 49/0：legacy pending 渲染无审批卡、不阻断发送、无 decision POST；history 卡全退役。
- `agent_ui_v1.test.js`：shell 无 slot、无 confirm 导出。
- `workbench_ui_interactions.test.js` 129/0（新增 1）：records-center replay = 单次 POST `{replace:true}`、零 window.confirm。
- 全仓 `pytest 1583 passed`（含 `test_ui_routes`、`test_grading_session_isolation` 白名单更新）、node 套件注册 12 passed、每个 `*.test.js` 单跑 0 fail。

## 未运行

- 记录中心「重做」按钮带活动轮次冲突的浏览器点击（临时工作区没有归档行+活动轮的组合，首轮完成被续用）；handler 契约由 node DOM 测试钉住（单次 POST replace:true、无 confirm），学习者正常入口的直开已在浏览器实测。
- 真实触觉设备。
