# 2.1 覆盖表：课程交换的 schema × 字段 × 样本

- 任务：`openspec/changes/expand-file-mediated-course-sync/tasks.md:9`（2.1）
- 规划矩阵：`docs/design/workbench-capability-maturation/data-exchange-matrix.md`
- 取证对象：`D:\.codex\worktrees\course-sync\lesson-kit`，HEAD `424453a1`
- 事实源（只读）：`pipeline/scripts/create-tables.py`、`pool/scripts/pool_schema.py` 的 `ensure_*`、`pool/scripts/experience_schema.py`、`workbench/data/pool.py:458`（`retired_paper_items`）。在临时目录用上述规范入口建库后实测列清单，再用该 schema 打开 F1 / F4 样本。
- 只读承诺：生产代码 0 改动、0 commit；所有试验在 `%TEMP%\e1-*`，`LESSONKIT_WB_HOME` 指向临时目录；真实课程池只读打开；未跑全仓 pytest。
- 复用样本：P3 证据 `evidence/expand-file-mediated-course-sync/2026-11-08-p3/`（F1=`f1-report.json`，F4=`f4-report.json`）。F1 实测库路径 `%TEMP%\p3-f1-usylxmjv\A\pool\course.db`，F4 源 `D:\Projects\Academic Workflow\lesson-kit\pool\dmath-pre-readiness-2026-08-26.db`。
- 临时脚本（未跟踪）：`tmp/accept/e1_schema.py`（建库+读写扫描）、`tmp/accept/e1_probe.py`（未知类型/列探针）、`tmp/accept/e1_delete_probe.py`（删除传播探针）。

**模块名简写**：`content`=`workbench/data/content.py`、`pool`=`workbench/data/pool.py`、`ingest`=`workbench/ingest/__init__.py`、`attempts`=`workbench/data/attempts.py`、`active`=`workbench/data/active_practice.py`、`paper_progress`=`workbench/data/paper_progress.py`、`practice_sets`=`workbench/data/practice_sets.py`、`records`=`workbench/data/records.py`、`relations`=`workbench/data/relations.py`、`experience`=`workbench/data/experience.py`、`content_mirror`=`workbench/data/content_mirror.py`、`figure_mirror`=`workbench/data/figure_mirror.py`、`difficulty`=`workbench/data/difficulty.py`、`display_metadata`=`workbench/data/display_metadata.py`、`grading_jobs`=`workbench/data/grading_jobs.py`、`part_grading`=`workbench/data/part_grading.py`、`part_practice`=`workbench/data/part_practice.py`、`tutor_handoff`=`workbench/data/tutor_handoff.py`、`mastery`=`workbench/data/mastery.py`、`evidence`=`workbench/data/evidence.py`、`queries`=`workbench/data/queries.py`、`course_sync`=`workbench/data/course_sync.py`、`course_preferences`=`workbench/data/course_preferences.py`、`pool_schema`=`pool/scripts/pool_schema.py`、`experience_schema`=`pool/scripts/experience_schema.py`。

## 0. 结论

| 项 | 值 |
|---|---|
| 实际 schema | **33 表 / 242 字段**（临时库实测，含 2 张设备本地账本表） |
| 随包交换 | **31 表 / 236 字段** |
| 不随包交换 | 2 表 / 6 字段（`course_sync_checkpoint`、`course_sync_units`，`course_sync:250` 显式剔除） |
| 仅旧池存在 | 2 表 / 29 字段（`candidate_problems` 22、`candidate_attempts` 7；`RETIRED_TABLES`，`course_sync:30,254-258,297-299`） |
| 已退役列 | `problems.topic_label`（`RETIRED_COLUMNS`，`course_sync:33,272-279`） |
| 矩阵逐行 | 21 类：**完整 8 / 部分 7 / 无 5 / 不适用 1**（§2）；矩阵未列的 `retired_paper_items` 另有完整样本 |
| GAP | **14 条**（§4） |
| 最需要主线决策 | **GAP-01 删除传播**：只有 `problems` 有本地墓碑；删闪卡/知识点/学习文件后下一次导出即失败（除非按原身份重建），且无 CLI 入口可记录显式删除或清理 `base` |

## 1. 实际 schema 清点

清点基准：用 `pipeline/scripts/create-tables.py` 在临时目录建库（它串起 `SCHEMA_SQL` + `ensure_problem_candidate_schema` + `ensure_workbench_schema` + `ensure_experience_schema`），再执行 `workbench/data/pool.py:458` 的 `ensure_paper_lifecycle_schema`，读 `PRAGMA table_info`。33 张表、242 列，与 `course_sync.TABLES`（33 项，含 2 张退役表名）逐一核对：真正存在的 31 张交换表全部在册，无实际表缺失、无多余登记。

### 1.1 总览

| # | 表 | 字段 | 主键 | 交换 | 身份式 | 行样本（F1 期末 / F4 源） |
|---|---|---|---|---|---|---|
| 1 | `knowledge_points` | 15 | kp_id | managed | `row/<t>/[…]` | F1 11 行；F4 28 行 |
| 2 | `knowledge_relations` | 8 | relation_id | managed | `row/<t>/[…]` | F1 5 行；F4 0 行 |
| 3 | `problems` | 27 | problem_id | managed | `row/<t>/[…]` | F1 25 行；F4 303 行 |
| 4 | `flash_cards` | 8 | card_id | managed | `row/<t>/[…]` | F1 6 行；F4 0 行 |
| 5 | `questions` | 6 | q_id | managed | `row/<t>/[…]` | F1 0 行；F4 0 行 |
| 6 | `question_progress` | 5 | id | managed | `row/<t>/<installation>/[…]` | F1 0 行；F4 0 行 |
| 7 | `kp_progress` | 3 | kp_id | managed | `row/<t>/[…]` | F1 0 行；F4 0 行 |
| 8 | `problem_progress` | 4 | problem_id | managed | `row/<t>/[…]` | F1 0 行；F4 3 行 |
| 9 | `problem_attempts` | 10 | id | managed | `row/<t>/<installation>/[…]` | F1 12 行；F4 3 行 |
| 10 | `feedback_events` | 7 | id | managed | `row/<t>/<installation>/[…]` | F1 0 行；F4 2 行 |
| 11 | `review_schedule` | 10 | item_type,item_id,direction | managed | `row/<t>/[…]` | F1 0 行；F4 1 行 |
| 12 | `learner_signals` | 11 | signal_id | managed | `row/<t>/[…]` | F1 0 行；F4 6 行 |
| 13 | `learning_current_state` | 4 | item_type,item_id | managed | `row/<t>/[…]` | F1 0 行；F4 1 行 |
| 14 | `kp_experiences` | 6 | kp_id | managed | `row/<t>/[…]` | F1 3 行；F4 0 行 |
| 15 | `kp_experience_problems` | 3 | kp_id,problem_id | managed | `row/<t>/[…]` | F1 0 行；F4 0 行 |
| 16 | `active_practice` | 13 | singleton | managed | `execution/*` | F1 1 行；F4 0 行 |
| 17 | `active_practice_items` | 9 | position | managed | `execution/*` | F1 2 行；F4 0 行 |
| 18 | `paper_state` | 5 | paper_id | managed | `row/<t>/[…]` | F1 2 行；F4 0 行 |
| 19 | `practice_runs` | 14 | id | managed | `row/<t>/<installation>/[…]` | F1 0 行；F4 0 行 |
| 20 | `problem_revisions` | 2 | problem_id | managed | `row/<t>/[…]` | F1 0 行；F4 0 行 |
| 21 | `practice_execution_ids` | 1 | id | managed | `row/<t>/<installation>/[…]` | F1 2 行；F4 0 行 |
| 22 | `attempt_operations` | 11 | request_id,problem_id | managed | `row/<t>/[…]` | F1 0 行；F4 0 行 |
| 23 | `practice_request_operations` | 4 | request_id | managed | `row/<t>/[…]` | F1 0 行；F4 0 行 |
| 24 | `part_attempt_context` | 3 | attempt_id | managed | `row/<t>/[…]` | F1 0 行；F4 0 行 |
| 25 | `part_grading_revisions` | 7 | attempt_id,revision | managed | `row/<t>/[…]` | F1 0 行；F4 0 行 |
| 26 | `part_grading_jobs` | 7 | attempt_id | managed | `row/<t>/[…]` | F1 0 行；F4 0 行 |
| 27 | `content_mirror_state` | 5 | entity_type,entity_id | managed | `row/<t>/[…]` | F1 0 行；F4 0 行 |
| 28 | `content_mirror_log` | 7 | id | managed | `row/<t>/<installation>/[…]` | F1 0 行；F4 0 行 |
| 29 | `content_sequences` | 3 | scope,entity_type | managed | `row/<t>/[…]` | F1 0 行；F4 0 行 |
| 30 | `ingest_batches` | 7 | batch_id | managed | `row/<t>/[…]` | F1 0 行；F4 0 行 |
| 31 | `retired_paper_items` | 11 | paper_id,sequence | managed | `row/<t>/<installation>/[…]` | F1 1 行；F4 0 行 |
| 32 | `course_sync_checkpoint` | 2 | singleton | **不交换** | — | 设备本地账本 |
| 33 | `course_sync_units` | 4 | identity | **不交换** | — | 设备本地账本 |
| — | `candidate_problems` | 22 | candidate_id | **跳过** | — | 仅旧池（F4 有表 0 行） |
| — | `candidate_attempts` | 7 | id | **跳过** | — | 仅旧池（F4 有表 0 行） |

