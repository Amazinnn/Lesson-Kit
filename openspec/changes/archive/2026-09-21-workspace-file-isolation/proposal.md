# workspace-file-isolation 提案

## Why

所有者定下本项目的硬性局限：**一个工作区的文件不与任何其他工作区的文件互通**
（"每个工作区（路径）的文件都是不能够在该项目的功能上和其他工作区的文件互通的！
… 一个工作区只能够有一个工作区的文件！"）。理由不是洁癖，而是防止不同学科串味：
`dmath` 的题、`c01` 的图、别的课的会话镜像一旦能互相进入，学习记录就失去意义。
接入的 Agent 本身不受约束（它可以读写任何路径），约束的是**本项目的功能**。

走查逐条核对后发现这条不变量目前并不成立，其中两条是真会丢数据的活口子：

1. **会话 id 可穿越**：`/api/w/{name}/ai/sessions/{conversation_id}` 的段先按 `/`
   切分再 `unquote`，所以 `%2F..%2F..%2F` 能作为"一个段"通过路由，最终拼进
   `.lessonkit/jobs/<id>`——`DELETE` 会对工作区外的目录执行 `rmtree`。
2. **静默挑第一个工作区**：不带名字的 CLI 命令（`weak/due/pull/practice/feedback/
   schedule/goals/data/open`）在注册了多个工作区时直接用 `workspaces[0]`，Agent 的
   写命令会落到另一个学科的工作区里（且没有任何提示）。
3. **池选择会挑到备份**：`find_pool()` 取 `pool/*.db` 排序后的第一个。本仓库
   `pool/` 里同时有 `dmath-pre-readiness-2026-08-26.db` 与 `dmath.db`，
   `find_pool` 返回的是**前者**——零参 `init` 会注册错库、`--course` 也变成
   `dmath-pre-readiness-2026-08-26`。同一文件夹放两份池时也没有任何提示。
4. **章值不经校验**：`init --chapter` / `use <course> <chapter>` 的章原样入注册表，
   而它被拼进 `f"{course}-{chapter}"` 前缀（SQL `LIKE`，`%`/`_` 是通配符）与图谱
   工件路径。
5. **入池门禁不认课程**：微题/闪卡的 id 只校验形状 `<course>-<chapter>-mq-NNN`，
   不校验 course 是否等于本工作区的课程；figure-patch 的 `course`/`chapter` 直接
   拼进 `.lessonkit/figures/<course>/<chapter>`（`../` 会写到工作区外）。
6. **给 Agent 的示例 id 硬编码 `dmath-ch06-fc-901`**：在别的学科工作区里，提示词
   仍在教 Agent 用 `dmath-ch06-*`——串味的最直接来源。
7. 注册表可写坏：`db` 指到工作区外、两个工作区共用一个文件夹/一个库、同名注册会
   **静默覆盖**掉原条目。

## What Changes

- 新增**包含性不变量**：工作区操作构造的每个文件路径都必须落在该工作区文件夹内；
  来自客户端的 id（会话、轮次、附图逻辑路径、图谱工件）先按"裸名字"校验，越界即
  报错且不写不删。
- `conversations`：`conv-NNN` / `turn-NNN` 形状校验（`%2F` 穿越成为历史）。
- `_resolve_name`：注册了多个工作区时**拒绝猜**，报错给出用位置名 `name` 的可粘贴
  完整命令（Agent 面命令本就接受位置名）。
- `registry`：注册时校验池在工作区内、路径与池都不重复、同名不同路径拒绝覆盖；
  池候选排除 ingest 备份（`*.db.ingest-backup`、`pool/backups/`）；同一文件夹有多份
  池且没有一份叫 `--course` 时拒绝并列出候选。
- 章标识符校验（`init --chapter` / `use`）：小写 ASCII slug，与课程同一规则。
- 入池门禁认课程：微题/闪卡 manifest 的 id 必须带本工作区课程前缀，figure-patch 的
  `course` 必须是本工作区的课程、`chapter` 必须是合法章标识。
- 会话提示词的示例 id 用上下文里的真实课程/章，不再硬编码 `dmath-ch06`。
- 文档：GLOSSARY 补「工作区」条目的包含性口气，PRODUCT-MANUAL 写清"一个工作区 =
  一个学科"的局限与切换方式；ACTION-GRAPH 与 L2 留痕。

## Capabilities

### Modified Capabilities

- `review-workbench`：新增 `Workspace file containment`（路径包含 + id 形状校验）；
  `Workspace registry` 增"一区一池"的注册校验；`Unified CLI entry point` 增"多工作区
  时默认选择必须拒绝猜"。
- `workbench-content-governance`：新增 `Ingest stays inside one course`（id 前缀、
  figure-patch 的课程与章）。
- `ai-teacher-bridge`：`Check ingest action` 的示例 id 改用真实课程/章。
- `workbench-ui`：`Local deletion is bounded` 明确只删本工作区的会话目录，坏 id 拒绝。

## Impact

- 代码：`workbench/bridge/conversations.py`（id 校验、`_prompt` 示例）、
  `workbench/registry.py`（注册校验、池候选、路径包含）、`workbench/cli/main.py`
  （`_resolve_name` 拒绝猜、章校验、`--chapter` 帮助文案）、
  `workbench/ingest/__init__.py`（id 前缀门禁、figure-patch 包含与课程校验）、
  `workbench/server/app.py`（会话路由段校验的兜底，若需要）。
- 测试：新增双学科工作区隔离用例（各自池、各自会话、跨区 id 被拒）；会话穿越
  回归用例；注册校验用例（备份不被采纳、多池拒绝、重名拒绝、db 越界拒绝）；
  `_resolve_name` 歧义用例；章校验用例；门禁课程前缀用例。
- 学习数据零变更：既有注册表条目、`dmath` 池内容、id 契约都不动；备份文件仍在原处
  （只是不再被当成主库采纳）。
