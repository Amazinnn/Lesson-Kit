# 规划交接状态

> **下一阶段决策（2026-11-08，所有者确认）**：大任务 = WP03 `retire-project-approval-gates`（0/13）；前置 = 推送授权确认 + `agent-chat-simplify` 6.4 浏览器验收（同套浏览器环境）。交接文档：`%TEMP%\handoff-wp03-approval-retirement.md`。

## 2026-11-08：前置收口（推送 + 6.4 归档）；WP03 开工

- **推送已完成**（所有者本轮明示授权）：`3dca0cc0..b6881510` → origin/main，main 与远端同步。
- **agent-chat-simplify 6.4 全过并归档**：隔离临时工作区 `wb64`（fixture 库 + 真实 CLI 存卷 ps-001）+ daemon 3123（`source_root` 核对=主检出）+ 协议忠实假 provider（`tests/workbench/fake_pi_rpc.py` 派生，真实 bridge/HTTP/落库链路）——8 项清单全过（Enter/Ctrl+Enter 真实 POST、Shift+Enter 原生键盘换行、满宽、无影响行、审批单卡、空队列直发、三类长卡折叠/展开、status 可见）；**发现并修复真缺陷**：恢复卡 `wbApplyCollapse` 在 `appendChild` 前调用致 scrollHeight=0 永不折叠（editCard 同类补挂），312 pytest + node 全绿（`e5d5c757`）。`openspec archive --yes` → `2026-11-08-agent-chat-simplify`，workbench-ui +1 ADDED/~3 MODIFIED 并入 live，strict 25/25（`b508995c`）。证据 `evidence/agent-chat-simplify/2026-11-08-64-browser/summary.md`。
- **editable 安装纠正**：`.pth` 实际指向 `D:\.codex\worktrees\course-sync\lesson-kit`（此前"editable=主检出"是 cwd 污染误判）；已 `pip install -e . --no-deps` 重装回主检出并经中性 cwd 探针 + `/api/runtime` 双核。daemon 3123 + wb64 环境保留，WP03 2.3 复用。

## 2026-11-09：stable-runtime-live-reload 归档；agent-chat-simplify 6.4 部分验收

- **stable-runtime-live-reload 3.2 勾选并归档**（`ca9363b8`）：全仓多轮绿（最新 1582）+ 真实隔离验收（真子进程 harness 4/4 + 3097/3098 端口 daemon 探针）+ 独立复核；`runtime-live-reload` 能力进入 live specs（25/25 strict）。
- **agent-chat-simplify 6.4 部分验收（未勾）**：隔离临时工作区 + daemon 3123 实测——`#ai-input`/`#ai-status` 存在、status 可见、Shift+Enter 不发送、空队列无出站行、审批卡槽存在，4 项过；**Enter/Ctrl+Enter 发送与长卡折叠/展开未验到**：Enter 的守卫是 `!aiConversation`（新建按钮未建立会话），需要 provider 支撑的真实会话才能走到发送与长卡渲染。剩余动作：配置临时 provider 起真实对话再跑 8 项清单。**6.4 保持未勾，不据部分结果勾选。**

## 2026-11-09 归档：WP02 已归档（live specs 24/24）

- `mature-course-content-operations` 归档为 `archive/2026-08-…`（目录名 2026-11-08 前缀为归档日期规则）：`knowledge-content-operations` 新能力进入 live specs；五个 MODIFIED capability（governance/bridge/flash-card/figures/micro-quiz）的单元化、分类补齐与 undo 退役规则并入。live specs strict **24/24**。
- 活跃 change 降至 19。**WP02 无剩余任务**；后续（部署/推送/真实环境验收）按所有者安排。

## 2026-11-09 终：WP02 15/15 ✓ Complete

- §1 基线任务（1.1 工件/身份/重叠、1.2 delta 逐条核对、1.3 失败检查先行）补记并勾选——证据 `evidence/mature-course-content-operations/2026-11-09-baseline/1-1-1-2-1-3-baseline.md`。其中核出 5 个 MODIFIED 块对 live 场景零丢失；扫描器对 knowledge-figures 的 REMOVED 报"场景缺失"属误报（REMOVED 不携带场景，Reason/Migration 齐全）。
- 独立验收条件已闭环（`ee2396c8`），3.5 按报告勾选。**WP02 15/15 ✓ Complete**，strict 有效。
- 未做（不属于本 change 任务）：真实浏览器/远端/调度/模型验收不涉及本包入口；发布与部署类动作仍需所有者单独安排。
- 后续：archive 流程未走（与其它 change 一样等所有者统一安排）；`data method kp` 与章节列等新行为已进 live specs 的路径 = 归档时并入。

## 2026-11-09 收官：WP02 独立验收有条件通过，条件已闭环（12/15）

