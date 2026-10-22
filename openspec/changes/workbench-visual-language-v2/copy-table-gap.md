# copy-table 未落地清单 — workbench-visual-language-v2

> **性质**：第 26 组（文案清理）落地前的**只读核查报告**。逐条比对
> `design-notes/copy-table.md` 的定稿与当前实现，标出**哪些还没落地**。
> **本文件不改任何实现**——`pages.py` / `records.py` / `experience_page.py` / `static/*.js`
> 一律由第 26 组落地；本文件只提供证据与顺序。
>
> **依据**：`design-notes/copy-table.md`（定稿来源，**以文件实际内容为准**）；
> `docs/GLOSSARY.md`（术语）；`docs/PRODUCT-MANUAL.md`（用户可见文案）；
> `openspec/specs/*/spec.md`（行为契约）。
>
> **核查日期**：2026-10-22　**核查基线**：`51791b1d`（`git log -1`）

---

## 0. 一屏结论

| 项 | 数字 |
|---|---|
| 清单总条数（§1 全量，含图谱） | **703** |
| 范围内（在本次变更内裁决） | **671** |
| **已落地** | **556** |
| **未落地** | **115** |
| **与定稿不一致** | **0** |

**按处理类别拆开**

| 定稿类别 | 已落地 | 未落地 | 不一致 | 小计 |
|---|---|---|---|---|
| 留 | 550 | 0 | 0 | 550 |
| 删 | 4 | 27 | 0 | 31 |
| 改 | 2 | 68 | 0 | 70 |
| 译 | 0 | 20 | 0 | 20 |
| **合计** | **556** | **115** | **0** | **671** |

**一句话**：copy-table 的 **671 条**里，**556 条已经落地**（其中 550 条是「留」——本来就不动的动作名与契约词），
**真正待做的是 115 条**：27 条「删」、68 条「改」、20 条「译」。
这 115 条**一条都没有被别的 agent 顺手改掉**——实现里的原文与 copy-table §1 抓取时**逐字一致**，
说明第 26 组是一次性的、可以从零开始的全量落地，而不是收尾修补。

**已落地的 4 条「删」+ 2 条「改」**（第 26 组不要重复动）：

| ID | 页面 | 原定稿 | 现状 | 证据 |
|---|---|---|---|---|
| P-26 | 练习页（作答流） | （删除） | （已从界面移除） | pages.py:316（仅代码注释残留，界面已无） |
| P-132 | 试卷列表 | （删除） | （已从界面移除） | 全仓库无命中 |
| P-195 | 时间安排与复习负荷 | （删除） | （已从界面移除） | 全仓库无命中；文档同步：docs/PRODUCT-MANUAL.md:196 |
| R-48 | 记录中心与会话末统一自评 | （删除） | （已从界面移除） | 全仓库无命中 |
| P-92 | 目标与计划 | 让 Agent 代填 | 让 Agent 代填 | pages.py:463 |
| P-131 | 试卷列表 | 还没有保存的试卷 | 还没有保存的试卷 | pages.py:819 |

> 注：P-26 的原句只以**代码注释**形式残留在 `pages.py:316`（注释不渲染），界面已无该文案。

---

## 1. 核查方法（可复核）

### 1.1 核查范围

copy-table §1 的清单分七段，本次**全部逐条核**（不是抽样）：

| 段 | 来源文件 | 条数 | 本清单是否核查 |
|---|---|---|---|
| `P-01…P-208` | `workbench/server/pages.py` | 208 | ✅ |
| `R-01…R-78` | `workbench/server/records.py` | 78 | ✅ |
| `E-01…E-12` | `workbench/server/experience_page.py` | 12 | ✅ |
| `E-13…E-20` | `workbench/server/static/kp-experience.js` | 8 | ✅ |
| `W-01…W-171` | `workbench/server/static/workbench.js` | 171 | ✅ |
| `F-01…F-104` | `workbench/server/static/practice-flow.js` | 104 | ✅ |
| `Q-01…Q-70` | `workbench/server/static/paper-practice.js` | 70 | ✅ |
| `A-01…A-20` | `workbench/server/static/agent-ui.js` | 20 | ✅ |
| `G-01…G-32` | 知识图谱页 | 32 | ❌ **范围外**（copy-table §0.4 / §1.11：不改、不给定稿、不计统计） |

> `workbench/server/static/middle-navigation.js`、`practice-deck.js`、`sfx.js`、
> `graph-physics*.js`、`graph-renderer.js` 经核**不含界面文案**（copy-table §1.7 已结论），不重复列。

### 1.2 判定规则

| 定稿类别 | 「已落地」的判据 | 「未落地」的判据 |
|---|---|---|
| **留** | 原文仍在实现里（逐字命中） | 原文已不在实现里 |
| **删** | 原文**已不在**实现里 | 原文仍在实现里 |
| **改 / 译** | 原文已不在 **且** 定稿文本已在 | 原文仍在（定稿文本可同时在别处出现） |

判定做在**实现源码的原文上**（把字符串字面量按拼接关系摊平再匹配），
因此跨行拼接的字符串（如 `workbench.js:3894-3895` 的 W-40）也能正确命中。
命中后人工复核到**文件 + 行号 + 该行原文**三层证据，逐条可复算。

### 1.3 排除项（不算界面文案）

按任务书要求，判定时**排除**：代码标识符、注释、URL、纯技术字符串，以及
**来自数据的用户内容**（题面 / 评语 / 章节名 / 知识点名 / 试卷名等）。
具体到本清单：

- `P-73`/`P-165`/`Q-28`/`F-51`/`R-04` 的**兜底标题**（`未命名目标` / `未命名题目`）算界面文案；
  但**标题本身**（章节名、试卷名、知识点名）是数据，不在本清单。
- `W-171`（`an unfinished practice already exists`）**从不渲染**——它只被 `error.message === "..."` 比较，
  改它会破坏与服务端错误串的对齐 → copy-table 已判「留 / 禁改」，本清单**不列入待办**。
- `W-167…W-170` 是**英文兜底但会渲染**（copy-table §4.1 已确认），所以列入待办。
- 图谱页 32 条（`G-*`）按 §0.4 范围外，不列。

---

## 2. 未落地清单（115 条 · 第 26 组的活儿）

按页面分组。**「当前文案」一栏是实现里此刻的原样**（可直接 grep 复现）；
**「定稿文案」一栏是 copy-table §2 给的目标形态**。

> 「建议动作」一栏：
> - `删除该文案` —— 少字原则，**直接删**，不要改写成更好看的说明句（26.2 的口径）。
> - `替换为定稿` —— 逐字换成定稿文案。

### 2.1 Hub 首页（3 条）

| ID | 页面 | 定稿文案 | 当前文案 | 状态 | 建议动作 | 证据（file:line） |
|---|---|---|---|---|---|---|
| P-01 | Hub 首页 | 工作区读取失败 | 数据库读不了：{error 首行} | 未落地 | 替换为定稿 | pages.py:149 |
| P-03 | Hub 首页 | 工作区 | 学习工作区 | 未落地 | 替换为定稿 | pages.py:155 |
| P-06 | Hub 首页 | （删除） | 选择一个工作区，从最需要回看的地方继续。 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:164 |

### 2.2 外壳（顶栏/透镜/列宽/Agent 浮层）（5 条）

| ID | 页面 | 定稿文案 | 当前文案 | 状态 | 建议动作 | 证据（file:line） |
|---|---|---|---|---|---|---|
| P-14 | 外壳（顶栏/透镜/列宽/Agent 浮层） | 调整左栏宽度 | 调整左栏宽度 ／ 拖动调整左栏宽度 | 未落地 | 替换为定稿 | pages.py:253 |
| P-15 | 外壳（顶栏/透镜/列宽/Agent 浮层） | 调整右栏宽度 | 调整右栏宽度 ／ 拖动调整右栏宽度 | 未落地 | 替换为定稿 | pages.py:255 |
| P-16 | 外壳（顶栏/透镜/列宽/Agent 浮层） | Agent 活动 | Agent activity | 未落地 | 替换为定稿 | pages.py:273 |
| P-21 | 外壳（顶栏/透镜/列宽/Agent 浮层） | 工件 | Artifact | 未落地 | 替换为定稿 | pages.py:286 |
| W-01 | 外壳（顶栏/透镜/列宽/Agent 浮层） | 章节切换失败：{msg} | 切换章节失败：{msg} | 未落地 | 替换为定稿 | workbench.js:63 |

### 2.3 练习页（作答流）（3 条）

| ID | 页面 | 定稿文案 | 当前文案 | 状态 | 建议动作 | 证据（file:line） |
|---|---|---|---|---|---|---|
| P-40 | 练习页（作答流） | 自评（1–5） | 自评分（1–5） | 未落地 | 替换为定稿 | pages.py:339 |
| P-42 | 练习页（作答流） | 备注（可选） | 卡点或心得（可选） | 未落地 | 替换为定稿 | pages.py:342 |
| P-43 | 练习页（作答流） | 备注（可选） | 卡点或心得（可选） | 未落地 | 替换为定稿 | pages.py:342 |

### 2.4 试卷练习（Paper）（6 条）

| ID | 页面 | 定稿文案 | 当前文案 | 状态 | 建议动作 | 证据（file:line） |
|---|---|---|---|---|---|---|
| P-68 | 试卷练习（Paper） | 本轮完成 | Congratulations! | 未落地 | 替换为定稿 | pages.py:405 |
| Q-13 | 试卷练习（Paper） | 先从试卷列表打开一份已保存的试卷。 | 从试卷列表打开已保存的试卷后即可开始练习。 | 未落地 | 替换为定稿 | paper-practice.js:442 |
| Q-14 | 试卷练习（Paper） | 选择试卷 | 先选择试卷 | 未落地 | 替换为定稿 | paper-practice.js:446 |
| Q-43 | 试卷练习（Paper） | 自评（可选） | 自评（可选，不影响继续练习） | 未落地 | 替换为定稿 | paper-practice.js:816 |
| Q-44 | 试卷练习（Paper） | 自评 1–5 | 熟悉程度 1–5 | 未落地 | 替换为定稿 | paper-practice.js:818 |
| Q-64 | 试卷练习（Paper） | 共 N 题；判定正确 N 题，错误 N 题；不会 N 题；待自评 N 题。 | 共 N 题；客观正确 N 题，错误 N 题；不会 N 题；待自评 N 题。 | 未落地 | 替换为定稿 | paper-practice.js:1461-1463 |

### 2.5 目标与计划（5 条）

| ID | 页面 | 定稿文案 | 当前文案 | 状态 | 建议动作 | 证据（file:line） |
|---|---|---|---|---|---|---|
| P-74 | 目标与计划 | 覆盖进度：{v} | 覆盖进度：{v} | 未落地 | 替换为定稿 | pages.py:436 |
| P-79 | 目标与计划 | 暂无目标 | 暂无已设置的长期或阶段目标。 | 未落地 | 替换为定稿 | pages.py:445；文档同步：docs/PRODUCT-MANUAL.md:58 |
| P-94 | 目标与计划 | 让 Agent 代填 | 让 Agent 填 | 未落地 | 替换为定稿 | pages.py:465 |
| W-17 | 目标与计划 | 暂无可用 Agent。请先配置一个提供方。 | 暂无可用 Agent。请先配置一个提供方，或手动填写字段。 | 未落地 | 替换为定稿 | workbench.js:3302；文档同步：docs/PRODUCT-MANUAL.md:371（前半句逐字保留，MANUAL 不必改） |
| W-19 | 目标与计划 | 请先在右侧选择 Agent，再点一次「让 Agent 代填」。 | 请先在右侧选择 Agent 开始对话，再点一次「让 Agent 填」。 | 未落地 | 替换为定稿 | workbench.js:3311 |

