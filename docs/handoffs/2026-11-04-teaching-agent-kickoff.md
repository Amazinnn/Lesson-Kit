# 新对话 Kickoff：教学 Agent（编排器）设计任务书

> 生成时间：2026-11-04。生成者：上一个对话（完成 R8 难度评估、R11 针对需求出题、difficulty-calibration change 的会话）。
> 用法：新对话开场发送本文件路径 + 一段启动语（见文末 §8），Agent 先读本文件再做任何事。
> 本文件是**交接提示词**，不是契约；所有研究/规格结论以仓库内正式文件为准。

---

## 0. 开场纪律（新对话必须先做到）

1. 工作目录：`D:\Projects\Academic Workflow\lesson-kit`；当前分支 `feat/exam-prep-engine`（**主检出在此分支，与 main 分叉**；已提交未推送 3 个：32b78ae9 / bfbd4278 / eebef218）。
2. 先读仓库 `AGENTS.md`，复述三条铁律再动手：**分层方向**（Shell→Domain→Data 单向；Domain 零 IO；Data 唯一碰 SQLite；新代码进 workbench/；禁改 pipeline/pool/scripts/lessonkit.py 行为契约）、**契约权威**（openspec/specs=行为；DATA_MODEL=字段；GLOSSARY=名词；冲突=contract drift 必须显式登记，禁止按时间戳选边）、**scope 边界**（用户可感知行为以旧优先；评级永远显式事务；不自动评级）。
3. 必须加载技能：`ask-user-question`（决策必须用工具、一次问满 4 问）、`ponytail`（要不要写→有没有现成→stdlib→一行）、`subagent-concurrency`（并发 ≤2，主会话干主活；任务书先落盘 `tmp/agent-briefs/`）、`grilling`（design tree 分轮提问，每题带推荐答案）。
4. 用户偏好：研究类扩展先问满 4 问且范围宁宽勿窄；grill **不少于 40 个且成体系**；每步给视图；合并与推送是两次独立授权；提交用 `git add -- <路径>` 与 `git commit -F <msg> -- <路径>` 双路径限定。

---

## 1. 本任务（所有者原话，逐字保留）

> 「我需要的是一个AI Agent能够结合学习者此时的各种状态，具体的任务，需要学习的知识点，合理地编写题目，通过交互式提问与批改问题并确保不偏离进度与核心任务，并处理答题之后、学习练习或者复习完毕的事宜。这不仅仅结合agent自己的对话机制（比如说hook，当然这不是本次对话需要实现的，但是得关心），还需要调配好整个流程——抱歉，我看起来像是许愿，但只有专业而思考全面且严谨的你才可以完成这一切。我会力所能及地给出具体的需求与功能想法，也请你多多grill我（最好不少于40个grill，且有系统地grill）。」

拆解成设计目标：
- **输入面**：学习者此时的各种状态（θ/弱项/到期/错题/自评/目标/考试倒排/进度）。
- **任务面**：具体任务 + 需学习的知识点（kp 组、目标类型、时间盒）。
- **出题**：合理编写题目（池内选题 + 必要时生成；难度/广度/认知层级可控——R11 已给指标与方法）。
- **交互**：交互式提问与批改（提示阶梯、追问、卡点、部分正确、主观批改）。
- **护栏**：不偏离进度与核心任务（偏离检测、纠偏、跑题暂存、疲劳）。
- **善后**：答题之后 / 练习完毕 / 复习完毕的处理（总结、错题沉淀、调度写回、下一步）。
- **机制面**：结合 Agent 对话机制（hook/事件/桥动作/上下文注入；本次不实现但要设计契约）；整个流程可编排。
- 交付口径：**不需要最优解，需要合适的指标 + 系统性的方法**；grill ≥40 个、成体系。

---

## 2. 已完成的成果（直接引用，不要重做）

### 2.1 R8 难度评估研究（本轮前一个对话的核心产出）
- 报告：`docs/research/2026-11-03-difficulty-assessment.md`（459 行）
- 内容：25 篇新核验文献 D1–D25；8 个研究问题逐条结论；4 条提案（D-A1 只读实证校准报告 / D-A2 实证 b 派生表 / D-A3 Agent 评级稳定性流程 / D-A4 耗时清洗规则）；§⑨ 跨报告拓展（与总提案 9 组算法+X10 交叉，10 条 E1–E10）。
- 核心口径（设计时直接用）：
  - **三层难度**：先验难度（四维+cognitive-v1，唯一入池）/ 实证难度（收缩错误率+Wilson，派生只读）/ 功能难度（p_expected，调度瞬时量）。
  - 小样本分层承诺：n<8 只排名；n≥8 只抓 ≥2 难度级粗错（Wilson 半宽 0.285）；n≥30 才出数值结论（半宽 0.168）；任何 n 用收缩估计（K=4）。
  - **choices 事实修正**：`problem_attempts.choices` 存浏览器通道学习者所选选项（JSON 列表）；R7-A3「无选项级数据」已过时。
  - 「做很久但对了」是 θ/稳定性证据，不是题目难度证据。
  - Elo 斜率 120 ⇒ 每 1 难度级正确率 odds ×2（10^(120/400)）。

