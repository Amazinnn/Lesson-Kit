## 1. 当前契约与失败基线

- [ ] 1.1 阅读本 change 全部工件、对应 package、execution-guide、contract-reconciliation、data-exchange-matrix 和 benchmarks/catalog，记录分支、commit、实际运行身份及重叠 change。
- [ ] 1.2 逐条核对本包已提供的 MODIFIED/REMOVED delta，补齐命中的次级引用，保持原场景名称或明确迁移；先更新职责契约再改代码。
- [ ] 1.3 在隔离课程副本建立 F1/F3/F4 回归样本，先运行针对本包缺口的失败检查，保存结果和期望差异。

## 2. 实现与逐单元检查

- [ ] 2.1 练习开始入口读取所有未完成Paper执行并恢复同一执行；30卷夹具无淘汰，显式目标覆盖last-course。
- [ ] 2.2 按execution_id清除本次未完成进度/草稿，加入晚到请求和本地出站箱身份校验，原Paper/题目/历史/其他执行不变。
- [ ] 2.3 在包证据中建立全部标题字段与显示/重命名读取表，用现有安全richText渲染并从持久源取编辑值。
- [ ] 2.4 逐字段验证Markdown/LaTeX、特殊字符、长标题和打开取消/原样保存；不得把DOM/KaTeX辅助文本写回。
- [ ] 2.5 当前输入/IME/未确认写入延后刷新，其他内容照常更新；真实输入、切题和Agent修改检验 PRACTICE-03。

## 3. 契约与实际验收

- [ ] 3.1 同步被命中的 GLOSSARY、DATA_MODEL、FILE_CONTRACT、ARCHITECTURE、PRODUCT-MANUAL、ACTION-GRAPH、surface、提示词及 agent_contracts，未受影响文件不机械改写。
- [ ] 3.2 按 PRACTICE-01–04 执行固定夹具、次数和门槛，保存真实CLI/浏览器/必要免费LLM证据，报告未达标和未运行，逐项区分模拟与实际入口。
- [ ] 3.3 执行 RELEASE-01 全仓检查及本包相关 Node/浏览器检查，失败原样登记并修复或明确阻断交付。
- [ ] 3.4 执行 RELEASE-02 的副本迁移、备份恢复及安装身份核对，验证目标入口实际使用本次源代码。
- [ ] 3.5 由独立验收角色复核完整证据，按真实通过情况勾选任务，生成精简交付摘要、完整交接和剩余限制。
- [ ] 3.6 每个可验证单元按具体路径提交；合入前按当前仓库策略处理，运行切换遵守S008默认直接通过，只有实际验证过的行为可标记已交付。
