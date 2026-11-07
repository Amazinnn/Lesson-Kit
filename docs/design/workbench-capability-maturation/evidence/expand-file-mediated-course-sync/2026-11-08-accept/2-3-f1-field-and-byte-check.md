# 2.3 F1 完整小课程：导出 → 接收的逐字段与字节核对（2026-11-08）

任务原文：

> 在 `workbench/data/course_sync.py` 复用现有查询导出完整 manifest、正文与附件，保存课程来源和记录来源映射。**F1 逐字段和字节核对**，再在 F2 计时。

本文件只回答 2.3 的核对部分；CLI 回执与退出码在 `2-7-cli-receipts.md`，F2 数值直接引用现成计时文件（本轮未重跑）。

## 夹具怎么造

复用 `tmp/accept/p3_f1.py` 的 `build_course` / `seed_f1` / `cli`：以 `exec` 加载该文件，`__name__` 不是 `"__main__"`，所以不会执行它自己的 `main()`；夹具内容一行未改写。驱动脚本是新增的 `tmp/accept/e2_f1_field_check.py`（只做核对，不改生产代码）。

| 资产类 | F1 规模 |
|---|---|
| 章节 / 知识点 | 3 章 / 12 个（正文含 `$P(A\mid B)$`） |
| 题目 | 24 道：每 3 道 1 道客观题（`single_choice` + `micro_quiz`，共 8 道）、每 4 道 1 道带小问（共 6 道）、前 10 道带引用图 |
| 卡片 / 知识关系 | 6 / 6 |
| 作答 | 12 份（`wrong`/`mastered` 交替，含原始作答文本与 `choices`） |
| 知识点经验 | 4 条 |
| Paper | 3 张（`ps-001..003`，共享题目），2 个未完成执行（含 2 条同卷/异卷草稿） |
| 学习文件 | 8 个 `.lessonkit/learning/note-*.md` |
| 目标 | `.lessonkit/goals.json` 2 条 |
| 引用图 | 10 张 `dmath/ch01/fig-*.png`（每张 70 B，内容互不相同） |
| 教材原件 | `textbook.pdf`，2,097,180 B |

运行方式：两台“设备”各自一个临时 `LESSONKIT_WB_HOME`；导出包用 `shutil.copytree` 复制后再接收（只走文件，不共享目录）。真实 `~/.lessonkit-workbench/workspaces.json`（22 个工作区，mtime 2026-11-04）全程未写。

F1 的两步走的是 `workbench.cli.course_sync.main()`（与安装入口同一函数，只是进程内调用）；真实 subprocess 的命令行回执见 `2-7-cli-receipts.md`。

| 步骤 | 调用 | exit | 顶层 status | 关键数字 |
|---|---|---|---|---|
| A 导出 | `course-sync dmath-a export --to <bundle>` | 0 | `success` | `assets 99`、`written 99`、`reused 0`、`manifest_changed true` |
| B 接收（包已复制） | `course-sync dmath-b receive --from <copied>` | 0 | `success` | `assets 99`、`applied 99`、`failed 0`、`conflicts 0`、`unchanged 0`、`base_size 99` |
| B 再导出 | `course-sync dmath-b export --to <bundle-b>` | 0 | `success` | 99 项，作为“接收端自己投影出来”的比较对象 |

## 核对方法、结果、差异数（逐类）

### 1. 交换投影逐字段（不是只数行数）

**方法**：双方各自 `export_course`，用 `read_exchange` 读回 manifest + envelope；按 identity 配对，把每个资产的 `kind` / `deleted` / `depends_on` / `content` 递归展开成叶子字段后逐值比较。文件资产的 `content.data`（base64）不按字符串比，换成 `path` + `encoding` + 字节长度 + sha256（字节另有专项，见第 3 类）。

**结果**：99 个 identity 对 99 个，展开 **1,704 个叶子字段**；`only_left` 与 `only_right` 均为空；**差异 0 条**。

覆盖的字段举例（说明覆盖面）：`problems` 27 列（`problem_text`、`solution`、`problem_type`、`source_kind`、`origin_kind`、`practice_modes`、`micro_quiz`、`parts`、`figure_paths`、`source_evidence`…）、`knowledge_points` 15 列、`problem_revisions`、`kp_experiences`、`paper_state` 的 item 级 `state`/`attempt_id`/`draft`/`draft_sequence`/`content_revision`、execution header 与 3 个 item。

### 2. 物理 SQLite 逐字段

**方法**：30 张受管表（不含 `course_sync_checkpoint` / `course_sync_units` 这两张本机账本）逐表比 `PRAGMA table_info` 的列名与顺序（schema 差异 0）；再逐行、逐列比值。接收端自己拥有的字段不比数值、只比身份（见下方“跳过字段”）。非空的 10 张表共 **72 行、1,106 个字段值**：