### 2.2 R11 针对需求出题研究
- 报告：`docs/research/2026-11-04-targeted-question-generation.md`
- 内容：13 篇新核验 G1–G13；六类指标（难度命中率/覆盖/认知层级/质量门禁/新颖度/实证回收）每条带定义+阈值+三层承诺；**五段闭环**：需求单→生成→门禁→评级→实证回收。
- 关键结论：纯提示词控制难度被文献一致证伪；可靠路线=蓝图结构继承+生成-评估迭代+实证回收；GLOSSARY 红线「出题 manifest 不写难度」不破（需求单是生成指令输入，不入池）。

### 2.3 difficulty-calibration change（未实施，提案已 validate）
- `openspec/changes/difficulty-calibration/`：proposal / specs delta（problem-difficulty）/ design / tasks；`openspec validate --strict` 通过。
- 行为：只读 `difficulty calibrate` 报告；`problem_difficulty_stat` 派生表（b/n/content_revision，可重建）；`item_snapshot_json` 补 `interaction_type`。
- design Open Questions 已挂 X1–X11（含 X11 = calibrate 报告加「生成题专项视图」）。

### 2.4 既有算法资产（其它对话已写入文档）
- 总提案：`docs/research/2026-11-02-learning-efficiency-algorithms.md`（9 组算法 A–I + P0 重放口径 LogLoss/AUC）。
- 分域报告：spaced-repetition / knowledge-tracing / adaptive-selection / learning-science / feedback-errors / knowledge-graph / test-assembly / motivation / metacognition / llm-era（共约 262 卡）。
- exam-prep-engine 已落地：`attempt_events`/`focus_events`/`review_state`/`ability_estimate` 四表；四档评分（忘了/勉强/记得/轻松，经 `feedback.grade_of` 读）；引擎策略（fsrs/weighted-score/ols-time/elo-ability + legacy-sm2 回退）；`experiment replay` 只读回放。

### 2.5 已核实的代码/契约事实（避免重复勘测）
- `problem_attempts` 列：id / problem_id / status / note / answer_text / verdict / choices / created_at / part_id / content_revision；dmath 测试池仅 3 行。
- `attempt_events`：attempt_id / problem_id / presented_at / submitted_at / elapsed_ms / away_ms / distracted / item_snapshot_json / created_at（dmath 尚未建表=钩子未接线）。
- `ability_estimate`：kp_id / theta / n / updated_at（KP 级）。`review_state`：problem_id / difficulty(学习者体感) / stability / retrievability / interval_days / due_at / last_grade / updated_at。
- `feedback.grade_of`：1,2→forgot；3→hard；4→good；5→easy。
- `item_snapshot_json`：problem_id / kp_ids / problem_type / source_kind / exam_year / difficulty / difficulty_dims(四维)。
- 既有 bridge 动作：`replace_practice_selection`、`prefill_goal_form`、`check_ingest`、learner-requested Agent attempt recording、explicit Agent difficulty rating；serialized turn、turn budgets、conversation mirror 在 `.lessonkit/jobs/conv-###/`。
- 既有相关 specs：`ai-teacher-bridge`（20+ requirement）、`agent-context`、`agent-learning-evidence`（零写、有界、不推断学习者特质）、`agent-contract-disclosure`、`practice-experience`、`daily-learning-plan`（含 Agent adjustment）、`agent-part-grading`（主观小问/可复议批改）、`practice-review`、`micro-quiz-content`。
- GLOSSARY 红线：四维难度 `_Avoid_` 明列「在出题 manifest 内写难度、difficulty_basis」；Check 管线是唯一 Agent 入池通道；自动评级/入池评级禁令（REQUIREMENTS）。PENDING-DEFINITIONS 现有 7 条待确认（含难度三层、实证猜测率、出题需求单、难度命中率、实证回收）。
- 架构锚点：ADR 0009（内核决定 WHAT / AI 决定 HOW、无 AI 全流程可跑）、ADR 0020（会话治理/教学行为契约）。