### 2.6 知识点页与知识点列表（4 条）

| ID | 页面 | 定稿文案 | 当前文案 | 状态 | 建议动作 | 证据（file:line） |
|---|---|---|---|---|---|---|
| P-101 | 知识点页与知识点列表 | （删除） | 先读正文，再按需要继续练习相关题目。 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:542 |
| P-102 | 知识点页与知识点列表 | （删除） | 练习入口 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:549 |
| P-109 | 知识点页与知识点列表 | （删除） | 阅读课程内容与关联题目；练习请使用已有试卷。 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:644 |
| P-113 | 知识点页与知识点列表 | （删除） | 当前排序 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:651 |

### 2.7 试卷列表（4 条）

| ID | 页面 | 定稿文案 | 当前文案 | 状态 | 建议动作 | 证据（file:line） |
|---|---|---|---|---|---|---|
| P-115 | 试卷列表 | 缺少 N 道题 | 缺少题目 N 道，详情见下方折叠项 | 未落地 | 替换为定稿 | pages.py:748 |
| P-124 | 试卷列表 | 当前试卷 N 题；旧执行 M 题，已完成 K 题。 | 当前试卷 N 题；旧执行仍保留 N 题，已完成 N 题。 | 未落地 | 替换为定稿 | pages.py:765-767 |
| P-125 | 试卷列表 | （删除） | 试卷 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:319 |
| P-136 | 试卷列表 | （删除） | 每份试卷独立保存作答进度，切换后可以继续。 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:825 |

### 2.8 记录中心与会话末统一自评（25 条）

| ID | 页面 | 定稿文案 | 当前文案 | 状态 | 建议动作 | 证据（file:line） |
|---|---|---|---|---|---|---|
| P-140 | 记录中心与会话末统一自评 | （删除） | 练习轮次、试卷作答和逐题记录都在这里；统计只从已有学习记录实时计算。 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:846 |
| P-143 | 记录中心与会话末统一自评 | （删除） | 只补充尚未评分的题目与闪卡；已写入的记录不会重复出现。 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:860 |
| P-144 | 记录中心与会话末统一自评 | （删除） | 待补充 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:865 |
| P-146 | 记录中心与会话末统一自评 | （删除） | 逐题输入 1–5 分；点击保存前不会写入学习记录。 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:866 |
| P-147 | 记录中心与会话末统一自评 | （删除） | 下一步 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:869 |
| P-149 | 记录中心与会话末统一自评 | （删除） | 重新开始时再次选择自评方式。 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:870 |
| R-06 | 记录中心与会话末统一自评 | 暂无记录 | 这里还没有记录。 | 未落地 | 替换为定稿 | records.py:122 |
| R-26 | 记录中心与会话末统一自评 | 暂无练习轮次 | 还没有完整的练习轮次记录。 | 未落地 | 替换为定稿 | records.py:191 |
| R-28 | 记录中心与会话末统一自评 | 最近判定 — ／ 最近判定 N/M | 最近正确率 — ／ 最近正确率 N% | 未落地 | 替换为定稿 | records.py:205 |
| R-31 | 记录中心与会话末统一自评 | 判定 — ／ 判定正确 N/M | 正确 — ／ 正确 N/M | 未落地 | 替换为定稿 | records.py:218 |
| R-34 | 记录中心与会话末统一自评 | （删除） | 这张试卷的题目或顺序曾变化；下面按每次实际内容分别显示，不合并成一条趋势。 | 未落地 | 删除该文案（不要改写成别的说明句） | records.py:232-233 |
| R-36 | 记录中心与会话末统一自评 | （删除） | 同一试卷 | 未落地 | 删除该文案（不要改写成别的说明句） | records.py:247 |
| R-38 | 记录中心与会话末统一自评 | （删除） | 只使用每次实际留下的作答、自评和不会记录。 | 未落地 | 删除该文案（不要改写成别的说明句） | records.py:248 |
| R-41 | 记录中心与会话末统一自评 | 客观题判定 ／ N/M | 客观题正确率 | 未落地 | 替换为定稿 | records.py:363 |
| R-44 | 记录中心与会话末统一自评 | 最近 14 天暂无作答 | 最近 14 天还没有作答。 | 未落地 | 替换为定稿 | records.py:449 |
| R-45 | 记录中心与会话末统一自评 | 最近 12 周暂无作答 | 最近 12 周还没有作答。 | 未落地 | 替换为定稿 | records.py:553 |
| R-49 | 记录中心与会话末统一自评 | 暂无带自评的作答 | 还没有带自评的作答。 | 未落地 | 替换为定稿 | records.py:587 |
| R-54 | 记录中心与会话末统一自评 | 按单题过滤 | 正在按单题过滤。 | 未落地 | 替换为定稿 | records.py:637 |
| R-57 | 记录中心与会话末统一自评 | （删除） | 练习 ／ 试卷 | 未落地 | 删除该文案（不要改写成别的说明句） | records.py:137 |
| R-58 | 记录中心与会话末统一自评 | 练习轮次 | 每一轮做了什么 | 未落地 | 替换为定稿 | records.py:651 |
| R-59 | 记录中心与会话末统一自评 | （删除） | 完成或替换一轮练习后保留快照；试卷记录保留当时的试卷名称。 | 未落地 | 删除该文案（不要改写成别的说明句） | records.py:652 |
| R-60 | 记录中心与会话末统一自评 | （删除） | 作答明细 | 未落地 | 删除该文案（不要改写成别的说明句） | records.py:607 |
| R-62 | 记录中心与会话末统一自评 | N 条 | N 条已载入。 | 未落地 | 替换为定稿 | records.py:660 |
| R-63 | 记录中心与会话末统一自评 | （删除） | 错题 | 未落地 | 删除该文案（不要改写成别的说明句） | records.py:608 |
| R-64 | 记录中心与会话末统一自评 | 错题 | 需要回看的作答 | 未落地 | 替换为定稿 | records.py:667 |

### 2.9 Agent 右栏与队列（28 条）

| ID | 页面 | 定稿文案 | 当前文案 | 状态 | 建议动作 | 证据（file:line） |
|---|---|---|---|---|---|---|
| A-03 | Agent 右栏与队列 | 试卷 | 练习 ／ 组卷 ／ 知识点 ／ 知识图谱 ／ 记录 ／ 目标 | 未落地 | 替换为定稿 | agent-ui.js:51 |
| A-13 | Agent 右栏与队列 | 打开试卷页 | 打开组卷页 | 未落地 | 替换为定稿 | agent-ui.js:267；文档同步：docs/PRODUCT-MANUAL.md:440（按文档改代码，MANUAL 不必改） |
| P-170 | Agent 右栏与队列 | 还没有对话 | 还没有对话。 | 未落地 | 替换为定稿 | pages.py:1060 |
| P-173 | Agent 右栏与队列 | （删除） | 先选一个起始 Agent；之后可在同一对话里切换可用模型与 Agent。 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:1064 |
| P-179 | Agent 右栏与队列 | 试卷更新待确认 | Paper 更新待确认 | 未落地 | 替换为定稿 | pages.py:1078；文档同步：docs/PRODUCT-MANUAL.md:462 |
| P-180 | Agent 右栏与队列 | 确认这次调整 | 确认这次题目调整 | 未落地 | 替换为定稿 | pages.py:1079 |
| W-29 | Agent 右栏与队列 | 将清除这张试卷未完成练习中的进度（当前已完成 N 项）和草稿 N 份；历史作答与评分保留。 | 将清除这张 Paper 未完成练习中的进度（当前已完成 N 项）和草稿 N 份；历史作答与评分保留。 | 未落地 | 替换为定稿 | workbench.js:3716-3718 |
| W-36 | Agent 右栏与队列 | Agent 提议更新试卷 · {标题} | Agent 提议更新 Paper · {标题} | 未落地 | 替换为定稿 | workbench.js:3747 |
| W-37 | Agent 右栏与队列 | 这个提议无法应用：{err} ／ 请检查目标试卷或题目。 | 这个提议无法应用：{err} ／ 请检查目标 Paper 或题目。 | 未落地 | 替换为定稿 | workbench.js:3751 |
| W-38 | Agent 右栏与队列 | 确认前不会修改试卷；批准或取消后，队列仍需手动继续。 | 确认前不会修改 Paper；批准或取消后，队列仍需手动继续。 | 未落地 | 替换为定稿 | workbench.js:3833 |
| W-40 | Agent 右栏与队列 | 试卷或练习进度已变化。请核对下面的最新影响，再次点击「批准更新」/「取消更新」。 | Paper 或练习进度已变化。请核对下面的最新影响，再次点击「批准更新」/「取消更新」。 | 未落地 | 替换为定稿 | workbench.js:3894-3895 |
| W-41 | Agent 右栏与队列 | 正在重新读取试卷状态；在核对完成前不会再次提交。 | 正在重新读取 Paper 状态；在核对完成前不会再次提交。 | 未落地 | 替换为定稿 | workbench.js:3908 |
| W-43 | Agent 右栏与队列 | 上次操作未能确认；当前试卷仍待确认。请核对影响后重试。 | 上次操作未能确认；当前 Paper 仍待确认。请核对影响后重试。 | 未落地 | 替换为定稿 | workbench.js:3936 |
| W-45 | Agent 右栏与队列 | 试卷更新待确认；批准或取消后，仍需手动继续队列。 | Paper 更新待确认；批准或取消后，仍需手动继续队列。 | 未落地 | 替换为定稿 | workbench.js:3986 |
| W-51 | Agent 右栏与队列 | 试卷更新待确认；请先处理审批，再立即发送。 | Paper 更新待确认；请先处理审批，再立即发送。 | 未落地 | 替换为定稿 | workbench.js:4092 |
| W-105 | Agent 右栏与队列 | 入库已回滚 | Check 入库已回滚 | 未落地 | 替换为定稿 | workbench.js:4827；文档同步：docs/PRODUCT-MANUAL.md:404（「已回滚」子串仍在，MANUAL 不必改） |
| W-108 | Agent 右栏与队列 | 入库完成 | Check 入库完成 | 未落地 | 替换为定稿 | workbench.js:4866 |
| W-109 | Agent 右栏与队列 | 入库完成 | Check 入库完成 | 未落地 | 替换为定稿 | workbench.js:4866 |
| W-118 | Agent 右栏与队列 | 内容变更不可撤销，需要你确认。 | 这是低可逆性的内容变更，需要你明确确认。 | 未落地 | 替换为定稿 | workbench.js:4984 |
| W-119 | Agent 右栏与队列 | 这批内容会从池中删除。 | 该批写入的内容会从学习池撤销。 | 未落地 | 替换为定稿 | workbench.js:4985 |
| W-121 | Agent 右栏与队列 | 整批回滚 {batchId}？这批内容会从池中删除。 | 整批回滚 {batchId}？该批全部内容行将从池中撤销。 | 未落地 | 替换为定稿 | workbench.js:4992 |
| W-157 | Agent 右栏与队列 | 本月之外或未设截止日期：{n} 个。 | 本月之外或未排期：{n}。 | 未落地 | 替换为定稿 | workbench.js:5822 |
| W-162 | Agent 右栏与队列 | 未来 14 天暂无到期复习项 | 未来 14 天暂无到期复习项。 | 未落地 | 替换为定稿 | workbench.js:5935 |
| W-163 | Agent 右栏与队列 | 暂无带截止日期的目标 | 还没有带截止日期的目标。 | 未落地 | 替换为定稿 | workbench.js:5963 |
| W-167 | Agent 右栏与队列 | Agent 未能完成 | Agent did not complete this turn（workbench.js:3568 / 5295；agent-ui.js:221 已是中文「Agent 未能完成」） | 未落地 | 替换为定稿 | workbench.js:3568 |
| W-168 | Agent 右栏与队列 | Agent 未能完成 | Agent did not complete this turn | 未落地 | 替换为定稿 | workbench.js:3568 |
| W-169 | Agent 右栏与队列 | 本轮已取消 | This turn was cancelled | 未落地 | 替换为定稿 | workbench.js:5309 |
| W-170 | Agent 右栏与队列 | 一条消息正在发送中 | a message is already being submitted | 未落地 | 替换为定稿 | workbench.js:4420 |