### 1.2 逐表字段清单

以下 31 张表即随包交换的全部持久字段（236 列）。设备本地账本与退役表见 §1.3。
字段行里的「表级 writer / 表级 consumer」指上方该表列出的整行写入与读取模块；有专属写入路径、专属读者或特殊语义的字段在同行单独标注。

### knowledge_points（15 字段）

- 交换：managed（行资产，身份 `row/knowledge_points/["<kp_id>"]`，不带安装来源）
- writer：`content:663,669`（改 `related_kp_ids`／硬删）；`ingest:1434`；`content_mirror:755`；`pool:88`（body/fragile）；`pipeline/scripts/insert-knowledge-points.py`；`pool/scripts/serve-graph.py`
- consumer：`pool:71,80`（`kps`/`kp`）；`ingest`；`relations:189`；`cli/doctor.py:51`；`pipeline/scripts/validate-pool.py`；`pool/scripts/query-pool.py`、`render-graph-html.py`、`serve-graph.py`
- 删除语义：硬删 `content:669`，并级联闪卡/题目/关系/信号/学习行（`content:602-669`）；题目保留但重写 `kp_ids` 且清空六列难度组（`content:642-651`）。**导出侧无墓碑**（见 GAP-01）
- 旧格式：F4 旧池 14 列（无 `ingest_batch_id`）；`graph_label` 由 `pool_schema:258-265` 增量补列，`figure_paths/ingest_batch_id` 由 `pool_schema:912-920` 补列

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `kp_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `knowledge_item` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `graph_label` | `pool_schema:258-265`（只建列，无稳定业务 writer） | 无可靠主消费者 | unresolved（`DATA_MODEL:58`） |
| `source_location` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `knowledge_type` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `related_kp_ids` | `ingest:1434`；`content:663` | `relations` 兼容边投影 | compat（`DATA_MODEL:61`） |
| `importance` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `learning_action` | 仅冻结 pipeline 写入 | 冻结 pipeline／溯源 | legacy（`DATA_MODEL:63`） |
| `body` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `difficulty` | 仅冻结 pipeline 写入 | 冻结 pipeline／兼容查询 | legacy，与题目四维无关（`DATA_MODEL:65`） |
| `fragile` | `pool:88`；冻结 pipeline | 知识点详情／兼容编辑 API | active |
| `created_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `updated_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `figure_paths` | `content_mirror:755` | `figure_mirror`（只读消费） | unresolved；F1/F4 全 NULL |
| `ingest_batch_id` | `ingest`（批次 apply） | 回滚／审计 | active |

### knowledge_relations（8 字段）

- 交换：managed（行资产，`row/knowledge_relations/["<relation_id>"]`）
- writer：`relations:33,76,98`；`content:562,633`（改/删）；`ingest`；`pipeline/scripts/insert-knowledge-relations.py`
- consumer：`relations:189,371`；`pool:209`；`pool/scripts/course_network.py`；图谱渲染脚本
- 删除语义：硬删 `content:562,633`；先清目标信号 `content:631`。导出侧无墓碑（GAP-01）
- 旧格式：F4 有表 0 行；`related_kp_ids` 仍作为低强度兼容边并存（`DATA_MODEL:71-80`）

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `relation_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `source_kp_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `target_kp_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `relation_type` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `direction` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `strength` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `created_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `updated_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### problems（27 字段）

- 交换：managed（行资产，`row/problems/["<problem_id>"]`；删除时带 `deleted: true`）
- writer：`content:256-352`（创建/修改/parts）、`content:409-412`；`content_mirror:732`；`difficulty:42-60`；`display_metadata:42`；`ingest:1298,1820`；`pipeline/scripts/insert-problems.py`；`course_sync:1464-1482`（接收修改）
- consumer：`pool:99`；`records`；`paper_progress`；`display_metadata`；`mastery`；`tutor_handoff`；`pipeline/scripts/validate-pool.py`；`pool/scripts/query-pool.py`
- 删除语义：软删 `deleted_at`（`content:587-592`）+ 卷名单 `paper_progress.remove_question`→`retired_paper_items`；导出为墓碑（`course_sync:291-292`）。**唯一有本地删除记录的实体**
- 旧格式：F4 旧池 12 列；`topic_label` 被 `RETIRED_COLUMNS`（`course_sync:33`）丢弃并记入 inventory；缺 `origin_kind`、六列难度组、`source_*`、`parts`、`deleted_at`、`ingest_batch_id`

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `problem_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `kp_ids` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `problem_text` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `solution` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `problem_type` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `source_kind` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `origin_kind` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `created_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `updated_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `figure_paths` | `content_mirror` | `figure_mirror` | unresolved；F1 10 张有样本 |
| `display_title` | `display_metadata:42`；`ingest` | UI 标题 | F1/F4 全 NULL |
| `display_summary` | `display_metadata:42`；`ingest` | UI（当前无稳定消费） | unresolved（`DATA_MODEL:111`） |
| `practice_modes` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `micro_quiz` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `ingest_batch_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `difficulty` | `difficulty:42-60`；`content_mirror:595-610`（先校验再重算总分/模型） | 练习/筛选/图 | 六列必须全空或全有；内容轴变更清空（`content:325`、`course_sync:1474-1477`）；**F1/F4 无样本** |
| `difficulty_knowledge_breadth` | 同上 | 同上 | 同组约束 |
| `difficulty_reasoning_depth` | 同上 | 同上 | 同组约束 |
| `difficulty_transfer_distance` | 同上 | 同上 | 同组约束 |
| `difficulty_construction_openness` | 同上 | 同上 | 同组约束 |
| `difficulty_model` | 同上（派生） | 同上 | 派生，不得由 ingest 直接赋值 |
| `source_evidence` | `ingest` | 溯源/审计 | F1 有样本 |
| `source_answer` | `ingest` | 揭晓 | F1/F4 全 NULL |
| `solution_origin` | `ingest` | 来源标注 | F1/F4 全 NULL |
| `exam_year` | `ingest` | 筛选 | F1/F4 全 NULL |
| `deleted_at` | `content:592` | 查询排除（`content:126,135`） | **唯一本地删除墓碑来源** |
| `parts` | `content:409-412`；`ingest` | 练习/Agent/批改 | JSON 有序小问；F1 有样本（24 题中 6 题） |

