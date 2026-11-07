# 4.4 LIFE-SYNC 全矩阵（2026-11-08）

任务原文：> LIFE-SYNC 全矩阵（active/parked、首尾/游标题移除、全移除、中断重试、旧库无表接收）与真实入口验收。

矩阵来自 `NEXT-EXECUTION-PLAN-2026-11-07.md` 的六条。除第 5 条的"进程级中断"本轮才补（见 `3-2-sync-04-process-kill.md`），其余由既有自动化用例覆盖；本轮逐条核对用例名与断言内容，未重跑全仓（RELEASE-01 已跑过全仓）。

| # | 矩阵要求 | 覆盖 | 结论 |
|---|---|---|---|
| 1 | A 移除一道重复题：存活题状态/attempt/草稿/序号不变，removed 项最后草稿与历史可查，结构版本只递增一次 | `tests/workbench/test_paper_lifecycle.py::test_removing_a_duplicate_keeps_every_surviving_state_draft_and_attempt`、`::test_a_removed_draft_is_retained_and_an_added_question_starts_pending` | PASS |
| 2 | 导出 A→新 B 一次接收→B 继续→导出 B→A 接收→再传 C；逐字段一致、运行记录不重复、无本机路径依赖 | `tests/workbench/test_course_sync_lifecycle.py::test_retained_history_survives_export_receive_and_the_next_hop`、`::test_receiving_the_same_history_twice_appends_nothing`、`::test_a_received_history_row_takes_a_local_sequence` | PASS |
| 3 | active 与 parked、游标题被移除、首尾题被移除、移除全部；其他卷与已完成轮次不动 | `test_paper_lifecycle.py::test_a_parked_paper_reconciles_the_same_way`、`::test_the_cursor_follows_its_question_then_the_next_survivor`、`::test_removing_every_question_clears_the_run_and_keeps_each_history_row` | PASS |
| 4 | B 已有相同整数编号但不同事实：引用指向原事实；两端相同课程内序列不得静默覆盖 | `test_course_sync_lifecycle.py::test_a_received_history_row_takes_a_local_sequence`、`::test_a_cached_display_id_never_blocks_export_or_gets_rebound` | PASS |
| 5 | 导出/提交/文件发布中断后重试；独立有效项继续、同一保留历史不重复；未知表仍拒绝 | 中断：`2026-11-08-accept/sync-04-kill-report.json`（真子进程硬杀 × 4，见 `3-2`）；未知表：`tests/workbench/test_course_sync_data.py::test_unknown_table_is_explicitly_rejected`、`::test_a_retired_staging_table_is_skipped_and_reported` | PASS |
| 6 | 从无此表的旧库接收、显式迁移后重复接收；旧作答/草稿不丢，不靠启动迁移掩盖缺表 | `test_course_sync_lifecycle.py::test_an_old_course_without_the_history_table_receives_and_repeats`；真实旧池由 F4 夹具覆盖（`../2026-11-08-p3/f4-report.json`，347 项 0 失败） | PASS |

## 真实入口

- CLI：本目录 `2-7-cli-receipts.md`（同批取证）。
- 浏览器：`../2026-11-08-p3/summary.md` 记录的隔离服务（端口 3099）实测——收到的偏好生效、新卷用收到的揭晓时机、进行中的卷冻结可继续。
- 免费 LLM：`../2026-11-07-09/`（1 次真实调用，0 重放，成本 0）。

## 保留意见

- 第 5 条的"提交中断"只覆盖到文件发布与数据库事务边界，没有对 Git 提交过程本身做硬杀（推送被拒/分叉由 `p3_git.py` 的专用 bare 远端覆盖）。
- 矩阵在 Windows 本机验证；未验证其他平台。
