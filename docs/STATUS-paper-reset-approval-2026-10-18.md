# 试卷进度重置审批：开工前决定（2026-10-18）

本轮仅确认需求与更新 `complete-agent-message-lifecycle` 的 proposal/design/specs/tasks，未实现代码、改变真实数据或归档 change。Glossary 已明确 Paper 审批与现有回滚审批的输入区规则不同；Product Manual、FILE_CONTRACT 和 Action Graph 的实际交付更新留在实施任务中，不将拟议功能写成已上线。

用户通过提问工具逐项确认：Agent 只提方案，由用户点击审批卡、页面调用现有更新接口；待审批暂停 B/C，批准或取消后仍手动继续；旧影响失效时不写入，刷新影响并再次确认，无需重新问 Agent；刷新/关闭后重开恢复待审批卡和暂停状态；输入区保持可用，新消息加入暂停队列。

复用现有 Paper preview/update、turn/conversation JSON、队列暂停与审批呈现。关键实现边界是先持久保存待审批状态并暂停队列，再释放 A 的 worker；现有 CLI confirmation 只是快照校验，并不能证明用户点击过批准。不新增调度服务、数据库、通用权限框架或所有工具的审批门。保留 Paper ID、题目实体、历史作答/评分和其他卷的进度。

已有消息可靠性、右栏和队列实现保持各自所有权。本轮剩余实施/验收任务保持未勾选；本轮验证仅为严格 OpenSpec 和文档 diff 检查，不宣称产品验收完成。