- **独立验收**（报告 `evidence/mature-course-content-operations/2026-11-09-acceptance/independent-review.md`）：三条 P1 经代码定位 + 42 passed + 变异探针确认回归真实；openspec 双 strict / guard / 独立复刻 DATA-01 通过。结论"有条件通过"，条件 = 提交 L1/L4 契约同步、更正 2.1/2.6 两处过时计数、修正 problem-patch docstring 的回滚残留——**本提交（`ee2396c8`）全部闭环**；2.4 MD 的机制描述按门禁分别说明。
- WP02 **12/15**：§2 全部（2.1–2.6）+ 3.1–3.4、3.5、3.6。剩 3 项为发布边界任务：3.7? 无—— tasks 剩余为 §3 的 3.2 未尽浏览器项？核对：剩余三条 = 2.x 无、3.x 无未勾……以 tasks.md 为准（11/15→12/15 后剩 3 条：3.2 的浏览器补充?、归档任务不在列）。**剩余清单以 tasks.md 未勾项为准**。
- 全仓基线：1582 passed / 432s（2.2 后记录）；compileall、Node 297、live specs 23/23、guard PASS。
- main 领先 origin/main，**未推送**（所有者决定）。

## 2026-11-09 续：WP02 2.2 完成（5/15），仅剩 2.6

- **2.6 标注案例**（证据 `evidence/mature-course-content-operations/2026-11-09-annotation/`：`2-6-annotation.md` 26 行案例表 + `annotation-report.json` + `annotation-run.py`）：映射 8 条 + 2 条真实门禁执行 + 语义核对 2 条 + 完整性 4 条（untitled/unmarked-objective/duplicates/figures）+ 分类补齐 6 条（C1–C6）。结构检查（audit/门禁/字段）与语义核对（同义折叠、判重、人工证据）分开报告；分类补齐只改有依据项（3 条 method-modeling），两条疑点保持占位且按 types 检索不在已核对范围。
- 全部案例在脱敏临时夹具执行；脚本注册工作区用 `LESSONKIT_WB_HOME` 隔离（曾误注册进真实注册表一次，已精确移除该条，22 个真实工作区完好）。
- §2 实现任务（2.1–2.6）全部完成；WP02 6/15，剩 §3 契约/验收/发布任务（3.1 文档同步、3.2 DATA-01–05/CONTENT-01/FLOW-03 验收、3.3 RELEASE-01、3.4 RELEASE-02、3.5 独立验收、3.6 提交纪律）。

## 2026-11-09 续：WP02 2.2 完成（5/15），仅剩 2.6

- **2.2 方法提案**（`7c90d201`，全仓 1582 passed / 432s）：`data method kp --input` 先按折叠标题查同义已有点——命中 1 个即复用身份（只追加适用原题关联，不改正文）、命中多个拒收并点名（要人工裁决）、未命中走治理新建（method-modeling / formula-calculation / algorithm-process 三类，分类不确定拒收零写入）；`problem_ids` 原题自动追加关联且既有关联保留，未知题号前置校验整体拒收。10 条用例（8 标注案例 + 同义多命中 + CLI 端到端）全过；L2/GLOSSARY（方法提案）/PRODUCT-MANUAL/ACTION-GRAPH 2026-11-09 留痕/agent_contracts 同批同步。
- **仅剩 2.6**：20 个映射/完整性标注案例（区分结构检查与语义核对；限定章节分类补齐只改有依据项，疑点不进已核对练习）。这是纯证据工作——建议做法：以脱敏 dmath-ch06 风格夹具构造 20 组「提案 ↔ 既有知识点」原文对，逐条跑 `find_equivalent_kp`（语义）+ `content_audit`（结构），证据表落 `evidence/mature-course-content-operations/`；"限定章节分类补齐"如需实现入口（批量 `data update kp` 的 knowledge_type 补齐），走 `data update kp` 既有路径 + 单元语义即可，不新增第二套通道。

## 2026-11-09：WP02 2.4 完成（4/15）

- 四类通道（content-bundle / problem-patch / micro-quiz+flash-card patch / figure-patch）全部单元化：门禁只产出接受单元的计划、依赖只认「库内 ∪ 已接受知识点」（题目与闪卡都查）、每个单元各自 savepoint、插图与行同生共死、批次记录只含实际落库单元。
- 审计三条 P1 全部有回归用例钉住（重复内容零写入、悬空闪卡零写入、插图失败只回滚本单元）。首版漏了 micro 门禁的 per-item 闸（全仓跑出 2 条旧原子用例失败后补上，`11629355`）。
- 旧原子断言已改写为单元语义；全仓 **1572 passed / 441s**、compileall OK、Node 297 断言、live specs 23/23、WP02 strict、guard PASS。
- 回执新增 `errors` / `partial` 字段；文档（GLOSSARY/PRODUCT-MANUAL/L1/L4/agent_contracts/FILE_CONTRACT）已同步为"逐单元提交"语义。
- **剩余**：2.2 提炼复用（同义已有点优先、新模型带条件/公式/步骤、自动追加原题关联；8 个标注案例）、2.6 二十个映射/完整性标注案例（区分结构检查与语义核对，疑点不入已核对练习）。

## 2026-11-09：WP02 2.4 内容包一半完成（`84b4f9cf`），其余三类待做

按 `docs/audits/2026-11-08-wp02-review.md` 的三条 P1 重做，**未采纳 stash**（原样保留）。

**已完成（content-bundle）**：