### 2.10 练习流（practice-flow.js）（23 条）

| ID | 页面 | 定稿文案 | 当前文案 | 状态 | 建议动作 | 证据（file:line） |
|---|---|---|---|---|---|---|
| F-09 | 练习流（practice-flow.js） | 请检查筛选条件；若正式题目不足，可通过 Check 管线检查并补充。 | 请检查筛选条件；若正式题目不足，可通过 Check 管线检查并补充。系统不会虚构题目。 | 未落地 | 替换为定稿 | practice-flow.js:287 |
| F-30 | 练习流（practice-flow.js） | 错因 | 为什么 | 未落地 | 替换为定稿 | practice-flow.js:921 |
| F-32 | 练习流（practice-flow.js） | 尚未自评 | 尚未自评。 | 未落地 | 替换为定稿 | practice-flow.js:932 |
| F-48 | 练习流（practice-flow.js） | （删除） | 先在心里回忆，再揭示对照。 | 未落地 | 删除该文案（不要改写成别的说明句） | practice-flow.js:1022 |
| F-49 | 练习流（practice-flow.js） | 已评分 | 已评分。 | 未落地 | 替换为定稿 | practice-flow.js:1023 |
| F-55 | 练习流（practice-flow.js） | 暂无更多同类题 | 暂无更多同类题。 | 未落地 | 替换为定稿 | practice-flow.js:1128 |
| F-56 | 练习流（practice-flow.js） | 当前范围暂无可用闪卡 | 当前范围暂无可用的闪卡，请选择其他模式。 | 未落地 | 替换为定稿 | practice-flow.js:1129 |
| F-57 | 练习流（practice-flow.js） | 当前范围暂无可用小测题目 | 当前范围暂无可用的小测题目，请选择其他模式。 | 未落地 | 替换为定稿 | practice-flow.js:1130 |
| F-58 | 练习流（practice-flow.js） | 当前范围暂无可用判断题 | 当前范围暂无可用的 Yes ／ No 题目，请选择其他模式。 | 未落地 | 替换为定稿 | practice-flow.js:1131 |
| F-59 | 练习流（practice-flow.js） | 本轮相关题目已练完 | 本轮相关题目已练完。 | 未落地 | 替换为定稿 | practice-flow.js:1132 |
| F-66 | 练习流（practice-flow.js） | 请先在知识点页选择范围 | 请先在知识点视图选择范围 | 未落地 | 替换为定稿 | practice-flow.js:1429 |
| F-67 | 练习流（practice-flow.js） | 请先在知识点页选择范围 | 请先在知识点视图选择范围 | 未落地 | 替换为定稿 | practice-flow.js:1429 |
| F-68 | 练习流（practice-flow.js） | 历年原题 ／ 改编 ／ AI 生成 | 历年原题 ／ 改编 ／ AI生成 | 未落地 | 替换为定稿 | practice-flow.js:1537 |
| F-69 | 练习流（practice-flow.js） | 暂无该维度 | 本池暂无此维度 | 未落地 | 替换为定稿 | practice-flow.js:1591 |
| F-75 | 练习流（practice-flow.js） | 错因 | 为什么 | 未落地 | 替换为定稿 | practice-flow.js:921 |
| F-79 | 练习流（practice-flow.js） | 请输入 1–5 的自评 | 请输入 1-5 的评分 | 未落地 | 替换为定稿 | practice-flow.js:1790 |
| F-81 | 练习流（practice-flow.js） | 没有待评的题 | 没有待评的题。 | 未落地 | 替换为定稿 | practice-flow.js:1993 |
| F-84 | 练习流（practice-flow.js） | 保存自评 | 保存评分 | 未落地 | 替换为定稿 | practice-flow.js:2018 |
| F-85 | 练习流（practice-flow.js） | 为“{题目}”自评（1–5） | 为“{题目}”评分（1-5） | 未落地 | 替换为定稿 | practice-flow.js:2022 |
| F-87 | 练习流（practice-flow.js） | 请输入 1–5 的自评 | 请输入 1-5 的评分 | 未落地 | 替换为定稿 | practice-flow.js:1790 |
| F-88 | 练习流（practice-flow.js） | 全部评完 | 全部评完 ✓ | 未落地 | 替换为定稿 | practice-flow.js:2061 |
| F-94 | 练习流（practice-flow.js） | 错因 | 为什么 | 未落地 | 替换为定稿 | practice-flow.js:921 |
| F-103 | 练习流（practice-flow.js） | （本题无解析） | （本题无解析，请基于自身作答自评） | 未落地 | 替换为定稿 | practice-flow.js:2159 |

### 2.11 时间安排与复习负荷（3 条）

| ID | 页面 | 定稿文案 | 当前文案 | 状态 | 建议动作 | 证据（file:line） |
|---|---|---|---|---|---|---|
| P-197 | 时间安排与复习负荷 | （删除） | 目标跑道 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:1501 |
| P-199 | 时间安排与复习负荷 | （删除） | 复习节奏 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:1507 |
| P-201 | 时间安排与复习负荷 | （删除） | 每天到期、建议回看的学习项 | 未落地 | 删除该文案（不要改写成别的说明句） | pages.py:1509 |

### 2.12 左栏导航与学习者设置（1 条）

| ID | 页面 | 定稿文案 | 当前文案 | 状态 | 建议动作 | 证据（file:line） |
|---|---|---|---|---|---|---|
| P-163 | 左栏导航与学习者设置 | 练习与组卷显示自评 | 练习显示自评 | 未落地 | 替换为定稿 | pages.py:994；文档同步：docs/PRODUCT-MANUAL.md:246/256/266/278/282/288 |

### 2.13 做题经验面板（5 条）

| ID | 页面 | 定稿文案 | 当前文案 | 状态 | 建议动作 | 证据（file:line） |
|---|---|---|---|---|---|---|
| E-03 | 做题经验面板 | 暂无经验总结 | 暂无经验总结。做题后可以把可复用的方法、易错点和判断经验沉淀在这里。 | 未落地 | 替换为定稿 | experience_page.py:64 |
| E-05 | 做题经验面板 | （删除） | 做题沉淀 | 未落地 | 删除该文案（不要改写成别的说明句） | experience_page.py:73 |
| E-10 | 做题经验面板 | （删除） | 进入编辑后载入关联题目。 | 未落地 | 删除该文案（不要改写成别的说明句） | experience_page.py:84 |
| E-15 | 做题经验面板 | 暂无关联题目 | 这个知识点暂时没有关联题目。 | 未落地 | 替换为定稿 | kp-experience.js:93 |
| E-16 | 做题经验面板 | 经验总结不能为空 | 经验总结不能为空；暂时没有经验时请保持未创建状态。 | 未落地 | 替换为定稿 | kp-experience.js:122 |

---

## 3. 已落地清单（556 条 · 第 26 组不要重复动）

「定稿文案」与「当前文案」**逐字相同**，故合并成一栏。
这 556 条是防误伤清单：第 26 组改文案时若碰到这些字符串，**说明已经改过了，不要再改一次**。

### 3.1 Hub 首页（6 条）

| ID | 定稿＝当前文案 | 证据（file:line） |
|---|---|---|
| P-02 | N 个知识点 · N 道题 · N 项待复习 | pages.py:152 |
| P-04 | lesson-kit | pages.py:162 |
| P-05 | 学习工作台 | pages.py:163 |
| P-07 | 工作区列表 | pages.py:166 |
| P-08 | lesson-kit 工作台 | pages.py:169 |
| P-11 | lesson-kit | pages.py:162 |

### 3.2 外壳（顶栏/透镜/列宽/Agent 浮层）（10 条）

| ID | 定稿＝当前文案 | 证据（file:line） |
|---|---|---|
| P-09 | 章 | pages.py:202 |
| P-10 | 选择章节 | pages.py:207 |
| P-12 | 打开导航 | pages.py:235 |
| P-13 | 打开对话 | pages.py:237 |
| P-17 | 正在处理 | pages.py:274 |
| P-18 | 收起 Agent 活动 | pages.py:276 |
| P-19 | 收起 | pages.py:277 |
| P-20 | Agent 工件预览 | pages.py:285 |
| P-22 | 最新工件 | pages.py:287 |
| P-23 | 关闭工件预览 | pages.py:289 |

### 3.3 练习页（作答流）（35 条）

| ID | 定稿＝当前文案 | 证据（file:line） |
|---|---|---|
| F-17 | 揭示另一面 ／ 查看解析 | practice-flow.js:674 |
| F-38 | 上一张 | practice-flow.js:956 |
| F-39 | 下一张 | practice-flow.js:961 |
| F-40 | 上一题 | practice-flow.js:973 |
| F-41 | 下一题 ／ 返回当前题 | practice-flow.js:978 |
| F-53 | 编辑自评 ／ 填写自评 | practice-flow.js:1067 |
| F-54 | 记录并下一题 | practice-flow.js:1077 |
| P-24 | 学习 ／ 试卷 | pages.py:319 |
| P-25 | 练习 | pages.py:319 |
| P-26 | （已从界面移除） | pages.py:316（仅代码注释残留，界面已无） |
| P-27 | 继续上次练习 | pages.py:324 |
| P-28 | 未完成练习 | pages.py:324 |
| P-29 | 查看旧执行情况 | pages.py:327 |
| P-30 | 继续练习 | pages.py:798 |
| P-31 | 练习过程 | pages.py:330 |
| P-32 | 重试 | pages.py:331 |
| P-33 | 写下你的作答 | pages.py:332 |
| P-34 | 提交作答 | pages.py:333 |
| P-35 | 查看解析 | pages.py:334 |
| P-36 | 下一题 | pages.py:335 |
| P-37 | 编辑自评 | pages.py:336 |
| P-38 | 上一张 | pages.py:337 |
| P-39 | 下一张 | pages.py:338 |
| P-41 | 自评 1–5 | pages.py:340 |
| P-44 | 记录并下一题 | pages.py:343 |
| P-45 | 取消 | pages.py:344 |
| P-46 | 不会，下一题 | pages.py:347 |
| P-47 | 暂停练习 | pages.py:347 |
| P-48 | 目标与时间安排 | pages.py:349 |
| P-57 | 暂停练习 | pages.py:347 |
| P-61 | 写下你的作答 | pages.py:332 |
| P-65 | 上一题 | pages.py:399 |
| P-66 | 下一题 | pages.py:335 |
| P-123 | 查看旧执行情况 | pages.py:327 |
| P-127 | 继续练习 ／ 开始练习 | pages.py:798 |

### 3.4 试卷练习（Paper）（90 条）

