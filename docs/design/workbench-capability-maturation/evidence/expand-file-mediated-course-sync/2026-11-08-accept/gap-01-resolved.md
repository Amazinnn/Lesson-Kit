# GAP-01 已解决：删除知识点写入显式墓碑

覆盖表（`../2026-11-08-accept/2-1-coverage-table.md` §4）报出的最严重缺口：只有 `problems` 有本地墓碑，删掉知识点后下一次导出会以 `managed assets are missing without explicit deletion` **永久失败**，且没有入口能记录"我删了"。

## 拍板

所有者选「删除时写墓碑」，不采用"导出时报待确认"——后者会让"文件丢了"和"本人删除"混在一起，正是现行 spec 禁止的。

## 实现

- `workbench/data/content.py::delete`：删除知识点后调用 `course_sync.record_row_deletions(pool, "knowledge_points", [id])`（延迟导入避免与 `course_sync` 的循环依赖）。
- `workbench/data/course_sync.py::record_row_deletions`：只在**该行曾经导出过**（`row_identities` 有映射且 `base` 里有它）时把 `base` 条目置 `deleted: True`；从未导出过的行无需墓碑，接收端本来就没有它。
- 既有 `_projection` 已经会把 `base` 里 `deleted` 的条目重新投影为出站资产，因此导出侧不需要第二套逻辑。

## 验证

`tests/workbench/test_course_sync_lifecycle.py`：

| 用例 | 断言 |
|---|---|
| `test_a_deleted_knowledge_point_travels_as_an_explicit_tombstone` | 删除 → 第二次导出**成功**（不再报缺失）→ 接收端知识点与关系都被删除 |
| `test_receiving_a_knowledge_point_tombstone_twice_is_idle` | 同一包裹再检查一次，`changes` 与 `outgoing` 都为空 |

相关回归：`tests/workbench/test_course_sync_receive.py` 38 passed、`test_course_sync_lifecycle.py` 11 passed（含本条与 2.3 的往返用例）。

## 未覆盖

- **闪卡**：没有面向用户的删除入口（删除只发生在删知识点的级联里，行随知识点一起消失，并由接收端跟随同一条墓碑链路处理）。
- **学习文件**：仍无写端删除入口；本地直接删文件会被如实判为"缺文件"而**不是**删除——这是 spec 要求的区分，若要支持删除需要新的显式删除入口。
- 覆盖表里其余 13 条 GAP 未在本次处理；GAP-12（本机新增列导出侧不报错，与 `FILE_CONTRACT.md:827` 冲突）仍待登记处置。
