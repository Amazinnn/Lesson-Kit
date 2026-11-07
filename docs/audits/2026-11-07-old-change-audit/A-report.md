# 任务书 A 报告：老 change 完成度核对

工作区：`D:\.codex\worktrees\course-sync\lesson-kit`（分支 `codex/course-sync`，HEAD `e5dc981b`）
判定依据：当前磁盘上的实现与测试；未使用真实课程目录、未起服务、未提交。
本次只复跑了两个聚焦测试文件（`tests/workbench/test_feedback_crud.py`、`tests/workbench/test_micro_quiz.py`，37 passed），其余全仓验证命令未复跑；凡属"跑命令"的验收项一律记 UNSURE 并写明缺哪条证据。

---

## remove-micro-quiz-error-reason（0/18）
verdict: COMPLETE（指 13 个实现/文档/测试项；6.1–6.4 是未复跑的验收命令）

- [1.1] SHIPPED — 实现: `workbench/domain/micro_quiz.py:81-96`（`validate_payload` 不再检查 `error_reason`，docstring 也已改）；测试: `tests/workbench/test_micro_quiz.py:73::test_a_supplied_key_is_still_checked`（带键但无 `error_reason` 期望 0 错误）；提交: `6b12b9ec`。
- [1.2] SHIPPED — 历史 payload 仍可校验/入库：`tests/workbench/test_micro_quiz.py:27-32` 的 fixture 仍带 `error_reason` 且断言 `errors == []`；`tests/workbench/test_content_bundle.py:35` 的 manifest 仍带该字段并走通 apply。
- [1.3] SHIPPED — `FILE_CONTRACT.md:204-205` 明确写了 legacy `error_reason` 被忽略、不再是必填项。
- [2.1] SHIPPED — `workbench/server/static/paper-practice.js:789-796` 只保留「参考答案」「解析」；全仓 `grep 判定依据` 除本 change 工件与无关 change 的历史文案表外无渲染代码。
- [2.2] SHIPPED — `tests/workbench/paper_practice.test.js:337`（`::single-choice selection submits once and shows the returned locked result`）断言 `paper-reference` 不含「判定依据」；`tests/workbench/workbench_ui_interactions.test.js` 已无该 section 的期望。
- [3.1] SHIPPED — `workbench/resources/skills/source-bounded-learning-drill/SKILL.md` 无 `error_reason` 命中。
- [3.2] SHIPPED — `skills/pool-pipeline/references/prompt-t1.md`、`skills/pool-pipeline/references/example.md` 无命中。
- [3.3] SHIPPED — `skills/pool-pipeline/scripts/preflight.py` 无命中。
- [4.1] SHIPPED — `tests/workbench/test_micro_quiz.py:73`、`tests/workbench/test_content_bundle.py:787` 已改为"不需要"语义；`tests/workbench/test_data_cli.py` / `test_problem_patch.py` / `test_ingest.py` 中残留的 `error_reason` 都是历史 fixture，不再断言 required。
- [4.2] SHIPPED — 测试: `tests/workbench/test_content_bundle.py:787::test_a_keyed_item_does_not_need_an_error_reason`。
- [4.3] SHIPPED — 历史值加载：`tests/workbench/test_micro_quiz.py:27-32`；不渲染「判定依据」：`tests/workbench/paper_practice.test.js:337`（fixture `paper_practice.test.js:73` 本身带 `error_reason`）。
- [5.1] SHIPPED — `docs/DATA_MODEL.md:113`、`docs/GLOSSARY.md:581`、`docs/ACTION-GRAPH.md:385`；`docs/REQUIREMENTS.md`、`docs/PRODUCT-MANUAL.md` 本就没有该字段可删。
- [5.2] SHIPPED — `docs/ACTION-GRAPH.md:385`、`docs/action-graph/L3-actions.md:79` 已登记退役及"无新增 CLI 动作"。
- [6.1] UNSURE — 缺证据: 本次未复跑全仓 `pytest`（仅跑了 2 个聚焦文件，37 passed），无 CI 记录附着在本 worktree。
- [6.2] UNSURE — 缺证据: 本次未复跑 `compileall`。
- [6.3] UNSURE — 缺证据: 本次未复跑 `openspec validate --specs --strict`。
- [6.4] UNSURE — 缺证据: 本次未跑 `guard extract-problems`（且该命令会读真实课程目录，按只读约束跳过）。
- [6.5] SHIPPED — 实测 `grep -rn "error_reason" workbench/resources/skills skills/pool-pipeline` 无命中。

---

## evaluation-terminology-and-agent-crud（0/31）
verdict: MOSTLY

