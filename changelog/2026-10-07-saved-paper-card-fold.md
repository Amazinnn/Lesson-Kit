# 组卷页：试卷卡片自身可收起

**日期：** 2026-10-07

## 变化

- 每张试卷卡片整体变成**可折叠**：卡片头（标题、`N 题 · 只保存题目与顺序`、
  开始练习/改名/导出/删除四个按钮）常驻，**题目列表折在下面**。
- **默认收起**：一页两张卷子从此是两行卡片，而不是 150 行题目；要看第二张卷子不用
  先滚过第一张的全部内容。
- **展开状态在当前标签页里记住**（`sessionStorage`，键 `wb_paper_open_<工作区>`，
  与练习页筛选状态的存法一致）：每点一次 ↑/↓/移除 页面都会重载，记住之后不会每次
  操作都把正在编辑的卷子折回去；关掉标签页即失效，不写池、不上报、不是试卷的事实。
- 卡片头里的四个按钮**不会被折叠吃掉**：点导出就导出、点开始练习就开始，卡片保持原样。
- 卡片的状态行（改名/导出失败时报错的地方）移到折叠区**外面**，收起的卡片上也能看到错误。

## 实现

- `workbench/server/pages.py`：卡片改为
  `<details class='practice-set-card-body'><summary class='practice-set-card-head'>`，
  题项 `<ol>` 进折叠区；`<li data-problem-id>` 与按钮都不动。
- `workbench/server/static/workbench.css`：卡片头保持 flex 行，加 `▸ / ▾`
  手绘标记（flex 会吃掉原生三角）与 `cursor: pointer`；`.practice-set-card-title`
  取 `flex: 1 1 auto`，按钮仍靠右、题目列表仍占满卡片宽度。
- `workbench/server/static/workbench.js`：`restorePaperFolds()` 恢复并记录每张卡片
  的展开状态（忽略题项子折叠冒泡上来的 `toggle`）；委托点击处理里对按钮
  `event.preventDefault()`，避免一次点击既执行命令又折叠卡片。

## 边界

- 不动试卷的数据契约（`ps-NNN`、`.lessonkit/practice-sets/`）、路由与 CLI；折叠不
  发任何请求。
- 折叠状态只活在当前标签页：新开标签页回到「全部收起」的默认。
- 未重启 3081 daemon（由主会话负责）。