### flash_cards（8 字段）

- 交换：managed（行资产，`row/flash_cards/["<card_id>"]`）
- writer：`ingest:598`；`content:611`（硬删）；`ingest:1419`（批次回滚删）
- consumer：`pool:139,146`；`ingest:1097`；`content:605`
- 删除语义：硬删 + 学习行/信号（`content:608-611`）；导出侧无墓碑（GAP-01）
- 旧格式：F4 无此表；`topic_label` 在此表仍 active（与 `problems.topic_label` 退役相反，`DATA_MODEL:131`）

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `card_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `kp_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `front` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `back` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `source_evidence` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `topic_label` | `ingest` | 筛选/标签 | active；F1 全 NULL |
| `directions` | `ingest` | 卡片正反方向 | F1 有样本 |
| `ingest_batch_id` | `ingest` | 回滚/审计 | F1/F4 全 NULL |

### questions（6 字段）

- 交换：managed（行资产，`row/questions/["<q_id>"]`）
- writer：**当前无 writer**（只有 `content:620` 的级联删除）
- consumer：`pipeline/scripts/validate-pool.py:290`；`pool/scripts/query-pool.py:155`
- 删除语义：硬删（随知识点删除 `content:620`）
- 旧格式：设计意图表（`create-tables.py` 注释：kept for design intent; not populated by Create）；F1/F4 均 0 行

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `q_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `question_text` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `answer_key` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `answer_explanation` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `kp_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `difficulty` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### question_progress（5 字段）

- 交换：managed（行资产，身份带安装来源 `row/question_progress/<installation>/[...]`）
- writer：**当前无 writer**（只有 `content:619` 的级联删除）
- consumer：`pool/scripts/query-pool.py:226`
- 删除语义：硬删（随知识点删除 `content:619`）
- 旧格式：legacy 交互日志表；F1/F4 均 0 行

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `q_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `note` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `mastery_state` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `created_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### kp_progress（3 字段）

- 交换：managed（行资产，`row/kp_progress/["<kp_id>"]`）
- writer：**当前无 writer**（只有 `content:621` 的级联删除）
- consumer：`pool/scripts/query-focus-map.py:129`；`query-pool.py:201`；`render-graph-html.py:171`
- 删除语义：硬删（随知识点删除 `content:621`）
- 旧格式：legacy 吸收状态表；F1/F4 均 0 行

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `kp_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `mastery_state` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `self_assessment` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### problem_progress（4 字段）

- 交换：managed（行资产，`row/problem_progress/["<problem_id>"]`）
- writer：`pool:256`；`attempts:787`；`pipeline/scripts/import-candidates.py:135`
- consumer：`pool:266`；`queries:33`；`attempts:716,765`；`pipeline/scripts/validate-pool.py`
- 删除语义：无删除路径（覆盖式状态）；题目软删时保留
- 旧格式：F4 4 列 3 行（完整旧格式样本）

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `problem_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `status` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `note` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `updated_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### problem_attempts（10 字段）

- 交换：managed（行资产，身份带安装来源 `row/problem_attempts/<installation>/[...]`）
- writer：`attempts:297`（correct 重写）、`attempts:517-575`（浏览器作答）；`pool:247`；`part_practice:110`；`pipeline/scripts/import-candidates.py:145`
- consumer：`records`（8 处）；`pool`；`tutor_handoff:143`；`grading_jobs:23`；`part_grading`；`evidence:61`；`mastery:20`；`pipeline/scripts/validate-pool.py`
- 删除语义：**无删除**（追加式作答事实）；题目软删不删 attempt
- 旧格式：F4 6 列 3 行（无 `verdict/choices/part_id/content_revision`）

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `problem_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `status` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `note` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `created_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `part_id` | `part_practice:110-111` | 批改精确定位 | **F1/F4 全 NULL** |
| `content_revision` | `part_practice:110-111` | 批改/提交校验 | **F1/F4 全 NULL** |
| `answer_text` | `attempts:297,573` | 记录页/批改/Agent 上下文 | F1 有样本（原始作答逐字保留） |
| `verdict` | `attempts:573-575` | 记录页客观判定 | F1 有样本；不得扩大为主观总判定（`DATA_MODEL:185`） |
| `choices` | `attempts:573-575` | 记录页选项 | F1 有样本 |

### feedback_events（7 字段）

- 交换：managed（行资产，身份带安装来源）
- writer：`pool:354`（新增）、`pool:410`（原位改）、`pool:417`（硬删）；`attempts:293`（改正重放）、`attempts:654`（同轮覆盖）
- consumer：`pool:365,371,402`；`records`；`evidence:78`；`mastery:23`；`queries`；`ingest`
- 删除语义：硬删 `pool:417`；实体删除时按 `item_type/item_id` 级联清（`content:594-599`）
- 旧格式：F4 6 列 2 行（无 `attempt_id`）；带 `attempt_id` 的现代行无样本（GAP-08）

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `item_type` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `item_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `rating` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `note` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `created_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `attempt_id` | `attempts:293`；`pool:354` | 记录页回看/批改 | F4 无此列 |

### review_schedule（10 字段）

- 交换：managed（行资产，`row/review_schedule/["<item_type>","<item_id>","<direction>"]`）
- writer：`pool:328`（评分后重排）
- consumer：`pool:320,344`；`attempts:771`；`mastery:27`
- 删除语义：硬删（`content:595`）
- 旧格式：F4 10/10 非空 1 行

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `item_type` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `item_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `direction` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `state` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `repetitions` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `ease` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `interval_days` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `due_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `last_rating` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `last_reviewed_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### learner_signals（11 字段）

- 交换：managed（行资产，`row/learner_signals/["<signal_id>"]`）
- writer：`pool:306`；`attempts:798`；`content:610,631,668`；`relations`；`pool/scripts/learner_signals.py`
- consumer：`attempts:755`；`pool:175`；`ingest`；`pipeline/scripts/validate-pool.py:590`；`pool/scripts/*`
- 删除语义：硬删（`content:610,631,668`）
- 旧格式：F4 10/11 非空 6 行

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `signal_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `target_type` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `target_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `signal_type` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `weight` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `evidence_count` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `note` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `last_practice_kind` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `last_practice_ref` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `created_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `updated_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### learning_current_state（4 字段）

- 交换：managed（行资产，`row/learning_current_state/["<item_type>","<item_id>"]`）
- writer：`attempts:793,801`；`pool:294`；`pool_schema:904`（旧评价回填）
- consumer：`attempts:751,758`；`pool:281,288`
- 删除语义：硬删（`content:595`）
- 旧格式：F4 4/4 非空 1 行

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `item_type` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `item_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `state` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `updated_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### kp_experiences（6 字段）

