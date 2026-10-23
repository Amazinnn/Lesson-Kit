# IMPL-F3 — Markdown 双渲染器统一 + parity 测试

> 实现任务：`openspec/changes/workbench-visual-language-v2/tasks.md` 的 **第 7 组**
> （7.1–7.5）。改 `workbench/server/pages.py` 与 `workbench/server/static/workbench.js`，
> **新增** `tests/test_markdown_render_parity.py`。**不碰 `workbench.css`**。

## 必读
1. `openspec/changes/workbench-visual-language-v2/tasks.md` 的 **第 7 组全文**（逐条实现）
2. `openspec/changes/workbench-visual-language-v2/design.md` 的 **D-6**
3. `openspec/changes/workbench-visual-language-v2/decisions.md` 的 **A-6**（字号口径）
4. `openspec/changes/workbench-visual-language-v2/design-notes/motion-spec.md`（动效口径，勿动）
5. `docs/ARCHITECTURE.md:240`（「普通 Paper 题目与知识正文共享主阅读层级」这条既有契约）

## 硬约束
- **只改/新建这 3 个文件**：
  `workbench/server/pages.py` · `workbench/server/static/workbench.js` ·
  `tests/test_markdown_render_parity.py`
- **不许**改 `workbench/server/static/workbench.css`（**并行 agent 正在改它**）、
  不许改 `records.py` / `practice-flow.js` / `paper-practice.js` / `docs/` / `openspec/` 下的文件。
- **不许**改 `tasks.md` 的复选框（会与并行 agent 冲突）—— 最终回报里逐条列出完成的 task id。
- 冻结项：**请求与持久化不变**。本组只改**渲染输出**，不改任何请求、任何学习事实。
- 遇到规范与实现冲突：**停下来报告**，不要自行发挥。

## 7.1–7.2 具体要求
- 统一到**服务端语义**：正文 `#` → `<h2>`、`##` → `<h3>`、`###` → `<h4>`。
  服务端 `pages.py:978` 的 `level = len(heading.group(1)) + 1` **保持不变**；
  客户端 `workbench.js:443` 的 `<h" + heading[1].length + ">` 改为**从 `<h2>` 起步**。
  ⇒ 客户端不再与页面标题争 h1。
- 服务端代码围栏补 `class='language-xx'`（`pages.py:955` 现在丢掉语言标记）。
- 引用块统一用客户端那条正则 `^\s*>\s?`（`pages.py:993` 现在用 `line.startswith(">")`，
  行首带空格会漏判）。
- ⚠️ **不要**顺手改标题的**字号**（那是第 6 组 `.wb-reading` 的活，另一个 agent 在做）。
  你只改**标签层级**。

## 7.3 parity 测试（本组的核心，别糊弄）
- 新建 `tests/test_markdown_render_parity.py`。
- 一份覆盖 3 级标题 / 有无语言标记的代码围栏 / 引用（**含行首带空格的**）/
  有序无序列表 / GFM 表格 / 分隔线 / 行内数学的 Markdown 语料。
- 语料**分别**喂：`pages._render_markdown()`（服务端）与 `workbench.js` 的渲染函数
  （客户端，**经 Node 调用同一份 JS 源**）。
- **断言两侧 HTML 逐字符相等**。
- 语料与断言放 `tests/` 下，**不进产品目录**。
- **测试在改造前先红**（把现状差异记录下来，例如写成注释或一个 `xfail` 说明），
  改完转绿。**不得用「人工同步」代替断言。**
- 若本机没有 Node：按 7.4 走退化路径（Node 单测 + pytest 黄金样本双跑），
  并把「人工同步」写进 `design.md` 的风险表 —— 但**优先尝试装 Node 或用已有 node**
  （本机 `frontend/editable-graph/node_modules` 存在，说明机器上有 node 生态）。
  ⚠️ 测 Node 是否存在要**先查**（`node --version`），别假设。

## 验证
- `python -m pytest tests/test_markdown_render_parity.py -q` 通过。
- `python -m pytest tests -q` 全绿。
- `python -m compileall -q lessonkit.py workbench pipeline pool tests` 通过。
- 截图走查：题面 / 知识点正文 / 解析 / 记录摘录四处**同源 Markdown** 的排版对照；
  确认「客户端 `#` → h2」是本变更**唯一让既有可见文字变小**的地方，并在回报里单列。

## 落盘纪律与回报
2 分钟内先落测试骨架（先红），再改实现转绿。
最终回报必须复述：**已落盘路径 + 完成的 task id 列表** + **parity 测试的语料覆盖项清单** +
**改造前红 / 改造后绿的实际输出** + **是否有 Node** + **四处 Markdown 对照截图路径** +
**四条验证命令结果** + 任何登记为待裁决的项。