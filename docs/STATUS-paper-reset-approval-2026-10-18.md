# 试卷进度重置审批：设计与交付（2026-10-18）

开工前先确认需求并更新 `complete-agent-message-lifecycle` 的 proposal/design/specs/tasks，明确 Paper 审批与回滚审批的输入区规则不同。随后经用户授权实施，交付记录见下。

用户通过提问工具逐项确认：Agent 只提方案，由用户点击审批卡、页面调用现有更新接口；待审批暂停 B/C，批准或取消后仍手动继续；旧影响失效时不写入，刷新影响并再次确认，无需重新问 Agent；刷新/关闭后重开恢复待审批卡和暂停状态；输入区保持可用，新消息加入暂停队列。

复用现有 Paper preview/update、turn/conversation JSON、队列暂停与审批呈现。关键实现边界是先持久保存待审批状态并暂停队列，再释放 A 的 worker；现有 CLI confirmation 只是快照校验，并不能证明用户点击过批准。不新增调度服务、数据库、通用权限框架或所有工具的审批门。保留 Paper ID、题目实体、历史作答/评分和其他卷的进度。

## 实施与验收

后端、界面和对应契约已实现，独立审查未发现 Critical/Important 问题。相关 Python conversation/API/action/surface 检查 115 项通过，最终审批测试 8 项、界面聚焦测试 5 项、全部 Node 229 项通过；compileall、extract-problems guard 和严格 OpenSpec 校验通过。

[PR #148](https://github.com/Amazinnn/Lesson-Kit/pull/148) 源码 CI 在 Python 3.11/3.12 均为 1078 passed、1766 subtests passed（run 39106077715）。CLI 已归档 `complete-agent-message-lifecycle` 并同步 live specs，归档后严格校验 23/23；最终文档提交及合并提交的 CI 结果以该 PR/Actions 为准。

隔离真实 Chromium 走查覆盖 A 提案后 B 暂停、输入可用、较新草稿令旧批准零写入并刷新影响、同一右栏导航/刷新恢复、新消息继续排队、禁止提前继续、批准后仅目标卷重置、取消零写入、手动继续及单 worker。夹具中的题目、历史学习记录和其他卷进度前后相同。测试未写真实课程库、未调用真实 provider；不将夹具验收描述为真实 provider 验收。