---

## 3. 本对话已走到哪（状态透明）

- 已拟好 Round 1 的四个顶层问题（定位/主通道/与桥关系/MVP 边界），**用户中止并转为新对话**；未产出任何新设计文档、未建新 change。
- 上一目标（R11）已 complete；本任务从零起 grill。

---

## 4. 新对话的 Grilling 计划（10 轮 × 4 问 = 40+，按 frontier 推进）

> 纪律：每轮只问「前置已定」的问题；用 AskUserQuestion 一次 4 问（推荐项排第一并标（推荐））；答案会重塑下一轮；事实由 Agent 自己查（本文件 §2.5 已给大部分），不问用户。

**Round 1 顶层定位（已拟好，可直接开问）**
- Q1 决策权：内核确定性编排 + Agent 执行教学动作（推荐）vs Agent 主导 vs 学习者主导。
- Q2 主通道：练习页为主（题面/作答/判分持久化）+ 对话做辅导（推荐）vs 对话为主 vs 双轨对等。
- Q3 与桥关系：扩展 ai-teacher-bridge + 新「教学会话编排」capability（推荐）vs 只扩动作集 vs 新教学协议。
- Q4 MVP：全链最小化（10–12 题会话可跑通/可回放/可无 AI 降级）（推荐）vs 只出题+批改 vs 只出题规格。

**Round 2 学习者状态模型**
- Q5 状态来源与优先级（θ/weak/due/错题/自评/目标/倒排/进度）。
- Q6 冲突裁决（θ 与 weak 冲突、自评与实证冲突时谁赢）。
- Q7 显式输入通道（今天想练 X / 没时间 / 累了）如何进入决策。
- Q8 状态可见性边界（哪些状态绝不注入 Agent，防污染/防隐私）。

**Round 3 任务与进度模型**
- Q9 进度权威（goal/考试倒排 vs 今日计划 vs 会话任务）。
- Q10 任务粒度（一次会话一个任务？跨会话如何续）。
- Q11 偏离的操作定义（题量/时间盒/正确率/支线话题的权重）。
- Q12 中断与恢复点（离开/次日回来读什么）。

**Round 4 出题决策**
- Q13 题源优先级（池内真题 > 池内生成题 > 现场生成；shortage 触发）。
- Q14 出题参数化主权（难度带/广度/kp 范围：内核默认 vs Agent 提议 vs 学习者覆盖）。
- Q15 出题批量与节奏（逐题 vs 3–5 题批滚）。
- Q16 重复/新颖控制（重做间隔、变式触发、去重阈值）。

**Round 5 交互提问与辅导**
- Q17 提示阶梯（几档、给完是否降分、ai_events 记录）。
- Q18 错题追问策略（归因追问 vs 直接讲解；与 stuck 标记兼容）。
- Q19 对话 vs 练习页职责边界（题面渲染/作答/揭晓分别在哪）。
- Q20 多小问/主观题的交互粒度（part 级）。

**Round 6 批改与反馈**
- Q21 批改权威（客观规则/主观 Agent/自评的三角色分工）。
- Q22 部分正确计分口径（0/0.5/1 vs 分档）。
- Q23 不确定批改（Agent 标 uncertain + 转人工/自评，不猜）。
- Q24 反馈三层（结论/归因/行动；禁对人评价）。

**Round 7 进度护栏**
- Q25 偏离检测信号（跑题/单题超时/题量不足/频繁跳题）。
- Q26 纠偏动作阶梯（提醒→换题→降难度→收尾；never lock）。
- Q27 学习者跑题提问的处理（parked digressions：回答+暂存+引回）。
- Q28 疲劳与时间盒（45min/正确率下降→建议不阻断）。

**Round 8 收尾善后**
- Q29 收尾判定（答完/时间到/喊停）。
- Q30 收尾产物（摘要工件/错题沉淀/调度写回 review_state）。
- Q31 下一步建议主权（内核给计划事实，Agent 写文案）。
- Q32 跨会话交接（下次开场读上次摘要+未完成题位+到期复习）。

**Round 9 对话机制与 hook 契约（本轮不实现，设计契约）**
- Q33 上下文注入分层（固定摘要 + 按需扩展读；token 预算）。
- Q34 工具面与写闸门（读自由/写 intent-gated；新增动作清单）。
- Q35 事件钩子（提交后/卡题超时/会话开始→主动介入；turn budget）。
- Q36 失败降级（无 AI 内核路径完整）。