- [1.1] SHIPPED — `workbench/server`、`workbench/data`、`workbench/domain`、`tests/workbench` 已无「自评」；用户可见文案改为「评价」，如 `workbench/server/pages.py:421`、`workbench/server/static/practice-flow.js:1100`、`workbench/server/static/paper-practice.js:897`。
- [1.2] PARTIAL — 已有: `docs/DATA_MODEL.md`、`docs/ARCHITECTURE.md`、`docs/REQUIREMENTS.md`、`docs/ACTION-GRAPH.md`、`docs/action-graph/L1-L4`、`docs/GLOSSARY.md:654` 已改名；缺: `docs/PRODUCT-MANUAL.md:9` 仍有「不会自动生成自评」。
- [1.3] PARTIAL — 已有: 本 change 四份 spec delta 已用「评价」，`openspec/changes/complete-live-display-preferences/specs/workbench-ui/spec.md` 也已同步；缺: `openspec/specs/workbench-ui/spec.md:1066`、`:1080` 仍写「关闭自评」（实现侧已是「评价」，见 `workbench/server/pages.py:998`）。
- [1.4] PARTIAL — grep gate 未完全通过：除历史文件/别名/「避免」条目外，仍有 `docs/PRODUCT-MANUAL.md:9` 与 `openspec/specs/workbench-ui/spec.md:1066,1080` 两处 live 残留。
- [2.1] SHIPPED — 实现: `workbench/data/pool.py:361`（feedback_events）、`:375`（for_attempt）、`:382`（by id）、`:388`（rows list）、`:408`（targeted update）、`:415`（hard delete）。
- [2.2] SHIPPED — 实现: `workbench/data/evaluations.py:95`（list）、`:107`（get）、`:111`（add）、`:152`（update）、`:167`（delete）；校验见 `:39-62`。
- [2.3] SHIPPED — 任何 writer/item_type 都可改删，且必须带 expected：`workbench/data/evaluations.py:152-171`；测试: `tests/workbench/test_feedback_crud.py:119::test_stale_expected_values_are_refused`、`:138::test_missing_expected_values_are_refused`。
- [2.4] SHIPPED — 只改/只删 `feedback_events` 一行，不重放投影：`workbench/data/pool.py:408-420`；测试: `tests/workbench/test_feedback_crud.py:66`、`:172`（断言 attempts/progress/schedule 不变）。
- [2.5] SHIPPED — 可选 `attempt_id`、重复拒绝并回现有 id：`workbench/data/evaluations.py:126-148`；测试: `tests/workbench/test_feedback_crud.py:204::test_add_with_attempt_id_refuses_a_duplicate`。
- [2.6] SHIPPED — `lesson-kit feedback add/list/get/update/delete`：`workbench/cli/main.py:436-506`（命令）、`:1110-1128`（parser，默认 `add`）。
- [2.7] SHIPPED — 字段齐备：`workbench/data/evaluations.py:81-92`（event_id/item_type/item_id/rating/note/attempt_id/created_at/agent_recorded/correctable）。
- [3.1] SHIPPED — `workbench/bridge/agent_contracts.py:74-81` 写明 get/list/add/update/delete、expected rule、hard delete/no replay、Agent 可自选 1-5。
- [3.2] SHIPPED — `workbench/bridge/conversations.py:760`（attempts 主题含「评价」）、`:766-767`（改/删前先 `feedback get` 的 read-before-modify 行）。
- [3.3] SHIPPED — `TASK_ROUTER.md:17` 已含 feedback get/list/update/delete 路由。
- [3.4] SHIPPED — `docs/PRODUCT-MANUAL.md:480-481`（第 8 章内）写明同一行评价可改/删、以及"改分只改评价行，不重放掌握度"的所有权边界。
- [4.1] SHIPPED — 测试: `tests/workbench/test_feedback_crud.py:66::test_agent_updates_and_deletes_a_browser_written_evaluation`。
- [4.2] SHIPPED — 测试: `tests/workbench/test_feedback_crud.py:94::test_agent_updates_an_agent_written_evaluation_without_redirect`。
- [4.3] SHIPPED — 测试: `tests/workbench/test_feedback_crud.py:119`、`:138`（conflict 零写入 + missing expected 报错）。
- [4.4] SHIPPED — 测试: `tests/workbench/test_feedback_crud.py:149::test_note_only_evaluation_can_be_updated_and_deleted`。
- [4.5] SHIPPED — 测试: `tests/workbench/test_feedback_crud.py:172::test_knowledge_point_and_card_evaluations_use_the_same_path`。
- [4.6] PARTIAL — 已有: 契约文本 `workbench/bridge/agent_contracts.py:81` 明确 "You may choose or change the 1-5 rating yourself"；`tests/workbench/test_attempts.py:259` 证明 manifest 可自带 rating 而不需学习者输入。缺: 没有一条专门断言"Agent 在无学习者给分时自行选分"的用例。
- [4.7] SHIPPED — 测试: `tests/workbench/test_feedback_crud.py:204`。
- [4.8] SHIPPED — 测试: `tests/workbench/test_feedback_crud.py:227::test_legacy_feedback_add_still_works`。
- [4.9] PARTIAL — 已有: 浏览器 stale expected 冲突：`tests/workbench/test_attempts.py:899::test_browser_rating_edit_is_in_place_and_bound_to_its_paper_run`（`:970-978` 断言 stale `expected_rating` 冲突且零写入）。缺: 该用例的"旧值"来自浏览器自己的前一次编辑，没有"Agent 先改、浏览器随后用旧值提交"的跨 writer 序列用例。
- [4.10] SHIPPED — 测试: `tests/workbench/workbench_ui_interactions.test.js:4924`（`::an empty rating input is rejected inline instead of dying at the server`）断言 `/请输入 1–5 的评价/`；测试数据中已无「自评」。
- [5.1] UNSURE — 缺证据: 本次只跑了 `test_feedback_crud.py`（8 项）与 `test_micro_quiz.py`，未复跑全仓。
- [5.2] UNSURE — 缺证据: 本次未跑 `compileall`。
- [5.3] UNSURE — 缺证据: 本次未跑 `openspec validate --specs --strict`。
- [5.4] UNSURE — 缺证据: 本次未跑 `guard extract-problems`（只读约束）。
- [5.5] SHIPPED（以自动化等价覆盖）— add/get/update/delete/stale 冲突由 `tests/workbench/test_feedback_crud.py:66,119,149,204` 覆盖；未做真实 CLI 冒烟。
- [5.6] PARTIAL — prompt 契约行存在（`workbench/bridge/conversations.py:766-767`）但无测试断言；「自评」grep gate 因 1.2/1.3 的残留未通过。

