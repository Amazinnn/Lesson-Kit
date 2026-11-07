# RELEASE-02：安装身份、副本升级与备份恢复（未切换）

## 实际安装身份

| 项 | 值 |
|---|---|
| 发行版 | `lesson-kit 0.1.0`，**editable** 安装 |
| 源码根 | `D:\Projects\Academic Workflow\lesson-kit` |
| 该检出的分支 | `main @ c5a9c642` |
| Python | 3.14.3 |
| 运行时 | **守护进程未运行**，因此没有 `/api/runtime` 的 `source_root` 可读 |

结论：本机 `lesson-kit` 命令服务的是 **main**，不是本分支。本分支从未安装、未切换，活跃课程未改动。这与交接文档一致（不自动合并、不启动主服务、不动活跃课程）。

## 副本升级（真实主池的只读副本）

- 源：`pool/dmath.db`（482 行，30 张表）。
- `pool/scripts/migrate-progress.py --db <副本>` → returncode 0，新增 `course_sync_checkpoint`、`course_sync_units` 两张表。
- 升级后：**所有原有表行数不变**（合计 482），`problems` 没有新增列（主池已是新 schema）。
- 源文件哈希前后一致（`source_unchanged: true`）。

## 备份恢复

- 升级前的字节备份可完整还原：还原副本与备份**逐字节相同**，行数与原始一致。

## 未执行

- **没有切换安装身份**：分支未合并，切换属发布动作，不在本轮范围。
- 没有启动运行时，因此没有核对 `/api/runtime` 的 `source_root`、worker pid、静态资源版本。
- 没有在已安装命令行下做新入口验收（`lesson-kit course-sync` 指向 main，main 上还没有本分支的实现）。
- 未覆盖多课程注册表的整体备份、旧池 `--force` 重建、真实崩溃恢复。

明细：`release-02-identity-and-restore.json`。
