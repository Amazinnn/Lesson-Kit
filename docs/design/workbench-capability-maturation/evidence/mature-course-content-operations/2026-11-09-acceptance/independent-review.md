# WP02 独立验收复核（IA-1，task 3.5）

- 复核人：独立验收角色（非实现者），只读复核，除本文件外未写任何工作区文件。
- 复核基线：`main` @ `6aef571c`（≥ 任务书要求的 `8ade79ea`）。
- 前置审查：`docs/audits/2026-11-08-wp02-review.md`（三条 P1 拒收记录）。
- 方法说明：除读代码与运行任务书指定命令外，对三条 P1 各做了**内存变异探针**（monkeypatch 还原旧缺陷形态，仅操作系统临时目录夹具），验证回归测试对旧缺陷确有捕获力。

## 一、逐项复核表

| # | 复核点 | 方法 | 结果 | 证据 |
|---|---|---|---|---|
| 1 | P1-1/P1-2/P1-3 回归真实性 | 读 `tests/workbench/test_content_bundle.py:815-880` 三条测试 + `PYTHONUTF8=1 python -m pytest tests/workbench/test_content_bundle.py -q`（**42 passed**）+ 三组变异探针 | **PASS** | 见第二节 |
| 2 | 门禁计划剔除（被拒单元无 plan） | 读 `_gate_content_bundle`（`workbench/ingest/__init__.py:855-1175`）、`_problem_identity_errors`（`:797-842`）；抽查 `_gate_micro_quiz`（`:390/433`）、`_gate_flash_cards`（`:2051/2082`）、`_gate_figure_patch`（`:1611/1653`）、`_gate_problem_patch`（`:1677-1716`） | **PASS** | 五个门禁均保证被拒条目不进 plans：bundle 三段（kp/problem/card）逐条 `refused_before`（`:896/931`、`:951/1099`、`:1113/1152`）；重复内容剔除在 `:1156-1161`（`problem_plans` 过滤 `refused_problems`）；micro-quiz/flash-card 同一 `refused_before` 模式；figure-patch 同上且 course/chapter 层错误整体拒绝（`:1603-1607`）；problem-patch 用逐条 `continue` 达到同效果（机制与 2.4 MD「同一 refused_before 模式」措辞略有出入，行为等价） |
| 3 | 单元一致性（行+图+快照+批次记录） | 读 `_apply_content_bundle`（`:1308-1490`）、`_apply_problem_patch`（`:1734-1811`）、`_apply_patch`（`:565-648`）、`_apply_figure_patch`（`:1841-1933`）、`_unit`（`:1225-1236`）、`_save_post_state`（`:1530-1567`） | **PASS** | bundle：章级 `_unit` 包住该章行+图+快照+批次记录（`:1337`，异常时 `:1455-1458` 回滚并删 chapter_files）；题目的 INSERT 与 `_publish_figure` 在**同一** `_unit` 内（`:1362-1366`）；`_save_post_state` 的 ids/figures 只取 `chapter_applied`（`:1396-1406`、`:1436-1449`），被拒单元不进快照。problem-patch 每行一个 `_unit`（`:1764`），快照 previous/post 只含 applied（`:1782-1796`）。micro/card 每条一个 `_unit`（`:588`），快照 `items` 只含 applied（`:630`）。figure-patch 复制文件+改行同 `_unit`（`:1869-1885`），失败删除本单元已复制文件（`:1887-1888`） |
| 4 | DATA-01 p95 / RELEASE-02 / 2.6 案例数 | 读 JSON + 独立复刻 bench | **PASS（带限制）** | 见第三节 |
| 5 | tasks.md 勾选与证据对应、夸大表述 | 逐条对照勾选文本与证据文件/实测 | **PASS（两处过时计数、一处与现状冲突）** | 见第四节 |
| 6 | 独立命令 | 见第五节命令记录 | **PASS** | content-bundle 42 passed；method_proposal/batch_undo/content_queries 合计 24 passed；`openspec validate mature-course-content-operations --strict` valid；`--specs --strict` 23/23；guard extract-problems PASS；`openspec list` 11/15 |

## 二、三条 P1 专项结论

### P1-1 重复内容零写入 — **确认修复**

