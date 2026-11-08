## 1. 当前契约与失败基线

- [ ] 1.1 阅读本 change 全部工件、对应 package、execution-guide、contract-reconciliation、data-exchange-matrix 和 benchmarks/catalog，记录分支、commit、实际运行身份及重叠 change。
- [ ] 1.2 逐条核对本包已提供的 MODIFIED/REMOVED delta，补齐命中的次级引用，保持原场景名称或明确迁移；先更新职责契约再改代码。
- [ ] 1.3 在隔离课程副本建立 F1/F3/F4 回归样本，先运行针对本包缺口的失败检查，保存结果和期望差异。

## 2. 实现与逐单元检查

- [x] 2.1 修改 data.content 查询和 installed CLI 筛选：type/章/文字组合，经验与来源检索，基础投影及关联题目去重。F2 100次查询验证 DATA-01。（证据 `evidence/mature-course-content-operations/2026-11-08-query/2-1-query.md`：`knowledge_query`/`related_problems` + CLI `--knowledge-type/--chapter` 与 `related`；DATA-01 100 次 p95 2.2ms ≤1s；7 用例）
- [ ] 2.2 复用 ingest content-bundle 提炼模型，先查同义已有点；新增点含条件/公式/步骤并自动给适用原题追加关联。8个标注案例覆盖已有点、新模型与反例。
- [x] 2.3 沿 ensure_* 增量迁移添加独立章节归属，回填旧ID初始章，更新所有推章消费者。使用带经验、关系和历史的旧点迁移并文件往返，记录全部引用。（证据 `evidence/mature-course-content-operations/2026-11-08-chapter/2-3-chapter-ownership.md`：`ensure_knowledge_chapter_schema` 加列+整段回填（多段章 `source-ch03` 已覆盖）；读取口径「列优先、NULL 回退」落在 Pool.kps/chapters、列表分组、knowledge_query、create、ingest 两处；`data move kp --chapter` 只改列、ID 不变，关系/经验/透镜/文件往返均有用例。**按所有者决定只改 workbench 层**，冻结层仍按 ID 推章并记为边界）
  - 合并审查保留 main 的章节查询回归；列值明确为空时不回退到旧 ID。

- [ ] 2.4 将 bundle/problem-patch/card/quiz/figure相关应用拆为独立完整单元；修改旧all-or-nothing场景，保持单元一致、批次provenance和重试身份。
  - 2026-11-08 审查拒收 stash：重复题与悬空闪卡报错仍写入，附件失败触发整包回滚；不是仅改写旧测试即可交付。见 `docs/audits/2026-11-08-wp02-review.md`。stash 保留，未应用。
- [x] 2.5 退役成功批次undo CLI/Agent提示/操作入口，历史 rolled_back 保持可读；用直接修正完成相同修错任务，FLOW-03实际走通。（证据 `evidence/mature-course-content-operations/2026-11-08-batch-undo/2-5-retire-batch-undo.md`：一次性移除 CLI/HTTP/前端按钮/Agent 提示/`rollback_batch` 及 7 个专用助手（净删 362 行）；保留 `rolled_back_at` 与历史卡片标记；FLOW-03 直接修正实跑：题号不变、作答原文不动、撤销入口已不存在；受影响套件 104 passed）
- [ ] 2.6 用原文标注20个映射/完整性案例，分别报告结构检查和语义核对。限定章节分类补齐只改有依据项，疑点不进入已核对练习。

## 3. 契约与实际验收

- [ ] 3.1 同步被命中的 GLOSSARY、DATA_MODEL、FILE_CONTRACT、ARCHITECTURE、PRODUCT-MANUAL、ACTION-GRAPH、surface、提示词及 agent_contracts，未受影响文件不机械改写。
- [ ] 3.2 按 DATA-01–05、CONTENT-01、FLOW-03 执行固定夹具、次数和门槛，保存真实CLI/浏览器/必要免费LLM证据，报告未达标和未运行，逐项区分模拟与实际入口。
- [ ] 3.3 执行 RELEASE-01 全仓检查及本包相关 Node/浏览器检查，失败原样登记并修复或明确阻断交付。
- [ ] 3.4 执行 RELEASE-02 的副本迁移、备份恢复及安装身份核对，验证目标入口实际使用本次源代码。
- [ ] 3.5 由独立验收角色复核完整证据，按真实通过情况勾选任务，生成精简交付摘要、完整交接和剩余限制。
- [ ] 3.6 每个可验证单元按具体路径提交；合入前按当前仓库策略处理，运行切换遵守S008默认直接通过，只有实际验证过的行为可标记已交付。
