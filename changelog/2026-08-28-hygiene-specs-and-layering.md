# 卫生债清偿：规格、分层、文档指针

一批已知小债的集中清偿，全部为小改动，行为面只有一处（见下）。

## 内容

1. **补齐两个 spec 的 Purpose**（归档时遗留的 TBD 占位）：
   `openspec/specs/daily-learning-plan/spec.md`、
   `openspec/specs/workbench-content-governance/spec.md`。
2. **AGENTS.md 验证节奏**：`openspec validate review-workbench-v1 --strict`
   指向早已归档的变更（命令必然失败），改为 `openspec validate --specs --strict`
   （已验证：7 个规格全部通过）。
3. **修复 Data→Domain 分层违规**（PR #7 Codex 审查意见）：
   `workbench/data/queries.py` 不再 import `workbench.domain.signals`；
   信号聚合改由 Shell 层（`workbench/server/api.py::graph_model`）经
   `domain.signals.strongest_by_target` 完成后作为 `signal_weights` 参数传入
   `queries.graph_model(pool, signal_weights)`。`docs/ARCHITECTURE.md` 的
   「Data 不 import Domain」边界恢复成立。
4. **每日计划首建即落盘**（PR #5 Codex 审查意见）：
   `daily_plan` GET 在无当日缓存时重建基线后原子落盘（复用 recalculate 的
   tmp+replace 写法，抽为 `_persist_plan`），一天内重复 GET 不再反复重算，
   对齐 daily-learning-plan spec「每日首次打开重算一次」的语义。
5. **过期文档指针**：`docs/REQUIREMENTS.md` 权威需求源改为 `openspec/specs/`；
   `docs/FUTURE-DEVELOPMENT-NOTES.md` 中 `openspec/changes/complete-learning-workbench/`
   改为规格库 + 归档位置。
6. **.gitignore**：`.lessonkit/plan.json`（运行时计划缓存，与 jobs/ 同类）与
   `workbench/_claude_*_task.txt`（临时工作文件）入 ignore。

## 验证

- 全量 pytest 通过（含 graph_model 信号聚合的既有测试改为显式传参后仍绿）。
- `openspec validate --specs --strict`：7 passed, 0 failed。
