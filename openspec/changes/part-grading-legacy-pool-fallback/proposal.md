# 未迁移池的批改退化路径

## Why

`agent-part-grading` 上线后，真实工作区池没有跟上：22 个注册工作区里 **19 个缺少**
`part_attempt_context` / `part_grading_revisions` / `part_grading_jobs` 三张表与
`problems.parts`、`problem_attempts.part_id/content_revision` 列（只有测试环境 dmath 迁过）。

在这类池上：

- **读**：打开任意已作答过的卷子时 `part_practice.project()` 调 `part_grading.get()` 查
  `part_grading_revisions`，无守卫 → `sqlite3.OperationalError` → HTTP 500
  “internal error: no such table: part_grading_revisions”（所有者在
  计算机组成 ch02 主观题卷子上实测，attempt#146 原样复现）。
- **写**：`_submit_item` 无条件写 `part_attempt_context`、`part_grading_jobs` 与
  `problem_attempts.part_id/content_revision`，在这些池上会直接抛错——**主观题无法提交**，
  包括本应走“整题”虚拟小问的老题。

现行契约已承诺这种降级：`review-workbench` → `Durable attempt records for every surface`
规定 “Old pools SHALL retain the existing degraded legacy answer-recording path, without
manufacturing part structure or conclusions; new structured grading requires the explicit
additive migration”。实现没做到：读会炸、写会炸，而不是退化。同一功能的
`grading_jobs.owns_conversation` 已有 `sqlite_master` 守卫，说明“按缺失退化”的模式存在，
只是提交与投影路径没覆盖。

## What Changes

- **读路径退化**：缺少批改 schema 时，练习状态投影报告“未请求批改”“无结论”，
  继续按既有整题路径展示，不报错；`part_grading.get/list_revisions`、
  `grading_jobs.target/get`、`part_practice.project` 均在数据层守卫。
- **写路径退化**：缺少 schema 时，主观题提交只写迁移前的既有 Attempt 列
  （`problem_attempts` 原有字段 + 既有 `active_practice_items` 状态），不建 part 上下文/job
  行，也不伪造小问结论；练习流程照常可用。
- **显式批改请求保持明确失败**：`GET/POST /grading`、`lesson-kit grading` 在缺 schema 的池上
  返回可操作的错误（附 `pool/scripts/migrate-progress.py` 迁移命令），绝不静默成功
  （HTTP 层守卫已在本轮早先修复，补齐 CLI/其余写入口）。
- **可见性**：`lesson-kit doctor` 报告哪些已注册池缺少批改 schema，让迁移缺口不再隐藏。
- **数据迁移**：对 19 个未迁移的已注册池执行 `migrate-progress.py`（逐池先备份），
  其中优先 计算机组成（所有者当前正在使用）。

## Capabilities

### Modified Capabilities

- `review-workbench`：
  - `Durable attempt records for every surface` —— 把“未迁移池的退化路径”写成可验收的行为：
    提交只写既有列、状态投影不报错、显式批改请求可操作地失败；四个既有场景保留，
    新增未迁移池提交与状态投影场景。

## Impact

- 代码：`workbench/data/part_grading.py`、`workbench/data/grading_jobs.py`、
  `workbench/data/part_practice.py`、`workbench/cli/doctor.py`（只读检查）。
- 测试：新增“最小旧池”夹具用例（读投影退化、提交退化、显式批改失败可操作）；
  既有全套不得回退。
- 数据/运维：19 个池的显式迁移（先备份，幂等）。
- 文档：`docs/DATA_MODEL.md`（退化路径说明）、`docs/PRODUCT-MANUAL.md`（未迁移池的行为）、
  `changelog/`。