| 表 | 行 | 列 | 实比列 | 比较的字段值 |
|---|---|---|---|---|
| `problems` | 24 | 27 | 27 | 648 |
| `knowledge_points` | 12 | 15 | 15 | 180 |
| `problem_attempts` | 12 | 10 | 9 | 108 |
| `knowledge_relations` | 6 | 8 | 8 | 48 |
| `flash_cards` | 6 | 8 | 8 | 48 |
| `active_practice_items` | 3 | 9 | 9 | 27 |
| `kp_experiences` | 4 | 6 | 6 | 24 |
| `active_practice` | 1 | 13 | 13 | 13 |
| `paper_state` | 2 | 5 | 5 | 10 |
| `practice_execution_ids` | 2 | 1 | 0 | 0（只有设备本地 `id`，按身份比对） |
| 其余 20 张空表 | 0 | — | — | schema 相等、行数相等 |

**结果**：**0 条实质差异**。仅 1 条“派生/序列化”差异（`paper_state.checkpoint_json`，见差异清单第 2 条）。

跳过数值、改按身份核对的字段（共 9 个字段，均有明确 writer 语义）：

| 表 | 字段 | 为什么不比数值 |
|---|---|---|
| `problem_attempts` / `feedback_events` / `practice_runs` / `practice_execution_ids` / `content_mirror_log` / `question_progress` | `id` | 接收端自增主键；导出时 `id` 已替换为 `row/<table>/<installation>/[<源号>]` 身份 |
| `retired_paper_items` | `sequence` | 保留历史由接收端按 `(paper_id)` 续号（S011）；F1 无该表行 |
| `part_grading_jobs` | `conversation_id`、`turn_id` | 会话/轮次属于执行它的机器，接收端置空（F1 无该表行） |

对 6 张身份表，替代核对是“每条本地记录都能映射回发送端身份”：F1 实际有 14 条（12 份作答 + 2 个执行号），**14/14 命中**，无孤立身份。

### 3. 文件字节

**方法**：每个 `file` 资产比四跳字节 —— A 的资产字节（envelope 里的 base64 解码）、A 包内 `files/` 可读副本、B 工作区磁盘上的同路径文件、B 再导出包里的同名资产。比较长度、sha256，并在不等时给出首个差异偏移。

| 类别 | 文件数 | A 侧字节合计 | 差异 |
|---|---|---|---|
| 学习文件 `.lessonkit/learning/*.md` | 8 | 368 | 0 |
| 引用图 `.lessonkit/figures/**` | 10 | 700 | 0 |
| Paper 文件 `.lessonkit/practice-sets/*.json` | 3 | 1,635 | 0 |
| 目标 `.lessonkit/goals.json` | 1 | 213 | 0 |
| 教材原件 `textbook.pdf` | 1 | 2,097,180 | 0 |
| **合计** | **23** | **2,100,096** | **0** |

包内可读副本同样 23 对 23，路径与 sha256 全部一致。

**行尾专项**（避免 CRLF 干扰的实证）：

- F1 夹具用 `Path.write_text` 写学习文件，本机磁盘上是 CRLF；B 接收后**字节完全相同**（含 CRLF），说明传输不重写行尾。
- 另用 `open(..., newline="\n")` 写一个 39 B 的纯 LF 文件，再导出、再接收：源 sha256 `c070b22bff15f0af…`，接收端相同，未被改成 CRLF。

### 4. 引用图

**方法**：比对 `problems.figure_paths` 的逻辑路径列表（A/B 各 10 道题非空），并逐张比磁盘字节、检查接收端是否存在。

**结果**：10 道题的引用列表**逐项相同**；10 个逻辑引用全部在 B 落地；10/10 张图字节相同；缺失 0。**差异 0 条**。

### 5. 学习文件

8 个 `.md` 全部出现在 B 的 `.lessonkit/learning/`，内容字节与 A 一致（含第 3 类的四跳比对）；`goals.json` 的 2 条目标也逐字节一致。**差异 0 条**。

### 6. 来源映射（course origin / record origin）

| 项 | A | B | 判定 |
|---|---|---|---|
| `course.id` | `dmath` | `dmath` | 相同 |
| `course.origin` | `course-221b73f9-…` | `course-221b73f9-…` | **相同**：课程来源随包复制 |
| `installation origin` | `installation-af02a80c-…` | `installation-39e21b13-…` | **不同**：每台安装各自分配，未混用 |
| 记录身份映射 | — | 14 条（12 作答 + 2 执行号） | **14/14 映射回发送端身份**，例如 B 本地 `problem_attempts/[1]` → `row/problem_attempts/installation-af02a80c…/[10]` |
| 共同基线 `base` | 99 项 | 99 项 | identity 集合完全相同 |