- 计划剔除：门禁里任一单元出现校验错误即不再产出 plan（知识点/题目/闪卡三段都加了 per-item 错误闸）；`_problem_identity_errors` 同时返回被拒 id 集合并剔除对应问题计划；
- 完整依赖：题目的 `kp_ids`、闪卡的 `kp_id` 只认「库内 ∪ 已接受的包内知识点」；被拒知识点的依赖方零写入；
- 单元一致：按章一个外层事务（行 + 附件 + 快照 + 批次记录同生共死），章内每个单元各自 savepoint；题目的插图在**同一 savepoint 内**发布，失败只回滚该题并删除已复制文件；
- 用例：5 条旧原子断言改写为单元语义；新增 5 条钉住审计三条 P1（含注入 `_publish_figure` 失败只回滚本单元、批次计数只含已应用单元）；
- 受影响套件 119 passed（content-bundle 42、ingest、figures、problem-patch、cards、conversation-api）。

**2.4 未完成部分（不得勾选）**：`_apply_problem_patch`、`_apply_patch`（micro-quiz / flash-card patch）、`apply_figure_patch` 仍是整单一事务；三者的门禁同样需要「拒收单元不产出计划 + 依赖完整」，并各自补单元级用例。2.2、2.6 未开始。

## 2026-11-08 WP02 合并前审查

审查 `5fc45cd0` 的已提交成果与 stash 对象 `36ce68193c4db5bd37119ea616cd8bd8205b921b`。stash 未应用、未整合：已复现重复题报错仍落库、未知知识点闪卡仍落库、附件失败退回整包回滚，不能归因于旧测试契约。

已提交代码另发现知识点删除先提交、删除标记后保存的不一致窗口。修复为交换锁先于删除事务，内容与 SQLite tombstone 同事务；检查点失败及锁冲突均保留原内容。只读复核已重复双连接交错与失败注入，无剩余 P1/P2；完整证据见 [审查报告](../../audits/2026-11-08-wp02-review.md)。主线既有更正重放、Tutor 和编码修复保留。2.4 仍未完成；2.2、2.6 与剩余整体验收不勾选。

本轮全仓终态与整合结果见审查报告验证段，不引用旧轮次测试冒充。

## 2026-11-08 末：WP02 2.4 的 WIP 在 stash（重做前先读这段）

我按设计做了一版 2.4 并跑过：门禁改为"即使有拒收项也返回有效 plans"、`_apply_content_bundle` 逐单元 `SAVEPOINT`、依赖被拒的知识点时阻断引用它的题目、批次只覆盖实际落库项、新增 3 条用例。**结果：内容包 37 条里 17 条失败**——它们全是编码旧"整批原子"契约的用例（`..._blocks_the_whole_bundle`、`..._refuse_the_whole_bundle`、`..._without_writes` 等），需要逐条改写成"无效单元零写入 + 有效邻居照常落库"。

我没有把半截重构留在工作区，已用
`git stash push -m "WIP WP02 2.4 independent content units" -- workbench/ingest/__init__.py tests/workbench/test_content_bundle.py`
存为 **stash@{0}**（另有更早的 `stash@{1}` 属别的分支，不要动）。恢复：`git stash apply stash@{0}`；参考实现另存在 `tmp/accept/apply_bundle_new.py`（gitignored）。当前工作区全绿（内容包 37、ingest 42）。

**重做 2.4 的顺序建议**：先逐条把 17 个旧用例改写为独立单元语义（它们的 bundle 大多只有一个无效项，改写只需把 `assertRaises` 换成"该单元零写入 + errors 含原因"），再 apply stash 并跑全仓；`test_a_problem_whose_knowledge_point_fails_at_write_is_blocked` 要用 monkeypatch 让该 KP 写入失败（测试夹具的 `knowledge_points` 没有 CHECK 约束，靠非法 `knowledge_type` 触发不了失败）。

## 2026-11-08 更晚：WP02 2.4 设计与依赖漏洞（未动手，先记录）

停止在 2.4 之前而不是硬做，因为拆"独立有效单元"必须重构 `_gate_content_bundle` 的判定与依赖关系，半途实现会造成**悬空引用**。勘察结论：

1. **现状是整批原子**：`_apply_content_bundle`（`workbench/ingest/__init__.py:1185`）先 `_gate_content_bundle`，`if not verified["ok"]: raise`，整批零写入；每章一个批次、一份备份、一个事务。
2. **门禁已经逐条累积错误**（`errors.append(f"{label}: …")`），并返回成功项的 plans（`knowledge_points`/`problems`/`flash_cards`/`chapters`/`typesetting`）。所以"应用有效项"本身只需要把 `raise` 改成"应用 plans + 报告 errors"。
3. 🔴 **必须先解决的依赖漏洞**：门禁的 `known_kps = 库内 KP ∪ 本包全部 kp_ids`（`:913-914`），而 `:943` 只检查 `kp_id in known_kps`。也就是说，**一个被拒收的知识点，它的 id 仍会让引用它的题目通过校验**。整批原子时无害（反正都不写），一旦改成独立单元，就会写出指向不存在知识点的题目。做 2.4 时必须在应用前算出"被拒收的 kp id 集合"，把 `kp_ids` 命中该集合的题目一并拒绝并记为依赖阻断，同时补一条"依赖被拒 → 题目保留不写"的用例。
4. 改动面：`_apply_content_bundle` 的 errors/ok 语义（改为 `errors` + `partial`，只在**完全没有有效项**时才抛）、批次分配只对已应用的分章、`apply_batch` 透传 `errors`、CLI/桥回执展示逐条失败；`problem-patch` / card / quiz / figure 的应用是否同样拆单元需逐个确认（`_apply_problem_patch`、`_apply_patch`）。
5. 会被改写的既有测试：`tests/workbench/test_content_bundle.py` 里"任一条不合法即整批零写入"的断言；新用例至少覆盖：2 有效 + 1 无效 → 2 条落库 + 1 条报错 + 备份仍是一份；依赖被拒的题目不落库；重试同一清单幂等。

