# IMPL-P26b 报告 —— 第 26 组收尾：文案清理的最后 27 条（记录中心 / 做题经验面板 / A-119 六条 / A-120 两条）

> 上一波报告：`./IMPL-P26-report.md`（主波，89 条，口径与本报告一致）
> 台账：`../copy-table-gap.md`（§2.8 / §2.12 / §2.13 / §3.14）
> 定稿：`../design-notes/copy-table.md`
> 裁定：`../decisions.md` §A-119 / §A-120
> 基线：`5f8440db`（本棒起点，即 `c01d55f3` 的父提交）
> 报告 HEAD：`3eb9f2a1`（本报告提交前的最后一个 commit）
> 日期：2026-10-23

---

## 0. 一屏结论

| 项 | 数字 |
|---|---|
| 任务书交付条数 | **27**（任务书写「25 条」，但枚举是 19 + 6 + 2 = **27** —— 以枚举为准，详见 §2） |
| **本棒已落** | **27 / 27** |
| 核对中发现的真 bug 并当场修掉 | **1**（R-54 尾句号，commit `3eb9f2a1`） |
| 核对中发现的**文档 / 契约漂移** | **3 类 12 处**（未修，见 §8.1 —— 需要所有者裁决） |
| 提交数 | **6**（4 个上一棒已提交 + 1 个主会话补的 + 1 个本棒补的）+ 本报告 1 个 |
| 六条验证命令 | **全绿**（pytest 1181 passed · node 264/264 · compileall OK · openspec 19/19 · guard extract-problems PASS · guard problem-set PASS） |
| 界面可见文本节点 | **563 → 561（-2）**，字符 **2361 → 2320（-41）** ⇒ **不增** ✅<br>（整波累计 **585 → 561（-24）** / **2989 → 2320（-669）**） |

**一句话**：上一波（P26）留下的 **27 条**（19 条 `records.py` / `experience_page.py` 台账 + A-119 六条 + A-120 两条）
**全部落地**；本棒做的是**核对与记录**，另外查出 **1 处真 bug（R-54 尾句号，已修）**
和 **3 类 12 处文档漂移（P-163 标签 / R-41 标签，未修 —— 需所有者裁）**。

---

## 1. 已落盘路径 + 每个 commit 的 hash 与内容

### 1.1 落盘路径清单

| 文件 | 类型 | 本棒落地条数 |
|---|---|---|
| `workbench/server/records.py` | 服务端渲染（记录中心） | **19**（台账 16 条：R-06 / R-26 / R-34 / R-36 / R-38 / R-44 / R-45 / R-49 / R-54 / R-57 / R-58 / R-59 / R-60 / R-62 / R-63 / R-64 ＋ A-119 落地 3 条：R-28 / R-31 / R-41） |
| `workbench/server/experience_page.py` | 服务端渲染（做题经验面板） | **3**（E-03 / E-05 / E-10） |
| `workbench/server/pages.py` | 服务端渲染（左栏设置） | **1**（P-163） |
| `workbench/server/static/agent-ui.js` | 客户端 | **2**（A-13 / P-209） |
| `workbench/server/static/workbench.js` | 客户端 | **2**（W-105 / P-210） |
| `openspec/.../design-notes/copy-table.md` | 设计件（定稿用词校正） | 1 行（P-163） |
| `tests/workbench/test_ui_routes.py` | 测试断言同步 | 2 处（R-54 / R-62） |
| `tests/workbench/workbench_ui_interactions.test.js` | 测试断言同步 | 1 处（W-105） |
| `tests/workbench/test_records.py` | 测试断言同步（R-34 删除后） | 2 处 |

**未触碰**（并发 CSS agent 的在途文件与其它一切）：
`workbench/server/static/workbench.css` · `workbench/server/static/agent-ui.css` ·
`pipeline/` · `pool/` · `pool/scripts/` · `lessonkit.py` · `docs/` 下**全部**文件 ·
`openspec/specs/` 下**全部**文件 · `openspec/changes/…` 下除本报告外的全部文件。

### 1.2 提交清单

| # | hash | 提交信息 | 文件 |
|---|---|---|---|
| 1 | `c01d55f3` | docs(workbench): 文案定稿 —— 记录中心与做题经验面板（19 条台账逐条落地） | `workbench/server/records.py` · `workbench/server/experience_page.py` |
| 2 | `7e4897b2` | docs(workbench): 文案定稿 —— A-119 六条裁定 + A-120 两条漏收文案 | `workbench/server/pages.py` · `workbench/server/static/agent-ui.js` · `workbench/server/static/workbench.js` |
| 3 | `94ac6370` | docs(v2): copy-table P-163 定稿用词校正 —— 「练习与组卷显示自评」→「练习与试卷显示自评」（A-119） | `openspec/…/design-notes/copy-table.md` |
| 4 | `8b0dbd1d` | test(workbench): 同步定稿文案的断言字符串（R-54/R-62/W-105 三处） | `tests/workbench/test_ui_routes.py` · `tests/workbench/workbench_ui_interactions.test.js` |
| 5 | `fea4ed7e` | test(workbench): 同步 R-34 删除后的断言（两轮的完成时间都在页面上）—— **主会话补的** | `tests/workbench/test_records.py` |
| 6 | `3eb9f2a1` | fix(workbench): R-54 去掉尾句号 —— 与 copy-table 定稿逐字一致 —— **本棒核对时补的** | `workbench/server/records.py` |
| 7 | （本报告） | docs(v2): IMPL-P26b 报告 —— 文案清理收尾的 27 条逐条核对与记录 | `openspec/…/reports/IMPL-P26b-report.md` |

> 同区间还有两个**交接文档**提交（`20b46e91` / `4fd3022b`，`docs/STATUS-…-2026-10-23.md`），
> 不属于文案工作本身，列在这里只为说明 HEAD 的连续性。
>
> **并发 owner 的提交（在本棒写报告期间落库）**：
> `3bfbb27d`（A-121 两族死规则 + IMPL-C2 取消）· `c1313468`（**勾上 tasks 26.1 / 26.2 / 26.3**）·
> `639b9072`（A-122 P24.1 降级）· `197e7e75`（**IMPLEMENTATION-LOG §9.44**）· `e65bb2a1`（P23 brief 补前置核实）。
> 这 5 个 commit **只动 `IMPLEMENTATION-LOG.md` / `tasks.md` / `decisions.md` / `briefs/`，零产品代码**，
> **本棒没有碰、也没有提交它们**。
> ⚠️ **口径差**：owner 在 §9.44 与 `tasks.md` 里写的文本数是 **585 → 563 / 2989 → 2361**
> （= **P26 交工时**的数字）；本报告 §6 给的是**最终数字 585 → 561 / 2989 → 2320**
> （含 P26b 这 25 条 + A-120 两条的净效果）。两者**不冲突，是同一条曲线的两个时点**。

**A-90 核对**：本棒自己只产生 2 个 commit（`3eb9f2a1` 与本报告），**都是
`git add -- <明确路径>` + `git commit -m ... -- <明确路径>`**；
**没有一次 `git add -A` / `git add -a` / `git add <目录>` / 不带路径的 `git commit`**。
并发 CSS agent 的 `workbench/server/static/workbench.css` 在工作区里一直是 `M` 状态，
**从未被卷进本棒任何 commit**（已用 `git show --name-only` 逐个复核 6 个 commit 的文件列表）。

**改动面实测**（`git diff --stat 5f8440db..3eb9f2a1`，**只列本棒动的文件**）：

```
 openspec/changes/workbench-visual-language-v2/design-notes/copy-table.md     |  2 +-
 tests/workbench/test_records.py                                             | 13 +-
 tests/workbench/test_ui_routes.py                                           |  4 +-
 tests/workbench/workbench_ui_interactions.test.js                           |  2 +-
 workbench/server/experience_page.py                                         |  6 +-
 workbench/server/pages.py                                                   |  2 +-
 workbench/server/records.py                                                 | 47 ++++++----
 workbench/server/static/agent-ui.js                                          |  4 +-
 workbench/server/static/workbench.js                                        |  4 +-
```

> ⚠️ **区间里混进了并发 owner 的 5 个 commit**（`3bfbb27d` A-121 / `c1313468` 勾 tasks 26.1-26.3 /
> `639b9072` A-122 / `197e7e75` log §9.44 / `e65bb2a1` P23 brief）——
> 它们在本棒写报告期间落库，**动的是 `IMPLEMENTATION-LOG.md` / `tasks.md` / `decisions.md` /
> `briefs/`，零产品代码**。本棒**没有碰它们**，它们也不在本棒任何 commit 里。
> ⇒ 上面的 stat 是**手工从区间 diff 里挑出本棒动的 9 个文件**得到的，不是整区间的 stat。

---

## 2. 27 条逐条「改前 → 改后 + 证据行号 + 落地方式」

> **口径说明**：任务书写「25 条」，但它自己枚举的是 19（台账）+ 6（A-119）+ 2（A-120）= **27**。
> 本报告按 **27** 交付。
> **行号一律是本棒落地之后当场 `grep -n` 实测的当前行号**（不是台账里的旧行号）；
> 「删」类条目因为目标已不存在，行号给的是**基线 `5f8440db` 里的旧行号**并注明。

### 2.1 台账 19 条（`records.py` 16 条 + `experience_page.py` 3 条）

> 这 19 条 = 上一波 P26 §2.1 登记的「文件不在本组可写范围」的 19 条
> （`records.py` 16 + `experience_page.py` 3）。
> A-119 裁定的 **R-28 / R-31 / R-41**（也落在 `records.py`）不在本表，列在 §2.2。