| ID | 定稿＝当前文案 | 证据（file:line） |
|---|---|---|
| F-51 | 未命名题目 | practice-flow.js:1047 |
| F-104 | 来源：{evidence} | practice-flow.js:2167 |
| P-49 | 试卷练习 | pages.py:361 |
| P-50 | 选择一份试卷 | pages.py:364 |
| P-51 | 答案展示方式 | pages.py:371 |
| P-52 | 做一题显示一题 | pages.py:372 |
| P-53 | 交卷后统一显示 | pages.py:373 |
| P-54 | 开始练习 | pages.py:798 |
| P-55 | 试卷列表 | pages.py:375 |
| P-56 | 返回完成页 | pages.py:378 |
| P-58 | 提交试卷 | pages.py:380 |
| P-59 | 答题情况与题号 | pages.py:381 |
| P-60 | 你的作答 | pages.py:391 |
| P-62 | 提交答案 | pages.py:394 |
| P-63 | 自评 | pages.py:397 |
| P-64 | 题目导航 | pages.py:398 |
| P-67 | 不会 | pages.py:347 |
| P-69 | 完成练习 | pages.py:405 |
| P-70 | 查看本次答卷 | pages.py:419 |
| P-71 | 再练一次 | pages.py:420 |
| P-72 | 返回试卷列表 | pages.py:421 |
| P-164 | 来源：{evidence} | pages.py:1028 |
| P-165 | 未命名题目 | pages.py:1035 |
| Q-01 | 操作未完成 | paper-practice.js:136 |
| Q-02 | 操作未完成 | paper-practice.js:136 |
| Q-03 | 服务端未确认练习模式更新，请重试。 | paper-practice.js:350 |
| Q-04 | 无法恢复此试卷练习，请重试。 ／ 重试恢复 | paper-practice.js:361 |
| Q-05 | 练习试卷 | paper-practice.js:368 |
| Q-06 | 继续练习 ／ 暂不能继续 | paper-practice.js:379 |
| Q-07 | 当前试卷无法继续。 | paper-practice.js:380 |
| Q-08 | 开始练习 | paper-practice.js:388 |
| Q-09 | 当前试卷暂时无法开始。 | paper-practice.js:389 |
| Q-10 | 无法读取试卷。 | paper-practice.js:412 |
| Q-11 | 无法恢复当前练习。 | paper-practice.js:434 |
| Q-12 | 选择一份试卷 | paper-practice.js:441 |
| Q-15 | 无法读取本次答卷。 | paper-practice.js:459 |
| Q-16 | 练习试卷 | paper-practice.js:368 |
| Q-17 | 服务端未返回已开始的练习。 | paper-practice.js:501 |
| Q-18 | 无法开始练习。 | paper-practice.js:505 |
| Q-19 | 是 ／ 否 | paper-practice.js:528 |
| Q-20 | 未作答 | paper-practice.js:599 |
| Q-21 | 已填写，未提交 | paper-practice.js:599 |
| Q-22 | 不会 | paper-practice.js:599 |
| Q-23 | 正确 | paper-practice.js:600 |
| Q-24 | 错误 | paper-practice.js:600 |
| Q-25 | 已提交，暂无判定 | paper-practice.js:600 |
| Q-26 | 状态未知 | paper-practice.js:601 |
| Q-27 | 第N题，{状态}，当前题 | paper-practice.js:616 |
| Q-28 | 未命名题目 | paper-practice.js:640 |
| Q-29 | 题面暂不可用。 | paper-practice.js:641 |
| Q-30 | 练习试卷 | paper-practice.js:368 |
| Q-31 | 来源：{evidence} | paper-practice.js:669 |
| Q-32 | 选择所有适用答案 ／ 选择答案 | paper-practice.js:684 |
| Q-33 | 本题已标记为“不会”。 | paper-practice.js:712 |
| Q-34 | 判定：正确 | paper-practice.js:713 |
| Q-35 | 判定：错误 | paper-practice.js:714 |
| Q-36 | 本次作答没有可用的客观判定。 | paper-practice.js:715 |
| Q-37 | 参考答案 | paper-practice.js:719 |
| Q-38 | 本题没有可用答案键。 | paper-practice.js:722 |
| Q-39 | 判定依据 | paper-practice.js:725 |
| Q-40 | 解析 | paper-practice.js:729 |
| Q-41 | 本题暂无可用参考内容。 | paper-practice.js:733 |
| Q-42 | 尚未显示参考答案。交卷前不会显示判定或参考材料。 | paper-practice.js:747 |
| Q-45 | 备注（可选） | paper-practice.js:827 |
| Q-46 | 保存自评修改 ／ 保存自评 | paper-practice.js:834 |
| Q-47 | 请输入 1–5 的自评分数。 | paper-practice.js:856 |
| Q-48 | 自评尚未确认保存，编辑内容已保留。 | paper-practice.js:892 |
| Q-49 | 重试提交 ／ 提交答案 | paper-practice.js:931 |
| Q-50 | 重试交卷 ／ 提交试卷 | paper-practice.js:941 |
| Q-51 | 输入尚未确认保存；编辑已保留在此浏览器中。 | paper-practice.js:1039 |
| Q-52 | 请先作答，或选择“不会”。 | paper-practice.js:1076 |
| Q-53 | 提交未确认；答案和请求编号已保留，可重试。 | paper-practice.js:1113 |
| Q-54 | 不会状态尚未确认保存；可再次提交。 | paper-practice.js:1171 |
| Q-55 | 不会状态尚未确认保存；编辑已在此浏览器保留。 | paper-practice.js:1201 |
| Q-56 | 题目位置尚未确认保存；当前浏览位置已保留。 | paper-practice.js:1244 |
| Q-57 | 已交卷。答卷统计暂不可用，请稍后刷新查看。 | paper-practice.js:1302 |
| Q-58 | 交卷已确认，但完成页暂时无法读取答卷。 | paper-practice.js:1303 |
| Q-59 | 交卷尚未确认；草稿和请求编号已保留，请重试。 | paper-practice.js:1310 |
| Q-60 | 浏览位置尚未确认保存。 | paper-practice.js:1334 |
| Q-61 | 不会状态尚未确认保存。 | paper-practice.js:1351 |
| Q-62 | 自评尚未确认保存。 | paper-practice.js:1364 |
| Q-63 | 练习试卷 | paper-practice.js:368 |
| Q-65 | 第N题：{状态} | paper-practice.js:1474 |
| Q-66 | 查看第N题，{状态} | paper-practice.js:1475 |
| Q-67 | 无法读取本次答卷。 | paper-practice.js:459 |
| Q-68 | 暂停状态尚未确认保存。 | paper-practice.js:1522 |
| Q-69 | 练习试卷 | paper-practice.js:368 |
| Q-70 | 无法重新读取试卷。 | paper-practice.js:1607 |
| R-04 | 未命名题目 | records.py:86 |
| R-23 | 查看本次答卷 | records.py:166 |

### 3.5 目标与计划（40 条）

| ID | 定稿＝当前文案 | 证据（file:line） |
|---|---|---|
| F-64 | window.prompt('试卷名称', '新的试卷') | practice-flow.js:1376 |
| P-73 | 未命名目标 | pages.py:435 |
| P-75 | {开始日期} → {截止日期} ／ 截止 {截止日期} | pages.py:437 |
| P-76 | 查看说明与范围 | pages.py:440 |
| P-77 | 编辑 | pages.py:441 |
| P-78 | 删除 | pages.py:442 |
| P-80 | 学习安排 | pages.py:447 |
| P-81 | 长期与阶段目标 | pages.py:448 |
| P-82 | 长期与阶段目标 | pages.py:448 |
| P-83 | 添加目标 | pages.py:449 |
| P-84 | 目标名称 | pages.py:451 |
| P-85 | 目标类型 | pages.py:452 |
| P-86 | 阶段目标 ／ 长期目标 | pages.py:452 |
| P-87 | 开始日期 | pages.py:453 |
| P-88 | 截止日期 | pages.py:454 |
| P-89 | 说明 | pages.py:455 |
| P-90 | 保存目标 | pages.py:456 |
| P-91 | 取消编辑 | pages.py:457 |
| P-92 | 让 Agent 代填 | pages.py:463 |
| P-93 | 例如：期末前掌握第六章计数，重点补鸽巢和组合 | pages.py:464 |
| P-95 | 拖了 N 天 ／ 今天到期 | pages.py:506 |
| P-96 | 覆盖仍低 | pages.py:514 |
| W-02 | window.prompt('试卷名称', …) | workbench.js:3118 |
| W-03 | 删除这张试卷？做题记录不会被删除。 | workbench.js:3128 |
| W-04 | 当前还有一轮练习没有完成。重新开始会清除旧进度，继续吗？ | workbench.js:3168 |
| W-05 | 无法重新开始 | workbench.js:3175 |
| W-06 | 无法重新开始 | workbench.js:3175 |
| W-07 | 保存目标 | workbench.js:3216 |
| W-08 | 添加目标 | workbench.js:3217 |
| W-09 | 保存修改 | workbench.js:3233 |
| W-10 | 修改目标 | workbench.js:3234 |
| W-11 | 删除这个目标？ | workbench.js:3248 |
| W-12 | 删除失败：{msg} ／ 未知错误 | workbench.js:3251 |
| W-13 | 请填写目标名称。 | workbench.js:3265 |
| W-14 | 开始日期不能晚于截止日期。 | workbench.js:3270 |
| W-15 | 保存失败：{msg} ／ 未知错误 | workbench.js:3291 |
| W-16 | 先用一句话写下你的目标。 | workbench.js:3298 |
| W-18 | Agent 请求仍在提交，请稍候。 | workbench.js:3306 |
| W-20 | 已发给 Agent，等待代填… | workbench.js:3316 |
| W-21 | 发送失败：{msg} ／ 未知错误 | workbench.js:3319 |

### 3.6 知识点页与知识点列表（14 条）

| ID | 定稿＝当前文案 | 证据（file:line） |
|---|---|---|
| P-97 | 未知知识点 | pages.py:526 |
| P-98 | 重点练习 ／ 可以复习 | pages.py:22 |
| P-99 | — | pages.py:537 |
| P-100 | 知识点 ／ 当前章节 ／ 全课程 | pages.py:644 |
| P-103 | 关联题目 | pages.py:549 |
| P-104 | 重点练习 ／ 可以复习 | pages.py:22 |
| P-105 | N 题 | pages.py:151 |
| P-106 | 暂无知识点 | pages.py:639 |
| P-107 | 学习 ／ 当前章节 ／ 全课程 | pages.py:319 |
| P-108 | 知识点 | pages.py:644 |
| P-110 | 排序 | pages.py:646 |
| P-111 | 课程顺序 ／ 名称 ／ 题目数量 ／ 学习状态 ／ 重要性 | pages.py:647 |
| P-112 | 切换排序方向 | pages.py:650 |
| P-114 | 本章知识点 ／ 全部知识点 | pages.py:652 |

### 3.7 试卷列表（17 条）

| ID | 定稿＝当前文案 | 证据（file:line） |
|---|---|---|
| P-116 | 当前试卷内容校验失败：{errors} | pages.py:750 |
| P-117 | 试卷为空 | pages.py:751 |
| P-118 | 无法开始：{reason} | pages.py:752 |
| P-119 | 暂时无法开始：{reason} | pages.py:754 |
| P-120 | 无法继续旧执行：{reason} | pages.py:757 |
| P-121 | 执行状态与当前试卷不一致 | pages.py:757 |
| P-122 | 查看不可用题目 ID（N） | pages.py:762 |
| P-126 | N 题 ／ · 已完成 N/M | pages.py:151 |
| P-128 | 改名 | pages.py:799 |
| P-129 | 导出 | pages.py:800 |
| P-130 | 删除 | pages.py:442 |
| P-131 | 还没有保存的试卷 | pages.py:819 |
| P-132 | （已从界面移除） | 全仓库无命中 |
| P-133 | 返回练习 | pages.py:827 |
| P-134 | 练习 ／ 试卷 | pages.py:319 |
| P-135 | 试卷 | pages.py:319 |
| P-137 | 返回练习 | pages.py:827 |

### 3.8 记录中心与会话末统一自评（65 条）

