# 2.9 系统任务：安装/启停/删除与运行语义（2026-11-08）

任务原文：> 系统任务按每小时、全部已配置课程调用同一 CLI，提供安装/更新/启停/删除。实测手动并发、某课程受阻、凭据缺失和一次冲突通知。

## 每小时 + 全部已配置课程

- 原生 Windows 任务 XML：`workbench/bridge/course_sync_task.py`（`test_native_definition_binds_command_and_directory`：命令、目录绑定、小时重复）；
- 任务动作就是同一 CLI：`--all-configured sync`；聚合逐课程退出码：`tests/workbench/test_course_sync_cli.py::test_all_configured_aggregates_each_course_exit_code`。

## 安装 / 更新 / 启停 / 删除

| 项 | 证据 |
|---|---|
| 单元级：install / enable / disable / remove | `tests/workbench/test_course_sync_task.py::test_lifecycle`（参数化四种动作 + XML `<Enabled>` 断言） |
| 任务创建用 XML、隐藏窗口、有超时、临时文件清理 | `::test_task_creation_uses_xml_hidden_timeout_and_removes_temporary_file` |
| 预检绑定所选 checkout | `::test_preflight_uses_the_selected_checkout` |
| 真实 Windows 任务 | `../2026-11-08-p3/task-report.json`：安装、停用（XML `<Enabled>false</Enabled>`）、启用、删除全部 returncode 0；任务动作手动执行返回 `success, courses:{task-course:0}` 并写出回执 |

## 手动并发

`tests/workbench/test_course_sync_lock.py`：

- `test_busy_lock_rejects_another_owner_and_then_releases`：第二个所有者被明确拒绝（不是静默破坏），释放后可用；
- `test_process_death_releases_lock_without_deleting_the_file`、`test_public_course_lock_releases_after_process_death`：进程硬杀后独占锁自动释放，锁文件不被误删；
- 本轮 SYNC-04 的硬杀夹具再次覆盖"进程死→锁释放→重试成功"。

## 某课程受阻

`test_all_configured_aggregates_each_course_exit_code`：一门课失败不影响其他课的结算与退出码聚合；`task-report.json` 的回执带 `failures` 数组。

## 凭据缺失

- Git 推送被拒：`tests/workbench/test_course_sync_cli.py::test_a_rejected_push_reports_local_completion_without_remote_success`（本地完成照报，远端成功不得冒充）；
- **未做**真实"无凭据访问私有远端"实验：本机没有可用的私有远端凭据环境，`git ls-remote` 只做了只读连通性探测。该分支按"推送失败→exit 4 partial"路径覆盖，不声称已实测凭据缺失。

## 一次冲突通知

`tests/workbench/test_course_sync_cli.py::test_a_genuine_conflict_returns_3_and_notifies_once`；CLI 在 `workbench/cli/course_sync.py:483` 写 `receipt["notification"] = {"notified": …, "identities": …}`，同一冲突第二次 `notification=null`（`task-report.json` 亦然）。

## ⚠️ 调度触发未验证（SYNC-06 唯一的真缺口）

`schtasks /Run` 与 `Start-ScheduledTask` 之后：`LastRunTime` 更新、`LastTaskResult=0`，但**任务动作没有任何副产物**，180 秒内无回执；同一 wrapper 手动执行则正常产出回执。已试过 `Register-ScheduledTask` + `Start-ScheduledTask`。判定为**平台/环境侧待查**，不是 CLI 缺陷：任务命令本身、XML、安装/启停/删除全部可验证。

结论：2.9 的"安装/更新/启停/删除 + 手动并发 + 某课程受阻 + 一次冲突通知"已实测；**真实调度触发与真实凭据缺失两项未验证**，按未运行登记，不勾成"已通过"。
