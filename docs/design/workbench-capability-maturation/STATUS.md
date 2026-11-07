# 规划交接状态

## 2026-11-07 接力第二棒（Codex 暂停后）

实际实现仍在 `D:\.codex\worktrees\course-sync\lesson-kit` 的 `codex/course-sync`，原 main 工作区未接收。本轮完成 `3c15a893`（学习偏好浏览器消费与 surface/L2/GLOSSARY/手册/动作图登记）、`cae8215d`（接收端：共同基线=本机接收确认，`apply_exchange` 逐单元提交、失败隔离、显式删除）与 `18d3abca`（执行重建：active 运行与 parked 检查点、单项补丁、generation tombstone）。接力前 Node 脏检查已全绿；定向回归 91 项 pytest 通过。

仍未完成：接收端既有 writer 校验接线、CLI/Git 编排与每小时计划任务、Tutor 交接与免费 LLM 回写、benchmarks 与发布级验收。`tasks.md` 2.3–2.10、3.1–3.6 保持未勾选，只有实际证据才能勾选。继续顺序见交接文档末尾的「接力记录」。

## 2026-11-07 实现暂停

用户因 Codex 额度要求暂停并移交其他 Agent。实际实现位于 `D:\.codex\worktrees\course-sync\lesson-kit` 的 `codex/course-sync`，原 main 工作区尚未接收实现。当前仅 WP01 在推进，完整同步 CLI 与接收端尚未交付。

接力先读 [暂停与实现交接](HANDOFF-2026-11-07.md)，其中记录提交、未完成工作、worker 终态、真实检查和继续顺序。P01 偏好接线为半成品，Node 检查仍有失败，不能直接发布。已停止本轮外部 workers，产物和任务书保留。

下文“规划 v1”是此前设计阶段记录，不能当作当前实现状态。

## 2026-11-07 规划 v1

103 个有效回答已收口，用户提供学习协议 V3.1 的新增范围已纳入。近期正常路径是外部 Tutor 使用课程文件、本地 CLI 接收回写。完整课程交换首包包含目标、范围、资料、理解/误解、总结与教学续接文件，另含内容、试卷、附件、原件、学习事实、草稿和已保存偏好。

形成六个独立 change 的 proposal/specs/design/tasks，以及实施入口、决策追踪、契约矩阵、数据矩阵、工作包卡、固定 benchmark 和实际操作场景。原审批默认直接通过，显式成功批次撤销退役，独立有效修改先完成。首包开始时直接采用其 tasks，按当前 checkout 重新核对契约和资产清单。

## 本轮验证

- 六个 change 的 strict 校验通过。
- 当前 live specs 21 项 strict 校验通过。
- 文档相对链接检查、UTF-8读取、103问主题合计及 diff whitespace 检查通过。
- 16 个 MODIFIED requirement 保留共 87 个原场景名称，退役条款通过 REMOVED 显式迁移。

## 真实完成度

本轮完成文档规划。未运行实现测试、真实浏览器、免费LLM、真实Git同步、定时任务或课程数据迁移。benchmarks/catalog 的性能及体验数值为工程制定的目标，全部待实际测量。不能从工件齐全和严格校验推断功能已实现。

存量测试曾有 Pi 编码相关失败，历史证据见 evidence.md；正式实现和验收需在实际环境完整重跑，不能引用本轮文档检查替代。原生 Provider 会话迁移边界按 Q014，课程可读续接已纳入首包。安装与活跃分支的事实在执行入口必须重新核查。

## 后续交付入口

先读 README 与 execution-guide，再进入 expand-file-mediated-course-sync 的完整任务。其他包按 work-packages 依赖推进。每包独立实测、独立验收、精简交付，详细证据完整保留。