| ID | 定稿＝当前文案 | 证据（file:line） |
|---|---|---|
| F-23 | 未判定 ／ 对 ／ 错 | practice-flow.js:861 |
| P-138 | 学习 ／ 记录 | pages.py:319 |
| P-139 | 记录 | pages.py:948 |
| P-141 | 练习 ／ 收束本轮 | pages.py:319 |
| P-142 | 会话末统一自评 | pages.py:859 |
| P-145 | 尚未评分的题目 | pages.py:865 |
| P-148 | 继续打磨弱项 | pages.py:869 |
| P-150 | 再练同类 | pages.py:872 |
| R-01 | 未判定 | records.py:80 |
| R-02 | 对 | records.py:82 |
| R-03 | 错 | records.py:84 |
| R-05 | （题目已删除） | records.py:88 |
| R-07 | 进行中 | records.py:128 |
| R-08 | 已完成 | records.py:130 |
| R-09 | 已结束 | records.py:132 |
| R-10 | Agent | records.py:136 |
| R-11 | 练习 | records.py:137 |
| R-12 | 综合题 | records.py:140 |
| R-13 | 小测 | records.py:141 |
| R-14 | 判断 | records.py:142 |
| R-15 | 闪卡 | records.py:143 |
| R-16 | 练习 | records.py:137 |
| R-17 | 逐题自评 | records.py:146 |
| R-18 | 统一自评 | records.py:147 |
| R-19 | 关闭自评 | records.py:148 |
| R-20 | 临时练习 | records.py:154 |
| R-21 | （试卷已删除） | records.py:156 |
| R-22 | N 个不会 | records.py:160 |
| R-24 | 再做一次 | records.py:169 |
| R-25 | 完成进度 | records.py:179 |
| R-27 | 已完成 N 次 | records.py:204 |
| R-29 | 最近自评 — ／ 最近自评 N ／ 5 | records.py:206 |
| R-30 | 最近不会 N 个 | records.py:207 |
| R-32 | 自评 — ／ 自评 N ／ 5 | records.py:224 |
| R-33 | 不会 N 个 | records.py:207 |
| R-35 | 未命名试卷 ／ （试卷已删除） | records.py:238 |
| R-37 | 多次练习 | records.py:247 |
| R-39 | 作答次数 | records.py:361 |
| R-40 | 完成练习 | records.py:362 |
| R-42 | 平均自评 | records.py:364 |
| R-43 | 记录摘要 | records.py:391 |
| R-46 | {日期} · N 次作答 ／ {日期}，N 次作答 | records.py:86 |
| R-47 | 最近 12 周作答日历 | records.py:577 |
| R-48 | （已从界面移除） | 全仓库无命中 |
| R-50 | N 分 | records.py:233 |
| R-51 | 自评分布 | records.py:599 |
| R-52 | 概览 ／ 练习 ／ 试卷 ／ 作答明细 ／ 错题 | records.py:605 |
| R-53 | 记录视图 | records.py:611 |
| R-55 | 查看全部记录 | records.py:638 |
| R-56 | 已载入最近 N 条，更早的记录未显示。 | records.py:644 |
| R-61 | 逐题记录 | records.py:659 |
| R-65 | N 条客观判错或卡住的记录。 | records.py:668 |
| R-66 | 最近 12 周 | records.py:678 |
| R-67 | 作答日历 | records.py:679 |
| R-68 | 最近 14 天 | records.py:683 |
| R-69 | 作答量 | records.py:684 |
| R-70 | 自评 | records.py:39 |
| R-71 | 1–5 分分布 | records.py:693 |
| R-72 | 最近练习 | records.py:697 |
| R-73 | 练习 ／ 试卷 | records.py:137 |
| R-74 | 查看全部 | records.py:698 |
| R-75 | 最近作答 | records.py:702 |
| R-76 | 逐题明细 | records.py:702 |
| R-77 | 查看全部 | records.py:698 |
| R-78 | 最近 14 天作答量 | records.py:489 |

### 3.9 Agent 右栏与队列（168 条）

| ID | 定稿＝当前文案 | 证据（file:line） |
|---|---|---|
| A-01 | 展开 Agent 活动 ／ 收起 Agent 活动 | agent-ui.js:43 |
| A-02 | 展开 ／ 收起 | agent-ui.js:44 |
| A-04 | 当前页 | agent-ui.js:58 |
| A-05 | 范围 N 个知识点 | agent-ui.js:92 |
| A-06 | 已完成 | agent-ui.js:149 |
| A-07 | 失败 | agent-ui.js:150 |
| A-08 | 进行中 | agent-ui.js:151 |
| A-09 | 执行步骤 | agent-ui.js:174 |
| A-10 | Agent 未能完成 | agent-ui.js:221 |
| A-11 | 未知错误 | agent-ui.js:223 |
| A-12 | · N 题 | agent-ui.js:259 |
| A-14 | 预览 | agent-ui.js:326 |
| A-15 | 需要确认 | agent-ui.js:362 |
| A-16 | 确认操作 | agent-ui.js:365 |
| A-17 | 此操作需要你的明确确认。 | agent-ui.js:368 |
| A-18 | 影响：{impact} | agent-ui.js:375 |
| A-19 | 取消 | agent-ui.js:383 |
| A-20 | 确认 | agent-ui.js:392 |
| P-166 | 对话 | pages.py:1055 |
| P-167 | 对话 | pages.py:1055 |
| P-168 | 新建 | pages.py:1058 |
| P-169 | 历史对话 | pages.py:1059 |
| P-171 | 选择 Agent | pages.py:1062 |
| P-172 | 选择 Agent | pages.py:1062 |
| P-174 | 当前对话 | pages.py:1067 |
| P-175 | 返回对话列表 | pages.py:1069 |
| P-176 | 切换模型 | pages.py:1071 |
| P-177 | 切换模型或 Agent（下一轮生效） | pages.py:1072 |
| P-178 | 当前模型 | pages.py:1073 |
| P-181 | 取消更新 | pages.py:1084 |
| P-182 | 批准更新 | pages.py:1085 |
| P-183 | 当前上下文 | pages.py:1087 |
| P-184 | 排队消息 | pages.py:1091 |
| P-185 | 待处理消息 | pages.py:1092 |
| P-186 | 继续队列 | pages.py:1093 |
| P-187 | 发送方式 | pages.py:1098 |
| P-188 | 使用默认方式 | pages.py:1099 |
| P-189 | 排队发送 | pages.py:991 |
| P-190 | 中断后发送 | pages.py:992 |
| P-191 | 输入问题 | pages.py:1101 |
| P-192 | 停止 | pages.py:1102 |
| P-193 | 发送 | pages.py:1103 |
| W-22 | 加入 {题目} | workbench.js:3703 |
| W-23 | 移除 {题目} | workbench.js:3704 |
| W-24 | 调整题目顺序 | workbench.js:3705 |
| W-25 | 成员与顺序未变化 | workbench.js:3706 |
| W-26 | 当前顺序 | workbench.js:3709 |
| W-27 | 更新后顺序 | workbench.js:3713 |
| W-28 | 提议顺序 | workbench.js:3752 |
| W-30 | 不会清除未完成进度或草稿；历史作答与评分保留。 | workbench.js:3721 |
| W-31 | 提议已记录 | workbench.js:3726 |
| W-32 | 已批准 | workbench.js:3727 |
| W-33 | 已取消 | workbench.js:3728 |
| W-34 | 无法应用 | workbench.js:3729 |
| W-35 | 等待确认 | workbench.js:3730 |
| W-39 | 正在提交批准并核对最新状态… ／ 正在取消并核对最新状态… | workbench.js:3866 |
| W-42 | 无法确认这次操作的结果。请刷新页面重新读取状态后再操作。 | workbench.js:3924 |
| W-44 | 正在等待当前回复停止，随后发送。 | workbench.js:3977 |
| W-46 | 队列已暂停；继续后会按顺序发送。 | workbench.js:3988 |
| W-47 | 当前回复结束后按顺序发送；列表中的消息尚未开始。 | workbench.js:3989 |
| W-48 | 该排队消息已开始或离开队列；未保存的编辑草稿保留在恢复摘要中。 | workbench.js:3998 |
| W-49 | 调整消息顺序；使用上、下方向键移动 | workbench.js:4022 |
| W-50 | 立即发送 | workbench.js:4089 |
| W-52 | 消息已提升，等待当前回复停止。 ／ 消息已提升为立即发送。 | workbench.js:4101 |
| W-53 | 消息状态已变化；已刷新队列，请确认后重试。 | workbench.js:4106 |
| W-54 | 立即发送失败：{msg} ／ 未知错误 | workbench.js:4107 |
| W-55 | 编辑 | workbench.js:4111 |
| W-56 | 请先从恢复摘要处理未保存的排队编辑草稿，再编辑其他排队消息。 | workbench.js:4114 |
| W-57 | 移出队列 | workbench.js:4122 |
| W-58 | 消息已移出队列；接受记录保留为已取消。 | workbench.js:4128 |
| W-59 | 消息已变化；已刷新队列，请再试一次。 | workbench.js:4133 |
| W-60 | 移出队列失败：{msg} ／ 未知错误 | workbench.js:4134 |
| W-61 | 队列已变化；当前显示服务器确认的顺序。 | workbench.js:4167 |
| W-62 | 调整队列顺序失败：{msg} ／ 未知错误 | workbench.js:4168 |
| W-63 | 保存 | workbench.js:4245 |
| W-64 | 消息不能为空。 | workbench.js:4248 |
| W-65 | 消息已开始执行或被修改；草稿仍保留，请复制后取消或重新读取。 | workbench.js:4270 |
| W-66 | 编辑队列消息失败：{msg} ／ 未知错误 | workbench.js:4271 |
| W-67 | 取消 | workbench.js:4275 |
| W-68 | 未完成的消息发送 | workbench.js:4315 |
| W-69 | 需要处理的消息（N） | workbench.js:4323 |
| W-70 | 发送状态未知。可用同一消息编号核对，避免重复执行。 | workbench.js:4333 |
| W-71 | 这条消息被服务端拒绝；原文仍保存在本机。 | workbench.js:4335 |
| W-72 | Agent 未完成这条消息；可以明确重试一次。 | workbench.js:4337 |
| W-73 | 核对发送状态 | workbench.js:4345 |
| W-74 | 恢复原文 | workbench.js:4350 |
| W-75 | 输入框已有草稿；为保护草稿，未覆盖它。请先清空输入框再恢复。没有执行整轮重试。 | workbench.js:4353 |
| W-76 | 已恢复原文，请编辑后重新发送。 | workbench.js:4358 |
| W-77 | 这条排队消息已开始或离开队列；未保存的编辑文本仍可手动恢复。 | workbench.js:4370 |
| W-78 | 恢复编辑草稿 | workbench.js:4375 |
| W-79 | 输入框已有草稿；为保护草稿，未覆盖它。请先清空输入框再恢复。 | workbench.js:4379 |
| W-80 | 已恢复未保存的排队编辑文本，请检查后决定是否发送。 | workbench.js:4386 |
| W-81 | 无法在本机保存发送记录；原文仍保留在恢复卡片中，请复制后再试。 | workbench.js:4405 |
| W-82 | 正在重试… ／ 正在核对发送状态… | workbench.js:4409 |
| W-83 | 发送未确认：{msg} ／ 未知错误 | workbench.js:4413 |
| W-84 | 无法在本机保存发送记录；输入尚未发送 | workbench.js:4431 |
| W-85 | 已接受，等待当前任务确认停止。 ／ 已加入队列，当前任务结束后执行。 | workbench.js:4467 |
| W-86 | 已完成 | workbench.js:4515 |
| W-87 | 失败 | workbench.js:63 |
| W-88 | 进行中 | workbench.js:4517 |
| W-89 | 已知影响：{summary} | workbench.js:4535 |
| W-90 | 影响未知 | workbench.js:4538 |
| W-91 | 执行计划 | workbench.js:4550 |
| W-92 | 执行计划 | workbench.js:4550 |
| W-93 | 执行步骤 | workbench.js:4606 |
| W-94 | 查看输出 | workbench.js:4617 |
| W-95 | 调用工具 | workbench.js:4673 |
| W-96 | 查看输出 | workbench.js:4617 |
| W-97 | 练习范围已更新 | workbench.js:4744 |
| W-98 | Agent 已代填目标字段，确认后保存。 | workbench.js:4764 |
| W-99 | 知识点 ／ 题目 ／ 闪卡 ／ 图片 ／ 未录答案键 | workbench.js:4769 |
| W-100 | 批次 {id} · {kind} | workbench.js:4787 |
| W-101 | 来源 {…} | workbench.js:4792 |
| W-102 | 工作区 {name} | workbench.js:4796 |
| W-103 | 备份 {file} | workbench.js:4798 |
| W-104 | 批次 {id} 已整批回滚 | workbench.js:4818 |
| W-106 | 批次 {id} 已整批回滚（撤销 N） ／ 池中不再包含该批内容。 | workbench.js:4971 |
| W-107 | 入库未执行 ／ 校验未通过：{err} | workbench.js:4848 |
| W-110 | 整批回滚 | workbench.js:4891 |
| W-111 | 批次 {id} | workbench.js:4902 |
| W-112 | 共 N 个批次 | workbench.js:4918 |
| W-113 | 备份 {file} | workbench.js:4925 |
| W-114 | 批次 {id} 已整批回滚（撤销 N 行） | workbench.js:4971 |
| W-115 | 批次已回滚 | workbench.js:4975 |
| W-116 | 回滚失败：{msg} ／ 未知错误 | workbench.js:4978 |
| W-117 | 整批回滚 {batchId} | workbench.js:4818 |
| W-120 | 确认回滚 | workbench.js:4986 |
| W-122 | 本轮已停止。 ／ 本轮未完成。 | workbench.js:5036 |
| W-123 | 基于此消息重试 | workbench.js:5045 |
| W-124 | 部分回答（本轮未完成） | workbench.js:5057 |
| W-125 | Agent 正在处理… | workbench.js:5091 |
| W-126 | 读取对话失败：{msg}。刷新页面可重试。 | workbench.js:5134 |
| W-127 | {model_entry} ／ {model} ／ {provider} 默认 | workbench.js:5171 |
| W-128 | 切换模型中… | workbench.js:5184 |
| W-129 | 无法切换模型：{msg} ／ 模型已切换，下一轮生效。 | workbench.js:5202 |
| W-130 | Agent 返回错误 | workbench.js:5272 |
| W-131 | Agent 失败：{msg} ／ 未知错误 | workbench.js:5300 |
| W-132 | 本轮已停止。 | workbench.js:5036 |
| W-133 | Agent 正在处理… | workbench.js:5091 |
| W-134 | 无法读取 Agent 进度，当前轮次状态暂时未知。请检查连接或重新打开此对话。 | workbench.js:5352 |
| W-135 | 无法在本机保存发送记录；消息仍留在输入框中，没有发送。 | workbench.js:5362 |
| W-136 | 正在发送… | workbench.js:5366 |
| W-137 | 发送失败：{msg} ／ 未知错误 | workbench.js:3319 |
| W-138 | 正在继续队列… | workbench.js:5389 |
| W-139 | 当前任务尚未结束，暂时无法继续队列。 ／ 继续队列失败：{msg} | workbench.js:5394 |
| W-140 | 正在停止… ／ 停止请求失败。 | workbench.js:5419 |
| W-141 | 返回对话列表 | workbench.js:5438 |
| W-142 | 未命名对话 | workbench.js:5451 |
| W-143 | · 运行中 | workbench.js:5475 |
| W-144 | 重命名对话 | workbench.js:5486 |
| W-145 | window.prompt('会话名称', …) | workbench.js:5490 |
| W-146 | 无法重命名：{msg} ／ 未知错误 | workbench.js:5498 |
| W-147 | 删除本地会话 | workbench.js:5505 |
| W-148 | 删除这个本地会话？ | workbench.js:5509 |
| W-149 | 会话运行中，暂时不能删除。 ／ 无法删除会话。 | workbench.js:5512 |
| W-150 | Agent 服务暂不可用。请稍后重试。 | workbench.js:5542 |
| W-151 | 暂无可用 Agent。请先配置一个提供方。 | workbench.js:5544 |
| W-152 | Agent 服务暂不可用。 | workbench.js:5565 |
| W-153 | 无法读取历史对话。 | workbench.js:5575 |
| W-154 | 无法新建对话：{msg} ／ 未知错误 | workbench.js:5591 |
| W-155 | 图 ／ （图缺失：{alt}） | workbench.js:5636 |
| W-158 | 共 N 项 | workbench.js:5912 |
| W-159 | 峰值 {MM.DD} · N 项 ／ 峰值 — | workbench.js:5915 |
| W-160 | 逾期 N 项 | workbench.js:5918 |
| W-161 | ，峰值 ／ ，任务偏重 | workbench.js:5925 |
| W-164 | 最近几天任务偏重（最多的一天 N 项），帮我重排一下。 | workbench.js:5972 |
| W-165 | 现有试卷 | workbench.js:3747 |
| W-171 | an unfinished practice already exists | workbench.js:3166 |

