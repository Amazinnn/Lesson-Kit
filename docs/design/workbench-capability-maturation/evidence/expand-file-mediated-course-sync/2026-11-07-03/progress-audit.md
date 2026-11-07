# Codex 接回时的进度核对

日期为 2026-11-07，核对的源码为 `codex/course-sync` 的 `5d3b5cef`。本次核对使用独立临时课程，没有改动真实课程、运行安装或远端。原 main 仍为 `c5a9c642`。工作区原有未跟踪 debug.log 保留。

## 已核实的进展

第二棒已提交课程学习偏好的浏览器消费、接收端、执行重建、CLI/Git/每小时任务入口、题目编辑与删除副作用、Tutor 可读交接与文件回写。相对第一次暂停交接共有 13 个新增提交。

本轮重新执行同步 Domain/Data/执行/接收/CLI、学习偏好 Data/API 和 Tutor 的组合检查，结果为 69 passed，61.82s。课程偏好 Node 检查为 12 passed，原先 9 项失败已解决。该组合没有包含独立 Git transport 测试文件，但 CLI 测试会运行临时 Git 场景。

第二棒证据记录真实课程副本 A→B 接收 489 项资产、30 张表及 7 个文件一致。其全仓 1,405 passed 与性能数字为第二棒记录，本轮未重新执行全仓。F2、真实免费 LLM、真实浏览器、真实 GitHub、原生计划任务和发布迁移仍缺完整验收。

## 新复现的接收提交边界问题

位置为 `workbench/data/course_sync.py` 的 `apply_exchange`。每单元在 SQLite transaction 内先把选定资产写入 state.base，并用 `_atomic_json` 发布 state.json，随后才退出 transaction 提交数据库。文件确认与 SQLite 提交不属于同一个原子操作。

本轮在临时两个课程中先完成初次接收，再将源知识点 body 从 before 改为 after。接收时在 transaction yield 之后、SQLite commit 之前注入一次 sqlite3.OperationalError，原事务完成 rollback。

实际结果为首次接收 success，注入失败的接收 partial，目标数据库 body 仍为 before。再次 inspect 同一个包得到 incoming changes=0、outgoing changes=1、conflicts=0。即失败更新已经被 state.base 误确认，重试方向反转。结构化结果见 commit-boundary-repro.json。

这阻断 task 2.4 与 SYNC-04 的完整验收。后续修复必须同时覆盖 commit 前后进程中断、整数来源映射、文件发布和执行聚合，保证失败可续办且历史不重复。仅把文件确认移到 commit 后面还需要处理数据库已提交但确认尚未发布的窗口。

## 接回后的优先顺序

先修复并验证数据库与确认/映射的持久一致性，再完成关系校验、文件/偏好损坏阻断与完整资产覆盖。随后执行 F1/F2/F3/F4 和真实体验验收，最后独立验收、职责契约协调及发布。后续五个工作包仍未开始，任务勾选不按代码文件存在推断。