**Round 10 指标、验收与不做清单**
- Q37 成功指标（学习：正确率趋势/校准 Brier/实证回收；流程：完成率/偏离率/提示率）。
- Q38 护栏指标（first_independent_correct_rate / 提示率 / 超时率三线）。
- Q39 评估协议（先 P0 回放口径，上线后 A/B 护栏）。
- Q40 明确不做清单（自动评级/改难度字段/跨课程汇总/第二套对话协议/惩罚式 streak…）。

**Round 11（若 frontier 未空）**：数据模型增列、工件契约（FILE_CONTRACT）、名词定义、与 difficulty-calibration / Check 管线的接口细节。

---

## 5. 硬约束（设计必须遵守，违反即错）

1. **三层难度边界**：只有先验难度写 `problems` 六字段组；实证/功能难度派生只读；评级永远显式事务（`difficulty check/apply`）。
2. **出题 manifest 不写难度**（GLOSSARY _Avoid_）：需求单是生成指令输入，不入池；Check 管线是唯一 Agent 入池通道。
3. **内核决定 WHAT / AI 决定 HOW**（ADR 0009）：无 AI 时全流程（出题→作答→判分→收尾）仍可跑。
4. **阅读零副作用**：Agent 读状态不得产生 attempts/ratings/practice 写（agent-learning-evidence / agent-context 纪律）。
5. **兼容边界**：用户可感知行为以旧优先；新策略并存+可回退；never lock 原则。
6. **名词先定义**：新概念（如「教学会话」「任务单元」「偏离」「提示阶梯」）先写 `docs/PENDING-DEFINITIONS.md`，采纳才进 GLOSSARY。
7. **stdlib-only / 单进程 / 无哈希 ID / 增量 schema**（ensure_* 模式）。
8. 本任务**不做实现**：产出研究报告 + OpenSpec change（建议名 `teaching-session-orchestrator` 或 `agent-teaching-loop`），可 validate --strict。

---

## 6. 建议的最终交付物（供新对话参考，非所有者的硬性裁定）

1. `docs/research/<date>-teaching-agent-orchestrator.md`：① 一页综述（教学环：状态→任务→出题→交互→批改→护栏→收尾→hook）② 每个 frontier 决策的结论 ③ **指标体系**（进程/学习/护栏三层）④ **系统性方法**（每段动作的输入/输出/失败降级/契约挂点）⑤ 与 R8/R11/difficulty-calibration/exam-prep-engine/Check 管线的接口。
2. OpenSpec change：proposal（why/what/capabilities/impact）+ specs delta（建议新 capability `teaching-session`，或 modified `ai-teacher-bridge`）+ design（事件/动作/hook 契约、上下文注入、写闸门）+ tasks（先失败测试再实现）。
3. PENDING-DEFINITIONS 新名词登记；changelog 交接记录。

---

## 7. 关键文件索引（新对话按需读）

| 主题 | 路径 |
|---|---|
| 难度评估研究（25 篇+D-A1..A4+§⑨） | `docs/research/2026-11-03-difficulty-assessment.md` |
| 针对需求出题（13 篇+六类指标+五段闭环） | `docs/research/2026-11-04-targeted-question-generation.md` |
| 既有算法总提案（9 组+P0） | `docs/research/2026-11-02-learning-efficiency-algorithms.md` |
| 难度契约 | `openspec/specs/problem-difficulty/spec.md` |
| 教学桥 | `openspec/specs/ai-teacher-bridge/spec.md` |
| 批改 | `openspec/specs/agent-part-grading/spec.md`、`practice-review/spec.md` |
| 学习证据/上下文 | `openspec/specs/agent-learning-evidence/spec.md`、`agent-context/spec.md` |
| 每日计划 | `openspec/specs/daily-learning-plan/spec.md` |
| 难度校准 change | `openspec/changes/difficulty-calibration/` |
| 引擎 change | `openspec/changes/exam-prep-engine/` |
| 名词 | `docs/GLOSSARY.md`、`docs/PENDING-DEFINITIONS.md` |
| 字段语义 | `docs/DATA_MODEL.md` |
| 架构/ADR | `docs/ARCHITECTURE.md`、`docs/adr/0009*`、`docs/adr/0020*` |

---

## 8. 新对话启动语（直接复制粘贴）

> 先读 `docs/handoffs/2026-11-04-teaching-agent-kickoff.md`，那是本对话的任务书与已有成果全集（含 40 问 grilling 计划）。按其中 §0 复述三条铁律、加载指定技能，然后从 §4 的 Round 1 开始提问。