**仍未做**：2.2 提炼复用（同义已有点优先 + 新模型带条件/公式/步骤 + 自动追加原题关联，8 个标注案例）、2.6（20 个映射/完整性标注案例）。WP02 当前 3/15。

## 2026-11-08 收尾：WP02 2.5 完成（3/15），批次 undo 已退役

- 一次性撤除显式成功批次撤销：CLI `ingest rollback`、`POST /ingest/rollback`（surface/app/api）、结果卡「整批回滚」按钮与确认面、`rollback_batch` 及 7 个专用助手（净删 362 行）、`agent_contracts` 两处提示。
- 保留 `ingest_batches.rolled_back_at` 与历史卡片「已回滚」标记；批次快照改称"应用于记录"。
- 文档同批：GLOSSARY（5 处）、FILE_CONTRACT、PRODUCT-MANUAL（第 8 章 6 处）、ACTION-GRAPH 2026-11-08 留痕 + L0–L4。
- 测试：删 17 条纯回滚用例、改写 2 条非回滚意图用例、`real_pool_conformance` 去掉回滚校验；新增 `test_batch_undo_retired.py`（CLI 已无该子命令 / 历史 `rolled_back_at` 可读）；Node UI 断言改为"无撤销入口"且历史标记仍在（128 pass）。
- **FLOW-03 实跑**：录一条作答 → 错改 → 同身份改正；题号不变、作答原文不动、撤销入口已不存在。证据 `evidence/mature-course-content-operations/2026-11-08-batch-undo/`。
- 未做：2.2 提炼复用、2.4 拆独立有效单元、2.6 20 个标注案例。

## 2026-11-08 末：WP02 2.5 撤除面已勘察（未动手）

全仓 **1577 passed（433s）**。`data move kp` / GAP-01 墓碑 / 章节归属均已提交并通过全仓回归。

2.5「退役成功批次 undo」的完整撤除面（**一次做完，不要拆半**：CLI 删了而界面还在 = 更糟）：

| 层 | 位置 |
|---|---|
| CLI | `workbench/cli/main.py:827`（dispatch）、`:1307`（`ingest rollback` parser） |
| HTTP | `workbench/surface.py:123`、`workbench/server/app.py:115`、`workbench/server/api.py:826`（`ingest_rollback`） |
| 数据层 | `workbench/ingest/__init__.py::rollback_batch`（2096+）、`_rollback_blockers`、`_rollback_conflicts`、快照 `manifest_path` 的保留逻辑 |
| 前端 | `workbench/server/static/workbench.js:5318`（`/ingest/rollback` 调用）、`:5217/:5229`（`rolled_back_at` → 「已回滚」标记）、按钮 `aiMarkRolledBack` 相关渲染 |
| Agent 提示 | `workbench/bridge/agent_contracts.py:142`（把 rollback 列为需显式请求的动作）、`:185`（"rollbackable by ingest batch"） |
| 手册 | `docs/PRODUCT-MANUAL.md:488/517/593/597/607`（整批回滚按钮、可按章回滚、整批可回滚等表述）——第 8 章是主战场 |
| 动作图/术语/工件 | `docs/action-graph/L2-interfaces.md`（路由）、`L3-actions.md`、`L4-workflows.md`、`L0-data.md`、`L1-services.md`；`docs/GLOSSARY.md`、`FILE_CONTRACT.md`（快照/回滚节） |
| 测试 | `tests/workbench/test_ingest.py`、`test_content_bundle.py`、`test_problem_patch.py`、`test_conversation_api.py`、`test_ingest_figures.py`、`test_cards.py` 里以 rollback 为断言的用例 |

保留：`ingest_batches.rolled_back_at` 列与 `list_batches` 的读取（`ingest/__init__.py:2078-2092`），历史批次仍可读；只退役**入口**与**能再次撤销**的能力。

FLOW-03 要求"用直接修正完成相同修错任务"：撤除后应演示 `data update problem`（单题）与 `problem-patch` 清单（成批）完成一次真实修错，并把该路径写进手册替代原回滚段落。

## 2026-11-08 深夜：GAP-01 关闭，WP02 2.1/2.3 完成（2/15）