- 交换：managed（行资产，`row/kp_experiences/["<kp_id>"]`）
- writer：`experience:33,54,75`
- consumer：`experience:11,19`
- 删除语义：硬删（`experience:76`）；`experience_schema:88` 触发器清关联
- 旧格式：F4 无此表；F1 4 行（导出时）→ 期末 3 行（FS-07 删 1）

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `kp_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `content` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `revision` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `updated_by` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `created_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `updated_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### kp_experience_problems（3 字段）

- 交换：managed（行资产，`row/kp_experience_problems/["<kp_id>","<problem_id>"]`）
- writer：`experience:73,112,114`；触发器 `experience_schema:52-73`（成员关系随 `problems.kp_ids` 收敛）
- consumer：`experience:19`
- 删除语义：硬删 + 触发器（`experience_schema:74-96`）
- 旧格式：**F1/F4 均 0 行（GAP-07）**

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `kp_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `problem_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `position` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### active_practice（13 字段）

- 交换：**不作为行资产**：投影为 `execution/<execution_id>`（`course_sync:470-498`），`singleton` 被丢弃
- writer：`active:287-310,447`；`paper_progress:75`；`practice_sets:497`；`course_sync:1283`（接收重建）
- consumer：`active:181`；`attempts:513`；`paper_progress`；`course_sync:1187,1225`；`tutor_handoff:101`
- 删除语义：`active:419-450`（clear）+ `course_sync:1138,1179-1199`（仅更高 Paper generation 的墓碑可清除）
- 旧格式：F4 无此表；旧行 `execution_id=0` 由 `pool_schema:1045-1049` 补

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `singleton` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `source_kind` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `source_ref` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `source_label` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `kp_ids_json` | `active:287-294` | 练习页 | 投影时还原为 `kp_ids` 数组（`course_sync:472`） |
| `practice_mode` | `active:287-294` | 兼容渲染元数据 | 非 Paper 身份（`DATA_MODEL:226-231`） |
| `rating_mode` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `cursor` | `active:453-470`（navigate） | 练习页 | 投影为 presentation 元数据，不参与语义比较 |
| `started_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `updated_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `execution_id` | `active:308,310`；`paper_progress:565` | 浏览器上下文/提交校验 | F1 有样本 |
| `paper_generation` | `active:310` | 陈旧写入拒绝 | F1 有样本 |
| `reveal_timing` | `active:287-290,447` | 练习页揭晓时机 | F1 有样本（`on_submit`/`per_item`）；执行级冻结 |

### active_practice_items（9 字段）

- 交换：**不作为行资产**：投影为 `execution/<execution_id>/item/<position>`（`course_sync:499-524`）；`locked` 被显式丢弃（`course_sync:501`，见 §3.3 存疑）
- writer：`active:299,314,512,559`；`part_practice:36,124`；`course_sync:1231,1291`
- consumer：`active`；`paper_progress`；`tutor_handoff`；`course_sync`
- 删除语义：随 active 行整表清空（`active:433`、`course_sync:1189`）；头部声明集合决定删除（`course_sync:1157-1176`）
- 旧格式：F4 无此表；`content_revision/draft_json/draft_sequence` 由 `pool_schema:1020-1023` 补列

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `position` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `item_type` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `item_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `direction` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `state` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `attempt_id` | `active:512,559`；`part_practice:124` | 提交校验/揭晓 | **F1 全 NULL**；单测覆盖（`test_course_sync_receive.py:870`） |
| `content_revision` | `active:314` | 内容轴陈旧校验 | F1 有样本（默认 1） |
| `draft_json` | `active:512-559`；`part_practice:36` | 暂停恢复 | 投影为 `draft` 对象（`course_sync:502-504`） |
| `draft_sequence` | `part_practice:36`（+1） | 迟到写入拒绝 | 投影为 presentation（`course_sync:524`） |

### paper_state（5 字段）

- 交换：行资产只保留 `paper_id/generation/pending_*`；`checkpoint_json` 被拆成 `execution/*`（`course_sync:464-469`），接收时重组（`course_sync:1310-1329`）
- writer：`paper_progress:32,142,163,224`；`active:889`；`practice_sets`；`course_sync:1197,1248,1306,1324`
- consumer：`paper_progress:81`；`practice_sets:259`；`course_sync:260`；`tutor_handoff`
- 删除语义：`pending_delete=1` + `checkpoint_json=NULL`（`paper_progress:224-245`）；导出前拒绝未落盘的 pending（`course_sync:259-263`）
- 旧格式：F4 无此表（新池启动时由 `pool_schema:1006-1013` 建）

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `paper_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `generation` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `checkpoint_json` | `paper_progress.park/bind_attempts` | 练习恢复/接收重组 | F1 有 2 个暂停卷样本 |
| `pending_json` | `paper_progress:224` | `flush_files`（`paper_progress:237-245`） | **F1 全 NULL**；未落盘时导出被拒 |
| `pending_delete` | `paper_progress:224` | `flush_files` | F1 有样本（0） |

### practice_runs（14 字段）

- 交换：managed（行资产，身份带安装来源）
- writer：`active:353,361`（`_archive`，完成/替换/清除时写）
- consumer：`records`；`paper_progress:259,321`；`active:375,756`；`practice_sets`
- 删除语义：**无删除**（完成轮次历史归档）
- 旧格式：F4 无此表；`execution_id/paper_generation/reveal_timing` 由 `pool_schema:1024-1027` 补列。**F1/F4 均 0 行（GAP-03）**

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `source_kind` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `source_ref` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `source_label` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `kp_ids_json` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `practice_mode` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `rating_mode` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `items_json` | `active:353-361` | 答卷回看 | 声明引用路径被转换（`course_sync:56`、`course_sync_references`） |
| `status` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `started_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `finished_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `execution_id` | `active:353-357` | 反馈校验 | 可为空（旧轮次） |
| `paper_generation` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `reveal_timing` | `active:353-357` | 答卷读取 | 历史快照，NULL 为兼容 |

### problem_revisions（2 字段）

- 交换：managed（行资产，`row/problem_revisions/["<problem_id>"]`）
- writer：`paper_progress:32`（首次修改时写 2）
- consumer：`paper_progress:14`（缺行等价 1）
- 删除语义：无删除（单调版本）
- 旧格式：F4 无此表；**F1/F4 均 0 行**（F1 未修改过题目）

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `problem_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `revision` | `paper_progress:32`（首次修改写 2） | `paper_progress:14`（缺行等价 1） | 作答语义版本 |

### practice_execution_ids（1 字段）

- 交换：managed（行资产，身份带安装来源）
- writer：`active:308`；`paper_progress:565`；`pool_schema:1047`（旧行补身份）
- consumer：无 SELECT；`id` 只作为其他表的执行身份值被引用
- 删除语义：无删除（执行身份不复用）
- 旧格式：F4 无此表；F1 2 行

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `id` | `active:308`；`paper_progress:565`；`pool_schema:1047` | 无 SELECT；作为其他表的 `execution_id` 值被引用 | 自增身份，不复用 |

### attempt_operations（11 字段）