### 3.10 练习流（practice-flow.js）（70 条）

| ID | 定稿＝当前文案 | 证据（file:line） |
|---|---|---|
| F-01 | 请求未完成：{msg} ／ 未知错误 | practice-flow.js:248 |
| F-02 | 作者指定 ／ 此前答错 ／ 到期复习 ／ 薄弱点优先 ／ 范围匹配 | practice-flow.js:265 |
| F-03 | 题目 | practice-flow.js:269 |
| F-04 | 原因未提供 | practice-flow.js:273 |
| F-05 | 本轮组卷：N/M 道。 | practice-flow.js:276 |
| F-06 | 本轮无法组题（0/M 道），当前范围没有可用题目。 | practice-flow.js:277 |
| F-07 | 逐题依据：{…}。 | practice-flow.js:278 |
| F-08 | 可用题数少于请求量的知识点：{…}。 | practice-flow.js:284 |
| F-10 | 未完成练习 | practice-flow.js:357 |
| F-11 | 旧执行与当前试卷不一致，不能继续 | practice-flow.js:365 |
| F-12 | 当前试卷 N 题；旧执行 N 题。 | practice-flow.js:367 |
| F-13 | 旧进度引用了不可用题目，不能继续。 | practice-flow.js:369 |
| F-14 | 已作答 · N ／ 不会 · N ／ 待完成 | practice-flow.js:372 |
| F-15 | 旧执行进度： ／ · 不可用题目 ID：{…} | practice-flow.js:385 |
| F-16 | 是 ／ 否 | practice-flow.js:502 |
| F-18 | 草稿尚未保存：{msg} | practice-flow.js:771 |
| F-19 | 本次作答没有可用的判定。 | practice-flow.js:811 |
| F-20 | 回答正确。 | practice-flow.js:819 |
| F-21 | 回答错误。 {错因} | practice-flow.js:820 |
| F-22 | 本题未录入答案键，请对照课本或解析自评。 | practice-flow.js:850 |
| F-24 | 历史作答 N 条 | practice-flow.js:878 |
| F-25 | 选择答案 | practice-flow.js:889 |
| F-26 | （未作答） | practice-flow.js:911 |
| F-27 | 本题当时标记为“不会”。 | practice-flow.js:913 |
| F-28 | 本次提交尚未确认保存，确认前不能为这次作答自评。 | practice-flow.js:915 |
| F-29 | 未录入答案键 | practice-flow.js:919 |
| F-31 | 答案 | practice-flow.js:924 |
| F-33 | 我的自评： | practice-flow.js:933 |
| F-34 | 我的作答 | practice-flow.js:938 |
| F-35 | 我的作答 | practice-flow.js:938 |
| F-36 | 我的自评 | practice-flow.js:933 |
| F-37 | 查看参考答案与解析 | practice-flow.js:945 |
| F-42 | 回看上一题 | practice-flow.js:991 |
| F-43 | 返回当前题 | practice-flow.js:978 |
| F-44 | 反向 ／ 正向 | practice-flow.js:1009 |
| F-45 | 另一面 | practice-flow.js:1012 |
| F-46 | 提示面 | practice-flow.js:1016 |
| F-47 | 闪卡 | practice-flow.js:2085 |
| F-50 | 回看 · 练习题 ／ 练习题 | practice-flow.js:1044 |
| F-52 | 保存自评 | practice-flow.js:1064 |
| F-60 | 当前知识点还有一轮未完成练习。确定重新开始吗？ | practice-flow.js:1318 |
| F-61 | 当前还有一轮练习没有完成。确定开始新的练习吗？ | practice-flow.js:1319 |
| F-62 | 当前范围没有可用闪卡。 | practice-flow.js:1335 |
| F-63 | 试卷只保存题目；闪卡请直接开始练习。 | practice-flow.js:1373 |
| F-65 | 当前范围没有可保存的题目。 | practice-flow.js:1383 |
| F-70 | 来源类型 ／ 题目来源方式 ／ 考查年份 ／ 来源文档 | practice-flow.js:1597 |
| F-71 | 清除全部 | practice-flow.js:1603 |
| F-72 | 关闭 | practice-flow.js:1604 |
| F-73 | 筛选维度读取失败。 | practice-flow.js:1638 |
| F-74 | 未录入答案键 | practice-flow.js:919 |
| F-76 | 答案 | practice-flow.js:924 |
| F-77 | 编辑自评 ／ 填写自评 | practice-flow.js:1067 |
| F-78 | 本次作答尚未确认保存，不能写入自评。 | practice-flow.js:1783 |
| F-80 | 本轮练习已提前结束。 | practice-flow.js:1903 |
| F-82 | 输入 1–5 | practice-flow.js:2007 |
| F-83 | 可选备注 | practice-flow.js:2010 |
| F-86 | 为“{题目}”添加备注 | practice-flow.js:2026 |
| F-89 | 保存失败 | practice-flow.js:2064 |
| F-90 | 反向 ／ 正向 | practice-flow.js:1009 |
| F-91 | 闪卡 · {方向} | practice-flow.js:2082 |
| F-92 | 另一面 | practice-flow.js:1012 |
| F-93 | 答案 | practice-flow.js:924 |
| F-95 | 解析 | practice-flow.js:2102 |
| F-96 | （本题无解析） | practice-flow.js:2103 |
| F-97 | 练习题 | practice-flow.js:1044 |
| F-98 | 我的作答 | practice-flow.js:938 |
| F-99 | （未作答） | practice-flow.js:911 |
| F-100 | 教材解析 ／ 解析 | practice-flow.js:2140 |
| F-101 | 教材答案 | practice-flow.js:2151 |
| F-102 | 解析 | practice-flow.js:2102 |

### 3.11 时间安排与复习负荷（14 条）

| ID | 定稿＝当前文案 | 证据（file:line） |
|---|---|---|
| P-194 | 时间安排 | pages.py:1497 |
| P-195 | （已从界面移除） | 全仓库无命中；文档同步：docs/PRODUCT-MANUAL.md:196 |
| P-196 | 时间安排 | pages.py:1497 |
| P-198 | 本月安排 | pages.py:1502 |
| P-200 | 未来 14 天复习负荷 | pages.py:1508 |
| P-202 | 让 Agent 看看 | pages.py:1510 |
| P-203 | 复习负荷摘要 | pages.py:1512 |
| P-204 | 共 N 项 | pages.py:1513 |
| P-205 | 峰值 — | pages.py:1514 |
| P-206 | 逾期 N 项 | pages.py:1515 |
| P-207 | 未来 14 天每日到期复习项 | pages.py:1518 |
| P-208 | 最近没有安排在日历上。 | pages.py:1521 |
| W-156 | {年}年{月}月 | workbench.js:5792 |
| W-166 | 较多 | workbench.js:5971 |