- **GAP-01 已修**（`82aa5e7b`）：删除知识点时在交换状态里记录删除，导出据此产出显式墓碑；接收端照常删除，重复接收为空操作。缺文件仍**不**授权删除。证据 `evidence/expand-file-mediated-course-sync/2026-11-08-accept/gap-01-resolved.md`。闪卡无独立删除入口、学习文件仍无写端删除，均记为边界。
- **WP02 2.3 完成**（同提交 + 证据 `evidence/mature-course-content-operations/2026-11-08-chapter/`）：`knowledge_points.chapter` 增量迁移与整段回填；读取口径「列优先、NULL 回退 ID」落在 `Pool.kps`/`Pool.chapters`/列表分组/typed query/create/ingest 两处；新增 `data move kp <id> --chapter chNN`，只改列、ID 不变，关系/经验/透镜/文件往返都有用例。冻结层（`pool/scripts`、`pipeline/scripts`）按所有者决定不动，作为已知边界写入证据。
- **E3 盘点纠错**：原先的回填取任意 `chNN` token，会把 `dmath-source-ch03-kp-001` 写成 `ch03`；已改为整段解析（`07f5efa0`）。
- **环境提醒**：editable 安装当前指向 worktree（开发期需要），收工前要 `cd 主检出 && pip install -e . --no-deps` 还原，否则 `lesson-kit` 继续服务 worktree。
- **下一步**：WP02 2.5（退役成功批次 undo）→ 2.4（拆独立有效单元）→ 2.2（提炼复用）→ 2.6（20 个标注案例）。

## 2026-11-08 夜：所有者四项拍板（下一段按此执行）

1. **WP02 2.3 消费者改写只做 workbench 层**：采用「`chapter` 列优先、NULL 回退 ID」；`pool/scripts/` 与 `pipeline/scripts/` 的旧视图仍按 ID 推章，作为**已知边界**写进文档，不为它改冻结层的行为契约。E3 盘点共 65 处消费者（50 处"必须改"），其中冻结层占一半——本次明确不动。
2. **GAP-01 取"删除时写墓碑"**：删闪卡/知识点/学习文件时写显式删除记录，导出据此生成墓碑；继续保持"文件丢失"与"本人删除"可区分（现行 spec 禁止混淆）。不要改成"导出时报待确认"。
3. **WP01 带未验证项归档**：已归档为 `2026-11-08-expand-file-mediated-course-sync`，`file-course-sync` 能力进入 live specs；SYNC-06 真实调度触发、真实 GitHub 发布、真实凭据缺失在验收矩阵中如实标注未运行。
4. **推送暂缓**：`main` 领先 `origin/main`，本地仍是唯一副本；所有者明确"暂不推送"。

## 2026-11-08 晚：合并入 main、WP01 收口、8 个 change 归档、WP02 开工

- **合并**：`codex/course-sync` 已两次 fast-forward 并入 `main`（现 `27642b55` + 提交后的 WP01 收口），主检出已 `pip install -e .` 重装，`lesson-kit` 与默认守护进程的服务来源都回到主检出。`main` 领先 `origin/main` **104**，**未推送**（推送需单独授权）。
- **WP01 23/23 ✓**：本轮新增证据目录 `evidence/expand-file-mediated-course-sync/2026-11-08-accept/`（12 份）。SYNC-04 补真进程硬杀 ×4；顺带修复孤儿 `<name>.<随机>.tmp` 被当资产传播的缺陷。**仍未验证、不可计为通过**：SYNC-06 真实调度触发、真实 GitHub 发布、真实凭据缺失；另有 receive 自身 partial 与多课程 2>3>4 优先级未验。**WP01 暂不归档**，等 SYNC-06 处置决定。
- **已归档 8 个 change**：align-runtime-source-with-installed-code、remove-micro-quiz-error-reason、workbench-v1-baseline-convergence、source-preserving-live-markdown、part-grading-legacy-pool-fallback、improve-agent-context-and-skills、cluster-flat-knowledge-graph-levels、complete-live-display-preferences（最后一个已被 live 吸收，比对后用 `--skip-specs`）。live specs **22/22**。两个 delta 缺陷（`graph-free-force-field`、`import-attempts-into-paper-progress`）已补回缺失的现行场景，全仓 MODIFIED delta 扫描 0 缺失。
- **WP02 已开工**：2.1 知识点组合查询 + CLI（`data … search kp --knowledge-type/--chapter`、`data … related problem`），DATA-01 p95 2.2ms；2.3 前半=`knowledge_points.chapter` 增量迁移 + 回填（`ensure_knowledge_chapter_schema`）。**未做**：2.2 提炼复用、2.3 消费者改写与跨章移动、2.4 独立有效单元、2.5 退役批次 undo、2.6 20 个标注案例。
- **待所有者拍板**：GAP-01 删除传播——只有 `problems` 有本地墓碑，删闪卡/知识点/学习文件后下一次导出永久失败且无 CLI 入口记录显式删除（A 写墓碑 / B 导出时报待确认）。详见 `evidence/expand-file-mediated-course-sync/2026-11-08-accept/2-1-coverage-table.md` §4（共 14 条 GAP，另 GAP-12 本机新增列导出侧不报错与 `FILE_CONTRACT.md:827` 冲突）。

## 2026-11-08 P4、FS-08 与交接

- **FS-08 恢复已实现**：`content.restore` + `data <ws> restore problem <id>`。恢复后内容与历史重新可读，**不会**自动回到任何试卷或执行；移除事实留在 `retired_paper_items`；重复恢复报 `already_current` 零写入。测试 `test_restoring_an_archived_question_keeps_it_out_of_its_papers`；FILE_CONTRACT / PRODUCT-MANUAL / L2 已同步。
- **P4 安装身份**：editable 已切到本 worktree（`workbench.__file__` 指 worktree、`lesson-kit --help` 含 `course-sync`）。**2026-11-08 起**默认守护进程也服务本 worktree（`align-runtime-source-with-installed-code`：默认来源 = 安装代码所在 checkout），`--project-root` 仍可指其他 checkout。验收后守护进程已停止，安装还原命令见交接文档 §1.3。
- **SYNC-06 调度触发仍未验证**：`Register-ScheduledTask` + `Start-ScheduledTask` 后 `LastRunTime` 更新、`LastTaskResult=0`，但动作无回执/无日志；安装/停用/启用/删除与任务命令本身均已验证。
- tasks 补勾 **3.4 / 3.5**（11/19）。
- 交接文档：[HANDOFF-2026-11-08.md](HANDOFF-2026-11-08.md)（含未验证项、待决策、复现命令与建议顺序）。

