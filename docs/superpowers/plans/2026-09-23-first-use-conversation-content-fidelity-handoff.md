# Lesson Kit 首次真实使用修缮：执行交接

**日期：** 2026-09-23  
**Active change：** `first-use-conversation-content-fidelity`  
**本轮边界：** 只更新 OpenSpec/交接文档；没有修改实现、测试、数据库或真实工作区。

## 1. 接管入口

按顺序阅读：

1. `openspec/changes/first-use-conversation-content-fidelity/proposal.md`
2. `openspec/changes/first-use-conversation-content-fidelity/design.md`
3. `openspec/changes/first-use-conversation-content-fidelity/tasks.md`
4. 该 change 下全部 spec deltas
5. 本文件与当前 `git status --short`

不要重新做需求访谈。若旧会话/旧文档与本 change 冲突，以本 change 为准。

## 2. 首次真实使用证据

只读核实对象：`大学物理乙II`，课程 `c01`，章透镜 `ch12`，Pi 对话 `conv-001`。

- 8 个 turn 最终均为 done。
- 第 3 轮因旧池缺 `problems.origin_kind` 写入失败；第 4 轮迁移后恢复。
- 五个未回滚 micro-quiz batch 共写入 `6+6+6+6+5=29` 题。
- 池中 8 个知识点、29 道题、0 闪卡、0 难度评级、0 attempts/feedback/schedule；
  外键与 integrity 正常。
- 29 题全部为 textbook + adapted_problem + single_choice；原教材习题 12-25 缺失。
- figure 目录没有文件，知识点关联题没有图片。
- Pi 表格按普通管道字符显示；事件文件未发现未遮盖的 assignment-style secret。

这次异常不是 Pi 单纯选错题型：对话 action 只支持 flash card 和 micro quiz，prompt 又把
micro 限定为判断/单选/多选，因此教材计算、证明等原题没有合法的对话写入通道。

## 3. Micro Quiz 历史与最终口径

- 2026-08-27：所有者提出 AI 只适合生成简单判断/选择练习，不适合综合主观大题。
- 2026-08-28：项目据此正式提出并实现 `micro-quiz-content`。
- 2026-08-29：旧卡片式短题模式正名为 `micro / 小测`，`flash_card` 留给真正的键值记忆卡；
  Check 首期因现成门禁只接闪卡和微题，正式题配方后置。
- 后续错误：首期限制被扩大成所有对话题目导入的唯一通道。

最终决定：保留微题名称、数据与现有 `综合题 / 小测 / 判断 / 闪卡` 四入口；微题与计算、
证明、建模等其他题型同类，内部继续分 yes_no/single_choice/multiple_choice。本轮只补齐
其他题型通道并禁止静默转微题，不做微题改名、删除或全局迁移。

## 4. 已锁定的产品决定

### 内容操作

- 删除浏览器关键词 regex；合法的 append-only 内容 action 自动执行、无确认弹窗。
- 自动范围：新增知识点、正式题、微题、闪卡、图片。
- 修改、删除、回滚、难度评级仍要求用户明确指令。
- 普通回答没有 action 时零写入；所有受治理写入仍走 gate/batch/backup/rollback。
- Agent 文件工具在所有对话中允许任意本机路径读写；工作区外写入不属于 Lesson Kit
  批次治理和回滚范围，文档/界面不得作相反承诺。

### 大批量与原子 bundle

- 删除 prompt 的 3–6 条限制。
- Agent 把完整 manifest 暂存在 `.lessonkit/jobs/conv-NNN/`，随对话保留；action 只引用文件。
- 一个 content bundle 可同时新增知识点、题目/卡片和图片；无固定数量上限。
- 全量预检后一个 batch 原子提交；任一非法项/缺图导致整批零写入。
- 失败时 Agent 修改完整暂存清单后整批重检，不自动剔除坏项。
- 用户拒绝机械覆盖门：“全部导入”只由 Agent 文字说明，不能宣称确定性无遗漏。

### 原题、答案与图片

- 教材题默认保留原题文字、数值、选项、作答形式与 `source_problem`；只有明确要求时改成微题。
- OCR 错误可对照 PDF/原图纠正，禁止自由润色。
- 新 Agent 题目的教材来源在题目下方可见。
- 教材短答案单独保留；AI 详细解析仅按需生成，直接入库但必须显示 `AI 生成解析`。
- 图片从任意源路径读取，原始字节复制到 `.lessonkit/figures/{course}/{chapter}/`，不转换、
  裁剪、增强或重绘。
- 缺必需图片的题不得入库。
- 回滚立即删除本批创建且已无引用的图片；仍被其他内容引用的文件保留。

### Markdown 与 Pi

