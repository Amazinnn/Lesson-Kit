# 测试夹具在 Windows 上释放数据库句柄

**日期：** 2026-09-29

**类型：** 测试修复

## 变化

- `tests/workbench/fixtures.py` 新增 `open_db(path)` 上下文管理器：退出时必定
  `close()`，同时保留 `with sqlite3.connect(...)` 原本的提交/回滚语义。
- 8 处只在事务上借道 `with` 的连接改用 `open_db(...)`：`test_content_audit` 3 处、
  `test_content_bundle` 3 处、`test_problem_patch` 1 处、`test_micro_quiz` 1 处。

## 不变

- 不触碰任何生产代码；断言、用例集与 CI 行为不变。

## 背景

`with sqlite3.connect(...)` 只负责提交事务，**不会关闭连接**。Windows 下句柄仍被占用时
`WorkspaceFixture.cleanup()` 删不掉临时工作区，于是一个断言完全通过的用例会在 teardown
抛 `PermissionError [WinError 32]`；Linux 允许 unlink 已打开的文件，所以 CI 一直看不见。
本机（Windows 11 + Python 3.14）复跑：修复前 750 passed / 6 failed，修复后 756 passed。
