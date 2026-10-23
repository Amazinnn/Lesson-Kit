# IMPL-N3 — copy-table 未落地清单（只读，为第 26 组铺路）

> 服务于 `tasks.md` **第 26 组**（文案清理）。
> **只新建** `openspec/changes/workbench-visual-language-v2/copy-table-gap.md`。
> **不修改任何其它文件。**

## 背景
`design-notes/copy-table.md` 定稿了 **671 条**界面文案（删 31 / 改 70 / 译 20 / 留 550）。
第 26 组要按它**逐条落地**。但现在**没人知道这 671 条里还剩多少没落地**——
一份可执行的「剩余清单」是第 26 组的前提。

## 要做什么
1. 逐条读 `copy-table.md`（**以文件实际内容为准**，不要照抄本任务书的数字）。
2. 逐条在实现里查**当前文案**（`workbench/server/pages.py` 与 `workbench/server/static/*.js`
   里的界面字符串）⇒ 判定该条是 **已落地 / 未落地 / 与定稿不一致**。
3. 输出一份**可执行的清单**：每条写 **ID · 页面 · 定稿文案 · 当前文案 · 状态 · 建议动作**。
4. 末尾给**统计**与**优先级建议**（哪些改动**用户可见**、哪些是**术语统一**）。

## 硬约束
- **只新建** `copy-table-gap.md`。**不修改任何其它文件**——
  **不要**顺手把文案改了（第 26 组才是干这个的，**它会动 `pages.py` 与 JS**，
  **另有 agent 正在并行改那些文件**）。
- **不要**改 `docs/` / `openspec/` 下其它文件。
- 判定「界面文案」时**排除**：代码标识符、注释、URL、aria-label 之外的纯技术字符串、
  用户内容（题面 / 评语 / 章节名等**来自数据**的文本）。
- 结论要有**可复核的证据**（文件 + 行号 + 当前文案原文）。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
```

## 落盘纪律与回报
- 一个 commit，只 `git add` 那个清单文件，**不要 `git add -A``**。
- 最终回报（中文）必须复述：已落盘路径 + commit 的内容 +
**统计（总数 / 已落地 / 未落地 / 不一致）** + **未落地条目按页面分组的前 20 条** +
**与第 26 组任务书（26.1 / 26.2）的对接建议** + 待裁决项。
