# 2.7 CLI 注册与回执契约实测（2026-11-08）

任务原文：

> 新增 `workbench/cli/course_sync.py` 并在 `main.py`/`surface.py` 注册 export/receive/check/sync/status/schedule。按 design 的 JSON/status/退出码契约测试一次导出、一次接收、无手改版本的单侧更新。

本文件只记录 2.7 的 CLI 侧：注册、JSON 字段、顶层 `status`、退出码、`local`/`remote` 分离。数据正确性在 `2-3-f1-field-and-byte-check.md`。

## 注册

| 检查 | 结果 |
|---|---|
| `workbench/cli/main.py` | `("course-sync", course_sync)` 进入子命令表（`main.py:967`），解析器由 `course_sync.build_parser()` 提供 |
| `workbench/surface.py` | `"course-sync": (HUMAN, "whole-course files, Git transport and the hourly task")`（`surface.py:196`） |
| `lesson-kit course-sync --help` | exit 0；位置参数列出 `{export,receive,check,sync,status,schedule}` |
| 安装入口 | `D:\Python\Scripts\lesson-kit`（`pyproject.toml` 的 `workbench.cli.entry:lesson_kit_main`），`workbench.__file__` 指向本 worktree |

实测脚本 `tmp/accept/e2_cli_receipts.py`：**每条命令都是真实 subprocess**（installed `lesson-kit`，不是进程内函数调用），每台“设备”一个临时 `LESSONKIT_WB_HOME`。真实 `~/.lessonkit-workbench/workspaces.json` 有 22 个工作区，mtime 仍为 2026-11-04（全程未写）。原始结果 `tmp/accept/e2-cli-receipts.json`。

夹具用 `tmp/accept/p3_f1.py` 的 `build_course`（只种数据库与文件，不含 Paper/执行，所以是 84 项资产；完整 F1 是 99 项）。

## 20 条真实命令与回执

| # | 命令（`lesson-kit course-sync …`） | exit | 顶层 status | 关键回执 |
|---|---|---|---|---|
| 1 | `dmath-a export --to <bundle> --json-output` | **0** | `success` | `assets 84`、`written 84`、`reused 0`、`manifest_changed true` |
| 2 | `dmath-b receive --from <copied> --json-output` | **0** | `success` | `applied 84`、`failed []`、`conflicts []`、`base_size 84` |
| 3 | `dmath-a export --to <bundle-2>`（单侧更新后） | 0 | `success` | `assets 85` |
| 4 | `dmath-b receive --from <bundle-2>` | **0** | `success` | `applied 2`、`unchanged 83` |
| 5 | `dmath-a export --to <bundle-3>` | 0 | `success` | `assets 86` |
| 6 | `dmath-b check --from <bundle-3> --json-output` | **0** | `success` | `changes 2`、`conflicts []` |
| 7 | `dmath-a export --to <bundle-4>`（冲突前） | 0 | `success` | `assets 87` |
| 8 | `dmath-b check --from <bundle-4>` | **3** | `conflict` | `conflicts [row/problems/["dmath-ch01-prob-004"]]` |
| 9 | `dmath-b receive --from <bundle-4>` | **3** | `conflict` | `applied 2`（独立单元完成）、`notification.notified true` |
| 10 | `dmath-b receive --from <bundle-4> --keep incoming` | **0** | `success` | `applied 1`；B 侧题干变为 `A 版本` |
| 11 | `dmath-a export --json-output`（缺 `--to`） | **2** | `failed` | `errors: ["--to is required"]` |
| 12 | `no-such-course export --to …` | **2** | `failed` | `errors: ["unknown workspace: no-such-course\nregistered workspaces: dmath-a"]` |
| 13 | `dmath-b receive --from <不存在的包>` | **2** | `failed` | `errors: ["[Errno 2] No such file or directory: '…\\manifest.json'"]` |
| 14 | `schedule`（无动作） | **2** | `failed` | `errors: ["schedule needs install, enable, disable or remove"]` |
| 15 | `dmath-a sync --repo <bare> --path sync` | **0** | `success` | `local.receive` 空、`local.export.assets 87`、`remote.status published` |
| 16 | 同一命令再跑（无变化） | **0** | `success` | `local.export.written 0`、`manifest_changed false`、`remote.status unchanged`、`changed_paths []` |
| 17 | 同一命令（远端 pre-receive 拒绝推送） | **4** | `partial` | `local.export.status success`、`remote.status failed` + 原始 reason |
| 18 | 移除 hook 后再跑 | **0** | `success` | 把 #17 的本地提交推上去，`changed_paths []` |
| 19 | `--all-configured sync`（隔离 home） | **0** | `success` | `courses {"dmath-a": 0}`、`failures []` |
| 20 | `dmath-a status` | **0** | 无（查询） | `state`、`media`、`last_receipt` |