---

## import-attempts-into-paper-progress（0/37）
verdict: MOSTLY

- [1.1] SHIPPED — 实现: `workbench/data/paper_progress.py:441-485` `preview_binding`（mode/execution_id/positions/states/actions/progress_before/after/completion，零写入）；测试: `tests/workbench/test_attempts.py:1289::test_check_previews_paper_binding_without_writing`。
- [1.2] SHIPPED — 实现: `workbench/data/paper_progress.py:487-598` `bind_attempts`（写前校验 Paper 成员、continuation、generation、content revision）；测试: `tests/workbench/test_attempts.py:1241`（非成员零写入）。
- [1.3] SHIPPED — 新 checkpoint 分支：`workbench/data/paper_progress.py:487-598`（mode=new 时 `_new_items` + `on_submit`，不写 active/practice_runs）；测试: `tests/workbench/test_attempts.py:1103::test_import_creates_parked_on_submit_progress_without_learning_effects`。
- [1.4] SHIPPED — 实现: `workbench/data/active_practice.py:595-634` `bind_attempt`（answered、清 pending 草稿/不会、保留 `reference_viewed`、不逐题归档）；测试: `tests/workbench/test_attempts.py:1142::test_import_rebinds_an_answered_item_and_keeps_the_old_attempt`。
- [1.5] SHIPPED — 实现: `workbench/data/active_practice.py:636-660` `finish_if_complete`（legacy 无 pending 才归档；per_item/on_submit 留待交卷）；测试: `tests/workbench/test_attempts.py:1220::test_legacy_active_paper_archives_when_import_fills_the_last_item`。
- [1.6] SHIPPED — 实现: `workbench/data/practice_sets.py:437-532` `append_saved`（幂等卷末追加、generation bump、active item/checkpoint 追加）；测试: `tests/workbench/test_saved_practice_sets.py:123,156,194,215,230`。
- [2.1] SHIPPED — manifest 顶层 `paper_id` 校验成员与可用性：`workbench/data/attempts.py:23`、`:103-115`、`:130-155`。
- [2.2] SHIPPED — `attempts check` 零写入 preview：`workbench/data/attempts.py:153`（调用 `preview_binding`）；测试: `tests/workbench/test_attempts.py:1289`。
- [2.3] SHIPPED — `attempts apply` 同事务绑定并把 binding 写进 `attempt_operations.result`：`workbench/data/attempts.py:47-67`、`:212-230`；重放保持原绑定：`tests/workbench/test_attempts.py:1255`。
- [2.4] SHIPPED — `paper_id` 进入幂等指纹：`workbench/data/attempts.py:822-830`；测试: `tests/workbench/test_attempts.py:1300::test_same_request_id_with_a_different_paper_is_refused`。
- [2.5] SHIPPED — `attempts get` 只读 Paper linkage：`workbench/data/attempts.py:713`（`attempt_paper`）。
- [2.6] SHIPPED — CLI `papers <ws> append <ps-NNN> --problem <id>` 与 JSON receipt：`workbench/cli/papers.py:18`、`:48-51`；测试: `tests/workbench/test_papers_cli.py:164::test_append_adds_a_problem_at_the_end_without_resetting_progress`。
- [2.7] SHIPPED — attempts help 写明 optional `paper_id`：`workbench/cli/main.py:1186`；surface 说明更新：`workbench/surface.py:195`。
- [3.1] SHIPPED — `workbench/bridge/agent_contracts.py:58-69` 写明 `paper_id`、三种绑定目标、rebind、completion、只改执行进度。
- [3.2] SHIPPED — practice 主题的 `papers append` 及其与 `papers update` 的区别：`workbench/bridge/agent_contracts.py:83-85`、`:106`。
- [3.3] SHIPPED — content 主题的缺题治理序列与 source-fidelity：`workbench/bridge/agent_contracts.py:189`。
- [3.4] SHIPPED — 注入提示词的 Paper 导入与缺题规则，且普通辅导仍零写入：`workbench/bridge/conversations.py:763-764`。
- [3.5] SHIPPED — `TASK_ROUTER.md:14`（papers append）、`:16`（attempts manifest 含 paper_id）。
- [4.1] SHIPPED — 测试: `tests/workbench/test_attempts.py:1103`（新 checkpoint + 不改学习投影）、`tests/workbench/test_attempts.py:1220`（legacy 归档）、`tests/workbench/test_attempts.py:1180`（parked 不碰当前卷）。
- [4.2] SHIPPED — 测试: `tests/workbench/test_attempts.py:1142`（answered 重绑 + 旧 attempt 保留）；stuck 重绑路径由同一 `bind_attempt` 覆盖（`active_practice.py:595-634` 对 `stuck` 同样走 state=answered）。
- [4.3] SHIPPED — 测试: `tests/workbench/test_attempts.py:1103`（无 rating 导入只改执行进度）。
- [4.4] PARTIAL — 已有: 非成员零写入 `tests/workbench/test_attempts.py:1241`、幂等重放 `:1255`、整批回滚 `tests/workbench/test_attempts.py:310::test_one_invalid_item_protects_the_whole_batch`（实现先整批 `_validate` 再进事务，`workbench/data/attempts.py:47-49`）。缺: 未知/无效 `paper_id`（Paper 不存在）的零写入用例。
- [4.5] SHIPPED — 测试: `tests/workbench/test_attempts.py:1289`。
- [4.6] SHIPPED — 测试: `tests/workbench/test_saved_practice_sets.py:123`（active）、`:156`（parked）、`:230`（无进度）、`:194`（幂等重复）、`:215`（未知题拒绝）。
- [4.7] SHIPPED — 测试: `tests/workbench/test_papers_cli.py:164`。
- [4.8] PARTIAL — 已有: 契约文本 `workbench/bridge/agent_contracts.py:69`（`paper_id` 绑定语义）、`:83-85`/`:189`（三步走）。缺: 没有测试断言这两段契约文本；`tests/workbench/test_agent_contracts.py` 未覆盖 `paper_id`/`papers append`。
- [5.1] MISSING — 任务定义为"归档时同步四份 delta 到 `openspec/specs/`"；本 change 尚未归档，live specs 中无对应新增 requirement，按任务本身属于已推迟项（不应现在勾选）。
- [5.2] SHIPPED — `FILE_CONTRACT.md:533-560` 含 `paper_id` manifest 契约与"同 id 不同内容/不同 Paper 拒绝"。
- [5.3] SHIPPED — `docs/DATA_MODEL.md:300-310` 写明 `paper_id` 是 manifest 输入、绑定不改 learning progress。
- [5.4] SHIPPED — `docs/GLOSSARY.md:1030`（导入绑定）、`:1035`（Paper 追加题）、`:1025`（试卷执行进度）。
- [5.5] SHIPPED — `docs/PRODUCT-MANUAL.md`、`docs/REQUIREMENTS.md`、`docs/ARCHITECTURE.md` 在同提交 `7ab4cd19` 内有同步。
- [5.6] SHIPPED — `docs/ACTION-GRAPH.md` 与 `docs/action-graph/L0-L4.md` 均在同提交 `7ab4cd19` 内更新（如 `docs/action-graph/L4-workflows.md`）。
- [6.1] UNSURE — 缺证据: 本次未复跑全仓 `pytest`。
- [6.2] UNSURE — 缺证据: 本次未跑 `compileall`。
- [6.3] UNSURE — 缺证据: 本次未跑 `openspec validate`。
- [6.4] UNSURE — 缺证据: 本次未跑 guard（只读约束）。
- [6.5] UNSURE — 缺证据: 没有临时 workspace 的 CLI 冒烟记录附着在当前 worktree；自动化等价覆盖见 4.1-4.7。

