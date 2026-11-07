# 3.2 SYNC / FS / LP 验收矩阵（2026-11-08）

任务原文：> 按 SYNC-01–08、FS-01–11、LP-01/02 执行固定夹具、次数和门槛，保存真实 CLI/浏览器/必要免费 LLM 证据，报告未达标和未运行，逐项区分模拟与实际入口。

本表汇总 P3（`../2026-11-08-p3/`）、P4（`../2026-11-08-p4/`）与本轮（`./`）的实际结果。

| 编号 | 结果 | 证据 |
|---|---|---|
| SYNC-01 完整课程交换 | **通过** | `../2026-11-08-p3/f1-report.json`（99 项资产，8 表计数一致） |
| SYNC-02 性能门槛 | **通过**（导出 p95 18.23s ≤30、无变化 3.19s ≤5、接收 9.96s ≤30；预热 1 + 各 20 次） | `../2026-11-08-p3/f2-timing.json` |
| SYNC-03 单侧/双侧/冲突/删除协调 | **通过** | `f1-report.json`、`f3-report.json` |
| SYNC-04 中断与重试 | **通过（本轮补真进程 kill）**：导出杀 1 次、接收杀 3 次，重试后计数一致、无重复作答、无缺失/多余文件；顺带修复孤儿 `.tmp` 被当资产传播 | `./3-2-sync-04-process-kill.md`、`./sync-04-kill-report.json` |
| SYNC-05 Git 传输 | **通过**（专用本地 bare 远端：发布/无变化/FF/拒推 exit 4/他源 exit 2/只 stage 包内路径） | `../2026-11-08-p3/git-report.json` |
| SYNC-06 每小时调度 | **部分**：安装/停用/启用/删除与任务命令实测通过；**真实调度触发未验证**（`schtasks /Run`、`Start-ScheduledTask` 后 `LastRunTime` 更新但动作无副产物） | `../2026-11-08-p3/task-report.json`、`./2-9-scheduled-task.md` |
| SYNC-07 外部 Tutor 往返 | **通过** | `f1-report.json`（LP-01 步骤）+ `../2026-11-07-09/`（1 次真实免费调用、0 重放） |
| SYNC-08 旧格式与身份 | **通过**（真实 2026-08-26 旧池 347 项 0 失败；同名异源需显式 associate；未知格式/表/缺图如实拒绝） | `../2026-11-08-p3/f4-report.json`、`f3-report.json` |
| FS-01 全资产往返 | **通过** | `f1-report.json` |
| FS-02 新资产接收 | **通过** | `f1-report.json` |
| FS-04 双侧修改选侧 | **通过** | `f3-report.json` |
| FS-05 缺文件如实阻断 | **通过**（exit 2，Paper 行保留，不写包） | `f1-report.json` |
| FS-06 共享题删除传播 | **通过**（保留历史 1 行，B 侧执行移除） | `f1-report.json` |
| FS-07 删知识点连带关系 | **通过**（关系清空、题目保留） | `f1-report.json` |
| FS-08 归档题恢复 | **通过（P4 补做）**：`data restore problem`，原卷不加回，重复恢复 `already_current` | `../2026-11-08-p4/`、`test_restoring_an_archived_question_keeps_it_out_of_its_papers` |
| FS-09 两侧各新增作答 | **通过**（往返两次合并、重复接收 `applied=[]`） | `f3-report.json` |
| FS-10 批量选侧 | **通过** | `f3-report.json` |
| FS-11 删改冲突保留 | **通过**（`applied=0 failed=0`，不自动选侧） | `f3-report.json` |
| LP-01 新设备读交接 | **通过**（目标/范围/原始作答/位置/文件索引可读） | `f1-report.json` |
| LP-02 学习文件编辑与回写 | **通过**（Tutor 写文件→CLI 接收→再导出带出） | `../2026-11-07-09/`、`2-5-learning-files-and-handoff.md` |

## 未达标 / 未运行（不得计为通过）

1. **SYNC-06 真实调度触发**：上面已述，平台侧待查。
2. **真实 GitHub 远端发布**：只做只读 `git ls-remote`（120 heads, exit 0）；向所有者账号建仓/推送属外部动作，未执行。
3. **真实凭据缺失**：无私有远端凭据环境，仅由"推送被拒 → exit 4 partial"路径覆盖。

## 真实入口 vs 模拟

- 真实入口：CLI 子进程（含本轮硬杀）、真实 Windows 计划任务（安装/启停）、真实浏览器（Playwright，端口 3099）、1 次真实免费 LLM 调用。
- 模拟/注入：接收端 SQLite savepoint 与发布失败用 monkeypatch 注入（`test_file_publication_failure_…` 等），已在表中注明为单元级。
