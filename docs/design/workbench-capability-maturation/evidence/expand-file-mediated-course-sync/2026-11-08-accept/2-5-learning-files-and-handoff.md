# 2.5 学习文件登记、接收与 Tutor handoff（2026-11-08）

任务原文：> 将目标、范围、资料索引、总结、误解和续接文件全部登记并接收 CRUD；定义无原生会话也可读取的 Tutor handoff，原始答案/揭晓/未答项完整。

## 登记范围

`workbench/data/course_sync.py` 的课程文件枚举覆盖：

| 类别 | 落点 | 是否随包 |
|---|---|---|
| 目标 | `.lessonkit/goals.json` | 是（JSON 结构校验：必须是对象数组） |
| 总结 / 误解 / 心得 | `.lessonkit/learning/*.md`（`rglob("*")` 全量） | 是 |
| 试卷文件 | `.lessonkit/practice-sets/*.json` | 是 |
| 图 | `.lessonkit/figures/<course>/<chapter>/…`（按 `figure_paths` 逻辑路径解析） | 是 |
| 教材/资料原件 | `textbook.pdf` 等根文件 + `config.json` 的 `managed_paths` 声明 | 是 |
| 本机媒介配置 | `.lessonkit/course-sync/config.json` | **否**（只读它取 `managed_paths`，本身不是资产） |

## CRUD 证据

| 操作 | 证据 |
|---|---|
| 创建 + 接收（新学习文件，无需手改 manifest） | `tests/workbench/test_tutor_handoff.py::test_tutor_written_learning_files_are_received`、`::test_new_tutor_learning_file_is_received_without_hand_editing_manifest`；真 CLI `LP-01`/`fs-02-new-assets`（`../2026-11-08-p3/f1-report.json`：`learning_file: true`） |
| 更新 | `tests/workbench/test_course_sync_receive.py::test_an_imported_deletion_keeps_the_writer_side_effects` 等接收路径用例；F1 的 `fs-06-propagate` 真 CLI 步骤 |
| 删除（显式墓碑） | `tests/workbench/test_course_sync_receive.py::test_explicit_deletion_removes_the_row_and_a_missing_file_does_not`、`tests/workbench/test_course_sync.py::test_explicit_deletion_and_transport_metadata` |
| 缺文件 ≠ 删除 | 同上用例的反面断言；导出侧遇缺文件直接报 `managed assets are missing without explicit deletion`（`course_sync.py` 的 `missing` 检查），F1 的 `fs-05-missing-file` 真 CLI 步骤 exit 2、`paper_row_kept: 1` |
| 恢复 | 题目归档恢复走 `content.restore` / `data <ws> restore problem`（adaptive change 3.2）；**文件**恢复=重新以正常文件出现并携带内容版本 |

## Tutor handoff

`workbench/data/tutor_handoff.py` 产出包内 `handoff.md`（不落工作区）：

- 目标与范围、当前卷与教学位置、**原始作答**、揭晓事实、未答项、学习文件索引；
- 无原生会话也可读：纯 Markdown，不依赖 provider 状态；
- 证据：`tests/workbench/test_tutor_handoff.py::test_the_handoff_carries_answers_reveals_unanswered_items_and_position`、`::test_the_handoff_lands_in_the_package_and_never_in_the_workspace`；真 CLI `LP-01` 步骤（`goals/scope/original_answer/position/notes` 全 true）。

## 已知边界（不是缺陷，按现行 spec）

- **写端没有"删除学习文件"命令**：删除只能以**显式墓碑**（包内 asset `deleted: true`）表达，接收端据此删除；本地把文件删掉再导出会被如实拒绝（`missing … without explicit deletion`）。spec「Governed file CRUD and identity」只要求**接收端**支持显式删除与恢复，未要求写端提供删除入口，因此不登记为缺口。若后续要 `course-sync … --delete` 入口，属新行为，需走 OpenSpec。
- 学习文件目录遍历不过滤扩展名——这正是 SYNC-04 发现孤儿 `.tmp` 的路径，已在发布侧修复（`3-2-sync-04-process-kill.md`）。