---

## json-content-repository-sync（33/36，只看未勾的 3 项）
verdict: MOSTLY

- [7.1] SHIPPED — 外部仓库已使用 `courses/<course-id>/{knowledge,problems,relations}`：`D:\Projects\Academic Workflow\Lesson-Kit-Content\courses\c02\knowledge`、`...\c04\problems`、`...\c13\relations`、`...\c14\relations`；仓库根已无 `entities/`（实测 `ls entities` 不存在）；契约见 `D:\Projects\Academic Workflow\Lesson-Kit-Content\README.md`（"Repository shape" 段）。
- [7.2] PARTIAL — 已有: deletion-request 样例存在，如 `D:\Projects\Academic Workflow\Lesson-Kit-Content\delete-requests\c03-del-ch01-prob-108.json`（同目录另有 8+ 个）；解析器支持见 `workbench/data/content_mirror.py:316-343`。缺: 全仓 `find courses -name course.json` 无任何结果；README 把 `course.json` 记为 "reserved course metadata surface"，没有可运行的示例。
- [7.3] SHIPPED — 外部仓库提交 `98e3f8a8` 标题即 "feat: bootstrap c02 and c04 as acceptance samples"，diff 落在 `courses/c02/knowledge/*.json` 与 `courses/c04/*`；目录中没有 workspace debris（仅 knowledge/problems/relations）。

---

## ingest-integrity-and-observability（3/44）
verdict: NOT-STARTED

