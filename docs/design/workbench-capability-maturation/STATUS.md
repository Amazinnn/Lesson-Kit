# 规划交接状态

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