- Agent 消息和知识点关联题统一支持标题、列表、引用、代码、链接、图片、数学与 GFM 表格；
  原始 HTML 继续转义/拒绝。
- Pi 每个对话一个 `--mode rpc` 进程，空闲 30 分钟退出，不设同时进程数上限。
- RPC 启动/握手失败可重启一次；prompt 接受后崩溃不得自动重放。
- cancel 先 abort，失效才 terminate/kill；服务关闭/删除对话/空闲到期清理进程。
- Pi/Codex/Claude 等全部 Windows provider 子进程隐藏启动，不弹终端。

## 5. 真实物理池修复授权

完整实现、全量自动化和隔离副本真实验收全部通过后，执行 Agent 无需再次确认即可修复真实池：

1. 创建并报告 pool/figure 可恢复备份。
2. 重新检查 batch-001～005 是否新增 attempts、feedback、schedule 或其他依赖；若不再为零，
   立即停止且不修改真实池。
3. 无阻塞时按 batch-005→001 回滚五批错误微题。
4. 保留并对照教材审阅现有 8 个知识点；缺失知识点随新 bundle 原子补充。
5. 按教材原题、原图、来源证据和来源答案重新导入；AI 解析保持按需。
6. 保留 `conv-001`；重开时旧结果卡读取批次现状并显示 `已回滚`，不再出现回滚按钮。
7. 输出最终 accounting、foreign_key_check、integrity_check、备份位置和页面验收证据。

## 6. 执行与验收纪律

- TDD；Shell → Domain → Data；stdlib-only；禁止 raw SQL Agent 通道。
- 开发和真实走查只使用物理工作区副本。
- 真实池修复前必须重新检查依赖，不能沿用 2026-09-22 的旧快照。
- 同一执行 Agent 负责本次实现到最终验收，这是用户对独立验收惯例的明确例外。
- 不 commit/push，除非用户另行授权。

## 7. 给执行 Agent 的提示词

```text
请接管 Lesson Kit 的 active OpenSpec change：

first-use-conversation-content-fidelity

你已经有项目上下文，不要重新做需求访谈。请先完整阅读：

1. openspec/changes/first-use-conversation-content-fidelity/{proposal,design,tasks}.md
2. 该 change 下全部 spec deltas
3. docs/superpowers/plans/2026-09-23-first-use-conversation-content-fidelity-handoff.md
4. 当前 git status；工作区已有他人改动，不得 reset、checkout 或覆盖

最新决定已经锁定：

- 保留“微题”和现有“综合题 / 小测 / 判断 / 闪卡”四入口；不要取消、迁移或改名微题。
- 微题是正常题型之一。教材原题必须保留计算、证明、建模等原始形式；只有明确要求时才改编为微题。
- 补齐正式题、知识点、微题、闪卡、图片的 Agent 对话入库通道。
- 删除 3–6 条 prompt 限制。大 manifest 存入 conv jobs，并作为一个原子 content bundle 提交。
- 知识点、题目和图片同批预检；任一失败则整批零写入。
- 图片保留原始字节并复制到 `.lessonkit/figures/{course}/{chapter}/`；缺必需图片的题不得入库。
- 删除关键词 regex。合法的 append-only 新增 action 自动执行；修改、删除、回滚和难度仍需明确指令。
- Provider 文件工具允许任意路径读写；Lesson Kit 批次治理只覆盖当前工作区内的受治理写入。
- 来源证据显示在题目下方。教材答案保留；AI 详细解析仅按需生成并显示“AI 生成解析”，无需独立审核。
- Agent 消息和知识点关联题统一支持安全 Markdown 子集及 GFM 表格。
- Pi 每个对话一个隐藏 `--mode rpc` 进程，空闲 30 分钟回收，不设数量上限；所有 provider 在 Windows 下不得弹终端。
- RPC 启动前失败可重启一次；prompt 接受后崩溃不得自动重放。
- 不做机械题目覆盖门；“全部导入”仍只是 Agent 文字说明。
- 功能与副本验收全部通过后，按交接文档直接修复真实大学物理乙II池；若五个旧 batch 已产生学习依赖，停止并报告。

请按 tasks 使用 TDD 实现，完成聚焦测试后运行全量 Python、全部 Node、compileall、OpenSpec strict、doctor、guards、隔离物理副本完整导入，以及真实 Pi 0.85.1 多轮单 PID/abort/恢复/隐藏窗口验收。

本次你负责执行到最终验收、真实物理池修复和 OpenSpec archive。不要 commit 或 push，除非用户另行授权。交付时更新 tasks、GLOSSARY、PRODUCT-MANUAL、ACTION-GRAPH、ARCHITECTURE 等 current docs，并报告精确测试数量、Pi PID 证据、真实池备份路径、回滚/重导 accounting 与剩余风险。
```