### 3.12 左栏导航与学习者设置（12 条）

| ID | 定稿＝当前文案 | 证据（file:line） |
|---|---|---|
| P-151 | 练习 ／ 试卷 ／ 知识点 ／ 知识图谱 ／ 记录 | pages.py:319 |
| P-152 | 优先回看 | pages.py:968 |
| P-153 | 本章知识点 ／ 全部知识点 | pages.py:652 |
| P-154 | 暂无明确薄弱证据 ／ 暂无提醒 | pages.py:974 |
| P-155 | 工作区 | pages.py:981 |
| P-156 | 切换工作区 | pages.py:982 |
| P-157 | 工作台导航 | pages.py:984 |
| P-158 | 页面 | pages.py:985 |
| P-159 | 设置 | pages.py:888 |
| P-160 | 运行中发送方式 | pages.py:990 |
| P-161 | 排队发送 | pages.py:991 |
| P-162 | 中断后发送 | pages.py:992 |

### 3.13 做题经验面板（15 条）

| ID | 定稿＝当前文案 | 证据（file:line） |
|---|---|---|
| E-01 | 典型题目 | experience_page.py:54 |
| E-02 | 编辑 | experience_page.py:59 |
| E-04 | 新增经验 | experience_page.py:67 |
| E-06 | 做题经验 | experience_page.py:73 |
| E-07 | 删除 | experience_page.py:76 |
| E-08 | 经验总结（Markdown） | experience_page.py:81 |
| E-09 | 典型题目（可选） | experience_page.py:83 |
| E-11 | 保存 | experience_page.py:88 |
| E-12 | 取消 | experience_page.py:89 |
| E-13 | 保存失败 | kp-experience.js:39 |
| E-14 | 正在载入关联题目… | kp-experience.js:82 |
| E-17 | 关联题目仍在载入，请稍后再保存。 | kp-experience.js:126 |
| E-18 | 这份经验刚刚被其他编辑更新，请刷新后合并你的修改。 | kp-experience.js:139 |
| E-19 | 删除这份做题经验？知识点、题目和学习记录不会受影响。 | kp-experience.js:149 |
| E-20 | 这份经验刚刚被其他编辑更新，请刷新后再删除。 | kp-experience.js:156 |

---

## 4. 统计与优先级建议

### 4.1 未落地 115 条的分布

| 页面 | 未落地条数 | 其中「术语统一」 | 其中「用户可见改写」 |
|---|---|---|---|
| Hub 首页 | 3 | 2 | 1 |
| 外壳（顶栏/透镜/列宽/Agent 浮层） | 5 | 3 | 2 |
| 练习页（作答流） | 3 | 3 | 0 |
| 试卷练习（Paper） | 6 | 3 | 3 |
| 目标与计划 | 5 | 2 | 3 |
| 知识点页与知识点列表 | 4 | 0 | 4 |
| 试卷列表 | 4 | 0 | 4 |
| 记录中心与会话末统一自评 | 25 | 3 | 22 |
| Agent 右栏与队列 | 28 | 23 | 5 |
| 练习流（practice-flow.js） | 23 | 11 | 12 |
| 时间安排与复习负荷 | 3 | 0 | 3 |
| 左栏导航与学习者设置 | 1 | 0 | 1 |
| 做题经验面板 | 5 | 0 | 5 |
| **合计** | **115** | **50** | **65** |

### 4.2 两类改动的区别（落地时的验收口径不同）

| 类别 | 条数 | 特征 | 验收口径 |
|---|---|---|---|
| **A 类 · 术语统一** | 50 | 只换词不动句式：把非契约词换成 GLOSSARY 里的中文名 | grep 旧词 **零命中** + grep 新词 **有命中**；不要求句子重写 |
| **B 类 · 用户可见改写** | 65 | 删注释句 / 空态句式统一 / 去掉解释性修饰 | 界面上的**整句话**变了；逐条走查「改前 → 改后」语义等价 |

**A 类（术语统一）逐条**：`Paper` → 「试卷」是最大一族（W-29 / W-36 / W-37 / W-38 / W-40 / W-41 / W-43 / W-45 / W-51 / P-179）、
`正确率` → 「判定」一族（R-28 / R-31 / R-41）、`评分` → 「自评」一族（F-79 / F-84 / F-85 / F-87 / Q-44）、
英文兜底译中文（W-167…W-170）、`Check 入库` → 「入库」（W-105 / W-108 / W-109）、
`Agent activity` / `Artifact` / `Congratulations!`（P-16 / P-21 / P-68）、
实现层词换用户词（P-01 / P-03 / P-40 / P-42 / P-43 / F-66 / F-67 / F-69 / W-01 / W-157 / W-118 / W-119 / W-121）、
`组卷` → 「试卷」（A-03 / A-13）。

### 4.3 建议的落地顺序

| 优先级 | 条数 | 内容 | 为什么排这个位置 |
|---|---|---|---|
| **P0 · 契约漂移 + 文档同步义务** | 10 | A-13、P-79、P-163、P-179、R-28、R-31、R-41、W-105、W-108、W-109 | 与 spec / GLOSSARY / MANUAL 冲突，改文案必须**同 PR 改文档**，漏一条就是新的 contract drift |
| **P1 · 术语统一** | 41 | A-03、F-30、F-58、F-66、F-67、F-69、F-75、F-79、F-84、F-85、F-87、F-94、P-01、P-03、P-16、P-21、P-40、P-42、P-43、P-68、P-94、Q-44、Q-64、W-01、W-29、W-36、W-37、W-38、W-40、W-41、W-43、W-45、W-51、W-118、W-119、W-121、W-157、W-167、W-168、W-169、W-170 | 用户可见但改动面窄、语义零风险；集中做完可一次性消掉「Paper / 正确率 / 评分」三类混排 |
| **P2 · 用户可见改写** | 63 | E-03、E-05、E-10、E-15、E-16、F-09、F-32、F-48、F-49、F-55、F-56、F-57、F-59、F-68、F-81、F-88、F-103、P-06、P-14、P-15、P-101、P-102、P-109、P-113、P-115、P-124、P-125、P-136、P-140、P-143、P-144、P-146、P-147、P-149、P-170、P-173、P-180、P-197、P-199、P-201、Q-13、Q-14、Q-43、R-06、R-26、R-34、R-36、R-38、R-44、R-45、R-49、R-54、R-57、R-58、R-59、R-60、R-62、R-63、R-64、W-17、W-19、W-162、W-163 | 影响版面与语气，要等空态形态（插画 + 一句 + 满宽主按钮）与页面骨架一起收口 |
| **P3 · 不属第 26 组** | 1 | P-74 | 文案本身与定稿一致，但**值域 / 口径待核**，要在第 26 组顺手改就等于替所有者做裁决 |

> ⚠️ **§4.1/§4.2 与 §4.3 是两个正交的切法**：
> §4.1/§4.2 按**改动的性质**分（术语统一 / 用户可见改写）；
> §4.3 按**落地顺序**分（P0 契约漂移 → P1 术语统一 → P2 用户可见改写 → P3 待裁决）。
> 两条 P0（`P-79` / `P-163`）既属「用户可见改写」又属 P0；因此 §4.3 的条数不能与 §4.2 相加。

### 4.4 「用户可见」与「术语统一」怎么分——判定依据

本清单把 115 条待办分成两类，依据是 **copy-table §2 自己的「理由」列**：

- **术语统一**：定稿与当前的差别**只在词**（`Paper`→`试卷`、`正确率`→`判定`、`评分`→`自评`、`组卷`→`试卷`、`视图`→`页`、`本池`→`该`），句式、字数、信息量都不变。
- **用户可见改写**：定稿与当前的差别是**整句**——删掉注释句、把空态改成短句、去掉解释性修饰（`仍保留` / `详情见下方折叠项` / `请选择其他模式` / `不影响继续练习`）。

两类都是用户可见的。区别在于**验收方式**：A 类只需 grep 前后词，B 类要逐句走查语义等价。

---

## 5. 待裁决项（第 26 组不要自行拍板）

| # | 涉及条目 | 问题 | 建议归属 |
|---|---|---|---|
| 1 | `P-74` 覆盖进度 | copy-table §2.5 给的定稿是 `覆盖进度：{v}`，但同格标注「**值域待核：不得显示百分比**」。当前 `pages.py:436` 直接把 `goal.coverage_progress` / `goal.progress` 打印出来，**值域未经核**。GLOSSARY「覆盖」_Avoid_「完成度百分比」 | `docs/DATA_MODEL.md` + 所有者裁决：要么确认该字段是离散计数，要么改成分段口径 |
| 2 | `R-28` / `R-31` / `R-41` 正确率 → 判定 | copy-table 已给定稿口径（`最近判定 N/M` / `判定正确 N/M` / `客观题判定`），但 §6.6 **D-09** 明确写着「**落地属于 proposal 已登记的另案**，本表只锁定文案口径，不改统计实现」。第 26 组若只换词不换值域（`{accuracy*100:.0f}%` 仍是百分比），等于把禁用词从标签挪到了数值里 | 与 D-09 一起裁决：统计实现改不改 |
| 3 | `W-105` `Check 入库已回滚` → `入库已回滚` | spec `workbench-ui/spec.md:916` 要求结果卡显示 `已回滚`；定稿 `入库已回滚` **包含**该子串，字面要求被满足。copy-table §6.6 **D-08** 登记为「待核：是否要求逐字相等」 | 问所有者：spec 按「包含」还是「逐字」判定 |
| 4 | `A-13` `打开组卷页` → `打开试卷页` | copy-table §6.6 **D-05** 已在本变更内裁决（按 PRODUCT-MANUAL:440 改代码），但 A-03（页面名 `组卷`→`试卷`）与左栏导航 `试卷` 在同一屏上会并存——**改完要确认不会两个地方都叫「试卷」**而失去区分 | 落地后走查 |
| 5 | `P-163` `练习显示自评` → `练习与组卷显示自评` | spec `workbench-ui/spec.md:1051` 点名了这串字，但**同 PR 必须同步 MANUAL 的 6 处引用**（246/256/266/278/282/288） | 已在本变更内裁决（D-01），但文档同步别漏 |
| 6 | `G-01…G-32` 图谱页 32 条 | 范围外（§0.4）。**本清单不列**，但第 26 组若按「全站文案」去扫图谱页会踩线 | 归 `graph-node-visual-language` change |
| 7 | `W-171` `an unfinished practice already exists` | **禁改**：从不渲染，只被 `error.message === "..."` 比较，改它会破坏与服务端错误串的对齐 | 不动 |

---

## 6. 与第 26 组任务书的对接建议

`tasks.md` 第 26 组：

> **26.1** 按 `design-notes/copy-table.md` 执行全站文案定稿：**一个中文语气**、一个标签 / 一句话里不混中英；空态 = 插画 + 一句 + 满宽主按钮（按钮文案即动作）。验证：逐页核对 copy-table 的「改前 → 改后」条目全部落地；页面上无中英混排标签残留；改动前后语义逐条核对。
>
> **26.2** 少字原则删注释：能删的界面注释**直接删除**（不是换成更漂亮的说明文字）；改造后界面上的说明性文字**数量不增加**。验证：交付一张删除前后信息量核对表，逐条说明删除理由；界面文字条数对比不增。
>
> **26.3** 阶段验收：跑 AGENTS.md 四条验证命令；按 `acceptance.md` §1 的「文字内容除文案清理项外应逐字一致」走查；同步 `docs/PRODUCT-MANUAL.md` 对应章节。

