# WP02 2.5 退役成功批次 undo + FLOW-03 直接修正

任务原文：> 退役成功批次undo CLI/Agent提示/操作入口，历史 rolled_back 保持可读；用直接修正完成相同修错任务，FLOW-03实际走通。

## 撤除了什么（一次性，不留半截）

| 层 | 移除内容 |
|---|---|
| CLI | `lesson-kit ingest rollback --batch/--backup`（子命令与派发分支） |
| HTTP | `POST /api/w/{name}/ingest/rollback`（`surface.py` 注册表、`server/app.py` 路由、`server/api.py::ingest_rollback`） |
| 数据层 | `ingest.rollback_batch` 与仅供它使用的 `_rollback_content_bundle`、`_rollback_conflicts`、`_rollback_problem_patch`、`_rollback_gate_report`、`_rollback_figure_patch`、`_rollback_blockers`（净删 362 行） |
| 前端 | 结果卡「整批回滚」按钮（两种渲染位置）、`aiRollbackBatch` 函数与其确认面调用、对应 CSS 规则 |
| Agent 提示 | `agent_contracts` 两处：动作清单里的 `rollback`、"rollbackable by ingest batch" |

**保留**：`ingest_batches.rolled_back_at` 列与 `list_batches` 的读取；已回滚批次的历史卡片仍显示「已回滚」标记（`aiMarkRolledBack`）。批次快照从"回滚护栏"改写为"应用于记录"（注释同步）。

## 验证

| 断言 | 证据 |
|---|---|
| CLI 不再接受该子命令 | `tests/workbench/test_batch_undo_retired.py::test_ingest_rollback_is_no_longer_a_command`（argparse 直接 SystemExit） |
| 历史回滚仍可读 | 同文件 `::test_a_historical_rollback_stays_readable`（`list_batches` 返回 `rolled_back_at`） |
| 既有测试面收敛 | 删除 17 条纯回滚用例；改写 2 条非回滚意图的用例：`test_gate_report_stamps_new_knowledge_points`（去掉回滚断言）、`test_a_patch_keeps_the_learning_records_it_touched`（改为断言补丁后学习记录仍在）；`real_pool_conformance.py` 去掉回滚校验，保留批次戳记与既有行不变 |
| 受影响套件 | `test_ingest / test_content_bundle / test_cards / test_conversation_api / test_problem_patch`：**104 passed** |

## FLOW-03：用直接修正完成同样的修错

`tmp/accept/flow03_direct_correction.py`（真实池 + 真实作答行）：

1. 录入一条作答（`problem_attempts`，正文「我原来的作答」）；
2. 做一次**错误**修改：`content.update(problem, {"display_title": "错的标题"})`；
3. 用**同一身份**再改一次：`display_title = "正确的标题"`；
4. 结果：

```
{"problem_id":"dmath-ch06-prob-001","display_title":"正确的标题",
 "identity_unchanged":true,"attempts":1,"original_answer_kept":true,
 "undo_entry_removed":true}
```

即：题号不变、作答原文一字未动、撤销入口已不存在，而"改错→改正"照样完成。成批场景走同一路径的另一形态：`problem-patch` 清单按字段写回（用例见 `tests/workbench/test_problem_patch.py`）。

## 文档同步

`GLOSSARY`（Check 管线、题图、problem-patch、批次 id、批次条目）、`FILE_CONTRACT`（批次快照语义）、`PRODUCT-MANUAL`（第 8 章 6 处：按章回滚、整批撤销按钮、整批可回滚、按章批次、旧值还原、备份机制）、`docs/ACTION-GRAPH.md`（2026-11-08 退役留痕）与 `L0/L1/L2/L3/L4`（数据表、服务、命令与路由、动作、流程图）。历史留痕条目（2026-09/10 的引入记录）保留不动。

## 边界

- 已存在数据库中 `rolled_back_at` 非空的批次不会再被处理；列表与卡片只读展示。
- 前端 `aiMarkRolledBack` 仍在，用于显示历史状态；不再有任何新的撤销入口。
- 幂等/依赖阻断等"回滚前检查"随实现一起退役；对应的保护改由"改不了题号 + 学习记录不动"直接承担。
