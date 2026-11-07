# 1.3 F1/F3/F4 回归样本（2026-11-08）

任务原文：> 在隔离课程副本建立 F1/F3/F4 回归样本，先运行针对本包缺口的失败检查，保存结果和期望差异。

## 夹具与覆盖

| 夹具 | 建的是什么 | 覆盖 | 报告 |
|---|---|---|---|
| `tmp/accept/p3_f1.py` → `sync-04-kill-fixture.py` 复用的造课函数 | F1 完整小课程：3 章 / 12 知识点 / 24 题（普通、客观、混合作答）/ 6 卡 / 6 关系 / 3 张共享题的卷 / 2 个未完成执行 / 12 条作答 / 4 条经验 / 2 个目标 / 8 个学习文件 / 10 张图 / 1 份教材原件 | SYNC-01、FS-01/02/05/06/07/08、LP-01 | `../2026-11-08-p3/f1-report.json` |
| `tmp/accept/p3_f3.py` | 异常矩阵：缺文件、坏信封、双侧冲突、同名异源、只读检查 | SYNC-03、FS-04/09/10/11 | `../2026-11-08-p3/f3-report.json` |
| `tmp/accept/p3_f4.py` | 真实旧池（2026-08-26 dmath，347 项），含已删列与退役表 | SYNC-08 旧格式 | `../2026-11-08-p3/f4-report.json` |

全部在临时目录里建课，每台"设备"独立 `LESSONKIT_WB_HOME`；不读不写真实课程池。

## 先跑失败检查，期望差异 → 两个真 bug

这两条是"先失败、后修复、再用同一夹具回归"的样本，不是事后补写的断言：

| 缺口 | 失败现象（修复前） | 期望差异 | 现在钉住它的用例 |
|---|---|---|---|
| 接收端按位置合并执行项 | 发送端已删除的执行项留在接收端 → `UNIQUE constraint failed: active_practice_items.item_type, item_id, direction` | 执行头应声明自己的题目集合，接收端按集合取数、丢弃未声明项；旧包无该字段时按位置合并 | `tests/workbench/test_course_sync_execution.py`（`test_parked_and_selected_papers_share_the_execution_projection`、`test_different_question_edits_do_not_conflict_across_device_exports`） |
| `content.delete` 删题不写保留历史 | 被删题在接收端无 `retired_paper_items` 记录，历史丢失 | 删题同时写保留历史（reason=deleted），随交换传播 | `tests/workbench/test_course_sync_lifecycle.py::test_deleting_a_shared_question_propagates_to_the_other_installation`、`tests/workbench/test_paper_lifecycle.py::test_removing_every_question_clears_the_run_and_keeps_each_history_row` |

修复提交：`78ef7bb0`（"P3 acceptance and the two defects it exposed"）。

## 本轮新增的失败样本

SYNC-04 的进程级 kill 夹具（`sync-04-kill-fixture.py`）在 `2026-11-08-accept` 首次运行时又暴露一个缺口：硬杀在文件发布中途留下 `<name>.<random>.tmp`，而学习目录遍历不过滤扩展名，孤儿会在下一次交换被当作资产传播。修复 + 回归用例见 `3-2-sync-04-process-kill.md`。

## 复现

```bash
cd "D:/.codex/worktrees/course-sync/lesson-kit"
PYTHONUTF8=1 python tmp/accept/p3_f1.py
PYTHONUTF8=1 python tmp/accept/p3_f3.py
PYTHONUTF8=1 python tmp/accept/p3_f4.py
PYTHONUTF8=1 python tmp/accept/p3_kill.py     # 证据版：docs/design/.../2026-11-08-accept/sync-04-kill-fixture.py
```
