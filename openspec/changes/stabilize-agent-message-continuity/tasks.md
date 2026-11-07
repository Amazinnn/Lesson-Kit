## 1. 当前契约与失败基线

- [ ] 1.1 阅读本 change 全部工件、对应 package、execution-guide、contract-reconciliation、data-exchange-matrix 和 benchmarks/catalog，记录分支、commit、实际运行身份及重叠 change。
- [ ] 1.2 逐条核对本包已提供的 MODIFIED/REMOVED delta，补齐命中的次级引用，保持原场景名称或明确迁移；先更新职责契约再改代码。
- [ ] 1.3 在隔离课程副本建立 F1/F3/F4 回归样本，先运行针对本包缺口的失败检查，保存结果和期望差异。

## 2. 实现与逐单元检查

- [ ] 2.1 建立可计数provider与内容写入夹具，分别复现UI重复呈现与真实重复操作。记录submission_id、接受次数、provider次数和数据库变化。
- [ ] 2.2 统一已接受用户消息与真实部分输出的历史投影，失败消息保留在流中；未知送达复用原身份，明确手动重试用linked新身份及当前编辑文本。
- [ ] 2.3 服务端主动停止暂停待处理项，重启never-started保持暂停。普通失败不自动重试原项，独立后项按原流程继续，CHAT-02逐次验证。
- [ ] 2.4 同时检查 aiRenderPendingQueue/aiRenderOutbox，仅正文编辑删除；移除排序/立即发送/额外字段。编辑删除竞态保留revision和原始捕获上下文。
- [ ] 2.5 两课程同题ID与A→B切题场景验证发送时上下文不变，等待只短状态/停止。真实浏览器完成 CHAT-01–05。

## 3. 契约与实际验收

- [ ] 3.1 同步被命中的 GLOSSARY、DATA_MODEL、FILE_CONTRACT、ARCHITECTURE、PRODUCT-MANUAL、ACTION-GRAPH、surface、提示词及 agent_contracts，未受影响文件不机械改写。
- [ ] 3.2 按 CHAT-01–05 执行固定夹具、次数和门槛，保存真实CLI/浏览器/必要免费LLM证据，报告未达标和未运行，逐项区分模拟与实际入口。
- [ ] 3.3 执行 RELEASE-01 全仓检查及本包相关 Node/浏览器检查，失败原样登记并修复或明确阻断交付。
- [ ] 3.4 执行 RELEASE-02 的副本迁移、备份恢复及安装身份核对，验证目标入口实际使用本次源代码。
- [ ] 3.5 由独立验收角色复核完整证据，按真实通过情况勾选任务，生成精简交付摘要、完整交接和剩余限制。
- [ ] 3.6 每个可验证单元按具体路径提交；合入前按当前仓库策略处理，运行切换遵守S008默认直接通过，只有实际验证过的行为可标记已交付。