## 2026-11-08 P3 完整同步验收

按 `NEXT-EXECUTION-PLAN-2026-11-07.md` 的 P3 跑完（P0–P2 已在前一段交付）。夹具全在临时目录，未触碰真实课程，未切换安装。

- **通过**：SYNC-01（F1 完整小课程 99 项资产、8 张表计数一致，学习文件/目标/原件/引用图全部落地）、SYNC-02（F2 预热后各 20 次：导出 p95 18.23s、无变化检查 p95 3.19s、接收 p95 9.96s，三项门槛全达标）、SYNC-03（双侧同题冲突→批量选侧、独立作答合并、删改冲突保留）、SYNC-05（专用远端：发布/无变化不产提交/FF 吸收/推送被拒 exit 4 保留本地提交/他源包 exit 2 不改两侧）、SYNC-07+LP-01（全新 B 可读目标、范围、原始作答、教学位置、学习文件）、SYNC-08（2026-08-26 真实旧池 347 项 0 失败 + 同名异源需显式关联 + 未知格式/未知表/缺图如实拒绝）、RELEASE-01（1,554 passed、compileall、live specs strict、guard，加隔离服务真实浏览器：收到的偏好生效、新卷用收到的揭晓时机、进行中的卷保持冻结并可继续）。
- **部分**：SYNC-06 计划任务安装/停用/启用/删除全部验证、任务命令手动执行成功并写回执，但 `/Run` 与 `Start-ScheduledTask` 触发后未见回执——调度触发未验证；冲突通知已验证「首次通知、二次去重」。
- **未支持**：FS-08 恢复（依赖 adaptive change 3.2）。**未执行**：真实 GitHub 发布（仅只读连通性探测）、SYNC-04 进程级中断（仍由自动化故障注入覆盖）、安装身份切换（P4）。

P3 暴露并修掉两个真实缺陷：接收端按位置合并会留下发送端已删除的执行项（改为执行头声明题目集合），以及 `content.delete` 删除题目不写保留历史（现与改名单同路径）。

证据见 `evidence/expand-file-mediated-course-sync/2026-11-08-p3/`。。tasks 已按实际结果勾选 2.8 / 3.3 / 3.6，并在 2.9 / 3.2 标注缺口。

## 2026-11-07 改卷生命周期首段（adaptive-paper-content-lifecycle）

按所有者要求实现该 change 的主体缺陷：**在已有作答的卷里改名单/改题序不再整卷清零**。提交 `4affbcb6`。

- `paper_progress.reconcile_membership`：按题目身份协调未完成执行——存活题的状态、attempt 关联、草稿与顺序跟随新位置；新增/替代题从 pending 开始；被移除题写入新的保留历史表 `retired_paper_items`（位置、状态、attempt、内容版本、最后草稿、原因、时间）；游标先跟原题，否则后一道再前一道存活题；结构版本递增一次；active 与 parked 用同一变换；只有整卷一道不升时才清空该卷执行。
- 预览改为报告 `preserved_items/added_items/removed_items`，`resets_progress` 仅在无存活项时为真；确认仍是并发 expected-state 守卫，不是额外审批。
- 测试：`tests/workbench/test_paper_lifecycle.py` 6 项新用例；原先钉住"改卷重置"的两条进度用例与两条审批用例已按新契约更新。全仓 1,547 passed。
- 已按实际证据勾选 tasks 4.1 / 4.2 / 7.1 / 7.2（4/29）。**未做**：题目归档恢复（3.2）、语义修订新身份与一次性继承（3.1/3.3）、Paper 归档恢复（4.3）、派生结果惰性失效（5.x）、CLI/API/UI（6.x）、审批退役（6.2/6.3，属 WP03）。`paper_progress.reset` 现仅由 `delete_saved` 使用，删除仍为硬删而非归档。

## 2026-11-07 第三棒：把已审接收修正合入实际源码

独立审查（C05）确认批次事务设计正确，同时复现了四项缺陷；本轮把审查期间冻结的修复草稿合入实际 `workbench/data/course_sync.py`，并补齐审查发现的剩余三项：分组执行头按题目依赖排序、stale 检查失败只报一条 `stale_inspection` 并停止、不完整执行信封按 `invalid_asset` 隔离。同时把 G06 的 `list_remote_files` 接进 CLI，使 Tutor 在 Git 里新增、未改 manifest 的学习文件也能被接收；codec 审查（B06）指出的三条未被测试钉死的规则已补测试。提交 `c2a12260`。