- 交换：managed（行资产，`row/attempt_operations/["<request_id>","<problem_id>"]`）
- writer：`attempts:360`（新增）；`attempts:234,238`（改正重放更新 result）
- consumer：`attempts:375`（按 request 查）、`attempts:382`（按 attempt 查）
- 删除语义：无删除（幂等操作日志，不是学习事件）
- 旧格式：F4 无此表；**F1/F4 均 0 行（GAP-04）**；跨机重放由 `test_course_sync_lifecycle.py:219` 覆盖

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `request_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `problem_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `attempt_id` | `attempts:360` | `attempts:382` | 导出为 attempt 资产身份，接收换回本地号 |
| `kind` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `rating` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `fingerprint` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `batch_fingerprint` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `result` | `attempts:360,234,238` | `attempts:375,382` | 声明引用路径被转换（`course_sync:58`）；操作日志不是学习事件 |
| `pre_state` | `attempts:360` | 审计/重放 | 快照原样携带（`course_sync_references` `_snapshot`） |
| `post_state` | `attempts:360` | 审计/重放 | 同上 |
| `created_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### practice_request_operations（4 字段）

- 交换：managed（行资产，`row/practice_request_operations/["<request_id>"]`）
- writer：`attempts:699`（浏览器请求幂等日志）
- consumer：`attempts:687`（相同载荷重放）
- 删除语义：无删除
- 旧格式：F4 无此表；**F1/F4 均 0 行（GAP-04）**

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `request_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `payload` | `attempts:699` | `attempts:687` | 声明引用路径被转换（`course_sync:59`） |
| `result` | `attempts:699` | `attempts:687`（相同载荷重放） | 缓存投影同样转换（`course_sync:59`） |
| `created_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### part_attempt_context（3 字段）

- 交换：managed（行资产，`row/part_attempt_context/["<attempt_id>"]`）
- writer：`part_practice:112`（小问提交同事务）
- consumer：`grading_jobs:24`（Agent target 读取）
- 删除语义：无删除（提交时定义快照）
- 旧格式：F4 无此表；**F1/F4 均 0 行（GAP-05）**

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `attempt_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `execution_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `part_json` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### part_grading_revisions（7 字段）

- 交换：managed（行资产，`row/part_grading_revisions/["<attempt_id>","<revision>"]`）
- writer：`part_grading:124`（追加修订/tombstone）
- consumer：`part_grading:70,78,105`（当前结果/审计）
- 删除语义：**追加式**：撤回写新 tombstone（`withdrawn=1`），不删历史
- 旧格式：F4 无此表；**F1/F4 均 0 行（GAP-05）**

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `attempt_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `revision` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `operation_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `request_json` | `part_grading:124` | `part_grading:70,105` | 仅元素 0 的引用被转换（`course_sync:60`） |
| `payload_json` | `part_grading:124` | `part_grading:78` | 原样携带（`_opaque`） |
| `withdrawn` | `part_grading:122-126` | `part_grading:62,70` | 撤回＝新 tombstone，不删历史 |
| `created_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### part_grading_jobs（7 字段）

- 交换：managed（行资产，`row/part_grading_jobs/["<attempt_id>"]`）；接收时 `pending/running` 拒绝、`conversation_id/turn_id` 置空（`course_sync:1377-1383`）
- writer：`part_practice:117`（提交写 pending）；`grading_jobs:42,56,70`
- consumer：`grading_jobs:12,34,51,65`；`part_practice:182`
- 删除语义：无删除（状态机 pending/running/completed/failed）
- 旧格式：F4 无此表；**F1/F4 均 0 行（GAP-05）**；单测 `test_course_sync_receive.py:402-424,904-917` 覆盖

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `attempt_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `execution_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `status` | `part_practice:117`（pending）；`grading_jobs:42,56,70` | `grading_jobs:12,34,51,65`；`part_practice:182` | 接收时 pending/running 拒绝（`course_sync:1377-1379`） |
| `error` | `grading_jobs:42,56` | `part_practice:182` | 失败原因随历史保留 |
| `conversation_id` | `grading_jobs:42` | `grading_jobs:8-13`（归属判定） | **接收置空**：会话属于发送机（`course_sync:1380-1383`） |
| `turn_id` | `grading_jobs:42` | Bridge 恢复 | **接收置空**（同上） |
| `updated_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### content_mirror_state（5 字段）

- 交换：managed（行资产，`row/content_mirror_state/["<entity_type>","<entity_id>"]`）
- writer：`content_mirror:239`（只在显式 mirror 同步事务内）
- consumer：`content_mirror:215,234,256`（三方比较基线）
- 删除语义：无删除（基线）
- 旧格式：F4 无此表；**F1/F4 均 0 行（GAP-06）**

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `entity_type` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `entity_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `revision` | `content_mirror:239` | `content_mirror:215,234` | 只随被接受的修改 +1，不由哈希派生 |
| `content_json` | `content_mirror:239` | `content_mirror:256` | 三方比较基线（不是第二份内容） |
| `updated_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### content_mirror_log（7 字段）

- 交换：managed（行资产，身份带安装来源）
- writer：`content_mirror:248`（只追加成功记录）
- consumer：无读取代码（只作审计/证据）
- 删除语义：无删除（append-only）
- 旧格式：F4 无此表；**F1/F4 均 0 行（GAP-06）**

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `entity_type` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `entity_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `direction` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `from_revision` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `to_revision` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `created_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### content_sequences（3 字段）

- 交换：managed（行资产，`row/content_sequences/["<scope>","<entity_type>"]`）
- writer：`content:231,238`；`ingest:1462`；`pool_schema:887`（建库时按现有 ID 回填）
- consumer：`content:215`（下一个可读 ID）
- 删除语义：无删除
- 旧格式：F4 无此表（旧池按 `-kp-NNN` 后缀推导）；**F1/F4 均 0 行（GAP-06）**

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `scope` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `entity_type` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `next_value` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### ingest_batches（7 字段）

- 交换：managed（行资产，`row/ingest_batches/["<batch_id>"]`）
- writer：`ingest:1626`（批次 apply）；`ingest:2145`（rollback 记时）
- consumer：`ingest:1390,1854,1876,2070`
- 删除语义：无删除（`rolled_back_at` 标记，非删行）
- 旧格式：F4 无此表；**F1/F4 均 0 行（GAP-06）**

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `batch_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `kind` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `manifest_path` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `counts_json` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `backup_path` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `applied_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `rolled_back_at` | `ingest:2145` | `ingest:1854` 等 | 回滚标记，不删行 |

### retired_paper_items（11 字段）

- 交换：managed（行资产，身份带安装来源：`row/retired_paper_items/<installation>/[...]`，`HISTORY_TABLES`，`course_sync:51`）；接收端取本地下一序号并记录映射（`course_sync:1418-1439`）
- writer：`paper_progress:212`（`_retire_item`，改名单/删题时）
- consumer：`paper_progress:209`（记录页/队列回看）；`course_sync:1434`（下一序号）
- 删除语义：**只增不改**；`attempt_id` 悬空容忍并记入 `dangling_history_references`（`course_sync:53,339-346`、`295-296`）
- 旧格式：F4 无此表：首次写入时迁移（`course_sync:1369-1373`、`1424-1425`；`pool:458-481`）；`test_course_sync_lifecycle.py:204` 覆盖旧库首收

| 字段 | writer | consumer | 备注 |
|---|---|---|---|
| `paper_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `sequence` | `course_sync:1433-1439`（接收端取本地下一序号） | `paper_progress:209`（续号） | 跨机同号并存，不按发送端编号绑定 |
| `problem_id` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `position` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `state` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `attempt_id` | `paper_progress:212` | 记录页回看 | 悬空容忍：记入 `dangling_history_references` 并置空（`course_sync:53,339-346`） |
| `content_revision` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |
| `draft_json` | `paper_progress:212` | 回看最后确认草稿 | F1 有样本 |
| `draft_sequence` | `paper_progress:212` | 迟到写入拒绝 | F1 有样本 |
| `reason` | `paper_progress:212`（membership／deleted 等） | 记录页解释 | F1 有样本 |
| `retired_at` | 表级 writer（整行写入） | 表级 consumer（`SELECT *` 后按字段访问） |  |

