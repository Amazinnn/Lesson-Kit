# IMPL-F1 — CSS 地基：token 架构 · 别名期 · 纸面层级 · 色彩收编

> 实现任务：`openspec/changes/workbench-visual-language-v2/tasks.md` 的 **第 1 / 2 / 3 / 4 组**
> （1.1–1.5 · 2.1–2.4 · 3.1–3.4 · 4.1–4.5）。**只改 `workbench/server/static/workbench.css`**。

## 必读（按顺序）
1. `openspec/changes/workbench-visual-language-v2/tasks.md` 的**第 1–4 组全文**（你的任务书，逐条实现）
2. `openspec/changes/workbench-visual-language-v2/design-notes/night-paper-tokens.md`（**token 唯一权威**，
   §2 结构 token / §3 值 token / §4 对比度实测 / §6 例外表）
3. `openspec/changes/workbench-visual-language-v2/design.md` 的 **D-1 / D-2 / D-3**
4. `openspec/changes/workbench-visual-language-v2/decisions.md` 的 **A-8 / A-9 / A-13 / A-20 / A-23 / A-30 / A-31**
5. `openspec/changes/workbench-visual-language-v2/design-notes/graph-isolation.md`（**图谱移交清单**）

## 硬约束（违反 = 任务失败）
- **知识图谱完全不动**：图谱专用区段 `workbench.css:1497-1884` 与其专用 `:root`（**1505-1518**，
  含 `--paper:#fffdf7` `--ink:#191816` `--hair:#ddd8cd` 等 12 个裸名）**一行都不许改**。
  新 token 与这 12 个裸名**零同名**（脚本校验求差为空）。
  这是本变更对图谱的**唯一**责任：不误伤。
- **无框架、无构建步骤、无 npm、无 CDN、无外部资源**。纯 CSS。
- **只改 `workbench/server/static/workbench.css` 这一个文件**。
  不要改 `pages.py` / `workbench.js` / `records.py` / `docs/` / `openspec/` 下的任何文件
  （**并行 agent 正在改它们**）。
- **不要改 `tasks.md` 的复选框**（会与并行 agent 冲突）—— 在最终回报里逐条列出
  你完成的 task id 与验证结果，由主会话统一勾。
- 遇到规范与实现冲突、或某条任务不可行：**停下来报告**，不要自行发挥。

## 实施顺序（严格按 `tasks.md` 1.4 的迁移步序）
1. **Step 1**：只在 `:root`（现 L4-46）里**换值**：加新 token 定义、把旧 `--lk-*`/`--dsw-*`
   改成指向新 token 的别名（**只改定义、不改任何引用点**），每条别名加注释「别名期，勿新增引用」。
   —— 这一步必须**单独一次提交**，且**零 class 变化、零 JS 变化、零结构变化**。
2. **Step 2**：换描边 / 抬升 / 文字灰 + 22 个硬编码色（4.2 的收编表逐条映射）。
3. **Step 3**：才动间距 / 字号 / 圆角 / 动效 / z-index（3.1 纸面四层 · 3.2 暖调柔影三档 ·
   3.3 取消 56 处描边，只留 `--rule-control` 与 `--rule-structure` 两类例外 · 4.3 墨阶 4+1 级收敛 ·
   4.4 契约外绿整体移除，「答对」改**中性墨 `--ink-strong` + 勾形几何**（4 处：
   `workbench.css:1211` `:1214` `:1462` `:1892`）。
4. **2.2** 补齐 4 个从未定义的变量（`--dsw-bg-layer-3` / `--dsw-border-subtle` / `--dsw-text-muted` /
   `--dsw-border`）—— **单独提交、单独 review、单独截图**。
   ⚠️ `--dsw-border-subtle` 无 fallback，补齐后表格线会从「正文色」变成新规则色，**属可见变化**。
5. **2.3** 别名期收尾：删除别名定义与引用点，**独立提交**（删除前用
   `grep -oE "var\(--[a-z0-9-]+" workbench.css | sort -u` 与新层定义集合求差验证无残留）。

## 提交纪律
每个可验证单元**单独提交**，前缀用 `feat/` `fix/` `chore/`。**工作区不留脏**。
每组末尾的阶段验收任务要求跑 AGENTS.md 四条验证命令：
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
```

## 截图走查（每步都要）
用**本地起临时 http 服务 + Playwright 截图**的方式，记录：工作台 / 练习 / 记录 / **图谱** 四页
（浅色 + 夜纸）。**图谱页必须逐像素无变化**（G-5 否定式断言）。
截图落在 `tmp/frontend-audit/impl-f1/`，用完清理临时脚本。

## 落盘纪律与回报
2 分钟内先落 Step 1（别名定义那一次提交），之后逐步推进；每步跑验证命令。
最终回报必须复述：**逐步提交清单（hash + 做了什么）** + **完成的 task id 列表** +
**新 token 与图谱 12 裸名求差为空的校验输出** + **四页截图路径 + 图谱页像素差异=0 的证据** +
**四次验证命令的结果** + 任何登记为待裁决的项。