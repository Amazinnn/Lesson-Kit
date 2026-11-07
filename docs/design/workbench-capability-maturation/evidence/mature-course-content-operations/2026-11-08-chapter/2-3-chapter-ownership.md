# WP02 2.3 独立章节归属与跨章移动

任务原文：> 沿 ensure_* 增量迁移添加独立章节归属，回填旧ID初始章，更新所有推章消费者。使用带经验、关系和历史的旧点迁移并文件往返，记录全部引用。

## 迁移与回填

`pool/scripts/pool_schema.py`：`ensure_knowledge_chapter_schema`（接在 `ensure_workbench_schema` 末尾，旧池由 `migrate-progress.py` 触发，新池由 `create-tables.py`/bootstrap 触发）

- 加可空列 `knowledge_points.chapter`；
- 只回填 `chapter IS NULL` 的行，取**整段**章（`course` 与 `-kp-` 之间），与仓库既有解析器一致：`dmath-ch06-kp-001 → ch06`、`dmath-source-ch03-kp-001 → source-ch03`；无 `-kp-` 段则保持 NULL，不猜；
- 重跑不覆盖显式值；变更条目合并成一条计数，真实池迁移不会刷几千行。

用例 `tests/test_knowledge_chapter_schema.py`（4）：普通回填、多段章、无章段保持 NULL、重跑保留显式值。

## 读取口径：列优先、NULL 回退 ID

按所有者拍板**只改 workbench 层**，冻结层不动。

| 消费者 | 改动 |
|---|---|
| `Pool.kps(prefix)` | 透镜章存在时按 `chapter=? OR (chapter IS NULL AND kp_id LIKE ?)`；无该列的旧池走原前缀查询（`workbench/data/pool.py`） |
| `Pool.chapters()` | 有 `chapter` 的知识点用它；其余实体与 NULL 行继续从 ID 推章 |
| `pages._kp_chapter` / 知识点列表分组 | 列优先，NULL 回退 ID 正则 |
| `content.knowledge_query(chapter=…)` | 用 `kp_chapter()`（列 → ID 整段），顺带修掉原先"按 `-` 切 token"对多段章失效的问题 |
| `content.create(kp)` | 新行直接写入章（来自 `data.chapter` 或 ID 段） |
| `ingest` 两处 KP 写入 | content-bundle 写 `plan["chapter"]`；旧 content_patch 从 `kp_id` 取段 |

## 跨章移动

新入口：`lesson-kit data <ws> move kp <kp-id> --chapter chNN`（`content.move_kp`）

- **只改 `chapter`**（有 `updated_at` 时一并刷新），`kp_id` 不变 ⇒ 题目关联、`knowledge_relations`、`kp_experiences`、`review_schedule`、学习记录、course-sync 身份全部继续有效；
- 返回 `previous` / `chapter` / `moved`；
- 池未迁移时明确报错，不静默降级。

用例（`tests/workbench/test_content_queries.py`）：

| 断言 | 用例 |
|---|---|
| 移动后旧 ID 仍可 get、关系与经验原样 | `test_a_chapter_move_keeps_the_id_and_every_reference` |
| 章透镜按新章读到、旧透镜读不到 | `test_the_active_lens_reads_a_moved_point_in_its_new_chapter` |
| 新建知识点自带章列 | `test_a_new_knowledge_point_gets_its_chapter_column` |
| 章列表随移动更新（章的存续看内容） | 同上，`ch09` 出现、`ch07` 消失 |
| **文件往返**：移动后导出 → 接收端仍是新章，旧透镜为空 | `tests/workbench/test_course_sync_lifecycle.py::test_a_moved_chapter_survives_the_exchange` |

引用核对：移动只改一列，`kp_id` 不变，故下列引用**无需改写**即可解析——`problems.kp_ids`、`knowledge_relations.source_kp_id/target_kp_id`、`flash_cards.kp_id`、`kp_experiences.kp_id`、`kp_progress.kp_id`、`learner_signals.target_id`、`review_schedule.item_id`、`learning_current_state.item_id`、`feedback_events.item_id`、课程交换 `row/knowledge_points/["<kp_id>"]` 身份。

## 已知边界（按所有者决定，不视为缺陷）

- **冻结层仍按 ID 推章**：`pool/scripts/{query-pool,print-graph,render-graph-html,serve-graph,course_network,learner_signals}.py`、`pipeline/scripts/{validate-pool,insert-knowledge-points}.py` 及其视图/命令文档。移动过的知识点在这些离线视图里仍显示**原章**。这是"只改 workbench 层"的直接后果，改它们需要给冻结层开例外。
- **题目没有独立章**：题目归属仍由 `problem_id` 决定；移动知识点**不会**把题目迁到新章（图谱/题目计数的章节口径也会因此与新章不一致）。
- **图片不随行**：`figure_paths` 与 `figures/<course>/<chapter>/` 目录不随移动改变，`figures_list` 按透镜章取目录时可能看不到旧目录里的图。
- **镜像不带 `chapter`**：`content_mirror` 的字段来自 `EDITABLE_FIELDS`，`chapter` 未加入，因此移动只存在于池与课程交换，不经 JSON 镜像往返。