### 1.3 不进入交换的表

| 表 | 字段 | 理由 | 证据 |
|---|---|---|---|
| `course_sync_checkpoint` | 2（`singleton`、`state_json`） | 接收账本；投影前被剔除 | `course_sync:250`、`pool:484-494` |
| `course_sync_units` | 4（`identity`、`asset_json`、`mappings_json`、`pending_json`） | 同上（逐单元覆盖） | `course_sync:250`、`pool:484-494` |
| `candidate_problems` | 22（旧池列含 `topic_label`、`structure_gate_status` 等） | `RETIRED_TABLES`：只跳过并记入 inventory，不导出 | `course_sync:30,254-258,297-299`；F4 实测 |
| `candidate_attempts` | 7（`id`、`candidate_id`、`status`、`selected_option_id`、`is_correct`、`note`、`created_at`） | 同上 | 同上 |

### 1.4 数据一致性核对

- 交换登记表 `course_sync.TABLES` 共 33 项 = 31 张实存交换表 + 2 张退役表名；实测库中不存在未登记的表（探针 `tmp/accept/e1_probe.py`：新增 `unexpected_data` 表后导出报 `ValueError: unregistered course tables: unexpected_data`）。
- 字段总数 242 = 236（交换）+ 6（两张账本表）；`problems.topic_label` 只存在于旧池，不进入 236。
- 无主键的表会被拒绝导出（`course_sync:268-269`），实测 33 张表均有主键。

## 2. data-exchange-matrix 逐行对照

覆盖状态口径：**完整**＝该类每个承载表/文件在 F1 或 F4 中都有行级样本且关键字段非空；**部分**＝有行级样本但关键字段或子表为空；**无**＝F1/F4 均为 0 行；**不适用**＝按设计不进入包。

| # | 矩阵类别（`data-exchange-matrix.md` 行号） | 实际承载 | writer / consumer 要点 | F1 样本 | F4 样本 | 状态 |
|---|---|---|---|---|---|---|
| 1 | 知识点（:13） | `knowledge_points` + `.lessonkit/figures/**` | 见 §1.2 | 11 行，7/15 非空 | 28 行，11/14 非空（旧列） | **完整**（行级） |
| 2 | 正式关系（:14） | `knowledge_relations` | `relations` | 5 行，8/8 | 0 行 | **完整** |
| 3 | 正式题与小问（:15） | `problems`（`parts`/`micro_quiz`/`source_*`）、`problem_attempts.part_id`、`part_attempt_context` | `content`/`ingest`/`part_practice` | 25 行，15/27；`parts` 6 题；`micro_quiz` 8 题 | 303 行，10/12（旧列） | **部分**：小问提交/批改链 0 行（GAP-05） |
| 4 | 闪卡（:16） | `flash_cards` | `ingest` | 6 行，6/8 | 0 行（无表） | **完整** |
| 5 | 难度与显示元数据（:17） | `problems` 六列难度组 + `display_title/display_summary` | `difficulty`、`display_metadata`、`content_mirror` | 全 NULL | 无该组列 | **无**（GAP-02） |
| 6 | 图片与附件（:18） | `.lessonkit/figures/**`（按 `problems/knowledge_points.figure_paths` 引用收集） | `figure_mirror` | 10 张 | 无文件 | **完整**（字节级） |
| 7 | 试卷（:19） | `.lessonkit/practice-sets/<ps-NNN>.json` + `paper_state` | `practice_sets`、`paper_progress` | 3 个卷文件 + 2 个暂停卷 | 无 | **完整** |
| 8 | 活动执行（:20） | `active_practice`、`active_practice_items`、`paper_state.checkpoint_json` | `active` | 1 个选中执行 + 2 个暂停卷 | 无 | **完整** |
| 9 | 完成执行（:21） | `practice_runs` | `active._archive` | 0 行 | 无表 | **无**（GAP-03） |
| 10 | 原始作答（:22） | `problem_attempts`、`part_attempt_context` | `attempts`、`part_practice` | 12 行，8/10 | 3 行，6/6（旧列） | **部分**：`part_id/content_revision` 全 NULL（GAP-05） |
| 11 | 反馈与修订（:23） | `feedback_events`、`part_grading_revisions` | `pool`、`part_grading` | 0 行 | 2 行，6/6（旧列） | **部分**：修订 0 行、现代反馈 0 行（GAP-05/GAP-08） |
| 12 | 学习信号/进度/排期（:24） | `learner_signals`、`learning_current_state`、`problem_progress`、`review_schedule`（+ legacy `kp_progress`/`question_progress`） | `pool`、`attempts` | 0 行 | 6/1/3/1 行（10/11、4/4、4/4、10/10） | **部分**：legacy 两张 0 行（GAP-09） |
| 13 | 经验总结（:25） | `kp_experiences`、`kp_experience_problems` | `experience` | 3 行（导出时 4），6/6；关联 0 行 | 无表 | **部分**：题目关联 0 行（GAP-07） |
| 14 | 课程目标（:26） | `.lessonkit/goals.json` | `data/goals.py`（写）、`queries`/`tutor_handoff`（读）、`course_sync:371-378`（交换；损坏即失败） | 2 个目标 | 无 | **完整** |
| 15 | 学习偏好（:27） | `.lessonkit/course-preferences.json`（四个学习键）+ 执行级 `reveal_timing` | `course_preferences`、`course_preferences_api`、`active` | 无偏好文件；`reveal_timing` 有样本 | 无 | **部分**：偏好文件 0 样本（GAP-10） |
| 16 | 课程学习文件（:28） | `.lessonkit/learning/**` 与 `managed_paths` 登记的 Markdown/JSON | 文件系统 writer；`tutor_handoff` 读；`course_sync:379-381,403-412` 交换 | 8 个 `.md` + FS-02 新增 1 个 | 无 | **部分**：只有 `.md`（GAP-11） |
| 17 | 原始教材/讲义/试卷（:29） | `managed_paths` 登记的任意文件（F1：`textbook.pdf`） | 同上 | 1 份 2.0 MiB PDF（2,097,180 B），字节保留 | 无 | **完整** |
| 18 | 请求操作身份（:30） | `attempt_operations`、`practice_request_operations` | `attempts` | 0 行 | 无表 | **无**（GAP-04） |
| 19 | 批改/Provider 运行作业（:31） | `part_grading_jobs`（`jobs/` 会话目录按设计排除） | `grading_jobs`、`part_practice` | 0 行 | 无表 | **无**（GAP-05；仅单测） |
| 20 | 镜像和序列状态（:32） | `content_mirror_state`、`content_mirror_log`、`content_sequences`、`ingest_batches` | `content_mirror`、`content`、`ingest` | 0 行 | 无表 | **无**（GAP-06） |
| 21 | 派生缓存（:33） | `.lessonkit/plan.json`、`jobs/`、锁/PID | 不进投影：`course_sync:424-426` 显式拒绝 `jobs`/`.git`/`course-sync` 路径；`plan.json` 不在受管集合内 | 不适用 | 不适用 | **不适用** |
| 22 | 撤回题历史（矩阵未列，change 4.1） | `retired_paper_items` | `paper_progress`、`course_sync` | 1 行（FS-06 删题后） | 无表（旧库首收迁移） | **完整** |

