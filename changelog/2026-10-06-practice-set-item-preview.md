# 组卷页：每道题就地展开预览

**日期：** 2026-10-06

## 变化

- 组卷页每张试卷卡片里的题项从「序号 + 标题 + ↑↓/移除」变成**可展开的块**：点开显示
  这道题的**完整题面**（与知识点页同一套渲染：公式、配图、代码一致）与**来源行**。
- 题项默认**收起**：77 题的试卷仍然先是一份目录，点哪题读哪题。
- 展开体复用知识点页的渲染路径（`_render_markdown` + `linked-problem-text rich-text`），
  没有第二套 Markdown 子集，也没有新的接口、状态或客户端代码。
- ↑ / ↓ / 移除三个控件留在 `<details>` **外面**：点「移除」只移除，不会顺手展开预览。
- 展开体只有**题面与来源，没有答案**——组卷页是选题与阅读的地方，答案在「导出」出的
  解答卷里。

## 实现

- `workbench/server/pages.py`：`practice_sets_page` 的题项包进
  `<details class='practice-set-item-body'><summary>`；`<li data-problem-id>` 外壳不变，
  所以重排/移除的既有交互路径原样可用。
- `workbench/server/static/workbench.css`：`.practice-set-item` 改成「题目块 + 操作」两列
  并对齐到顶部（展开长题面时按钮不跟着垂直居中）；`summary` 自己排「标记 + 序号 + 标题」
  三列，`▸ / ▾` 由 `::before` 画出（`display: grid` 会吃掉浏览器原生的三角）。

## 边界

- 不动试卷的数据契约（`ps-NNN`、`.lessonkit/practice-sets/`）、路由与 CLI。
- 不记「哪几行展开着」的偏好：刷新回到全收起，这是刻意的默认。
- 展开体不显示答案、不显示解题过程。
- 未重启 3081 daemon（由主会话负责）。