- [1.4] MISSING — `workbench/domain/micro_quiz.py:122-148` 的 `validate_problem_row` 仍不检查 `problem_type` 枚举（普通题分支有 `PROBLEM_TYPES` 检查）。
- [2.1] MISSING — `docs/adr/` 止于 `0028-graph-lod-and-layout-seeds.md`；没有任何 pipeline/`--upsert` 决策 ADR，grep `docs/adr` 无相关条目。
- [2.2] MISSING — `pipeline/scripts/insert-problems.py:257` 仍是 `INSERT OR REPLACE INTO problems`（6 列）；`:65` 的 `--upsert` help 仍在。
- [2.3] MISSING — `pipeline/scripts/insert-knowledge-points.py:246` 仍打印 "Continuing with valid rows only..."，`:297` 仍 `return 0`；`:255` 仍是 `INSERT OR REPLACE`。
- [2.4] MISSING — `pipeline/scripts/candidate_contract.py:12` 的 `COLLAPSED_SUBPART_PATTERN` 未收窄。
- [2.5] MISSING — `pipeline/scripts/validate-pool.py:152-163` 仍把 `candidate_problems`/`candidate_attempts` 列为 required；早退见 `:612-614`。
- [2.6] MISSING — `pipeline/scripts/validate-pool.py:32` 的 `PROBLEM_ID_PATTERN` 仍只接受 `-prob-NNN`。
- [2.7] MISSING — 没有决定"哪个 sweep 是验收信号"的文档/ADR（grep 无命中）。
- [3.1] MISSING — 无稳定 id 方案或"拒绝 id 位移"的门禁；`pipeline/scripts/insert-problems.py:110` 仍只校验显式 id 格式。
- [3.2] PARTIAL — 已有: 问题清单的 kp 必须存在：`pipeline/scripts/insert-problems.py:143-147`（`kp_id '...' not found in knowledge_points`）。缺: 反向（KP→problems）核对与"清单 KP 数 vs 声明拆分"。
- [3.3] MISSING — `workbench/ingest/__init__.py:246` 仍默认 `<db>.ingest-backup` 单一路径（存在即报错），没有 per-batch 备份与保留策略；pipeline 侧同样未改。
- [3.4] MISSING — 没有独立的 knowledge-point ingest ledger；`_record_batch`（`workbench/ingest/__init__.py:1624-1631`）只记单一 kind。
- [3.5] PARTIAL — 已有: `FILE_CONTRACT.md:417-419` 现在列出了 kp 的 `source_location/related_kp_ids/fragile/graph_label`（镜像投影字段）。缺: 没有 ingest manifest 自身的 schema（9 种 key set 的归一化）。
- [3.6] MISSING — `docs/DATA_MODEL.md:59` 只有"位置/出处指针"的描述，没有 `§syllabus-chapter.textbook-section` 的 schema/validator。
- [3.7] MISSING — 无字段区分"题源无答案"与"抽取失败"；grep `solution_absent/no_answer_reason/solution_state` 无命中。
- [3.8] MISSING — 无新的去重指纹实现；`pipeline/` 未见 CJK 保留或 50 字符前缀替代。
- [3.9] MISSING — 无 difficulty anchors 进入 manifest；`grep anchor/cognitive-v1` 在 `pipeline/scripts` 与 `workbench/data/difficulty.py` 无命中。
- [3.10] MISSING — `workbench/ingest/__init__.py:2594-2599` 的 `_accounting` 只是当前表计数（写前快照），没有"事务内观察到的 counts"与记录值互校；rollback 场景外的 requirement 也未新增。
- [4.1] MISSING — `workbench/data/difficulty.py:9-14` 仍自称"complete rating manifest"，`check` 只校验非空+逐项。
- [4.2] MISSING — 无 re-anchor 实现/记录（课程侧工作，仓库无证据）。
- [4.3] MISSING — 无对 `content-dedup-and-audit` 的长度校验排序声明（该 change 亦不在 `openspec/changes/`）。
- [5.1] MISSING — `pool/scripts/render-graph-html.py` 无 graph_label 唯一性/章节名校验。
- [5.2] MISSING — 截断检测仍只有 `pipeline/scripts/insert-knowledge-points.py:127-128` 的 `len(graph_label) > 24`（未改）。
- [5.3] MISSING — 搜索语料仍是 `[id,label,graph_label,body,source_location]`：`pool/scripts/render-graph-html.py:1313`（未含 `learning_action`）。
- [5.4] MISSING — fragile 过滤仍是 `Boolean(node.fragile)`：`pool/scripts/render-graph-html.py:1315`。
- [5.5] MISSING — 无跨章关系一等公民实现（graph 读取仍按 manifest/池现状）。
- [6.1] PARTIAL — 已有: `openspec/changes/ingest-integrity-and-observability/design.md:363-405` 独立重算了大部分数字，并显式列出未核项。缺: 143 前缀去重跳过、419 手写 KP 归属、`【…】` 标题准确率、`ncmc` 全部计数仍标为 "Unverified"（同文件 `:398-403`）。
- [6.2] MISSING — `pipeline/` 无 textbook 抽取的 re-entrancy/probe/partial 守卫（grep `partial|probe|reentran` 无实现）。
- [6.3] MISSING — 无关于 ingest log 用途的决定；`design.md:357` 只是缺陷记录。
- [7.1] SHIPPED（作为记录）— 多边保留/空 `knowledge_relations` 的说明已写入 `design.md:95-108` 与 `tasks.md:81`；注意 `openspec/specs/review-workbench/spec.md:389-391` 的"one edge for unordered pair"场景仍未更新，任务本身写明"下一次触碰 review-workbench 时更新"。
- [7.2] SHIPPED（作为记录）— refuted 假设与每章引用数写入 `design.md:409-434`。
- [7.3] SHIPPED（作为记录）— LIKE 缺 `%` 的证伪与 `31` ids 复算写入 `design.md:110-118`。
- [8.1] MISSING — 无把 §3.1/3.2/3.3 交接给后续 change 的记录；`openspec/changes/` 下没有承接的 `workbench-content-governance` change。
- [8.2] MISSING — 无 `pipeline/` 分层决定/交接记录（见 2.1）。
- [8.3] MISSING — `content-dedup-and-audit` 不在 `openspec/changes/`，无交接。
- [8.4] MISSING — 无 P0-5/P0-6 交接记录。
- [9.1] MISSING（按设计故意未决）— seam boundary 仍是 NEW-GAP，无实现/决定。
- [9.2] MISSING（按设计故意未决）— fragile/learning_action 测量带未定。
- [9.3] MISSING（按设计故意未决）— body 边界是否可调未定。
- [9.4] MISSING（OUTSIDE）— ncmc 正文重写属课程工作，无仓库证据。
- [9.5] MISSING（DOCTRINE）— upsert 冻结决策未定（同 2.1）。

---

## mature-course-content-operations（0/15）
verdict: NOT-STARTED

说明：本 change 是规划工件（`proposal.md` 末段自述 "This is a planning artifact"），程序状态 `docs/design/workbench-capability-maturation/STATUS.md` 明确"其他工作包仍未开工，当前仅 WP01 在推进"。

