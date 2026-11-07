# SYNC-08：真实旧格式课程池的导出与接收

夹具：`D:/Projects/Academic Workflow/lesson-kit/pool/dmath-pre-readiness-2026-08-26.db` 的只读副本
（真实课程，2026-08-26 readiness 迁移之前：28 知识点 / 303 题 / 3 作答 / 6 learner_signals，
另带两个已退役的 ingest 候选表）。

目标：用 `pipeline/scripts/create-tables.py` 新建的当前 schema 课程。

## 结果

| 步骤 | 结果 |
|---|---|
| 导出 | success，**347 项资产**；清单明确登记被跳过的退役内容 |
| 检查 | `errors: []`，`changes: 347` |
| 接收 | **success，347 项全部落地，0 失败** |
| 落地计数 | knowledge_points 28、problems 303、problem_attempts 3、learner_signals 6（与源一致） |
| 题目正文 | 逐字保留（含原始英文题干与换行） |
| `problems.topic_label` | 目标库不含该列（符合 DATA_MODEL「已删除字段」） |

## 为让旧数据可用而做的两处映射（都写进清单，不静默）

1. **退役表**：旧池仍带 `candidate_problems` / `candidate_attempts`，而当前 schema 不创建它们，
   `FILE_CONTRACT` 也声明"没有候选表/暂存态"。原先它们会让导出直接失败（`unregistered course tables`）。
   现在把这两个名字作为**已知退役表**跳过，并在清单里记 `retired_tables`；真正未知的表仍然报错。
2. **退役列**：旧 `problems` 带 `topic_label`，而 DATA_MODEL 明确该列已删除、历史值只能留在库外备份。
   原先每个题目行都以"row does not match the target course schema"被判无效（303 题全部被拒）。
   现在导出时按已知退役列剔除，并在清单里记 `retired_columns`；其它未知列仍然逐项判无效。

## 边界

- 这不是"旧库自动迁移"：接收目标是当前 schema 的新课程，旧库本身只读未改。
- 未覆盖：更早的池（缺 primary key 的表）、带非法/未知列的真实池、`--force` 重建、安装身份切换（RELEASE-02）。
- 同一夹具的注意点：`knowledge_relations` 在旧池为 0 行，因此"关系迁移"没有真实样本。
