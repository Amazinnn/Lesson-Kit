## 1. 当前契约与失败基线

- [x] 1.1 阅读本 change 全部工件、对应 package、execution-guide、contract-reconciliation、data-exchange-matrix 和 benchmarks/catalog，记录分支、commit、实际运行身份及重叠 change。证据 `evidence/retire-project-approval-gates/2026-11-08-baseline/1-1-1-2-baseline.md`。
- [x] 1.2 逐条核对本包已提供的 MODIFIED/REMOVED delta，补齐命中的次级引用，保持原场景名称或明确迁移；先更新职责契约再改代码。同上证据：10 块 delta 全部场景保全，change strict ✓。
- [x] 1.3 在隔离课程副本建立 F1/F3/F4 回归样本，先运行针对本包缺口的失败检查，保存结果和期望差异。证据 `2026-11-08-baseline/1-3-failing-checks.txt`（4 红 + 1 护栏绿），样本=WorkspaceFixture 副本 + 合成 legacy pending 记录（F4 旧形状）。

## 2. 实现与逐单元检查

- [x] 2.1 修改 Bridge action/提示词，沿既有 Data Paper 更新直接执行，去除额外批准状态和派发阻断；无页面时也完成，目标历史/其他Paper保留。`_apply_paper_update_action` + `_notice_outcome` 回执 + `_prompt`/agent_contracts 措辞；提交点 revalidation 由 preview+update_saved 承担。
- [x] 2.2 实现一次性 pending approval 迁移，校验真实workspace/turn/Paper及操作身份，已执行不重写，失效输入真实记录未完成。两次恢复证明最多写入一次。`_reconcile_legacy_paper_approvals` 挂 get()/start_turn()/interrupt_pending()；证据 `evidence/retire-project-approval-gates/2026-11-08-impl/2-1-2-2-direct-and-reconcile.md`。
- [x] 2.3 删除回滚/改卷/重做等审批卡、批准按钮和composer替换；删除审批暂停保留用户主动停止暂停。逐旧入口截图与可访问树确认 FLOW-01。证据 `evidence/retire-project-approval-gates/2026-11-08-impl/2-3-ui-retirement.md`（浏览器：审批元素不在 DOM、proposal 直执行、legacy pending 重开自动迁移最多一次、重做零弹窗直开；node：DOM 契约全改写）。
- [x] 2.4 准备、备份和副本验证通过后的部署直接切换；验证 installed CLI、source_root、进程身份及资源版本，不等待另一批准。证据 `evidence/retire-project-approval-gates/2026-11-08-impl/2-4-cutover.md`（无 schema 变更；installed CLI=主检出、两个 daemon 的 source_root/pid/assets 全核、静态资源为新代码、3099 验收后 stop 复原）。

## 3. 契约与实际验收

- [x] 3.1 同步被命中的 GLOSSARY、DATA_MODEL、FILE_CONTRACT、ARCHITECTURE、PRODUCT-MANUAL、ACTION-GRAPH、surface、提示词及 agent_contracts，未受影响文件不机械改写。commit `98eaca82`：GLOSSARY 两条退役词条+Agent 表面/中断条目、ARCHITECTURE 279 直执行条款、PRODUCT-MANUAL §4/§8.5/§9 措辞、动作图 L0/L2/L3/L4；DATA_MODEL/FILE_CONTRACT 零命中未动。
- [x] 3.2 按 FLOW-01–03、RELEASE-02 执行固定夹具、次数和门槛，保存真实CLI/浏览器/必要免费LLM证据，报告未达标和未运行，逐项区分模拟与实际入口。证据 `evidence/retire-project-approval-gates/2026-11-08-impl/3-2-flow-and-release.md`：FLOW-01 浏览器+CLI 实测（零审批点击/零待确认/写入一次）、FLOW-02 双恢复证明、FLOW-03 CLI 直修正实测+旧撤销入口不存在。
- [x] 3.3 执行 RELEASE-01 全仓检查及本包相关 Node/浏览器检查，失败原样登记并修复或明确阻断交付。node 全套 0 fail、compileall、strict 25/25、change strict、guard extract-problems PASS；全仓 pytest 终检（后台）另记。
- [x] 3.4 执行 RELEASE-02 的副本迁移、备份恢复及安装身份核对，验证目标入口实际使用本次源代码。本包无 schema 变更/无池写入（无迁移副本可升）；副本验证=wb64 实跑+全仓 pytest；安装身份核对见 `2-4-cutover.md`。
- [ ] 3.5 由独立验收角色复核完整证据，按真实通过情况勾选任务，生成精简交付摘要、完整交接和剩余限制。
- [ ] 3.6 每个可验证单元按具体路径提交；合入前按当前仓库策略处理，运行切换遵守S008默认直接通过，只有实际验证过的行为可标记已交付。