- [1.1] MISSING — 无本包基线记录（分支/commit/运行身份/重叠 change）；`docs/design/workbench-capability-maturation/evidence/` 下只有 `expand-file-mediated-course-sync` 的证据目录。
- [1.2] MISSING — 无逐条核对 MODIFIED/REMOVED delta 与次级引用的记录。
- [1.3] MISSING — 无 F1/F3/F4 回归样本或失败检查记录。
- [2.1] PARTIAL — 已有: 通用读取 `workbench/data/content.py:129`（list_items）、`:144-157`（search，按整行 JSON 关键词 AND）。缺: type/章/文字组合筛选、经验与来源检索、关联题目去重；`grep knowledge_type` 在 `content.py` 只出现在字段白名单 `:33`。
- [2.2] MISSING — 无"先查同义已有点"或"新增点含条件/公式/步骤并自动追加原题关联"的实现；`workbench/bridge/agent_contracts.py:189` 只规定缺题时如何创建题目。
- [2.3] MISSING — 知识点无独立章节归属列：`pool/scripts/pool_schema.py:258-265` 对 `knowledge_points` 只增量加 `graph_label`；无回填/推章消费者。
- [2.4] PARTIAL — 已有: bundle 仍是单事务原子应用 `workbench/ingest/__init__.py:626-631`（docstring 即 "one atomic content bundle"）。缺: 按 bundle/problem-patch/card/quiz/figure 拆成独立完整单元、独立有效项先完成、无效项保留。
- [2.5] MISSING — 成功批次撤销仍在：CLI `workbench/cli/main.py:813-814`、`:1287`（`ingest rollback`），Agent 契约仍称可回滚：`workbench/bridge/agent_contracts.py:142`、`:185`。
- [2.6] MISSING — 无 20 个映射/完整性案例的标注与结构/语义分离报告。
- [3.1] MISSING — 未见本包命中文件的 GLOSSARY/DATA_MODEL/FILE_CONTRACT/ARCHITECTURE/PRODUCT-MANUAL/ACTION-GRAPH/surface/提示词/agent_contracts 同步记录（本包尚未实施）。
- [3.2] MISSING — 无 DATA-01–05、CONTENT-01、FLOW-03 的夹具/次数/门槛证据。
- [3.3] MISSING — 无 RELEASE-01 及本包 Node/浏览器检查记录。
- [3.4] MISSING — 无 RELEASE-02 副本迁移/备份恢复/安装身份核对记录。
- [3.5] MISSING — 无独立验收角色复核记录。
- [3.6] MISSING — 无按路径提交的可验证单元（本包无专属提交）。

---

## retire-project-approval-gates（0/13）
verdict: NOT-STARTED

说明：项目级决定已存在（`AGENTS.md` 的"取消项目审批"，以及规划树 S008），但代码与测试仍是审批门实现。`docs/PRODUCT-MANUAL.md:576` 仍描述审批卡与「批准更新」。

- [1.1] MISSING — 无本包基线记录（分支/commit/运行身份/重叠 change）。
- [1.2] MISSING — 无 delta 核对与次级引用迁移记录。
- [1.3] MISSING — 无 F1/F3/F4 回归样本/失败检查。
- [2.1] MISSING — 直接执行未接通：Paper 变更仍走提议+批准：`workbench/bridge/agent_contracts.py:134`（"waits for the learner's separate approval click"）、`workbench/bridge/conversations.py:768`（"提交 paper_update_proposal 请求人工批准"）。
- [2.2] MISSING — 无一次性 pending approval 迁移实现；审批状态仍在 `workbench/bridge/conversations.py:284`、`:426-480` 持久化。
- [2.3] MISSING — 审批卡/按钮仍在：`workbench/server/pages.py:1177-1185`（`ai-paper-approval`、取消/批准按钮）、`workbench/server/static/workbench.js:3993-4026`；审批暂停仍阻断继续：`workbench/bridge/conversations.py:1015-1018`、`:1251-1252`、`:1306-1310`；测试仍钉住审批：`tests/workbench/test_paper_approval.py:181::test_pending_approval_queues_messages_blocks_continue_and_cancel_keeps_backlog_paused`。
- [2.4] MISSING — 无直接切换/安装身份/资源版本核对的执行记录。
- [3.1] MISSING — 未退役 GLOSSARY/DATA_MODEL/FILE_CONTRACT/ARCHITECTURE/PRODUCT-MANUAL/ACTION-GRAPH/surface/提示词/agent_contracts 中的审批语义（现状仍在，见 2.1/2.3）。
- [3.2] MISSING — 无 FLOW-01–03、RELEASE-02 证据。
- [3.3] MISSING — 无 RELEASE-01/Node/浏览器检查记录。
- [3.4] MISSING — 无 RELEASE-02 记录。
- [3.5] MISSING — 无独立验收复核记录。
- [3.6] MISSING — 无本包可验证提交。

---

## stabilize-agent-message-continuity（0/14）
verdict: NOT-STARTED

说明：本 change 是规划工件（`proposal.md` 末段自述）。部分行为由更早的归档 change（`2026-10-18-preserve-agent-messages-and-tool-outcomes`、`2026-10-21-compact-agent-queue-and-direct-interrupt` 等）先行落地，但本包自己的任务大多未做，尤其 2.4 要求的"删除排序/立即发送"与当前实现相反。

