## Why

`pool/c02.db`（497 题）经 `ads-pool-content-repair` 修完结构后，答案侧仍留着
三处缺漏，练习页上表现为"看不到答案/解析"之外的第三种残缺——**题没有答案**：

- **109 道 micro-quiz 没有 `answer_key`**（65 判断 + 42 单选 + 2 多选）。这些题
  在练习页不判分，只说"本题没有存储答案键"。修复时按"源里推不出来就留空"的
  规则（`ads-pool-content-repair` D6）处理，但 109 题的 `solution` **全部带有
  【答案】段**，源文件也都在 `题库/` 下可读——答案本可以补上。
- **3 道题 `solution` 为空**：`c02-ch04-prob-001`、`c02-ch13-prob-004`、
  `c02-ch07-prob-021`（key 已有，只缺解析）。
- **325 条 `error_reason` 是 40 字以下的泛化标签**（p50=6 字，大量"概念辨析
  易混"），判错时给不出任何具体信息，起不到"为什么错"的作用。

门禁规定"有键必填 `error_reason`"（`workbench/domain/micro_quiz.py::
validate_payload`），所以补 109 个 key 的同时必须给它们写 error_reason。

## What Changes

- **补 109 个 `answer_key`**：按 `source_evidence` 回到 `题库/` 原卷逐题核对
  推导（源为准），源无法判定时 fallback 到本题 `solution`【答案】段，推导
  出处写进 `source_answer`；每个 key 都要过 quiz-type 形状校验
  （判断→是/否，单选→选项之一，多选→选项子集）。
- **同步写 109 条短标签 `error_reason`**（≤15 字，与现库 346 条风格一致）。
- **补 3 条 `solution`**：读源文件写【答案】【解析】结构的解析，
  `solution_origin` 按来源标注。
- **扩写 325 条短 `error_reason`**（现有 <40 字的全部）：从各题 `solution`
  提炼成 20–100 字的具体易错原因句，替换"概念辨析易混"这类泛化标签。
- 全部改动走现成的 `ingest recipe problem-patch --apply`（原地 UPDATE，不删
  行、不改 id、不动学习记录，逐批有备份和 `ingest rollback --batch` 回滚）。
- 不改任何代码、schema、门禁；不碰 109 题以外的 answer_key、不动选项/题干/
  知识点绑定。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. 这是一次数据补漏，不改变系统行为，`.openspec.yaml` 声明
`skip_specs: true`。答案键的形状与"有键必填 error_reason"契约仍由
`micro-quiz-content` 既有要求约束，本次只是让数据满足它；补漏台账与验收
标准写在 `design.md`。

## Impact

- **Data**: `pool/c02.db` 的 437 行（109 行 key+error_reason+source_answer、
  3 行 solution、325 行 error_reason），经 15 个按章 patch 批次写入。
- **Learning records**: 现有 `problem_progress` 36 / `problem_attempts` 39 /
  `review_schedule` 36 条——id 不变、只 UPDATE，全部保留。
- **Source material**: `题库/期中`（6 md）与 `题库/期末`（43 md）只读，
  `题库原料/` 原件只读。
- **Tool**: 无代码改动；新增的只有 `repair/` 下的推导台账、preflight 脚本
  与 manifest（与 `ads-pool-content-repair` 同目录惯例）。
- **Risk**: 答案推导错误会让练习判错分——用"源 + solution 双验证 + 冲突不落
  库"控制，见 design.md。
