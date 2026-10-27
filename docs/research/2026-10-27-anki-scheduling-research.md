# Anki 记忆调度算法与 Lesson Kit 适配资料（2026-10-27）

本轮是知识搜集与适配条件分析，不构成产品规格或迁移授权。已查 Anki 手册、固定发布标签源码、FSRS 作者仓库，并核对 Lesson Kit 当前实现；未更换现有调度算法或写入课程数据。

## 建议先读的结论

1. 后续重点研究 FSRS。Anki 还保留 legacy SM-2 路径；本轮核对的 Anki 26.09.3 提供 FSRS-6，上游 FSRS-7 开发进展不能等同于 Anki 已部署版本。
2. FSRS 按稳定的复习项目跟踪 D（记忆难度）、S（稳定性）、R（回忆概率），用于安排下一次复习。它的回忆概率不能直接解释为知识点掌握度、考试得分或迁移能力。
3. Lesson Kit 已有 SM-2 变体。主要适配难点是证据语义：现有 1–5 自评与 FSRS 四级评分不同，客观答对也不等于 Easy；复习方向、内容版本及被更正的历史都需要明确规则。
4. 调度与个性化优化可以分开：先研究默认参数的小范围离线重放，随后才讨论个体拟合。对比到期日期只能检查接入行为；预测效果需要按时间留出后续复习结果，不能把未来记录泄漏给训练。

## 如何解释算法评估