三条必跑命令的真实输出（`--json-output`，节选）：

```text
$ lesson-kit course-sync dmath-a export --to <bundle> --json-output
{
  "status": "success",
  "course": {"id": "dmath", "origin": "course-0a3668d4-9639-4f0a-a2cd-9edb502bc79a"},
  "origin": "installation-c71f2364-38b3-462b-bfa1-835656c99155",
  "export_id": "export-d9781c79-cd5a-45c5-94b8-043e679f1623",
  "assets": 84, "written": 84, "reused": 0, "manifest_changed": true,
  "cleanup_errors": [], "destination": "…\\bundle",
  "local": {"exported": true}, "remote": null
}
exit=0
```

```text
$ lesson-kit course-sync dmath-b receive --from <copied> --json-output
{
  "status": "success",
  "course": {"id": "dmath", "origin": "course-0a3668d4-9639-4f0a-a2cd-9edb502bc79a"},
  "assets": 84, "changes": [84 项], "outgoing": [], "conflicts": [], "unchanged": 0,
  "errors": [], "operation": "receive-…", "applied": [84 项], "kept": [],
  "failed": [], "base_size": 84, "local": {"applied": 84}, "remote": null
}
exit=0
```

```text
$ lesson-kit data dmath-a update problem dmath-ch01-prob-002 --input <payload> --json
exit=0        # 正常写入口（content.update，同时写 problem_revisions），不是手改包内版本

$ lesson-kit course-sync dmath-a export --to <bundle-2> --json-output     # exit=0
$ lesson-kit course-sync dmath-b receive --from <bundle-2> --json-output
{
  "status": "success",
  "changes": ["row/problem_revisions/[\"dmath-ch01-prob-002\"]",
              "row/problems/[\"dmath-ch01-prob-002\"]"],
  "applied": ["row/problem_revisions/[\"dmath-ch01-prob-002\"]",
              "row/problems/[\"dmath-ch01-prob-002\"]"],
  "unchanged": 83, "conflicts": [], "failed": [],
  "local": {"applied": 2}, "remote": null
}
exit=0
```

B 侧落库核对：`problem_text = 单侧更新：A 的正常写入`，`problem_revisions` 新增 1 行。

默认（不加 `--json-output`）是单行人类摘要，实测：`success: 88 项资产 → …\human-out`（1 行，exit 0）。

## JSON 字段契约

| design 要求 | export | receive | check | sync | status | schedule（成功路径） |
|---|---|---|---|---|---|---|
| 顶层 `status` ∈ success/partial/conflict/failed | ✅ | ✅ | ✅ | ✅ | ❌ 无该字段 | ✅（代码结构；本轮未实跑） |
| `local` | ✅ `{exported:true}` | ✅ `{applied:N}` | ❌ | ✅ `{receive,export}` | ❌ | ❌ |
| `remote` | ✅ `null` | ✅ `null` | ❌ | ✅ `{status,commit,reason,local_commit,changed_paths}` | ❌ | ❌ |
| 课程来源 | ✅ `course{id,origin}` + `origin` | ✅ `course{id,origin}` | ✅ | ✅ `course{id}` | ✅ `course.id` + `state.course_origin` | ✅ `media` |
| 资产数 | ✅ `assets` | ✅ `assets` | ✅ `assets` | `local.export.assets` | `state.base_size` | ❌ |
| 操作身份 | ✅ `export_id` | ✅ `operation` | ❌ | ✅ `operation` | 回看 `last_receipt` | ❌ |
| 逐项变化 | `written/reused/manifest_changed/cleanup_errors` | `changes/applied/kept/failed/conflicts/outgoing/unchanged` | 同 receive | `local.receive` + `remote.changed_paths` | 回看 `last_receipt` | ❌ |

