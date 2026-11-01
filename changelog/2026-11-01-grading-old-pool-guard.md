# 2026-11-01 — 旧池上的 grading 请求防静默断连（rollout 加固）

背景：所有者在真实 `pool/dmath.db` 上通过 CLI 打开 dashboard 后访问 grading API，
收到空响应（curl exit 52 / HTTP 000）。该池尚未跑过综合题批改的显式增量迁移，
`part_attempt_context` 缺表，`sqlite3.OperationalError` 穿透 HTTP 层未捕获，
worker 直接丢连接且不留痕迹。

## 修复

- `workbench/server/api.py`：`grading_read` / `grading_write` 捕获 `sqlite3.Error`
  → `ApiError(500)`，消息含可操作指引（"no such table" 时附
  `pool/scripts/migrate-progress.py --db <池路径>`）。与 CLI `cmd_grading` 的
  异常口径对齐。
- `workbench/server/app.py`：`_dispatch_admitted` 增加最后兜底 `except Exception`
  → 500 JSON + stderr traceback；任何未来漏网的处理器异常都不再表现为静默断连。
- 测试：`tests/workbench/test_grading_pool_guard.py`（旧式最小池 → 两个 grading
  handler 均返回 500 ApiError，消息含迁移指引）。

## 数据迁移（所有者的真实测试池）

- 先备份：`pool/dmath.db.pre-part-grading-migrate-20261101-212722`。
- `python pool/scripts/migrate-progress.py --db pool/dmath.db` →
  `problem_attempts.part_id`、`problem_attempts.content_revision`、`problems.parts`。
- 三张 part_* 表确认存在；daemon 重启后 grading API 对不存在 attempt 返回
  干净的 400 JSON（`{"error": "saved part Attempt not found"}`）。

## 验收

`python -m pytest tests -q`：1305 passed（含 2 个新守护测试）。