作者维护的 [SRS Benchmark](https://github.com/open-spaced-repetition/srs-benchmark) 用历史复习预测之后的回忆结果，报告 Log Loss、RMSE (bins)、AUC。它提供预测校准与区分能力的证据，不直接检验课程考试、综合解题或学习迁移。未来若试点，应分别观察预测、实际复习负担与学习效果，不能只用一个预测分数宣布教学效果更好。

## 下一步的最小研究实验（尚未执行）

先限定少量原子、单方向闪卡。新试点直接收集 Again／Hard／Good／Easy 的明确反馈；旧 1–5 记录只在语义已确认时考虑映射。先在隔离资料上重放、比较行为，不改真实到期日。进入实现前只需解决四个问题：调度项目是什么、评分表达什么、历史怎样保留及更正、一天从什么时候开始。依赖选择与版本固定留待方案阶段。

以下保留详细证据及适用边界；来源阅读日均为 2026-10-27，带 main 链接的内容未来可能变化。

## Anki 调度算法资料核对

抓取日期：2026-10-27。范围：Anki 现行手册与固定版本源码、FSRS 作者维护的文档/仓库。标记「已确认」表示来源直接写明；「推断」是基于来源边界的判断；「未知」表示资料冲突或未覆盖。

### 结论

**已确认：Anki 26.09.3 提供可选 FSRS-6，并保留 legacy SM-2。** Anki Releases 页面抓取时将 26.09.3 标作 Latest；26.09 发布说明记载更新 FSRS 到 6.6.2。固定的 26.09.3 `Cargo.toml` 将 Rust crate `fsrs` 锁到 6.6.2；同标签源码直接把 `FSRS6_DEFAULT_DECAY` 注释为 FSRS-6，并以 21 个参数区分旧的 FSRS-4.5/5。因此版本判断来自实际 Anki 源码，不是从 crate 的 `6.6.2` 数字猜测。现行手册没有标注算法代际，且短期调度段仍提 FSRS-5；上游 TS-FSRS 主分支已有 FSRS-7 beta 变更，不能把它称作 Anki 26.09.3 已部署算法。[S1][S3][S4][S5][S11]

**已确认：Anki 的 legacy SM-2 是带产品规则的变体。** 它有可配置的学习/重学步骤与四档按钮，而不是照搬 SM-2 的六档评分。旧复习中 Again 进入重学并降低 ease；Hard 下调 ease、Good 按 ease 延长、Easy 再加 easy bonus。新卡学习阶段的反复失败不降低后续 ease。启用 FSRS 后，毕业间隔、easy bonus 等 SM-2 专属设置隐藏，故比较必须说明走哪套调度路径。[S1][S2]

**已确认：FSRS 的状态是按卡片建模。** R（retrievability）是当前回忆概率，随距上次复习的时间和 S 变化；S（stability）是回忆概率从 100% 降至 90% 所需的时间；D（difficulty）取 1–10，表示记忆状态中的难度并影响后续间隔增长。R 随时间变，D/S 在复习后更新。它们不是题目内容难度等级，也不是对考试成绩的直接估计。[S6][S7][S8]

**调度与优化不是同一步。** 调度器根据当前卡片状态、参数、评分和 desired retention 计算下次间隔；优化器则用过去的复习日志拟合参数。新用户可以先用 FSRS 默认参数；个性化优化需要足够历史，Anki 手册把「少于几百次复习」列为健康检查可能较差的原因，但没有将它列为硬性最低门槛。缺历史记录时，手册允许用 historical retention 近似填补，默认假设旧复习成功率为 90%。[S1][S7][S10]

**desired retention 是记忆/工作量旋钮。** Anki 默认 90%；提高目标会缩短间隔、增加每日复习量，接近 100% 时负担快速上升，手册建议低于 97%，并建议按可投入的每日分钟数或复习量选择。更改参数、保留率或启用 FSRS 默认不会立即重排既有到期日；启用重排可能造成大量卡片集中到期。旧版「Compute Minimum Recommended Retention」已在 Anki 25.07 移除，不能当作当前功能介绍。[S1]

**评分语义和短期步骤需分开记。** Again 表示忘记/失败；Hard 仍是答对，只是迟疑或费力；Good/Easy 代表成功回忆且熟练程度不同。把忘记误按 Hard 会让预测间隔过长。复习卡按 Again 会进入 relearning；手册建议 learning/relearning 步骤少且短于一天，并在同日完成。清空步骤让 FSRS 控制短期调度仍标为实验功能。FSRS-6 公式专门处理同日复习；作者 ABC 文档称 FSRS-6 使用同日全部复习，但作者教程仍称优化器一天只用第一条，Anki 真保留率统计也只数每天首条。**未知：**这些统计/教程规则不能代替对 Anki 26.09.3 优化器数据整理代码的逐行核验，因此当前版优化是否把多条同日记录都用于训练，不在本次结论中确认。[S1][S6][S7][S8][S9]

**数据最低轮廓（已确认）**：按卡片稳定标识关联的有序评分历史；训练材料至少需要时间/间隔与 Again、Hard、Good、Easy 评分。作者优化器的兼容 schema 还列出 review state、时区和 day-start，前两者可选；review duration 记录成本但可选。评分是学习者当时对记忆表现的主观报告。若用于逐卡预测，卡片身份不可丢；新卡尚无历史时由默认模型起步，首次作答后才有该卡状态。缺日志或跨产品导入时，应保留「历史保留率是假设」这一不确定性。[S7][S10]

**推断边界：** D/S/R 与评分描述的是单张卡片的回忆概率及复习时机。以上来源没有证明 FSRS 预测提升会迁移到考试中的综合解题、概念迁移或长期课程成绩；这类效果须单独用考试/迁移任务验证。[S7][S8]

**已核许可范围：** FSRS Optimizer Python 仓库标注 BSD-3-Clause；这不证明 Rust `fsrs` crate、整套 FSRS 算法或 Anki 代码具有相同授权，后续若考虑复用需逐个核验对应仓库/版本。[S10]

### 来源表

| ID | 一手来源（抓取日均为 2026-10-27） | 支持内容 / 证据状态 |
|---|---|---|
| S1 | [Anki Manual：Deck Options](https://docs.ankiweb.net/manual/deck-options) | 当前设置、保留率、重排、步骤；已确认。 |
| S2 | [Anki FAQ：What spaced repetition algorithm?](https://github.com/ankitects/faqs/blob/main/src/what-spaced-repetition-algorithm.md) | Anki legacy SM-2 与按钮行为；用于旧路径说明。 |
| S3 | [Anki Releases](https://github.com/ankitects/anki/releases) | 抓取时 26.09.3 为 Latest；26.09 更新 FSRS 6.6.2；已确认。 |
| S4 | [Anki 26.09.3 Cargo.toml](https://raw.githubusercontent.com/ankitects/anki/26.09.3/Cargo.toml) | 固定依赖 `fsrs = 6.6.2`；已确认。 |
| S5 | [Anki 26.09.3 memory_state.rs](https://raw.githubusercontent.com/ankitects/anki/26.09.3/rslib/src/scheduler/fsrs/memory_state.rs) | 明确标注 FSRS-6 默认衰减与 21 参数边界；已确认。 |
| S6 | [Anki Manual：Statistics](https://docs.ankiweb.net/manual/stats) | D/S/R 含义；真保留率每日首条规则；已确认。 |
| S7 | [FSRS Wiki：ABC of FSRS（固定修订）](https://github.com/open-spaced-repetition/fsrs4anki/wiki/ABC-of-FSRS/7a41bf8382f0b94f4a8e4d72b713e07d9affc375) | 状态、默认参数、FSRS-6 同日规则、保留率；作者文档已确认。 |
| S8 | [FSRS Wiki：The Algorithm（固定修订）](https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm/bccece8e7888c8121784ef9d9e8022d4961baf83) | FSRS-6 公式、21 参数、同日复习；已确认。 |
| S9 | [FSRS4Anki tutorial](https://github.com/open-spaced-repetition/fsrs4anki/blob/main/docs/tutorial.md) | 旧版优化器每日首条说法；与 S7 冲突，故该点未知。 |
| S10 | [FSRS Optimizer repository](https://github.com/open-spaced-repetition/fsrs-optimizer) | 复习日志字段、subjective rating、BSD-3-Clause；仓库标注已确认。 |
| S11 | [TS-FSRS changelog](https://github.com/open-spaced-repetition/ts-fsrs/blob/main/packages/fsrs/CHANGELOG.md) | 上游 main 中 FSRS-7 beta 开发条目；不能外推为 Anki 稳定版。 |

### 使用限制

这份便笺用于未来方案讨论，不是算法移植规范。FSRS 作者文档与 Anki 手册有短期/同日细节的版本差异；若需要复刻 Anki 26.09.3，下一步应固定到其源码审查 `reviews_for_fsrs` 和优化输入整理路径。不要仅凭学习曲线指标推断考试迁移收益。

## Lesson Kit 与 Anki FSRS 兼容性研究

范围：只读核对 Lesson Kit 当前排期、作答记录与学习状态，并查 FSRS 一手资料；未实现或修改任何代码、数据与规格。

### 仓库现状

Lesson Kit 当前是一个 SM-2 变体：调度单位按 `(item_type, item_id, direction)` 区分知识点、题目与闪卡；闪卡的正反方向也可独立排期。公式以 ease 2.5 起步，成功间隔为 1 天、6 天、之后按 ease 扩张；低评分归零间隔并进入 relearning。纯调度函数把 correct=4、wrong/stuck=2、skip=不更新，显式自评 1–5 则直接作为调度质量值；浏览器关闭自评时另走兼容分支，把答对折算为 5、答错折算为 2。[workbench/domain/schedule.py:1-70] [workbench/data/attempts.py:522-544] [pool/scripts/pool_schema.py:609-628]

调度行只保留当前 repetitions、ease、interval、due、last_rating、last_reviewed_at，不是逐次复习日志。历史主要在 problem_attempts（题目作答、判定、时间）和 feedback_events（1–5 自评、备注、时间；评分可通过 attempt_id 关联作答）中。多次作答/评分会新增行，行 id 可帮助排序同秒记录，但数据库默认 created_at 只有秒级时间；schedule 的 last_reviewed_at 又只写日期。另有两个例外：Paper 回看能原位改评分，Agent 更正可替换最新尝试及其影响；二者都不是不可变事件历史。反馈事件未存闪卡 direction，故同一双向卡的两种回忆历史不能可靠拆开。[pool/scripts/pool_schema.py:286-297,609-642,955-965] [workbench/data/pool.py:213-229,318-378] [docs/DATA_MODEL.md:146-156] [docs/GLOSSARY.md:187-188]

三种学习证据不可混用：客观 verdict 是本次答对/答错；自评是学习者显式的 1–5 反馈（1–2 needs_work、3–4 review、5 mastered）；当前状态是覆盖式投影。开启自评时，单有作答/判定不会推进调度；但关闭自评的兼容流程会把客观答对折算为 mastered 且不写评分事件。不要把此兼容折算当作 FSRS 的 Easy，也不要由单次正确回答断言持久掌握。独立 mastery v0 的 recently_stable 至少要求跨两个日期的正向证据。[workbench/domain/feedback.py:15-16,33-86] [workbench/data/attempts.py:461-544] [docs/GLOSSARY.md:177-179,635-637] [workbench/domain/mastery.py:114-123]

身份与证据映射也有边界：problem_id 虽稳定，但题目可原地改内容，旧尝试不会随新题面重判；一题还可关联多个 kp_id。当前反馈会把一个题目评分投影到这些知识点，但把它复制为多条 FSRS 训练记录会虚增证据。题目集成需先决定内容更新是否重置记忆，以及跨 KP 题是否只保留题目级调度。[docs/DATA_MODEL.md:21,65] [workbench/domain/feedback.py:33-47,91-98] [openspec/specs/review-workbench/spec.md:1039-1040]

### FSRS 一手资料核实（网页核对日：2026-10-27）

FSRS 的评分是 1–4：Again、Hard、Good、Easy；不是 Lesson Kit 的 1–5 自评。其优化示例按单个复习项目组织 `rating + delta_t` 历史，并称最好使用多张卡的历史；FSRS-RS README 明确提供 `compute_parameters` 优化入口及按多卡历史构造 `FSRSItem` 的示例，也有以 ease、interval、retention 调用 `memory_state_from_sm2` 的迁移 API。它可做状态迁移，但不等于可无损还原 Lesson Kit 的完整历史。[FSRS-RS optimizer README](https://github.com/open-spaced-repetition/fsrs-rs#optimize-parameters-from-review-logs) [SM-2 迁移示例](https://github.com/open-spaced-repetition/fsrs-rs/blob/main/examples/migrate.rs)

Py-FSRS 的 ReviewLog 字段为 card_id、rating、review_datetime、review_duration；duration 可为空。其调度器对间隔不足一天的再次复习走短期稳定性更新，说明同日复习的事件顺序和各次评分不能被 latest-row 覆盖。[ReviewLog 定义](https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/review_log.py) [同日处理](https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/scheduler.py)

Anki 手册说明优化器需要一段复习历史，少于数百次可能数据不足；Hard 表示仍然回忆成功但费力，忘记应按 Again。MCQ 的二元正确并不能表明是否猜中或回忆费力；教学理论卡建议从选择题识别逐步转向简答回忆与应用题。因此客观判分与 FSRS 自评不可直接按数字转换。[Anki FSRS 手册](https://docs.ankiweb.net/manual/deck-options) [practice-structuring.md:9-19]

| FSRS 输入 | Lesson Kit 对应物 | 兼容判断 |
|---|---|---|
| 项目身份 | `item_type+item_id+direction`；题目 attempt 用 problem_id | 闪卡方向历史缺失；多 KP 题目不能自动拆成多个独立项目 |
| 每次评分 | feedback_events.rating；verdict 单独存 | 1–5 与 1–4 语义不一致；客观猜对不可冒充 Easy |
| 时间 / 间隔 | attempt 与反馈 created_at、id | 可按历史重建日间隔；时区、秒级并列及编辑后历史须定规则 |
| 当前状态 | review_schedule 最新 ease / interval / due | 可研究 SM-2 状态初始化；持续重放仍需完整事件与 retention |
| 作答耗时 | 无专用字段 | FSRS ReviewLog 中可选，当前缺失不阻塞基本调度 |

### 最小安全实验与待决问题

建议先做离线纸面重放：只取一小组原子闪卡、只保留单方向。旧 1–5 评分只有在其含义经确认后才映射；更安全的新试点可直接收集 Again/Hard/Good/Easy。逐事件重放 FSRS、与现有 due 日期比较，不写池、不改用户排期；这只能检查集成行为，不证明算法更优。准确性比较还需按时间切分训练与留出复习结果。暂不混入 MCQ 客观 verdict、跨多个 KP 的综合题，也不优化个体参数，直到有足够多卡片和复习历史。

之后需决定：正式调度单位是闪卡、题目还是知识点；自评是否改用四级量表及如何处理“会但不稳”；复习时间的 UTC/本地日界规则；Paper/Agent 原位更正是否保留训练审计版本。