- 测试 `test_duplicate_content_is_reported_and_never_written`（`tests/workbench/test_content_bundle.py:815-829`）：两道不同 key、相同题干；断言 `counts["problems"]==0` **且** 数据库 `problems` 行数不变，并报 `duplicate content`。正是审计要求的「断言拒收实体实际零写入」。
- 修复机制：`_problem_identity_errors` 返回 `(errors, refused)`（`__init__.py:842`），`:1159-1161` 把被拒 id 从 problem plans 剔除。
- **变异探针**：将 refused 集合清空（还原旧行为）后，`counts.problems=2`、库内重复题 2 行——旧缺陷复现，测试断言必然失败；未变异时 `counts.problems=0`。回归真实成立。

### P1-2 悬空闪卡零写入 — **确认修复（双保险）**

- 测试 `test_a_card_whose_knowledge_point_was_refused_is_not_written`（`:831-848`）：KP 仅有 `key=bad`、闪卡引用 bad；断言 `counts["flash_cards"]==1` 且 `SELECT COUNT(*) FROM flash_cards WHERE kp_id='bad'` 为 0，报 `unknown knowledge point bad`。
- 修复机制有两层：① 门禁层 `known_kps = 库内 ∪ kp_plans（仅接受单元）`（`:943-944`），被拒 KP 不进集合，卡被拒（`:1129-1131`、`:1152`）；② 应用层每张卡再查 `existing_kps ∪ applied_kps`，报 `depends on a rejected knowledge point`（`:1374-1381`）。
- **变异探针**：强行让门禁返回被拒卡的 plan（还原旧门禁行为），应用层依赖检查触发、`kp_id='bad'` 落库 0 行——第二层保险独立有效。

### P1-3 附件失败只回滚本单元 — **确认修复**

- 测试 `test_a_figure_publication_failure_rolls_back_only_its_unit`（`:850-880`）：注入 `_publish_figure` OSError；断言邻居 plain 题照常落库（`counts.problems==1`、批次计数 1、库内 2 行）、无任何 figure_paths、`.lessonkit/figures` 目录不存在——正是审计要求「其他成功单元不被撤掉」。
- 修复机制：插图发布与题目 INSERT 同一 `_unit`（`:1362-1366`），失败回滚该题行并删除本单元已复制文件（`:1367-1371`）；快照只含已应用题目的图（`:1404-1406`），不会再触发 `could not snapshot applied figure` 连带整包回滚。
- **变异探针**：把 `_unit` 替换为空操作（还原「只给 INSERT 加 savepoint、发布在其外」的旧形态）后，图题行残留库内（3 行 vs 回执 counts=1，收执与库不一致）；未变异时库内 2 行、无图目录。测试断言对旧缺陷有捕获力。

## 三、证据数字抽查

| 项 | 声明 | 复核 | 结果 |
|---|---|---|---|
| DATA-01 | 100 次 p95 2.2ms ≤1s（`data-01-query-timing.json`） | JSON 实值 p95=0.0022s、verdict PASS。**独立复刻**（自建 501 kps/2001 problems 等量级夹具、同 random seed 结构）：p95=1.3ms，同数量级，门槛余量巨大 | PASS |
| — | `sample_hits: 0` 疑点 | 已解释：500 个插入点的 type 由 chapter 决定（index%8 与 index%4 相关），32 个 (type,chapter) 组合仅 8 个非空，最后一次随机抽取落在空组合；计时仍是全表扫描，p95 有效。**非异常** | 说明 |
| — | bench 可复现性 | `data-01-bench.py:7` 依赖未跟踪的 `tmp/accept/p3_f1.py`（全仓无 `def build_course`），**按现状不可原样复跑**；p95 数值以独立复刻佐证 | 限制 |
| RELEASE-02 | 三组全 true（`release-02-report.json`） | copy_migration 3 项、backup_restore 4 项、install_identity 均为 true；`release-02-run.py:65-104` 逐项真实计算（列存在、值比对、文件存在、子进程身份输出），非硬编码；脚本自包含可复跑 | PASS |
| 2.6 | 26 条标注案例 | `annotation-report.json` 26 cases（mapping 8 + mapping-gate 4 + semantic 3 + integrity-audit 5 + classification 6），与 2-6-annotation.md 表格逐一对应；summary 的 `doubtful_excluded_from_verified=true` 与 kp-060~062/kp-063~064 划分一致；`annotation-run.py` 只依赖 workbench 模块，自包含 | PASS |

## 四、任务勾选核对与表述问题

