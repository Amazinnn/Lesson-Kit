# 3.1 职责契约同步核对（2026-11-08）

任务原文：> 同步被命中的 GLOSSARY、DATA_MODEL、FILE_CONTRACT、ARCHITECTURE、PRODUCT-MANUAL、ACTION-GRAPH、surface、提示词及 agent_contracts，未受影响文件不机械改写。

## 实际改动（`git diff --stat c5a9c642..HEAD`）

| 文件 | 行数 | 同步了什么 |
|---|---|---|
| `FILE_CONTRACT.md` | +85/−4 | `files/` 明文副本、manifest 分组包 v2、回执与退出码、`retired_paper_items` 同步语义、显示快照不重绑、归档与恢复语义 |
| `docs/ACTION-GRAPH.md` | +10 | 学习偏好改级（3 条）、课程交换 CLI（L2 两条命令 / L3 两条动作）、运行时来源（2026-11-08） |
| `docs/ARCHITECTURE.md` | +10/−1 | Domain 的 `course_sync.py`、Bridge 的 `git_sync.py`、WP01 接收持久化边界（checkpoint / sidecar / 发布意图 / 任务 XML 隔离） |
| `docs/DATA_MODEL.md` | +35/−1 | `retired_paper_items` 字段语义与 writer/consumer、改名单协调规则、`course_sync_checkpoint` 等运行表 |
| `docs/GLOSSARY.md` | +14/−2 | 「已确认课程学习偏好」「运行时来源」等新名词（先定义后使用） |
| `docs/PRODUCT-MANUAL.md` | +22/−1 | 课程交换章节（文件、Git、每小时同步）、设置页偏好说明、稳定运行时默认来源 |
| `docs/action-graph/L2-interfaces.md` | +7 | `course-sync` 命令、偏好两条路由、`/api/runtime` 字段 |
| `docs/action-graph/L3-actions.md` | +3 | 修改学习偏好、课程交换两个动作 |

## 明确未改（不是遗漏）

| 资产 | 判断 |
|---|---|
| `skills/**`（技能提示词） | 无课程交换语义；命令注册在 CLI（`workbench/cli/main.py:967` 的 `("course-sync", course_sync)`），不是提示词列表。搜 `course-sync` 在 `skills/` 命中 0 |
| `workbench/agent_contracts.py` / Agent 契约注入文本 | 同上：本次没有改变 Agent 的写入契约或动作白名单语义（偏好是课程数据，但写入走服务端 HTTP，不是 Agent 工具） |
| `openspec/specs/*/spec.md` | 按 OpenSpec 流程由 delta 承载，归档时并入；本轮只核对（见 `1-2-delta-check.md`） |
| `docs/DATA_MODEL.md` 的池表字段 | 本包不新增学习事实表；`course_sync_checkpoint` 属运行检查点，已在 DATA_MODEL 的运行时段落登记 |

## 本轮新增/变更的契约（随本批提交）

- `workbench/data/course_sync.py::_write_file` 在发布前清理同名 `*.tmp` 孤儿——行为属于「发布中断可重试」的实现细节，不改变 manifest/回执契约，故不改 FILE_CONTRACT；理由与证据见 `3-2-sync-04-process-kill.md`。