F1 列为期末（FS-07 删除之后）状态：导出时 `knowledge_points` 为 12 行、`kp_experiences` 为 4 行（见 §3.3 第 3 条）。

矩阵未列、但实际存在的交换表：`questions`、`question_progress`、`kp_progress`（legacy 设计表，§1.2 已登记）、`problem_revisions`、`practice_execution_ids`、`paper_state` 的非 checkpoint 列、`course_sync_checkpoint/units`（不交换）。这些在 §1.2 逐字段登记，不静默略过。

## 3. 未知类型/表/列/格式的实际行为

### 3.1 导出侧（本机 schema → 包）

| 情形 | 行为 | 证据 |
|---|---|---|
| 未登记的表 | **显式失败**，整次导出拒绝 | `course_sync:250-253`；实测 `ValueError: unregistered course tables: unexpected_data`（`tmp/accept/e1_probe.py`） |
| 已登记的退役表 | 跳过并写入 inventory `retired_tables` | `course_sync:254-258,297-299`；`tests/workbench/test_course_sync_data.py:385` |
| 已登记的退役列 | 从行与 inventory 中剔除，记 `retired_columns` | `course_sync:272-279`；`tests/workbench/test_course_sync_data.py:404`；F4 实测 `retired_columns:["topic_label"]` |
| **未登记的新列** | **静默随包导出**（无列白名单） | 实测 `ALTER TABLE knowledge_points ADD COLUMN memo` 后导出 `status=success`，行资产与 inventory 均含 `memo`（`tmp/accept/e1_probe.py`）。与 `FILE_CONTRACT.md:827`「any other unknown table or column remains an explicit failure」冲突 → **GAP-12** |
| 无主键的表 | 显式失败 | `course_sync:268-269` |
| 未落盘的 Paper 文件意图 | 显式失败 | `course_sync:259-263` |
| 引用图片缺失 | 显式失败 | `course_sync:392-395`；`test_course_sync_data.py:213` |
| `goals.json` 损坏 | 显式失败 | `course_sync:375-377` |
| `managed_paths` 缺失/越界 | 显式失败 | `course_sync:397-412`、`_relative` `course_sync:111-131` |
| base 中有、本机已消失且无墓碑 | 显式失败（GAP-01 的机制） | `course_sync:541-544` |

### 3.2 接收侧（包 → 本机 schema）

| 情形 | 行为 | 证据 |
|---|---|---|
| 未知 `format_version`（非 1/2） | **整包拒绝**，不逐项降级 | `course_sync:1554-1556`、`course_bundle.py:50-52`；`test_course_sync_data.py:255-268`；实测 `ValueError: unsupported course exchange format_version` |
| 未知 asset `kind` | 逐项 `invalid_asset`，其他资产继续 | `course_sync:1573-1581`；实测 `invalid asset envelope` |
| 行资产 `table` 不在 `TABLES` | 逐项 `invalid_asset: invalid row projection`，不加载 | `course_sync:1599-1603`；实测同一结果 |
| 行资产含目标 schema 没有的列 | 逐项 `invalid_asset: row does not match the target course schema` | `course_sync:674-682`；`test_course_sync_data.py:145-158`；实测被剔除且其他资产保留 |
| 目标缺整张表（除 `retired_paper_items`） | 整表资产按 `invalid_asset` 拒绝（不做可执行迁移） | `course_sync:674-682`、`FILE_CONTRACT.md:833`；**无旧库缺表接收样本**（GAP-13） |
| 目标缺 `retired_paper_items` | 校验用静态列声明，首写时迁移 | `course_sync:706-712,1369-1373,1424-1425`；`test_course_sync_lifecycle.py:204` |
| 执行项/执行头不完整 | 逐项 `invalid_asset`，同组依赖被阻断 | `course_sync:913-938`、`683-690` |
| `part_grading_jobs` 为 `pending/running` | 拒绝导入（不派发 Provider 作业） | `course_sync:1377-1379`；`test_course_sync_receive.py:402` |
| 不安全相对路径/编码 | 逐项 `invalid_asset` | `course_sync:1614-1622`；`test_course_sync_data.py:233` |
| `files/` 下新增普通文件 | 视为显式创建（不是未知类型） | `course_sync:1656-1671` |
| `files/` 中缺失的声明文件 | 不构成删除 | `course_sync:1654-1655` |

结论：**未知表、未知资产类型、未知目标列、未知格式版本都不会静默略过**；唯一无法识别的是导出侧的“本机新增列”，它没有列白名单可对照（GAP-12）。

### 3.3 存疑项（需主线确认，不擅自裁决）

1. `course_sync:501` 的 `item.pop("locked", None)`：当前 schema 无 `locked` 列，`RETIRED_COLUMNS` 也未声明它。这只可能是更早旧池遗留列的防御性丢弃，但 `DATA_MODEL`/`FILE_CONTRACT` 无对应记载，也无 F4 样本证明它存在过。**存疑原因**：无契约依据、无旧格式证据。
2. 执行项 `attempt_id` 在 F1 全为 NULL，`retired_paper_items.attempt_id` 亦然。引用转换逻辑有单测（`test_course_sync_receive.py:870`、`test_course_sync_lifecycle.py:181`），但“真实样本往返后 attempt 引用仍指向正确 attempt”缺 F1/F4 证据。**存疑原因**：夹具未建立带 attempt 链接的暂停卷。
3. F1-A 期末 `knowledge_points=11` 而最后一次导出的 `base` 含 12 个身份（`reply2` 包 inventory=12）：FS-07 之后未再导出，所以 P3 的“FS-07 通过”只证明本地删除效果，**不证明删除可传播**；若此时再导出必定失败（与 GAP-01 同一机制）。这是对既有 P3 结论范围的收窄，不是推翻。

## 4. 浏览器保存值

浏览器持久化位置共 4 类（`wb_settings_*`、两个纸卷出站箱、图谱布局种子）；只有服务端投影 `.lessonkit/course-preferences.json` 以“已确认保存值”的身份进入课程交换。

| 键/文件 | writer | consumer | 是否随包交换 | 证据 |
|---|---|---|---|---|
| `wb_settings_<workspace>`（localStorage JSON） | `workbench.js:301-307`（`saveSetting`） | `workbench.js:289-299`（`loadSetting`）、`:309-316`（显示偏好）、`:369-373` | **否，仅交互镜像**；其中 4 个学习键通过 `saveLearningSetting` 同步到服务端投影（`:414-425`） | `workbench.js:287`、`DATA_MODEL:328` |
| ↳ 学习键 `showRating`/`showSource`/`submissionGranularity`/`revealTiming` | `workbench.js:1353,1361,1372,1530,1539,1548` | 练习页（`paper-practice.js:261`、`part-practice.js:15`） | 只有写进 `.lessonkit/course-preferences.json` 后才交换 | `DATA_MODEL:326-330` |
| ↳ 设备键 `theme`/`readingFace`/`motion`/`sound`/`runningSendAction` | `workbench.js:1559,1572,1585,1593,1601,1845`；`sfx.js:29-30` | 本机界面 | **否**（设备外观不在课程投影内） | `DATA_MODEL:330` |
| `.lessonkit/course-preferences.json` | `course_preferences.save_preferences`（`course_preferences.py:48-63`），入口 PATCH `/api/w/{name}/course-preferences`（`server/course_preferences_api.py:23-31`） | `load_preferences`（`course_preferences.py:40-45`）、GET（`server/course_preferences_api.py:15-21`）、浏览器 hydration（`workbench.js:380-402`） | **是**：`course_sync:371-378` 按受管文件收集；接收走文件单元（`course_sync:1521-1547`）。损坏文件导出时不校验、接收后由浏览器显式报错 | `FILE_CONTRACT.md:823` |
| `wb_paper_practice_<workspace>_<execution_id>` | `paper-practice.js:283` 起（失败重试出站箱） | 同一执行恢复 | **否**（不是学习事实） | `DATA_MODEL:296` |
| `wb_paper_draft_<workspace>_<execution_id>_<position>` | `practice-flow.js:778` 起 | 逐题草稿恢复 | **否** | `DATA_MODEL:294` |
| `lk_graph_layout_v1_<workspace>` | `graph-physics.js:47` 起（Worker 稳定后写一次） | 同文件读取 | **否**（本地缓存，损坏只丢布局起点） | `DATA_MODEL:314-320` |
| `sessionStorage`（模式/评分/闪卡方向/`wb_agent_scope_*`） | 各页面 | 各页面 | **否**（会话级） | `workbench.js:17`、`DATA_MODEL:296` |