20 条命令的回执字段全体命中（脚本逐条检查 required fields，`missing_receipt_fields` 全为空；退出码 2 的 4 条按统一错误回执 `{status, errors}` 检查）。

契约观察（登记，不判缺陷、不改代码）：

- design 的“统一 JSON 回执，顶层 status + local/remote”落在**操作类**子命令（export/receive/check/sync）上完整成立；`status` 是状态查询（无顶层 `status`、无 `local`/`remote`，字段为 `course/state/media/last_receipt`），`schedule` 是任务管理回执（`status/action/task/command/runtime/media/output`，无 `local`/`remote`）。现行 spec 未逐字段规定这两个查询/管理输出的结构，建议后续 OpenSpec 明确，避免“统一回执”被误读为所有子命令同构。
- 退出码 2 的错误路径统一输出 `{status: "failed", errors: [原文]}`；`check` 与 `receive` 的 inspection 回执不含 `operation`/`local`/`remote`（只读、无操作身份）。

持久回执：`.lessonkit/course-sync/last-receipt.json` 在回执外多写 `exit_code`，与进程退出码一致（A：`exit_code 0` / `sync-…`；B：`exit_code 0` / `receive-…`）；每课程只保留最新一份，没有历史目录。

## 退出码四档

| 档位 | 实测条数 | 样本 |
|---|---|---|
| 0 完整成功 | 13 | export、receive、单侧更新接收、check、sync published/unchanged、`--all-configured`、status |
| 2 输入或格式错误 | 4 | 缺 `--to`、未知工作区、不存在的包、`schedule` 无动作 |
| 3 待选侧 | 2 | `check` 与 `receive` 遇到同一题的双侧修改 |
| 4 部分完成或传输失败 | 1 | `sync` 的 push 被 pre-receive 拒绝（`partial`） |

`status` → 退出码的映射在 `workbench/cli/course_sync.py:252`（`_exit_code`）与 `:459`（`_sync_exit`）；错误路径固定 2/4（`:87-92`）。20 条命令中没有出现“status 与退出码不一致”。

未验到的部分（不得勾成通过）：

- **混合优先级 2 > 3 > 4**：代码在 `_run_every_course`（`course_sync.py:589`）按 2→3→4 聚合，但本轮 `--all-configured` 只有 1 门配置课程，未构造“一门 2、一门 3/4”的混合集；现有单元测试 `test_all_configured_aggregates_each_course_exit_code` 也只覆盖“跳过未配置课程”。
- **receive 自身的 partial（exit 4）**：本轮 exit 4 只来自 sync 传输失败；没有构造发布失败/写入失败导致的 receive partial。

## `local` / `remote` 分开报告

- 文件通道：`export` / `receive` 的 `remote` 是 `null`（没有远端），`local` 分别给 `exported` / `applied` 数。
- Git 通道：`local.receive`（有无入站、逐项结果）与 `local.export`（`status/assets/written/reused/manifest_changed/cleanup_errors`）分开；`remote` 独立给 `status/commit/reason/local_commit/changed_paths`。
- 拒绝推送实例（#17）：`status: partial`、exit 4，但 `local.export.status: success`、`remote.status: failed`，reason 是原始 `remote rejected … pre-receive hook declined`；本地领先远端 1 个提交（`git rev-list --count origin/main..HEAD = 1`）。移除 hook 后 #18 把该提交推上去（`published`，`changed_paths []`）——既不冒充远端成功，也不丢本地提交。