- [1.1] MISSING — 无本包基线记录。
- [1.2] MISSING — 无 delta 核对/次级引用迁移记录。
- [1.3] MISSING — 无 F1/F3/F4 回归样本。
- [2.1] PARTIAL — 已有: 测试内可计数的假 provider 与提交身份记录，如 `tests/workbench/test_conversations.py:107`（call 记录）、`:369`（`submission_id="send-partial"`）、`:1389`（`process.wait.call_count`）。缺: 任务要求的"UI 重复呈现 vs 真实重复操作"成对夹具及接受次数/provider 次数/数据库变化的统一记录。
- [2.2] PARTIAL — 已有: 失败消息保留在流中 `tests/workbench/test_conversations.py:356-366`；未知送达复用原身份并保护草稿 `tests/workbench/agent_session_ui.test.js:427::an unknown send survives reload and reconciles with the same identity without replacing a draft`；显式重试用 linked 新身份 `tests/workbench/agent_session_ui.test.js:594-601`（`retry_of` + 新 `submission_id`）。缺: "重试用**当前编辑文本**"——`workbench/server/static/workbench.js:4736-4743` 仍复制 `item.body` 的原文，测试也断言 `body.message === "Retry me"`（`agent_session_ui.test.js:602`）。
- [2.3] PARTIAL — 已有: 主动停止保留积压暂停 `tests/workbench/test_agent_queue.py:461::test_successful_interrupt_keeps_existing_older_backlog_paused`；失败不自动重放 `tests/workbench/agent_session_ui.test.js:1310`（"failures wait for a manual send"）。缺: 重启后 never-started 的"保持暂停"语义；现有用例是 `tests/workbench/test_agent_queue.py:592::test_recovery_fails_unstarted_interrupt_instead_of_queueing_or_replaying`（失败而非保持暂停）。
- [2.4] MISSING — 与要求相反：pending 队列仍渲染排序手柄（`workbench/server/static/workbench.js:4343` aria-label "调整消息顺序"）、立即发送（`:4431` `"send-now"`）、排序路由（`:4479` `POST .../queue/reorder`），后端仍有 `workbench/bridge/conversations.py:1199`（`reorder_queue`）与 `:1247`（send-now）。
- [2.5] PARTIAL — 已有: 两课程同题 ID 的隔离测试 `tests/workbench/test_attempts.py:722::test_attempts_and_corrections_stay_inside_their_workspace`。缺: A→B 切题时发送上下文不变的浏览器级 CHAT-01–05 证据。
- [3.1] MISSING — 未见本包专属的 GLOSSARY/DATA_MODEL/FILE_CONTRACT/ARCHITECTURE/PRODUCT-MANUAL/ACTION-GRAPH/surface/提示词/agent_contracts 同步（现有文案来自其他 change）。
- [3.2] MISSING — 无 CHAT-01–05 夹具/次数/门槛证据。
- [3.3] MISSING — 无 RELEASE-01 记录。
- [3.4] MISSING — 无 RELEASE-02 记录。
- [3.5] MISSING — 无独立验收记录。
- [3.6] MISSING — 无本包可验证提交。

---

## complete-practice-continuity-and-rich-titles（0/14）
verdict: NOT-STARTED

说明：本 change 是规划工件（`proposal.md` 末段自述）。未完成 Paper 的继续/暂停能力已由 `2026-10-19-free-navigation-paper-practice` 等归档 change 部分提供，但本包的目标（无淘汰上限、标题富文本、启动恢复 last course）未交付。

- [1.1] MISSING — 无本包基线记录。
- [1.2] MISSING — 无 delta 核对记录。
- [1.3] MISSING — 无 F1/F3/F4 回归样本。
- [2.1] PARTIAL — 已有: 同一 Paper 的未完成执行会被恢复，`workbench/data/active_practice.py:863-889`（`start_saved` 读 `paper_state.checkpoint_json`）与 `workbench/data/practice_sets.py:219-236`（每个保存 Paper 暴露 `continuation`）。缺: "所有未完成 Paper 执行在练习开始处可发现、无计数/年龄淘汰"的 30 卷夹具；"启动恢复 last course"未实现（`workbench/data/course_preferences.py` 无 last-course 字段，`grep last_course` 无命中）。
- [2.2] PARTIAL — 已有: 按 `execution_id` 校验并暂停当前执行、清除其草稿：`workbench/data/active_practice.py:419-437`（`clear`），API `workbench/server/api.py:505`。缺: 对**任意 parked 执行**按 `execution_id` 清除；晚到请求与本地出站箱身份校验的用例（该出站箱属 Agent 消息，不在练习路径）。
- [2.3] MISSING — 标题未走安全 richText：`workbench/server/static/paper-practice.js:737` 标题用 `escapeHtml(title)`，正文才用 `richText`（`:738`）；`workbench/server/pages.py:1133-1142` 的 `_problem_title/_problem_summary` 也是纯文本。
- [2.4] MISSING — 无"Markdown/LaTeX/特殊字符/长标题/打开取消/原样保存"的逐字段用例或实现。
- [2.5] UNSURE — 缺证据: `workbench/server/static/workbench.js` 有 `aiMutationIsCurrent` 一类延后刷新守卫，但未找到针对"当前输入/IME/未确认写入"在练习页面的 PRACTICE-03 实测或测试；无法判断是否覆盖该任务。
- [3.1] MISSING — 未见本包专属契约同步（现有 CONTENT 文档是其他 change 的产物）。
- [3.2] MISSING — 无 PRACTICE-01–04 证据。
- [3.3] MISSING — 无 RELEASE-01 记录。
- [3.4] MISSING — 无 RELEASE-02 记录。
- [3.5] MISSING — 无独立验收记录。
- [3.6] MISSING — 无本包可验证提交。

---

## connect-evidence-guided-learning（0/15）
verdict: NOT-STARTED

说明：本 change 是规划工件（`proposal.md` 末段自述 "This is a planning artifact"）。仓库里已有若干零件（`workbench/data/evidence.py`、`goals.py`、`domain/planning.py`、`data/tutor_handoff.py`），但没有把"目标/范围→短诊断→代表题→反馈→复习"接成工作流；包内指定的目标测试文件 `tests/workbench/test_evidence_guided_learning.py` 不存在。

