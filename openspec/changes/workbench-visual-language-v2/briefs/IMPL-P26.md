# IMPL-P26 — 第 26 组：文案清理（照台账逐条落地）

> 对应 `tasks.md` **第 26 组（26.1–26.3）**。
> **只改 `workbench/server/pages.py` 与 `workbench/server/static/*.js`**（**只改文案，不改逻辑**）。

## 手上已经有的台账（**先读它，别自己重做清单**）
`openspec/changes/workbench-visual-language-v2/copy-table-gap.md`（1155 行）：
**671 条定稿文案：已落地 557 · 未落地 114（删 27 / 改 67 / 译 20）· 与定稿不一致 0**。
每条带 `file:line` 证据与「当前文案 → 定稿文案」。

## 要做
- **26.1** 按 `design-notes/copy-table.md` 执行全站文案定稿：**一个中文语气**、
  一个标签 / 一句话里不混中英；空态 = 插画 + 一句 + 满宽主按钮（按钮文案即动作）。
  ⇒ **逐条落那 114 条**。台账里已算清「一个中文语气」的**全部落点共 36 条**
  （`Paper`→试卷 10 · `Check 入库` 3 · `Yes/No` 1 · `AI生成` 1 · 英文兜底 4 · 纯英文标签 3 ·
  `组卷`/`试卷` 不统一 2 · `正确率` 4 · `评分`/`自评分`/`熟悉程度` 6 · `卡点或心得` 2）。
- **26.2** 少字原则**删注释**：能删的界面注释**直接删除**（不是换成更漂亮的说明文字）；
  改造后界面上的说明性文字**数量不增加**。
  ⇒ 台账里那 **27 条「删」可直接当「删除前后信息量核对表」骨架**（copy-table §3 已给每条写好
  「删后由什么承担」）。

## ⚠️ 七条**不许动**（台账 §「待裁决」里的）
`P-74`（覆盖进度值域）· `R-28`/`R-31`/`R-41`（正确率→判定，与 D-09 一起裁）·
`W-105`（已回滚）· `A-13`（同屏两个「试卷」）· `P-163`（自评开关六处同 PR）·
`G-01…G-32`（**图谱 32 条，归 `graph-node-visual-language` change**）·
`W-171`（`an unfinished practice already exists` —— **禁改**，它只被 `===` 比较、从不渲染）。

## 硬约束
- **只改文案，一个字都不许改逻辑**：请求序列、载荷键、DOM 身份、事件绑定、
  判定分支、类名（**类名不是文案，不许顺手改**）—— 一律不动。
- **不许新增请求、零池写入、零新增 localStorage 键**。
- 知识图谱**一行都不许碰**；`G-01…G-32` 属另一个 change。
- ⚠️ **「一个中文语气」的落地**别只改标签：**逐条对照台账**（有的地方是
  `Paper`→`试卷`、有的是英文兜底 `Check 入库`，**「Check 管线」是 GLOSSARY 条目名，保留不译**）。
- 提交一律 `git commit -- <明确的路径列表>` 限定范围（**不要 `git add -A` / `-a`**）。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
node --test tests/workbench/*.test.js
```
- **台账里给的两条 grep 复核要跑**（那是它算好的验收口径）。
- 走查：仓库根 cwd、**独立端口**、池副本 + `LESSONKIT_WB_HOME`；**服务字节数 == 磁盘字节数**。
- `acceptance.md` §1「**文字内容除文案清理项外应逐字一致**」⇒
  **没在台账里的文案不许动**（要逐字比对）。

## 落盘纪律与回报
- 按页面分 commit（每页一个），只 `git add` 对应路径。
- 回报（中文）必含：已落盘路径 + 每个 commit 的内容 + **114 条的落地统计（逐条：已落 / 未落 / 原因）** +
  **27 条删除的「删除前后信息量核对表」** + **两条 grep 复核的输出** +
  **「除文案清理项外逐字一致」的核对结果** + 四条验证命令结果 + 待裁决项。
