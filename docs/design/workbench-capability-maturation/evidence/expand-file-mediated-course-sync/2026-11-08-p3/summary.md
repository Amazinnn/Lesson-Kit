# P3 完整同步验收（2026-11-08）

按 `NEXT-EXECUTION-PLAN-2026-11-07.md` 的 P3 执行。所有夹具在临时目录，未触碰任何真实课程；
本机 `lesson-kit` 安装仍指向主检出，未切换。

## 结果总表

| 编号 | 夹具/场景 | 结果 | 证据 |
|---|---|---|---|
| SYNC-01 | F1 完整小课程 A 导出 → 只复制包 → 新 B 一次接收 | **通过**：99 项资产，8 张表计数与源一致，8 个学习文件/目标/教材原件/引用图全部落地 | `f1-report.json` |
| SYNC-02 | F2 全量，预热 1 次后各 20 次 | **通过**：导出 p50 16.47s / p95 **18.23s**；无变化检查 p50 2.94s / p95 **3.19s**；接收 p50 9.21s / p95 **9.96s**；终态 `changes=0 errors=[]` | `f2-timing.json` |
| SYNC-03 / FS-04 / FS-10 | 双侧同题修改 | **通过**：先 `conflict` 零写入，批量选 incoming 后落到「左边版本」 | `f3-report.json` |
| SYNC-03 / FS-09 | 两侧各新增作答再往返两次 | **通过**：两份作答都在，重复接收 `applied=[]` | 同上 |
| SYNC-03 / FS-11 | 一侧删除、另一侧修改 | **通过**：保留真实冲突，`applied=0 failed=0`，定时不自动选侧 | 同上 |
| SYNC-03 / FS-02 | 文件侧新增题目与学习文件 | **通过**：2 项资产被接收 | `f1-report.json` |
| SYNC-03 / FS-05 | 仅移走一个 Paper 文件 | **通过（如实阻断）**：导出 exit 2「managed assets are missing without explicit deletion」，Paper 行保留，未写包 | 同上 |
| SYNC-03 / FS-06 | 删除两卷共有的一题并同步 | **通过**：保留历史 1 行，B 侧该题从执行移除、`deleted_at` 已到位 | 同上 |
| SYNC-03 / FS-07 | 删除仍有题目归属的知识点 | **通过**：知识点与关系清空，题目保留 | 同上 |
| SYNC-08 | F4 真实旧池（2026-08-26） | **通过**：导出 347 项、接收 347 项 0 失败，28/303/3/6/2/1 与源一致，题干逐字保留，目标库无 `topic_label`；只新增两张交换账本表 | `f4-report.json` |
| SYNC-08 | 同名不同来源 | **通过**：`association_required=true`，未给 associate 时拒绝（exit 2） | `f3-report.json` |
| SYNC-08 | 未知交换格式 / 未知表 / 缺引用图 | **通过**：三者都如实拒绝，不静默忽略 | 同上 |
| SYNC-05 | 专用远端（本地 bare，真实 Git 协议） | **通过**：首次发布、无变化不产提交、FF 吸收远端新提交、**push 被拒 → exit 4 partial 且保留本地提交**、他源包 → exit 2 且不改本地/远端、只 stage 包内路径 | `git-report.json` |
| SYNC-06 | 真实 Windows 计划任务 | **部分**：安装/停用（XML `<Enabled>false</Enabled>`）/启用/删除全部成功，任务动作（同一 wrapper）手动执行返回 `success, courses:{task-course:0}` 并写出回执；**但 `schtasks /Run` 与 `Start-ScheduledTask` 触发后 180 秒内没有产生回执**，真实调度触发未验证。冲突通知：首次 `notified=true`，同一冲突第二次 `notification=null`（去重） | `task-report.json` |
| SYNC-07 / LP-01 | 全新 B 读交接 | **通过**：目标、课程范围、原始作答、教学位置、学习文件索引都可读 | `f1-report.json` |
| FS-08 | 恢复被删题目 | **通过（后续补做）**：`data restore problem <id>` 恢复内容与历史，原试卷不自动加回；用例 `test_restoring_an_archived_question_keeps_it_out_of_its_papers` | 见 2026-11-08-p4 与本文件末尾 |
| RELEASE-01 | 全仓检查 + 真实浏览器 | **通过**：`pytest tests -q` 1,554 passed、compileall、live specs strict 21/21、`guard extract-problems` PASS；隔离服务（端口 3099，`--project-root` 指本 worktree）实跑浏览器：偏好基线为空 → PATCH 后重载 → `lkCoursePreferences.values()` 生效、镜像写入、`data-show-rating=off`；新卷 ps-003 开始页显示收到的 `on_submit`；进行中的 ps-001 显示「继续练习」且揭晓时机冻结为不可改 | 本节与 Playwright 会话 |

## 本轮暴露并修掉的两个真实缺陷

1. **删除题目后接收端执行体损坏**：A 删除题目后导出，B 侧写入该执行时触发 `UNIQUE constraint failed: active_practice_items.item_type, item_id, direction`——头部只报"哪些位置变了"，接收端按位置合并留下了发送端已删除的项。改为**由执行头声明自己的题目集合**（`content.items`），接收端按该集合取数、丢弃未声明的本地项。旧包没有该字段时回退到按位置合并。
2. **删除题目不保留历史**：`content.delete` 走 `remove_question` 时只清空项，没有写 `retired_paper_items`。现在删除同样写入保留历史（理由 `deleted`），与改名单路径一致。

## 未验证（不得勾选）

- FS-08 恢复（依赖 adaptive change 3.2）。
- 真实 GitHub 远端发布：仅做了只读连通性探测（`git ls-remote` 120 heads，exit 0）；向所有者账号发布属外部动作，未执行。
- 计划任务的**调度触发**（安装/启停/删除已验证，`/Run` 与 `Start-ScheduledTask` 后未见回执）。
- SYNC-04 的进程级中断：仍由自动化故障注入用例覆盖，本轮未额外做进程 kill。
- 安装身份切换（P4）。

## 后续补做（同日）

- FS-08 恢复已实现：`content.restore` + `data restore problem <id>`，重复恢复报 `already_current` 零写入；原卷与执行都不自动加回，移除事实留在 `retired_paper_items`。
- P4 安装身份：editable 已切到本 worktree（`workbench.__file__` 指向 worktree，`lesson-kit --help` 含 `course-sync`）；默认守护进程 `source_root` 仍为主检出，`--project-root` 下为 worktree。证据见 `2026-11-08-p4/`。