要点：真正被交换的“浏览器保存值”只有 `.lessonkit/course-preferences.json` 与执行级 `reveal_timing`（`active_practice`/`practice_runs`）。未确认的浏览器输入不会被当作已保存状态导出（`DATA_MODEL:328`、`FILE_CONTRACT.md:823`）。

## 5. GAP 清单

| ID | GAP | 类型 | 证据 | 影响 |
|---|---|---|---|---|
| GAP-01 | **本地删除无法记录/传播**：只有 `problems.deleted_at` 会生成墓碑；闪卡、知识点、关系、经验、学习文件、卷文件等硬删后，下一次导出报 `managed assets are missing without explicit deletion`，且无名命令可记录显式删除或清理 `base` | 行为缺口 | `course_sync:291-292,541-544`；探针 `tmp/accept/e1_delete_probe.json`（闪卡、学习文件、知识点三种删除各自复现；知识点删除后即使把学习文件恢复也无法再导出，因为缺失的是知识点资产）；F1 期末状态 | 与矩阵「文件 CRUD」「明确删除记录才传播」不符；按原身份重建前同步不可用，且用户无从得知该身份仍挂在 `base` 里 |
| GAP-02 | 难度组与显示元数据无任何非空样本：F1 `problems` 15/27 非空，六列难度 + `display_*` 全 NULL；F4 旧池无该组列 | 覆盖缺口 | F1/F4 非空实测；`difficulty:42-60`、`display_metadata:42` | “逐字段核对”只能证明空值可往返，不能证明值可往返 |
| GAP-03 | `practice_runs`（完成执行）0 样本 | 覆盖缺口 | F1/F4 均 0 行 | 答卷回看、`items_json` 引用转换无真实样本 |
| GAP-04 | `attempt_operations`、`practice_request_operations` 0 样本 | 覆盖缺口 | F1/F4 均 0 行 | 幂等/跨机重放只有单测（`test_course_sync_lifecycle.py:219`） |
| GAP-05 | 小问批改链 `part_attempt_context`/`part_grading_revisions`/`part_grading_jobs` 0 样本；`problem_attempts.part_id/content_revision` 全 NULL | 覆盖缺口 | F1/F4 非空实测；单测 `test_course_sync_receive.py:402-424,904-917` | “正式题与小问”“原始作答”“反馈与修订”“批改作业”四行都只能记部分 |
| GAP-06 | 镜像与序列 `content_mirror_state`/`content_mirror_log`/`content_sequences`/`ingest_batches` 0 样本 | 覆盖缺口 | F1/F4 均 0 行 | 矩阵第 20 类无真实样本 |
| GAP-07 | `kp_experience_problems` 0 样本（F1 只建经验正文，不建题目关联） | 覆盖缺口 | F1 实测 | 经验与题目的关联从未被交换验证 |
| GAP-08 | `feedback_events` 只有 F4 旧 6 列 2 行；带 `attempt_id` 的现代行 0 样本 | 覆盖缺口 | F4 实测；`pool:354` | 记录页回看/原位覆盖路径无真实样本 |
| GAP-09 | `questions`/`question_progress`/`kp_progress` 0 样本，且当前代码**无 writer**，只有级联删除 | 覆盖缺口 + 存量表定性 | `content:619-621` 仅 DELETE；`create-tables.py` 注释 | 三张表随包交换但无本机产生路径，建议登记为 legacy（不阻断） |
| GAP-10 | 学习偏好文件 `course-preferences.json` 无 F1/F4 样本（F1 未保存偏好；P3 浏览器 PATCH 未走交换） | 覆盖缺口 | `course_sync:371-378`；`f1-report.json` 无偏好步骤 | 矩阵第 15 类只由 `reveal_timing` 支撑 |
| GAP-11 | 课程学习文件只有 Markdown 样本；JSON/二进制/误解-续接专类文件无样本 | 覆盖缺口 | F1 bundle `files/` 清单 | “任意已登记课程文件原文保真”未覆盖非文本 |
| GAP-12 | **未知列导出侧不报错**：本机新增列会随包导出并进 inventory；`FILE_CONTRACT.md:827` 要求“any other unknown column remains an explicit failure” | 契约漂移 | 探针 `tmp/accept/e1_probe.py`；`course_sync:265-277`；`FILE_CONTRACT.md:827` | 发送端新列会被旧接收端逐项拒绝（已是 `invalid_asset`），但导出侧不会提前报错，排障成本转移给接收方 |
| GAP-13 | 旧库缺表接收无样本（除 `retired_paper_items`）：缺表时整表资产按 `invalid_asset` 拒绝 | 覆盖缺口 | `course_sync:674-682`；`FILE_CONTRACT.md:833`；`tasks.md:34`（4.4 未完成） | LIFE-SYNC 全矩阵仍缺旧库接收证据 |
| GAP-14 | 执行草稿内 per-part `attempt_id` 引用无样本（F1 草稿只有 `answer`） | 覆盖缺口 | `course_sync:502-519`、`course_sync_references:51-61`；只有单测 | 混合小问卷的草稿往返未验证 |

### 5.1 按影响排序的三条

1. **GAP-01**（删除传播）——唯一会让同步彻底不可用的行为缺口，需主线决定：为每类资产增加“显式删除记录”写入路径，或提供 `course-sync forget <identity>` 之类的受控入口，并定义“删除 vs 修改”冲突选侧。
2. **GAP-12**（未知列导出不报错）——契约漂移，需决定是给导出加列白名单（严格）还是修订 `FILE_CONTRACT.md:827`（宽松）。两者都可行，但必须选一边。
3. **GAP-02/GAP-03**（难度组、完成执行零样本）——不是代码缺陷，而是台架缺口：要给 F1 补上非空难度组与一次真实交卷，否则“逐字段核对”无法覆盖最容易在转换中丢失的派生组。

## 6. 未做/未验证

- 未跑全仓 pytest（主线在跑别的）；本文件引用的单测均为已存在用例，未重跑。
- 未修改生产代码、未 commit、未写任何真实课程池。
- F1/F4 的字节级往返、时序等属 2.3/3.2 的证据范围，本文件只核对字段/表/样本覆盖。
- F2（大规模）与 F3（异常变体）不在 2.1 的样本口径内，本文件未引用其数据。