勾选 11/15（2.1–2.6、3.1–3.4、3.6；1.1–1.3 与 3.5 未勾），与 `openspec list` 一致。勾选项与证据文件一一对应（2.1→query、2.2→methods、2.3→chapter、2.4→units、2.5→batch-undo、2.6→annotation、3.2→matrix、3.1/3.3/3.4/3.6→contract-and-release）。2.5 的 `flow03_direct_correction.py` 已存于证据目录，FLOW-03 输出（题号不变、作答原文不动、撤销入口不存在）有实跑记录。

**夸大/不实表述清单（2 条）**：

1. **3.6「工作区无遗留改动（仅 owner 侧既有未跟踪文件）」与当前事实不符**：`docs/action-graph/L1-services.md` 与 `docs/action-graph/L4-workflows.md` 两个已跟踪文件存在未提交改动，且内容正是本包 2.4 的契约同步（「单事务 apply→逐单元事务」「整批零写入→该单元零写入」）。3.1 声称 ACTION-GRAPH「已同步」，但该同步目前只存在于工作区，未按 3.6 自身的路径限定提交纪律落库。
2. **2.4 MD「五个门禁……同一模式（refused_before）」以偏概全**：`_gate_problem_patch`（`:1677-1716`）实际用逐条 `continue` 而非 `refused_before` 记账。行为等价（被拒单元同样不产出 plan），但机制描述不准确。

**过时/不准计数（2 处，非夸大方向，均为少报）**：

3. tasks.md 2.1 与 2-1-query.md 写「7 用例」，实测 `test_content_queries.py` 现为 **12 passed**（3.2 矩阵写 12 正确；5 条为 3.x 阶段补充的四位置命中断言，2.1 文本未回更）。
4. tasks.md 2.6 写「映射 8+2 门禁实测」，实际门禁执行案例 **4 条**（M1v/M3v/M6v/M7v），总数 26 不受影响。

**其他记录（nit，不计数）**：`_gate_problem_patch` docstring 仍写 "so the whole batch can be rolled back"（`__init__.py:1664`），与 2.5 退役整批撤销后的「快照=应用于记录」语义不符，属 2.5 注释同步的遗漏。2.4 MD「全仓 1572 passed」与 3.3「1582 passed」为不同时点的两轮全仓（中间有新增用例），各自如实标注，不算矛盾。

## 五、独立命令记录（任务书第 6 项）

| 命令 | 结果 |
|---|---|
| `PYTHONUTF8=1 python -m pytest tests/workbench/test_content_bundle.py -q` | 42 passed |
| `PYTHONUTF8=1 python -m pytest tests/workbench/test_method_proposal.py tests/workbench/test_batch_undo_retired.py tests/workbench/test_content_queries.py -q` | 24 passed（分文件：10 / 2 / 12） |
| `PYTHONUTF8=1 openspec validate mature-course-content-operations --strict` | Change 'mature-course-content-operations' is valid |
| `PYTHONUTF8=1 openspec validate --specs --strict` | Totals: 23 passed, 0 failed |
| `PYTHONUTF8=1 python lessonkit.py guard extract-problems --course dmath --chapter ch06` | Result: PASS |
| `PYTHONUTF8=1 openspec list` | mature-course-content-operations 11/15 tasks |

未跑全仓 pytest（按任务书要求抽查；实现者 1582 passed 的全仓记录未独立重跑，本报告不为其背书，仅记录）。全部测试走 `tempfile.TemporaryDirectory` 夹具，未触碰 22 个真实工作区与真实课程数据。

## 六、最终验收意见

**有条件通过。**

三条 P1 的修复真实成立：修复机制在代码中可定位，回归测试断言到库级零写入/邻居存活，变异探针证明三条测试对旧缺陷形态均有捕获力。门禁剔除、单元一致性、RELEASE-02、26 条标注案例、openspec 双 strict、guard 均复核通过。

通过条件（实现者处理后即可转「通过」）：

1. **必须**：将 `docs/action-graph/L1-services.md`、`docs/action-graph/L4-workflows.md` 的 WP02 契约同步按路径限定提交（或由所有者裁定该改动归属后更正 3.1/3.6 的相应表述）；当前状态与 3.6「工作区无遗留改动」直接冲突。
2. **应当**：更正 tasks.md 2.1「7 用例」→12、2.6「8+2 门禁实测」→8+4 两处过时计数；顺带修正 `_gate_problem_patch` docstring 的整批回滚残留表述。
3. **建议（不阻塞）**：为 `data-01-bench.py` 补提交其夹具依赖（或在 MD 注明该依赖未入库），使 DATA-01 bench 可原样复跑。

3.5 本身按流程保持未勾，待上述条件闭环后由所有者/实现者按本报告结论处理。
