# SYNC-04：进程级中断与重试（2026-11-08）

任务原文（`openspec/changes/expand-file-mediated-course-sync/tasks.md` §3.2、§2.4）要求「导出/提交/文件发布中断后重试；独立有效项继续，同一保留历史不重复」。上一轮（2026-11-08-p3）只做了进程内故障注入，**没有真实 kill**；本条补上。

## 怎么做的

夹具：`sync-04-kill-fixture.py`（原 `tmp/accept/p3_kill.py`，复用 `tmp/accept/p3_f1.py` 的 F1 造课：12 知识点 / 24 题 / 6 卡 / 6 关系 / 12 作答 / 4 经验 / 试卷与执行，另加 120 个学习文件把文件发布阶段拉长到可命中）。

每个边界都用**真子进程 + 硬杀**：`python -B -m workbench.cli.main course-sync …` 起子进程，`sleep(基线用时 × 比例)` 后 `Popen.kill()`（Windows 上是 TerminateProcess，**没有任何清理机会**），随后用同一命令重试到成功。每个"设备"用独立 `LESSONKIT_WB_HOME` 临时目录；全程不碰真实课程。

| 边界 | 杀点 | 重试结果 |
|---|---|---|
| 导出到包目录 | 基线 1.41s 的 50%（0.705s） | exit 0，1.4s，204 项资产 |
| 接收（收到空课程） | 基线 1.55s 的 30% / 60% / 90% | 三轮 exit 0 |

## 结果（`sync-04-kill-report.json`）

三轮接收杀点全部满足：

- `all_counts_equal = true`：12/24/6/6/12/4 各表计数与来源一致；
- `no_duplicate_attempts = true`：`problem_attempts` 12 行、`DISTINCT id` 12，无重复作答；
- `no_missing_or_extra_files = true`：`.lessonkit/**` 逐文件与来源一致（`course-sync/config.json` 是本机媒介配置、非资产，已从比对中排除）；
- `all_retries_succeeded = true`：三轮重试均 exit 0。

## 这轮测出的真缺陷（已修）

首轮 90% 杀点留下 `.lessonkit/learning/note-05.md.ixfg5cor.tmp`，且重试后**仍在**。

根因：`workbench/data/course_sync.py::_write_file` 用 `tempfile.mkstemp(prefix=<name>., suffix=.tmp)` 写临时文件再 `os.replace`；进程被硬杀时 `finally` 不执行，孤儿留在课程目录。而导出的课程文件扫描是 `folder.rglob("*")`（**不按扩展名过滤**，`course_sync.py` 的 learning/practice-sets 遍历），所以孤儿**会在下一次交换中被当成资产传播到其他设备**——不是无害残留。

修法：`_write_file` 写盘前清掉同名前缀的 `*.tmp` 兄弟（`iterdir` 判断，避免 glob 元字符歧义）。回归用例 `tests/workbench/test_course_sync_receive.py::test_publication_clears_a_temp_left_by_a_killed_writer`（38 passed）。修复后同一夹具三轮杀点全部无 extra file。

## 未覆盖

- 判分作业、Bridge 会话与 AI 调用链不在本条范围。
- 数据库级别只验证了"重试后一致"，没有逐事务检查 WAL/journals；SQLite 的崩溃恢复由其自身提供。
- 未做 Windows 之外的平台（本机 WSL 不可用）。
