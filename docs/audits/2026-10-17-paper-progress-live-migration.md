# 2026-10-17 Paper 独立进度：正式池迁移快照

## 授权与代码

沿用所有者“检查其它课程，未迁移则统统迁移”的明确授权，应用本项正常使用所需的增量字段。代码为 `3812b42f`，`pool/scripts/migrate-progress.py` / `ensure_workbench_schema`。这是带日期的审计快照，不取代 DATA_MODEL 或 live OpenSpec。

## 结果

17 个正式注册池全部完成迁移，各留一份新的 SQLite backup，文件名为 `<原库>.pre-paper-progress-20261017-<时分秒>`。所有真实结果与对应的已验证副本在 schema、原字段/原行及新增执行元数据上完全一致；完整性检查均为 `ok`。没有向原库提交测试作答、评分、删题或改卷。

每个池应用前均重新比较原库与此前的只读快照；备份完成后再次比较。副本迁移事先通过全部原列投影值保留及幂等复跑。既有学习/内容行不删不改；新执行 ID 仅标识旧 active 状态，既有题序、游标、attempt 关联不变。旧备份未清理。

CO 原有 19 个缺失 attempt 父记录仍是 19 个，旧 70 项状态保留；迁移不把它们转挂到当前 22 题卷、不补造作答。未出现新的外键错误。没有对临时副本发起真实写入。

完整逐池源路径、备份路径、schema 改动、行数、外键结果、CLI 回执及可重复的审计/应用脚本：

`C:\Users\yanwei\AppData\Local\Temp\lesson-kit-paper-all-course-20261017\batch-report.json`

`C:\Users\yanwei\AppData\Local\Temp\lesson-kit-paper-all-course-20261017\batch_migrate.py`

## 运行验收边界

独立 gpt-6-luna max 使用三个另外的真实课程副本与隔离注册表/端口，进行了浏览器和 HTTP/CLI 验收。切卷、草稿重启恢复、语义修改、旧提交零写入、确认式改卷、删题/删卷保留均在副本进行。Physics 的旧 120 项执行恢复后保持 cursor 3、3 stuck、117 pending 和 attempt 1–3；空草稿从 SQL NULL 序列化成 `{}`，语义不变。CO 界面明确列出缺失题号并禁用恢复，拒绝启动不会修改任何表。

证据目录：`C:\Users\yanwei\AppData\Local\Temp\lesson-kit-paper-acceptance-20261017\review-run-02`。
关键文件：`migration-preservation.json`、`acceptance-lifecycle-continuation.json`、`co-runtime-http.json`、`physics-park-restore.json`。运行验收曾发现跨卷浏览器缓存污染；修复后复验通过，Node 回归同时防止 A 的迟到回执污染 B。

选择、判断、开放题控件均在真实副本的浏览器中实际见到。A/B 过程操作了选择题；另用两个只含既有判断题/开放题的副本试卷核对“是/否”单选和文本框，不提交作答。设置回执见 `runtime-ui-control-papers.json`，Playwright 快照时间为 07:55:07 / 07:55:50 UTC。语义修改和删除的细粒度保持性由 HTTP/CLI 与逐表快照检查证明，不冒充每一步都由鼠标完成。

生产服务的代码位置、PID、HTTP 只读回读及所服务静态文件的字节一致性，以发布时生成的 `C:\Users\yanwei\AppData\Local\Temp\lesson-kit-paper-all-course-20261017\production-server.json` 为凭据；副本验收不等于真实库有测试学习记录。
