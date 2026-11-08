# WP02 2.6 映射/完整性标注案例（26 条）

任务原文：> 用原文标注20个映射/完整性案例，分别报告结构检查和语义核对。限定章节分类补齐只改有依据项，疑点不进入已核对练习。

全部案例在脱敏临时夹具中执行（脚本 `annotation-run.py`，原始输出 `annotation-report.json`），不触碰真实课程数据；`knowledge_type` 走既有治理路径 `data update kp`（2.4 之后为独立单元），未新增第二套写池通道。

**口径**：结构检查 = content_audit 的六项检查 + ingest 门禁 + 字段校验；语义核对 = 折叠标题同义匹配、题干判重（problem_identity）与人工证据。两者分开报告，语义存疑时不写入。

| # | 类型 | 原文（摘录） | 结构检查 | 语义核对 | 处置 |
|---|---|---|---|---|---|
| M1 | mapping | 提案「等差数列求和公式」 ↔ 既有「等差数列求和公式」 | 折叠标题相同 | 同义：复用既有身份 | 见下述验证 |
| M2 | mapping | 提案「等差数列 求和 公式！」 ↔ 既有「等差数列求和公式」 | 折叠标题相同（仅空格/标点差异） | 同义：复用既有身份 | 见下述验证 |
| M3 | mapping | 提案「抽屉原理」 ↔ 既有「鸽笼原理」 | 折叠标题不同 | 同义但词面不同：机器不合并，人工裁决 | 见下述验证 |
| M4 | mapping | 提案「组合数的两个性质」 ↔ 库内无同义点 | 折叠标题无命中 | 按治理路径新建（bundle 计划成立） | 见下述验证 |
| M5 | mapping | 提案「加法原理（练习总结）」 ↔ 既有「加法原理」与「加法原理（讲义版）」 | 同一折叠命中两条既有记录 | 歧义：拒收并点名两条，人工裁决 | 见下述验证 |
| M6 | mapping | 两道不同 key、相同题干「袋中有 5 只白球…」的题目 | problem_identity 相同 | 重复内容：双拒零写入 | 见下述验证 |
| M7 | mapping | 题目 kp_ids 引用「dmath-ch06-kp-999」（库内与包内均无） | unknown knowledge point | 依赖阻断：该题零写入 | 见下述验证 |
| M8 | mapping | 提案「错位排列公式」 knowledge_type=concept-property | 方法提案要求三类方法类型之一 | 拒收：分类不确定不创建 | 见下述验证 |
| M1v | mapping-gate | M1 的真实门禁执行 | plans=1（接受） | 折叠命中库内既有 → 应改走复用 | 演示：门禁只做身份校验，同义复用在提案层 |
| M3v | mapping-gate | M3 的真实门禁执行 | plans=1（接受） | 「抽屉原理」与「鸽笼原理」折叠不同 → 不会被自动合并 | 反例：同义词不静默合并 |
| M6v | mapping-gate | M6 的真实门禁执行 | plans=0，duplicate 错误 2 条 | 同一题干判重 | 双拒零写入 |
| M7v | mapping-gate | M7 的真实门禁执行 | plans=0 | unknown knowledge point | 依赖阻断零写入 |
| S0 | semantic | 提案「加法原理（练习总结）」的折叠匹配（歧义环境） | 输入合法 | 折叠无精确命中 0 条 | 因此走新建路径——下面的拒收来自多命中，不是这里的探测 |
| S1 | semantic | 提案「等差数列 求和 公式！」的折叠匹配 | 输入合法（标题/正文/类型） | 折叠命中 [] | 复用既有身份 |
| S5 | semantic | 提案「加法原理」在两条同折叠记录之间的复用检查 | 输入合法 | 拒收：several equivalent knowledge points exist: dmath-ch06-kp-001, dmath-ch06-kp-070 — decide which one to extend instead of creating another | 歧义拒收，知识点总数不变（3 == 3） |
| I1 | integrity-audit | 知识点「无标题检查」正文为空、标题缺失 | untitled 检查命中 | 标题缺失即结构问题 | 进入 findings，不落已核对 |
| I2 | integrity-audit | 选择题「P50」未标 objective 与答案键 | unmarked-objective 检查命中 | 形态完整但判分依据缺失 | 进入 findings |
| I3 | integrity-audit | 题目「P51」为普通计算题（对照） | unmarked-objective 未命中 | 无需补标 | 保持原状 |
| I4 | integrity-audit | 题干「P50/P51」正文不同 → 非重复 | duplicates 检查 | 题干规范化后不同 | 无 finding（对照） |
| I5 | integrity-audit | 题 P51 引用 dmath/ch06/absent.png 但文件不存在 | figures 检查命中 2 条 | 引用与文件不一致 | 进入 findings，不落已核对 |
| C1 | classification | 「错位排列公式」有教材出处 | 字段合法（method-modeling） | 证据=教材例 6.3 | 补齐 knowledge_type |
| C2 | classification | 「捆绑法」有教材出处 | 字段合法 | 证据=教材例 6.5 | 补齐 knowledge_type |
| C3 | classification | 「隔板法」有教材出处 | 字段合法 | 证据=教材例 6.8 | 补齐 knowledge_type |
| C4 | classification | 「存疑：讲义说法不一致」无依据 | 不写入 | 证据不足 | 保持原状，不进已核对练习 |
| C5 | classification | 「存疑：两道题答案矛盾」无依据 | 不写入 | 证据不足 | 保持原状，不进已核对练习 |
| C6 | classification | 已核对范围 = 按 types 检索 | knowledge_query(types=['method-modeling']) | 命中 3 条，全部有证据 | 疑点不在其中：dmath-ch06-kp-063, dmath-ch06-kp-064 |

## 分类补齐（C1–C6）的行为验证

- 有依据的三条（教材例 6.3/6.5/6.8）→ `knowledge_type` 由占位 memory-recall 补齐为 method-modeling；
- 无依据的两条（讲义说法不一致、题目答案矛盾）→ 保持占位值原状，**不进入已核对练习**：按 `knowledge_query(types=['method-modeling'])` 检索的已核对范围只含 dmath-ch06-kp-060 / kp-061 / kp-062 三条有依据项，疑点不在其中；
- 汇总字段 `doubtful_excluded_from_verified = true`。

## 结论

- 映射：同义折叠命中即复用；词面不同的同义词（抽屉/鸽笼）**不自动合并**，歧义命中拒收并点名；重复题干双拒零写入；依赖被拒单元零写入。
- 完整性：untitled / unmarked-objective / figures 各检查按例命中并入 findings；结构合法不等于语义完整（I 类案例与 C4/C5 的区分）。
- 门禁计划剔除与单元化（2.4）使上述处置逐单元生效；本表为证据记录，不含生产数据。