### 6.1 对 26.1 的建议

1. **直接用本清单第 2 节当验收台账**：115 条待办逐条有「当前文案 → 定稿文案」，验收时把「当前文案」改成「定稿文案」逐条打勾即可，不需要再从 copy-table 反查。
2. **「一个中文语气」这一条**，本清单已经算清了它的**全部落点**：

   | 中英混排来源 | 条数 | 对应 ID |
   |---|---|---|
   | `Paper` | 10 | P-179、W-29、W-36、W-37、W-38、W-40、W-41、W-43、W-45、W-51 |
   | `Check 入库` | 3 | W-105、W-108、W-109 |
   | `Yes / No` | 1 | F-58 |
   | `AI生成`（缺空格） | 1 | F-68 |
   | 英文兜底（渲染到界面） | 4 | W-167、W-168、W-169、W-170 |
   | 纯英文标签 | 3 | P-16（Agent activity）、P-21（Artifact）、P-68（Congratulations!） |
   | `组卷` vs `试卷` 术语不统一 | 2 | A-03、A-13 |
   | `正确率` / `客观正确` | 4 | R-28、R-31、R-41、Q-64（另见 §5-2 的口径问题） |
   | `评分` / `自评分` / `熟悉程度` | 6 | P-40、F-79、F-84、F-85、F-87、Q-44 |
   | `卡点或心得` → `备注` | 2 | P-42、P-43 |
   | **合计** | **36** | |

   落地后建议直接跑一次全站 grep 复核：

   ```bash
   grep -rn "Paper\|Agent activity\|Artifact\|Congratulations\|Check 入库\|Yes / No\|AI生成" \
   workbench/server/ | grep -v "^\s*#"
   grep -rn "正确率\|客观正确\|熟悉程度\|自评分" workbench/server/
   ```

   （**注意**：`workbench.js` 里的 `Paper` 有非文案用途——变量名 / 协议字段 / 注释不在此列；
   `practice-flow.js` 的 `Check 管线` 是 GLOSSARY 条目名，**保留不译**。）

3. **「空态 = 插画 + 一句 + 满宽主按钮」**：本清单里与空态直接相关的待办共 **22 条**（E-03、E-15、P-79、P-115、P-136、P-140、P-143、P-146、P-149、P-170、P-173、Q-13、Q-14、Q-43、Q-64、R-06、R-26、R-44、R-45、R-49、W-162、W-163），建议**单独一个批次**做（它们牵涉页面骨架，不适合和纯术语替换混在一个 PR 里）：

   > 其中 **P-131「还没有保存的试卷」已经落地**（`pages.py:819`），
   > 说明**试卷列表页的空态骨架已经改过了**（空态插画 + 一句 + 满宽主按钮已在位），
   > 第 26 组在这张页上只剩 `P-115` / `P-136` 两条纯文案。

### 6.2 对 26.2 的建议

**「删」类共 27 条未落地**，可直接用作 26.2 的「删除前后信息量核对表」的骨架——copy-table §3 已经给每条写好了「删后由什么承担」，第 26 组只需把那条理由搬进核对表。

**建议按这个顺序落地「删」**（每条都是纯删除，风险低、收益直接）：

| 序 | ID | 页面 | 删什么 | 删后由什么承担（copy-table §3 已写） |
|---|---|---|---|---|
| 1 | P-06 | Hub 首页 | 选择一个工作区，从最需要回看的地方继续。 | 工作区卡片（名称 + 三个计数）+ 卡片点击态 |
| 2 | P-101 | 知识点页与知识点列表 | 先读正文，再按需要继续练习相关题目。 | 页面结构本身（正文纸 + 关联题目纸） |
| 3 | P-102 | 知识点页与知识点列表 | 练习入口 | `关联题目` 标题 |
| 4 | P-109 | 知识点页与知识点列表 | 阅读课程内容与关联题目；练习请使用已有试卷。 | 页面标题 + 排序工具条 |
| 5 | P-113 | 知识点页与知识点列表 | 当前排序 | 排序下拉 + ↑ 按钮 |
| 6 | P-125 | 试卷列表 | 试卷 | 试卷卡标题 |
| 7 | P-136 | 试卷列表 | 每份试卷独立保存作答进度，切换后可以继续。 | 卡片上的进度计数 + 「继续练习」按钮 |
| 8 | P-140 | 记录中心与会话末统一自评 | 练习轮次、试卷作答和逐题记录都在这里；统计只从已有学习记录实时计算。 | 记录页签（概览/练习/试卷/作答明细/错题）+ 仪表盘卡片 |
| 9 | P-143 | 记录中心与会话末统一自评 | 只补充尚未评分的题目与闪卡；已写入的记录不会重复出现。 | `尚未评分的题目` 列表 + 空态 |
| 10 | P-144 | 记录中心与会话末统一自评 | 待补充 | 标题 `尚未评分的题目` |
| 11 | P-146 | 记录中心与会话末统一自评 | 逐题输入 1–5 分；点击保存前不会写入学习记录。 | 1–5 输入控件 + 「保存」按钮 + 未保存时的状态点 |
| 12 | P-147 | 记录中心与会话末统一自评 | 下一步 | `继续打磨弱项` 标题 + 「再练同类」满宽按钮 |
| 13 | P-149 | 记录中心与会话末统一自评 | 重新开始时再次选择自评方式。 | 左栏「设置 / 练习显示自评」开关 |
| 14 | R-34 | 记录中心与会话末统一自评 | 这张试卷的题目或顺序曾变化；下面按每次实际内容分别显示，不合并成一条趋势。 | 每轮一张卡片（天然分开，不合并） |
| 15 | R-36 | 记录中心与会话末统一自评 | 同一试卷 | `多次练习` 标题 |
| 16 | R-38 | 记录中心与会话末统一自评 | 只使用每次实际留下的作答、自评和不会记录。 | 每轮卡片里的计数与 `正确 N/M` / `自评 N/5` / `不会 N 个` |
| 17 | R-57 | 记录中心与会话末统一自评 | 练习 ／ 试卷 | `练习轮次` 标题 |
| 18 | R-59 | 记录中心与会话末统一自评 | 完成或替换一轮练习后保留快照；试卷记录保留当时的试卷名称。 | 卡片上的时间戳 + 试卷名 |
| 19 | R-60 | 记录中心与会话末统一自评 | 作答明细 | `逐题记录` 标题 |
| 20 | R-63 | 记录中心与会话末统一自评 | 错题 | `错题` 标题 |
| 21 | P-173 | Agent 右栏与队列 | 先选一个起始 Agent；之后可在同一对话里切换可用模型与 Agent。 | `选择 Agent` 面板 + 对话头部的模型下拉 |
| 22 | F-48 | 练习流（practice-flow.js） | 先在心里回忆，再揭示对照。 | 按钮 `揭示另一面` + 卡片两面的 `提示面` / `另一面` 标题 |
| 23 | P-197 | 时间安排与复习负荷 | 目标跑道 | 月历里的细轨道本身 |
| 24 | P-199 | 时间安排与复习负荷 | 复习节奏 | `未来 14 天复习负荷` 标题 |
| 25 | P-201 | 时间安排与复习负荷 | 每天到期、建议回看的学习项 | 负荷柱 + `共 N 项` / `峰值` / `逾期` 摘要 |
| 26 | E-05 | 做题经验面板 | 做题沉淀 | `做题经验` 标题 |
| 27 | E-10 | 做题经验面板 | 进入编辑后载入关联题目。 | fieldset 标题 `典型题目（可选）` + 载入中占位 `正在载入关联题目…` |

**注意事项**：

- **P-195（删 kicker `实验视图`）必须同 PR 改 `docs/PRODUCT-MANUAL.md:196`**——
  MANUAL 现在写着「全宽「时间安排」卡（**标注了「实验视图」——形态还会迭代**）」，
  kicker 一删这句话就成了假陈述（copy-table §6.2 M-02 已登记）。
- **P-132（删空态说明）**落地后，空态只剩「插画 + 一句 `还没有保存的试卷` + 满宽主按钮」，
  而**主按钮 `返回练习` 在别处**——copy-table §2.7 末尾那条「待核」（是否新增直达 Agent 的主按钮）
  **尚未裁决**，第 26 组不要自行加按钮（那是新增功能，超出文案清理范围）。
- **P-140 / P-143 / P-146 / P-149** 这四条删完后，**页头摘要区会变成只有标题**——
  「记录」页与「会话末统一自评」页的页头会显得很空。copy-table 判定可接受，
  但落地后建议走查一眼版面（`acceptance.md` §1）。
- **R-48（删 `颜色只表示当天的作答次数。`）** 与 26.2「说明性文字数量不增加」直接相关：
  新的作答日历是**热力方块（填色 + 高度双编码）**，这句话既在解释图形，
  又建立在「只靠颜色」的旧口径上——删掉才是对的。

### 6.3 对 26.3 的建议

26.3 要求「同步 `docs/PRODUCT-MANUAL.md` 对应章节」。本清单已经把**需要同步的条目**
标出来了（各行「证据」列末尾带「文档同步：」）：

| ID | 同 PR 必须同步的 MANUAL 位置 | 备注 |
|---|---|---|
| P-79 | `docs/PRODUCT-MANUAL.md:58` | 引号内的句子改成「暂无目标」 |
| P-195 | `docs/PRODUCT-MANUAL.md:196` | 删掉「标注了「实验视图」——形态还会迭代」 |
| P-163 | `docs/PRODUCT-MANUAL.md:246/256/266/278/282/288` | 六处引用一起改 |
| P-179 | `docs/PRODUCT-MANUAL.md:462` | 引号内改成「试卷更新待确认」 |
| W-17 | `docs/PRODUCT-MANUAL.md:371` | **不必改**（前半句逐字保留） |
| W-105 | `docs/PRODUCT-MANUAL.md:404` | **不必改**（「已回滚」子串仍在） |
| A-13 | `docs/PRODUCT-MANUAL.md:440` | **不必改**（按文档改代码） |

另：copy-table §6.2 M-01…M-13 已逐条列过 MANUAL 的引用关系，**第 26 组照它走即可**。

---

## 7. 附录：证据的复算方式

本清单每一行的「当前文案」都可以用一条 grep 复现（把占位符换成实际值）：

```bash
# 例：P-01 未落地
grep -n "数据库读不了" workbench/server/pages.py
#   → pages.py:149:    detail = f"数据库读不了：{str(ws['error']).splitlines()[0]}"

# 例：W-167 / W-170 未落地（英文兜底会渲染）
grep -n "Agent did not complete this turn\|a message is already being submitted" \
  workbench/server/static/workbench.js
#   → workbench.js:3568 / workbench.js:5295 / workbench.js:4420

# 例：已落地的 4 条「删」（界面已无，仅注释残留）
grep -rn "选择已有试卷开始\|请在右侧对话中让 Agent 组卷\|实验视图\|颜色只表示当天的作答次数" \
  workbench/server/
#   → 只剩 pages.py:316 的代码注释，其余零命中
```

**判定口径的一句话总结**：

- `留` → 原文还在 = 已落地；
- `删` → 原文不在 = 已落地；
- `改` / `译` → 原文还在 = 未落地，定稿文本已在别处出现也算未落地（原文没删干净）。

**本次核查未做的事**（留给第 26 组或另案）：

- **没有改任何实现文件**——`pages.py` / `records.py` / `experience_page.py` / `static/*.js` 一字未动。
- **没有改 `docs/` 或 `openspec/` 下的其它文件**。
- **没有核图谱页 32 条**（范围外）。
- **没有核 `W-171`**（禁改协议串）。