| # | ID | 文件 | 改前 | 改后 | 证据（实测行号） | 落地方式 |
|---|---|---|---|---|---|---|
| 1 | **R-06** | `records.py` | 这里还没有记录。 | 暂无记录 | `records.py:122` | **改** |
| 2 | **R-26** | `records.py` | 还没有完整的练习轮次记录。 | 暂无练习轮次 | `records.py:191` | **改** |
| 3 | **R-34** | `records.py` | 这张试卷的题目或顺序曾变化；下面按每次实际内容分别显示，不合并成一条趋势。 | **（删除）** | 基线 `5f8440db:records.py:232-235`；现 `records.py` 内该串 **0 命中** | **删** |
| 4 | **R-36** | `records.py` | 同一试卷（kicker） | **（删除）** | 基线 `5f8440db:records.py:247`；现 **0 命中** | **删** |
| 5 | **R-38** | `records.py` | 只使用每次实际留下的作答、自评和不会记录。 | **（删除）** | 基线 `5f8440db:records.py:248`；现 **0 命中** | **删** |
| 6 | **R-44** | `records.py` | 最近 14 天还没有作答。 | 最近 14 天暂无作答 | `records.py:445` | **改** |
| 7 | **R-45** | `records.py` | 最近 12 周还没有作答。 | 最近 12 周暂无作答 | `records.py:549` | **改** |
| 8 | **R-49** | `records.py` | 还没有带自评的作答。 | 暂无带自评的作答 | `records.py:583` | **改** |
| 9 | **R-54** | `records.py` | 正在按单题过滤。 | 按单题过滤 | `records.py:633`（+ `635` 链接行） | **改**（尾句号由本棒补，见 §8.3） |
| 10 | **R-57** | `records.py` | 练习 / 试卷（kicker） | **（删除）** | 基线 `5f8440db:records.py:651`；现 **0 命中**（kicker 形态） | **删** |
| 11 | **R-58** | `records.py` | 每一轮做了什么 | 练习轮次 | `records.py:649`（`<h2>练习轮次</h2>`） | **改** |
| 12 | **R-59** | `records.py` | 完成或替换一轮练习后保留快照；试卷记录保留当时的试卷名称。 | **（删除）** | 基线 `5f8440db:records.py:652`；现 **0 命中** | **删** |
| 13 | **R-60** | `records.py` | 作答明细（kicker） | **（删除）** | 基线 `5f8440db:records.py:659`；现 **0 命中**（kicker 形态） | **删** |
| 14 | **R-62** | `records.py` | N 条已载入。 | N 条 | `records.py:657` | **改** |
| 15 | **R-63** | `records.py` | 错题（kicker） | **（删除）** | 基线 `5f8440db:records.py:667`；现 **0 命中**（kicker 形态） | **删** |
| 16 | **R-64** | `records.py` | 需要回看的作答 | 错题 | `records.py:664`（`<h2>错题</h2>`） | **改** |
| 17 | **E-03** | `experience_page.py` | 暂无经验总结。做题后可以把可复用的方法、易错点和判断经验沉淀在这里。 | 暂无经验总结 | `experience_page.py:64` | **改** |
| 18 | **E-05** | `experience_page.py` | 做题沉淀（kicker） | **（删除）** | 基线 `5f8440db:experience_page.py:73`；现 **0 命中** | **删** |
| 19 | **E-10** | `experience_page.py` | 进入编辑后载入关联题目。 | **（删除）** | 基线 `5f8440db:experience_page.py:84`；现 `experience_page.py:84` 是 `<div id='experience-problem-choices'></div>`（空容器） | **删** |

> ⚠️ **同名不同位**：R-57 的「练习 / 试卷」、R-60 的「作答明细」、R-63 的「错题」
> 在 `records.py` 里**还各有一处同名文本**（视图页签 R-52 与概览 h2 R-73）——
> 那两处 copy-table 判「**留**」，**必须保留**，本次**一个字没动**。
> 逐条核对：R-52 = `records.py:602-604`（页签数组）、R-73 = `records.py:692`（概览 h2）。

### 2.2 A-119 六条裁定

> 这 6 条 = 上一波 P26 §2.1 登记的「任务书点名不许动」的 6 条待裁决项。
> A-119（`decisions.md` §A-119）逐条取证后全部照准。

| # | ID | 文件 | 改前 | 改后 | 证据（实测行号） | 落地方式 |
|---|---|---|---|---|---|---|
| 20 | **P-163** | `pages.py` | 练习显示自评 | **练习与试卷显示自评** | `pages.py:997` | **改**（A-119 裁定的用词，非定稿原文的「组卷」；设计件已由 `94ac6370` 同步；**spec / MANUAL / GLOSSARY 未同步 ⇒ 见 §8.1**） |
| 21 | **W-105** | `static/workbench.js` | Check 入库已回滚 | 入库已回滚 | `workbench.js:4861` | **译** |
| 22 | **A-13** | `static/agent-ui.js` | 打开组卷页 | 打开试卷页 | `agent-ui.js:267` | **译** |
| 23 | **R-28** | `records.py` | 最近正确率 — ／ 最近正确率 N% | 最近判定 — ／ 最近判定 N/M | `records.py:205-207` | **改（只改呈现）** |
| 24 | **R-31** | `records.py` | 正确 — ／ 正确 N/M | 判定 — ／ 判定正确 N/M | `records.py:220-222` | **改（只改呈现）** |
| 25 | **R-41** | `records.py` | 客观题正确率 ／ N% | 客观题判定 ／ N/M | `records.py:358-360` | **改（只改呈现）**（**MANUAL 未同步 ⇒ 见 §8.2**） |

> R-28 / R-31 / R-41 的「口径一个字不许动」核对见 **§5.3**。

### 2.3 A-120 两条漏收文案

> 这 2 条 = 上一波 P26 §8.2 诚实登记的「台账漏收」（纯英文界面文案）。
> A-120（`decisions.md` §A-120）裁定照准，并已补进台账 §3.14。

| # | ID | 文件 | 改前 | 改后 | 证据（实测行号） | 落地方式 |
|---|---|---|---|---|---|---|
| 26 | **P-209** | `static/agent-ui.js` | `Artifact · Paper` | 工件 · 试卷 | `agent-ui.js:308` | **译** |
| 27 | **P-210** | `static/workbench.js` | `Paper：` | 试卷： | `workbench.js:3732` | **译** |

> 两条都**只改界面字符串**：类名（`agent-surface-kicker` / `ai-paper-approval-paper`）、
> id、载荷键一个字没动（`git diff` 实测，见 §5.1）。

**合计 27 条 = 19（台账）+ 6（A-119）+ 2（A-120）。**

---

## 3. 删除类条目的「删除前后信息量核对表」

台账 §6.2 的「删」类共 **27** 条：上一波落 **18** 条（见 `IMPL-P26-report.md` §3），
**本棒落 9 条**。下表是本棒的 9 条 —— 每条写「**删了什么 / 由什么承担**」，
「由什么承担」一栏**逐字取自 copy-table §3**（台账转述，设计件是权威）。

| # | ID | 文件 | 删了什么 | **删后由什么承担**（copy-table §3） | 本棒状态 | 落点 |
|---|---|---|---|---|---|---|
| 1 | **R-34** | `records.py` | 这张试卷的题目或顺序曾变化；下面按每次实际内容分别显示，不合并成一条趋势。 | 每轮一张卡片（天然分开，不合并） | **已删** | `records.py` 内 `content_changed` 分支整段移除（连 `changed = (...)` 变量一起） |
| 2 | **R-36** | `records.py` | 同一试卷（kicker） | `多次练习` 标题 | **已删** | `records.py:243` 现在是 `<h2>多次练习</h2>`，kicker 连元素一起删 |
| 3 | **R-38** | `records.py` | 只使用每次实际留下的作答、自评和不会记录。 | 每轮卡片里的计数与 `正确 N/M` / `自评 N/5` / `不会 N 个` | **已删** | 同上；计数现在由每轮 `<li>` 承担（且 `正确 N/M` 已按 R-31 改称 `判定正确 N/M`） |
| 4 | **R-57** | `records.py` | 练习 / 试卷（kicker） | `练习轮次` 标题 | **已删** | `records.py:649` 现在是 `<h2>练习轮次</h2>` |
| 5 | **R-59** | `records.py` | 完成或替换一轮练习后保留快照；试卷记录保留当时的试卷名称。 | 卡片上的时间戳 + 试卷名 | **已删** | 同上；时间戳 = 每轮的 `<time>{finished_at}</time>`，试卷名 = 卡片 `<h3>` |
| 6 | **R-60** | `records.py` | 作答明细（kicker） | `逐题记录` 标题 | **已删** | `records.py:656` 现在是 `<h2>逐题记录</h2>` |
| 7 | **R-63** | `records.py` | 错题（kicker） | `错题` 标题 | **已删** | `records.py:664` 现在是 `<h2>错题</h2>` |
| 8 | **E-05** | `experience_page.py` | 做题沉淀（kicker） | `做题经验` 标题 | **已删** | `experience_page.py:73` 现在是 `<h2>做题经验</h2>` |
| 9 | **E-10** | `experience_page.py` | 进入编辑后载入关联题目。 | fieldset 标题 `典型题目（可选）` + 载入中占位 `正在载入关联题目…` | **已删** | `experience_page.py:84` 现在是 `<div id='experience-problem-choices'></div>`（**空容器**，fieldset 的 `<legend>典型题目（可选）</legend>` 保留；载入中占位由 JS 写） |

**核对结论**：9 条全部是**整段删除**（连同 `class` / 元素一起删），**没有一条被改写成另一句说明性文字**
—— 26.2 的「少字原则删注释」口径成立。
9 条的「删后由什么承担」在代码里**逐条可验**（标题 / 计数 / 时间戳 / 空容器由 JS 填）。

### 3.1 ⚠️ 必须明确记下的产品后果 ①：**R-34 删掉那句说明后，「试卷内容有变化」在界面上不再有任何提示**

| 事实 | 状态 |
|---|---|
| 数据层 `content_changed` 字段 | **仍然存在**（`workbench/data/records.py` 计算，测试 `test_records.py:122` 仍断言 `assertTrue` / `:226` 仍断言 `assertFalse`） |
| 界面提示 | **已删除，且无任何替代提示** —— `records.py` 里 `content_changed` 分支整段移除，全仓库 `grep -F "题目或顺序曾变化"` = **0 命中** |
| 后果 | 学习者在「多次练习」页**看不出**这张试卷这一轮和上一轮的内容是否变过；两轮只是各自一条 `<li>`（时间戳 + 判定 + 自评 + 不会） |

**这是 copy-table 定稿的结果，不是实现漏做。** 本报告**如实记下，不自行加回提示**。
若所有者认为「内容变过」这件事对学习者有价值，需要**新开一条 change**（改 copy-table 的
R-34「删后由什么承担」那一栏，再落地 UI 提示）—— **不是**本棒该顺手做的事。

### 3.2 ⚠️ 必须明确记下的产品后果 ②：**R-28 / R-31 / R-41 只改了呈现**

