# CSS 行号锚点重定位表（2026-10-22）

> **为什么有这张表**：第 1–4 组在 `workbench/server/static/workbench.css` 的 `:root` 里
> 插入了 318 行新 token 定义，**该文件以下所有行号全部位移**，且位移不均匀
> （+307 / +308 / +310 / +312 / +702，甚至 **−100 / −127**）。
> 本表是**参考**，不是定位依据。

## 🔴 定位纪律（所有改 `workbench.css` 的 agent 必须遵守）

> **按选择器 / 声明 / 注释文本定位，不要按行号定位。**
> 用 `grep -n "<选择器>" workbench/server/static/workbench.css` 现场取行号。
> 本表只用于**交叉核对**（例如「我以为它在 1211 行，实际在 1518 行」）。

## 重定位表

| 锚点 | 旧行号 | 新行号 | 位移 |
|---|---|---|---|
| 图谱区段起点（`知识图谱 —— 纸质蒙德里安` 注释块） | 1497 | 1807 | +310 |
| 图谱专用 `:root`（`--paper:#fffdf7`） | 1505 | 1813 | +308 |
| `.micro-verdict.ok`（契约外绿） | 1211 | 1518 | +307 |
| `label.option-correct`（契约外绿环） | 1214 | 1521 | +307 |
| `.record-verdict-ok`（契约外绿药丸） | 1462 | 1769 | +307 |
| `.paper-dot.state-correct`（契约外绿格） | 1892 | 2199 | +307 |
| `.practice-question-card`（题面纸） | 924 | 1231 | +307 |
| `.knowledge-body`（知识点正文） | 493 | 393 | **−100** |
| `.practice-solution`（解析纸） | 933 | 1240 | +307 |
| `.linked-problem-text` | 524 | 397 | **−127** |
| `.record-answer`（记录摘录） | 1467 | 1774 | +307 |
| `.rich-text` 块（待整体退役） | 752 | 1059 | +307 |
| 全局降级闸门（`transition:none !important`） | 733 | 1435 | **+702** |
| 全局降级闸门（`animation:none !important`） | 1126 | 1436 | +310 |
| `#layout` grid 模板 | 160 | 467 | +307 |
| 退役 scope-tray 死 CSS | — | 485 | — |
| 128px 死预留（`padding-right:128px`） | 255 | 562 | +307 |
| 76×8 装饰黄块 | 261 | 573 | +312 |
| 3px 纯黑底线 | 258 | 566 | +308 |

## 影响面

- 本变更的所有任务书（`briefs/IMPL-*.md`）里的 `workbench.css:NNNN` 引用**全部过期**。
- `design-notes/*.md` 与 `decisions.md` 里对 `workbench.css` 的行号引用同样过期
  （**内容结论不受影响**，只是行号）。
- **图谱 change**（`graph-node-visual-language`）的任务书里也引用了
  `workbench.css:1497-1884` / `:1505-1518` 等 —— 那个 change 实现时同样要按选择器定位。
