# design — workspace-file-isolation

## 决策 1：包含性校验放在"拼路径"的那一层，而不是每个入口

**问题**：会话 id、轮次 id、figure 的 course/chapter、图谱工件名，都会经"客户端 →
路径拼接 → 文件系统"。逐个入口校验必然会漏（路由、API、CLI、recipe 各一套）。

**选择**：在**路径构造的单一咽喉**上校验，让所有读写删路径天然被覆盖：

- `conversations._conversation_dir(pool, conversation_id)`：`conv-\d+` 形状不匹配即
  `ValueError`（`_turn_file`/`_events_file` 顺带校验 `turn-\d+`）。四个路由
  （get / rename / delete / turns / events）和 CLI 全部走它。
- `ingest._figures_root(database, course, chapter)`：course 必须等于池课程、chapter
  必须是章标识符；再由 `_gate_figure_patch` 在写之前拒绝。
- `registry` 侧：`db` 必须在工作区内（`Path(workspace["path"]) / db` 解析后
  `is_relative_to(folder)`）。

**不选择**：全局的"路径白名单"抽象或中间件——防御性编程，且违反 ponytail 阶梯。

## 决策 2：`_resolve_name` 拒绝猜，而不是加新参数

Agent 面命令（`weak/due/pull/practice/feedback/schedule/goals/data`）**本来就接受位置名**
（`lesson-kit pull <name> --kp …`），所以歧义时只需报错并把可粘贴命令给出来——不加
参数、不改用法。单工作区仍零参可用（保持"能推导就推导"的人面简洁原则）。

报错文本形状：`several workspaces registered (dmath, c01) — name one:
  lesson-kit pull dmath --kp …`（用实际命令名 + 实际位置名拼）。

## 决策 3：池候选排除备份，多份池时用 `--course` 选

**现状**：`find_pool()` = `sorted(pool/*.db)[0]`。本仓库因此会选到
`dmath-pre-readiness-2026-08-26.db`。

**选择**：
1. 候选 = `pool/*.db` 去掉 `*.db.ingest-backup` 与 `pool/backups/**`；
2. 若 `pool/<course>.db` 存在（course 由决策 4 的推导顺序得到）→ 用它；
3. 否则候选恰好一份 → 用它；
4. 否则候选多份 → 拒绝，列出候选并给出 `--course <name>` 的完整命令；
5. 否则（没有候选）→ 保持今天的建库行为（`pool/<course>.db`）。

这样 `--course` 从"只定 id 前缀"升级为"也定池文件"，零新增参数就消掉歧义。

## 决策 4：章标识符与课程同一规则

`init --chapter` 与 `use <course> <chapter>` 的章原样入注册表，而它被拼进
`f"{course}-{chapter}"`（SQL `LIKE`，`%`/`_` 是通配符）与
`output/<course>/<chapter>/<chapter>-graph.html`。因此章也必须是
`[a-z0-9][a-z0-9-]*`（可空 = 全课程，保持既有语义）。复用 B 的 `_require_slug`，
只把报错里的名词换成"chapter"。

**边界**：不引入"章名单表"，章仍只是 id 前缀（GLOSSARY「章」不变）。

## 决策 5：入池门禁认课程，靠池自己的课程而不是新字段

微题/闪卡门禁拿到 manifest 时手里就有连接（`_gate_micro_quiz(conn, manifest)`），
但 conn 不含课程。选择：把"本工作区课程"作为参数传进门禁（`apply_batch` →
`_apply_patch` → gate 链），由调用方从 `pool.course` 给出；**课程为空则拒绝**
（宁可报错也不猜前缀）。id 前缀不匹配时逐条报错并给出期望前缀。

figure-patch 同法：`_gate_figure_patch` 增加"course 必须等于本工作区课程、
chapter 是章标识符"，并在 `_figures_root` 里做最终包含性断言（两道，因为
`_figures_root` 也被 rollback/迁移路径使用）。

## 决策 6：示例 id 用上下文里的真实课程/章

`_prompt(message, context)` 已经收到服务端重建的上下文，里面有
`workspace.course` / `workspace.chapter`（`context.py` 已经在填）。因此**不改签名**，
只在拼示例时取这两个值：`f"{course}-{chapter}-fc-901"`；章为空时用 `ch01` 占位并
在示例里写明"编号从 next_free_ids 起顺延"（既有措辞已如此）。绝不出现硬编码
`dmath-ch06`。

## 决策 7：注册校验的边界

- 拒绝：同文件夹换名注册、两个名字共用一个池、同名不同文件夹、db 越界。
- 允许：同一工作区重复注册**同名同路径**（幂等 `init`，今天的既有行为）。
- 不做：注册表迁移/去重脚本、锁文件、并发写保护（单机单进程，超出本次范围）。

## 风险与不做

- 不做"Agent 越界拦截"：所有者明确说接入的 Agent 不受约束，本 change 只管本项目
  功能构造的路径。
- 不改 id 契约与池结构；既有 `dmath` 数据与注册表条目零迁移。
- `pool/backups/` 里的历史备份文件不移动（是否归档为独立 change 的待办）。