## 单侧更新与冲突选侧

- **无手改版本的单侧更新**：改动经 `lesson-kit data … update problem`（`content.update` → `plan_problem_update`，同时写 `problem_revisions`）产生；导出/接收后 `applied` 精确列出 problem 与 revision 两个 identity，B 侧题干与 revision 行都到位（见上文）。
- **真实冲突**：双侧改同一题后，`check` 与 `receive` 都是 exit 3、`status conflict`、`conflicts` 只列 `row/problems/["dmath-ch01-prob-004"]`；`receive` 仍完成 2 个独立单元（上一轮遗留的单侧更新），并写 `notification: {notified: true, identities: [...]}`。
- `--keep incoming` 只作用于真实冲突：解析后 exit 0、`applied 1`、B 侧题干变为 `A 版本`；同一冲突的重复通知去重证据见 `../2026-11-08-p3/task-report.json`（第二次 `notification` 为 null）。

## `check` 只读

`check` 前后对 B 的整库（全部表逐行）与工作区文件（含 2 MiB 教材、图、学习文件）做 sha256 指纹：**完全相同**；它只替换自己的 `last-receipt.json`（回执文件，不是课程资产，`course-sync` 目录本就不参与导出）。`changes` 逐项列出待接收的 2 个 identity。

## `--all-configured sync`

- 没有跳过，但在**隔离 home** 中运行：脚本先断言该 home 的注册表只有 `["dmath-a"]`，再执行；回执 `{status: success, courses: {"dmath-a": 0}, failures: []}`，exit 0。
- 未配置 media 的课程被跳过（同一脚本里的 `dmath-b` 不在该 home）；真实 22 个工作区没有参与。

## 环境发现：Git 行尾归一会影响字节保真（记录，不判产品缺陷）

本机 system Git 配置 `core.autocrlf=true`。首轮实测（结果保留在 `tmp/accept/e2-cli-receipts-autocrlf-true.json`）中：

- F1 夹具用 `Path.write_text` 写出的学习文件在磁盘上是 CRLF；
- push 时 Git 把文本归一为 LF 存进对象库；下一次 `sync` 从远端读回 LF，与本地 CRLF 逐字节不同 → 8 个 learning 文件被当作真实变化应用，`sync-unchanged` 因此产生第二个提交；
- 之后本地已是 LF，再下一次 sync 才回到 0 变化。

同一脚本把测试仓库设为 `core.autocrlf=false`（仓库级，`core.safecrlf=false`）后：`sync-unchanged` = `remote.status "unchanged"`、`changed_paths []`、`local.export.written 0`，与 p3 的 SYNC-05 结论一致。文件通道不受影响（`2-3` 的 23 个文件四跳字节全同）。

判定：这是“使用系统 git”这一设计选择带来的环境约束，不是 fallback，也不是本轮代码缺陷；但若要求 Git 通道也保持字节保真，需在 OpenSpec/spec 里明确“交换仓库必须禁用行尾归一”，且 `handoff.md`/Markdown 的 CRLF 来源应统一（本轮夹具用默认 newline，真实写入端也需确认）。

## 未验证清单

- `schedule install|enable|disable|remove` 的真实系统任务操作：本轮只验了 `course-sync schedule`（无动作）exit 2 与 help 注册；真实安装/停用/启用/删除的 returncode 0 证据在 `../2026-11-08-p3/task-report.json`（避免再次操作真实任务计划程序，也未触碰本机任务）。
- 真实私有远端的凭据缺失（仅有本地 bare remote 的 push 拒绝）。
- 多课程混合退出码优先级、receive 自身 partial（见上）。
- 生产代码未改，未 commit；证据脚本 `tmp/accept/e2_cli_receipts.py`，原始结果 `tmp/accept/e2-cli-receipts.json`。
