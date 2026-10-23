# HANDOFF —— 把产品收敛到 V1 基线

> 给下一个对话的**提示词**在下面第 2 节，**整段复制**即可。

---

## 1. 现状（下一个对话必须先知道）

| 项 | 值 |
|---|---|
| 仓库 | `D:/Projects/Academic Workflow/lesson-kit` |
| 分支 | `feat/workbench-visual-language-v2`（**main 已合并 V1 基线**，分支比 main 多这一个 change 的 planning artifacts） |
| 靶子（基线） | `openspec/changes/workbench-visual-language-v2/design-notes/mockup-baseline/v1.html`（tag `v1-mockup-baseline`） |
| 本次要实现的 change | `openspec/changes/workbench-v1-baseline-convergence/`（proposal / specs / design / tasks 齐了，`openspec validate --change ... --strict` 通过） |
| 硬边界 | 请求序列与载荷不变 · 组件形态听 `component-spec.md` §4.30（A-115）· 图谱页范围外 · **不合并 main、不 push** |
| 起手状态 | `pytest tests -q` 全绿（**1198 passed**）· `openspec validate --specs --strict` 19/19 · `guard extract-problems` PASS |

---

## 2. 提示词（整段复制给下一个对话）

```
在 D:/Projects/Academic Workflow/lesson-kit 仓库里，把工作台产品收敛到「V1 基线」。

## 先读这五份（按顺序，别跳）
1. AGENTS.md（分层方向 / 兼容边界 / scope 边界 / 开发纪律）
2. openspec/changes/workbench-v1-baseline-convergence/proposal.md
   → design.md → specs/workbench-ui/spec.md → tasks.md
3. openspec/changes/workbench-visual-language-v2/VERSION-V1.md（V1 是什么）
   与 design-notes/mockup-baseline/README.md（权威分工）
4. openspec/changes/workbench-visual-language-v2/decisions.md 的
   A-142 / A-143 / A-144（靶子优先的规矩）与 A-136 / A-137（几何与夹取）
5. openspec/changes/workbench-visual-language-v2/design-notes/layout-spec.md 的
   §2（顶栏）§3（左栏）§6（右栏）—— 只读这几节，别通读

## 靶子
openspec/changes/workbench-visual-language-v2/design-notes/mockup-baseline/v1.html
（浏览器 file:// 直接开；六个样板图页面原样拼在一页里）
**构图与数值以靶子为准；组件形态以 component-spec.md §4.30 为准**（A-115 晚于靶子 17 小时）。
graph.html 那页**不作数**（图谱页范围外）。

## 要做的四件事（tasks.md 的第 2–5 组）
2. 顶栏动作区：Agent 对话开关 · 主题开关 · 对话视图开关 · 搜索
3. 右栏会话按「今天 / 昨天 / 更早」分组（不加计数）
4. 优先回看条目加状态点（颜色 + 几何双通道）
5. 左栏首组改「学习」，工作区身份上移到顶栏段二

## 三条不许越界的
- **请求序列与载荷不变**（冻结项）；会话分组只能在客户端做
- **组件形态不动**（听 A-115）；本轮只「把既有控件摆到靶子的位置」，不造新组件
- **不合并 main、不 push**（合并由所有者另行指示）

## 两条要先定的（design.md 的 Open Questions，未定就停，不要在产品里试）
- 顶栏「搜索」接哪条检索通路？（产品有 retrieval-evaluation 能力但未接 UI；
  也许只做「跳到知识图谱搜索」。**不要放假搜索框** —— 不查东西的搜索比没有更糟）
- 优先回看的状态词表（到期复习 / 阻塞 / 未开始 的确切措辞）：
  先按 AGENTS.md 纪律 2 落 docs/GLOSSARY.md，再落 copy-table.md §5 的状态词表

## 工作方式（每一条都要照做）
- **在分支上做**（当前分支 feat/workbench-visual-language-v2）；不并 main、不 push
- **同文件串行**：workbench.css / workbench.js / pages.py 一波只碰一个文件的同一段
- **每完成一项就出一张三列对照板**给所有者看：靶子 | 改前 | 改后
  工具：python tools/walkthrough/view.py capture --base-url ... --ws walk --out <dir>
        python tools/walkthrough/view.py board --before <dir> --after <dir> --reference <靶子截图目录> --out <html>
  ⚠️ 抓图必须过**动画闸门**（等「没有正在跑的有限动画」再拍）——
  否则视图转场会把中栏拍成一片空白（工具已内建，**别改**）
- **实测口径**：probe.py static（3.5-1/2/3 必 PASS）· 四档几何
  （1440 280/740/420 · 1280 248/652/380 · 1024 232/792/抽屉380 · 768 抽屉300/768/抽屉380）
  · 图谱页 G-5 三处冻结仍在
- **提交**：`git add -- <路径>` 与 `git commit -- <路径>` **两个都带**，绝不 `git add -A`
- **收工前**跑：pytest tests -q · compileall · openspec validate --specs --strict ·
  guard extract-problems --course dmath --chapter ch06
- **契约同步**（AGENTS.md 纪律 3）：docs/PRODUCT-MANUAL.md（顶栏与左栏的用户可见说明）·
  docs/GLOSSARY.md（新状态词）· docs/ACTION-GRAPH.md（若新增动作）·
  spec delta 已在本 change 里，不要另起
- 交接：docs/STATUS-workbench-visual-language-v2-2026-10-23.md 回写

## 已知的坑
- pip 里装了 lesson-kit 0.1.0 ⇒ 必须在**仓库根**起服务，并核对服务字节 == 磁盘字节（A-39）
- 本机 http_proxy=127.0.0.1:7890 会吞掉 localhost 请求 ⇒ 命令前加
  env -u http_proxy -u https_proxy -u all_proxy
- 端口避开 3081/3092/3099/3177/3178/3184/3200/3201/3281/3282/3288/3411/3460/3461/3462/3477/3481/3482
- 每跑一次 defects.py 会新增一条练习记录 ⇒ D1–D5 的数字要用「同数据态」对比
- :where() 特异度为 0，压不住基类规则 ⇒ 形态高度写在形态规则里
- 图谱作用域冻结了三处（外壳几何）⇒ 改外壳时别把图谱页带着变
```

---

## 3. 下一个对话可以直接用的三个入口

| 入口 | 命令 / 路径 |
|---|---|
| 应用 change | `openspec apply workbench-v1-baseline-convergence`（或按 `tasks.md` 手工走） |
| 看靶子 | `openspec/changes/workbench-visual-language-v2/design-notes/mockup-baseline/v1.html` |
| 出对照板 | `tools/walkthrough/view.py`（`capture` / `capture-static` / `board`） |