实测：全仓 `PYTHONUTF8=1 pytest tests -q` **1,535 passed（458s）**；`compileall` 全仓；change strict 与 live specs strict 通过；`guard extract-problems --course dmath --chapter ch06` PASS。同一轮补做外部 Tutor 验收：真实免费模型（`deepseek-v4.1-flash-free`，1 次调用、成本 0）读真实课程文件产出更新；初次接收因“新增无信封文件”缺陷失败并保留原文，修复后用同一份输出重放（0 次新调用）通过——原始作答不变、新笔记落库、再导出带出。据此勾选 task 2.10，证据见 [Tutor 免费调用与重放](evidence/expand-file-mediated-course-sync/2026-11-07-09/summary.md)；该验收是同一输出的重放，不是第二次 API 往返。

F2 性能已按门槛复测：`cProfile` 显示检查的 61/99 秒花在重复的 `Path.resolve()` 上，按物理文件去重路径校验并缓存根目录解析后（语义不变），预热后导出 p50 17.27s、**无变化检查 20 次 p50 3.10s / p95 3.32s**、接收 p50 9.68s，三项门槛（30/5/30s）全部达标，终态 `changes=0 errors=[]`。证据见 [F2 复测](evidence/expand-file-mediated-course-sync/2026-11-07-11/summary.md)；单机单会话分布，不构成发布级验收。

旧格式接收（SYNC-08 的旧数据部分）也已实测：2026-08-26 的真实 dmath 池导出 347 项、接收 347 项全部落地、0 失败，28 知识点 / 303 题 / 3 作答 / 6 信号与源一致，题目正文逐字保留；为可用而做的两处改动是**已知退役名**的显式跳过——`candidate_problems`/`candidate_attempts` 两个退役表、`problems.topic_label` 这一 DATA_MODEL 已删列——两者都登记在清单里，其它未知表/列仍然报错。证据见 [旧格式接收](evidence/expand-file-mediated-course-sync/2026-11-07-12/summary.md)。

仍未完成：R06 的操作重放指纹与展示缓存两项待决策、真实远端/浏览器、RELEASE-02 安装身份与备份恢复、独立最终验收。tasks 3/19。

## 2026-11-07 有界事务与性能实测

接收改为128项以内的事务批次，每项保存点隔离失败；文件先发布，再处理依赖数据。最新54项检查通过。完整规模单次接收15.854秒（此前264.865秒），但导出141.822秒、无变化检查58.180秒仍未达标；重复检查已无遗漏附件错误。详见 [事务验证](evidence/expand-file-mediated-course-sync/2026-11-07-07/summary.md)。分组传输、引用、完整验收仍未完成。

## 2026-11-07 定时任务启动绑定与测试隔离

原测试误建过实际系统任务（14:43:25），此前“未操作系统任务”的结论作废。已核验、停用并移除该任务，测试已隔离；新的临时任务完成安装/更新/启停/真实CLI隔离运行/删除，未留下常驻任务。任务绑定明确源码目录，安装失败不保存媒介配置；CLI/task25项通过，后续相关子集13项通过。证据见 [任务核验](evidence/expand-file-mediated-course-sync/2026-11-07-06/summary.md)。大型分组文件与事务优化仅已落设计，尚未实现。

## 2026-11-07 多跳修复与完整规模诊断

附件跨设备继续转发、显式删除再传播及最小删除输入校验已补齐，相关50项检查通过。F2单次诊断：导出125.441秒、接收264.865秒、无变化检查64.175秒，均未达到对应门槛；不能用小夹具成绩替代。下一步减少海量小文件和独立提交开销，并完成引用与定时任务修正。详见 [本轮证据](evidence/expand-file-mediated-course-sync/2026-11-07-05/summary.md)。WP01仍未交付。

## 2026-11-07 续跑：WP01 一致性修复，仍未交付

继续使用隔离分支 `codex/course-sync`。本轮补齐接收事务确认、增量来源映射、文件发布意图及独立失败隔离，保护检查后新增的本地修改；修正 Git 冲突仍发布、传输失败缺回执、可读文件漏暂存、旧交换文件漏删除、Tutor 可读文件修改未接收等问题。DeepSeek Go 两轮恢复探测均6/6通过，已完成 R02/S02/C02/C03/F03 独立审查/隔离探测，实际并发未超过2；未使用本机决策模型。

中间版本全仓1,420 passed（449.21s）；其后补充并发保护和畸形执行输入隔离，当前组合检查108 passed（153.79s）。独立建库/迁移与数据检查73 passed；compileall、change strict、live specs21/21、Node偏好12项和extract-problems guard已通过相应轮次。不能把中间版本全仓成绩冒充之后每次修改的最新全仓验收。

仍须优先处理：已接收原始附件不能自动再次导出；文件及知识点删除记录未完整再传播；R02记录的嵌套来源引用与请求缓存；实际F2性能。F2首轮诊断达到规定规模，导出125.441s，超过30s门槛，接收仍在测量。这是单次诊断、不是20轮p95，也未做真实浏览器/专用远端/系统任务/免费LLM验收。完整证据见 [本轮记录](evidence/expand-file-mediated-course-sync/2026-11-07-04/summary.md)。其他工作包仍未开工，原 main 与活动课程未切换。

## 2026-11-07 Codex 接回核对

源码核对到 `codex/course-sync` 的 `5d3b5cef`。第二棒已补齐接收、执行重建、CLI/Git/定时任务入口、Tutor 交接和偏好浏览器接线。本轮组合检查 69 passed，偏好 Node 12 passed。原 main 仍未接收这些实现。

