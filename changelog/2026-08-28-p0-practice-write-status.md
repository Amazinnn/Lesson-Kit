# P0: practice 写入状态映射修复

## 问题

`wb practice --result correct|skip` 与 `POST /api/w/{name}/practice` 携带同样 result 时，
真实题库上必然崩溃（`sqlite3.IntegrityError: CHECK constraint failed`，HTTP 连接被重置）。

根因是结果词表与落库词表分叉：

- 接受侧：`workbench/domain/schedule.py` 的 `RESULT_QUALITY` 允许
  `correct / wrong / stuck / skip`；
- 落库侧：`problem_attempts.status` 的 CHECK 只允许
  `new / wrong / stuck / reviewing / mastered`（`pool/scripts/pool_schema.py`，
  真实 dmath.db 同）；
- 两个调用点（`workbench/server/api.py` practice、`workbench/cli/main.py` cmd_practice）
  把 result 原样当 status 写入；
- 测试 fixture 建表没有这个 CHECK，因此测试永远无法暴露该缺陷。

## 修复

- 新增 `domain/schedule.py::recorded_status(result)` 纯映射：
  `correct→reviewing`、`wrong→wrong`、`stuck→stuck`（与 problem_progress 既有映射一致）；
  `skip→None`，即不写任何学习记录（沿用 2026-08-22 学习流变更「skipped 永不成为
  学习记录」的既定原则），schedule 亦不推进。
- API 与 CLI 两个调用点统一改经该映射；CLI 的 `RESULT_PROGRESS` 本地映射删除。
- `tests/workbench/fixtures.py` 的 `problem_attempts` 建表补上与 `pool_schema.py`
  一致的 CHECK，让这一类「接受词表 vs 落库词表」分叉今后能被测试直接抓住。

## 验证

- 新增回归测试：correct 落库 status 为 `reviewing`（attempt + progress）；
  skip 返回 `recorded: false` 且 attempts / progress / schedule 三表零写入；
  CLI skip 打印 no learning record。
- 既有 wrong 路径、schedule 推进行为不变；全量 pytest 通过。
- 真实表结构副本上实测：`wb practice --result correct` 成功记录；
  skip 零写入；UI 提交作答流程不受影响。