**被计数的口径、统计行、请求序列一个字没动。** 证据见 §5.3 的渲染对照表。

---

## 4. 两条 grep 复核的原样输出

台账 §6.1 给的两条验收口径，**原样跑、原样贴**。

### 4.1 复核一

```bash
grep -rn --exclude="*.pyc" "Paper\|Agent activity\|Artifact\|Congratulations\|Check 入库\|Yes / No\|AI生成" \
  workbench/server/ | grep -v "^\s*#"
```

**原样输出 190 行**（下面整块是未经加工的原始输出；Git Bash 把路径分隔符渲染成 `\`，上一波存档用的是 `/`）：

```
workbench/server/\api.py:530:        raise ApiError(409, 'stale draft: reload the current Paper')
workbench/server/\pages.py:317:    """Practise a saved Paper; authoring is delegated to Agent/CLI."""
workbench/server/\static\agent-ui.css:428:/* Artifact = durable result handoff. The chat card is the record; Adaptive Split
workbench/server/\static\agent-ui.js:16:    latestArtifact: null,
workbench/server/\static\agent-ui.js:17:    renderedArtifacts: {},
workbench/server/\static\agent-ui.js:125:  function setArtifactPreviewHandler(handler) {
workbench/server/\static\agent-ui.js:238:  function cleanArtifact(raw) {
workbench/server/\static\agent-ui.js:271:  function openArtifact(raw, explicit) {
workbench/server/\static\agent-ui.js:272:    var action = cleanArtifact(raw);
workbench/server/\static\agent-ui.js:274:    state.latestArtifact = action;
workbench/server/\static\agent-ui.js:299:  function renderArtifactCard(action) {
workbench/server/\static\agent-ui.js:301:    if (!messages || state.renderedArtifacts[action.practice_set_id]) return;
workbench/server/\static\agent-ui.js:302:    state.renderedArtifacts[action.practice_set_id] = true;
workbench/server/\static\agent-ui.js:327:    preview.addEventListener("click", function () { openArtifact(action, true); });
workbench/server/\static\agent-ui.js:335:    var action = cleanArtifact(raw);
workbench/server/\static\agent-ui.js:337:    state.latestArtifact = action;
workbench/server/\static\agent-ui.js:338:    renderArtifactCard(action);
workbench/server/\static\agent-ui.js:339:    if (!(options && options.restore)) openArtifact(action, false);
workbench/server/\static\agent-ui.js:408:    state.renderedArtifacts = {};
workbench/server/\static\agent-ui.js:409:    state.latestArtifact = null;
workbench/server/\static\agent-ui.js:425:    state.latestArtifact = null;
workbench/server/\static\agent-ui.js:469:    openArtifact: openArtifact,
workbench/server/\static\agent-ui.js:472:    setArtifactPreviewHandler: setArtifactPreviewHandler,
workbench/server/\static\practice-flow.js:701:    function isPaperReviewItem(item) {
workbench/server/\static\practice-flow.js:707:      if (isPaperReviewItem(item)) {
workbench/server/\static\practice-flow.js:718:      return isPaperReviewItem(item)
workbench/server/\static\practice-flow.js:981:        var paperReview = isPaperReviewItem(item);
workbench/server/\static\practice-flow.js:1054:      var paperReview = reviewOnly && isPaperReviewItem(item);
workbench/server/\static\practice-flow.js:1381:    function saveCurrentSelectionAsPaper() {
workbench/server/\static\practice-flow.js:1539:      savePracticeSet.addEventListener("click", saveCurrentSelectionAsPaper);
workbench/server/\static\practice-flow.js:1760:      if (!isPaperReviewItem(item) || !item.attempt_id || offNow()) return;
workbench/server/\static\practice-flow.js:1793:      if (reviewingItem && (!isPaperReviewItem(item) || !ratingEditOpen)) return;
workbench/server/\static\practice-flow.js:1933:          if (!isPaperReviewItem(contextProblem())) return;
workbench/server/\static\practice-flow.js:2221:    if (document.getElementById("paper-practice") && typeof PaperPractice !== "undefined") {
workbench/server/\static\practice-flow.js:2222:      return PaperPractice.start(deps, function () { return startLegacy(deps); });
workbench/server/\static\paper-practice.js:1:/* PaperPractice — browser controller for freely navigable saved-Paper runs. */
workbench/server/\static\paper-practice.js:3:  root.PaperPractice = factory();
workbench/server/\static\paper-practice.js:59:    var requestedPaperId = address.searchParams.get("paper") || "";
workbench/server/\static\paper-practice.js:61:    var savedPaper = null;
workbench/server/\static\paper-practice.js:188:    function isPaperRun(record) {
workbench/server/\static\paper-practice.js:196:    function isSavedPaperRun(record) {
workbench/server/\static\paper-practice.js:308:      var shouldAdoptMode = !isArchived && !record.reveal_timing && isPaperRun(record);
workbench/server/\static\paper-practice.js:366:      savedPaper = record;
workbench/server/\static\paper-practice.js:398:    function initializePaper(paperId) {
workbench/server/\static\paper-practice.js:420:        if (isPaperRun(current)) {
workbench/server/\static\paper-practice.js:439:      savedPaper = null;
workbench/server/\static\paper-practice.js:464:      if (!savedPaper || !ids.start || ids.start.disabled) return Promise.resolve();
workbench/server/\static\paper-practice.js:467:      var continuation = savedPaper.continuation;
workbench/server/\static\paper-practice.js:475:          source_label: replay.source_label || savedPaper.title || "练习试卷",
workbench/server/\static\paper-practice.js:496:        startRequest = post("/practice-sets/" + encodeURIComponent(savedPaper.practice_set_id) + "/start", body);
workbench/server/\static\paper-practice.js:642:      var paperTitle = run.source_label || (savedPaper && savedPaper.title) || "练习试卷";
workbench/server/\static\paper-practice.js:1285:    function submitPaper(retry) {
workbench/server/\static\paper-practice.js:1335:        submitPaper(local.pendingFinalize);
workbench/server/\static\paper-practice.js:1472:      if (ids.title) ids.title.textContent = archived.source_label || savedPaper && savedPaper.title || "练习试卷";
workbench/server/\static\paper-practice.js:1525:        if (!isSavedPaperRun(run)) return null;
workbench/server/\static\paper-practice.js:1551:    if (ids.finalSubmit) ids.finalSubmit.addEventListener("click", function () { submitPaper(); });
workbench/server/\static\paper-practice.js:1567:      if (archived && isPaperRun(archived) && !isSavedPaperRun(archived)) {
workbench/server/\static\paper-practice.js:1570:        savedPaper = {
workbench/server/\static\paper-practice.js:1579:          requestedPaperId = "";
workbench/server/\static\paper-practice.js:1592:        showSetup(savedPaper);
workbench/server/\static\paper-practice.js:1595:      var paperId = (archived && archived.source_ref) || requestedPaperId;
workbench/server/\static\paper-practice.js:1604:        requestedPaperId = paperId;
workbench/server/\static\paper-practice.js:1701:    else if (requestedPaperId) initializePaper(requestedPaperId);
workbench/server/\static\workbench.js:536:     flow** — the quick-practice flow reads the micro-quiz verdict, the Paper
workbench/server/\static\workbench.js:3089:  function restorePaperFolds() {
workbench/server/\static\workbench.js:3118:  function downloadPaper(title, suffix, text) {
workbench/server/\static\workbench.js:3132:    restorePaperFolds();
workbench/server/\static\workbench.js:3174:          downloadPaper(title, "-problem-set.md", rendered.practice_set || "");
workbench/server/\static\workbench.js:3175:          downloadPaper(title, "-solutions.md", rendered.solutions || "");
workbench/server/\static\workbench.js:3374:  var aiLiveArtifactId = "";
workbench/server/\static\workbench.js:3395:  var aiCurrentPaperApproval = null;
workbench/server/\static\workbench.js:3396:  var aiPaperApprovalOwner = null;
workbench/server/\static\workbench.js:3397:  var aiPaperApprovalNotice = null;
workbench/server/\static\workbench.js:3398:  var aiPaperApprovalUnknownKey = "";
workbench/server/\static\workbench.js:3399:  var aiPaperApprovalInFlight = {};
workbench/server/\static\workbench.js:3400:  var aiPaperProposalCards = {};
workbench/server/\static\workbench.js:3408:  function aiClearLiveArtifact() {
workbench/server/\static\workbench.js:3412:  function aiForgetLiveArtifact() {
workbench/server/\static\workbench.js:3413:    aiLiveArtifactId = "";
workbench/server/\static\workbench.js:3414:    aiClearLiveArtifact();
workbench/server/\static\workbench.js:3417:  function aiGetLiveArtifact(conversationId) {
workbench/server/\static\workbench.js:3422:      aiForgetLiveArtifact();
workbench/server/\static\workbench.js:3425:    aiLiveArtifactId = marker.practice_set_id;
workbench/server/\static\workbench.js:3429:  function aiSaveLiveArtifact(action) {
workbench/server/\static\workbench.js:3431:    aiLiveArtifactId = action.practice_set_id;
workbench/server/\static\workbench.js:3439:  function aiHasLiveArtifact(conversationId, practiceSetId) {
workbench/server/\static\workbench.js:3440:    var marker = aiGetLiveArtifact(conversationId);
workbench/server/\static\workbench.js:3444:  if (aiConversation) aiGetLiveArtifact(aiConversation);
workbench/server/\static\workbench.js:3445:  else aiForgetLiveArtifact();
workbench/server/\static\workbench.js:3447:  function aiResetConversationRuntime(preserveLiveArtifactConversationId) {
workbench/server/\static\workbench.js:3449:    if (preserveLiveArtifactConversationId) {
workbench/server/\static\workbench.js:3450:      aiGetLiveArtifact(preserveLiveArtifactConversationId);
workbench/server/\static\workbench.js:3452:      aiForgetLiveArtifact();
workbench/server/\static\workbench.js:3479:    aiCurrentPaperApproval = null;
workbench/server/\static\workbench.js:3480:    aiPaperApprovalOwner = null;
workbench/server/\static\workbench.js:3481:    aiPaperApprovalNotice = null;
workbench/server/\static\workbench.js:3482:    aiPaperApprovalUnknownKey = "";
workbench/server/\static\workbench.js:3483:    aiPaperProposalCards = {};
workbench/server/\static\workbench.js:3491:    AgentUISurfaces.setCollapseHandler(aiClearLiveArtifact);
workbench/server/\static\workbench.js:3493:  if (typeof AgentUISurfaces !== "undefined" && AgentUISurfaces.setArtifactPreviewHandler) {
workbench/server/\static\workbench.js:3494:    AgentUISurfaces.setArtifactPreviewHandler(function (action) {
workbench/server/\static\workbench.js:3495:      if (action && action.practice_set_id === aiLiveArtifactId) aiSaveLiveArtifact(action);
workbench/server/\static\workbench.js:3701:  function aiPaperApprovalDecisionKey(conversationId, approval) {
workbench/server/\static\workbench.js:3706:  function aiPaperApprovalProposalKey(conversationId, approval) {
workbench/server/\static\workbench.js:3710:  function aiPaperText(host, tag, className, value) {
workbench/server/\static\workbench.js:3718:  function aiPaperOrder(host, label, ids) {
workbench/server/\static\workbench.js:3720:    aiPaperText(host, "p", "ai-paper-approval-order-label", label);
workbench/server/\static\workbench.js:3724:      aiPaperText(list, "li", "", String(id));
workbench/server/\static\workbench.js:3729:  function aiPaperApprovalDetails(host, approval, fallbackProposedIds) {
workbench/server/\static\workbench.js:3732:    aiPaperText(host, "p", "ai-paper-approval-paper", "试卷：" + title
workbench/server/\static\workbench.js:3741:    aiPaperText(host, "p", "ai-paper-approval-change", changes.join("；"));
workbench/server/\static\workbench.js:3743:      aiPaperOrder(host, "当前顺序", approval.current_problem_ids);
workbench/server/\static\workbench.js:3747:    aiPaperOrder(host, "更新后顺序", proposedIds);
workbench/server/\static\workbench.js:3749:      aiPaperText(host, "p", "ai-paper-approval-impact",
workbench/server/\static\workbench.js:3754:      aiPaperText(host, "p", "ai-paper-approval-impact",
workbench/server/\static\workbench.js:3759:  function aiPaperActionStatus(approval) {
workbench/server/\static\workbench.js:3767:  function aiRenderPaperProposalHistory(action, turnId) {
workbench/server/\static\workbench.js:3772:    var card = aiPaperProposalCards[id];
workbench/server/\static\workbench.js:3776:      aiPaperProposalCards[id] = card;
workbench/server/\static\workbench.js:3780:    aiPaperText(card, "strong", "ai-paper-approval-history-title",
workbench/server/\static\workbench.js:3782:    aiPaperText(card, "p", "ai-paper-approval-history-status", aiPaperActionStatus(approval));
workbench/server/\static\workbench.js:3784:      aiPaperText(card, "p", "ai-paper-approval-impact",
workbench/server/\static\workbench.js:3786:      if (Array.isArray(action.problem_ids)) aiPaperOrder(card, "提议顺序", action.problem_ids);
workbench/server/\static\workbench.js:3789:    aiPaperApprovalDetails(card, Object.assign({}, approval, {
workbench/server/\static\workbench.js:3794:  function aiUpdatePaperProposalHistory(record) {
workbench/server/\static\workbench.js:3798:        aiRenderPaperProposalHistory(action, message.turn_id);
workbench/server/\static\workbench.js:3800:      aiRenderPaperProposalHistory(message.action, message.turn_id);
workbench/server/\static\workbench.js:3804:  function aiSetPaperApprovalOwner(record) {
workbench/server/\static\workbench.js:3808:      aiPaperApprovalOwner = {
workbench/server/\static\workbench.js:3822:        aiPaperApprovalOwner = {
workbench/server/\static\workbench.js:3831:    aiPaperApprovalOwner = null;
workbench/server/\static\workbench.js:3834:  function aiRenderPaperApproval(approval) {
workbench/server/\static\workbench.js:3843:    aiCurrentPaperApproval = current;
workbench/server/\static\workbench.js:3850:      aiPaperApprovalNotice = null;
workbench/server/\static\workbench.js:3851:      aiPaperApprovalUnknownKey = "";
workbench/server/\static\workbench.js:3854:    var proposalKey = aiPaperApprovalProposalKey(aiConversation, current);
workbench/server/\static\workbench.js:3855:    var decisionKey = aiPaperApprovalDecisionKey(aiConversation, current);
workbench/server/\static\workbench.js:3856:    var inFlight = !!aiPaperApprovalInFlight[proposalKey];
workbench/server/\static\workbench.js:3857:    var unknown = aiPaperApprovalUnknownKey === decisionKey;
workbench/server/\static\workbench.js:3858:    var notice = aiPaperApprovalNotice;
workbench/server/\static\workbench.js:3863:      aiPaperApprovalNotice = null;
workbench/server/\static\workbench.js:3868:    if (details) aiPaperApprovalDetails(details, current);
workbench/server/\static\workbench.js:3873:  function aiPaperApprovalDecisionOwnerMatches(context, revision) {
workbench/server/\static\workbench.js:3874:    var owner = aiPaperApprovalOwner;
workbench/server/\static\workbench.js:3884:  function aiDecidePaperApproval(decision) {
workbench/server/\static\workbench.js:3885:    var approval = aiCurrentPaperApproval;
workbench/server/\static\workbench.js:3893:    var proposalKey = aiPaperApprovalProposalKey(conversationId, approval);
workbench/server/\static\workbench.js:3894:    var decisionKey = aiPaperApprovalDecisionKey(conversationId, approval);
workbench/server/\static\workbench.js:3895:    if (aiPaperApprovalInFlight[proposalKey] || aiPaperApprovalUnknownKey === decisionKey) return;
workbench/server/\static\workbench.js:3896:    aiPaperApprovalInFlight[proposalKey] = decisionKey;
workbench/server/\static\workbench.js:3897:    aiPaperApprovalNotice = {
workbench/server/\static\workbench.js:3902:    aiRenderPaperApproval(approval);
workbench/server/\static\workbench.js:3915:      if (!responseMatches || !aiPaperApprovalDecisionOwnerMatches(context, responseRevision)) {
workbench/server/\static\workbench.js:3919:        aiPaperApprovalOwner = {
workbench/server/\static\workbench.js:3925:        aiPaperApprovalNotice = {
workbench/server/\static\workbench.js:3931:        aiRenderPaperApproval(responseApproval);
workbench/server/\static\workbench.js:3933:        aiPaperApprovalNotice = null;
workbench/server/\static\workbench.js:3938:      if (aiPaperApprovalDecisionOwnerMatches(context)) {
workbench/server/\static\workbench.js:3939:        aiPaperApprovalNotice = {
workbench/server/\static\workbench.js:3947:      if (!aiPaperApprovalDecisionOwnerMatches(context,
workbench/server/\static\workbench.js:3952:          var unresolved = aiCurrentPaperApproval || approval;
workbench/server/\static\workbench.js:3953:          var unresolvedKey = aiPaperApprovalDecisionKey(conversationId, unresolved);
workbench/server/\static\workbench.js:3954:          aiPaperApprovalUnknownKey = unresolvedKey;
workbench/server/\static\workbench.js:3955:          aiPaperApprovalNotice = {
workbench/server/\static\workbench.js:3960:          aiRenderPaperApproval(aiCurrentPaperApproval);
workbench/server/\static\workbench.js:3967:          aiPaperApprovalNotice = {
workbench/server/\static\workbench.js:3976:      if (aiPaperApprovalInFlight[proposalKey] === decisionKey) {
workbench/server/\static\workbench.js:3977:        delete aiPaperApprovalInFlight[proposalKey];
workbench/server/\static\workbench.js:3980:        aiRenderPaperApproval(aiCurrentPaperApproval);
workbench/server/\static\workbench.js:4213:      aiSetPaperApprovalOwner(record);
workbench/server/\static\workbench.js:4214:      aiUpdatePaperProposalHistory(record);
workbench/server/\static\workbench.js:4215:      aiRenderPaperApproval(record.pending_paper_approval);
workbench/server/\static\workbench.js:4486:            aiForgetLiveArtifact();
workbench/server/\static\workbench.js:4767:      aiLiveArtifactId = action.practice_set_id || "";
workbench/server/\static\workbench.js:4770:        if (AgentUISurfaces.artifact(action) && previewAllowed) aiSaveLiveArtifact(action);
workbench/server/\static\workbench.js:4771:        else aiClearLiveArtifact();
workbench/server/\static\workbench.js:5046:    aiPaperProposalCards = {};
workbench/server/\static\workbench.js:5057:    aiSetPaperApprovalOwner(record);
workbench/server/\static\workbench.js:5101:            aiRenderPaperProposalHistory(restored, message.turn_id);
workbench/server/\static\workbench.js:5110:          var livePreview = aiHasLiveArtifact(
workbench/server/\static\workbench.js:5116:          aiRenderPaperProposalHistory(message.action, message.turn_id);
workbench/server/\static\workbench.js:5122:    aiRenderPaperApproval(record.pending_paper_approval);
workbench/server/\static\workbench.js:5417:        || (aiCurrentPaperApproval && aiCurrentPaperApproval.status === "pending")) return;
workbench/server/\static\workbench.js:5434:  var aiPaperApprovalApprove = document.getElementById("ai-paper-approval-approve");
workbench/server/\static\workbench.js:5435:  var aiPaperApprovalCancel = document.getElementById("ai-paper-approval-cancel");
workbench/server/\static\workbench.js:5436:  if (aiPaperApprovalApprove) aiPaperApprovalApprove.addEventListener("click", function () {
workbench/server/\static\workbench.js:5437:    aiDecidePaperApproval("approve");
workbench/server/\static\workbench.js:5439:  if (aiPaperApprovalCancel) aiPaperApprovalCancel.addEventListener("click", function () {
workbench/server/\static\workbench.js:5440:    aiDecidePaperApproval("cancel");
workbench/server/\static\workbench.css:4772:/* 题号格的状态几何（INC-05 · A-94 · spec「Accessible Paper status dots」）------
```

**逐类归因**（本棒只对自己的文件负责）：

| 类别 | 命中 | 是不是界面文案 |
|---|---|---|
| 变量名 / 函数名 / 协议字段（`aiPaperApproval*` / `savedPaper` / `isPaperRun` / `downloadPaper` / `PaperPractice` / `renderArtifactCard` / `aiArtifact` …） | 绝大多数 | ❌ 不是文案（台账 §6.1 明示：「`workbench.js` 里的 `Paper` 有非文案用途——变量名 / 协议字段 / 注释不在此列」） |
| 注释 / docstring（`pages.py:317` `Practise a saved Paper; …`、`workbench.js:536` 注释、`workbench.css` / `agent-ui.css` 里的 CSS 注释） | 5 | ❌ 不渲染 |
| **API 错误串** `api.py:530` `'stale draft: reload the current Paper'` | 1 | ❌ 服务端协议串，**不渲染**；且 `api.py` 不在本变更可写范围（上一波已登记，本棒**未动**） |
| **本棒文件里残留的界面文案** | **0 条** | ✅ |

**与上一波（`IMPL-P26-report.md` §4.1，192 行）逐行对比**（路径分隔符归一后做多重集差集）：

| 变化 | 命中 | 归属 |
|---|---|---|
| 消失 | `agent-ui.js:308 kicker.textContent = "Artifact · Paper";` | **P-209 已落** ✅ |
| 消失 | `workbench.js:3732 aiPaperText(..., "Paper：" + title` | **P-210 已落** ✅ |
| 消失 | `workbench.js:4861 if (title) title.textContent = "Check 入库已回滚";` | **W-105 已落** ✅ |
| 行号平移 | `agent-ui.css:426` → `agent-ui.css:428` | 并发 CSS agent 的在途改动，**不是本棒** |
| 行号平移 | `workbench.css:4524` → `workbench.css:4757` | 并发 CSS agent 的在途改动，**不是本棒** |
| 新增 | `workbench.js:3732 ... "试卷：" + title` | P-210 落地后的新内容 |

⇒ **上一波 §8.2 登记的 2 条「台账漏收」文案 + §8.1 登记的 W-105 待裁决项，全部消干净了。**
上一波 §8.2 里**还没解决的**只剩 `api.py:530` 那条 API 错误串（不在本变更范围）。

### 4.2 复核二

```bash
grep -rn --exclude="*.pyc" "正确率\|客观正确\|熟悉程度\|自评分" workbench/server/
```

**原样输出 7 行**（整块未加工）：

```
workbench/server/\records.py:400:    `.record-rating-*` 留给 `_rating_chart` 的自评分布）。
workbench/server/\records.py:595:    return "<div class='record-rating-chart' aria-label='自评分布'>" + "".join(rows) + "</div>"
workbench/server/\static\paper-practice.js:871:        showError("请输入 1–5 的自评分数。");
workbench/server/\static\workbench.css:3312:/* 自评分布 —— `.record-rating-*` 一族**只归自评**（圆点 / 星级 / 自评分布条）。 */
workbench/server/\static\workbench.css:3320:   自评分布 / 判定分布 / 练习进度三条轨道以前各带一条
workbench/server/\static\workbench.css:3339:   ⚠️ 四条轨道（完成页进度带 / 自评分布 / 判定分布 / 练习进度）**一次改齐**，
workbench/server/\static\workbench.css:4005:   ⚠️ 四条轨道（完成页进度带 / 自评分布 / 判定分布 / 练习进度）**一次改齐**，
```

**逐条归因**（与上一波的 10 行逐行对比）：

| 命中 | 是什么 | 归属 |
|---|---|---|
| `records.py:400` `.record-rating-*` 留给 `_rating_chart` 的自评分布 | **代码注释** | ❌ 不渲染 |
| `records.py:595` `aria-label='自评分布'` | 命中的是「自评**分布**」这个**复合词**里的子串 `自评分`… 确切说是 `自评分布` 的「自评」+「分布」被正则 `自评分` 跨词命中 | ❌ 不是禁用词本身 |
| `paper-practice.js:871` `showError("请输入 1–5 的自评分数。")` | 命中的是「自评**分数**」 | ❌ 复合词，不是禁用词 `自评分` |
| `workbench.css:3312 / 3320 / 3339 / 4005` | CSS 注释里的「自评分布 / 判定分布 / 练习进度」 | ❌ 不渲染 |

**上一波 10 行 → 本棒 7 行，消失的 3 行正是本棒修掉的三处**：

| 消失的上一波命中 | 对应 |
|---|---|
| `records.py:205` `最近正确率 …` | **R-28 已落** ✅ |
| `records.py:257` `客观题正确率` | **R-41 已落** ✅ |
| `records.py:363` `正确率`（`_verdict_ring` 的 docstring） | 随 R-41 一并改为「判定占比」 ✅ |

⇒ **本棒文件里没有 `正确率` / `客观正确` / `熟悉程度` / `自评分` 残留。**

---

## 5. 「除文案清理项外逐字一致」的核对结果

口径 = `acceptance.md` §1「文字内容除文案清理项外应逐字一致」。

### 5.1 第一层 · 源文件改动面（最硬的一层）

`git diff 5f8440db..3eb9f2a1` 在 5 个产品文件上的**全部**增删行（**63 行**，逐行贴出；`git diff --unified=0`）：

```
-            "暂无经验总结。做题后可以把可复用的方法、易错点和判断经验沉淀在这里。"
+            "暂无经验总结"
-        "<p class='section-kicker'>做题沉淀</p><h2>做题经验</h2>"
+        "<h2>做题经验</h2>"
-        "<div id='experience-problem-choices'><p class='muted'>进入编辑后载入关联题目。</p></div>"
+        "<div id='experience-problem-choices'></div>"
-        "练习显示自评</label>"
+        "练习与试卷显示自评</label>"
-    return "".join(rows) or "<p class='muted'>这里还没有记录。</p>"
+    return "".join(rows) or "<p class='muted'>暂无记录</p>"
-    return "".join(items) or "<p class='muted'>还没有完整的练习轮次记录。</p>"
+    return "".join(items) or "<p class='muted'>暂无练习轮次</p>"
-            "最近正确率 —" if accuracy is None else f"最近正确率 {accuracy * 100:.0f}%",
+            "最近判定 —" if accuracy is None else (
+                f"最近判定 {latest.get('correct') or 0}/"
+                f"{latest.get('judged') or 0}"),
-                    "正确 —"
+                    "判定 —"
-                    else f"正确 {run.get('correct') or 0}/{run.get('judged') or 0}"
+                    else f"判定正确 {run.get('correct') or 0}/{run.get('judged') or 0}"
-        changed = (
-            "<p class='record-filter-note'>这张试卷的题目或顺序曾变化；"
-            "下面按每次实际内容分别显示，不合并成一条趋势。</p>"
-            if item.get("content_changed") else ""
-        )
-            + changed
-            + "<ul>"
+            "<ul>"
-        "<p class='section-kicker'>同一试卷</p><h2>多次练习</h2></div>"
-        "<p>只使用每次实际留下的作答、自评和不会记录。</p></div>"
+        "<h2>多次练习</h2></div>"
-    整圈 = 已判定的作答数，所以墨色弧的占比就是卡片上的正确率；
+    整圈 = 已判定的作答数，所以墨色弧的占比就是卡片上的判定占比；
-        ("客观题正确率", "—" if accuracy is None else f"{accuracy * 100:.0f}%"),
+        ("客观题判定", "—" if accuracy is None else (
+            f"{int(summary.get('correct') or 0)}/{int(summary.get('judged') or 0)}")),
-        return "<p class='muted'>最近 14 天还没有作答。</p>"
+        return "<p class='muted'>最近 14 天暂无作答</p>"
-        return "<p class='muted'>最近 12 周还没有作答。</p>"
+        return "<p class='muted'>最近 12 周暂无作答</p>"
-        return "<p class='muted'>还没有带自评的作答。</p>"
+        return "<p class='muted'>暂无带自评的作答</p>"
-            "<p class='record-filter-note'>正在按单题过滤。"
+            # R-54（copy-table 定稿）：`按单题过滤` —— 去掉"正在"与句号，
+            # 作为状态标签而非叙述句（copy-table §2.8 R-54）。
+            "<p class='record-filter-note'>按单题过滤"
-            "<p class='section-kicker'>练习 / 试卷</p><h2>每一轮做了什么</h2></div>"
-            "<p>完成或替换一轮练习后保留快照；试卷记录保留当时的试卷名称。</p></div>"
+            "<h2>练习轮次</h2></div>"
-            "<p class='section-kicker'>作答明细</p><h2>逐题记录</h2></div>"
-            f"<p>{len(records)} 条已载入。</p></div>"
+            "<h2>逐题记录</h2></div>"
+            f"<p>{len(records)} 条</p></div>"
-            "<p class='section-kicker'>错题</p><h2>需要回看的作答</h2></div>"
+            "<h2>错题</h2></div>"
-    link.textContent = "打开组卷页";
+    link.textContent = "打开试卷页";
-    kicker.textContent = "Artifact · Paper";
+    kicker.textContent = "工件 · 试卷";
-    aiPaperText(host, "p", "ai-paper-approval-paper", "Paper：" + title
+    aiPaperText(host, "p", "ai-paper-approval-paper", "试卷：" + title
-    if (title) title.textContent = "Check 入库已回滚";
+    if (title) title.textContent = "入库已回滚";
```

**逐条归因**：以上 **63 行**里，**55 行是纯字符串字面量替换 / 删除**，
**4 行是 R-34 删除时一并删掉的代码**（`changed = (` / `if item.get("content_changed") else ""` / `)` / `+ changed`），
**2 行是 `_verdict_ring` 的 docstring 一词**（`正确率` → `判定占比`，**不渲染**，属 R-41 口径的连带清理），
**2 行是本棒给 R-54 加的注释**（不渲染）。⇒ **没有任何一行是逻辑改动。**

**硬约束核对**：

| 硬约束 | 实测 | 结论 |
|---|---|---|
| 类名 / id / DOM 身份未改 | `git diff` 里带 `class=` / `id=` 的行只有「**整元素删除**」与「**同类名替换**」，**没有一处 `class=` 值发生变化** | ✅ |
| 请求序列未改 | diff 里**零** `fetch(` / `.post(` / `method:` 改动 | ✅ |
| 载荷键未改 | diff 里**零** `data-` / 载荷键改动；`ai-paper-approval-paper` 等类名原样 | ✅ |
| 存储未改 | diff 里**零** `localStorage` / `sessionStorage` 改动 | ✅ |
| 统计实现未改 | `_verdict_ring` / `_run_blocks` / `_sparkline` / `_rating_spark` **函数体逐字未变**（只有 docstring 一词） | ✅ |
| 零池写入 | 本棒没碰任何持久化代码 | ✅ |

### 5.2 第二层 · DOM 可见文本节点**有序** diff（基线 vs HEAD）

方法：用 `git worktree` 在 `tmp_local2/p26b/base` 拉出基线 `5f8440db` 的独立检出，
同一套 fixture、同一批路由，分别渲染基线与 HEAD，抽出 HTML 里**全部可见文本节点**
（跳过 `script` / `style` / 内联 SVG），然后做**有序序列 diff**（`difflib.SequenceMatcher`，
不是多重集 —— 多重集会漏掉「顺序变了」的情况）。

"> **注**：本节的节点数与 §6 的**不是同一把尺子** —— 本节**跳过内联 SVG**（`svg` 里的
> `<text>` 不算可见文本节点），§6 用的 `p26_textcount.py` **不跳 SVG**。
> 两把尺子各自的**改前 → 改后**方向完全一致，**绝对值不同**。

> **A-39 核对**：两边的 `workbench` 包与 `tests.workbench.fixtures` 都是从**各自 checkout 的根目录**加载的
> （输出里 echo 了 `__file__`），**没有解析到 site-packages 快照**；
> 另外单独起服务 GET 两个改过的静态文件，**服务字节数 == 磁盘字节数**：
> `agent-ui.js served=16695 disk=16695 identical=True` · `workbench.js served=259469 disk=259469 identical=True`。

**结果：24 个非 equal hunk，全部是本棒的 27 条文案，零条越界改动。**

| 路由 | 基线节点 → HEAD 节点 | 删除的文本节点 | 新增的文本节点 |
|---|---|---|---|
| `/` | 6 → 6 | （无） | （无） |
| `/w/dmath/practice` | 112 → 112 | 练习显示自评 | 练习与试卷显示自评 |
| `/w/dmath/kps` | 73 → 73 | 练习显示自评 | 练习与试卷显示自评 |
| `/w/dmath/kp/dmath-ch06-kp-001` | 66 → 64 | 练习显示自评 / 做题沉淀 / 暂无经验总结。做题后可以把可复用的方法、易错点和判断经验沉淀在这里。 / 进入编辑后载入关联题目。 | 练习与试卷显示自评 / 暂无经验总结 |
| `/w/dmath/practice-sets` | 57 → 57 | 练习显示自评 | 练习与试卷显示自评 |
| `/w/dmath/records` | 91 → 91 | 练习显示自评 / 客观题正确率 / 最近 12 周还没有作答。 / 最近 14 天还没有作答。 / 还没有带自评的作答。 / 还没有完整的练习轮次记录。 / 这里还没有记录。 | 练习与试卷显示自评 / 客观题判定 / 最近 12 周暂无作答 / 最近 14 天暂无作答 / 暂无带自评的作答 / 暂无练习轮次 / 暂无记录 |
| `/w/dmath/records?view=runs` | 62 → 60 | 练习显示自评 / 练习 / 试卷 / 每一轮做了什么 / 完成或替换一轮练习后保留快照；试卷记录保留当时的试卷名称。 / 还没有完整的练习轮次记录。 | 练习与试卷显示自评 / 练习轮次 / 暂无练习轮次 |
| `/w/dmath/records?view=attempts` | 62 → 61 | 练习显示自评 / 作答明细 / 0 条已载入。 / 这里还没有记录。 | 练习与试卷显示自评 / 0 条 / 暂无记录 |
| `/w/dmath/records?view=wrong` | 62 → 61 | 练习显示自评 / 需要回看的作答 / 这里还没有记录。 | 练习与试卷显示自评 / 暂无记录 |
| `/w/dmath/session-end` | 57 → 57 | 练习显示自评 | 练习与试卷显示自评 |
| `/w/dmath/settings` | 65 → 65 | 练习显示自评 | 练习与试卷显示自评 |

**逐条对回 27 条**（可见层面）：

| 条目 | 可见层面落在哪 | 在上表里 |
|---|---|---|
| P-163 | 每个页面的左栏设置项 | ✅ **10 个路由**都出现（除 `/` 外的全部） |
| E-03 / E-05 / E-10 | 知识点页的经验面板 | ✅ |
| R-06 / R-26 | 记录页 + 各子页空态 | ✅ |
| R-41 | 记录页概览的第三张统计卡 | ✅ |
| R-44 / R-45 / R-49 | 记录页概览的三个图表空态 | ✅ |
| R-54 | 记录页**按单题过滤时**的提示块 | ⚠️ **默认 fixture 不带 `?problem=`，本轮路由表里没渲染出来**（已单独渲染确认，见 §8.3） |
| R-57 / R-58 / R-59 | `?view=runs` | ✅ |
| R-60 / R-62 | `?view=attempts` | ✅ |
| R-63 / R-64 | `?view=wrong` | ✅ |
| R-28 / R-31 / R-34 / R-36 / R-38 | 记录页「多次练习」卡（**需要 practice_sets 数据**） | ⚠️ **默认 fixture 的 `practice_sets` 为空 ⇒ 这些分支不渲染**，本轮路由表里看不到 |
| W-105 / A-13 / P-209 / P-210 | **客户端 JS 渲染**（Agent 右栏 / 工件卡） | ⚠️ 服务端 HTML 里没有（由 `agent-ui.js` / `workbench.js` 在浏览器里生成） |

> ⚠️ **诚实说明**：上表**不是** 27 条的逐条可见证据 —— 有 6 条（R-28 / R-31 / R-34 / R-36 / R-38 / R-54）
> 在默认 fixture 下**不渲染**，4 条（W-105 / A-13 / P-209 / P-210）是**客户端渲染**。
> 这 10 条的证据是**源码层**的：`git diff` 逐字（§5.1）+ `grep -n` 实测行号（§2）+ 旧串 0 命中（§2.1）。
> 其中 **R-28 / R-31 / R-41 的渲染对照**在 §5.3 用**同一份数据喂两个版本**补上了实证。

### 5.3 第三层 · R-28 / R-31 / R-41 的「只改呈现」实证

**方法**：把**同一份 overview 数据**分别喂给基线版本的 `records.py` 与 HEAD 版本的 `records.py`，
打印两边渲染出来的字符串。

```
----- BASE(5f8440db) -----
  试卷卡 meta : 已完成 2 次 · 最近正确率 50% · 最近自评 3.5 / 5 · 最近不会 1 个
  轮次条目   : | 2026-09-29 10:20:00 |  · 正确 5/10 · 自评 3.5 / 5 · 不会 1 个
  轮次条目   : | 2026-09-20 10:20:00 |  · 正确 8/10 · 自评 4.0 / 5 · 不会 0 个
  四个汇总数字: 作答次数=40 · 完成练习=2 · 客观题正确率=75% · 平均自评=3.5 / 5

----- HEAD(3eb9f2a1) -----
  试卷卡 meta : 已完成 2 次 · 最近判定 5/10 · 最近自评 3.5 / 5 · 最近不会 1 个
  轮次条目   : | 2026-09-29 10:20:00 |  · 判定正确 5/10 · 自评 3.5 / 5 · 不会 1 个
  轮次条目   : | 2026-09-20 10:20:00 |  · 判定正确 8/10 · 自评 4.0 / 5 · 不会 0 个
  四个汇总数字: 作答次数=40 · 完成练习=2 · 客观题判定=30/40 · 平均自评=3.5 / 5
```

**「口径一个字没动」的证据链**：

| # | 事实 | 证据 |
|---|---|---|
| 1 | **被计数的集合完全相同** | 数据层 `workbench/data/records.py:97` 与 `:252`：`"accuracy": (correct / judged) if judged else None` —— 改前渲染的 `{accuracy*100:.0f}%` 与改后渲染的 `{correct}/{judged}` **分子分母是同一对字段**（实测 5/10 ⇒ 0.5 ⇒ 50%；30/40 ⇒ 0.75 ⇒ 75%） |
| 2 | **空态判定条件没变** | 三处都保留 `if accuracy is None` ⇒ 「—」的触发条件仍是 `judged == 0`，一字未改 |
| 3 | **统计行数没变** | 四个汇总数字的**顺序、个数、其余三个的值**（40 / 2 / 3.5 / 5）逐位相同 |
| 4 | **迷你图没变** | `_verdict_ring(correct, judged)` **函数体逐字未变**（弧长 = `correct/judged` 的占比，不画百分比曲线、不显示任何数字）；`_sparkline` / `_run_blocks` / `_rating_spark` 同样逐字未变 ⇒ A-119 要求的「概览页迷你图若画的是百分比曲线，一并改成非百分比形态」**不适用**（它本来就不是百分比曲线） |
| 5 | **请求序列没变** | `git diff` 零 `fetch` / `.post` 改动；这三个数字**全部由服务端同一次 `records.overview(pool)` 查询供给** |

⚠️ **必须说清的一点**：改前渲染的是**四舍五入后的百分比**（`{accuracy*100:.0f}%`），
改后是**分数**（`correct/judged`）⇒ **同一个比例，呈现格式不同，显示的位数也不同**
（例如 7/10 → 改前 `70%`、改后 `7/10`）。这是 **A-119 明确裁定的结果**
（「落地只改呈现（百分比 → N/M 分数），被计数的口径、统计行、请求序列全部不动」），
**不是**口径变更。spec delta 的原话是「the four summary figures **keep their present values and their
present definitions**；a difference in **what any of them counts** is registered as separate drift」——
**被计数的定义没变**，变的是渲染格式。

### 5.4 结论

**「除文案清理项外逐字一致」成立。**
三层独立核对（源码改动面 63 行逐条 + DOM 可见文本**有序** diff 24 hunk + 同数据双版本渲染对照）
都只发现台账内的文案改动，**没有一条越界的文字改动、没有一条逻辑改动**。

---

## 6. 界面可见文本条数与字数对比

**口径**：`tmp_local2/p26_textcount.py`（**上一波 P26 报告用的同一个脚本**，未改动，
只换 cwd = 各 checkout 根目录）⇒ 数字与 P26 报告**同口径可比**。
计数对象 = 服务端渲染 HTML 里的**可见文本节点**（跳过 `script` / `style`）。

**自检**：用同一个脚本跑基线 `872e6297`（上一波的起点）→ 得到 **585 节点 / 2989 字符**，
与上一波 P26 报告 §3 的「585 → 563 / 2989 → 2361」**完全吻合** ⇒ 口径一致，数字可信。

### 6.1 本棒（`5f8440db` → `3eb9f2a1`）

| 页面 | 可见文本节点（改前 → 改后） | 可见字符数（改前 → 改后） | 结论 |
|---|---|---|---|
| `/` | 6 → 6（0） | 59 → 59（0） | ✅ 不增 |
| `/w/dmath/practice` | 117 → 117（0） | 514 → 517（**+3**） | ✅ 节点不增 |
| `/w/dmath/kps` | 78 → 78（0） | 291 → 294（**+3**） | ✅ 节点不增 |
| `/w/dmath/kp/dmath-ch06-kp-001` | 71 → 69（**-2**） | 334 → 293（**-41**） | ✅ 不增 |
| `/w/dmath/practice-sets` | 63 → 63（0） | 259 → 262（**+3**） | ✅ 节点不增 |
| `/w/dmath/records` | 96 → 96（0） | 395 → 380（**-15**） | ✅ 不增 |
| `/w/dmath/session-end` | 62 → 62（0） | 254 → 257（**+3**） | ✅ 节点不增 |
| `/w/dmath/settings` | 70 → 70（0） | 255 → 258（**+3**） | ✅ 节点不增 |
| **合计** | **563 → 561（-2）** | **2361 → 2320（-41）** | **✅ 不增** |

**逐页 +3 是哪来的**：`练习显示自评`（6 字）→ `练习与试卷显示自评`（9 字）= **+3**。
这个标签在**左栏设置区**，而左栏在**除 `/` 外的每一个页面**上 ⇒ 8 个页面里 7 个 +3。
**这是唯一一处「变长」的文案**，且它不是「说明性文字」，是**一个开关的标签**
（P-163 的定稿用词裁决，A-119 拍板）。

### 6.2 整波累计（`872e6297` → `3eb9f2a1`）

| | 节点 | 字符 |
|---|---|---|
| 起点（上一波 P26 的基线） | 585 | 2989 |
| 上一波 P26 交工时 | 563 | 2361 |
| **本棒交工时** | **561** | **2320** |
| **累计** | **-24** | **-669** |

⇒ **26.2 的「改造后界面上的说明性文字数量不增加」成立**（节点 -24 / 字符 -669）。
**八个页面逐页节点数全部不增**；字符数在 5 个页面上各 +3（P-163 标签），
但**说明性文字**（段落说明句、图表空态、页头摘要）在每一页上**都只减不增**。

---

## 7. 六条验证命令的原样结果

全部在**仓库根**执行（`cd "D:/Projects/Academic Workflow/lesson-kit"`），跑在**最终代码状态**（`3eb9f2a1`）。

### 7.1 `env -u http_proxy -u https_proxy -u all_proxy python -m pytest tests -q`

```
........................................................................ [ 67%]
........................................................................ [ 73%]
........................................................................ [ 79%]
........................................................................ [ 85%]
........................................................................ [ 91%]
........................................................................ [ 97%]
.............................                                            [100%]
1181 passed in 243.18s (0:04:03)
```

> **代理坑已规避**（A-环境坑）：`http_proxy=127.0.0.1:7890` 会吞 localhost，故 pytest 显式
> `env -u http_proxy -u https_proxy -u all_proxy`。
> 本棒**自己又跑了一遍**（不是在上一波的输出上誊抄）：R-54 修复后重跑，**1181 passed**。
> 修复前也跑了一遍，同样 1181 passed（`241.05s`）。

### 7.2 `python -m compileall -q lessonkit.py workbench pipeline pool tests`

```
EXIT=0
```

（无输出 = 全部字节码编译通过。）

### 7.3 `openspec validate --specs --strict`

```
- Validating...
✓ spec/agent-assisted-practice-records
✓ spec/agent-context
✓ spec/agent-contract-disclosure
✓ spec/agent-learning-evidence
✓ spec/ai-teacher-bridge
✓ spec/calendar-workload
✓ spec/daily-learning-plan
✓ spec/flash-card
✓ spec/knowledge-figures
✓ spec/mastery-evaluation
✓ spec/micro-quiz-content
✓ spec/practice-experience
✓ spec/practice-review
✓ spec/practice-set-export
✓ spec/problem-difficulty
✓ spec/retrieval-evaluation
✓ spec/review-workbench
✓ spec/workbench-content-governance
✓ spec/workbench-ui
Totals: 19 passed, 0 failed (19 items)
EXIT=0
```

### 7.4 `python lessonkit.py guard extract-problems --course dmath --chapter ch06`

```
Gate: extract-problems
Course: dmath
Chapter: ch06
Result: PASS

All required artifacts exist and check files contain no blocking markers.
EXIT=0
```

### 7.5 `node --test tests/workbench/*.test.js`

```
✔ running off mode survives the preference change (0.7582ms)
✔ an empty rating input is rejected inline instead of dying at the server (1.5026ms)
ℹ tests 264
ℹ suites 0
ℹ pass 264
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 935.0286
EXIT=0
```

### 7.6 `python lessonkit.py guard problem-set --course dmath --chapter ch06`（工作区产物验收，额外跑）

```
Gate: problem-set
Course: dmath
Chapter: ch06
Result: PASS

All required artifacts exist and check files contain no blocking markers.
EXIT=0
```

> AGENTS.md 说明：`problem-set` guard 属于工作区产物验收，不是仓库级 CI 前置条件
> （干净 checkout 不跟踪 `output/`）。本次工作区**有**该产物，所以**顺手也跑了**，结果 PASS。

---

## 8. 待裁决项

### 8.1 ⚠️ 【最高优先】**P-163 的文档 / 契约漂移** —— 代码改了，spec / GLOSSARY / MANUAL 没跟上

**事实**：`7e4897b2` 把代码里的左栏设置标签从「练习显示自评」改成「**练习与试卷显示自评**」
（A-119 裁定），`94ac6370` 只同步了**设计件** `copy-table.md`。
**其它三份职责文件至今仍写旧词**：

| 文件 | 行 | 现在写的是 | 状态 |
|---|---|---|---|
| `openspec/specs/workbench-ui/spec.md` | **1051** | 「练习与**组卷**显示自评」 | ❌ **当前行为契约**与代码不一致 |
| `openspec/changes/workbench-visual-language-v2/specs/workbench-ui/spec.md` | **924** | 「练习与**组卷**显示自评」 | ❌ 本 change 的 spec delta 也未改 |
| `docs/GLOSSARY.md` | **183** | 第一项是「练习与**组卷**显示自评」（默认开） | ⚠️ **A-119 明写「GLOSSARY 不改」** ⇒ 属**有意的**遗留，但仍与代码不一致 |
| `docs/GLOSSARY.md` | **479** | 「练习与**组卷**显示自评等**学习行为**偏好」 | ⚠️ 同上 |
| `docs/PRODUCT-MANUAL.md` | **266 / 276 / 286 / 325 / 327 / 331 / 337** | 「**练习显示自评**」（7 处，旧简称） | ❌ **假陈述**：界面上已经没这个标签了 |
| `docs/PRODUCT-MANUAL.md` | **610** | 「练习与**组卷**显示自评」 | ❌ 假陈述 |

> ⚠️ **时序提醒**：owner 在 `c1313468`（09:07）里**已经勾上 tasks 26.1 / 26.2 / 26.3**，
> 证据引的是 `IMPL-P26-report.md`（**本报告写出来之前**）。
> ⇒ **这两条漂移在勾选时还没有被发现**，勾选本身没错，但「已闭合」的结论**要按本节修正**。

**为什么本棒没有直接修**：
1. 本棒的文件所有权明确是「**只写报告文件**」，`docs/` 与 `openspec/specs/` 都不在本棒的写权限内；
2. 修 `openspec/specs/workbench-ui/spec.md` 是**改当前行为契约**，属所有者 / change owner 的动作
   （要走 spec delta → 归档的流程）；
3. A-119 已经明确「GLOSSARY 不改」⇒ 这条漂移里**有一半是有意为之**，
   另一半（spec + MANUAL）是真的漏了 —— **两者必须一起裁，不能只补一半**。

**给所有者的精确改法**（一次 commit 即可闭合）：

```text
openspec/specs/workbench-ui/spec.md:1051
  「练习与组卷显示自评」 → 「练习与试卷显示自评」

openspec/changes/workbench-visual-language-v2/specs/workbench-ui/spec.md:924
  「练习与组卷显示自评」 → 「练习与试卷显示自评」

docs/PRODUCT-MANUAL.md:266,276,286,325,327,331,337   （7 处）
  「练习显示自评」 → 「练习与试卷显示自评」

docs/PRODUCT-MANUAL.md:610
  「练习与组卷显示自评」 → 「练习与试卷显示自评」

docs/GLOSSARY.md:183,479
  「练习与组卷显示自评」 → 「练习与试卷显示自评」（⚠️ 与 A-119 的「GLOSSARY 不改」相抵，需所有者拍板）
```

⚠️ **补充一条口径事实**，供裁决时参考：
GLOSSARY「组卷 / Paper Assembly」条明写「浏览器不提供学生手工组卷入口」，
而这个开关**实际**被 `practice-flow.js:483`（练习流）与 `paper-practice.js:478/492`（**试卷**流）读取
⇒ 它的作用域确实是「练习 + 试卷」，**「组卷」这个词本身是错的**（浏览器里没有组卷流程）。
⇒ 建议**连 GLOSSARY 一起改**（与 A-119 的「GLOSSARY 不改」相抵，需要所有者点头）。

### 8.2 ⚠️ **R-41 的 MANUAL 同步漏了**（2 处假陈述）

| 文件 | 行 | 现在写的是 | 代码里现在是 |
|---|---|---|---|
| `docs/PRODUCT-MANUAL.md` | **343** | 「**概览**看作答次数、完成练习数、**客观题正确率**、平均自评」 | 第三张卡的标签是「**客观题判定**」 |
| `docs/PRODUCT-MANUAL.md` | **345** | 「**客观题正确率**配一个墨色占比环」 | 同上 |

⇒ 改法：`客观题正确率` → `客观题判定`（两处）。
（这两处**在本棒之前是自洽的** —— 上一波的 W3e/W3f2 波把卡片做成「客观题正确率」，
MANUAL 跟着写的；本棒 R-41 改了标签，MANUAL 没跟上。）

### 8.3 【本棒已修】**R-54 的尾句号** —— 落地与定稿差 1 个字符

| | 文案 | 依据 |
|---|---|---|
| 定稿 | `按单题过滤` | copy-table §2.8 R-54：「去掉"正在"与句号，作为状态标签而非叙述句」 |
| 落地（`c01d55f3`） | `按单题过滤。` | ❌ 「正在」删了，**句号没删** ⇒ 仍是叙述句，与定稿差 1 字 |
| 本棒修后 | `按单题过滤` | commit `3eb9f2a1` |

**渲染对照**（实测）：

```html
改前：<p class='record-filter-note'>按单题过滤。<a href='/w/dmath/records'>查看全部记录</a></p>
改后：<p class='record-filter-note'>按单题过滤<a href='/w/dmath/records'>查看全部记录</a></p>
```

⚠️ **副作用（需所有者知情）**：句号去掉后，这一段的**可见文本**变成
「按单题过滤查看全部记录」—— 标签与链接之间**没有分隔**（因为 R-55「查看全部记录」
copy-table 判「留」、本棒不能动）。
这是 copy-table 定稿自身两条叠加的结果（**R-54 去句号 + R-55 留链接**），
不是本棒引入的。**如果要断开**，正确做法是**改 copy-table 让 R-55 带上分隔**，
而不是在代码里加一个字。⇒ 登记在此，请所有者决定。

**为什么本棒可以修**：这是**一条落地的文案与定稿不一致**（不是逻辑 bug），
属任务书「真 bug（落地错了）」的范围；改动面 = **1 个字符**，不碰任何其它文案 / 结构 / 逻辑。
`tests/workbench/test_ui_routes.py:1198` 的断言是 `assertIn("按单题过滤", body)`（子串），
改前改后都通过 ⇒ **不需要改测试**。

### 8.4 其它已登记但**不在本变更范围**的项（沿用上一波的登记，本棒**未动**）

| # | 事项 | 状态 |
|---|---|---|
| 1 | `workbench/server/api.py:530` `'stale draft: reload the current Paper'` | API 错误串，**不渲染**；`api.py` 不在本变更可写清单。上一波 §8.2 已登记，**仍未处理** |
| 2 | **P-74**（`覆盖进度：{v}` 的值域） | 台账 §5 #1：值域未经核（可能是百分比），待 `DATA_MODEL.md` + 所有者裁决。**未动** |
| 3 | **W-171**（`an unfinished practice already exists`） | 协议串，只被 `===` 比较、从不渲染 ⇒ **禁改**。已核实 `workbench.js:3200` 的比较仍在，**未动** |
| 4 | **G-01…G-32**（图谱 32 条） | 归 `graph-node-visual-language` change。**本棒图谱页与三个图谱 JS 零改动** |
| 5 | **R-34 的 UI 提示** | 见 §3.1 —— **要加回提示必须新开 change**，不能在本棒顺手加 |

---

## 9. 诚实回报

### 9.1 做到的

- **27 条逐条核对落地**：每条都做了「定稿文案在实现里命中」+「旧文案 0 命中」**双向** grep，
  没有一条靠肉眼估；证据行号全部是**当场实测**的当前行号。
- **查出并修掉 1 处真 bug**：R-54 尾句号（commit `3eb9f2a1`，1 个字符）。
- **查出并登记 3 类 12 处文档漂移**（§8.1 的 P-163 链 + §8.2 的 R-41 链），
  给出了**逐行可直接执行的改法**，但**没有擅自去改** `docs/` 与 `openspec/specs/`
  —— 因为那不在本棒的文件所有权内，且其中一半与 A-119 的「GLOSSARY 不改」相抵，需要所有者先裁。
- **六条验证命令全绿**，且 **pytest 是自己重跑的两遍**（修复前 1181 passed / 修复后 1181 passed），
  不是誊抄上一波的输出。
- **「除文案清理项外逐字一致」用三层独立方法证明**：
  源码改动面 63 行逐条归因 + **DOM 可见文本有序 diff**（24 hunk，零越界）+ 同数据双版本渲染对照。
- **数字与上一波同口径**：复用上一波的 `p26_textcount.py` 脚本，并用 `872e6297` 基线
  自检出 **585 / 2989**，与上一波报告的 585 / 2989 完全吻合 ⇒ 口径可比。
- **A-39 规避**：渲染用的是各 checkout 根目录里的 `workbench` 包（输出了 `__file__` 佐证），
  另单独起服务核对 **服务字节 == 磁盘字节**（两个改过的静态文件都 identical=True）。
- **并发安全**：`workbench.css` / `agent-ui.css` **一个字节都没进本棒任何 commit**；
  本棒 2 个 commit 都是 `git add -- <路径>` + `git commit -- <路径>`，**无 `git add -A`**。

### 9.2 没做到的 / 打折的 / 绕过的

| # | 事项 | 说明 |
|---|---|---|
| 1 | **27 条里有 10 条没有「渲染层」证据** | R-28 / R-31 / R-34 / R-36 / R-38 / R-54 在默认 fixture 下**不渲染**（`practice_sets` 为空 / 无 `?problem=`），W-105 / A-13 / P-209 / P-210 是**客户端 JS 渲染**。这 10 条的证据是**源码层**的（`git diff` 逐字 + `grep -n` 实测 + 旧串 0 命中）。其中 R-28 / R-31 / R-41 用「同数据双版本渲染」补上了实证；**R-34 / R-36 / R-38 的渲染结果我没能实测出来**（需要造一份带 `practice_sets` 的 fixture 数据） |
| 2 | **没起浏览器走查截图** | 本棒只改文案、零布局零逻辑，DOM 文本 diff 比截图更能证「逐字一致」；且两个 CSS agent 正在并行改 `workbench.css` / `agent-ui.css`，此刻截图会带进别人的在途改动、污染基线。**没有做视觉走查** —— 特别是 §8.3 那处「按单题过滤查看全部记录」的无分隔读感，**没有截图确认过实际观感** |
| 3 | **文档漂移只登记、没修** | 见 §8.1 / §8.2。理由已写明（文件所有权 + spec 属所有者 + 与 A-119 相抵）。**代价**：合上这个 change 之前，MANUAL 与 spec 里仍有假陈述 |
| 4 | **R-54 的「无分隔」副作用没解** | 见 §8.3。要断开得改 copy-table 的 R-55，**不是本棒能单方面决定的** |
| 5 | **本棒只跑了 1 个自定义路由表** | §5.2 的路由表覆盖了 11 个 URL（含 3 个记录子页），**没有覆盖浏览器端交互路径**（Agent 右栏、工件卡、审批卡）；那 4 条客户端文案（W-105 / A-13 / P-209 / P-210）**没有实机截图**，只有源码 diff + `node --test`（264 全绿，含 `workbench_ui_interactions.test.js:3113` 那条 W-105 断言） |
| 6 | **没改 `IMPLEMENTATION-LOG.md` / `decisions.md` / `contract-drift.md` / `tasks.md`** | 这四个是共享台账，由所有者统一登记。**但本棒有东西需要落进去**：§8.1 / §8.2 的 3 类 12 处漂移、§8.3 的 R-54 修正、以及 §3.1 的 R-34 产品后果。**本棒无权写，请所有者补登记** |
| 7 | **并发 CSS agent 的在途改动影响了 grep 复核一的行数** | 复核一 192 → 190 行里，有 **2 行**是 CSS 文件的行号平移（`agent-ui.css:426→428`、`workbench.css:4524→4757`），
  **不是本棒改的**。§4.1 的差集表已把这 2 条单独归因，不计进本棒的功劳 |
| 8 | **另一份报告（`reports/IMPL-C1-report.md`）也还缺** | IMPLEMENTATION-LOG §9.44 的「仍未闭合」里写着「C1 / P26b 的**两份报告**在关机前没写成，开机后已重新派发」。本棒**只负责 P26b 这一份**，C1 那份**不在本棒范围**，没有代写。`reports/IMPL-C1-shots/` 目录在仓库里是 untracked |
| 9 | **`tmp_local2/p26b/` 下的两个 worktree 与量测脚本未清理** | 它们在 `tmp_local2/`（untracked scratch，上一波的约定），**没提交**。但 `git worktree list` 里会多出
  `tmp_local2/p26b/base` 与 `tmp_local2/p26b/base0` 两条 —— **收工时请 `git worktree remove` 掉**，否则会留两条游离检出 |

### 9.3 明确没有做的事（逐条对照硬约束）

| 硬约束 | 状态 |
|---|---|
| 只写报告文件 | ✅ 本棒只写了 `reports/IMPL-P26b-report.md`；唯一的例外是 §8.3 的 R-54 一字符修正（任务书「真 bug 就修掉」条款） |
| 不许碰 `workbench.css` / `agent-ui.css` | ✅ 未碰、未提交（工作区里它们一直是别人的 `M` 状态） |
| 不许碰 `docs/` / `openspec/specs/` / 本 change 的其它文件 | ✅ 未碰（漂移只登记在 §8.1 / §8.2） |
| 不许 `git add -A` / `-a` / 不带路径的 commit（A-90） | ✅ 本棒 2 个 commit 都是明确路径 |
| 只改文案，不改逻辑（请求序列 / 载荷键 / DOM 身份 / 事件绑定 / 判定分支 / 类名 / 变量名） | ✅ §5.1 逐行归因 + §5.3 口径证据链 |
| 零池写入 / 零新增 localStorage 键 / 不许新增请求 | ✅ diff 里零命中 |
| 知识图谱一行都不许碰 | ✅ 本棒没碰 `graph_page()` 与三个图谱 JS |
| 26.2 删注释而非改写 | ✅ 本棒 9 条「删」全是**整段删除**（连元素与 class 一起），**零条改写成另一句说明** |
| 26.2 界面文字条数不增 | ✅ 节点 -2 / 字符 -41（本棒）；累计 -24 / -669 |
| 代理坑（`http_proxy` 吞 localhost） | ✅ pytest 与全部涉及 localhost 的量测都 `env -u http_proxy -u https_proxy -u all_proxy` |
| A-39（仓库根外起服务 ⇒ 解析到 site-packages 快照） | ✅ 渲染全部在各自 checkout 根执行；服务字节 == 磁盘字节已核对 |

---

*报告完*