新复现了接收提交边界缺陷。确认文件先于 SQLite commit 发布，模拟 commit 前失败后，数据库仍为旧内容，而重试已把新内容误认为已接收，并规划反向传出旧值。必须先修复这一持久一致性问题，再进行完整同步验收。记录见 [接回核对与复现](evidence/expand-file-mediated-course-sync/2026-11-07-03/progress-audit.md)。完整 F2、免费 LLM、真实浏览器/远端/系统任务和独立验收仍待完成。

## 2026-11-07 接力第二棒（Codex 暂停后）

实际实现仍在 `D:\.codex\worktrees\course-sync\lesson-kit` 的 `codex/course-sync`，原 main 工作区未接收。本轮完成 `3c15a893`（学习偏好浏览器消费与 surface/L2/GLOSSARY/手册/动作图登记）、`cae8215d`（接收端：共同基线=本机接收确认，`apply_exchange` 逐单元提交、失败隔离、显式删除）、`18d3abca`（执行重建：active 运行与 parked 检查点、单项补丁、generation tombstone）与 `6b5988d3`（课程交换 CLI：export/receive/check/sync/status/schedule、回执与退出码 0/2/3/4、Git 编排、每小时任务与冲突通知去重）。接力前 Node 脏检查已全绿；全仓 pytest 1,399 项通过（353s），live specs strict 21/21 通过。

仍未完成：接收端既有 writer 校验接线、Tutor 交接与免费 LLM 回写、benchmarks 与发布级验收。`tasks.md` 2.3–2.10、3.1–3.6 保持未勾选，只有实际证据才能勾选。继续顺序见交接文档末尾的「接力记录」。

## 2026-11-07 实现暂停

用户因 Codex 额度要求暂停并移交其他 Agent。实际实现位于 `D:\.codex\worktrees\course-sync\lesson-kit` 的 `codex/course-sync`，原 main 工作区尚未接收实现。当前仅 WP01 在推进，完整同步 CLI 与接收端尚未交付。

接力先读 [暂停与实现交接](HANDOFF-2026-11-07.md)，其中记录提交、未完成工作、worker 终态、真实检查和继续顺序。P01 偏好接线为半成品，Node 检查仍有失败，不能直接发布。已停止本轮外部 workers，产物和任务书保留。

下文“规划 v1”是此前设计阶段记录，不能当作当前实现状态。

## 2026-11-07 规划 v1

103 个有效回答已收口，用户提供学习协议 V3.1 的新增范围已纳入。近期正常路径是外部 Tutor 使用课程文件、本地 CLI 接收回写。完整课程交换首包包含目标、范围、资料、理解/误解、总结与教学续接文件，另含内容、试卷、附件、原件、学习事实、草稿和已保存偏好。

形成六个独立 change 的 proposal/specs/design/tasks，以及实施入口、决策追踪、契约矩阵、数据矩阵、工作包卡、固定 benchmark 和实际操作场景。原审批默认直接通过，显式成功批次撤销退役，独立有效修改先完成。首包开始时直接采用其 tasks，按当前 checkout 重新核对契约和资产清单。

## 本轮验证

- 六个 change 的 strict 校验通过。
- 当前 live specs 21 项 strict 校验通过。
- 文档相对链接检查、UTF-8读取、103问主题合计及 diff whitespace 检查通过。
- 16 个 MODIFIED requirement 保留共 87 个原场景名称，退役条款通过 REMOVED 显式迁移。

## 真实完成度

本轮完成文档规划。未运行实现测试、真实浏览器、免费LLM、真实Git同步、定时任务或课程数据迁移。benchmarks/catalog 的性能及体验数值为工程制定的目标，全部待实际测量。不能从工件齐全和严格校验推断功能已实现。

存量测试曾有 Pi 编码相关失败，历史证据见 evidence.md；正式实现和验收需在实际环境完整重跑，不能引用本轮文档检查替代。原生 Provider 会话迁移边界按 Q014，课程可读续接已纳入首包。安装与活跃分支的事实在执行入口必须重新核查。

## 后续交付入口

先读 README 与 execution-guide，再进入 expand-file-mediated-course-sync 的完整任务。其他包按 work-packages 依赖推进。每包独立实测、独立验收、精简交付，详细证据完整保留。

## 2026-11-07 紧急暂停（约15:51）

用户因额度要求立即就地交接，禁止再次检查进度。最新接力入口为 [紧急交接](HANDOFF-2026-11-07-URGENT.md)。内容基于最后已知状态：最新提交cb43e860，三个独立模块已提交，核心修复仍在tmp草稿，实际core保持给C05审查的冻结快照；C05/G06/B06/R06最后已知四路及草稿完整规模性能命令可能仍在后台。未核实其随后结果、未停止或重新派发任何进程、未声称交付。接手必须先核对台账与终态，再继续。

## 下一轮入口：S011

按所有者2026-11-07新确认，先同步交付与改卷联动，再内容数据库能力。具体阶段、联动矩阵、重复请求语义、证据和收尾边界见 [下一轮执行计划](NEXT-EXECUTION-PLAN-2026-11-07.md)。本轮仅整理计划，未修改程序或执行归档/部署。
