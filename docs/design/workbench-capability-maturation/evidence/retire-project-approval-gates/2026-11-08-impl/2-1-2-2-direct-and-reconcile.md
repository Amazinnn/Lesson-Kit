# WP03 2.1/2.2 实现证据（2026-11-08）

## 2.1 Bridge action/提示词直执行

- `_apply_paper_update_action`（`workbench/bridge/conversations.py`）：`_store_answer` 遇 `paper_update_proposal` 时直接走 Data 既有路径——`_paper_update_preview` 校验真实输入并产出当前 confirmation，`practice_sets.update_saved` 在**真正提交点**再次校验 confirmation；成功在 action 上记 `result`（practice_set_id/title/applied_problem_ids），失败如实记 `error`，零审批状态、零派发暂停。无页面参与即完成；目标历史/其他 Paper 保留（`update_saved` 语义不变）。
- `_prepare_paper_approval` 删除；`resolve_paper_approval` 与 HTTP 路由暂留至 2.3 与 UI 一同退役（过渡期对无 pending 的回调返回 409，测试已钉）。
- 回执行：`_notice_outcome` 对已应用的更新产出"已直接应用"提示，Agent 下一轮如实报告；不重复提交。
- 提示词同步：`_prompt`（"服务端校验输入后直接应用，无需学生批准"）与 `agent_contracts.py` actions 主题（"applies the update directly; there is no separate approval click"）。wire 类型名 `paper_update_proposal` 保持不变（兼容既有 agent 习惯与解析）。

## 2.2 存量 pending approval 一次性迁移

- `_reconcile_legacy_paper_approvals(pool, record)`：按 turn 顺序扫描 `paper_approval.status=="pending"` 的遗留记录：
  1. `_paper_update_preview` 重验当前目标；异常（目标不存在/输入失效）→ status `invalid` + 如实错误；
  2. 预览 confirmation 与记录不一致（目标已变化或上次写入后状态翻转丢失）→ `invalid` + "记录的预览已过期…未执行写入"；
  3. 一致 → `update_saved(stored confirmation)` 原身份执行一次，成功记 `applied`+`resolved_at`，提交点冲突如实记 `invalid`；
  4. 处理后写回 turn；随后按 `_approval_pause_for_retained` 重新计算 `queue_paused`（遗留暂停只在有保留排队消息时延续）。
- **至多一次写入的双保险**：状态翻转（pending→applied/invalid）落在 turn 文件；即使翻转丢失，重放也会撞上"写入后 confirmation 必然变化"→ 走分支 2 零写入；`update_saved` 的 `next_plan==current` 幂等分支再兜一层。
- 接入点：`get()`（服务打开旧会话，FLOW-02）、`start_turn()`、`interrupt_pending()`（遗留 pending 不再阻断派发，live delta 场景）。`list_sessions` 只读不迁移。

## 红绿证据

- 红基线：`2026-11-08-baseline/1-3-failing-checks.txt`（4 失败钉住缺口，1 护栏绿：已决议回调当时代码就不写）。
- 绿：`test_direct_paper_actions.py` 5/5（直执行无审批无暂停、缺卷如实失败零写入、迁移一次执行+重开不重写、缺目标记未完成、陈旧回调零写入）；`test_paper_approval.py` 重写为直执行契约 8/8（含提交点重验失败零写入、遗留 409、无 pending 投影）；`test_agent_queue.py` 改写"legacy pending 不阻断 send-now"。
- 全仓 workbench 套件 1490 passed（0:09:37），无其他回归。
