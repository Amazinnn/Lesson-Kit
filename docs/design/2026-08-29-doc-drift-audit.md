# 文档漂移审计报告（2026-08-29）

> 结论先行：**漂移 = (a) 旧文档留白 + (b) 2026-08-29 的新增规格把一种解读
> 固化**。复习页从未被任何在先文档定义或与 Yes/No 关联；日历/任务量曲线的
> 前端位置从未被记录。三页导航与 Yes/No 属于练习页模式，是记录在案的决定。

## 审计方法

对 `docs/REQUIREMENTS.md`、`docs/FUTURE-DEVELOPMENT-NOTES.md`、
`docs/DISCUSSION-RECORD.md`、`docs/adr/*`、`openspec/changes/archive/*`
（20 个变更）、`openspec/specs/*`、`changelog/*` 中关于三个主题的每一处
提及做逐条引文与时间线对照。执行于 2026-08-29，由设计会话发起。

## 主题一：复习页 / review page

| 来源 | 位置 | 原文 | 时间 |
|---|---|---|---|
| DISCUSSION-RECORD.md | L368（B7 后置清单） | 「……速成模式视图；**复习页（前端）**；记忆卡片页（前端）；Agent 组织面板……」——仅名字，无定义 | 2026-08-28 归档 |
| 2026-08-16-workbench-ui/proposal.md | L45 | 「Explicitly deferred: review page, memory cards, agent organization panel, batch reveal, any extended summary, generate bridge op, Scoropic mode.」——仅名字 | 2026-08-16 |
| 2026-08-16-workbench-ui/design.md | L27 | 「Non-Goals: review page……」——同上 | 2026-08-16 |
| ARCHITECTURE.md | L41 | 「queries.py # 视图查询（hub 统计、练习页、**复习页数据**）」——模块注释 | 2026-08-16 |
| review-workbench spec | L124-127 | 「WHEN the workspace home is opened THEN it shows a due-items summary……alongside (never instead of) the weak-point list」——到期摘要的原始设计位置是**工作区主页** | v1 |

**结论 A**：在 2026-08-28 之前，不存在任何把复习页定义为其内容或将其与
Yes/No 关联的文档。「复习页」只是一个挂名的后置条目。

## 主题二：Yes/No（判断）的归属

| 来源 | 位置 | 原文 |
|---|---|---|
| FUTURE-NOTES.md | L80 | 「**Yes/No 更适合作为 Micro Quiz 的一种回答类型，而不是单独维护一整套会话系统**」 |
| FUTURE-NOTES.md | L313/L322（2026-08-28 原话记录） | 「每一次练习它就只能完成一种题目……**卡片、或者判断、或者综合三种中的一种**」「练习启动卡强制选择且只选择一次综合、卡片、判断中的一种」 |
| REQUIREMENTS.md | L235/L249 | 「试卷、Flash Card 或 Yes/No 入口」「综合/闪卡/判断题型」 |
| daily-learning-plan spec | L18 | 「the existing exam, Flash Card, or Yes/No practice path」 |
| micro-quiz-content spec | L76 | 「The practice page SHALL render micro quizzes by quiz type: yes/no buttons」（2026-08-29 新增，忠实于在先记录） |

**结论 B**：全部在先文档一致把 Yes/No 定位在**练习页的模式**里；
专门的 Yes/No 页面在零份文档中出现。

## 主题三：时间安排（日历 + 任务量曲线）

| 来源 | 位置 | 原文 |
|---|---|---|
| FUTURE-NOTES.md | L207-213（2026-08-27 原话记录） | 「以一个日历视图来把目标卡放进去……**我还没有具体的网页前端构思**」「日历视图和每日任务量曲线暂列 Experimental，**前端设计以后再做**」 |
| REQUIREMENTS.md | L239/L254 | 「日历、任务量曲线……继续作为后续实验方向」 |
| complete-learning-workbench proposal | L22-24 | 「Keep calendar, workload curve……as documented future work rather than fake controls.」 |

**结论 C**：日历/曲线被有意记录为「前端位置未定」的实验方向；
任何页面（复习页或练习页）都未被指名。所有者后来的期望（练习页、
与学习安排并列）在 2026-08-29 之前无文字记录，只能来自未落档的口头讨论。

## 新增规格与在先文档的对照（2026-08-29 两天内合并）

| 新增 | 对照结论 |
|---|---|
| workbench-ui「Review page with card sessions」（第 4 导航页） | **超出**在先文档：页面从未被定义；与三页导航记录（DISCUSSION-RECORD L259/L353）相抵触，甚至与本 spec 自己的 Purpose 段（仍写三页）不一致 |
| review-page「Directional card session」 | **新的落位决定**：ADR 0019 只说「offered by the UI, never required」，未指名页面 |
| calendar-workload「inside the review page」 | **超出**在先文档（未指名页面），并与所有者期望（练习页并列）直接冲突；提案中「练习页顶部已较满」是新的 UX 论证而非既定需求 |
| micro-quiz-content | **忠实**：几乎逐字实现 FUTURE-NOTES 练习活动的分化与「最小 Micro Quiz 先只支持 Yes/No」 |
| 副作用 | docs/REQUIREMENTS.md 与 docs/ARCHITECTURE.md 的三页描述未同步更新，docs/ 与 openspec/specs/ 互相矛盾 |

## 总裁定

**(c) 两者皆有**：

1. **留白在先**：「复习页」三次被挂名、零次被定义；日历前端被明确推迟。
   空白本身是合规的（后置=未想清楚不落档），但缺少「此名未定义」的警示。
2. **固化在后**：2026-08-29 的 review-page / calendar-workload 两个提案用
   自己的解读填充了空白并通过校验合并——strict 校验只查结构，不查意图。
   这是漂移被固化的具体机制。
3. **纠偏依据**：所有者的口头澄清（复习页 = Yes/No 功能的家；时间安排 =
   练习页与学习安排并列）+ 三页导航的两次在案纠正 + v1 到期摘要原始位置。
   处置见 `openspec/changes/consolidate-practice-views/`。

## 防复发约定

- 后置清单中的挂名条目在启动设计时，第一步必须向所有者确认定义，
  并把确认结果先写入 proposal 的 Why，再写 What Changes；
- 「页面级」新增（新增导航项/新增页面）一律视为大决定，提案 PR 必须
  单独向所有者展示页面清单变化，不得夹带在实现 PR 中；
- 归档时 Purpose 段为必填项（openspec 校验不查内容，靠 tasks 清单约束）。
