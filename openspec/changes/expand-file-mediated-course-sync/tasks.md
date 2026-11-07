## 1. 当前契约与失败基线

- [x] 1.1 阅读本 change 全部工件、对应 package、execution-guide、contract-reconciliation、data-exchange-matrix 和 benchmarks/catalog，记录分支、commit、实际运行身份及重叠 change。
- [x] 1.2 逐条核对本包已提供的 MODIFIED/REMOVED delta，补齐命中的次级引用，保持原场景名称或明确迁移；先更新职责契约再改代码。（证据 `evidence/expand-file-mediated-course-sync/2026-11-08-accept/1-2-delta-check.md`：9 条 ADDED 属新能力、0 条 REMOVED；唯一 MODIFIED「Learner settings in the settings view」4 条现行场景逐条保留 + 2 条新增；全仓 live spec 无该偏好的次级引用）
- [x] 1.3 在隔离课程副本建立 F1/F3/F4 回归样本，先运行针对本包缺口的失败检查，保存结果和期望差异。（证据 `…/2026-11-08-accept/1-3-regression-samples.md`：F1/F3/F4 夹具与报告、两个先失败后修复的缺口及其回归用例、本轮 SYNC-04 新样本）

## 2. 实现与逐单元检查

- [ ] 2.1 从实际 schema、注册目录及浏览器保存值生成覆盖表，对 data-exchange-matrix 每行登记字段、writer、consumer、引用、删除和旧格式。F1/F4 中每类均有样本，未知类型不得静默略过。
- [x] 2.2 在 workbench/domain/course_sync.py 实现 plan_exchange 的纯比较，先覆盖无变化、单侧、同改一致、双侧、明确删除/缺文件、历史并集和按题草稿冲突。通过 tests/workbench/test_course_sync.py 的表驱动反例。
- [ ] 2.3 在 workbench/data/course_sync.py 复用现有查询导出完整manifest、正文与附件，保存课程来源和记录来源映射。F1 逐字段和字节核对，再在 F2 计时。
- [x] 2.4 实现预检、注册新课程、身份疑点输入、独立单元接收及中断续办；按同一操作身份重试。每个数据库/文件发布边界注入失败，证明无悬空引用和重复作答。（预检/注册新课程：F1 一次接收；身份疑点：F3 同名异源需显式 associate；独立单元：`test_bad_execution_item_does_not_block_independent_content`；文件发布失败续办：`test_file_publication_failure_has_read_only_inspection_and_resumes`；进程级中断与重试：`…/2026-11-08-accept/3-2-sync-04-process-kill.md`，真子进程硬杀 ×4 后计数一致、无重复作答、无缺失/多余文件；顺带修复孤儿 `.tmp` 被当资产传播的缺陷 + 回归用例）
- [ ] 2.5 将目标、范围、资料索引、总结、误解和续接文件全部登记并接收 CRUD；定义无原生会话也可读取的 Tutor handoff，原始答案/揭晓/未答项完整。
- [ ] 2.6 为浏览器学习偏好建立已确认保存的课程投影和接收消费路径。A→B 后真实练习验证提交粒度和揭晓时机，未确认浏览器输入不得冒充已保存。
- [ ] 2.7 新增 workbench/cli/course_sync.py 并在 main.py/surface.py 注册 export/receive/check/sync/status/schedule。按 design 的 JSON/status/退出码契约测试一次导出、一次接收、无手改版本的单侧更新。
- [x]  新增 workbench/bridge/git_sync.py，参数数组调用显式cwd的系统git，只stage受管理路径；以临时bare仓库覆盖push拒绝、真实分叉和无变化，再以专用远端回读验证。
- [ ] 2.9 系统任务按每小时、全部已配置课程调用同一CLI，提供安装/更新/启停/删除。实测手动并发、某课程受阻、凭据缺失和一次冲突通知。（计划任务安装/停用/启用/删除已验证，调度触发未验证）
- [x] 2.10 用免费真实LLM在独立对话读取课程文件，输出更新后CLI接收并反向交换；保存输入输出与实际落库，不能只给模拟器日志。证据：`evidence/expand-file-mediated-course-sync/2026-11-07-09/`（真实免费调用 1 次，初次接收失败原文保留；修复后以同一份输出重放，0 次新调用，原始作答不变、新笔记落库、再导出带出）。

## 3. 契约与实际验收

- [x] 3.1 同步被命中的 GLOSSARY、DATA_MODEL、FILE_CONTRACT、ARCHITECTURE、PRODUCT-MANUAL、ACTION-GRAPH、surface、提示词及 agent_contracts，未受影响文件不机械改写。（证据 `…/2026-11-08-accept/3-1-contract-sync.md`：8 份职责文件逐项对应改动；`skills/**` 与 `agent_contracts` 未命中，给出未改理由）
- [ ] 3.2 按 SYNC-01–08、FS-01–11、LP-01/02 执行固定夹具、次数和门槛，保存真实CLI/浏览器/必要免费LLM证据，报告未达标和未运行，逐项区分模拟与实际入口。（SYNC-01/02/03/05/07/08 与 LP-01 通过；FS-08 恢复依赖 adaptive 3.2，SYNC-06 触发未验证）
- [x]  执行 RELEASE-01 全仓检查及本包相关 Node/浏览器检查，失败原样登记并修复或明确阻断交付。
- [x]  执行 RELEASE-02 的副本迁移、备份恢复及安装身份核对，验证目标入口实际使用本次源代码。
- [x]  由独立验收角色复核完整证据，按真实通过情况勾选任务，生成精简交付摘要、完整交接和剩余限制。
- [x]  每个可验证单元按具体路径提交；合入前按当前仓库策略处理，运行切换遵守S008默认直接通过，只有实际验证过的行为可标记已交付。

## 4. 与改卷历史的同步联动（S011）

- [x] 4.1 把 `retired_paper_items` 纳入完整资产矩阵：身份带安装来源、attempt 引用转换、接收端分配本地序号、多跳传递与重复接收幂等。（实现 `workbench/data/course_sync.py`；`tests/workbench/test_course_sync_lifecycle.py` 覆盖首跳/次跳/同号并存/重复接收）
- [x] 4.2 历史快照中不可解析的引用如实报告且不阻断导出；不按相同编号绑定本地记录。（导出清单 `dangling_history_references`；同上测试）
- [x] 4.3 跨机重复请求识别并返回原结果；同请求不同内容仍为真实冲突；历史显示快照与可操作引用分离。（`attempts._correction_already_holds`：指纹绑在本机 attempt 号上的 `correct` 在目标机按「效果已成立」返回原结果且零写入；不同内容仍是真实冲突；显示缓存编号保留为不透明值、不重绑，见 `tests/workbench/test_course_sync_lifecycle.py`）
- [ ] 4.4 LIFE-SYNC 全矩阵（active/parked、首尾/游标题移除、全移除、中断重试、旧库无表接收）与真实入口验收。（证据 `…/2026-11-08-accept/4-4-life-sync.md`：六行逐条映射到用例，中断重试由 SYNC-04 硬杀覆盖，真实入口含 CLI/浏览器/免费 LLM；保留意见：未对 Git 提交本身做硬杀、仅 Windows 验证。**该项待 2.7 CLI 回执证据落定后一并勾**）
