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

---

## 3. 这一波做完了（2026-10-24 · 四组 + 一次缺陷修复）

> ⚠️ 本节是**已完成态**的记录；第 2 节的提示词是给「还没开始」时用的。

### 3.1 提交

| 组 | 做了什么 | 提交 |
|---|---|---|
| 工具 | 对照板带靶子列时改成三列（`.pair--3`；动画闸门未动） | `164bd935` |
| 2 | 顶栏动作区四个控件（搜索 · 对话视图 · 夜纸 · Agent 对话）+ 工作区身份上移到顶栏段二 | `4ef7d435` |
| 3 | 右栏会话按 **今天 / 昨天 / 更早** 分组（客户端分桶，组标题无计数） | `5fff561f` |
| 4 | 优先回看条目加状态点（红叉 / 黄斜杠 / 中性墨环） | `30846738` |
| 5 | 左栏首组「页面」→「**学习**」+ 分组间距照 V1 | `4ea8062d` |
| 修 | 回看条目第三态不另造词 + 状态点几何按 A-115 改成纯线条 | `7f18a293` |
| 修 | **图谱页窄视口下画布盖住抽屉**（学习者截图；不是本波引入的） | `aabf46d9` |
| 文档 | 契约同步（GLOSSARY / copy-table / PRODUCT-MANUAL / ACTION-GRAPH / contract-drift / design / tasks） | `3eee5f05` |

**对照板**：`tmp/wt-v1/board-w1.html` … `board-w4.html`（靶子 | 改前 | 改后）。
⚠️ `tmp/` 不入库 ⇒ 清了就没了；工具在库里，随时能重抓。

### 3.2 两个 Open Question 的裁定（**按文档判，不在产品里试**）

- **顶栏搜索接哪条通路** ⇒ **跳到知识图谱页既有的搜索框**（`#graph-search`）。
  依据：本 change 的 Non-Goals 禁「新请求 / 新载荷」；`retrieval-evaluation` 的 spec
  明文「SHALL NOT integrate with the student UI」；靶子给的是**按钮**不是搜索框。
  ⚠️ 图谱页本身**范围外** ⇒ 只当落点，不改它一个字节。
- **状态词表** ⇒ **不新造词**：复用 `docs/GLOSSARY.md`「行动提醒」的
  **重点练习 / 可以复习**，第三态**没有词**（保持中性）。
  ⚠️ 早先的设计稿写「未开始（蓝 ring）」——按 `component-spec` §3.6/§4.14 改走
  **中性墨环**（蓝环 =「当前选中」，挂在回看条目上会读错），已登记 CD-185。

### 3.3 三个值得所有者过目的判断

1. **顶栏动作区的顺序**取的是**靶子**的（搜索 · 对话视图 · 夜纸 · Agent 对话），
   不是任务清单里写的顺序 —— 依据 A-143「构图以靶子为准」。一句话就能换。
2. **状态点几何**：产品原本是「彩色圆盘 + 挖空符号」且 `dash` 是横杠；
   §4.14 的样例与靶子都是**纯线条**（dash = 45° 斜杠）⇒ 按权威改了。
   ⚠️ 这是本轮唯一一处越出「把控件摆到靶子位置」的改动，可单独回退。
3. **导航项名一个没动**（靶子写「图谱」，copy-table §2.12 P-151 定稿「知识图谱」留）。

### 3.4 验收

`pytest tests -q` 1202 passed · `compileall` OK · `openspec validate --specs --strict`
19/19 · `guard extract-problems` PASS · `probe.py static` 3.5-1/2/3/**4** 全 PASS ·
四档几何 `280/740/420 · 248/652/380 · 232/792/抽屉380 · 抽屉300/768/抽屉380` 全中 ·
A-39 服务字节 == 磁盘字节 · **图谱页 G-5 三处冻结未变** ·
`/api/w/{name}/weak` 载荷仍是原四个字段。

### 3.5 走查清单新增一条

**3.5-4**「窄视口下抽屉里的内容可点（图谱页：画布不得盖住抽屉）」——
对着**改前的 CSS 跑是 FAIL**、对着修完是 PASS ⇒ 它真的抓得住那个缺陷。
**此前 3.5-2/3.5-3 只在练习页开抽屉，图谱页的抽屉一直没人测过**（口径缺口）。

### 3.6 留给所有者

靶子 `mockup-baseline/shell.html:620` 那条**仍画着蓝环**（静态样板图没动）——
要么在靶子旁标注「此点以 component-spec 为准」，要么改画法；
靶子是 A-143 定的构图基准，**改它的取舍归所有者**。
