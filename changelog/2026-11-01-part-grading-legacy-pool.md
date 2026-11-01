# 2026-11-01 — 未迁移池的批改退化路径（part-grading-legacy-pool-fallback）

`agent-part-grading` 上线只迁移过测试环境 dmath；22 个注册工作区中 19 个池缺
`part_attempt_context` / `part_grading_revisions` / `part_grading_jobs` 与
`problems.parts`、`problem_attempts.part_id/content_revision`。所有者在
计算机组成 ch02 主观题卷子上遇到 “internal error: no such table:
part_grading_revisions”。

## 根因

- 读：`part_practice.project()` 无守卫读 `part_grading_revisions` / `part_grading_jobs`；
- 写：`_submit_item` 无条件写 part 列与 part 表 → 未迁移池上主观题无法提交；
- 违反 spec：`review-workbench` → `Durable attempt records for every surface`
  要求旧池保留退化整题路径。

## 修复

- `workbench/data/part_grading.py`：`missing_schema(conn)`（诊断用）、
  `has_revisions(pool)`（只读存储）、`has_schema(pool)`（完整存储，per-request 缓存）、
  `SchemaMissing(ValueError)`；`get/list_revisions` 在缺表时返回 `None/[]`。
- `workbench/data/grading_jobs.py`：`target` 缺存储时抛 `SchemaMissing`（含迁移命令），
  `get` 返回 `None`。
- `workbench/data/part_practice.py`：`project()` 缺存储时不读批改表，状态保持
  `not_requested`；`_submit_item` 缺存储时只写迁移前字段，不建 part 上下文/job。
- `workbench/server/api.py`：`SchemaMissing` 映射为 500（服务端状态问题），其余
  ValueError 仍是 400。
- `workbench/cli/doctor.py`：每池新增 `part grading schema` 只读检查，缺项列出迁移命令。

## 数据迁移

逐池备份后执行 `pool/scripts/migrate-progress.py`，**19/19 成功**（备份名
`<db>.pre-part-grading-20261101-231213`）：计算机组成、大学物理乙II、高级数据结构与算法分析、
概率论与数理统计、全国大学生数学竞赛、宏观经济学甲、习概、数值分析、面向对象程序设计（C++）、
计算机体系结构、数据库系统、计算机网络、编译原理、操作系统、毛概、软件工程、
c05-thin-tempval、w5-replica、graph-preview。已就绪：lesson-kit；db 缺失：graph-dmath、graph-c02。

## 验收

- `python -m pytest tests -q`：1313 passed（新增 5 个退化/医生用例）。
- 真实池复核（只读）：计算机组成 attempt#146 的练习投影返回
  `grading_status='not_requested'`、零异常；`/grading` 返回干净 400 JSON。
- daemon 已重启到本提交；`/api/runtime` 的 `source_root` = 主检出。