- [1.1] MISSING — 无教学分支 commit/调用图核对记录（`session_machine`/`registry`/`forms`/`guardrails` 无实现或记录）。
- [1.2] MISSING — 无目标/范围→短诊断→代表题→反馈→复习的接线实现；`grep session_machine|evidence_guided|evidence-guided` 无命中。
- [2.1] MISSING — 无本包入口调用图/运行身份记录。
- [2.2] MISSING — 无短诊断与分段覆盖实现（无 session machine、无诊断题序）。
- [2.3] PARTIAL — 已有: 证据读取 `workbench/data/evidence.py`、合法 writer（feedback/schedule/attempts）均已存在。缺: 把"猜对/看答案/未答不算稳定掌握"形成判断并只经合法 writer 落地的教学判定层。
- [2.4] MISSING — 无主线/返回点、已完成/待补、时间预算的持久与读回；`workbench/data/tutor_handoff.py:101-140` 只读当前 Paper 位置，不是教学 mainline/return point。
- [2.5] PARTIAL — 已有: Agent 契约/提示词存在通用"读取上下文、写入需明确意图"规则（`workbench/bridge/conversations.py:750-770`）。缺: "请求帮助才给最小提示、逐步加深"的专门规则与来源/不确定性回答一致性测试。
- [2.6] MISSING — 无 12 脚本/5 目标 50 题标注/迁移题材料核对，也无免费真实 LLM 执行记录。
- [3.1] MISSING — 未见本包专属契约同步。
- [3.2] MISSING — 无 LEARN-01–05、LP-03–06 证据。
- [3.3] MISSING — 无 RELEASE-01 记录。
- [3.4] MISSING — 无 RELEASE-02 记录。
- [3.5] MISSING — 无独立验收记录。
- [3.6] MISSING — 无本包可验证提交。

---

## 需要人决断

1. **evaluation change 的两处 live 文案残留**：`docs/PRODUCT-MANUAL.md:9`（「自评」）与 `openspec/specs/workbench-ui/spec.md:1066,1080`（「关闭自评」）。是补两处文案即可勾 1.2/1.3/1.4，还是把它们归入后续 copy 清理？我倾向补文案（实现侧 `pages.py:998` 已是「评价」）。
2. **evaluation 4.9/4.6 的"测试算不算"**：4.9 只有浏览器 stale 冲突用例，没有"Agent 先改、浏览器后提交旧值"的跨 writer 序列；4.6 只有契约文本 + manifest 自带 rating 的旁证。按严格口径应保持未勾，或补两条小用例。
3. **import change 4.4/4.8**：4.4 缺"无效/未知 `paper_id`"的零写入用例（非成员、整批回滚、幂等重放都有）；4.8 的 Agent 契约文本已存在（`agent_contracts.py:69,83-85,189`），但 `tests/workbench/test_agent_contracts.py` 没有 `paper_id`/`papers append` 断言。是否接受"文档任务只需文本存在"，以及是否补无效 Paper 用例？
4. **json-content 7.2**：外部仓库没有任何 `course.json` 样例。是补一个空/示例 `course.json`，还是把 README 的 "reserved" 视为该任务的最终形态？
5. **ingest-integrity §7 的勾法**：7.1–7.3 的"记录"职责已由 `design.md` 承担，但 7.1 明确要求下一次触碰 `review-workbench` 时更新 `spec.md:389-391` 的旧场景。现在勾 7.1 会让人误以为 spec 已修正；建议拆成"记录已完成 / spec 更新待办"。
6. **mature/retire/stabilize/practice/evidence 五个包的性质**：它们都是规划工件，`STATUS.md` 说 WP02 之后未开工，且 retire 的实现与 `AGENTS.md` 的"取消审批"决定相反。建议这五个 change 不做逐项勾选，而是标注"未开工/规划中"，避免把规划文档当成交付证据。
7. **stabilize 2.4 与现状方向冲突**：任务要求删除排序/立即发送，但这两个控件当前是完整实现且有测试（`test_agent_queue.py:109,259`）。是否意味着该包的部分任务已被后续产品决定推翻，需要先改 tasks 再谈勾选？

---

## 总体总结

可以**整份勾完**的只有 `remove-micro-quiz-error-reason`：18 项里 13 个实现/文档项全部能在当前树找到实现与测试，5 个"跑命令"的验收项本次未复跑（记 UNSURE），其中 6.5 的 grep gate 已实测无命中。

只能**部分勾选**的有三个：`evaluation-terminology-and-agent-crud`（31 项里约 21 项可勾，1.2/1.3/1.4/4.6/4.9/5.6 需人决断或补小用例，5.1–5.4 未复跑）、`import-attempts-into-paper-progress`（37 项里约 29 项可勾，4.4/4.8 缺一条用例、5.1 是归档时动作、6.x 未复跑）、`json-content-repository-sync`（7.1/7.3 可勾，7.2 缺 `course.json` 样例）。

`ingest-integrity-and-observability` 是"登记册"型 change：44 项里只有 §7 的三条记录和 6.1 的部分重算算已交付，§1.4、§2、§3–§5、§8–§9 的实现/决定均未落地，不能按"进展"勾选，只能按"未开工"处理。

`mature-course-content-operations`、`retire-project-approval-gates`、`stabilize-agent-message-continuity`、`complete-practice-continuity-and-rich-titles`、`connect-evidence-guided-learning` 五个包均为规划工件，当前 worktree 没有对应交付：retire 的审批门仍在（pages/JS/API/测试都还在），practice 的富标题与 last-course 未实现，evidence 的教学工作流只有零件没有接线。建议这五个 change 保持 0 勾选，并在协调记录里写明"规划中/未开工"，而不是逐项评估完成度。
