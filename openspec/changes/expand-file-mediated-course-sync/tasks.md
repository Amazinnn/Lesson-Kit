## 1. 当前契约与失败基线

- [ ] 1.1 阅读本 change 全部工件、对应 package、execution-guide、contract-reconciliation、data-exchange-matrix 和 benchmarks/catalog，记录分支、commit、实际运行身份及重叠 change。
- [ ] 1.2 逐条核对本包已提供的 MODIFIED/REMOVED delta，补齐命中的次级引用，保持原场景名称或明确迁移；先更新职责契约再改代码。
- [ ] 1.3 在隔离课程副本建立 F1/F3/F4 回归样本，先运行针对本包缺口的失败检查，保存结果和期望差异。

## 2. 实现与逐单元检查

- [ ] 2.1 从实际 schema、注册目录及浏览器保存值生成覆盖表，对 data-exchange-matrix 每行登记字段、writer、consumer、引用、删除和旧格式。F1/F4 中每类均有样本，未知类型不得静默略过。
- [ ] 2.2 在 workbench/domain/course_sync.py 实现 plan_exchange 的纯比较，先覆盖无变化、单侧、同改一致、双侧、明确删除/缺文件、历史并集和按题草稿冲突。通过 tests/workbench/test_course_sync.py 的表驱动反例。
- [ ] 2.3 在 workbench/data/course_sync.py 复用现有查询导出完整manifest、正文与附件，保存课程来源和记录来源映射。F1 逐字段和字节核对，再在 F2 计时。
- [ ] 2.4 实现预检、注册新课程、身份疑点输入、独立单元接收及中断续办；按同一操作身份重试。每个数据库/文件发布边界注入失败，证明无悬空引用和重复作答。
- [ ] 2.5 将目标、范围、资料索引、总结、误解和续接文件全部登记并接收 CRUD；定义无原生会话也可读取的 Tutor handoff，原始答案/揭晓/未答项完整。
- [ ] 2.6 为浏览器学习偏好建立已确认保存的课程投影和接收消费路径。A→B 后真实练习验证提交粒度和揭晓时机，未确认浏览器输入不得冒充已保存。
- [ ] 2.7 新增 workbench/cli/course_sync.py 并在 main.py/surface.py 注册 export/receive/check/sync/status/schedule。按 design 的 JSON/status/退出码契约测试一次导出、一次接收、无手改版本的单侧更新。
- [ ] 2.8 新增 workbench/bridge/git_sync.py，参数数组调用显式cwd的系统git，只stage受管理路径；以临时bare仓库覆盖push拒绝、真实分叉和无变化，再以专用远端回读验证。
- [ ] 2.9 系统任务按每小时、全部已配置课程调用同一CLI，提供安装/更新/启停/删除。实测手动并发、某课程受阻、凭据缺失和一次冲突通知。
- [ ] 2.10 用免费真实LLM在独立对话读取课程文件，输出更新后CLI接收并反向交换；保存输入输出与实际落库，不能只给模拟器日志。

## 3. 契约与实际验收

- [ ] 3.1 同步被命中的 GLOSSARY、DATA_MODEL、FILE_CONTRACT、ARCHITECTURE、PRODUCT-MANUAL、ACTION-GRAPH、surface、提示词及 agent_contracts，未受影响文件不机械改写。
- [ ] 3.2 按 SYNC-01–08、FS-01–11、LP-01/02 执行固定夹具、次数和门槛，保存真实CLI/浏览器/必要免费LLM证据，报告未达标和未运行，逐项区分模拟与实际入口。
- [ ] 3.3 执行 RELEASE-01 全仓检查及本包相关 Node/浏览器检查，失败原样登记并修复或明确阻断交付。
- [ ] 3.4 执行 RELEASE-02 的副本迁移、备份恢复及安装身份核对，验证目标入口实际使用本次源代码。
- [ ] 3.5 由独立验收角色复核完整证据，按真实通过情况勾选任务，生成精简交付摘要、完整交接和剩余限制。
- [ ] 3.6 每个可验证单元按具体路径提交；合入前按当前仓库策略处理，运行切换遵守S008默认直接通过，只有实际验证过的行为可标记已交付。
