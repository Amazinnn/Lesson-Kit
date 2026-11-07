# Design

## Context

- 22 个注册工作区池中 19 个缺 `part_*` 三张表与 `problems.parts`、
  `problem_attempts.part_id/content_revision`（2026-11-01 全量只读扫描）。
- 读：`workbench/data/part_practice.py:177` 的 `part_grading.get(pool, attempt_id)` 与
  `:178` 的 `SELECT status,error FROM part_grading_jobs` 无守卫；`part_grading.get`
  （`workbench/data/part_grading.py:26`）直接查 `part_grading_revisions`。
- 写：`workbench/data/part_practice.py:109-117` 无条件写
  `problem_attempts.part_id/content_revision`、`part_attempt_context`、`part_grading_jobs`。
- 同功能已有守卫先例：`workbench/data/grading_jobs.py:8` 用
  `sqlite_master` 探测 `part_grading_jobs` 后再查询。
- `part_grading.ensure_schema` / `part_practice` 的建表只由 `pool_schema.ensure_*`
  （迁移命令）调用；服务端不做自动迁移（契约要求"explicit additive migration"）。

## Goals / Non-Goals

**Goals:**
- 未迁移池：打开卷子、作答、交卷、评价全部照旧可用；批改状态显示为未请求。
- 显式批改（HTTP/CLI）保持可操作失败，不静默成功。
- 迁移缺口可从 `doctor` 看到；对全部已注册池执行一次幂等迁移（先备份）。

**Non-Goals:**
- 不在打开池时自动迁移（契约要求显式；自动迁移会让"读一次页面"变成 schema 变更）。
- 不改批改的数据模型与 revision 语义。
- 不为未迁移池伪造任何小问结论或提炼答案。

## Decisions

1. **守卫放数据层，模式统一**：在 `part_grading.py` 增加一个
   `has_schema(pool)`（`sqlite_master` 探测三表 + `problems.parts` 列），
   `grading_jobs.target/get` 与 `part_practice.project/submit` 复用它。
   替代方案（在每个 handler 里捕 `sqlite3.Error`）被否：错误在投影/提交路径而非
   端点级，捕异常会把"缺 schema"伪装成一般错误，也让 CLI 与 HTTP 行为分裂。
2. **读退化返回值**：`part_grading.get/list_revisions` → `None`/`[]`；
   `grading_jobs.get` → `None`；`project()` 在 `has_schema` 为假时跳过 job 查询，
   `grading_status` 保持 `not_requested`。投影形状不变，前端无需分支。
3. **写退化**：`_submit_item` 在 `has_schema` 为假时只做迁移前的写入
   （`pool.insert_attempt` + `active_practice_items` 状态），跳过
   `UPDATE ... part_id/content_revision`、`part_attempt_context`、`part_grading_jobs`。
   虚拟 `whole` 小问语义不变（老题本来就是整题作答）。
4. **显式批改失败**：`grading.apply/withdraw/retry` 与 `dispatch_pending` 在缺 schema 时
   抛带迁移命令的 `ValueError`；HTTP 层既有 `sqlite3.Error → ApiError(500, 指引)`
   保留为二道防线。CLI `cmd_grading` 已捕 `sqlite3.Error`，口径一致。
5. **doctor 可见性**：`workbench/cli/doctor.py` 增加每池"批改 schema 就绪"只读检查
   （缺则报告缺哪几项并给迁移命令），不改退出码语义。
6. **迁移顺序**：先 计算机组成（所有者正在用），再其余 18 个；逐池
   `cp pool/<db> pool/<db>.pre-part-grading-<ts>` 后跑
   `python pool/scripts/migrate-progress.py --db <db>`，迁移后用只读扫描复核。

## Risks / Trade-offs

- `has_schema` 每请求一次 `sqlite_master` 查询（每池一次连接内缓存可省；先在 `project`
  的每调用缓存到 pool 对象的一个属性，避免逐 item 重复查询）。
- 退化写入的 Attempt 没有 `content_revision`：之后迁移完成，历史老 attempt 的
  `part_id` 为空——这符合"不伪造小问结构"的契约，查询侧本就按 NULL 兼容。
- 迁移 19 个真实池是不可逆变更（加列/加表），备份先行；迁移命令幂等，可重跑。
