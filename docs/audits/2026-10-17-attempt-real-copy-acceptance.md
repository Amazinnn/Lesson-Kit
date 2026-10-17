# Attempt 修复：真实课程副本验收 · 2026-10-17

代码候选：`5f29affb`。本记录是实施 Agent 根据用户追加要求完成的真实副本验收，
不冒充另一位 Agent 的独立审查，也不代表真实课程库已迁移或服务已部署。

## 环境与保全

使用 SQLite 只读连接和 backup API，从当前注册的大学物理乙II `pool/c01.db`、计算机组成
`pool/co.db` 生成一致性快照；各保留 `raw.db`、仅外键修复副本、完整迁移副本。
来源完整路径、UTC 捕获时间和快照路径保存在本地 `provenance.json`。

证据目录：`C:\Users\yanwei\AppData\Local\Temp\lesson-kit-real-acceptance-20261017-19x73eii`。
`migration-report.json` 保存完整外键检查和前后差异，`browser-result.json` 保存浏览器作答后的核验结果。
独立注册表在该目录 `registry/`，测试服务使用端口 3087、当前候选 worktree；未修改用户注册表，
未重启 3081 正式服务，未向真实库提交任何练习或迁移。

## 结构修复结果

两库均逐行比较全部 25 张表，包含内部序列表；只运行本次外键修复函数后所有行完全相同，
唯一变化的 schema 对象是 `active_practice_items` 的外键声明。再次执行无结构或数据变化。

| 项目 | 大学物理乙II | 计算机组成 |
| --- | --- | --- |
| 正式题数 | 694 | 658 |
| 原有作答数 | 0 | 0 |
| 当前检查点数 | 0 | 70 |
| 原有调度数 | 0 | 19 |
| 修复后外键违规数 | 0 | 19 |

CO 的 19 条违规对应 `active_practice_items` 的位置 0–18，缺失 attempt ID 为 1–19。
外键父表从 `problem_attempts_widening_old` 修正为 `problem_attempts`，但这些作答仍不存在。
警告明确报告全部违规与缺失 ID，没有补造作答或删除任何检查点、调度记录。
物理子表为空时 `foreign_key_check` 本来就可能返回空；因此同时检查 DDL，不能把空结果当成声明健康。

## 完整既有迁移命令的额外效果

在各自新副本运行候选代码的
`python pool/scripts/migrate-progress.py --db <副本路径>`，两者退出码均为 0，首次输出三项：
`active_practice_items.attempt_foreign_key`、`active_practice.source_kind-paper`、
`practice_runs.source_kind-paper`。再次执行无新增迁移项。

完整命令还执行既有 ensure：两库 `sqlite_sequence` 新增空 `practice_runs` 的序号 0；CO 的
`content_sequences` 中 `(co-ch02, kp)` 的 next_value 从 26 校准至 30。
这些是既有完整迁移路径的效果，不是本次纯外键函数的改动；其他原有行值保持一致。
首次使用过度宽泛的“完整迁移所有表零变化”断言因此失败；经逐表比较，将这些真实差异显式记录，
没有把它们掩盖成保全通过。真实库执行前应审阅完整命令的影响，而非仅凭外键函数结果授权。

## 物理 Failed to fetch 的复现与浏览器验收

原库中 `active_practice.source_kind` 和 `practice_runs.source_kind` 的 CHECK 仍只接受
`quick / practice_set / agent`，Data 写入已归一成 `paper`。正式服务日志记录
`practice_set_start → active_practice.create → sqlite3.IntegrityError`。
HTTP dispatch 未捕获该异常，连接关闭而没有 JSON 错误响应。

1. 独立端口打开真实物理副本的组卷页，确认今天保存的 `ps-001`：
   「第三周随堂习题（Ch13 静电介质与能量 + Ch14 稳恒电流与磁场）」、120 题。
2. 迁移前点击“开始练习”：POST `/practice-sets/ps-001/start` 返回
   `net::ERR_EMPTY_RESPONSE`，页面显示 `Failed to fetch`。不是试卷未保存。
3. 同一副本执行完整迁移后，重试同一按钮返回 HTTP 200，成功进入 120 题执行。
4. 继续练习，第一题判断题选择“是”，提交、查看解析、自评 5、下一题；attempt 与 feedback
   请求均 HTTP 200。副本各新增 1 条 attempt、feedback、progress、schedule；首检查点为
   `(position=0, state=answered, attempt_id=1)`，cursor 为 1，外键检查为空。
5. 停止并重启仅测试端口的服务，重新打开页面，恢复第二题；不重复产生作答。

Playwright 快照证据时间：03:44:37Z（失败）、03:45:47Z（开始成功）、03:46:33Z（自评后）、
03:46:54Z（重启恢复）。本地 `.playwright-mcp/` 中保存了这些工具快照。

## 发现的相邻问题与剩余边界

组卷页把任意开始失败都解释为“已有未完成练习”，弹出清除旧进度确认；本次副本实际无旧练习，
因此该提示不实。应只对确切的未完成冲突呈现对应确认；服务器也应把未迁移池转成明确错误响应。
这些属于 Paper/API 错误呈现的后续修复，本验收未改动其他 Agent 的 change 或共享前端文件。

真实大学物理库尚未迁移；真实 CO 的 19 个缺失父记录仍需单独恢复方案。
本地 raw 快照是本次副本验收来源，不宣称已验证任何更早历史备份能恢复缺失作答。