说明：身份串把发送端安装来源和原记录号固化在 identity 里，接收端把本地自增号写进 `state.json` 的 `row_identities` 反向绑定；因此两台机器的 `1..12` 号即使顺序不同（本例 B 的 1 号对应 A 的 10 号）也不会被当成同一事实。**差异 0 条**。

### 7. 差异清单（逐条，区分预期/缺陷）

| # | 差异 | 条数 | 判定 | 依据 |
|---|---|---|---|---|
| 1 | 身份表 `id` 数值不同（`problem_attempts` 12 行、`practice_execution_ids` 2 行） | 14 行 | **预期** | 接收端自增；投影中 `id` 已替换为身份，第 1 类投影比较为 0 差异；第 6 类 14/14 映射成功 |
| 2 | `paper_state.checkpoint_json` 的 `locked` 字段与键序 | 1 行（`ps-002`） | **预期** | `workbench/data/course_sync.py:501` 在投影时 `item.pop("locked")`；`workbench/data/active_practice.py:203` / `:771` 在读取时按 `state != "pending"` 重算。解析后除 `locked` 外完全相同，读侧取值一致 |
| 3 | `manifest.origin` / `manifest.export_id` | 2 个元数据 | **预期** | 分别是“本安装来源”和“本次导出身份”，不是课程资产；`course` 与 99 项资产不受影响 |

**实质差异合计：0 条**（字段 0、文件字节 0、引用图 0、学习文件 0、来源映射 0）。

### 8. 负向自检（证明比较器不是空转）

在接收端 B 上注入两处真实差异，再用同一套比较器比一次：

- 数据库：`UPDATE problems SET problem_text='自检注入的差异文本' WHERE problem_id='dmath-ch01-prob-001'`；
- 文件：给 `.lessonkit/learning/note-02.md` 追加 9 字节。

重新导出 B 后，比较器检出 **3 条投影差异**：1 条 `row/problems/["dmath-ch01-prob-001"].content.row.problem_text`，2 条同一文件资产的 `bytes_length` / `bytes_sha256`；文件四跳比较另检出 2 个跳变（`received_disk`、`re_export`），且 `only_left` / `only_right` 仍为空。说明“0 差异”来自真实一致，而不是比较函数没有生效。

## F2 计时（引用现成数值）

来源 `tmp/accept/f2-timing.json`（生成脚本 `tmp/agent-runs/bench_f2.py`；`timed()` 在计时循环前先调用一次 `action()`，即**预热 1 次 + 每阶段 20 次**）。

夹具：20 章、1,000 知识点、10,000 题、100 Paper、10,000 份作答、30 个并存未完成执行、500 个学习文件、100 MiB 附件；文本含中文、行内/块公式、表格与特殊字符。

| 阶段 | p50 | p95 | max | 门槛（SYNC-02） | 余量 |
|---|---|---|---|---|---|
| 导出 | 16.469 s | **18.232 s** | 18.414 s | p95 ≤ 30 s | 60.8% |
| 接收 | 9.210 s | **9.963 s** | 11.161 s | p95 ≤ 30 s | 33.2% |
| 无变化检查 | 2.936 s | **3.187 s** | 3.291 s | p95 ≤ 5 s | 63.7% |

终态：`changes 0`、`outgoing 0`、`errors []`（重复接收不新增、不残留待办）。

两点如实说明：

- “接收”计时把 `inspect_exchange` 与 `apply_exchange` 都算在计时 lambda 内（`bench_f2.py`），比只计 apply 更严格，因此 9.963 s 不是纯写入时间。
- 这是同机并发环境下的 20 次分布，不是跨机基准；数值与 P3 evidence 一致，本轮未重跑。

## 结论与限制

- 2.3 的 F1 逐字段 + 字节要求**通过**：99 项资产、1,704 个投影字段、1,106 个 SQLite 字段值、23 个文件 2,100,096 B、10 张引用图、14 条记录身份，**实质差异 0 条**；3 条差异全部是设备本地号/派生字段/导出元数据，已逐条给出依据。
- 未在本轮覆盖（不得据此判通过）：双侧改同一题与删除传播（F3 证据已覆盖，见 `../2026-11-08-p3/f3-report.json`）、Git 通道的字节保真（见 `2-7-cli-receipts.md` 的行尾发现）、format_version 2 大包（F2 计时阶段覆盖）。
- 生产代码未改，未 commit；临时脚本 `tmp/accept/e2_f1_field_check.py`，原始结果 `tmp/accept/e2-f1-field-check.json`。
