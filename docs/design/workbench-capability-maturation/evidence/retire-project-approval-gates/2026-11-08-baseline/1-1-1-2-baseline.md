# WP03 基线与 delta 核对（任务 1.1 / 1.2，2026-11-08）

## 1.1 身份与基线

- 分支 `main`，HEAD `b508995c`；origin/main 已同步（本会话前段完成授权推送）。
- editable 安装 = 主检出（中性 cwd 探针 `import workbench` → `D:\Projects\Academic Workflow\lesson-kit\workbench\__init__.py`；本会话早段纠正过 `.pth` 指向 course-sync worktree 的误装）。daemon 3123 `/api/runtime` 的 `source_root` = 主检出（wb64 隔离环境，WP03 2.3 复用）。
- 已读本包全部工件（proposal/specs×4/design/tasks）、`packages/wp03.md`、execution-guide、contract-reconciliation（CR06 = 本包登记项；CR14 提示核对活跃 change 重叠）、data-exchange-matrix、benchmarks/catalog（FLOW-01/02/03、RELEASE-01/02/03 为本包验收门槛）。
- **重叠 change 核对**：
  - `agent-chat-simplify` 本会话前段已归档（其 workbench-ui delta 与本包 MODIFIED "Existing approval controls…" 的衔接顺序：先简化后退役，live 已含简化版，本包 REMOVED 整体撤除该 requirement）。
  - `workbench-content-governance`（WP02 已归档）已把批次撤销语义改写为"无撤销入口 + 直接修正"——本包 workbench-ui REMOVED "Low-reversibility rollback requires an Approval Gate" 与之衔接：能力入口 WP02 已撤，本包撤其审批门 requirement 本体。
  - `adaptive-paper-content-lifecycle`（活跃）：4affbcb6 已实现"改名单按题目身份协调、不再整卷清零"，其 6.2/6.3（审批退役）明确挂在本包。本包 practice-set-export MODIFIED "Saved Paper updates preserve container identity" 与其 `reconcile_membership` 语义一致（预览/确认是并发 expected-state 守卫，不是审批）。
  - `json-content-repository-sync`、`import-attempts-into-paper-progress` 等活跃 change 与本包无共享 requirement。
- 影响面粗查（与 handoff 一致）：`workbench/bridge/**` 109 处 approval 引用、`workbench.js` 90 处、`surface.py` 5 处路由；迁移目标 = 会话/turn JSON 文件里的 pending approval（`_prepare_paper_approval`/`resolve_paper_approval` 路径），非 SQLite 表。

## 1.2 delta 逐块核对（脚本对比 live，场景保全）

| capability | requirement | 类型 | live 场景数 | delta 场景数 | 保全 |
|---|---|---|---|---|---|
| direct-project-actions | （新能力，4 requirements） | ADDED | — | 6 场景 | live 无同名 capability（25 caps 中无），无静默覆盖 |
| ai-teacher-bridge | Paper update approval pauses conversation dispatch | REMOVED | 5 | 0（REMOVED 携 Reason/Migration） | 随 requirement 整体退役，合规 |
| ai-teacher-bridge | Interrupt-and-send waits for the old turn to stop | MODIFIED | 8 | 8 | 名称逐一保留，两条审批场景改写为"按 direct-project-actions 协调、不再审批阻断" |
| ai-teacher-bridge | Pending messages can be revised or removed before execution | MODIFIED | 11 | 11 | 名称逐一保留，"Send-now is blocked" 同上改写 |
| workbench-ui | Low-reversibility rollback requires an Approval Gate | REMOVED | 4 | 0 | 合规 |
| workbench-ui | Existing approval controls remain truthful and scoped | REMOVED | 10 | 0 | 合规（live 现为 agent-chat-simplify 简化版，本包整体退役） |
| workbench-ui | Agent sending is single-flight and session-bound | MODIFIED | 5 | 5 | 名称逐一保留 |
| workbench-ui | Scrollable Agent conversation | MODIFIED | 2 | 2 | 名称逐一保留 |
| workbench-ui | Content results expose type, source, and rollback state | MODIFIED | 3 | 3 | 名称逐一保留（改为无回滚状态字段/无撤销控件，衔接 WP02） |
| practice-set-export | Saved Paper updates preserve container identity | MODIFIED | 3 | 3 | 名称逐一保留 |

- `openspec validate retire-project-approval-gates --strict` ✓；live specs strict 25/25 ✓（agent-chat-simplify 归档后）。
- 结论：delta 无场景丢失、无对 live 不存在 requirement 的 MODIFIED；可以先更新职责契约再改代码（次级引用的文件同步在 3.1 随实现走）。
